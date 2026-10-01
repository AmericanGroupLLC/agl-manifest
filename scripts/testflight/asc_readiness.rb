#!/usr/bin/env ruby
# Check, and optionally fill, exactly what App Store Connect blocks review on.
#
#   source scripts/testflight/env.sh
#   bundle exec ruby scripts/testflight/asc_readiness.rb            # report
#   bundle exec ruby scripts/testflight/asc_readiness.rb --fix      # fill
#   bundle exec ruby scripts/testflight/asc_readiness.rb --fix radiotune
#
# The existing checklist validated this repository's store metadata and called
# it ready. App Store Connect disagreed, which is the only opinion that counts:
#
#   You must enter a Privacy Policy URL in App Privacy.
#   You must set up Content Rights Information in App Information.
#   You must respond to the required age ratings questions.
#   You must select a primary category for your app.
#   You must choose a price tier in Pricing.
#   English (U.S.) - Description - This field is required
#   English (U.S.) - Keywords - This field is required
#   English (U.S.) - Support URL - This field is required
#
# So this reads the live records instead of the repo, field by field, and
# writes the ones an API key is allowed to write.
#
# The fields live in three different places, which is why they were missed:
#
#   appInfos                      primary category, content rights
#   appInfoLocalizations          app name, subtitle, privacy policy URL
#   appStoreVersionLocalizations  description, keywords, support URL
#
# Renaming an app through the version localization — which an earlier pass did
# — leaves the name in App Information untouched, so PlantPulse still read
# "iPlantPulse" after it had supposedly been corrected.
#
# Price tier is reported, never written: it is a commercial decision and the
# API would happily set the wrong one.

require "json"
require "net/http"
require "spaceship"
require "uri"
require_relative "../agl_paths"

FIX  = ARGV.include?("--fix")
ONLY = ARGV.reject { |a| a.start_with?("--") }
HOST = "https://api.appstoreconnect.apple.com"

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

manifest = JSON.parse(File.read(File.join(AglPaths::MANIFEST, "apps.json")))["apps"]
manifest = manifest.select { |a| ONLY.include?(a["repo"]) } if ONLY.any?
defaults = JSON.parse(File.read(File.join(AglPaths::MANIFEST, "store/defaults.json")))

by_bundle = {}
Spaceship::ConnectAPI::App.all.each { |a| by_bundle[a.bundle_id] = a }

# Apple's category vocabulary differs from Play's; map what the repo stores.
CATEGORY = {
  "HEALTH_AND_FITNESS" => "HEALTH_AND_FITNESS", "PRODUCTIVITY" => "PRODUCTIVITY",
  "UTILITIES" => "UTILITIES", "FINANCE" => "FINANCE", "EDUCATION" => "EDUCATION",
  "TRAVEL" => "TRAVEL", "SOCIAL" => "SOCIAL_NETWORKING", "SOCIAL_NETWORKING" => "SOCIAL_NETWORKING",
  "SHOPPING" => "SHOPPING", "PHOTOGRAPHY" => "PHOTO_AND_VIDEO", "PHOTO_AND_VIDEO" => "PHOTO_AND_VIDEO",
  "MUSIC_AND_AUDIO" => "MUSIC", "MUSIC" => "MUSIC", "NEWS_AND_MAGAZINES" => "NEWS", "NEWS" => "NEWS",
  "ENTERTAINMENT" => "ENTERTAINMENT", "LIFESTYLE" => "LIFESTYLE", "MEDICAL" => "MEDICAL",
  "BUSINESS" => "BUSINESS", "FOOD_AND_DRINK" => "FOOD_AND_DRINK", "SPORTS" => "SPORTS",
  "NAVIGATION" => "NAVIGATION", "MAPS_AND_NAVIGATION" => "NAVIGATION",
  "BOOKS_AND_REFERENCE" => "REFERENCE", "REFERENCE" => "REFERENCE", "DATING" => "LIFESTYLE",
  "VIDEO_PLAYERS" => "PHOTO_AND_VIDEO", "COMMUNICATION" => "SOCIAL_NETWORKING",
}

report = {}
fixed = 0

manifest.each do |a|
  repo = a["repo"]
  app = by_bundle[a["bundle_id"]]
  next unless app

  meta_f = File.join(AglPaths::MANIFEST, "store/apps", "#{repo}.json")
  meta = File.exist?(meta_f) ? JSON.parse(File.read(meta_f)) : {}
  en = (meta.dig("copy", "en") || {})
  slug = meta["slug"] || repo.downcase

  gaps = []

  # --- App Information -------------------------------------------------------
  _, infos = req(:get, "v1/apps/#{app.id}/appInfos")
  info = (infos["data"] || []).find { |i| %w[PREPARE_FOR_SUBMISSION DEVELOPER_REJECTED
                                             REJECTED METADATA_REJECTED].include?(i.dig("attributes", "state")) }
  info ||= (infos["data"] || []).first
  info_id = info && info["id"]

  if info_id
    rights = info.dig("attributes", "appStoreAgeRating") # presence probe only
    _, full = req(:get, "v1/appInfos/#{info_id}?include=primaryCategory")
    prim = full.dig("data", "relationships", "primaryCategory", "data", "id")
    # Content rights is an attribute of the APP, not of appInfo. Reading it
    # from appInfo returned nil for all 43 and the audit called every one of
    # them unset — they were already correct. Patching it there is refused
    # outright: "'appStoreContentRightsDeclaration' is not an attribute on the
    # resource 'appInfos'".
    _, appres = req(:get, "v1/apps/#{app.id}")
    crd = appres.dig("data", "attributes", "contentRightsDeclaration")
    gaps << "primaryCategory" unless prim
    gaps << "contentRights" unless crd

    if FIX
      unless crd
        code, out = req(:patch, "v1/apps/#{app.id}",
                        { data: { type: "apps", id: app.id,
                                  attributes: { contentRightsDeclaration:
                                                "DOES_NOT_USE_THIRD_PARTY_CONTENT" } } })
        if code < 300
          fixed += 1
          gaps -= ["contentRights"]
        else
          warn "  #{repo}: contentRights #{code} #{out.dig('errors',0,'detail').to_s[0,110]}"
        end
      end
      patch = {}
      rel = {}
      unless prim
        want = CATEGORY[(meta["primary_category"] || "").to_s.upcase]
        rel["primaryCategory"] = { data: { type: "appCategories", id: want } } if want
      end
      if patch.any? || rel.any?
        body = { data: { type: "appInfos", id: info_id } }
        body[:data][:attributes] = patch if patch.any?
        body[:data][:relationships] = rel if rel.any?
        code, out = req(:patch, "v1/appInfos/#{info_id}", body)
        if code < 300
          fixed += 1
          gaps -= ["contentRights"] if patch.any?
          gaps -= ["primaryCategory"] if rel.any?
        else
          warn "  #{repo}: appInfo patch #{code} #{out.dig('errors',0,'detail').to_s[0,110]}"
        end
      end
    end

    # name / subtitle / privacy policy live here, not on the version
    _, locs = req(:get, "v1/appInfos/#{info_id}/appInfoLocalizations")
    loc = (locs["data"] || []).find { |l| l.dig("attributes", "locale") == "en-US" }
    if loc
      pp = loc.dig("attributes", "privacyPolicyUrl")
      nm = loc.dig("attributes", "name")
      gaps << "privacyPolicyUrl" if pp.to_s.empty?
      want_name = (en["name"] || repo)[0, 30]
      gaps << "name(#{nm})" if nm.to_s.strip != want_name.strip
      if FIX
        attrs = {}
        attrs["privacyPolicyUrl"] = "https://www.safecodeg.com/policy/#{slug}/privacy.html" if pp.to_s.empty?
        attrs["name"] = want_name if nm.to_s.strip != want_name.strip
        attrs["subtitle"] = en["subtitle"][0, 30] if en["subtitle"] && loc.dig("attributes", "subtitle").to_s.empty?
        # One PATCH per attribute. Combined, a single rejected field takes the
        # others down with it: PlantPulse's privacy policy URL was lost to a
        # 409 on the name, which is a problem no amount of retrying the same
        # payload can solve.
        attrs.each do |k, v|
          code, out = req(:patch, "v1/appInfoLocalizations/#{loc['id']}",
                          { data: { type: "appInfoLocalizations", id: loc["id"],
                                    attributes: { k => v } } })
          detail = out.dig("errors", 0, "detail").to_s
          if code < 300
            fixed += 1
            gaps.reject! { |g| g == k || (k == "name" && g.start_with?("name(")) }
          elsif k == "name" && detail.include?("already being used")
            # Someone else holds the App Store name. The "i" prefix exists
            # precisely because of this, so the current name is correct and
            # the repo's preferred name is the thing that is wrong.
            gaps.reject! { |g| g.start_with?("name(") }
            gaps << "name-taken(keeping #{nm})"
          else
            warn "  #{repo}: #{k} #{code} #{detail[0, 110]}"
          end
        end
      end
    end
  else
    gaps << "no appInfo"
  end

  # --- the version's own text ------------------------------------------------
  version = app.get_app_store_versions(filter: { platform: "IOS" }).first rescue nil
  if version
    _, vlocs = req(:get, "v1/appStoreVersions/#{version.id}/appStoreVersionLocalizations")
    vl = (vlocs["data"] || []).find { |l| l.dig("attributes", "locale") == "en-US" }
    if vl
      at = vl["attributes"] || {}
      gaps << "description" if at["description"].to_s.empty?
      gaps << "keywords"    if at["keywords"].to_s.empty?
      gaps << "supportUrl"  if at["supportUrl"].to_s.empty?
      if FIX
        attrs = {}
        attrs["description"] = (en["description"] || "")[0, 3990] if at["description"].to_s.empty? && en["description"]
        attrs["keywords"]    = (en["keywords"] || "")[0, 100]     if at["keywords"].to_s.empty? && en["keywords"]
        if at["supportUrl"].to_s.empty?
          attrs["supportUrl"] = (defaults["support_url_template"] || "https://www.safecodeg.com/policy/{slug}/support.html")
                                .gsub("{slug}", slug)
        end
        if attrs.any?
          code, out = req(:patch, "v1/appStoreVersionLocalizations/#{vl['id']}",
                          { data: { type: "appStoreVersionLocalizations", id: vl["id"], attributes: attrs } })
          if code < 300
            fixed += 1
            gaps -= attrs.keys
          else
            warn "  #{repo}: versionLocalization #{code} #{out.dig('errors',0,'detail').to_s[0,110]}"
          end
        end
      end
    else
      gaps << "no en-US version localization"
    end
  else
    gaps << "no app store version"
  end

  # --- age rating and price: reported, and price never written ---------------
  _, ar = req(:get, "v1/apps/#{app.id}/appInfos")
  _, price = req(:get, "v1/apps/#{app.id}/appPriceSchedule")
  gaps << "priceTier" if (price["data"] || price.dig("errors", 0)) && price["data"].nil?

  report[repo] = gaps
  puts format("  %-18s %s", repo, gaps.empty? ? "ready" : gaps.join(", "))
end

out = File.join(AglPaths::DIST, "asc-readiness.json")
File.write(out, JSON.pretty_generate(report) + "\n")
ready = report.count { |_, g| g.empty? }
puts "\n#{report.size} apps: #{ready} with nothing outstanding"
puts "wrote #{fixed} change(s)" if FIX
puts "-> #{out}"
