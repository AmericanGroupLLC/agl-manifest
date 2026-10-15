# Resubmit a rejected review submission IN PLACE — the API form of App Store
# Connect's "Resubmit to App Review": mark each REJECTED item resolved, then set
# the same submission submitted. Never cancels (cancelling discards Apple's
# rejection thread and the founder's Resolution Center replies — what
# resubmit_rejected.rb did on 2026-10-02).
#
#   source scripts/testflight/env.sh
#   bundle exec ruby scripts/testflight/resolve_and_resubmit.rb --dry-run AeroSwift
#   bundle exec ruby scripts/testflight/resolve_and_resubmit.rb --override-account-freeze AeroSwift …
#
# Founder decision 2026-10-14: resubmit the 41 rejected apps after replying in
# Resolution Center. submit_production.rb's PATCH submitted:true alone answers
# "Version is not ready to be submitted yet" while an item is REJECTED/unresolved.
require "json"; require "net/http"; require "spaceship"; require "uri"
require_relative "../agl_paths"
require_relative "account_freeze"
# Decision log 2026-10-15: Stage B + the submission hold, for the build the
# rejected version carries. On 2026-10-14 this script resubmitted 35 OLD
# binaries in place; all came back 4.3(a). No override flag on purpose.
require_relative "submission_gate"
DRY = ARGV.include?("--dry-run")
ONLY = ARGV.reject { |a| a.start_with?("--") }
AccountFreeze.enforce!(ARGV) unless DRY
TOKEN = Spaceship::ConnectAPI::Token.create(key_id: ENV.fetch("ASC_KEY_ID"), issuer_id: ENV.fetch("ASC_ISSUER_ID"), filepath: ENV.fetch("ASC_KEY_PATH"))
def req(verb, path, body = nil)
  u = URI("https://api.appstoreconnect.apple.com/#{path}")
  r = { get: Net::HTTP::Get, patch: Net::HTTP::Patch }[verb].new(u)
  r["Authorization"] = "Bearer #{TOKEN.text}"; r["Content-Type"] = "application/json"; r.body = body.to_json if body
  res = Net::HTTP.start(u.host, 443, use_ssl: true, read_timeout: 120) { |h| h.request(r) }
  [res.code.to_i, (JSON.parse(res.body) rescue {})]
end
# Apple's 409 says only "check associated errors"; the reasons are in meta.associatedErrors.
def why(b)
  (b["errors"] || [{}]).flat_map do |e|
    assoc = (e.dig("meta", "associatedErrors") || {}).flat_map { |path, list| list.map { |x| "#{path.split('/').last(2).join('/')}: #{x['code']} #{x['detail']}" } }
    [e["detail"] || e["title"], *assoc]
  end.compact.join("; ")
end
apps = JSON.parse(File.read(File.join(AglPaths::MANIFEST, "apps.json")))["apps"].select { |a| ONLY.empty? || ONLY.include?(a["repo"]) }
out = {}
apps.each do |a|
  repo = a["repo"]
  _, ap = req(:get, "v1/apps?filter[bundleId]=#{a['bundle_id']}"); app = (ap["data"] || [])[0]
  next (out[repo] = { "status" => "no_app" }) unless app
  _, s = req(:get, "v1/apps/#{app['id']}/reviewSubmissions?limit=10")
  sub = (s["data"] || []).find { |x| x.dig("attributes", "state") == "UNRESOLVED_ISSUES" }
  next (puts("#{repo}: no UNRESOLVED_ISSUES submission"); out[repo] = { "status" => "nothing_to_resubmit" }) unless sub
  _, it = req(:get, "v1/reviewSubmissions/#{sub['id']}/items?include=appStoreVersion")
  rejected = (it["data"] || []).select { |i| i.dig("attributes", "state") == "REJECTED" && !i.dig("attributes", "resolved") }
  # Resubmitting in place sends whatever build the version holds — find it and gate it.
  vid = (it["data"] || []).map { |i| i.dig("relationships", "appStoreVersion", "data", "id") }.compact.first
  bc, bb = vid ? req(:get, "v1/appStoreVersions/#{vid}/build") : [0, {}]
  build_no = bb.dig("data", "attributes", "version")
  gate_ok, gate_msg = build_no ? SubmissionGate.check(repo, build_no, bb.dig("data", "attributes", "uploadedDate"))
                               : [false, "#{repo}: no build found on the rejected version (#{vid ? "HTTP #{bc}" : 'no appStoreVersion item'})"]
  if DRY
    puts "#{repo}: would resolve #{rejected.size} item(s) and resubmit #{sub['id'][0, 8]} with build #{build_no}; gate: #{gate_msg}"
    out[repo] = { "status" => "dry_run", "build" => build_no, "gate" => gate_msg }; next
  end
  unless gate_ok
    puts "#{repo}: NOT RESUBMITTED — #{gate_msg}"
    out[repo] = { "status" => "refused-by-gate", "build" => build_no, "detail" => gate_msg }; next
  end
  errs = []
  rejected.each do |i|
    c, b = req(:patch, "v1/reviewSubmissionItems/#{i['id']}", { data: { type: "reviewSubmissionItems", id: i["id"], attributes: { resolved: true } } })
    errs << "resolve #{c} #{why(b)}" unless c.between?(200, 299)
  end
  c, b = req(:patch, "v1/reviewSubmissions/#{sub['id']}", { data: { type: "reviewSubmissions", id: sub["id"], attributes: { submitted: true } } })
  if c.between?(200, 299)
    puts "#{repo}: RESUBMITTED in place (#{sub['id'][0, 8]}, state #{b.dig('data', 'attributes', 'state')})"; out[repo] = { "status" => "resubmitted", "submission" => sub["id"], "build" => build_no }
    SubmissionGate.record!(repo, build_no, "resubmitted", "resolve_and_resubmit.rb")
  else
    d = why(b)
    puts "#{repo}: refused #{c} — #{d}#{errs.any? ? " (#{errs.join(', ')})" : ''}"; out[repo] = { "status" => "refused", "code" => c, "detail" => d, "item_errors" => errs }
  end
end
File.write(File.join(AglPaths::DIST, "appstore-resubmit-in-place.json"), JSON.pretty_generate(out))
puts "\n" + out.values.group_by { |v| v["status"] }.map { |k, v| "#{k}: #{v.size}" }.join("  ")
