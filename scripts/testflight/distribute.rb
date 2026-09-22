#!/usr/bin/env ruby
# Make every uploaded TestFlight build reachable by the team's testers.
#
# Two groups per app, because they behave differently.
#
#   AGL Internal (internal, hasAccessToAllBuilds) — every App Store Connect
#     account user. Apple makes every uploaded build available to these people
#     immediately, with no Beta App Review, which is what "the build appears on
#     their phone" actually requires.
#
#   AGL Testers (external) — anyone on the roster who is not an account user.
#     Apple reviews each build before an external group receives it.
#
# Creating the internal group needs a raw request: spaceship's create_beta_group
# always sends publicLinkLimitEnabled, and App Store Connect refuses that on an
# internal group ("Public link limit cannot be applied to internal group").
# Getting that wrong is what made internal groups look impossible to fill.
#
#   bundle exec ruby distribute.rb --report          # what each app has today
#   bundle exec ruby distribute.rb --app CalcMaster  # one app
#   bundle exec ruby distribute.rb --all             # every uploaded build
#   bundle exec ruby distribute.rb --all --no-submit # stop before Beta App Review
require "json"
require "spaceship"
require "shellwords"
require "fileutils"

# ROOT is where the scratch artefacts live (.dist); MANIFEST is this repository.
# On this Mac the repository sits inside ROOT, but in CI the checkout is the
# repository and there is no enclosing agl directory, so the two must be separate.
MANIFEST  = File.expand_path("../..", __dir__)
ROOT      = ENV.fetch("AGL_ROOT", File.expand_path("..", MANIFEST))
GROUP     = "AGL Testers"     # external: reviewed before delivery
INTERNAL  = "AGL Internal"     # internal: every build, immediately, no review
# The review contact already recorded on this account (Kinnav's betaAppReviewDetail).
# Apple rejects invented phone numbers, and this is the number the team already gave.
CONTACT   = { firstName: "Shivani", lastName: "Patel",
              email: "shivanipatel89@gmail.com", phone: "6507044568" }.freeze
WHATS_NEW = "Full app walkthrough. Please try every screen and report anything that looks wrong."

SLUGS = { "TripNest" => "TripNest", "AGrammarly" => "agrammarly", "BodyQuest" => "bodyquest",
          "CalcMaster" => "calcmaster", "CarDeal" => "cardeal", "daily-pulse" => "dailypulse",
          "DriftDate" => "driftdate", "FashionFactory" => "fashionfactory", "GroceryMatch" => "grocerymatch",
          "HerJourney" => "herjourney", "iMaps" => "iMaps", "iMeasure" => "iMeasure", "MyHealth" => "myhealth",
          "Photriya" => "photriya", "PilotEnRoute" => "pilotenroute", "radiotune" => "radiotune",
          "Uscis-Case" => "uscis-case-tracker", "Verba" => "verba", "VirtuBand" => "virtuband" }.freeze
def policy_url(repo) = "https://www.safecodeg.com/policy/#{SLUGS.fetch(repo, repo.downcase)}/"

REPORT = ARGV.include?("--report")
STATE  = ARGV.include?("--state")
SYNC   = ARGV.include?("--sync")   # membership only: no metadata, no review submission
ALL    = ARGV.include?("--all")
SUBMIT = !ARGV.include?("--no-submit")
ONLY   = ARGV.each_cons(2).find { |a, _| a == "--app" }&.last

Spaceship::ConnectAPI.token = Spaceship::ConnectAPI::Token.create(
  key_id: ENV.fetch("ASC_KEY_ID"), issuer_id: ENV.fetch("ASC_ISSUER_ID"), filepath: ENV.fetch("ASC_KEY_PATH"))

apps    = JSON.parse(File.read(File.join(MANIFEST, "apps.json")))["apps"]
results = JSON.parse(File.read("#{ROOT}/.dist/ios-batch/results.json")) rescue {}
HAVE_RESULTS = !results.empty?
apps    = apps.select { |a| a["repo"] == ONLY } if ONLY
apps    = apps.select { |a| results.dig(a["repo"], "status") == "uploaded" } if !ONLY && HAVE_RESULTS

# Who should receive builds: everyone in App Store Connect's Users and Access
# (GET /v1/users), plus anyone already recorded as a beta tester. Names come
# from Apple rather than being invented, so nobody shows up misnamed.
roster = {}
account = {}
begin
  Spaceship::ConnectAPI::User.all.each do |u|
    next if u.username.to_s.empty?
    rec = { email: u.username, firstName: u.first_name.to_s, lastName: u.last_name.to_s }
    roster[u.username.downcase] = rec
    account[u.username.downcase] = rec
  end
rescue StandardError => e
  warn "could not read account users: #{e.message.lines.first}"
end
Spaceship::ConnectAPI::BetaTester.all.each do |t|
  next if t.email.to_s.empty?
  roster[t.email.downcase] ||= { email: t.email, firstName: t.first_name.to_s, lastName: t.last_name.to_s }
end
TEAM = roster.values.freeze
ACCOUNT_USERS = account.values.freeze
abort "no testers and no account users found" if TEAM.empty?
FileUtils.mkdir_p(File.join(ROOT, ".dist"))
File.write(File.join(ROOT, ".dist/tester-roster.json"), JSON.pretty_generate(TEAM))

def say(repo, msg) = puts(format("%-18s %s", repo, msg))

def ensure_group(app)
  g = app.get_beta_groups.find { |x| x.name == GROUP }
  return g if g
  Spaceship::ConnectAPI.create_beta_group(app_id: app.id, group_name: GROUP, is_internal_group: false).to_models.first
end

# The internal group has one owner, scripts/sync_testflight_testers.rb, so the
# logic is not written twice. Shipping one app still needs it done immediately,
# hence the shell-out rather than a second implementation.
def sync_internal(repo)
  out = `cd #{MANIFEST.shellescape} && bundle exec ruby scripts/sync_testflight_testers.rb --app #{repo.shellescape} 2>&1`
  n = out[/(\d+)\s+tester/, 1]
  [n ? n.to_i : nil, $?.success?]
end

def add_testers(group)
  in_group = Spaceship::ConnectAPI::BetaTester.all(filter: { betaGroups: group.id }).map { |t| t.email.to_s.downcase }
  added = in_group.size
  TEAM.reject { |t| in_group.include?(t[:email].downcase) }.each do |t|
    Spaceship::ConnectAPI.post_beta_tester_assignment(beta_group_ids: [group.id], attributes: t)
    added += 1
  rescue StandardError => e
    warn "    #{t[:email]}: #{e.message.gsub(/\s+/, ' ')[0, 120]}"
  end
  added
end

# External distribution needs a beta description, feedback email, what-to-test
# and a review contact, or the Beta App Review submission is refused.
def ensure_metadata(app, build, repo)
  locs = Spaceship::ConnectAPI.get_beta_app_localizations(filter: { app: app.id }).to_models
  attrs = { feedbackEmail: CONTACT[:email], description: WHATS_NEW,
            privacyPolicyUrl: policy_url(repo), marketingUrl: "https://www.safecodeg.com" }
  if (loc = locs.find { |l| l.locale == "en-US" })
    Spaceship::ConnectAPI.patch_beta_app_localizations(localization_id: loc.id, attributes: attrs)
  else
    Spaceship::ConnectAPI.post_beta_app_localizations(app_id: app.id, attributes: attrs.merge(locale: "en-US"))
  end

  blocs = Spaceship::ConnectAPI.get_beta_build_localizations(filter: { build: build.id }).to_models
  if (bl = blocs.find { |l| l.locale == "en-US" })
    Spaceship::ConnectAPI.patch_beta_build_localizations(localization_id: bl.id, attributes: { whatsNew: WHATS_NEW })
  else
    Spaceship::ConnectAPI.post_beta_build_localizations(build_id: build.id, attributes: { whatsNew: WHATS_NEW, locale: "en-US" })
  end

  Spaceship::ConnectAPI.patch_beta_app_review_detail(app_id: app.id, attributes: {
    contactFirstName: CONTACT[:firstName], contactLastName: CONTACT[:lastName],
    contactPhone: CONTACT[:phone], contactEmail: CONTACT[:email], demoAccountRequired: false
  })
end

summary = Hash.new { |h, k| h[k] = [] }
state_out = {}
STATE_FILE = File.join(ROOT, ".dist/testflight-state.json")

apps.each do |a|
  repo = a["repo"]
  app = Spaceship::ConnectAPI::App.find(a["bundle_id"]) rescue nil
  (say(repo, "NO APP STORE CONNECT RECORD for #{a['bundle_id']}"); summary[:no_record] << repo; next) if app.nil?

  build = Spaceship::ConnectAPI::Build.all(app_id: app.id, sort: "-uploadedDate", limit: 1).first
  (say(repo, "no build uploaded"); summary[:no_build] << repo; next) if build.nil?

  groups = app.get_beta_groups
  if SYNC
    # --sync is the scheduled job; the workflow runs the internal sync in its own
    # step, so do not repeat it here.
    g = ensure_group(app)
    before = Spaceship::ConnectAPI::BetaTester.all(filter: { betaGroups: g.id }).size
    n = add_testers(g)
    state_out[repo] = { "testers" => n, "added" => n - before }
    say(repo, "#{n}/#{TEAM.size} in #{GROUP}#{n > before ? " (+#{n - before})" : ''}")
    next
  end
  if STATE
    g = groups.find { |x| x.name == GROUP }
    n = g ? Spaceship::ConnectAPI::BetaTester.all(filter: { betaGroups: g.id }).size : 0
    attached = g ? (Spaceship::ConnectAPI.get_builds(filter: { "betaGroups" => g.id }, includes: "app", limit: 10)
                      .to_models.map(&:id).include?(build.id) rescue false) : false
    sub = Spaceship::ConnectAPI.get_beta_app_review_submissions(filter: { build: build.id }).to_models.first rescue nil
    state_out[repo] = { "testers" => n, "attached" => attached,
                        "review" => sub&.beta_review_state || "NONE", "build" => build.version }
    say(repo, "testers=#{n} attached=#{attached} review=#{state_out[repo]['review']}")
    next
  end
  if REPORT
    say(repo, "build #{build.version} | groups: #{groups.map { |g| "#{g.name}#{g.is_internal_group ? '(int)' : '(ext)'}" }.join(', ')}")
    next
  end
  next unless ALL || ONLY

  begin
    # An unanswered export-compliance question keeps a build out of external
    # groups. These apps use only HTTPS and the platform's own crypto, so the
    # exemption applies; ios/Runner/Info.plist carries the same answer for
    # future builds.
    if build.uses_non_exempt_encryption.nil?
      begin
        Spaceship::ConnectAPI.patch_builds(build_id: build.id, attributes: { usesNonExemptEncryption: false })
        build = Spaceship::ConnectAPI::Build.all(app_id: app.id, sort: "-uploadedDate", limit: 1).first
      rescue StandardError => e
        warn "    export compliance: #{e.message.gsub(/\s+/, ' ')[0, 140]}"
      end
    end

    inside, int_ok = sync_internal(repo)
    warn "    internal group sync reported a problem for #{repo}" unless int_ok
    g = ensure_group(app)
    n = add_testers(g)
    ensure_metadata(app, build, repo)
    begin
      build.add_beta_groups(beta_groups: [g])
    rescue StandardError => e
      warn "    attach: #{e.message.gsub(/\s+/, ' ')[0, 140]}"
    end
    state = "build #{build.version} -> #{INTERNAL} (#{inside || '?'} account users, immediate) + #{GROUP} (#{n}/#{TEAM.size})"
    if SUBMIT
      begin
        Spaceship::ConnectAPI.post_beta_app_review_submissions(build_id: build.id)
        state += " | SUBMITTED for Beta App Review"
        summary[:submitted] << repo
      rescue StandardError => e
        msg = e.message.gsub(/\s+/, ' ')
        if msg =~ /already exists|已/i
          state += " | already in Beta App Review"
          summary[:submitted] << repo
        else
          state += " | review submit failed: #{msg[0, 160]}"
          summary[:submit_failed] << repo
        end
      end
    else
      summary[:staged] << repo
    end
    say(repo, state)
  rescue StandardError => e
    say(repo, "FAILED #{e.message.gsub(/\s+/, ' ')[0, 200]}")
    summary[:failed] << repo
  end
end

if STATE || SYNC
  if STATE
    File.write(STATE_FILE, JSON.pretty_generate(state_out))
    puts "\nwrote #{STATE_FILE} (#{state_out.size} apps)"
  else
    added = state_out.values.sum { |v| v["added"].to_i }
    puts "\nsynced #{state_out.size} app(s); #{added} tester assignment(s) added"
  end
elsif !REPORT
  puts "\n--- summary ---"
  summary.each { |k, v| puts "#{k}: #{v.size} #{v.join(', ')}" }
end
