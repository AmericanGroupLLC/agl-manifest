#!/usr/bin/env ruby
# Read why Apple rejected each app, from Resolution Center.
#
# The public API does not carry this: an API key gets 404 on
# `v1/resolutionCenterThreads`, and a rejected submission reports only
# `betaReviewState: REJECTED` with no text. The `iris` host behind App Store
# Connect does carry it, and takes an Apple ID session:
#
#   bundle exec fastlane spaceauth -u srikanth.patchava@outlook.com
#   FASTLANE_USER=srikanth.patchava@outlook.com \
#     bundle exec ruby scripts/testflight/rejection_reasons.rb
#
# Writes ~/agl/.dist/rejections.json and prints a digest.
require "json"
require "spaceship"

USER = ENV.fetch("FASTLANE_USER", "srikanth.patchava@outlook.com")
ONLY = ARGV.reject { |a| a.start_with?("--") }

Spaceship::Tunes.login(USER)
Spaceship::ConnectAPI.token = Spaceship::ConnectAPI::Token.create(
  key_id: ENV.fetch("ASC_KEY_ID"), issuer_id: ENV.fetch("ASC_ISSUER_ID"), filepath: ENV.fetch("ASC_KEY_PATH"))
tunes = Spaceship::Tunes.client

def get(tunes, path)
  r = tunes.request(:get) { |req| req.url("https://appstoreconnect.apple.com/#{path}") }
  r.status == 200 ? r.body : nil
rescue StandardError
  nil
end

apps = JSON.parse(File.read(File.expand_path("../../apps.json", __dir__)))["apps"]
apps = apps.select { |a| ONLY.include?(a["repo"]) } unless ONLY.empty?
out = {}

apps.each do |a|
  app = Spaceship::ConnectAPI::App.find(a["bundle_id"]) rescue nil
  next if app.nil?
  ver = Spaceship::ConnectAPI.get_app_store_versions(app_id: app.id, limit: 1).to_models.first
  next if ver.nil?
  next unless ver.app_store_state == "REJECTED"

  body = get(tunes, "iris/v1/resolutionCenterThreads?filter[appStoreVersion]=#{ver.id}")
  threads = (body && body["data"]) || []
  msgs = []
  threads.each do |t|
    mb = get(tunes, "iris/v1/resolutionCenterThreads/#{t['id']}/resolutionCenterMessages")
    ((mb && mb["data"]) || []).each do |m|
      txt = m.dig("attributes", "messageBody").to_s
      msgs << txt unless txt.empty?
    end
  end
  out[a["repo"]] = { "version" => ver.version_string, "threads" => threads.size, "messages" => msgs }
  first = msgs.first.to_s.gsub(/\s+/, " ")
  puts format("%-18s %s", a["repo"], first.empty? ? "(no message text)" : first[0, 150])
end

File.write("/Users/spatchava/agl/.dist/rejections.json", JSON.pretty_generate(out))
puts "\n#{out.size} rejected app(s) -> ~/agl/.dist/rejections.json"
