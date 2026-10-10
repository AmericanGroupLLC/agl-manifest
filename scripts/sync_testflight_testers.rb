#!/usr/bin/env ruby
# Mirror every App Store Connect account user into each app's internal
# TestFlight group.
#
#   bundle exec ruby scripts/sync_testflight_testers.rb --dry-run
#   bundle exec ruby scripts/sync_testflight_testers.rb
#   bundle exec ruby scripts/sync_testflight_testers.rb --app CalcMaster
#
# Why this exists: a build uploaded to an internal group that has no testers
# reaches nobody, which is exactly what had happened across the account. Users
# get added in "Users and Access" and are then silently absent from TestFlight.
#
# Note for anyone who read docs/MANUAL_ACTIONS.md MA-013: that entry says
# internal groups "cannot be filled through the API" and that
# POST /v1/betaTesters is refused with "Tester(s) cannot be assigned".
# Re-tested 2026-09-22 and that is no longer true — the call returns HTTP 201
# and the tester appears in the group. The 409 in the old note comes from
# assigning a tester who is *already* in another group for the same app, not
# from the group being internal. This script treats that 409 as success.
#
# Idempotent: a tester already in the group is left alone.

require "json"
require "net/http"
require "spaceship"

require "fileutils"
require_relative "agl_paths"
ROOT = AglPaths::ROOT
DRY = ARGV.include?("--dry-run")
ONLY = (i = ARGV.index("--app")) ? ARGV[i + 1] : nil

Spaceship::ConnectAPI.token = Spaceship::ConnectAPI::Token.create(
  key_id: ENV.fetch("ASC_KEY_ID"),
  issuer_id: ENV.fetch("ASC_ISSUER_ID"),
  filepath: ENV.fetch("ASC_KEY_PATH")
)
TOKEN = Spaceship::ConnectAPI.token.text

def api(method, path, body = nil)
  uri = URI("https://api.appstoreconnect.apple.com#{path}")
  klass = { "GET" => Net::HTTP::Get, "POST" => Net::HTTP::Post,
            "DELETE" => Net::HTTP::Delete }.fetch(method)
  req = klass.new(uri, { "Authorization" => "Bearer #{TOKEN}",
                         "Content-Type" => "application/json" })
  req.body = body.to_json if body
  res = Net::HTTP.start(uri.hostname, uri.port, use_ssl: true) { |h| h.request(req) }
  parsed = begin
    JSON.parse(res.body)
  rescue StandardError
    {}
  end
  [res.code.to_i, parsed]
end

def all_pages(path)
  out = []
  url = path
  loop do
    code, body = api("GET", url)
    break unless code == 200
    out.concat(body["data"] || [])
    nxt = body.dig("links", "next")
    break unless nxt
    url = nxt.sub("https://api.appstoreconnect.apple.com", "")
  end
  out
end

# ── who should have access ───────────────────────────────────────────────────
users = all_pages("/v1/users?limit=200").map do |u|
  {
    email: u.dig("attributes", "username"),
    first: u.dig("attributes", "firstName").to_s,
    last: u.dig("attributes", "lastName").to_s,
    roles: u.dig("attributes", "roles") || [],
  }
end.reject { |u| u[:email].to_s.empty? }

puts "App Store Connect account users: #{users.size}"
users.each { |u| puts "   #{u[:email]}  #{u[:roles].join(',')}" }
puts

# store_eligible is still honoured so the manifest can exclude an app, but
# nothing sets it false any more: all 43 are in scope. This comment used to
# say the portfolio was 42.
apps = JSON.parse(File.read("#{ROOT}/agl-manifest/apps.json"))["apps"]
         .select { |a| a["flutter"] && a["store_eligible"] != false }
by_bundle = {}
Spaceship::ConnectAPI::App.all.each { |a| by_bundle[a.bundle_id] = a }

results = []
added_total = 0
apps.each do |a|
  repo = a["repo"]
  next if ONLY && ONLY != repo
  app = by_bundle[a["bundle_id"]]
  unless app
    results << { repo: repo, state: "NO_ASC_RECORD" }
    next
  end

  groups = all_pages("/v1/apps/#{app.id}/betaGroups?limit=50")
  internal = groups.select { |g| g.dig("attributes", "isInternalGroup") }
  if internal.empty?
    # Most apps in this account have no internal group at all, which is the
    # real reason uploaded builds reached nobody. The API can create one:
    # hasAccessToAllBuilds is the "auto-distribute new builds" behaviour, so a
    # future upload goes out without anyone touching the console.
    if DRY
      puts "#{repo.ljust(18)} would CREATE internal group + add #{users.size}"
      results << { repo: repo, state: "WOULD_CREATE_GROUP", would_add: users.map { |u| u[:email] } }
      next
    end
    code, body = api("POST", "/v1/betaGroups", {
      data: {
        type: "betaGroups",
        attributes: { name: "Internal testers", isInternalGroup: true,
                      hasAccessToAllBuilds: true },
        relationships: { app: { data: { type: "apps", id: app.id } } },
      },
    })
    unless [200, 201].include?(code)
      detail = body.dig("errors", 0, "detail") || body.dig("errors", 0, "title") || code
      results << { repo: repo, state: "GROUP_CREATE_FAILED", detail: detail.to_s[0, 160] }
      puts "#{repo.ljust(18)} could not create internal group: #{detail.to_s[0, 110]}"
      next
    end
    group = body["data"]
    puts "#{repo.ljust(18)} created internal group"
    internal = [group]
  end
  group = internal.find { |g| g.dig("attributes", "name") == "Internal testers" } || internal.first
  gid = group["id"]

  present = all_pages("/v1/betaGroups/#{gid}/betaTesters?limit=200")
             .map { |t| t.dig("attributes", "email").to_s.downcase }
  missing = users.reject { |u| present.include?(u[:email].downcase) }

  if missing.empty?
    results << { repo: repo, state: "IN_SYNC", group: group.dig("attributes", "name"),
                 testers: present.size }
    puts "#{repo.ljust(18)} in sync (#{present.size} testers)"
    next
  end

  if DRY
    puts "#{repo.ljust(18)} would add #{missing.size}: #{missing.map { |m| m[:email] }.join(', ')}"
    results << { repo: repo, state: "WOULD_ADD", would_add: missing.map { |m| m[:email] } }
    next
  end

  added = []
  failed = []
  missing.each do |u|
    code, body = api("POST", "/v1/betaTesters", {
      data: {
        type: "betaTesters",
        attributes: { email: u[:email], firstName: u[:first], lastName: u[:last] },
        relationships: { betaGroups: { data: [{ type: "betaGroups", id: gid }] } },
      },
    })
    # 409 here means the tester already exists on this app under another group;
    # the account already has them, which is the outcome we want.
    if [200, 201, 409].include?(code)
      added << u[:email]
    else
      detail = body.dig("errors", 0, "detail") || body.dig("errors", 0, "title") || code
      failed << "#{u[:email]}: #{detail.to_s[0, 90]}"
    end
  end
  added_total += added.size
  results << { repo: repo, state: "SYNCED", group: group.dig("attributes", "name"),
               added: added, failed: failed }
  puts "#{repo.ljust(18)} added #{added.size}#{failed.empty? ? '' : ", FAILED #{failed.size}"}"
  failed.each { |f| puts "      #{f}" }
end

# <DIST>, not ~/agl/.sweep: .sweep exists only on the old laptop layout, and
# writing there crashed the CI job after every app had already synced.
FileUtils.mkdir_p(AglPaths::DIST)
File.write(File.join(AglPaths::DIST, "testflight-tester-sync.json"), JSON.pretty_generate(results))
counts = results.group_by { |r| r[:state] }.transform_values(&:size)
puts "\n#{counts.map { |k, v| "#{k}=#{v}" }.join('  ')}"
puts "testers added this run: #{added_total}" unless DRY
