#!/usr/bin/env ruby
# Print the repo name of every app whose bundle id has an App Store Connect record.
require "json"; require "spaceship"
Spaceship::ConnectAPI.token = Spaceship::ConnectAPI::Token.create(key_id: ENV.fetch("ASC_KEY_ID"), issuer_id: ENV.fetch("ASC_ISSUER_ID"), filepath: ENV.fetch("ASC_KEY_PATH"))
apps = JSON.parse(File.read("/Users/spatchava/agl/agl-manifest/apps.json"))["apps"]
ids = Spaceship::ConnectAPI::App.all.map(&:bundle_id)
apps.each { |a| puts a["repo"] if ids.include?(a["bundle_id"]) }
