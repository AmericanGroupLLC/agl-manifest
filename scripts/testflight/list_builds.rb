require "spaceship"
Spaceship::ConnectAPI.token = Spaceship::ConnectAPI::Token.create(key_id: ENV["ASC_KEY_ID"], issuer_id: ENV["ASC_ISSUER_ID"], filepath: ENV["ASC_KEY_PATH"])
ARGV.each do |bid|
  app = Spaceship::ConnectAPI::App.find(bid)
  (puts "#{bid}: NO RECORD"; next) unless app
  builds = Spaceship::ConnectAPI::Build.all(app_id: app.id, sort: "-uploadedDate", limit: 3)
  puts "#{bid} -> '#{app.name}' (id #{app.id})"
  builds.each { |b| puts "   build #{b.version} v#{b.app_version rescue '?'} #{b.processing_state} uploaded #{b.uploaded_date}" }
  puts "   (no builds)" if builds.empty?
end
