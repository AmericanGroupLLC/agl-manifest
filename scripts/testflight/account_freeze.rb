# Refuse to submit anything for App Review while the account holds a 5.6 finding.
#
# On 2026-10-08 sixteen apps were rejected under Guideline 5.6 (Developer Code
# of Conduct, "features intentionally hidden during review") within the same
# minute, each on its first review, three days after 26 were rejected under
# 4.3. That is a judgment about the account's submission pattern; the step
# after it can be termination of the developer account. store_watch.py stops
# submitting while docs/store-holds.json carries a 5.6 hold. This makes the
# scripts that submit directly stop too, so a manual run or another session
# cannot add to the pattern by accident.
#
#   --override-account-freeze   only after a person has read the 5.6 findings,
#                               replied in Resolution Center, and decided.
require "json"
require_relative "../agl_paths"

module AccountFreeze
  def self.enforce!(argv)
    return if argv.include?("--override-account-freeze")
    path = File.join(AglPaths::MANIFEST, "docs/store-holds.json")
    holds = File.exist?(path) ? JSON.parse(File.read(path)) : {}
    frozen = holds.select { |_, h| h["guideline"] == "5.6" }.keys.sort
    return if frozen.empty?
    warn "ACCOUNT FREEZE: #{frozen.size} app(s) hold a Guideline 5.6 finding " \
         "(#{frozen.join(', ')}). Nothing is submitted for review until a person " \
         "has answered them; see docs/REJECTION_ANALYSIS.md. " \
         "Override: --override-account-freeze"
    exit 4
  end
end
