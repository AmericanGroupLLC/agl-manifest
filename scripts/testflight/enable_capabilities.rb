#!/usr/bin/env ruby
# Enable, on each app's Developer Portal App ID, the capabilities its
# ios/Runner/*.entitlements declares — otherwise the App Store profile that
# `ship` generates lacks the entitlement and Xcode refuses to archive
# ("Provisioning profile … doesn't include the com.apple.developer.applesignin
# entitlement"). Idempotent; API key only.
#
#   bundle exec ruby enable_capabilities.rb            # every app in apps.json
#   bundle exec ruby enable_capabilities.rb BodyQuest
require "json"
require "spaceship"

require_relative "../agl_paths"
ROOT = AglPaths::ROOT
apps = JSON.parse(File.read(File.join(AglPaths::MANIFEST, "apps.json")))["apps"]
apps = apps.select { |a| ARGV.include?(a["repo"]) } unless ARGV.empty?

ENTITLEMENT_TO_CAPABILITY = {
  "com.apple.developer.applesignin" => "APPLE_ID_AUTH",
  "aps-environment" => "PUSH_NOTIFICATIONS",
  "com.apple.developer.associated-domains" => "ASSOCIATED_DOMAINS",
  "com.apple.developer.healthkit" => "HEALTHKIT",
  "com.apple.developer.in-app-payments" => "APPLE_PAY",
  "com.apple.security.application-groups" => "APP_GROUPS",
  "keychain-access-groups" => nil, # always available; no capability to enable
}

Spaceship::ConnectAPI.token = Spaceship::ConnectAPI::Token.create(
  key_id: ENV.fetch("ASC_KEY_ID"), issuer_id: ENV.fetch("ASC_ISSUER_ID"), filepath: ENV.fetch("ASC_KEY_PATH"))

apps.each do |a|
  dir = a["dir"] == "." ? "#{ROOT}/#{a['repo']}" : "#{ROOT}/#{a['repo']}/#{a['dir']}"
  keys = Dir["#{dir}/ios/Runner/*.entitlements"].flat_map { |f| File.read(f).scan(/<key>([^<]+)<\/key>/).flatten }.uniq
  wanted = keys.map { |k| ENTITLEMENT_TO_CAPABILITY[k] }.compact.uniq
  unknown = keys.reject { |k| ENTITLEMENT_TO_CAPABILITY.key?(k) }
  puts "#{a['repo']}: MANUAL — unmapped entitlements #{unknown.inspect}" unless unknown.empty?
  next if wanted.empty?

  bid = Spaceship::ConnectAPI::BundleId.all(filter: { identifier: a["bundle_id"] }).find { |b| b.identifier == a["bundle_id"] }
  (puts "#{a['repo']}: bundle id #{a['bundle_id']} not registered"; next) unless bid
  have = Spaceship::ConnectAPI::BundleIdCapability.all(bundle_id_id: bid.id).map(&:capability_type) rescue []
  # bundle_id_capabilities is not always populated by .all; fetch via the bundle id include
  have = bid.get_capabilities.map(&:capability_type) if have.empty? && bid.respond_to?(:get_capabilities)
  wanted.each do |cap|
    if have.include?(cap)
      puts "#{a['repo']}: #{cap} already enabled"
    else
      begin
        # Sign in with Apple must be configured as the primary app (the group
        # configuration needs a server-to-server key and is not what these apps use).
        settings = cap == "APPLE_ID_AUTH" ? [{ key: "APPLE_ID_AUTH_APP_CONSENT", options: [{ key: "PRIMARY_APP_CONSENT" }] }] : []
        Spaceship::ConnectAPI::BundleIdCapability.create(bundle_id_id: bid.id, capability_type: cap, settings: settings)
        puts "#{a['repo']}: #{cap} ENABLED on #{a['bundle_id']}"
      rescue => e
        puts "#{a['repo']}: #{cap} FAILED #{e.message.lines.first.to_s.strip[0, 200]}"
      end
    end
  end
end
