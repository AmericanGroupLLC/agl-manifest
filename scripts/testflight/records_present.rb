#!/usr/bin/env ruby
# Print the repo name of every app whose bundle id has an App Store Connect record.
require "json"; require "spaceship"
require_relative "../agl_paths"
Spaceship::ConnectAPI.token = Spaceship::ConnectAPI::Token.create(key_id: ENV.fetch("ASC_KEY_ID"), issuer_id: ENV.fetch("ASC_ISSUER_ID"), filepath: ENV.fetch("ASC_KEY_PATH"))
apps = JSON.parse(File.read(File.join(AglPaths::MANIFEST, "apps.json")))["apps"]
ids = Spaceship::ConnectAPI::App.all.map(&:bundle_id)
apps.each { |a| puts a["repo"] if ids.include?(a["bundle_id"]) }
