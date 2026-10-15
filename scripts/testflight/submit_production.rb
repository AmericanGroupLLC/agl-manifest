#!/usr/bin/env ruby
# Take every eligible app as far towards App Store release as an API key can:
# attach the newest valid build to the version, open a review submission, add
# the version to it, and submit.
#
# The last step is refused account-wide until a person publishes the App Privacy
# answers ("You must have published answers to your app's data usages").
# Verified 2026-09-22 on AGStudio, RoomCraft and WiFiTrail; the endpoints that
# would set those answers (v1/appDataUsages, dataUsagePublishState) do not exist
# for an API key, only for an Apple ID web session. Everything before that step
# is done here, so once the answers are published this script finishes the job.
#
#   bundle exec ruby submit_production.rb            # every app with a record
#   bundle exec ruby submit_production.rb --dry-run  # attach builds, do not submit
#   bundle exec ruby submit_production.rb AGStudio
require "json"
require "spaceship"

DRY = ARGV.include?("--dry-run")
ONLY = ARGV.reject { |x| x.start_with?("--") }
require_relative "account_freeze"
AccountFreeze.enforce!(ARGV) unless DRY
# Decision log 2026-10-15: Stage B + the submission hold, for the exact build
# that would go to review. No override flag on purpose.
require_relative "submission_gate"

Spaceship::ConnectAPI.token = Spaceship::ConnectAPI::Token.create(
  key_id: ENV.fetch("ASC_KEY_ID"), issuer_id: ENV.fetch("ASC_ISSUER_ID"), filepath: ENV.fetch("ASC_KEY_PATH"))

require_relative "../agl_paths"
apps = JSON.parse(File.read(File.join(AglPaths::MANIFEST, "apps.json")))["apps"]
# store_eligible is still honoured so the manifest can exclude an app, but
# nothing sets it false any more: all 43 are in scope. This comment used to
# say the portfolio was 42.
apps = ONLY.empty? ? apps.select { |a| a["store_eligible"] != false } : apps.select { |a| ONLY.include?(a["repo"]) }
out = {}

apps.each do |a|
  repo = a["repo"]
  app = Spaceship::ConnectAPI::App.find(a["bundle_id"]) rescue nil
  (out[repo] = { "status" => "no-record" }; next) if app.nil?

  ver = Spaceship::ConnectAPI.get_app_store_versions(app_id: app.id, limit: 1).to_models.first
  (out[repo] = { "status" => "no-version" }; puts("#{repo}: no App Store version"); next) if ver.nil?
  if %w[READY_FOR_SALE IN_REVIEW WAITING_FOR_REVIEW PENDING_DEVELOPER_RELEASE].include?(ver.app_store_state)
    out[repo] = { "status" => ver.app_store_state }
    puts "#{repo}: already #{ver.app_store_state}"
    next
  end

  build = Spaceship::ConnectAPI::Build.all(app_id: app.id, sort: "-uploadedDate", limit: 1)
                                      .find { |b| b.processing_state == "VALID" }
  (out[repo] = { "status" => "no-valid-build" }; puts("#{repo}: no processed build"); next) if build.nil?

  # Before anything changes on App Store Connect (attaching included): the
  # build that would be submitted must pass gate_for_submission.
  gate_ok, gate_msg = SubmissionGate.check(repo, build.version, build.uploaded_date)
  unless gate_ok || DRY
    out[repo] = { "status" => "refused-by-gate", "build" => build.version, "detail" => gate_msg }
    puts "#{repo}: NOT SUBMITTED — #{gate_msg}"
    next
  end

  begin
    ver.select_build(build_id: build.id)
    attached = true
  rescue StandardError => e
    attached = e.message.include?("already") ? true : false
    puts "#{repo}: attach build: #{e.message.gsub(/\s+/, ' ')[0, 140]}" unless attached
  end

  if DRY
    out[repo] = { "status" => "build-attached", "build" => build.version, "version" => ver.version_string,
                  "gate" => gate_msg }
    puts "#{repo}: build #{build.version} on version #{ver.version_string} (dry run, not submitted); gate: #{gate_msg}"
    next
  end
  # The gate passed for `build`; if it is not the one attached, the version
  # would go to review with another (unchecked) build.
  unless attached
    out[repo] = { "status" => "refused-by-gate", "build" => build.version,
                  "detail" => "build #{build.version} could not be attached to the version" }
    puts "#{repo}: NOT SUBMITTED — build #{build.version} could not be attached; the version holds another build"
    next
  end

  begin
    existing = (Spaceship::ConnectAPI.get_review_submissions(app_id: app.id).to_models rescue [])

    # A rejected app's version stays attached to the submission that carried it,
    # which sits in UNRESOLVED_ISSUES. A new submission cannot take that version
    # ("Item is already present in another reviewSubmission"), and the symptom
    # further down is the misleading "must have an approved appStoreVersions".
    # The way back in is to resubmit that same submission once the issues are
    # addressed, which is what the console's Submit for Review does.
    if (stuck = existing.find { |s| s.state == "UNRESOLVED_ISSUES" })
      begin
        Spaceship::ConnectAPI.patch_review_submission(review_submission_id: stuck.id,
                                                      attributes: { submitted: true })
        out[repo] = { "status" => "resubmitted", "submission" => stuck.id, "build" => build.version }
        SubmissionGate.record!(repo, build.version, "resubmitted", "submit_production.rb")
        puts "#{repo}: RESUBMITTED the rejected submission"
        next
      rescue StandardError => e
        msg = e.message.gsub(/\s+/, " ")
        out[repo] = { "status" => "blocked", "blocker" => msg[0, 300] }
        puts "#{repo}: cannot resubmit yet — #{msg[/Version is not ready[^.]*/] || msg[0, 160]}"
        next
      end
    end

    sub = begin
      Spaceship::ConnectAPI.post_review_submission(app_id: app.id, platform: "IOS").to_models.first
    rescue StandardError
      existing.find { |s| s.state == "READY_FOR_REVIEW" }
    end
    raise "no review submission could be opened" if sub.nil?
    begin
      Spaceship::ConnectAPI.post_review_submission_item(review_submission_id: sub.id, app_store_version_id: ver.id)
    rescue StandardError => e
      # Already present is fine; anything else must not be hidden, or the submit
      # below fails with a confusing "must include an appStoreVersions" error.
      raise unless e.message =~ /already|duplicate|exists/i
    end
    Spaceship::ConnectAPI.patch_review_submission(review_submission_id: sub.id, attributes: { submitted: true })
    out[repo] = { "status" => "submitted", "build" => build.version, "version" => ver.version_string }
    SubmissionGate.record!(repo, build.version, "submitted", "submit_production.rb")
    puts "#{repo}: SUBMITTED FOR APP STORE REVIEW (build #{build.version})"
  rescue StandardError => e
    msg = e.message.gsub(/\s+/, ' ')
    blocker = msg[/data usages/] ? "app-privacy-answers-not-published" : msg[0, 700]
    out[repo] = { "status" => "blocked", "blocker" => blocker, "build" => build.version, "attached" => attached }
    puts "#{repo}: blocked — #{blocker}"
  end
end

File.write(File.join(AglPaths::DIST, "appstore-submit-results.json"), JSON.pretty_generate(out))
counts = out.values.group_by { |v| v["status"] }.transform_values(&:size)
puts "\n#{counts.map { |k, v| "#{k}: #{v}" }.join('  ')}"
puts "-> #{File.join(AglPaths::DIST, "appstore-submit-results.json")}"
