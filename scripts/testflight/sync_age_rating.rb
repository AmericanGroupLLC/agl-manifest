#!/usr/bin/env ruby
# Make Apple's age-rating answers agree with what the app actually ships.
#
#   source scripts/testflight/env.sh
#   bundle exec ruby scripts/testflight/sync_age_rating.rb --dry-run
#   bundle exec ruby scripts/testflight/sync_age_rating.rb
#   bundle exec ruby scripts/testflight/sync_age_rating.rb DriftDate iMaps
#
# Two sources, no invention:
#
#   * `advertising` is derived, not configured. An app depends on
#     google_mobile_ads or it does not, and docs/release-readiness.json already
#     measures that. Declaring "no advertising" while shipping the AdMob SDK is
#     a misdeclaration, and it was true of five apps when this was written.
#   * everything else comes from store/age-rating.json, where each entry has to
#     cite the file that makes it true.
#
# Idempotent: the live declaration is read first and a PATCH is only sent for
# fields whose value actually differs, so a second run reports no changes.
#
# Contrary to what the checklist used to claim, this needs no Apple ID session.
# ageRatingDeclarations is part of the public App Store Connect API and the
# team's API key can read and write it. (App *Privacy* answers are the ones
# that genuinely require a web session - see MA-022.)
require "json"
require "spaceship"

ROOT = "/Users/spatchava/agl"
M = "#{ROOT}/agl-manifest"
DRY = ARGV.include?("--dry-run")
ONLY = ARGV.reject { |a| a.start_with?("--") }

apps = JSON.parse(File.read("#{M}/apps.json"))["apps"]
apps = apps.select { |a| ONLY.include?(a["repo"]) } unless ONLY.empty?

overrides = JSON.parse(File.read("#{M}/store/age-rating.json")).reject { |k, _| k.start_with?("_") }

readiness = JSON.parse(File.read("#{M}/docs/release-readiness.json"))
readiness = readiness["apps"] if readiness.is_a?(Hash) && readiness["apps"]
ships_ads = readiness.each_with_object({}) { |r, h| h[r["repo"]] = !!r["dep_google_mobile_ads"] }

Spaceship::ConnectAPI.token = Spaceship::ConnectAPI::Token.create(
  key_id: ENV.fetch("ASC_KEY_ID"),
  issuer_id: ENV.fetch("ASC_ISSUER_ID"),
  filepath: ENV.fetch("ASC_KEY_PATH")
)

results = {}
changed = 0
skipped = 0

apps.each do |a|
  repo = a["repo"]
  begin
    app = Spaceship::ConnectAPI::App.find(a["bundle_id"])
    unless app
      puts "#{repo.ljust(18)} no ASC record"
      results[repo] = { "state" => "no-asc-record" }
      next
    end

    info = app.fetch_edit_app_info || app.fetch_latest_app_info
    decl = info&.fetch_age_rating_declaration
    unless decl
      puts "#{repo.ljust(18)} no age rating declaration"
      results[repo] = { "state" => "no-declaration" }
      next
    end

    # Derived first, then the cited per-app overrides on top.
    want = { "advertising" => ships_ads.fetch(repo, false) }
    (overrides[repo] || {}).each { |k, v| want[k] = v unless k.start_with?("_") }

    diff = want.reject { |field, value| decl.send(field) == value }

    if diff.empty?
      puts "#{repo.ljust(18)} already correct"
      results[repo] = { "state" => "already-correct", "rating" => info.app_store_age_rating }
      skipped += 1
      next
    end

    shown = diff.map { |f, v| "#{f}: #{decl.send(f).inspect} -> #{v.inspect}" }.join(", ")
    if DRY
      puts "#{repo.ljust(18)} WOULD SET #{shown}"
      results[repo] = { "state" => "would-change", "diff" => diff }
      next
    end

    decl.update(attributes: diff)

    # Read back rather than trusting the write.
    after = (app.fetch_edit_app_info || app.fetch_latest_app_info)&.fetch_age_rating_declaration
    bad = diff.reject { |field, value| after.send(field) == value }
    if bad.empty?
      puts "#{repo.ljust(18)} SET #{shown}  (rating now #{after ? (app.fetch_edit_app_info || app.fetch_latest_app_info)&.app_store_age_rating : '?'})"
      results[repo] = { "state" => "updated", "diff" => diff }
      changed += 1
    else
      puts "#{repo.ljust(18)} WROTE BUT DID NOT STICK: #{bad.keys.join(', ')}"
      results[repo] = { "state" => "verify-failed", "not_applied" => bad }
    end
  rescue => e
    msg = e.message.lines.first.to_s.strip
    puts "#{repo.ljust(18)} FAILED #{msg[0, 120]}"
    results[repo] = { "state" => "failed", "error" => msg[0, 300] }
  end
end

out = "#{ROOT}/.dist/age-rating-sync.json"
File.write(out, JSON.pretty_generate(results))
puts
puts "#{changed} updated, #{skipped} already correct -> #{out}"
