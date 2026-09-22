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

root  = "/Users/spatchava/agl"
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

out = File.join(root, ".sweep/asc_upload.psv")
File.write(out, lines.join("\n") + "\n")
counts = lines.group_by { |l| l.split("|")[1] }.transform_values(&:size)
puts counts.map { |k, v| "#{k}=#{v}" }.join("  ")
puts "-> #{out}"
