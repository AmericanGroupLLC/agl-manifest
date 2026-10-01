#!/usr/bin/env ruby
# Put each app's newest build in front of its testers.
#
#   source scripts/testflight/env.sh
#   bundle exec ruby scripts/testflight/distribute_builds.rb --dry-run
#   bundle exec ruby scripts/testflight/distribute_builds.rb
#   bundle exec ruby scripts/testflight/distribute_builds.rb AGCleaner
#
# Why this exists: a TestFlight link was answering "requested app not available
# or doesn't exist" for every app. Uploading a build does not distribute it.
# Checked on AGCleaner — build 202609250224, processing VALID, not expired:
#
#   groups this build is distributed to: 0
#   AGL Internal  testers 0
#   beta testers on the account: 416
#
# So the builds were fine, the testers existed, and nothing connected the two.
# A build in no group is invisible to every tester, which is exactly the error
# the link gives.
#
# This attaches the newest usable build to the app's internal group and makes
# sure the group has testers in it. Internal groups are used because they need
# no Beta App Review: an external group would sit at
# READY_FOR_BETA_SUBMISSION, which is where these apps already are.

require "json"
require "set"
require "spaceship"
require_relative "../agl_paths"

DRY  = ARGV.include?("--dry-run")
ONLY = ARGV.reject { |a| a.start_with?("--") }
GROUP = "AGL Internal"

Spaceship::ConnectAPI.token = Spaceship::ConnectAPI::Token.create(
  key_id: ENV.fetch("ASC_KEY_ID"),
  issuer_id: ENV.fetch("ASC_ISSUER_ID"),
  filepath: ENV.fetch("ASC_KEY_PATH"),
)

apps = JSON.parse(File.read(File.join(AglPaths::MANIFEST, "apps.json")))["apps"]
by_bundle = {}
Spaceship::ConnectAPI::App.all.each { |a| by_bundle[a.bundle_id] = a }

# Everyone already known to the account, so the same people get every app
# rather than a per-app list that drifts.
account_testers = begin
  Spaceship::ConnectAPI::BetaTester.all(limit: 200)
rescue StandardError => e
  warn "could not list testers: #{e.message[0, 120]}"
  []
end
emails = account_testers.map(&:email).compact.uniq
puts "account testers: #{emails.size} unique"

distributed = added = skipped = failed = 0

apps.each do |a|
  repo = a["repo"]
  next if ONLY.any? && !ONLY.include?(repo)
  app = by_bundle[a["bundle_id"]]
  next unless app

  build = begin
    Spaceship::ConnectAPI::Build.all(app_id: app.id, limit: 10)
      .reject { |b| b.expired || %w[FAILED INVALID PROCESSING].include?(b.processing_state.to_s) }
      .max_by { |b| b.uploaded_date.to_s }
  rescue StandardError
    nil
  end
  if build.nil?
    puts format("%-18s no usable build", repo)
    skipped += 1
    next
  end

  group = (app.get_beta_groups rescue []).find { |g| g.name == GROUP && g.is_internal_group }
  group ||= (app.get_beta_groups rescue []).find(&:is_internal_group)
  if group.nil?
    puts format("%-18s no internal beta group", repo)
    skipped += 1
    next
  end

  already = (build.get_beta_groups rescue []).map(&:id).to_set
  in_group = (group.get_beta_testers rescue []).map(&:email).compact.to_set
  want = emails.reject { |e| in_group.include?(e) }

  if DRY
    puts format("%-18s build %s -> %s%s", repo, build.version,
                already.include?(group.id) ? "already distributed" : "attach",
                want.empty? ? "" : ", add #{want.size} tester(s)")
    next
  end

  unless already.include?(group.id)
    begin
      Spaceship::ConnectAPI.add_beta_groups_to_build(build_id: build.id,
                                                     beta_group_ids: [group.id])
      distributed += 1
    rescue StandardError => e
      puts format("%-18s attach FAILED %s", repo, e.message.gsub(/\s+/, " ")[0, 110])
      failed += 1
      next
    end
  end

  unless want.empty?
    begin
      # In batches: the bulk endpoint rejects very large payloads.
      want.each_slice(50) do |slice|
        Spaceship::ConnectAPI.post_bulk_beta_tester_assignments(
          beta_group_id: group.id,
          beta_testers: slice.map { |e| { email: e } },
        )
      end
      added += want.size
    rescue StandardError => e
      puts format("%-18s testers FAILED %s", repo, e.message.gsub(/\s+/, " ")[0, 110])
    end
  end

  puts format("%-18s build %s in %s, group has %d tester(s)",
              repo, build.version, group.name, in_group.size + want.size)
end

puts "\nattached #{distributed} build(s), added #{added} tester assignment(s), " \
     "skipped #{skipped}, failed #{failed}"
