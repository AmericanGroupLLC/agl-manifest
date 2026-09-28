#!/usr/bin/env ruby
# What App Store Connect actually holds for each app, measured through the API,
# split into what TestFlight beta distribution needs and what App Store review
# needs. Writes JSON for scripts/store_gates.py to merge with the Play side.
#
#   bundle exec ruby store_gates.rb        # -> ~/agl/.dist/asc-gates.json
require "json"
require "fileutils"
require "spaceship"
require_relative "agl_paths"

Spaceship::ConnectAPI.token = Spaceship::ConnectAPI::Token.create(
  key_id: ENV.fetch("ASC_KEY_ID"), issuer_id: ENV.fetch("ASC_ISSUER_ID"), filepath: ENV.fetch("ASC_KEY_PATH"))

apps = JSON.parse(File.read(File.join(AglPaths::MANIFEST, "apps.json")))["apps"]
out = {}

apps.each do |a|
  repo = a["repo"]
  app = Spaceship::ConnectAPI::App.find(a["bundle_id"]) rescue nil
  if app.nil?
    out[repo] = { "record" => false }
    warn "#{repo}: no record"
    next
  end
  r = { "record" => true, "name" => app.name }

  build = Spaceship::ConnectAPI::Build.all(app_id: app.id, sort: "-uploadedDate", limit: 1).first
  r["build"] = build&.version
  r["export_compliance"] = build && !build.uses_non_exempt_encryption.nil?

  info = Spaceship::ConnectAPI.get_app_infos(app_id: app.id, includes: "primaryCategory,secondaryCategory").to_models.first
  r["primary_category"] = info&.primary_category&.id
  # The age-rating questionnaire is answered when the declaration exists and
  # carries at least one answered field.
  begin
    decl = Spaceship::ConnectAPI.get_age_rating_declaration(app_info_id: info.id).to_models.first
    r["age_rating"] = !decl.nil?
  rescue StandardError
    r["age_rating"] = nil
  end

  loc = (info&.get_app_info_localizations rescue []).find { |l| l.locale == "en-US" }
  r["subtitle"] = !loc&.subtitle.to_s.empty?
  r["privacy_policy_url"] = !loc&.privacy_policy_url.to_s.empty?

  ver = Spaceship::ConnectAPI.get_app_store_versions(app_id: app.id, limit: 1).to_models.first
  if ver
    r["version"] = ver.version_string
    r["version_state"] = ver.app_store_state
    vloc = (ver.get_app_store_version_localizations rescue []).find { |l| l.locale == "en-US" }
    r["description"] = vloc&.description.to_s.length
    r["keywords"] = !vloc&.keywords.to_s.empty?
    r["support_url"] = !vloc&.support_url.to_s.empty?
    sets = (vloc&.get_app_screenshot_sets rescue []) || []
    r["screenshot_sets"] = sets.map { |s| [s.screenshot_display_type, (s.app_screenshots || []).size] }.to_h
  end
  out[repo] = r
  puts "#{repo}: measured"
end

out_path = File.join(AglPaths::DIST, "asc-gates.json")
FileUtils.mkdir_p(File.dirname(out_path))
File.write(out_path, JSON.pretty_generate(out))
puts "\nwrote #{out_path} (#{out.size} apps)"
