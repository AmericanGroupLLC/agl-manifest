#!/usr/bin/env ruby
# Delete review submissions that were prepared and never sent.
#
#   source scripts/testflight/env.sh
#   FASTLANE_USER=srikanth.patchava@outlook.com \
#     bundle exec ruby scripts/testflight/clear_stale_submissions.rb --dry-run
#   FASTLANE_USER=... bundle exec ruby scripts/testflight/clear_stale_submissions.rb
#
# A submission left in READY_FOR_REVIEW with no submittedDate holds its app
# store version, so nothing else can be submitted for that app. They accumulate
# from any attempt that creates a submission and then fails before sending it.
#
# The public API will not remove them:
#
#   DELETE /v1/reviewSubmissions/{id}   403  does not allow 'DELETE'
#   PATCH  {"canceled": true}           409  Resource is not in cancellable state
#
# The iris host behind App Store Connect will, given an Apple ID session:
#
#   DELETE iris/v1/reviewSubmissions/{id}  204
#
# Only un-sent READY_FOR_REVIEW submissions are touched.
#
# This used to add that an UNRESOLVED_ISSUES submission "returns 409 here too
# and is released by replying in Resolution Center, not by deletion". That is
# no longer true: measured on 2026-10-01, PATCH {"canceled": true} against a
# real UNRESOLVED_ISSUES submission answers 200 and the app submits again
# once it settles. resubmit_rejected.rb does that, and it freed 24 apps.

require "json"
require "spaceship"
require_relative "../agl_paths"

DRY  = ARGV.include?("--dry-run")
ONLY = ARGV.reject { |a| a.start_with?("--") }

Spaceship::Tunes.login(ENV.fetch("FASTLANE_USER", "srikanth.patchava@outlook.com"))
Spaceship::ConnectAPI.token = Spaceship::ConnectAPI::Token.create(
  key_id: ENV.fetch("ASC_KEY_ID"),
  issuer_id: ENV.fetch("ASC_ISSUER_ID"),
  filepath: ENV.fetch("ASC_KEY_PATH"),
)
tunes = Spaceship::Tunes.client

apps = JSON.parse(File.read(File.join(AglPaths::MANIFEST, "apps.json")))["apps"]
by_bundle = {}
Spaceship::ConnectAPI::App.all.each { |a| by_bundle[a.bundle_id] = a }

deleted = kept = failed = 0
apps.each do |a|
  repo = a["repo"]
  next if ONLY.any? && !ONLY.include?(repo)
  app = by_bundle[a["bundle_id"]]
  next unless app

  subs = begin
    Spaceship::ConnectAPI.get_review_submissions(app_id: app.id).to_models
  rescue StandardError
    []
  end
  stale = subs.select { |s| s.state == "READY_FOR_REVIEW" && s.submitted_date.to_s.empty? }
  next if stale.empty?

  stale.each do |s|
    if DRY
      puts format("%-18s would delete %s", repo, s.id[0, 8])
      deleted += 1
      next
    end
    begin
      r = tunes.request(:delete) do |req|
        req.url "https://appstoreconnect.apple.com/iris/v1/reviewSubmissions/#{s.id}"
      end
      if r.status.to_i < 300
        puts format("%-18s deleted %s", repo, s.id[0, 8])
        deleted += 1
      else
        puts format("%-18s HTTP %s on %s", repo, r.status, s.id[0, 8])
        failed += 1
      end
    rescue StandardError => e
      puts format("%-18s failed %s — %s", repo, s.id[0, 8], e.message.gsub(/\s+/, " ")[0, 110])
      failed += 1
    end
  end
  kept += subs.count { |s| s.state == "UNRESOLVED_ISSUES" }
end

puts "\ndeleted #{deleted}, failed #{failed}; " \
     "#{kept} rejected submission(s) left alone — those need a Resolution Center reply"
