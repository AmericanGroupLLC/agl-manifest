#!/usr/bin/env ruby
# Download the screenshots App Store Connect actually holds, per app.
#
#   source scripts/testflight/env.sh
#   bundle exec ruby scripts/testflight/asc_screenshots.rb             # every app
#   bundle exec ruby scripts/testflight/asc_screenshots.rb MyCard Kinnav
#
# Six apps were rejected under 2.3.3 ("the screenshots only display a login
# screen", "only display a splash screen", "do not show the current version")
# while the gate passed them, because the gate looked at the PNGs on this
# laptop. Apple looks at what was uploaded. This fetches exactly that — the
# newest App Store version's en-US screenshot sets — so
# scripts/screenshot_audit.py can judge the same pixels Apple's reviewer saw.
#
# Writes <DIST>/asc-screenshots/<repo>/<displayType>-NN.png and
# <DIST>/asc-screenshots/index.json. Read-only against Apple.
require "json"
require "net/http"
require "fileutils"
require "spaceship"
require "uri"
require_relative "../agl_paths"

ONLY = ARGV.reject { |a| a.start_with?("--") }
HOST = "https://api.appstoreconnect.apple.com"
TOKEN = Spaceship::ConnectAPI::Token.create(
  key_id: ENV.fetch("ASC_KEY_ID"), issuer_id: ENV.fetch("ASC_ISSUER_ID"),
  filepath: ENV.fetch("ASC_KEY_PATH"))
Spaceship::ConnectAPI.token = TOKEN
OUT = File.join(AglPaths::DIST, "asc-screenshots")

def get(path)
  uri = URI(path.start_with?("http") ? path : "#{HOST}/#{path}")
  http = Net::HTTP.new(uri.host, 443)
  http.use_ssl = true
  http.read_timeout = 120
  r = Net::HTTP::Get.new(uri)
  r["Authorization"] = "Bearer #{TOKEN.text}" if uri.host == "api.appstoreconnect.apple.com"
  res = http.request(r)
  [res.code.to_i, res.body]
end

def json(path)
  code, body = get(path)
  code == 200 ? JSON.parse(body) : {}
end

apps = JSON.parse(File.read(File.join(AglPaths::MANIFEST, "apps.json")))["apps"]
apps = apps.select { |a| ONLY.include?(a["repo"]) } unless ONLY.empty?
by_bundle = {}
Spaceship::ConnectAPI::App.all.each { |a| by_bundle[a.bundle_id] = a }
index = File.exist?(File.join(OUT, "index.json")) ? JSON.parse(File.read(File.join(OUT, "index.json"))) : {}

apps.each do |a|
  repo = a["repo"]
  app = by_bundle[a["bundle_id"]]
  next puts(format("  %-18s no App Store Connect record", repo)) unless app
  ver = (json("v1/apps/#{app.id}/appStoreVersions?limit=1&filter[platform]=IOS")["data"] || []).first
  next puts(format("  %-18s no App Store version", repo)) unless ver
  locs = json("v1/appStoreVersions/#{ver['id']}/appStoreVersionLocalizations")["data"] || []
  loc = locs.find { |l| l.dig("attributes", "locale") == "en-US" } || locs.first
  next puts(format("  %-18s no localization", repo)) unless loc
  dir = File.join(OUT, repo)
  FileUtils.rm_rf(dir)
  FileUtils.mkdir_p(dir)
  rec = { "version" => ver.dig("attributes", "versionString"),
          "state" => ver.dig("attributes", "appStoreState"), "sets" => {} }
  sets = json("v1/appStoreVersionLocalizations/#{loc['id']}/appScreenshotSets")["data"] || []
  sets.each do |s|
    type = s.dig("attributes", "screenshotDisplayType")
    shots = json("v1/appScreenshotSets/#{s['id']}/appScreenshots")["data"] || []
    files = []
    shots.each_with_index do |sh, i|
      asset = sh.dig("attributes", "imageAsset") or next
      url = asset["templateUrl"].sub("{w}", asset["width"].to_s).sub("{h}", asset["height"].to_s).sub("{f}", "png")
      code, body = get(url)
      next unless code == 200
      f = File.join(dir, format("%s-%02d.png", type, i + 1))
      File.binwrite(f, body)
      files << File.basename(f)
    end
    rec["sets"][type] = files
  end
  index[repo] = rec
  n = rec["sets"].values.sum(&:size)
  puts format("  %-18s v%-8s %-24s %d screenshot(s) in %d set(s)", repo, rec["version"], rec["state"], n, rec["sets"].size)
end

File.write(File.join(OUT, "index.json"), JSON.pretty_generate(index))
puts "  -> #{OUT}"
