#!/usr/bin/env ruby
# Exit 0 if App Store Connect lists a build with this CFBundleVersion, else 1.
#   bundle exec ruby check_build.rb com.americangroupllc.agcleaner 2026091320
# Several pairs at once (one token, one process — run_batch.py --defer-listing
# polls every pending upload together); exit 0 only if every one is listed:
#   bundle exec ruby check_build.rb <bundle_id> <build> <bundle_id> <build> ...
# A query that fails prints UNKNOWN for that pair; it is not counted as listed.
require "spaceship"
abort("usage: check_build.rb <bundle_id> <build_number> [<bundle_id> <build_number> ...]") if ARGV.empty? || ARGV.size.odd?
Spaceship::ConnectAPI.token = Spaceship::ConnectAPI::Token.create(
  key_id: ENV.fetch("ASC_KEY_ID"), issuer_id: ENV.fetch("ASC_ISSUER_ID"), filepath: ENV.fetch("ASC_KEY_PATH"))
all_present = true
ARGV.each_slice(2) do |bundle_id, build_number|
  begin
    app = Spaceship::ConnectAPI::App.find(bundle_id)
    unless app
      puts "ABSENT #{bundle_id} build #{build_number} (no App Store Connect record)"
      all_present = false
      next
    end
    b = Spaceship::ConnectAPI::Build.all(app_id: app.id, sort: "-uploadedDate", limit: 20).find { |x| x.version.to_s == build_number.to_s }
    if b
      puts "PRESENT #{bundle_id} build #{b.version} v#{b.app_version rescue '?'} #{b.processing_state} uploaded #{b.uploaded_date}"
    else
      puts "ABSENT #{bundle_id} build #{build_number}"
      all_present = false
    end
  rescue StandardError => e
    puts "UNKNOWN #{bundle_id} build #{build_number} (#{e.message.lines.first.to_s.strip[0, 160]})"
    all_present = false
  end
end
exit(all_present ? 0 : 1)
