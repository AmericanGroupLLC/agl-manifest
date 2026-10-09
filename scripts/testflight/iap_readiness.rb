#!/usr/bin/env ruby
# Report, per app, whether the in-app purchases the binary sells exist in App
# Store Connect with everything App Review needs before it will look at them.
#
#   source scripts/testflight/env.sh
#   bundle exec ruby scripts/testflight/iap_readiness.rb                 # report
#   bundle exec ruby scripts/testflight/iap_readiness.rb NexusTransferPay
#   bundle exec ruby scripts/testflight/iap_readiness.rb --fix           # fill
#
# NexusTransferPay was rejected on 2026-09-29 under Guideline 2.1(b): "one or
# more of the In-App Purchase products have not been submitted for review ...
# you must provide an App Review screenshot". App Store Connect held no product
# for it at all; the binary queried two subscription ids that had never been
# created. Apple reviews an app and its IAPs together, so either side missing
# stops both. This lines the two sides up:
#
#   code   does the app's pubspec pull in a store-billing plugin?
#   asc    inAppPurchasesV2 and subscriptionGroups/subscriptions, each with its
#          state, review screenshot, localizations and price
#
# and calls out the mismatches: billing code with no products (what Apple
# rejected), products with no billing code, and products missing the metadata
# that has to exist before "Submit for Review" is even offered.
#
# --fix fills only metadata, and only from a source a person wrote down: the
# optional "in_app_purchases" object in store/apps/<repo>.json, keyed by
# product id:
#
#   "in_app_purchases": {
#     "com.example.plus.monthly": {
#       "name": "Plus (monthly)", "description": "...",
#       "review_screenshot": "store/iap/Example/plus_monthly.png"
#     },
#     "group:Plus": { "name": "Plus" }        # subscription group localization
#   }
#
# Nothing is invented: an absent entry stays an honest gap in the report. Price
# is reported and never written — it is a commercial decision. Nothing here
# submits an IAP or an app for review; the account is under an App Review
# freeze (docs/MANUAL_ACTIONS.md MA-043) and submission is a person's call.

require "digest"
require "fileutils"
require "json"
require "net/http"
require "spaceship"
require "uri"
require_relative "../agl_paths"

FIX    = ARGV.include?("--fix")
ONLY   = ARGV.reject { |a| a.start_with?("--") }
HOST   = "https://api.appstoreconnect.apple.com"
LOCALE = "en-US"

# Plugins that put a store purchase flow in the binary.
BILLING_PLUGINS = %w[in_app_purchase purchases_flutter flutter_inapp_purchase].freeze

TOKEN = Spaceship::ConnectAPI::Token.create(
  key_id: ENV.fetch("ASC_KEY_ID"),
  issuer_id: ENV.fetch("ASC_ISSUER_ID"),
  filepath: ENV.fetch("ASC_KEY_PATH"),
)
Spaceship::ConnectAPI.token = TOKEN

def req(verb, path, body = nil)
  uri = URI("#{HOST}/#{path}")
  http = Net::HTTP.new(uri.host, 443)
  http.use_ssl = true
  http.read_timeout = 120
  klass = { get: Net::HTTP::Get, patch: Net::HTTP::Patch, post: Net::HTTP::Post }[verb]
  r = klass.new(uri)
  r["Authorization"] = "Bearer #{TOKEN.text}"
  r["Content-Type"] = "application/json"
  r.body = body.to_json if body
  res = http.request(r)
  [res.code.to_i, (JSON.parse(res.body) rescue {})]
end

def detail_of(out)
  out.dig("errors", 0, "detail").to_s.gsub(/\s+/, " ")
end

# Every page of a collection, so an app with more than one page of products is
# not silently truncated.
def all(path)
  rows = []
  code, out = req(:get, path)
  loop do
    return [code, rows, out] if code >= 300
    rows.concat(out["data"] || [])
    nxt = out.dig("links", "next")
    break unless nxt
    code, out = req(:get, nxt.sub("#{HOST}/", ""))
  end
  [code, rows, out]
end

# Billing plugins declared in the app's own pubspec (not transitive ones).
def billing_plugins(app)
  dir = File.join(AglPaths::ROOT, app["repo"], app["dir"].to_s)
  pubspec = File.join(dir, "pubspec.yaml")
  return nil unless File.exist?(pubspec)
  deps = File.readlines(pubspec).map { |l| l[/^\s{2}([a-z_]+):/, 1] }.compact
  deps & BILLING_PLUGINS
end

# Three-step upload Apple uses for every asset: reserve, PUT the bytes to the
# operations it hands back, then commit with the checksum.
def upload_review_screenshot(kind, rel_type, rel_id, file)
  bytes = File.binread(file)
  code, out = req(:post, "v1/#{kind}", { data: {
    type: kind,
    attributes: { fileName: File.basename(file), fileSize: bytes.bytesize },
    relationships: { rel_type => { data: { type: rel_type == :subscription ? "subscriptions" : "inAppPurchases", id: rel_id } } },
  } })
  return "reserve #{code} #{detail_of(out)[0, 90]}" if code >= 300
  shot_id = out.dig("data", "id")
  (out.dig("data", "attributes", "uploadOperations") || []).each do |op|
    uri = URI(op["url"])
    http = Net::HTTP.new(uri.host, uri.port)
    http.use_ssl = uri.scheme == "https"
    put = Net::HTTP.const_get(op["method"].capitalize).new(uri)
    (op["requestHeaders"] || []).each { |h| put[h["name"]] = h["value"] }
    put.body = bytes.byteslice(op["offset"], op["length"])
    res = http.request(put)
    return "upload #{res.code}" if res.code.to_i >= 300
  end
  code, out = req(:patch, "v1/#{kind}/#{shot_id}", { data: {
    type: kind, id: shot_id,
    attributes: { uploaded: true, sourceFileChecksum: Digest::MD5.hexdigest(bytes) },
  } })
  code >= 300 ? "commit #{code} #{detail_of(out)[0, 90]}" : nil
end

manifest = JSON.parse(File.read(File.join(AglPaths::MANIFEST, "apps.json")))["apps"]
manifest = manifest.select { |a| ONLY.include?(a["repo"]) } if ONLY.any?

by_bundle = {}
Spaceship::ConnectAPI::App.all.each { |a| by_bundle[a.bundle_id] = a }

report = {}
fixed = 0

manifest.each do |a|
  repo = a["repo"]
  meta_f = File.join(AglPaths::MANIFEST, "store/apps", "#{repo}.json")
  meta = File.exist?(meta_f) ? JSON.parse(File.read(meta_f)) : {}
  source = meta["in_app_purchases"] || {}
  plugins = billing_plugins(a)
  entry = { "billing_plugins" => plugins, "products" => [], "issues" => [] }
  report[repo] = entry

  app = by_bundle[a["bundle_id"]]
  unless app
    entry["issues"] << "no App Store Connect record"
    puts format("  %-20s %s", repo, entry["issues"].join("; "))
    next
  end

  # --- one-time purchases (consumable, non-consumable, non-renewing) ----------
  code, iaps, out = all("v1/apps/#{app.id}/inAppPurchasesV2?limit=200")
  entry["issues"] << "inAppPurchasesV2 #{code} #{detail_of(out)[0, 80]}" if code >= 300
  iaps.each do |p|
    at = p["attributes"] || {}
    pid = at["productId"]
    gaps = []
    _, shot = req(:get, "v2/inAppPurchases/#{p['id']}/appStoreReviewScreenshot")
    gaps << "review screenshot" unless shot["data"]
    _, locs = all("v2/inAppPurchases/#{p['id']}/inAppPurchaseLocalizations?limit=50")
    gaps << "localization" if locs.empty?
    # A bare GET of the schedule answers with an empty schedule; ask for the
    # prices in it, the same trap asc_readiness.rb fell into for app pricing.
    pc, sched = req(:get, "v2/inAppPurchases/#{p['id']}/iapPriceSchedule?include=manualPrices")
    gaps << "price" if pc >= 300 || (sched["included"] || []).empty?

    if FIX && (want = source[pid])
      if gaps.include?("localization") && want["name"]
        c, o = req(:post, "v1/inAppPurchaseLocalizations", { data: {
          type: "inAppPurchaseLocalizations",
          attributes: { locale: LOCALE, name: want["name"], description: want["description"] }.compact,
          relationships: { inAppPurchaseV2: { data: { type: "inAppPurchases", id: p["id"] } } },
        } })
        c < 300 ? (fixed += 1; gaps -= ["localization"]) : warn("  #{repo} #{pid}: localization #{c} #{detail_of(o)[0, 90]}")
      end
      file = want["review_screenshot"] && File.join(AglPaths::MANIFEST, want["review_screenshot"])
      if gaps.include?("review screenshot") && file && File.exist?(file)
        err = upload_review_screenshot("inAppPurchaseAppStoreReviewScreenshots", :inAppPurchaseV2, p["id"], file)
        err ? warn("  #{repo} #{pid}: screenshot #{err}") : (fixed += 1; gaps -= ["review screenshot"])
      end
    end

    entry["products"] << { "product_id" => pid, "kind" => at["inAppPurchaseType"],
                           "state" => at["state"], "missing" => gaps }
  end

  # --- auto-renewable subscriptions --------------------------------------------
  code, groups, out = all("v1/apps/#{app.id}/subscriptionGroups?limit=200")
  entry["issues"] << "subscriptionGroups #{code} #{detail_of(out)[0, 80]}" if code >= 300
  groups.each do |g|
    ref = g.dig("attributes", "referenceName")
    _, glocs = all("v1/subscriptionGroups/#{g['id']}/subscriptionGroupLocalizations?limit=50")
    if glocs.empty?
      want = source["group:#{ref}"]
      if FIX && want && want["name"]
        c, o = req(:post, "v1/subscriptionGroupLocalizations", { data: {
          type: "subscriptionGroupLocalizations",
          attributes: { locale: LOCALE, name: want["name"] },
          relationships: { subscriptionGroup: { data: { type: "subscriptionGroups", id: g["id"] } } },
        } })
        c < 300 ? (fixed += 1; glocs = [1]) : warn("  #{repo} group #{ref}: localization #{c} #{detail_of(o)[0, 90]}")
      end
      entry["issues"] << "subscription group #{ref.inspect} has no localization" if glocs.empty?
    end

    _, subs = all("v1/subscriptionGroups/#{g['id']}/subscriptions?limit=200")
    subs.each do |s|
      at = s["attributes"] || {}
      pid = at["productId"]
      gaps = []
      _, shot = req(:get, "v1/subscriptions/#{s['id']}/appStoreReviewScreenshot")
      gaps << "review screenshot" unless shot["data"]
      _, locs = all("v1/subscriptions/#{s['id']}/subscriptionLocalizations?limit=50")
      gaps << "localization" if locs.empty?
      pc, prices = req(:get, "v1/subscriptions/#{s['id']}/prices?limit=1")
      gaps << "price" if pc >= 300 || (prices["data"] || []).empty?

      if FIX && (want = source[pid])
        if gaps.include?("localization") && want["name"]
          c, o = req(:post, "v1/subscriptionLocalizations", { data: {
            type: "subscriptionLocalizations",
            attributes: { locale: LOCALE, name: want["name"], description: want["description"] }.compact,
            relationships: { subscription: { data: { type: "subscriptions", id: s["id"] } } },
          } })
          c < 300 ? (fixed += 1; gaps -= ["localization"]) : warn("  #{repo} #{pid}: localization #{c} #{detail_of(o)[0, 90]}")
        end
        file = want["review_screenshot"] && File.join(AglPaths::MANIFEST, want["review_screenshot"])
        if gaps.include?("review screenshot") && file && File.exist?(file)
          err = upload_review_screenshot("subscriptionAppStoreReviewScreenshots", :subscription, s["id"], file)
          err ? warn("  #{repo} #{pid}: screenshot #{err}") : (fixed += 1; gaps -= ["review screenshot"])
        end
      end

      entry["products"] << { "product_id" => pid, "kind" => "AUTO_RENEWABLE (#{ref})",
                             "state" => at["state"], "missing" => gaps }
    end
  end

  # --- the two sides against each other ------------------------------------------
  if plugins&.any? && entry["products"].empty?
    entry["issues"] << "binary links #{plugins.join(', ')} but App Store Connect has no products " \
                       "(Guideline 2.1(b) risk: create the products or remove the billing code)"
  elsif plugins && plugins.empty? && entry["products"].any?
    entry["issues"] << "products exist but the app declares no billing plugin"
  end
  entry["issues"] << "app checkout not found; billing code not checked" if plugins.nil?
  entry["products"].each do |p|
    entry["issues"] << "#{p['product_id']} (#{p['state']}) missing #{p['missing'].join(', ')}" if p["missing"].any?
  end

  line = entry["products"].empty? ? "no products" :
           entry["products"].map { |p| "#{p['product_id']}=#{p['state']}" }.join(" ")
  line += " | billing: #{plugins.nil? ? '?' : (plugins.empty? ? 'none' : plugins.join(','))}"
  line += " | #{entry['issues'].join('; ')}" if entry["issues"].any?
  puts format("  %-20s %s", repo, line)
end

out = File.join(AglPaths::DIST, "iap-readiness.json")
FileUtils.mkdir_p(File.dirname(out))
File.write(out, JSON.pretty_generate(report) + "\n")
with_products = report.count { |_, e| e["products"].any? }
flagged = report.count { |_, e| e["issues"].any? }
puts "\n#{report.size} apps: #{with_products} with IAP products in App Store Connect, #{flagged} with something to resolve"
puts "wrote #{fixed} change(s)" if FIX
puts "-> #{out}"
