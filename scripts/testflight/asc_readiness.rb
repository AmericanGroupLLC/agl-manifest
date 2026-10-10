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

def detail_of(out)
  out.dig("errors", 0, "detail").to_s.gsub(/\s+/, " ")
end

# Demo-account passwords, read from the integration guide at push time.
#
# store/apps/*.json names the reviewer account but deliberately does not carry
# its password: the guide already holds it, and copying it into 15 more
# committed files would be 15 more places to leak it from. Overridable with
# AGL_DEMO_PASSWORD for a run that must not touch the guide.
GUIDE = File.join(AglPaths::MANIFEST,
                  "AmericanGroupLLC — Complete Developer Integration Guide.md")
DEMO_PW = begin
  pw = {}
  if File.exist?(GUIDE)
    File.read(GUIDE).scan(/\|\s*\*\*\w+\*\*\s*\|\s*`([^`]+@[^`]+)`\s*\|\s*`([^`]+)`/) do |email, secret|
      pw[email] = secret
    end
  end
  pw
end

# The review-contact and demo-account attributes Apple should hold for an app.
def review_attrs(meta, defaults)
  ri = meta["review_information"] || {}
  attrs = {
    contactFirstName: ri["first_name"] || defaults["review_contact_first"] || "App",
    contactLastName: ri["last_name"] || defaults["review_contact_last"] || "Support",
    contactEmail: ri["email_address"] || defaults["support_email"] || "contact@americangroup.ai",
    contactPhone: ri["phone_number"] || defaults["support_phone"] || "+1 669 388 1960",
    demoAccountRequired: false,
  }
  user = ri["demo_account_name"].to_s
  secret = ENV["AGL_DEMO_PASSWORD"] || DEMO_PW[user]
  # Never advertise an account without the password to use it — a reviewer who
  # is handed a username and no secret is a Guideline 2.1 rejection with extra
  # steps.
  if ri["demo_account_required"] && !user.empty? && secret
    attrs[:demoAccountRequired] = true
    attrs[:demoAccountName] = user
    attrs[:demoAccountPassword] = secret
  end
  attrs
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
        attrs["privacyPolicyUrl"] = "https://www.americangroup.ai/policy/#{slug}/privacy.html" if pp.to_s.empty?
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
  vl_id = nil
  version = app.get_app_store_versions(filter: { platform: "IOS" }).first rescue nil
  if version
    _, vlocs = req(:get, "v1/appStoreVersions/#{version.id}/appStoreVersionLocalizations")
    vl = (vlocs["data"] || []).find { |l| l.dig("attributes", "locale") == "en-US" }
    vl_id = vl && vl["id"]
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
          attrs["supportUrl"] = (defaults["support_url_template"] || "https://www.americangroup.ai/policy/{slug}/support.html")
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

  # --- what only an actual submission attempt revealed -----------------------
  # Everything above came from the "Unable to Add for Review" list. These four
  # are not on that list and are not refused at save time either: the version
  # saves clean and then POST reviewSubmissions answers
  #
  #   The provided entity is missing a required attribute - You must provide a
  #   value for the attribute 'copyright' with this request
  #   The appStoreReviewDetail associated with appStoreVersions ... was not found
  #   App screenshot missing (APP_IPAD_PRO_3GEN_129)
  #
  # so an audit that never tries to submit cannot see them. Age ratings are the
  # fourth and belong to sync_age_rating.rb, which owns store/ratings/*.json.
  if version
    _, vfull = req(:get, "v1/appStoreVersions/#{version.id}")
    if vfull.dig("data", "attributes", "copyright").to_s.empty?
      gaps << "copyright"
      if FIX
        code, out = req(:patch, "v1/appStoreVersions/#{version.id}",
                        { data: { type: "appStoreVersions", id: version.id,
                                  attributes: { copyright: defaults["copyright"] ||
                                                "#{Time.now.year} American Group LLC" } } })
        code < 300 ? (fixed += 1; gaps -= ["copyright"]) : warn("  #{repo}: copyright #{code} #{detail_of(out)[0, 90]}")
      end
    end

    # The detail is created when absent *and corrected when present*. It used
    # to be create-only, so the 15 apps that already had a detail kept
    # demoAccountRequired: false for ever — including the ones that open on a
    # sign-in wall. Apple cannot review what it cannot sign in to.
    want = review_attrs(meta, defaults)
    rd_code, rd = req(:get, "v1/appStoreVersions/#{version.id}/appStoreReviewDetail")
    if rd_code >= 300
      gaps << "appStoreReviewDetail"
      if FIX
        code, out = req(:post, "v1/appStoreReviewDetails", {
                          data: {
                            type: "appStoreReviewDetails",
                            attributes: want,
                            relationships: { appStoreVersion: {
                              data: { type: "appStoreVersions", id: version.id } } },
                          },
                        })
        code < 300 ? (fixed += 1; gaps -= ["appStoreReviewDetail"]) : warn("  #{repo}: reviewDetail #{code} #{detail_of(out)[0, 90]}")
      end
    else
      have = rd.dig("data", "attributes") || {}
      rd_id = rd.dig("data", "id")
      # Apple never returns the stored password, so it cannot be compared;
      # drift is judged on the account name and the required flag.
      stale = have["demoAccountRequired"] != want[:demoAccountRequired] ||
              have["demoAccountName"].to_s != want[:demoAccountName].to_s
      if stale
        gaps << "demo account"
        if FIX && rd_id
          code, out = req(:patch, "v1/appStoreReviewDetails/#{rd_id}",
                          { data: { type: "appStoreReviewDetails", id: rd_id,
                                    attributes: want } })
          code < 300 ? (fixed += 1; gaps -= ["demo account"]) : warn("  #{repo}: demo account #{code} #{detail_of(out)[0, 90]}")
        end
      end
    end

    # Screenshots are reported, never invented: the files come from
    # scripts/screenshots.py and uploading a wrong-sized image is worse than
    # an honest gap. Apple accepts 6.7" in place of 6.5", so either satisfies
    # the iPhone requirement.
    if vl_id
      _, sets = req(:get, "v1/appStoreVersionLocalizations/#{vl_id}/appScreenshotSets")
      have = (sets["data"] || []).map { |s| s.dig("attributes", "screenshotDisplayType") }
      gaps << "screenshots:iphone" if (have & %w[APP_IPHONE_67 APP_IPHONE_65]).empty?
      gaps << "screenshots:ipad" if !have.include?("APP_IPAD_PRO_3GEN_129")
    end
  end

  # --- age rating and price: reported, and price never written ---------------
  # An appInfo that is IN_REVIEW is read-only, so an unanswered field on one is
  # not something to act on — the app is already with Apple. Reporting it as a
  # gap sends you chasing a PATCH that Apple will refuse.
  if info_id && info.dig("attributes", "state") != "IN_REVIEW"
    _, ard = req(:get, "v1/appInfos/#{info_id}/ageRatingDeclaration")
    at = ard.dig("data", "attributes") || {}
    # kidsAgeBand only applies to the Kids category, and the last two are
    # optional everywhere; Apple does not require any of the three.
    optional = %w[kidsAgeBand gracRatingClassificationNumber developerAgeRatingInfoUrl]
    unanswered = at.reject { |k, v| !v.nil? || optional.include?(k) }
    gaps << "ageRating(#{unanswered.size} unanswered)" if unanswered.any?
  end
  # Pricing was on the "Unable to Add for Review" list and this check used to
  # pass every app anyway — a bare GET of appPriceSchedule answers 200 with a
  # schedule object that has no price in it. Three apps reported ready and
  # then failed submission with "App is missing required pricing. App is not
  # eligible for submission until pricing has been set." Ask for the prices
  # themselves and count them.
  pc, price = req(:get, "v1/apps/#{app.id}/appPriceSchedule?include=manualPrices")
  gaps << "price" if pc >= 300 || (price["included"] || []).empty?

  report[repo] = gaps
  puts format("  %-18s %s", repo, gaps.empty? ? "ready" : gaps.join(", "))
end

out = File.join(AglPaths::DIST, "asc-readiness.json")
File.write(out, JSON.pretty_generate(report) + "\n")
ready = report.count { |_, g| g.empty? }
puts "\n#{report.size} apps: #{ready} with nothing outstanding"
puts "wrote #{fixed} change(s)" if FIX
puts "-> #{out}"
