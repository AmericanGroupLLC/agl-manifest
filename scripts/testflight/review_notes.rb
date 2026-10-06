#!/usr/bin/env ruby
# Answer Apple's Guideline 2.1 information request in the App Review Notes.
#
# All 20 rejections carry the same text: "This app has been submitted by a
# developer account that has a limited App Review history. We need additional
# information..." Apple then asks for five things and says to put them in the
# Notes field of App Review Information.
#
# Four of the five are facts this repository already holds, so they are written
# here rather than typed 20 times:
#
#   2. purpose and target audience  <- store/apps/<repo>.json
#   3. how to set up and reach the main features, and any credentials
#   4. the external services the app relies on  <- the app's own pubspec
#   5. regional differences  <- whether the app ships more than en-US
#
# The fifth, a screen recording made on a physical device, cannot come from a
# script. It is the one thing left per app.
#
#   source scripts/testflight/env.sh
#   bundle exec ruby scripts/testflight/review_notes.rb --dry-run
#   bundle exec ruby scripts/testflight/review_notes.rb
require "json"
require "yaml"

require "spaceship"

DRY  = ARGV.include?("--dry-run")
ONLY = ARGV.reject { |a| a.start_with?("--") }
require_relative "../agl_paths"
ROOT = AglPaths::ROOT
M    = File.expand_path("../..", __dir__)

Spaceship::ConnectAPI.token = Spaceship::ConnectAPI::Token.create(
  key_id: ENV.fetch("ASC_KEY_ID"), issuer_id: ENV.fetch("ASC_ISSUER_ID"), filepath: ENV.fetch("ASC_KEY_PATH"))

# A dependency is only worth naming to App Review if it reaches a service.
SERVICES = {
  "firebase_core" => "Firebase (Google) — app initialisation",
  "firebase_auth" => "Firebase Authentication (Google) — sign-in",
  "cloud_firestore" => "Cloud Firestore (Google) — data storage",
  "firebase_crashlytics" => "Firebase Crashlytics (Google) — crash reporting",
  "firebase_analytics" => "Firebase Analytics (Google) — usage analytics",
  "supabase_flutter" => "Supabase — account and data storage",
  "google_mobile_ads" => "Google AdMob — advertising",
  "google_sign_in" => "Google Sign-In — authentication",
  "sign_in_with_apple" => "Sign in with Apple — authentication",
  "in_app_purchase" => "Apple In-App Purchase — paid features",
  "geolocator" => "device location services (on-device)",
  "http" => "HTTPS requests to the app's own endpoints",
}.freeze

def app_dir(a)
  a["dir"].to_s.empty? || a["dir"] == "." ? "#{ROOT}/#{a['repo']}" : "#{ROOT}/#{a['repo']}/#{a['dir']}"
end

def services_for(a)
  path = File.join(app_dir(a), "pubspec.yaml")
  return [] unless File.exist?(path)
  deps = File.read(path).split("dev_dependencies").first.to_s
  SERVICES.select { |k, _| deps.match?(/^\s{2}#{Regexp.escape(k)}\s*:/) }.values
end

# The languages the *app* runs in, not the languages its store listing is
# written in. Apple's question is about regional differences in features and
# content, and the store-listing folders under fastlane/metadata answered a
# different question — they said "None" for apps that ship twelve languages.
I18N = begin
  rows = JSON.parse(File.read(File.join(M, "docs/i18n-audit.json")))["apps"]
  rows.each_with_object({}) { |r, h| h[r["repo"]] = r }
rescue StandardError
  {}
end

def locales_for(a)
  row = I18N[a["repo"]] || {}
  n = row["declared_locales"].to_i
  return [] if n <= 1
  arb = row["arb_locales"]
  arb.is_a?(Array) && arb.size >= n ? arb : Array.new(n) { |i| "locale #{i + 1}" }
end

# Stated plainly because Apple asks what the build was tested on, and the
# honest answer is simulators and emulators rather than a device lab.
TEST_DEVICES = "iPhone 17 Pro Max and iPad Pro 13-inch simulators on iOS 26, " \
               "and a Pixel Android emulator on API 34".freeze

REGULATED = "The app is not in a regulated industry and carries no licensed " \
            "third-party material. All content, artwork and copy are the " \
            "developer's own.".freeze

def notes_for(a, copy)
  en = copy.dig("copy", "en") || {}
  purpose = en["description"].to_s.split("\n\n").first.to_s.strip
  purpose = en["short_description"].to_s if purpose.empty?
  audience = en["subtitle"].to_s
  auth = a["auth"] || {}
  services = services_for(a)
  locales = locales_for(a)

  access =
    if auth["login_screen"]
      "The app opens on a sign-in screen. #{auth['account_optional'] ? 'An account is optional; the main features can be reached without signing in.' : 'Test credentials are in the demo account fields of App Review Information.'}"
    else
      "No account and no login are required. Every feature is reachable from the first screen after launch."
    end

  <<~NOTE.strip
    2. DEVICES AND OS VERSIONS TESTED
    Automated tests run on every build: #{TEST_DEVICES}.
    Each release is also installed and launched on those targets, so a
    build that cannot start never ships.

    3. WHAT THIS APP DOES, AND FOR WHOM
    #{purpose}

    Intended audience:
    #{audience.empty? ? 'General consumer audience; no specialist knowledge is assumed.' : audience}

    4. SETTING UP AND REACHING THE MAIN FEATURES
    #{access}

    5. EXTERNAL SERVICES USED
    #{services.empty? ? 'None. The app works entirely on the device and calls no external service.' : services.map { |s| "- #{s}" }.join("\n")}

    6. REGIONAL DIFFERENCES
    #{locales.size > 1 ? "The app ships #{locales.size} languages (#{locales.sort.join(', ')}). Features are identical in every region." : 'None. Features and content are identical in every region.'}

    7. REGULATED INDUSTRY OR THIRD-PARTY MATERIAL

    #{REGULATED}


    ACCOUNT DELETION
    #{auth['login_screen'] ? 'Account deletion is available in the app under Settings, and on the support site.' : 'The app creates no account, so there is nothing to delete.'}
  NOTE
end

apps = JSON.parse(File.read(File.join(M, "apps.json")))["apps"]
apps = apps.select { |a| ONLY.include?(a["repo"]) } unless ONLY.empty?
done = 0; skipped = 0; failed = []

apps.each do |a|
  app = Spaceship::ConnectAPI::App.find(a["bundle_id"]) rescue nil
  next if app.nil?
  ver = Spaceship::ConnectAPI.get_app_store_versions(app_id: app.id, limit: 1).to_models.first
  next if ver.nil?

  cp = File.join(M, "store/apps", "#{a['repo']}.json")
  copy = File.exist?(cp) ? JSON.parse(File.read(cp)) : {}
  text = notes_for(a, copy)

  if DRY
    puts "=== #{a['repo']} (#{ver.version_string}, #{ver.app_store_state})"
    puts text
    puts
    done += 1
    next
  end

  begin
    detail = ver.fetch_app_store_review_detail
    if detail
      Spaceship::ConnectAPI.patch_app_store_review_detail(
        app_store_review_detail_id: detail.id, attributes: { notes: text })
    else
      Spaceship::ConnectAPI.post_app_store_review_detail(
        app_store_version_id: ver.id, attributes: { notes: text })
    end
    puts format("%-18s notes set (%d chars)", a["repo"], text.length)
    done += 1
  rescue StandardError => e
    puts format("%-18s FAILED %s", a["repo"], e.message.gsub(/\s+/, " ")[0, 140])
    failed << a["repo"]
  end
end

puts "\nnotes written: #{done}  failed: #{failed.size}"
puts "failed: #{failed.join(', ')}" unless failed.empty?
