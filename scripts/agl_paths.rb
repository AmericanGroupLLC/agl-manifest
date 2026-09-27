# Where things are, resolved rather than assumed. The Ruby twin of
# scripts/agl_paths.py — see that file for why this exists.
#
#   require_relative "agl_paths"   # or "../agl_paths" from scripts/testflight
#   AglPaths::MANIFEST, AglPaths::ROOT, AglPaths::DIST
module AglPaths
  # .../scripts/agl_paths.rb -> scripts -> the manifest
  MANIFEST = File.expand_path("..", __dir__)

  def self.checkout?(dir)
    return false unless File.directory?(dir)
    names = Dir.children(dir).select { |c| File.directory?(File.join(dir, c)) }
    apps = JSON.parse(File.read(File.join(MANIFEST, "apps.json")))["apps"]
    # Two, not one — see the note in agl_paths.py. CI sets AGL_ROOT rather
    # than depending on this.
    apps.count { |a| names.include?(a["repo"]) } >= 2
  rescue StandardError
    false
  end

  # Locally the apps sit beside the manifest; in CI checkout.py clones them
  # into <manifest>/work. A stray empty work/ is not a CI layout, so the test
  # is whether it actually holds app repositories.
  ROOT = ENV["AGL_ROOT"] || (checkout?(File.join(MANIFEST, "work")) ?
                             File.join(MANIFEST, "work") :
                             File.expand_path("..", MANIFEST))

  DIST = ENV["AGL_DIST"] || File.join(ROOT, ".dist")
end
