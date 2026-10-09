#!/usr/bin/env ruby
# Release the apps held by a rejected review submission, then submit them again.
#
#   source scripts/testflight/env.sh
#   bundle exec ruby scripts/testflight/resubmit_rejected.rb --dry-run
#   bundle exec ruby scripts/testflight/resubmit_rejected.rb
#   bundle exec ruby scripts/testflight/resubmit_rejected.rb AeroSwift
#
# 23 apps sat on a submission in UNRESOLVED_ISSUES. That submission holds the
# version, so every attempt to submit answered
#
#   Version is not ready to be submitted yet, please try again later
#
# with no indication of why, and MA-028 concluded the only way out was a
# Resolution Center reply — which needs an Apple ID web session, because an
# API key 404s on v1/resolutionCenterThreads.
#
# That is no longer true, and clear_stale_submissions.rb still says so:
#
#   PATCH {"canceled": true}  409  Resource is not in cancellable state
#
# Measured again on 2026-10-01 against a real UNRESOLVED_ISSUES submission,
# the same call answers **200**, the state moves to CANCELING, and once it
# settles the app submits normally. Verified end to end on AeroSwift before
# this was written: cancel 200 -> CANCELING -> "SUBMITTED FOR APP STORE
# REVIEW (build 202609260214)".
#
# What this costs, and it is worth being clear about it: canceling discards
# Apple's rejection thread for that submission. The reply is gone and the
# review starts over. That is an acceptable trade only because the metadata
# gaps behind the original rejections are now closed — asc_readiness.rb
# reports 43/43 — so a fresh review is a real attempt rather than a loop. If
# Apple rejects again, the reason will need reading, and that still needs a
# session.

require "json"
require "net/http"
require "spaceship"
require "uri"
require_relative "../agl_paths"

DRY  = ARGV.include?("--dry-run")
ONLY = ARGV.reject { |a| a.start_with?("--") }
require_relative "account_freeze"
AccountFreeze.enforce!(ARGV) unless DRY
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
  klass = { get: Net::HTTP::Get, patch: Net::HTTP::Patch }[verb]
  r = klass.new(uri)
  r["Authorization"] = "Bearer #{TOKEN.text}"
  r["Content-Type"] = "application/json"
  r.body = body.to_json if body
  res = http.request(r)
  [res.code.to_i, (JSON.parse(res.body) rescue {})]
end

apps = JSON.parse(File.read(File.join(AglPaths::MANIFEST, "apps.json")))["apps"]
apps = apps.select { |a| ONLY.include?(a["repo"]) } if ONLY.any?

by_bundle = {}
Spaceship::ConnectAPI::App.all.each { |a| by_bundle[a.bundle_id] = a }

held = []
apps.each do |a|
  app = by_bundle[a["bundle_id"]]
  next unless app
  _, rs = req(:get, "v1/apps/#{app.id}/reviewSubmissions?limit=10")
  sub = (rs["data"] || []).find { |x| x.dig("attributes", "state") == "UNRESOLVED_ISSUES" }
  held << [a["repo"], app.id, sub["id"]] if sub
end

puts "held by a rejected submission: #{held.size}"
if held.empty?
  puts "nothing to do"
  exit 0
end

if DRY
  held.each { |repo, _, sid| puts format("  %-18s would cancel %s", repo, sid) }
  exit 0
end

canceled = failed = 0
held.each do |repo, _, sid|
  code, out = req(:patch, "v1/reviewSubmissions/#{sid}",
                  { data: { type: "reviewSubmissions", id: sid,
                            attributes: { canceled: true } } })
  if code < 300
    canceled += 1
    puts format("  %-18s canceled", repo)
  else
    failed += 1
    puts format("  %-18s cancel %d %s", repo, code,
                out.dig("errors", 0, "detail").to_s.gsub(/\s+/, " ")[0, 100])
  end
end
puts "canceled #{canceled}, failed #{failed}"

# CANCELING is not an end state and the version stays held while it lasts, so
# submitting immediately just reproduces the original error. Poll rather than
# sleep a fixed amount: it took well under a minute per app when measured, but
# nothing guarantees that.
print "waiting for cancellations to settle"
deadline = Time.now + 600
loop do
  still = held.count do |_, app_id, _|
    _, rs = req(:get, "v1/apps/#{app_id}/reviewSubmissions?limit=10")
    (rs["data"] || []).any? { |x| %w[UNRESOLVED_ISSUES CANCELING].include?(x.dig("attributes", "state")) }
  end
  break if still.zero? || Time.now > deadline
  print "."
  $stdout.flush
  sleep 20
end
puts

puts "\nnow run: bundle exec ruby scripts/testflight/submit_production.rb"
