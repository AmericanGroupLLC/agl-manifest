#!/usr/bin/env ruby
# Reply to Apple's Guideline 2.1 rejection in Resolution Center.
#
#   source scripts/testflight/env.sh
#   FASTLANE_USER=srikanth.patchava@outlook.com \
#     bundle exec ruby scripts/testflight/reply_rejections.rb --dry-run
#   FASTLANE_USER=... bundle exec ruby scripts/testflight/reply_rejections.rb yourtube
#   FASTLANE_USER=... bundle exec ruby scripts/testflight/reply_rejections.rb
#
# Every rejection is the same: "submitted by a developer account that has a
# limited App Review history", followed by six numbered requests. A rejected
# version stays locked to its submission — the item cannot be deleted (409) and
# the submission cannot be cancelled (409) — so replying is the only way to
# release it.
#
# Items 2 to 6 are already written into each app's App Review Notes by
# review_notes.rb, from facts this repository holds. This posts the same text
# into the thread, because Apple asks for it in both places.
#
# Item 1, a screen recording made on a physical device, cannot come from a
# script. The reply says so plainly rather than implying it is attached —
# claiming otherwise to a reviewer would be worse than omitting it.
#
# Only threads with canDeveloperAddNote true are touched, and only one reply is
# posted per thread: a second would just push the app down the queue again.

require "json"
require "spaceship"
require_relative "../agl_paths"

DRY  = ARGV.include?("--dry-run")
ONLY = ARGV.reject { |a| a.start_with?("--") }
LOG  = File.join(AglPaths::DIST, "rejection-replies.json")

Spaceship::Tunes.login(ENV.fetch("FASTLANE_USER", "srikanth.patchava@outlook.com"))
Spaceship::ConnectAPI.token = Spaceship::ConnectAPI::Token.create(
  key_id: ENV.fetch("ASC_KEY_ID"),
  issuer_id: ENV.fetch("ASC_ISSUER_ID"),
  filepath: ENV.fetch("ASC_KEY_PATH"),
)
tunes = Spaceship::Tunes.client

def iris(tunes, verb, path, body = nil)
  tunes.request(verb) do |req|
    req.url "https://appstoreconnect.apple.com/iris/#{path}"
    if body
      req.headers["Content-Type"] = "application/json"
      req.body = body.to_json
    end
  end
end

def parse(res)
  res.body.is_a?(Hash) ? res.body : (JSON.parse(res.body.to_s) rescue {})
end

# Worded carefully: it promises a recording without asserting one is already
# in progress, which would be a false statement of present fact to a reviewer.
RECORDING_NOTE = <<~TEXT.strip
  Item 1, the screen recording on a physical device, will be provided in a
  follow-up reply on this thread. Items 2 to 6 are answered in full below, and
  the same text has been added to the App Review Information Notes field for
  future submissions.
TEXT

apps = JSON.parse(File.read(File.join(AglPaths::MANIFEST, "apps.json")))["apps"]
by_bundle = {}
Spaceship::ConnectAPI::App.all.each { |a| by_bundle[a.bundle_id] = a }

log = File.exist?(LOG) ? JSON.parse(File.read(LOG)) : {}
posted = skipped = failed = 0

apps.each do |a|
  repo = a["repo"]
  next if ONLY.any? && !ONLY.include?(repo)
  app = by_bundle[a["bundle_id"]]
  next unless app

  version = begin
    app.get_app_store_versions(filter: { platform: "IOS" }).first
  rescue StandardError
    nil
  end
  next unless version

  detail = begin
    version.fetch_app_store_review_detail
  rescue StandardError
    nil
  end
  notes = detail&.notes.to_s.strip
  if notes.empty?
    puts format("%-18s no review notes to send — run review_notes.rb first", repo)
    skipped += 1
    next
  end

  threads = (parse(iris(tunes, :get,
    "v1/resolutionCenterThreads?filter[appStoreVersion]=#{version.id}"))["data"] || [])
  thread = threads.find { |t| t.dig("attributes", "canDeveloperAddNote") }
  if thread.nil?
    skipped += 1
    next
  end

  if log.dig(repo, "threadId") == thread["id"]
    puts format("%-18s already replied on this thread", repo)
    skipped += 1
    next
  end

  body = "#{RECORDING_NOTE}\n\n#{notes}"
  if DRY
    puts format("%-18s would reply on %s (%d chars)", repo, thread["id"][0, 8], body.length)
    posted += 1
    next
  end

  begin
    # Two steps, which the API only reveals when asked wrongly. Posting
    # straight to resolutionCenterMessages answers
    #   "The attribute 'messageBody' can not be included in a 'CREATE'"
    # and then
    #   "missing a required relationship: createFromDraftMessage"
    # A reply is a draft that is then sent.
    draft = iris(tunes, :post, "v1/resolutionCenterDraftMessages", {
      data: {
        type: "resolutionCenterDraftMessages",
        attributes: { messageBody: body },
        relationships: {
          resolutionCenterThread: {
            data: { type: "resolutionCenterThreads", id: thread["id"] },
          },
        },
      },
    })
    unless draft.status.to_i < 300
      puts format("%-18s draft failed HTTP %s — %s", repo, draft.status,
                  parse(draft).dig("errors", 0, "detail").to_s[0, 120])
      failed += 1
      next
    end
    draft_id = parse(draft).dig("data", "id")

    res = iris(tunes, :post, "v1/resolutionCenterMessages", {
      data: {
        type: "resolutionCenterMessages",
        relationships: {
          createFromDraftMessage: {
            data: { type: "resolutionCenterDraftMessages", id: draft_id },
          },
        },
      },
    })
    unless res.status.to_i < 300
      # Do not leave the draft behind; it shows in the console as an unsent reply.
      iris(tunes, :delete, "v1/resolutionCenterDraftMessages/#{draft_id}") rescue nil
    end
    if res.status.to_i < 300
      puts format("%-18s replied (%d chars)", repo, body.length)
      log[repo] = { "threadId" => thread["id"], "at" => Time.now.utc.iso8601 }
      posted += 1
    else
      detail_msg = parse(res).dig("errors", 0, "detail") || res.status
      puts format("%-18s HTTP %s — %s", repo, res.status, detail_msg.to_s[0, 130])
      failed += 1
    end
  rescue StandardError => e
    puts format("%-18s failed — %s", repo, e.message.gsub(/\s+/, " ")[0, 140])
    failed += 1
  end
  File.write(LOG, JSON.pretty_generate(log) + "\n")
end

require "time"
File.write(LOG, JSON.pretty_generate(log) + "\n")
puts "\nreplied #{posted}, skipped #{skipped}, failed #{failed}"
