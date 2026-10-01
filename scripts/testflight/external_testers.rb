#!/usr/bin/env ruby
# Put the whole tester roster on every app's external TestFlight group.
#
#   source scripts/testflight/env.sh
#   bundle exec ruby scripts/testflight/external_testers.rb --dry-run
#   bundle exec ruby scripts/testflight/external_testers.rb
#   bundle exec ruby scripts/testflight/external_testers.rb Kinnav
#
# The roster lives in store/testers.json so that this script, the Play side and
# docs/TESTERS.md all read one list instead of three that drift apart.
#
# Beta groups are per-app, not per-account: "AGL Testers" on one app has
# nothing to do with "AGL Testers" on another, and a tester added to one is
# invisible to the other 42. Groups are created where they are missing.
#
# External rather than internal, deliberately. Internal membership requires an
# App Store Connect account, and the point of this roster is that these people
# should not have one — see set_team_access.rb.
#
# Membership is the only thing this script can finish. Delivery still waits on
# Beta App Review, which currently refuses with "Beta contract is missing for
# the app" (MA-019). Adding people now means that the moment the agreement is
# accepted, nothing else has to happen.

require "json"
require "net/http"
require "set"
require "spaceship"
require "uri"
require_relative "../agl_paths"

DRY   = ARGV.include?("--dry-run")
ONLY  = ARGV.reject { |a| a.start_with?("--") }
GROUP = "AGL Testers"

roster = JSON.parse(File.read(File.join(AglPaths::MANIFEST, "store/testers.json")))
EMAILS = roster["external"].map { |t| t["email"].to_s.downcase }.uniq
NAMES  = roster["external"].each_with_object({}) { |t, h| h[t["email"].to_s.downcase] = t }
puts "roster: #{EMAILS.size} external tester(s)"

TOKEN = Spaceship::ConnectAPI::Token.create(
  key_id: ENV.fetch("ASC_KEY_ID"),
  issuer_id: ENV.fetch("ASC_ISSUER_ID"),
  filepath: ENV.fetch("ASC_KEY_PATH"),
)
Spaceship::ConnectAPI.token = TOKEN

# Spaceship's post_bulk_beta_tester_assignments posts to
# v1/bulkBetaTesterAssignments, which Apple answers with
#
#   409 The URL path is not valid - The resource
#       'v1/bulkBetaTesterAssignments' does not exist
#
# for all 43 apps. It is worth knowing that set_team_access.rb called the same
# helper inside a bare rescue, so its "external assignments" count was reporting
# attempts, not successes. The two endpoints that do exist are used instead:
# create the tester once, then attach them to each group by relationship.
HOST = "https://api.appstoreconnect.apple.com"

def req(verb, path, body = nil)
  uri = URI("#{HOST}/#{path}")
  http = Net::HTTP.new(uri.host, 443)
  http.use_ssl = true
  http.read_timeout = 120
  klass = { get: Net::HTTP::Get, post: Net::HTTP::Post, delete: Net::HTTP::Delete }[verb]
  r = klass.new(uri)
  r["Authorization"] = "Bearer #{TOKEN.text}"
  r["Content-Type"] = "application/json"
  r.body = body.to_json if body
  res = http.request(r)
  [res.code.to_i, (JSON.parse(res.body) rescue {})]
end

def detail_of(out)
  out.dig("errors", 0, "detail").to_s.gsub(/\s+/, " ")
end

apps = JSON.parse(File.read(File.join(AglPaths::MANIFEST, "apps.json")))["apps"]
by_bundle = {}
Spaceship::ConnectAPI::App.all.each { |a| by_bundle[a.bundle_id] = a }

# BetaGroup#get_beta_testers answers empty even for groups that have members,
# so membership is read from the tester side, which reports it correctly. One
# account-wide read, then looked up per app.
memberships = Hash.new { |h, k| h[k] = Set.new }
tester_ids = {}
begin
  Spaceship::ConnectAPI::BetaTester.all(includes: "betaGroups", limit: 200).each do |t|
    e = t.email.to_s.downcase
    next unless EMAILS.include?(e)
    tester_ids[e] = t.id
    (t.beta_groups || []).each { |g| memberships[e] << g.id }
  end
rescue StandardError => e
  warn "could not read existing membership (will add blind): #{e.message[0, 100]}"
end
puts "already known to the account: #{tester_ids.size} of #{EMAILS.size}"

created = added = complete = failed = 0
missing = {}

apps.each do |a|
  repo = a["repo"]
  next if ONLY.any? && !ONLY.include?(repo)
  app = by_bundle[a["bundle_id"]]
  unless app
    puts format("%-18s no App Store record", repo)
    next
  end

  groups = (app.get_beta_groups rescue [])
  group = groups.find { |g| g.name == GROUP && !g.is_internal_group }
  group ||= groups.find { |g| !g.is_internal_group }

  if group.nil?
    if DRY
      puts format("%-18s would create external group %s", repo, GROUP)
      created += 1
      next
    end
    begin
      group = Spaceship::ConnectAPI::BetaGroup.create(
        app_id: app.id, group_name: GROUP, public_link_enabled: false,
      )
      created += 1
    rescue StandardError => e
      puts format("%-18s group FAILED %s", repo, e.message.gsub(/\s+/, " ")[0, 110])
      failed += 1
      next
    end
  end

  want = EMAILS.reject { |e| memberships[e].include?(group.id) }
  if want.empty?
    complete += 1
    puts format("%-18s %-14s all %d already members", repo, group.name, EMAILS.size)
    next
  end

  if DRY
    puts format("%-18s %-14s would add %d: %s", repo, group.name, want.size, want.join(", "))
    next
  end

  ok = []
  want.each do |e|
    n = NAMES[e] || {}

    # POST v1/betaTesters for every group, including for a tester who already
    # exists. It reads like a create, but Apple keys on the email address and
    # simply adds the group, answering 201 with the same tester id — so it is
    # the one call that works in both cases.
    #
    # The obvious alternative does not work. Attaching an existing tester with
    # POST v1/betaGroups/{id}/relationships/betaTesters succeeds for the first
    # group and then answers every later one with
    #
    #   409 STATE_ERROR  Tester(s) cannot be assigned
    #
    # which is why the roster went in through this endpoint instead.
    code, out = req(:post, "v1/betaTesters", {
                      data: {
                        type: "betaTesters",
                        attributes: { email: e, firstName: n["first"], lastName: n["last"] }.compact,
                        relationships: { betaGroups: { data: [{ type: "betaGroups", id: group.id }] } },
                      },
                    })
    if code < 300
      tester_ids[e] = out.dig("data", "id")
      memberships[e] << group.id
      ok << e
    else
      puts format("%-18s %-14s %s %d %s", repo, group.name, e, code, detail_of(out)[0, 90])
      (missing[repo] ||= []) << e
    end
  end

  added += ok.size
  failed += 1 if missing[repo]
  puts format("%-18s %-14s added %d of %d", repo, group.name, ok.size, want.size)
end

puts "\ngroups created #{created}, assignments added #{added}, " \
     "apps already complete #{complete}, failed #{failed}"
out = File.join(AglPaths::DIST, "external-testers.json")
File.write(out, JSON.pretty_generate({ "roster" => EMAILS, "failed" => missing }) + "\n")
puts "-> #{out}"
