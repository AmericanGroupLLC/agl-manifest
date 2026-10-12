#!/usr/bin/env ruby
# What TestFlight actually recorded for each app: builds, testers, installs,
# sessions and feedback. READ-ONLY — every request below is a GET, and the
# helper cannot issue anything else.
#
#   source scripts/testflight/env.sh
#   bundle exec ruby scripts/testflight/beta_evidence.rb            # all apps
#   bundle exec ruby scripts/testflight/beta_evidence.rb AeroSwift  # some
#
# Written for question 4 of Apple's Guideline 4.3 / 4.2.6 questionnaire ("what
# beta testing did you conduct ... examples of user feedback applied"). The
# reply drafted by differentiation_scaffold.py quotes this file, so the answer
# starts from what Apple's own records say rather than from memory. Apple can
# see these same numbers; a reply that contradicts them is worse than none.
#
# Writes docs/beta-evidence.json (committed, measured — re-run, never edit).
# A request Apple refuses is recorded with its exact status and detail under
# the app's "refused" list instead of being skipped silently.
#
# Endpoints (all GET):
#   v1/apps                                         bundle id -> app id
#   v1/builds?filter[app]=                          builds + buildBetaDetail
#   v1/apps/{id}/betaGroups                         groups
#   v1/betaGroups/{id}/betaTesters                  members and their state
#   v1/builds/{id}/metrics/betaBuildUsages          installs/sessions/crashes/feedback per build
#   v1/apps/{id}/betaFeedbackScreenshotSubmissions  tester feedback with screenshot
#   v1/apps/{id}/betaFeedbackCrashSubmissions       tester crash feedback
#   v1/betaAppReviewSubmissions?filter[build]=      Beta App Review submissions
#
# No tester email, name or id is written out — only counts.

require "json"
require "net/http"
require "time"
require "uri"
require "spaceship"
require_relative "../agl_paths"

ONLY = ARGV.reject { |a| a.start_with?("--") }
HOST = "https://api.appstoreconnect.apple.com"
TOKEN = Spaceship::ConnectAPI::Token.create(
  key_id: ENV.fetch("ASC_KEY_ID"), issuer_id: ENV.fetch("ASC_ISSUER_ID"),
  filepath: ENV.fetch("ASC_KEY_PATH"))

# GET only. There is deliberately no verb parameter: this account is under a
# Guideline 5.6 freeze (MA-043) and this script must not be able to change it.
def get(path)
  uri = URI(path.start_with?("http") ? path : "#{HOST}/#{path}")
  r = Net::HTTP::Get.new(uri)
  r["Authorization"] = "Bearer #{TOKEN.text}"
  res = Net::HTTP.start(uri.host, 443, use_ssl: true, read_timeout: 120) { |h| h.request(r) }
  [res.code.to_i, (JSON.parse(res.body) rescue { "raw" => res.body.to_s[0, 300] })]
end

# Follows links.next; returns [data, included, refusal-or-nil].
def get_all(path)
  data, included = [], []
  url = path
  while url
    code, body = get(url)
    unless code == 200
      err = (body["errors"] || [{}]).first
      return [data, included, { "path" => path.sub(HOST + "/", ""), "status" => code,
                                "code" => err["code"], "detail" => err["detail"] || body["raw"] }]
    end
    data.concat(body["data"] || [])
    included.concat(body["included"] || [])
    url = body.dig("links", "next")
  end
  [data, included, nil]
end

def tally(list)
  list.each_with_object(Hash.new(0)) { |x, h| h[x.to_s] += 1 }.sort.to_h
end

apps = JSON.parse(File.read(File.join(AglPaths::MANIFEST, "apps.json")))["apps"]
apps = apps.select { |a| ONLY.include?(a["repo"]) } if ONLY.any?

records, _inc, refusal = get_all("v1/apps?limit=200&fields[apps]=name,bundleId")
abort "v1/apps refused: #{refusal.inspect}" if refusal
by_bid = records.each_with_object({}) { |r, h| h[r.dig("attributes", "bundleId")] = r }

rows = apps.map do |a|
  repo = a["repo"]
  rec = by_bid[a["bundle_id"]]
  next({ "repo" => repo, "bundle_id" => a["bundle_id"], "app_store_record" => false }) unless rec

  id = rec["id"]
  refused = []

  builds, inc, ref = get_all("v1/builds?filter[app]=#{id}&limit=200" \
    "&fields[builds]=version,uploadedDate,processingState,expired" \
    "&include=buildBetaDetail&fields[buildBetaDetails]=internalBuildState,externalBuildState")
  refused << ref if ref
  detail = inc.select { |x| x["type"] == "buildBetaDetails" }.each_with_object({}) { |x, h| h[x["id"]] = x["attributes"] }
  dates = builds.map { |b| b.dig("attributes", "uploadedDate") }.compact.sort

  usage = Hash.new(0)
  per_build = builds.map do |b|
    _c, body = get("v1/builds/#{b["id"]}/metrics/betaBuildUsages")
    vals = {}
    if _c == 200
      (body["data"] || []).each { |d| (d["dataPoints"] || []).each { |p| (p["values"] || {}).each { |k, v| vals[k] = vals.fetch(k, 0) + v.to_i } } }
      vals.each { |k, v| usage[k] += v }
    else
      err = (body["errors"] || [{}]).first
      refused << { "path" => "v1/builds/{id}/metrics/betaBuildUsages", "status" => _c,
                   "code" => err["code"], "detail" => err["detail"] }
    end
    bd = detail[b["id"]] || {}
    { "version" => b.dig("attributes", "version"),
      "uploaded" => b.dig("attributes", "uploadedDate"),
      "processing_state" => b.dig("attributes", "processingState"),
      "expired" => b.dig("attributes", "expired"),
      "internal_state" => bd["internalBuildState"],
      "external_state" => bd["externalBuildState"],
      "usage" => vals }
  end.sort_by { |b| b["uploaded"].to_s }

  groups, _i, ref = get_all("v1/apps/#{id}/betaGroups?limit=200&fields[betaGroups]=name,isInternalGroup,publicLinkEnabled,createdDate")
  refused << ref if ref
  seen = {}
  internal_ids = {}
  group_rows = groups.map do |g|
    members, _i2, r2 = get_all("v1/betaGroups/#{g["id"]}/betaTesters?limit=200&fields[betaTesters]=state,inviteType")
    refused << r2 if r2
    members.each { |m| seen[m["id"]] = m.dig("attributes", "state") }
    members.each { |m| internal_ids[m["id"]] = true } if g.dig("attributes", "isInternalGroup")
    { "name" => g.dig("attributes", "name"),
      "internal" => g.dig("attributes", "isInternalGroup"),
      "public_link" => g.dig("attributes", "publicLinkEnabled"),
      "created" => g.dig("attributes", "createdDate"),
      "testers" => members.size,
      "tester_states" => tally(members.map { |m| m.dig("attributes", "state") }) }
  end

  # Who generated the sessions: members of an internal group are App Store
  # Connect users of this account (i.e. us), everyone else is external.
  by_tester = { "internal_group_members" => Hash.new(0), "external_only" => Hash.new(0) }
  active = { "internal_group_members" => 0, "external_only" => 0 }
  tu, _it, rt = get_all("v1/apps/#{id}/metrics/betaTesterUsages?period=P365D&groupBy=betaTesters")
  refused << rt if rt
  tu.each do |d|
    tid = d.dig("dimensions", "betaTesters", "data", "id")
    side = internal_ids[tid] ? "internal_group_members" : "external_only"
    vals = Hash.new(0)
    (d["dataPoints"] || []).each { |p| (p["values"] || {}).each { |k, v| vals[k] += v.to_i } }
    vals.each { |k, v| by_tester[side][k] += v }
    active[side] += 1 if vals["sessionCount"].positive?
  end

  feedback = {}
  %w[betaFeedbackScreenshotSubmissions betaFeedbackCrashSubmissions].each do |rel|
    items, _i3, r3 = get_all("v1/apps/#{id}/#{rel}?limit=200")
    if r3
      refused << r3
      feedback[rel] = nil
    else
      feedback[rel] = items.size
    end
  end

  reviews = []
  builds.map { |b| b["id"] }.each_slice(50) do |ids|
    subs, _i4, r4 = get_all("v1/betaAppReviewSubmissions?limit=200&filter[build]=#{ids.join(",")}")
    refused << r4 if r4
    reviews.concat(subs.map { |s| s["attributes"] || {} })
  end

  row = {
    "repo" => repo, "bundle_id" => a["bundle_id"], "app_store_record" => true, "apple_id" => id,
    "builds" => {
      "count" => builds.size,
      "valid" => builds.count { |b| b.dig("attributes", "processingState") == "VALID" },
      "first_uploaded" => dates.first, "last_uploaded" => dates.last,
      "external_states" => tally(per_build.map { |b| b["external_state"] }),
      "internal_states" => tally(per_build.map { |b| b["internal_state"] }),
    },
    "beta_groups" => group_rows,
    "testers" => { "unique" => seen.size, "in_internal_groups" => internal_ids.size,
                   "states" => tally(seen.values) },
    "usage_all_builds" => usage.sort.to_h,
    "usage_by_tester_kind_365d" => by_tester.transform_values { |h| h.sort.to_h },
    "testers_with_sessions_365d" => active,
    "feedback_submissions" => {
      "screenshot" => feedback["betaFeedbackScreenshotSubmissions"],
      "crash" => feedback["betaFeedbackCrashSubmissions"],
    },
    "beta_app_review_submissions" => {
      "count" => reviews.size,
      "states" => tally(reviews.map { |r| r["betaReviewState"] }),
      "first_submitted" => reviews.map { |r| r["submittedDate"] }.compact.min,
      "last_submitted" => reviews.map { |r| r["submittedDate"] }.compact.max,
    },
    "per_build" => per_build,
    "refused" => refused.uniq,
  }
  puts format("%-18s builds=%-3d testers=%-3d installs=%-3s sessions=%-3s ext_sessions=%-3s feedback=%-3s shots=%s crashes=%s refused=%d",
              repo, builds.size, seen.size, usage["installCount"], usage["sessionCount"],
              by_tester["external_only"]["sessionCount"],
              usage["feedbackCount"], feedback["betaFeedbackScreenshotSubmissions"].inspect,
              feedback["betaFeedbackCrashSubmissions"].inspect, refused.uniq.size)
  row
end

out = File.join(AglPaths::MANIFEST, "docs", "beta-evidence.json")
doc = {
  "measured_at" => Time.now.utc.iso8601,
  "source" => "App Store Connect API, GET only (scripts/testflight/beta_evidence.rb)",
  "notes" => [
    "usage_all_builds sums betaBuildUsages over every build; Apple reports the last 365 days.",
    "testers.unique counts distinct tester records across all of the app's beta groups; states are the betaTesters resource's own state field.",
    "usage_by_tester_kind_365d splits betaTesterUsages (groupBy=betaTesters, P365D): internal_group_members are App Store Connect users of this account, external_only are everyone else.",
    "feedback_submissions counts betaFeedbackScreenshotSubmissions / betaFeedbackCrashSubmissions; null means the request was refused (see refused).",
  ],
  "apps" => rows,
}
if ONLY.any? && File.exist?(out)
  # A partial run updates only the apps it measured.
  old = JSON.parse(File.read(out))
  keep = (old["apps"] || []).reject { |r| ONLY.include?(r["repo"]) }
  doc["apps"] = (keep + rows).sort_by { |r| r["repo"].downcase }
end
File.write(out, JSON.pretty_generate(doc) + "\n")
puts "-> #{out}"
