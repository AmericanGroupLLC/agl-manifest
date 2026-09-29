#!/usr/bin/env ruby
# Declare, per app, whether the build uses the Advertising Identifier (IDFA).
#
#   source scripts/testflight/env.sh
#   bundle exec ruby scripts/testflight/set_idfa.rb --dry-run
#   bundle exec ruby scripts/testflight/set_idfa.rb
#   bundle exec ruby scripts/testflight/set_idfa.rb yourtube
#
# Every one of the 39 App Store versions had `usesIdfa: null` — the question
# has never been answered for any app. App Store Connect will not submit a
# version while it is unanswered, and the surface error says only
#
#     This resource cannot be reviewed, please check associated errors
#
# which names nothing. It is answered here rather than 39 times by hand.
#
# The answer is measured, not guessed: an app uses the IDFA if it depends on
# `google_mobile_ads`, which docs/release-readiness.json records per app from
# the app's own pubspec. 11 of 43 do.
#
# For those 11 this only sets the flag. Apple also wants an idfaDeclaration —
# which of serving ads, attributing installs or attributing actions applies —
# and that is a separate resource; if it is missing the submission will say so
# specifically, which is a better error than the one above.

require "json"
require "net/http"
require "uri"
require "spaceship"
require_relative "../agl_paths"

DRY  = ARGV.include?("--dry-run")
ONLY = ARGV.reject { |a| a.start_with?("--") }

tok = Spaceship::ConnectAPI::Token.create(
  key_id: ENV.fetch("ASC_KEY_ID"),
  issuer_id: ENV.fetch("ASC_ISSUER_ID"),
  filepath: ENV.fetch("ASC_KEY_PATH"),
)
Spaceship::ConnectAPI.token = tok

def request(tok, verb, path, body = nil)
  uri = URI("https://api.appstoreconnect.apple.com/#{path}")
  http = Net::HTTP.new(uri.host, 443)
  http.use_ssl = true
  req = (verb == :patch ? Net::HTTP::Patch : Net::HTTP::Get).new(uri)
  req["Authorization"] = "Bearer #{tok.text}"
  req["Content-Type"] = "application/json"
  req.body = body.to_json if body
  res = http.request(req)
  [res.code.to_i, (JSON.parse(res.body) rescue {})]
end

manifest = JSON.parse(File.read(File.join(AglPaths::MANIFEST, "apps.json")))["apps"]
ready = JSON.parse(File.read(File.join(AglPaths::MANIFEST, "docs/release-readiness.json")))
uses_ads = ready.each_with_object({}) { |r, h| h[r["repo"]] = !!r["dep_google_mobile_ads"] }

by_bundle = {}
Spaceship::ConnectAPI::App.all.each { |a| by_bundle[a.bundle_id] = a }

changed = skipped = failed = 0
manifest.each do |a|
  repo = a["repo"]
  next if ONLY.any? && !ONLY.include?(repo)

  app = by_bundle[a["bundle_id"]]
  next unless app
  version = begin
    app.get_app_store_versions(filter: { platform: "IOS" }).first
  rescue StandardError
    nil
  end
  next unless version

  wanted = uses_ads.fetch(repo, false)
  _, current = request(tok, :get, "v1/appStoreVersions/#{version.id}")
  now = current.dig("data", "attributes", "usesIdfa")

  if now == wanted
    skipped += 1
    next
  end

  if DRY
    puts format("%-18s usesIdfa %s -> %s (dry run)", repo, now.inspect, wanted)
    changed += 1
    next
  end

  code, body = request(tok, :patch, "v1/appStoreVersions/#{version.id}",
                       { data: { type: "appStoreVersions", id: version.id,
                                 attributes: { usesIdfa: wanted } } })
  if code < 300
    puts format("%-18s usesIdfa = %s", repo, wanted)
    changed += 1
  else
    detail = body.dig("errors", 0, "detail") || body.dig("errors", 0, "title") || code
    puts format("%-18s FAILED %s", repo, detail.to_s[0, 130])
    failed += 1
  end
end

puts "\nset #{changed}, already correct #{skipped}, failed #{failed}"
