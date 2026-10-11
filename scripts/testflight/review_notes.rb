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

def services_for(a, omit = [])
  path = File.join(app_dir(a), "pubspec.yaml")
  return [] unless File.exist?(path)
  deps = File.read(path).split("dev_dependencies").first.to_s
  SERVICES.reject { |k, _| omit.include?(k) }
          .select { |k, _| deps.match?(/^\s{2}#{Regexp.escape(k)}\s*:/) }.values
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

LANG = {
  "ar" => "Arabic", "de" => "German", "en" => "English", "es" => "Spanish",
  "fr" => "French", "hi" => "Hindi", "it" => "Italian", "ja" => "Japanese",
  "ko" => "Korean", "pt" => "Portuguese", "ru" => "Russian",
  "zh" => "Chinese (Simplified)",
}.freeze

# The twelve the shared agl_i18n package translates. An app's own ARB folder
# is usually a subset of this — the rest of its strings come from the package
# — so the package list, not the app's, is what the binary actually ships.
SHARED_LOCALES = Dir[File.join(M, "packages/agl_i18n/lib/l10n/agl_*.arb")]
                 .map { |f| File.basename(f, ".arb").sub("agl_", "") }.sort

# Declaring 12 locales is not translating 12 locales: most apps translate the
# shared labels (agl_i18n) and leave their own screens in English. Telling App
# Review "the app ships 12 languages" for those was a false claim that the
# 2026-10-11 verification found re-appearing in Verba, GadgetNest and others
# whenever this generator ran. The claim now follows docs/i18n-audit.json.
def regional_text(a, locales)
  return "None. Features and content are identical in every region." if locales.size <= 1
  row = I18N[a["repo"]] || {}
  ui, done = row["ui_files"].to_i, row["ui_files_localized"].to_i
  names = locales.sort.join(", ")
  if ui.positive? && done >= ui && row["hardcoded_ui_strings"].to_i.zero?
    "The app is translated into #{locales.size} languages (#{names}). Features are identical in every region."
  else
    "The app follows the device language for #{locales.size} locales (#{names}), but translation is partial: " \
      "shared labels are translated, while most screen text is in English only. Features are identical in every region."
  end
end

def locales_for(a)
  row = I18N[a["repo"]] || {}
  n = row["declared_locales"].to_i
  return [] if n <= 1
  arb = row["arb_locales"]
  arb = SHARED_LOCALES unless arb.is_a?(Array) && arb.size >= n
  # Previously this fell through to "locale 1, locale 2, ..." whenever the
  # app's own ARB set was smaller than its declared count — which is the
  # normal case. Apple was being told the app ships "locale 1, locale 10,
  # locale 11", which reads exactly like the templated output Guideline 4.3
  # screens for. Codes are mapped to names for the same reason.
  arb.sort.map { |c| LANG[c] || c }
end

# Stated plainly because Apple asks what the build was tested on, and the
# honest answer is simulators and emulators rather than a device lab.
TEST_DEVICES = "iPhone 17 Pro Max and iPad Pro 13-inch simulators on iOS 26, " \
               "and a Pixel Android emulator on API 34".freeze

REGULATED = "The app is not in a regulated industry and carries no licensed " \
            "third-party material. All content, artwork and copy are the " \
            "developer's own.".freeze

# App-specific answers live in their own fields of review_information and are
# always carried into the generated text. Until 2026-10-09 this script rebuilt
# every app's notes from the template alone and pushed them to App Store
# Connect on each scheduled pass, which erased WiFiTrail's answer to Apple's
# VPN question, CalcMaster's description of where the ATT prompt appears,
# CodeDeal's in-app sign-in instructions and the real deletion paths — both
# here and in the notes Apple reads.
#   access            replaces the generic "SETTING UP AND REACHING" text
#   account_deletion  replaces the generic deletion sentence
#   services_extra    extra lines for EXTERNAL SERVICES (keyless HTTP APIs)
#   services_omit     pubspec packages whose generic SERVICES line is wrong
#                     for this app (e.g. "http" when the app calls third-party
#                     APIs, not its own endpoints); list them in services_extra
#   regulated         replaces the generic REGULATED sentence in section 7,
#                     for apps that do carry third-party material
#   notes_extra       appended verbatim, as its own sections, at the end
def notes_for(a, copy)
  ri = copy["review_information"] || {}
  en = copy.dig("copy", "en") || {}
  purpose = en["description"].to_s.split("\n\n").first.to_s.strip
  purpose = en["short_description"].to_s if purpose.empty?
  audience = en["subtitle"].to_s
  auth = a["auth"] || {}
  # Keyless public APIs reached over plain HTTP have no pubspec dependency to
  # name them, so the app's own record lists them (services_extra).
  omit = Array(ri["services_omit"]).map(&:to_s)
  services = services_for(a, omit) + Array(ri["services_extra"]).map(&:to_s).reject(&:empty?)
  locales = locales_for(a)

  access =
    if auth["login_screen"]
      "The app opens on a sign-in screen. #{auth['account_optional'] ? 'An account is optional; the main features can be reached without signing in.' : 'Test credentials are in the demo account fields of App Review Information.'}"
    else
      "No account and no login are required. Every feature is reachable from the first screen after launch."
    end

  access = ri["access"].to_s.strip unless ri["access"].to_s.strip.empty?
  deletion = if !ri["account_deletion"].to_s.strip.empty?
               ri["account_deletion"].to_s.strip
             elsif auth["login_screen"]
               "Account deletion is available in the app under Settings, and on the support site."
             else
               "The app creates no account, so there is nothing to delete."
             end
  extra = ri["notes_extra"].to_s.strip
  regulated = ri["regulated"].to_s.strip
  regulated = REGULATED if regulated.empty?

  text = <<~NOTE.strip
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
    #{regional_text(a, locales)}

    7. REGULATED INDUSTRY OR THIRD-PARTY MATERIAL

    #{regulated}


    ACCOUNT DELETION
    #{deletion}
  NOTE
  extra.empty? ? text : "#{text}\n\n#{extra}"
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

  # Write the same text back into store/apps/<repo>.json so the repository
  # and App Store Connect say the same thing. They did not: the checklist
  # read the stored notes, which still answered Apple's old five-item
  # request, and reported PASS while the live notes were a different text.
  begin
    raw = File.exist?(cp) ? File.read(cp) : "{}"
    cp_json = JSON.parse(raw)
    cp_json["review_information"] ||= {}
    if cp_json["review_information"]["notes"] != text
      cp_json["review_information"]["notes"] = text
      # Keep the file's own format (these are written by Python with a
      # one-space indent and \u escapes); rewriting every file in Ruby's
      # default style turned a one-line change into a whole-file diff.
      indent = raw.start_with?("{\n ") && !raw.start_with?("{\n  ") ? " " : "  "
      File.write(cp, JSON.pretty_generate(cp_json, indent: indent, ascii_only: raw.include?("\\u")) + "\n")
    end
  rescue StandardError => e
    warn "  #{a['repo']}: could not update #{cp}: #{e.message[0, 90]}"
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
