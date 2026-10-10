#!/usr/bin/env ruby
# Set every app's App Store privacy, support and marketing URLs, in every
# localization, to the pages that are verified to serve on www.americangroup.ai.
#
#   source scripts/testflight/env.sh
#   bundle exec ruby scripts/testflight/asc_urls.rb --check     # report only
#   bundle exec ruby scripts/testflight/asc_urls.rb             # every app
#   bundle exec ruby scripts/testflight/asc_urls.rb radiotune
#
# The domain moved on 2026-10-09. deliver_metadata.py reported "ok" for all 43
# apps, yet reading App Store Connect back showed 28 still carrying
# safecodeg.com somewhere — mostly the marketing URL, and five apps not changed
# at all — because deliver only writes the URL files a repo happens to have,
# and only for the locales it finds. This writes the three fields directly and
# reads them back.
#
# Sources: privacy and support URLs from <DIST>/policy-urls.json (written by
# scripts/verify_policy_urls.py, which proves each one serves the right page);
# marketing URL = the app's product page on the website. An app without a
# verified privacy URL is skipped, never given a guessed one.
require "json"
require "spaceship"
require_relative "../agl_paths"

CHECK = ARGV.include?("--check")
ONLY = ARGV.reject { |a| a.start_with?("--") }
SITE = "https://www.americangroup.ai"

Spaceship::ConnectAPI.token = Spaceship::ConnectAPI::Token.create(
  key_id: ENV.fetch("ASC_KEY_ID"), issuer_id: ENV.fetch("ASC_ISSUER_ID"), filepath: ENV.fetch("ASC_KEY_PATH"))

apps = JSON.parse(File.read(File.join(AglPaths::MANIFEST, "apps.json")))["apps"]
apps = apps.select { |a| ONLY.include?(a["repo"]) } unless ONLY.empty?
verified = JSON.parse(File.read(File.join(AglPaths::DIST, "policy-urls.json")))
generated = File.read(File.join(AglPaths::ROOT, "americangroup.ai/client/src/data/mobileApps.generated.ts"))
product = generated.scan(/repo: "([^"]+)",\s*slug: "([^"]+)"/).to_h

changed = 0
apps.each do |a|
  repo = a["repo"]
  v = verified[repo] || {}
  privacy = v.dig("privacy", "url") if v.dig("privacy", "state") == "OK"
  support = v.dig("support", "url") if v.dig("support", "state") == "OK"
  unless privacy && support
    puts format("  %-18s skipped: no verified privacy/support URL", repo)
    next
  end
  marketing = "#{SITE}/products/#{product[repo] || repo.downcase}"

  app = Spaceship::ConnectAPI::App.find(a["bundle_id"]) rescue nil
  next puts(format("  %-18s no App Store Connect record", repo)) unless app
  notes = []

  info = (app.fetch_edit_app_info rescue nil) || (app.fetch_live_app_info rescue nil)
  (info&.get_app_info_localizations || []).each do |l|
    next if l.privacy_policy_url == privacy
    notes << "#{l.locale} privacy #{l.privacy_policy_url.inspect}"
    l.update(attributes: { privacy_policy_url: privacy }) unless CHECK
  end

  ver = app.get_app_store_versions(limit: 1).first
  (ver&.get_app_store_version_localizations || []).each do |l|
    attrs = {}
    attrs[:support_url] = support if l.support_url != support
    attrs[:marketing_url] = marketing if l.marketing_url != marketing
    next if attrs.empty?
    notes << "#{l.locale} #{attrs.keys.join('+')}"
    l.update(attributes: attrs) unless CHECK
  end

  changed += 1 unless notes.empty?
  puts format("  %-18s %-24s %s", repo, ver&.app_store_state.to_s,
              notes.empty? ? "already correct" : "#{CHECK ? 'would set' : 'set'} #{notes.size}: #{notes.first(3).join('; ')}")
rescue StandardError => e
  puts format("  %-18s FAILED %s", repo, e.message.gsub(/\s+/, " ")[0, 160])
end
puts "\n  #{changed} app(s) #{CHECK ? 'need changes' : 'updated'}"
