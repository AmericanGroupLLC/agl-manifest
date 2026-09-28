#!/usr/bin/env ruby
# Put GoogleService-Info.plist into the Xcode project, so iOS actually gets it.
#
#   bundle exec ruby scripts/fix_ios_firebase_plist.rb --dry-run
#   bundle exec ruby scripts/fix_ios_firebase_plist.rb
#   bundle exec ruby scripts/fix_ios_firebase_plist.rb CalcMaster
#
# Shipping the file in the repo is not the same as shipping it in the app.
# Xcode only copies what the project references, and on 2026-09-23 the file
# was present on disk for all 43 apps but referenced by the project in only 7.
# The other 36 launched with:
#
#   [FirebaseCore][I-COR000012] Could not locate configuration file:
#   'GoogleService-Info.plist'.
#
# which means Firebase never initialised: no Crashlytics, no Analytics, no
# Performance, no Remote Config. Nothing crashed, because agl_observability
# guards every path - so this failed silently for as long as it existed, and
# the audit that only checked `File.exist?` reported it as healthy.
#
# Idempotent: an app that already references the file is reported and skipped.
require "json"
require "xcodeproj"

require_relative "agl_paths"
ROOT = AglPaths::ROOT
M = "#{ROOT}/agl-manifest"
DRY = ARGV.include?("--dry-run")
ONLY = ARGV.reject { |a| a.start_with?("--") }

apps = JSON.parse(File.read("#{M}/apps.json"))["apps"]
apps = apps.select { |a| ONLY.include?(a["repo"]) } unless ONLY.empty?

results = {}
fixed = 0
already = 0

apps.each do |a|
  repo = a["repo"]
  proj_path = Dir.glob("#{ROOT}/#{repo}/**/ios/Runner.xcodeproj")
                 .reject { |p| p.include?("/build/") }.first
  plist = Dir.glob("#{ROOT}/#{repo}/**/ios/Runner/GoogleService-Info.plist")
             .reject { |p| p.include?("/build/") }.first

  if proj_path.nil? || plist.nil?
    puts "#{repo.ljust(18)} SKIP (no #{proj_path.nil? ? 'Runner.xcodeproj' : 'plist'})"
    results[repo] = { "state" => "skip-missing" }
    next
  end

  begin
    project = Xcodeproj::Project.open(proj_path)
    target = project.targets.find { |t| t.name == "Runner" } || project.targets.first
    raise "no target" if target.nil?

    in_resources = target.resources_build_phase.files.any? do |bf|
      bf.file_ref&.path.to_s.end_with?("GoogleService-Info.plist")
    end

    if in_resources
      puts "#{repo.ljust(18)} already referenced"
      results[repo] = { "state" => "already-referenced" }
      already += 1
      next
    end

    if DRY
      puts "#{repo.ljust(18)} WOULD ADD to #{File.basename(proj_path)} / #{target.name}"
      results[repo] = { "state" => "would-add" }
      next
    end

    # Reuse a stray file reference if one exists but was never added to the
    # phase; otherwise create it inside the Runner group so the path stays
    # relative, exactly as the seven already-correct apps have it.
    group = project.main_group.find_subpath("Runner", true)
    ref = group.files.find { |f| f.path.to_s.end_with?("GoogleService-Info.plist") }
    ref ||= group.new_reference(plist)
    ref.path = "GoogleService-Info.plist"
    ref.source_tree = "<group>"

    target.resources_build_phase.add_file_reference(ref, true)
    project.save

    # Re-open from disk rather than trusting the in-memory object.
    verify = Xcodeproj::Project.open(proj_path)
    vt = verify.targets.find { |t| t.name == target.name }
    stuck = vt.resources_build_phase.files.any? do |bf|
      bf.file_ref&.path.to_s.end_with?("GoogleService-Info.plist")
    end

    if stuck
      puts "#{repo.ljust(18)} ADDED"
      results[repo] = { "state" => "added" }
      fixed += 1
    else
      puts "#{repo.ljust(18)} WROTE BUT DID NOT STICK"
      results[repo] = { "state" => "verify-failed" }
    end
  rescue => e
    msg = e.message.lines.first.to_s.strip
    puts "#{repo.ljust(18)} FAILED #{msg[0, 120]}"
    results[repo] = { "state" => "failed", "error" => msg[0, 300] }
  end
end

out = "#{ROOT}/.dist/ios-firebase-plist.json"
File.write(out, JSON.pretty_generate(results))
puts
puts "#{fixed} added, #{already} already referenced -> #{out}"
