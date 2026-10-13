# Where one build stands in TestFlight internal testing — read-only.
#
#   source scripts/testflight/env.sh
#   bundle exec ruby scripts/testflight/build_delivery_state.rb com.americangroupllc.bodyquest 202610081811
#
# Prints one JSON object: the build's processing state, export-compliance
# answer, internal beta state, which internal groups can see it (a group with
# hasAccessToAllBuilds sees every build), the testers in those groups and their
# state (INVITED / ACCEPTED / INSTALLED), and the "What to Test" text.
# Section 6 of scripts/predelivery.py reads this. Only GET requests: it never
# adds a build to a group, invites anyone or edits test notes.
require "json"
require "net/http"
require "uri"
require "spaceship"

HOST = "https://api.appstoreconnect.apple.com"
TOKEN = Spaceship::ConnectAPI::Token.create(
  key_id: ENV.fetch("ASC_KEY_ID"), issuer_id: ENV.fetch("ASC_ISSUER_ID"),
  filepath: ENV.fetch("ASC_KEY_PATH"))

def get(path)
  uri = URI(path.start_with?("http") ? path : "#{HOST}/#{path}")
  r = Net::HTTP::Get.new(uri)
  r["Authorization"] = "Bearer #{TOKEN.text}"
  res = Net::HTTP.start(uri.host, 443, use_ssl: true, read_timeout: 120) { |h| h.request(r) }
  [res.code.to_i, (JSON.parse(res.body) rescue { "raw" => res.body.to_s[0, 300] })]
end

def get_all(path)
  data, url = [], path
  while url
    code, body = get(url)
    return [code, body] unless code == 200
    data.concat(body["data"] || [])
    url = body.dig("links", "next")
  end
  [200, data]
end

bundle_id, build_number = ARGV
abort "usage: build_delivery_state.rb <bundle_id> <build_number>" unless bundle_id && build_number
out = { "bundle_id" => bundle_id, "build" => build_number }

code, apps = get("v1/apps?filter[bundleId]=#{URI.encode_www_form_component(bundle_id)}")
app = (apps["data"] || [])[0] if code == 200
unless app
  out["error"] = "no App Store Connect record (HTTP #{code})"
  puts JSON.pretty_generate(out); exit 0
end
out["app_id"] = app["id"]

code, builds = get("v1/builds?filter[app]=#{app['id']}&filter[version]=#{URI.encode_www_form_component(build_number)}" \
                   "&include=buildBetaDetail&limit=5")
b = (builds["data"] || [])[0] if code == 200
unless b
  _c, latest = get("v1/builds?filter[app]=#{app['id']}&sort=-uploadedDate&limit=1")
  out["found"] = false
  out["latest_uploaded"] = (latest["data"] || [])[0]&.dig("attributes", "version")
  puts JSON.pretty_generate(out); exit 0
end
a = b["attributes"]
out.merge!("found" => true, "build_id" => b["id"], "processing_state" => a["processingState"],
           "uploaded" => a["uploadedDate"], "expired" => a["expired"],
           "uses_non_exempt_encryption" => a["usesNonExemptEncryption"],
           "min_os" => a["minOsVersion"])
detail = (builds["included"] || []).find { |x| x["type"] == "buildBetaDetails" }
out["internal_build_state"] = detail&.dig("attributes", "internalBuildState")
out["external_build_state"] = detail&.dig("attributes", "externalBuildState")

_c, locs = get("v1/builds/#{b['id']}/betaBuildLocalizations")
out["what_to_test"] = (locs["data"] || []).map { |l| { "locale" => l.dig("attributes", "locale"),
                                                       "text" => l.dig("attributes", "whatsNew") } }

code, groups = get_all("v1/apps/#{app['id']}/betaGroups?limit=200")
out["internal_groups"] = []
if code == 200
  groups.select { |g| g.dig("attributes", "isInternalGroup") }.each do |g|
    sees = g.dig("attributes", "hasAccessToAllBuilds")
    unless sees
      _c2, gb = get_all("v1/betaGroups/#{g['id']}/builds?limit=200")
      sees = gb.is_a?(Array) && gb.any? { |x| x["id"] == b["id"] }
    end
    _c3, testers = get_all("v1/betaGroups/#{g['id']}/betaTesters?limit=200")
    states = Hash.new(0)
    (testers.is_a?(Array) ? testers : []).each { |t| states[t.dig("attributes", "state") || "UNKNOWN"] += 1 }
    out["internal_groups"] << { "name" => g.dig("attributes", "name"), "sees_build" => sees,
                                "all_builds" => g.dig("attributes", "hasAccessToAllBuilds"),
                                "testers" => states.values.sum, "tester_states" => states }
  end
else
  out["groups_error"] = "HTTP #{code}"
end
puts JSON.pretty_generate(out)
