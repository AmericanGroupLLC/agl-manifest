#!/usr/bin/env ruby
# Put every app on the free price tier.
#
# Apple rejects submission with "App is missing required pricing. - App is not
# eligible for submission until pricing has been set." A newly created record
# has no price at all, and the old `prices` relationship is retired —
# `app.update(app_price_tier_id:)` now answers "'prices' is not a relationship".
# The current shape is an appPriceSchedule referencing a price point, so this
# finds the app's own 0.00 point in the US and schedules it.
#
#   bundle exec ruby set_free_price.rb            # every app with a record
#   bundle exec ruby set_free_price.rb Verba
require "json"
require "spaceship"

ONLY = ARGV.reject { |a| a.start_with?("--") }
Spaceship::ConnectAPI.token = Spaceship::ConnectAPI::Token.create(
  key_id: ENV.fetch("ASC_KEY_ID"), issuer_id: ENV.fetch("ASC_ISSUER_ID"), filepath: ENV.fetch("ASC_KEY_PATH"))

apps = JSON.parse(File.read(File.expand_path("../../apps.json", __dir__)))["apps"]
apps = apps.select { |a| ONLY.include?(a["repo"]) } unless ONLY.empty?
client = Spaceship::ConnectAPI.tunes_request_client
done = 0; already = 0; failed = []

apps.each do |a|
  app = Spaceship::ConnectAPI::App.find(a["bundle_id"]) rescue nil
  next if app.nil?
  # A schedule object comes back even when Apple still considers the app
  # unpriced, so its presence proves nothing; only manualPrices does.
  begin
    sched = client.get("v1/apps/#{app.id}/appPriceSchedule",
                       { "include" => "manualPrices" }).body
    if (sched["included"] || []).any?
      puts format("%-18s already priced", a["repo"]); already += 1; next
    end
  rescue StandardError
    # no schedule yet, which is the case we are here to fix
  end
  begin
    pts = client.get("v1/apps/#{app.id}/appPricePoints",
                     { "filter[territory]" => "USA", "limit" => 1 }).body["data"]
    free = pts.find { |d| d.dig("attributes", "customerPrice").to_f.zero? }
    raise "no 0.00 price point offered" if free.nil?
    body = {
      data: {
        type: "appPriceSchedules",
        relationships: {
          app: { data: { type: "apps", id: app.id } },
          baseTerritory: { data: { type: "territories", id: "USA" } },
          manualPrices: { data: [{ type: "appPrices", id: "${price}" }] },
        },
      },
      included: [{
        type: "appPrices", id: "${price}",
        relationships: { appPricePoint: { data: { type: "appPricePoints", id: free["id"] } } },
      }],
    }
    client.post("v1/appPriceSchedules", body)
    puts format("%-18s free", a["repo"]); done += 1
  rescue StandardError => e
    msg = e.message.gsub(/\s+/, " ")[0, 160]
    puts format("%-18s FAILED %s", a["repo"], msg); failed << a["repo"]
  end
end

puts "\nset free: #{done}  already priced: #{already}  failed: #{failed.size}"
puts "failed: #{failed.join(', ')}" unless failed.empty?
