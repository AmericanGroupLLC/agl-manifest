#!/usr/bin/env ruby
# Ask App Store Connect which app records actually exist.
#
# Writes docs/appstore-records.json, which scripts/status.py reads to show a
# per-app "record exists" column. Run it with the same credentials delivery
# uses:
#
#   ASC_KEY_ID=... ASC_ISSUER_ID=... ASC_KEY_PATH=/path/AuthKey_XXX.p8 \
#     bundle exec ruby scripts/appstore_records.rb
#
# A bundle id that does not match a record is not a warning at upload time —
# it is a rejected build with a message about an unknown application.

require "jwt"
require "net/http"
require "json"

key_id    = ENV.fetch("ASC_KEY_ID")
issuer    = ENV.fetch("ASC_ISSUER_ID")
key_path  = ENV.fetch("ASC_KEY_PATH")

key   = OpenSSL::PKey::EC.new(File.read(key_path))
token = JWT.encode(
  { iss: issuer, iat: Time.now.to_i, exp: Time.now.to_i + 300,
    aud: "appstoreconnect-v1" },
  key, "ES256", { kid: key_id, typ: "JWT" }
)

uri = URI("https://api.appstoreconnect.apple.com/v1/apps?limit=200")
req = Net::HTTP::Get.new(uri)
req["Authorization"] = "Bearer #{token}"
res = Net::HTTP.start(uri.hostname, uri.port, use_ssl: true) { |h| h.request(req) }

abort("App Store Connect returned #{res.code}: #{res.body[0, 300]}") unless res.code == "200"

records = (JSON.parse(res.body)["data"] || []).map do |a|
  { "bundleId" => a.dig("attributes", "bundleId"),
    "name" => a.dig("attributes", "name"),
    "sku" => a.dig("attributes", "sku") }
end.sort_by { |r| r["bundleId"].to_s }

File.write("docs/appstore-records.json", JSON.pretty_generate(records) + "\n")
puts "#{records.size} App Store Connect records -> docs/appstore-records.json"
