#!/usr/bin/env ruby
# Exit 0 if App Store Connect lists a build with this CFBundleVersion, else 1.
#   bundle exec ruby check_build.rb com.americangroupllc.agcleaner 2026091320
require "spaceship"
bundle_id, build_number = ARGV
abort("usage: check_build.rb <bundle_id> <build_number>") unless bundle_id && build_number
Spaceship::ConnectAPI.token = Spaceship::ConnectAPI::Token.create(
  key_id: ENV.fetch("ASC_KEY_ID"), issuer_id: ENV.fetch("ASC_ISSUER_ID"), filepath: ENV.fetch("ASC_KEY_PATH"))
app = Spaceship::ConnectAPI::App.find(bundle_id) or abort("#{bundle_id}: no App Store Connect record")
b = Spaceship::ConnectAPI::Build.all(app_id: app.id, sort: "-uploadedDate", limit: 20).find { |x| x.version.to_s == build_number.to_s }
if b
  puts "PRESENT #{bundle_id} build #{b.version} v#{b.app_version rescue '?'} #{b.processing_state} uploaded #{b.uploaded_date}"
  exit 0
else
  puts "ABSENT #{bundle_id} build #{build_number}"
  exit 1
end
