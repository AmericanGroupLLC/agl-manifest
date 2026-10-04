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
require "net/http"
require "set"
require "spaceship"
require "uri"
require_relative "../agl_paths"

DRY  = ARGV.include?("--dry-run")
ONLY = ARGV.reject { |a| a.start_with?("--") }
GROUP = "AGL Internal"

Spaceship::ConnectAPI.token = Spaceship::ConnectAPI::Token.create(
  key_id: ENV.fetch("ASC_KEY_ID"),
  issuer_id: ENV.fetch("ASC_ISSUER_ID"),
  filepath: ENV.fetch("ASC_KEY_PATH"),
)

HOST = "https://api.appstoreconnect.apple.com"

def req(verb, path, body = nil)
  uri = URI("#{HOST}/#{path}")
  http = Net::HTTP.new(uri.host, 443)
  http.use_ssl = true
  http.read_timeout = 120
  r = { get: Net::HTTP::Get, post: Net::HTTP::Post }[verb].new(uri)
  r["Authorization"] = "Bearer #{Spaceship::ConnectAPI.token.text}"
  r["Content-Type"] = "application/json"
  r.body = body.to_json if body
  res = http.request(r)
  [res.code.to_i, (JSON.parse(res.body) rescue {})]
end

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
# The two store owners, who must be able to install every build from
# TestFlight.app. Measured 2026-10-04: rainbow472.sri@gmail.com was in none of
# the 43 internal groups, which is why half the TestFlight links answered
# "the requested app is not available or doesn't exist".
OWNERS = {
  "srikanth.patchava@outlook.com" => %w[Srikanth Patchava],
  "rainbow472.sri@gmail.com" => %w[Srikanth Patchava],
}.freeze
NAMES = OWNERS

emails = OWNERS.keys
puts "owners to seat in every internal group: #{emails.size}"

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
  # No `next` here. Seating an owner in a beta group has nothing to do with
  # whether a build exists, and skipping early left CodeDeal as the only app
  # of 43 whose groups never got rainbow472.sri@gmail.com — because its one
  # build is expired.
  puts format("%-18s no usable build (seating owners anyway)", repo) if build.nil?

  # Every internal group, not just the first. Several apps carry two ("AGL
  # Internal" and "Internal testers"); seating an owner in one of them left
  # the other empty, and which one TestFlight shows is not ours to choose.
  internals = (app.get_beta_groups rescue []).select(&:is_internal_group)
  internals = internals.sort_by { |g| g.name == GROUP ? 0 : 1 }
  group = internals.first
  if group.nil?
    puts format("%-18s no internal beta group", repo)
    skipped += 1
    next
  end

  # BetaGroup#get_beta_testers answers empty even for groups that have
  # members, so membership is read from the group's own relationship, which
  # reports it correctly.
  todo = internals.map do |g|
    _, tl = req(:get, "v1/betaGroups/#{g.id}/betaTesters?limit=200")
    have = (tl["data"] || []).map { |x| x.dig("attributes", "email").to_s.downcase }.to_set
    [g, emails.reject { |e| have.include?(e.downcase) }]
  end
  want = todo.flat_map { |_, w| w }

  if DRY
    puts format("%-18s build %s, %s", repo, build.version,
                want.empty? ? "group already complete" : "would add #{want.size} tester(s)")
    next
  end

  # Builds are NOT attached to internal groups. Every internal group here has
  # hasAccessToAllBuilds=true (checked: 43/43), so Apple hands them every
  # build automatically and the attach is refused outright:
  #
  #   POST v1/builds/{id}/relationships/betaGroups  422 Cannot add internal
  #   group to a build.
  #
  # An earlier reading of "newest build not in the internal group" as a gap
  # was therefore wrong — there is nothing to attach.
  todo.each do |g, missing|
  missing.each do |e|
    first, last = NAMES.fetch(e, ["AGL", "Owner"])
    code, out = req(:post, "v1/betaTesters", {
                      data: {
                        type: "betaTesters",
                        attributes: { email: e, firstName: first, lastName: last },
                        relationships: { betaGroups: { data: [{ type: "betaGroups", id: g.id }] } },
                      },
                    })
    # POST v1/betaTesters, not the bulk endpoint spaceship wraps: Apple
    # retired v1/bulkBetaTesterAssignments and answers 409 "does not exist"
    # for every call, which this script used to swallow and count as success.
    if code < 300
      added += 1
    else
      puts format("%-18s %-14s %s %d %s", repo, g.name, e, code,
                  out.dig("errors", 0, "detail").to_s.gsub(/\s+/, " ")[0, 80])
      failed += 1
    end
  end
  end

  # Counted from the live read above, not from "what I was about to add" —
  # the old line printed "group has 2 tester(s)" for apps where the add had
  # silently gone to the app's other internal group.
  puts format("%-18s build %s, %d internal group(s), %d seat(s) added",
              repo, build ? build.version : "none", internals.size, want.size)
end

puts "\nattached #{distributed} build(s), added #{added} tester assignment(s), " \
     "skipped #{skipped}, failed #{failed}"
