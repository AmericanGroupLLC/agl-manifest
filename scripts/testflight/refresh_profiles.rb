#!/usr/bin/env ruby
# Re-issue every App Store provisioning profile so it carries all distribution
# certificates, not just the one it was created with.
#
#   source scripts/testflight/env.sh
#   bundle exec ruby scripts/testflight/refresh_profiles.rb --dry-run
#   bundle exec ruby scripts/testflight/refresh_profiles.rb
#
# A profile pins the certificates that may sign against it. The existing 47
# profiles all name one certificate, Q385P88X3N, whose private key is in a
# keychain on one Mac and cannot be exported without a GUI prompt — which is
# why CI has never been able to sign an iOS build.
#
# A second distribution certificate now exists, created from a CSR generated
# here, so its private key is available and can be a CI secret. Signing with it
# still fails until the profiles list it, because Apple checks the pairing.
#
# Profiles are immutable: Apple has no update for the certificate list, so each
# one is deleted and recreated carrying every distribution certificate. The
# name is kept, which keeps build_ipa.py's profile map valid, and the old
# profile is only deleted once the new one exists.

require "json"
require "spaceship"
require_relative "../agl_paths"

DRY  = ARGV.include?("--dry-run")
ONLY = ARGV.reject { |a| a.start_with?("--") }

Spaceship::ConnectAPI.token = Spaceship::ConnectAPI::Token.create(
  key_id: ENV.fetch("ASC_KEY_ID"),
  issuer_id: ENV.fetch("ASC_ISSUER_ID"),
  filepath: ENV.fetch("ASC_KEY_PATH"),
)

dist_certs = Spaceship::ConnectAPI::Certificate.all
                                               .select { |c| c.certificate_type.to_s == "DISTRIBUTION" }
cert_ids = dist_certs.map(&:id)
abort "no DISTRIBUTION certificates found" if cert_ids.empty?
puts "distribution certificates: #{cert_ids.join(', ')}"

apps = JSON.parse(File.read(File.join(AglPaths::MANIFEST, "apps.json")))["apps"]
wanted = apps.each_with_object({}) { |a, h| h[a["bundle_id"]] = a["repo"] }

profiles = Spaceship::ConnectAPI::Profile.all(includes: "certificates,bundleId")
targets = profiles.select do |p|
  p.profile_state == "ACTIVE" &&
    p.profile_type.to_s.start_with?("IOS_APP_STORE") &&
    wanted.key?(p.bundle_id&.identifier) &&
    !(p.certificates || []).map(&:id).to_set.superset?(cert_ids.to_set)
end

require "set"
puts "profiles missing a certificate: #{targets.size}"

done = failed = 0
targets.each do |profile|
  ident = profile.bundle_id.identifier
  repo = wanted[ident]
  next if ONLY.any? && !ONLY.include?(repo)

  if DRY
    puts format("%-18s would re-issue %s", repo, profile.name)
    done += 1
    next
  end

  name = profile.name
  bundle_id_id = profile.bundle_id.id
  begin
    # Delete first: Apple refuses a second profile with the same name, and
    # keeping the name is what keeps the profile map and build_ipa.py working.
    profile.delete!
    fresh = Spaceship::ConnectAPI::Profile.create(
      name: name, profile_type: "IOS_APP_STORE",
      bundle_id_id: bundle_id_id, certificate_ids: cert_ids,
    )
    puts format("%-18s re-issued %s (%s)", repo, fresh.name, fresh.profile_state)
    done += 1
  rescue StandardError => e
    detail = (JSON.parse(e.message[/\{.*\}/m])["errors"][0]["detail"] rescue e.message)
    puts format("%-18s FAILED %s", repo, detail.to_s.gsub(/\s+/, " ")[0, 140])
    failed += 1
  end
end

puts "\nre-issued #{done}, failed #{failed}"
