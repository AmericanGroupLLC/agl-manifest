# The one gate every App Review submit path goes through (decision log,
# 2026-10-15: #48 two-stage pre-delivery, and the submission hold after 35
# in-place resubmissions of OLD binaries came back 4.3(a) with Apple's Extended
# Review warning).
#
# The rules live in scripts/predelivery.py gate_for_submission(); this only
# asks it. A build may be submitted when:
#   * Stage B is complete for that TestFlight build number: every human check
#     signed against it, D.1 (4.3(a) distinctness review) signed, and a passing
#     Stage A record exists for it;
#   * it was uploaded after the app's last commit touching lib/ and was built
#     from a commit that contains it;
#   * fewer than 3 other apps were submitted in the last 7 days — counted from
#     App Store Connect's own submittedDate (read here, GET only) plus the local
#     log <DIST>/appstore-submissions.jsonl. The local files alone are not
#     enough: the 2026-10-14 resubmissions are in neither of them.
#
# Fails closed: if App Store Connect cannot be read, or python or the gate
# errors, the answer is "refused".
require "json"
require "net/http"
require "open3"
require "tempfile"
require "time"
require "uri"
require_relative "../agl_paths"

module SubmissionGate
  PREDELIVERY = File.join(AglPaths::MANIFEST, "scripts", "predelivery.py")
  WINDOW_DAYS = 7

  def self.token
    require "spaceship"
    @token ||= Spaceship::ConnectAPI::Token.create(key_id: ENV.fetch("ASC_KEY_ID"), issuer_id: ENV.fetch("ASC_ISSUER_ID"),
                                                   filepath: ENV.fetch("ASC_KEY_PATH"))
  end

  def self.get(path)
    u = URI(path.start_with?("http") ? path : "https://api.appstoreconnect.apple.com/#{path}")
    r = Net::HTTP::Get.new(u)
    r["Authorization"] = "Bearer #{token.text}"
    res = Net::HTTP.start(u.host, 443, use_ssl: true, read_timeout: 120) { |h| h.request(r) }
    raise "GET #{u.path} -> HTTP #{res.code}" unless res.code.to_i == 200
    JSON.parse(res.body)
  end

  # Apple's record: [{repo, at, state}] for every review submission of every
  # portfolio app with a submittedDate in the last WINDOW_DAYS. Read once per run.
  def self.recent_submissions
    @recent ||= begin
      by_bundle = JSON.parse(File.read(File.join(AglPaths::MANIFEST, "apps.json")))["apps"]
                      .to_h { |a| [a["bundle_id"], a["repo"]] }
      since = Time.now - WINDOW_DAYS * 86_400
      apps, url = [], "v1/apps?limit=200&fields[apps]=bundleId"
      while url
        page = get(url)
        apps.concat(page["data"] || [])
        url = page.dig("links", "next")
      end
      apps.flat_map do |app|
        repo = by_bundle[app.dig("attributes", "bundleId")]
        next [] unless repo
        subs = get("v1/apps/#{app['id']}/reviewSubmissions?limit=50&fields[reviewSubmissions]=submittedDate,state")["data"] || []
        subs.filter_map do |s|
          d = s.dig("attributes", "submittedDate")
          { "repo" => repo, "at" => d, "state" => s.dig("attributes", "state"), "source" => "App Store Connect" } if d && Time.parse(d) >= since
        end
      end
    end
  end

  # [ok, message]
  def self.check(repo, build_number, uploaded_at = nil)
    return [false, "#{repo}: no TestFlight build number to check"] if build_number.to_s.strip.empty?
    asc = begin
      recent_submissions
    rescue StandardError => e
      return [false, "REFUSED #{repo}: cannot read recent submissions from App Store Connect " \
                     "(#{e.class}: #{e.message}) — the 3-apps-per-week rule cannot be proven"]
    end
    file = Tempfile.new(["asc-submissions", ".json"])
    file.write(JSON.generate(asc))
    file.flush
    cmd = ["python3", PREDELIVERY, "--gate-submission", repo, "--build", build_number.to_s, "--asc-submissions", file.path]
    cmd += ["--uploaded-at", uploaded_at.to_s] unless uploaded_at.to_s.strip.empty?
    out, status = Open3.capture2e(*cmd)
    line = out.strip.lines.last.to_s.strip
    return [true, line] if status.success? && line.start_with?("PASS")
    [false, line.empty? ? "REFUSED #{repo}: gate produced no answer (exit #{status.exitstatus})" : line]
  rescue StandardError => e
    [false, "REFUSED #{repo}: gate could not run: #{e.class}: #{e.message}"]
  ensure
    file&.close!
  end

  # Append a submission to <DIST>/appstore-submissions.jsonl. Call it only after
  # Apple accepted the submit.
  def self.record!(repo, build_number, status, script)
    out, st = Open3.capture2e("python3", PREDELIVERY, "--record-submission", repo, "--build", build_number.to_s,
                              "--status", status, "--script", script)
    warn "SUBMISSION LOG NOT WRITTEN for #{repo} build #{build_number}: #{out.strip}" unless st.success?
  end
end
