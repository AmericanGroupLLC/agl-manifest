#!/usr/bin/env ruby
# Write .dist/ios/profile_map.json — bundle id => provisioning profile name.
#
#   ASC_KEY_ID=... ASC_ISSUER_ID=... ASC_KEY_PATH=... \
#     bundle exec ruby scripts/ios_profile_map.rb [--install]
#
# scripts/build_ipa.py has read this file since it was written, but nothing in
# the repository ever produced it: the copy on the build Mac was made by hand.
# The ship pipeline's iOS job therefore could not succeed on a fresh runner,
# and the symptom gave no hint of that — a bare
#
#     FileNotFoundError: .../work/.dist/ios/profile_map.json
#
# from inside build_ipa.py, after the checkout and Flutter setup had already
# spent several minutes. Generating the map from the App Store Connect API
# makes the input reproducible and makes a genuinely missing profile say so.
#
# Only App Store profiles are considered. A development profile cannot sign an
# upload, so silently matching one would move the failure to the far slower
# `xcodebuild -exportArchive` step.
#
# With --install the profiles themselves are written into
# ~/Library/MobileDevice/Provisioning Profiles, which is where Xcode looks.
# The names alone are not enough on a fresh runner: export fails with
# "no profile matching" if the file is not installed, whatever the map says.
#
# Note what this does NOT solve: signing also needs the distribution
# certificate's private key, which the API cannot hand out — it has to be
# exported from a keychain as a .p12 and stored as a secret. Tracked as MA-005
# in docs/MANUAL_ACTIONS.md.

require "base64"
require "fileutils"
require "json"
require "spaceship"
require_relative "agl_paths"

WANTED_STATE = "ACTIVE".freeze

def main
  Spaceship::ConnectAPI.token = Spaceship::ConnectAPI::Token.create(
    key_id: ENV.fetch("ASC_KEY_ID"),
    issuer_id: ENV.fetch("ASC_ISSUER_ID"),
    filepath: ENV.fetch("ASC_KEY_PATH"),
  )

  apps = JSON.parse(File.read(File.join(AglPaths::MANIFEST, "apps.json")))["apps"]
  wanted = apps.each_with_object({}) { |a, h| h[a["bundle_id"]] = a["repo"] }

  profiles = Spaceship::ConnectAPI::Profile.all(includes: "bundleId")

  # An app can carry several profiles. Prefer an active App Store one, and
  # among those the one that expires last, so a map generated today does not
  # pick a profile that stops working next week.
  best = {}
  profiles.each do |p|
    next unless p.profile_type.to_s.start_with?("IOS_APP_STORE")
    next unless p.profile_state.to_s == WANTED_STATE
    id = p.bundle_id&.identifier
    next unless id && wanted.key?(id)
    current = best[id]
    best[id] = p if current.nil? ||
                    p.expiration_date.to_s > current.expiration_date.to_s
  end

  map = best.transform_values(&:name)

  if ARGV.include?("--install")
    dir = File.expand_path("~/Library/MobileDevice/Provisioning Profiles")
    FileUtils.mkdir_p(dir)
    installed = 0
    best.each_value do |profile|
      content = profile.profile_content
      next if content.nil? || content.empty?
      # uuid is the filename Xcode expects; the display name is not unique.
      File.binwrite(File.join(dir, "#{profile.uuid}.mobileprovision"),
                    Base64.decode64(content))
      installed += 1
    end
    puts "installed #{installed} profile(s) into #{dir}"
  end

  out = File.join(AglPaths::DIST, "ios", "profile_map.json")
  FileUtils.mkdir_p(File.dirname(out))
  File.write(out, JSON.pretty_generate(map) + "\n")

  missing = wanted.keys.reject { |id| map.key?(id) }.sort
  puts "#{map.size}/#{wanted.size} bundle ids mapped -> #{out}"
  unless missing.empty?
    puts "no active App Store profile for #{missing.size}:"
    missing.each { |id| puts "  #{wanted[id]}  #{id}" }
  end
  0
end

exit(main) if $PROGRAM_NAME == __FILE__
