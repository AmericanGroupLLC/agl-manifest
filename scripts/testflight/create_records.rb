#!/usr/bin/env ruby
# Create the Developer Portal bundle id and the App Store Connect app record for
# each app that has none, using only the ASC API key (no Apple ID login).
#
#   bundle exec ruby create_records.rb AeroSwift GadgetNest ...
#
# Idempotent: existing bundle ids and records are reported, not recreated.
require "json"
require "spaceship"

ROOT = "/Users/spatchava/agl"
apps = JSON.parse(File.read("#{ROOT}/agl-manifest/apps.json"))["apps"]

NAMES = {
  "AeroSwift" => "AeroSwift",
  "GadgetNest" => "GadgetNest",
  "MyHealth" => "MyHealth: Fitness Tracker",
  "Verba" => "Verba: Voice Translator",
}
def store_name(repo)
  return NAMES[repo] if NAMES[repo]
  path = "#{ROOT}/agl-manifest/store/apps/#{repo}.json"
  File.exist?(path) ? JSON.parse(File.read(path)).dig("copy", "en", "name") || repo : repo
end

Spaceship::ConnectAPI.token = Spaceship::ConnectAPI::Token.create(
  key_id: ENV.fetch("ASC_KEY_ID"),
  issuer_id: ENV.fetch("ASC_ISSUER_ID"),
  filepath: ENV.fetch("ASC_KEY_PATH")
)

results = {}
ARGV.each do |repo|
  a = apps.find { |x| x["repo"] == repo } or (puts "#{repo}: not in apps.json"; next)
  bid = a["bundle_id"]
  name = store_name(repo)
  ver = a["version"].split("+").first
  sku = "#{repo.downcase}-001"
  begin
    b = Spaceship::ConnectAPI::BundleId.all(filter: { identifier: bid }).find { |x| x.identifier == bid }
    if b
      puts "#{repo}: bundle id exists (#{b.name})"
    else
      b = Spaceship::ConnectAPI::BundleId.create(name: name.gsub(/[^A-Za-z0-9 ]/, " ").squeeze(" ").strip, identifier: bid, platform: "IOS")
      puts "#{repo}: bundle id CREATED #{bid}"
    end
    app = Spaceship::ConnectAPI::App.find(bid)
    if app
      puts "#{repo}: app record exists -> '#{app.name}' (id #{app.id})"
      results[repo] = { status: "exists", app_id: app.id, name: app.name }
    else
      app = Spaceship::ConnectAPI::App.create(name: name, version_string: ver, sku: sku, primary_locale: "en-US", bundle_id: bid, platforms: ["IOS"])
      puts "#{repo}: app record CREATED -> '#{name}' (id #{app.id}) v#{ver} sku #{sku}"
      results[repo] = { status: "created", app_id: app.id, name: name }
    end
  rescue => e
    msg = e.message.lines.first.to_s.strip
    puts "#{repo}: FAILED #{msg}"
    results[repo] = { status: "failed", error: msg[0, 300] }
  end
end
File.write("#{ROOT}/.dist/ios-batch/records-result.json", JSON.pretty_generate(results))
puts JSON.pretty_generate(results)
