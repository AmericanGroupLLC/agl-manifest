#!/usr/bin/env ruby
# Add ios/Runner/PrivacyInfo.xcprivacy to the Runner target's resources.
#
# Writing the file is not enough: a resource that is not a member of the
# target's "Copy Bundle Resources" phase is never copied into the .app, so
# Apple never sees it and the submission is rejected exactly as if the file did
# not exist.
#
#   ruby scripts/add_privacy_manifest_to_xcode.rb ~/agl/AppName[/subdir]
#
# Idempotent: a project that already references the file is left alone.

require "xcodeproj"

app_dir = ARGV[0] or abort("usage: #{$0} <flutter app directory>")
project_path = File.join(app_dir, "ios", "Runner.xcodeproj")
manifest_path = File.join(app_dir, "ios", "Runner", "PrivacyInfo.xcprivacy")

abort("no #{project_path}") unless Dir.exist?(project_path)
abort("no #{manifest_path}") unless File.exist?(manifest_path)

project = Xcodeproj::Project.open(project_path)
target = project.targets.find { |t| t.name == "Runner" }
abort("no Runner target in #{project_path}") unless target

already = target.resources_build_phase.files.any? do |f|
  f.file_ref&.path&.end_with?("PrivacyInfo.xcprivacy")
end
if already
  puts "#{app_dir}: already a member of Copy Bundle Resources"
  exit 0
end

group = project.main_group.find_subpath("Runner", true)
ref = group.files.find { |f| f.path&.end_with?("PrivacyInfo.xcprivacy") }
ref ||= group.new_reference("PrivacyInfo.xcprivacy")

target.resources_build_phase.add_file_reference(ref, true)
project.save
puts "#{app_dir}: added PrivacyInfo.xcprivacy to Copy Bundle Resources"
