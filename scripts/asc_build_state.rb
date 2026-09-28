#!/usr/bin/env ruby
# Ask App Store Connect which apps really have a build, and write the evidence
# file store_checklist.py reads.
#
# That file used to be a hand-appended log of what this machine had tried to
# upload. It drifted: AGrammarly and NewsBoard both carry VALID builds on
# App Store Connect and were still reported "no ASC record or not uploaded",
# because a local log records intent, not outcome. Apple is the only authority
# on what Apple has.
#
#   bundle exec ruby scripts/asc_build_state.rb
require "spaceship"
require "json"

Spaceship::ConnectAPI.token = Spaceship::ConnectAPI::Token.create(
  key_id: ENV.fetch("ASC_KEY_ID"), issuer_id: ENV.fetch("ASC_ISSUER_ID"),
  filepath: ENV.fetch("ASC_KEY_PATH"))

require_relative "agl_paths"
root  = AglPaths::ROOT
apps  = JSON.parse(File.read(File.join(root, "agl-manifest/apps.json")))["apps"].select { |a| a["flutter"] }
by_bid = {}
Spaceship::ConnectAPI::App.all.each { |a| by_bid[a.bundle_id] = a }

lines = []
apps.each do |a|
  repo, bid = a["repo"], a["bundle_id"]
  app = by_bid[bid]
  if app.nil?
    lines << "#{repo}|NO_RECORD|#{bid}"
    next
  end
  builds = begin
    Spaceship::ConnectAPI::Build.all(app_id: app.id, limit: 20)
  rescue StandardError => e
    warn "#{repo}: #{e.message.to_s[0, 120]}"
    []
  end
  # A build that failed processing is not a delivered build.
  usable = builds.reject { |b| b.processing_state == "FAILED" || b.processing_state == "INVALID" }
  if usable.empty?
    lines << "#{repo}|NO_BUILD|#{bid}"
  else
    newest = usable.max_by { |b| b.uploaded_date.to_s }
    lines << "#{repo}|UPLOADED|#{bid}|#{newest.version}|#{newest.processing_state}|#{newest.uploaded_date}"
  end
end

# Two homes, and the JSON one is the real one.
#
# This only ever wrote .sweep/asc_upload.psv, which lives outside the
# repository, is never committed, and so cannot be read on a runner or by
# anyone else. It went stale without saying so: store_checklist.py was reading
# a copy from 2026-09-25 and reporting 14 apps with no App Store build when
# Apple actually had 38 uploaded. Measured facts belong in docs/ and committed,
# which is the rule CLAUDE.md already states for everything else.
# Review state too. Nothing measured it, so it was argued about from memory —
# including by me, claiming nothing had been submitted when 36 of 43 had.
# Apple is the only authority, so ask it and commit the answer.
review = {}
apps.each do |a|
  app = by_bid[a["bundle_id"]]
  next if app.nil?
  begin
    v = app.get_app_store_versions(filter: { platform: "IOS" }).first
    review[a["repo"]] = v ? v.app_store_state.to_s : "NO_VERSION"
  rescue StandardError => e
    warn "#{a["repo"]}: review state unavailable (#{e.message.to_s[0, 80]})"
    review[a["repo"]] = "UNKNOWN"
  end
end

rows = lines.map do |l|
  repo, state, bundle, version, processing, uploaded = l.split("|")
  { "repo" => repo, "state" => state, "bundle_id" => bundle,
    "version" => version, "processing_state" => processing,
    "uploaded_at" => uploaded, "review_state" => review[repo] }
end
docs = File.expand_path(File.join(__dir__, "..", "docs", "asc-build-state.json"))
File.write(docs, JSON.pretty_generate(rows) + "\n")

legacy = File.join(root, ".sweep/asc_upload.psv")
File.write(legacy, lines.join("\n") + "\n") if File.directory?(File.dirname(legacy))

counts = lines.group_by { |l| l.split("|")[1] }.transform_values(&:size)
puts counts.map { |k, v| "#{k}=#{v}" }.join("  ")
puts "-> #{docs}"
