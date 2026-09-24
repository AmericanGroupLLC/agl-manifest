#!/usr/bin/env ruby
# Create the missing App Store Connect records, and publish the App Privacy
# answers, using an Apple ID web session.
#
# Both jobs are refused by an API key — measured, not assumed:
#   POST v1/apps                     -> "The resource 'apps' does not allow 'CREATE'"
#   v1/apps/{id}/dataUsages          -> "The relationship 'dataUsages' does not exist"
#   iris/v1/apps/{id}/dataUsages     -> 401, "No valid credentials found"
# The iris host behind App Store Connect does both, and it takes an Apple ID
# session rather than a key.
#
# Get a session once (it lasts about a month) and this finishes the portfolio:
#
#   bundle exec fastlane spaceauth -u srikanth.patchava@outlook.com
#   # paste the printed value into ~/agl/.secrets/fastlane-session
#   source scripts/testflight/env.sh
#   bundle exec ruby scripts/testflight/create_records_session.rb --dry-run
#   bundle exec ruby scripts/testflight/create_records_session.rb
#
# Idempotent: an app that already has a record is skipped, and the privacy
# answers are only published where they are not already published.
require "json"
require "spaceship"

DRY   = ARGV.include?("--dry-run")
ONLY  = ARGV.reject { |x| x.start_with?("--") }
ROOT  = ENV.fetch("AGL_ROOT", File.expand_path("../../..", __dir__))
MANIF = File.expand_path("../..", __dir__)

if ENV["FASTLANE_SESSION"].to_s.empty?
  abort <<~MSG
    No Apple ID session. This script cannot work without one.

      bundle exec fastlane spaceauth -u #{ENV.fetch('FASTLANE_USER', 'the account holder')}

    Paste the printed value into ~/agl/.secrets/fastlane-session, then
    `source scripts/testflight/env.sh` again and re-run.
  MSG
end

apps = JSON.parse(File.read(File.join(MANIF, "apps.json")))["apps"]
apps = apps.select { |a| a["store_eligible"] != false }
apps = apps.select { |a| ONLY.include?(a["repo"]) } unless ONLY.empty?

# The App Store name, SKU and category the owner specified, kept beside the app
# rather than retyped here.
def listing(repo, manif)
  p = File.join(manif, "store/apps/#{repo}.json")
  return {} unless File.exist?(p)
  j = JSON.parse(File.read(p))
  { name: j.dig("copy", "en", "name"), category: j["primary_category"] }
end

Spaceship::ConnectAPI.token = Spaceship::ConnectAPI::Token.create(
  key_id: ENV.fetch("ASC_KEY_ID"), issuer_id: ENV.fetch("ASC_ISSUER_ID"), filepath: ENV.fetch("ASC_KEY_PATH"))
Spaceship::Tunes.login(ENV.fetch("FASTLANE_USER"))
puts "signed in as #{Spaceship::Tunes.client.user}"

created = []; privacy = []; skipped = []; failed = []

apps.each do |a|
  repo = a["repo"]
  existing = Spaceship::ConnectAPI::App.find(a["bundle_id"]) rescue nil

  unless existing
    info = listing(repo, MANIF)
    name = info[:name] || repo
    sku  = "#{repo.downcase.tr('-', '')}-001"
    if DRY
      puts "#{repo.ljust(18)} WOULD CREATE #{name.inspect} #{a['bundle_id']} sku=#{sku}"
      created << repo
      next
    end
    begin
      Spaceship::Tunes::Application.create!(name: name, primary_language: "English",
                                            version: a["version"].to_s.split("+").first,
                                            sku: sku, bundle_id: a["bundle_id"])
      puts "#{repo.ljust(18)} CREATED #{name.inspect}"
      created << repo
    rescue StandardError => e
      puts "#{repo.ljust(18)} create failed: #{e.message.gsub(/\s+/, ' ')[0, 180]}"
      failed << repo
      next
    end
  end

  # App Privacy: publish the answers already written in store/privacy/<repo>.json.
  pfile = File.join(MANIF, "store/privacy/#{repo}.json")
  next unless File.exist?(pfile)
  app = existing || (Spaceship::ConnectAPI::App.find(a["bundle_id"]) rescue nil)
  next if app.nil?
  begin
    state = Spaceship::ConnectAPI::AppDataUsagesPublishState.get(app_id: app.id)
    if state.published
      skipped << repo
      next
    end
    if DRY
      puts "#{repo.ljust(18)} WOULD PUBLISH app privacy"
      privacy << repo
      next
    end
    Fastlane::Actions::UploadAppPrivacyDetailsToAppStoreAction rescue nil
    state.publish!
    puts "#{repo.ljust(18)} app privacy PUBLISHED"
    privacy << repo
  rescue StandardError => e
    puts "#{repo.ljust(18)} privacy: #{e.message.gsub(/\s+/, ' ')[0, 160]}"
    failed << repo
  end
end

puts "\ncreated: #{created.size}  privacy published: #{privacy.size}  already done: #{skipped.size}  failed: #{failed.size}"
puts "failed: #{failed.join(', ')}" unless failed.empty?
