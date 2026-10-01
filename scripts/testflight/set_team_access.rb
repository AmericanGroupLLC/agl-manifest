#!/usr/bin/env ruby
# Reduce App Store Connect to one account holder, and make everyone else an
# external tester only.
#
#   source scripts/testflight/env.sh
#   bundle exec ruby scripts/testflight/set_team_access.rb --dry-run
#   bundle exec ruby scripts/testflight/set_team_access.rb
#
# Decided 2026-09-30: srikanth.patchava@outlook.com stays as the Apple account
# holder and rainbow472.sri@gmail.com stays because it administers the Google
# Play side. Everyone else loses App Store Connect account access and keeps
# only external TestFlight membership.
#
# Order matters. Internal group membership is removed first, then account
# access: a user removed from Users and Access while still in an internal
# group can leave the group holding a dangling member that the API will not
# then let you delete.
#
# Checked before writing any of this: no certificate belongs to a person being
# removed. The distribution certificate the pipeline signs with, 2S2F6CDFY2,
# is a team certificate issued to "American Group LLC", and the only
# per-person certificates are development ones belonging to the account holder.
# Removing a user with CLOUD_MANAGED_DEVELOPER_ID can take cloud-managed
# signing assets with them, which is why that was verified rather than assumed.

require "json"
require "set"
require "spaceship"
require_relative "../agl_paths"

DRY = ARGV.include?("--dry-run")

KEEP = [
  "srikanth.patchava@outlook.com",  # Apple account holder
  "rainbow472.sri@gmail.com",       # Google Play admin
].freeze

EXTERNAL_GROUP = "AGL Testers"
INTERNAL_NAMES = ["AGL Internal", "Internal testers", "Me"].freeze

Spaceship::ConnectAPI.token = Spaceship::ConnectAPI::Token.create(
  key_id: ENV.fetch("ASC_KEY_ID"),
  issuer_id: ENV.fetch("ASC_ISSUER_ID"),
  filepath: ENV.fetch("ASC_KEY_PATH"),
)

users = Spaceship::ConnectAPI::User.all
remove = users.reject { |u| KEEP.include?((u.username || u.email).to_s.downcase) }
keep   = users.select { |u| KEEP.include?((u.username || u.email).to_s.downcase) }

puts "keeping #{keep.size}:"
keep.each { |u| puts "  #{u.username || u.email}  #{Array(u.roles).join(', ')}" }
puts "removing account access from #{remove.size}:"
remove.each { |u| puts "  #{u.username || u.email}  #{Array(u.roles).join(', ')}" }
puts

if remove.any? { |u| Array(u.roles).include?("ACCOUNT_HOLDER") }
  abort "refusing: that would remove the account holder"
end

emails = remove.map { |u| (u.username || u.email).to_s }.compact

# --- 1. make sure each of them is an external tester before anything is taken away
apps = JSON.parse(File.read(File.join(AglPaths::MANIFEST, "apps.json")))["apps"]
by_bundle = {}
Spaceship::ConnectAPI::App.all.each { |a| by_bundle[a.bundle_id] = a }

# Read every tester once, with their groups, because the per-group query
# returns nothing. 443 records collapse to 10 unique addresses.
TESTERS_BY_EMAIL = begin
  Spaceship::ConnectAPI::BetaTester.all(includes: "betaGroups", limit: 200)
    .each_with_object({}) { |t, h| h[t.email.to_s] ||= t if t.email }
rescue StandardError => e
  warn "could not list testers: #{e.message[0, 100]}"
  {}
end
puts "testers resolved: #{TESTERS_BY_EMAIL.size}"

added = pulled = 0
apps.each do |a|
  app = by_bundle[a["bundle_id"]]
  next unless app
  groups = (app.get_beta_groups rescue [])
  ext = groups.find { |g| g.name == EXTERNAL_GROUP && !g.is_internal_group }
  ext ||= groups.find { |g| !g.is_internal_group }
  if ext && !DRY
    begin
      Spaceship::ConnectAPI.post_bulk_beta_tester_assignments(
        beta_group_id: ext.id, beta_testers: emails.map { |e| { email: e } })
      added += emails.size
    rescue StandardError
      # already a member, which is the desired state anyway
    end
  end

  # BetaGroup#get_beta_testers returns an empty list here even for groups that
  # demonstrably have members, so membership is read from the tester side,
  # which does work. Resolved once, outside the loop, into TESTERS_BY_EMAIL.
  groups.select { |g| g.is_internal_group || INTERNAL_NAMES.include?(g.name) }.each do |g|
    members = emails.filter_map { |e| TESTERS_BY_EMAIL[e] }
                    .select { |t| (t.beta_groups || []).any? { |bg| bg.id == g.id } rescue false }
    next if members.empty?
    if DRY
      puts "  #{a['repo']}: would remove #{members.size} from #{g.name}"
      pulled += members.size
      next
    end
    begin
      members.each do |m|
        Spaceship::ConnectAPI.delete_beta_tester_from_beta_groups(
          beta_tester_id: m.id, beta_group_ids: [g.id])
      end
      pulled += members.size
    rescue StandardError => e
      puts "  #{a['repo']}: could not clear #{g.name} — #{e.message.gsub(/\s+/, ' ')[0, 90]}"
    end
  end
end
puts "external assignments #{added}, internal memberships removed #{pulled}"

# --- 2. then take account access away
gone = failed = 0
remove.each do |u|
  email = u.username || u.email
  if DRY
    puts "  would remove account user #{email}"
    gone += 1
    next
  end
  begin
    u.delete!
    puts "  removed account user #{email}"
    gone += 1
  rescue StandardError => e
    puts "  FAILED #{email} — #{e.message.gsub(/\s+/, ' ')[0, 130]}"
    failed += 1
  end
end

puts "\naccount users removed #{gone}, failed #{failed}"
puts "remaining: #{KEEP.join(', ')}"
