"""Tests for the two pre-delivery gates (decision #48) and the 2026-10-15 submission hold.

    python3 -m unittest discover -s scripts/tests -v      # stdlib; pytest collects these too

Every test runs against a throwaway manifest, app repo and DIST in a temp
directory: nothing here reads or writes the real docs/, store/ or ~/agl/.dist.
"""

from __future__ import annotations

import datetime
import io
import json
import os
import pathlib
import plistlib
import subprocess
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import predelivery as P  # noqa: E402

REPO = "TestApp"
BUILD = "202610151200"
UTC = datetime.timezone.utc


def ts(s: str) -> datetime.datetime:
    return datetime.datetime.fromisoformat(s).replace(tzinfo=UTC)


class Sandbox(unittest.TestCase):
    """A temp manifest + app repo + DIST, with predelivery's paths pointed at it."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = pathlib.Path(self.tmp.name)
        self.m, self.root, self.dist = t / "manifest", t / "apps", t / "dist"
        for d in (self.m / "docs", self.root, self.dist):
            d.mkdir(parents=True)
        (self.m / "apps.json").write_text(json.dumps({"apps": [
            {"repo": REPO, "dir": "mobile", "bundle_id": "com.example.testapp"},
            {"repo": "Other", "dir": ".", "bundle_id": "com.example.other"}]}))
        (self.m / "docs/asc-build-state.json").write_text("[]")
        sign = self.m / "store/predelivery"
        patches = {
            "M": self.m, "ROOT": self.root, "DIST": self.dist, "OUT_DIR": self.m / "docs/predelivery",
            "SIGN_DIR": sign, "STAGE_A_DIR": sign / "stage-a",
            "SUBMISSION_LOG": self.dist / "appstore-submissions.jsonl",
            "LEGACY_SUBMISSION_FILES": (self.dist / "appstore-resubmit-in-place.json",
                                        self.dist / "appstore-submit-results.json"),
        }
        for k, v in patches.items():
            p = mock.patch.object(P, k, v)
            p.start()
            self.addCleanup(p.stop)
        # The app repo, with lib/ last changed at 2026-10-14 12:00 UTC.
        self.repo_dir = self.root / REPO
        (self.repo_dir / "mobile/lib").mkdir(parents=True)
        self.git("init", "-q", "-b", "main")
        self.lib_commit = self.commit("mobile/lib/main.dart", "v1", "2026-10-14T12:00:00+00:00")
        # A later commit outside lib/ must not move the line.
        self.commit("README.md", "docs", "2026-10-15T09:00:00+00:00")

    def tearDown(self):
        self.tmp.cleanup()

    # ---------------------------------------------------------------- helpers
    def git(self, *args, env=None):
        e = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@x", "GIT_COMMITTER_NAME": "t",
             "GIT_COMMITTER_EMAIL": "t@x", **(env or {})}
        return subprocess.run(["git", "-C", str(self.repo_dir), *args], check=True, capture_output=True,
                              text=True, env=e).stdout.strip()

    def commit(self, rel, text, when):
        f = self.repo_dir / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text)
        self.git("add", rel)
        self.git("commit", "-q", "-m", f"change {rel}", env={"GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when})
        return self.git("rev-parse", "HEAD")

    def ipa(self, build=BUILD, salt=b"") -> pathlib.Path:
        p = self.dist / f"{REPO}.ipa"
        with zipfile.ZipFile(p, "w") as z:
            z.writestr("Payload/Runner.app/Info.plist", plistlib.dumps({"CFBundleVersion": build}))
            z.writestr("Payload/Runner.app/Runner", b"binary" + salt)
        return p

    def rows(self, auto=P.PASS, human=P.HUMAN, overrides=None):
        overrides = overrides or {}
        out = []
        for cid, kind, text in P.CHECKS:
            st = auto if kind == "auto" else human if kind == "human" else P.HUMAN
            st = overrides.get(cid, st)
            out.append({"id": cid, "section": cid.split(".")[0], "kind": kind, "text": text,
                        "state": st, "evidence": f"test {st}"})
        return out

    def result(self, ipa, rows=None, commit=None):
        rows = rows or self.rows()
        sa = P.stage_a_state(rows)
        return {"record": {"app": REPO, "build": P.ipa_build(ipa), "ipa_sha256": P.sha256(ipa),
                           "git_commit": commit or self.git("rev-parse", "--short", "HEAD"), "version": "1.0.0"},
                "rows": rows, "gates": [], "stage_a": sa, "deliverable": sa["passed"], "done": 0, "total": len(rows)}

    def pass_stage_a(self, rows=None, commit=None):
        ipa = self.ipa()
        res = self.result(ipa, rows, commit)
        self.assertIsNotNone(P.write_stage_a_record(res))
        return ipa

    def sign_all(self, build=BUILD, skip=()):
        for cid in P.STAGE_B_IDS + [r[0] for r in P.SUBMISSION_REVIEWS]:
            if cid not in skip:
                with redirect_stdout(io.StringIO()):
                    P.sign(REPO, cid, build, "tester", "iPhone 15, iOS 27.0", "did it")

    def gate(self, uploaded="2026-10-15T10:00:00+00:00", asc=None, now="2026-10-16T12:00:00"):
        with mock.patch.object(P, "last_lib_commit", lambda a, fetch=True: P.__dict__["_real_llc"](a, fetch=False)):
            return P.gate_for_submission(REPO, BUILD, uploaded, now=ts(now), asc_submissions=asc)

    def log(self, *entries):
        P.SUBMISSION_LOG.write_text("".join(json.dumps(e) + "\n" for e in entries))


P._real_llc = P.last_lib_commit  # the gate tests call it with fetch=False (no network)


# ==================================================================== Stage A
class StageATest(Sandbox):
    def test_stage_a_counts_exactly_the_20_automated_checks_of_sections_1_to_5(self):
        self.assertEqual(len(P.STAGE_A_IDS), 20)
        self.assertTrue(all(i.split(".")[0] in "12345" for i in P.STAGE_A_IDS))
        self.assertEqual(len(P.STAGE_B_IDS), 18)

    def test_human_checks_do_not_block_stage_a(self):
        sa = P.stage_a_state(self.rows(auto=P.PASS, human=P.HUMAN))
        self.assertTrue(sa["passed"])
        self.assertEqual(sa["open"], [])

    def test_na_auto_check_still_passes(self):
        self.assertTrue(P.stage_a_state(self.rows(overrides={"2.2": P.NA}))["passed"])

    def test_one_failed_or_open_auto_check_fails_stage_a(self):
        for st in (P.FAIL, P.HUMAN):
            sa = P.stage_a_state(self.rows(overrides={"2.7": st}))
            self.assertFalse(sa["passed"])
            self.assertEqual(sa["open"], ["2.7"])

    def test_failed_precondition_is_reported_as_blocking_stage_b_not_a(self):
        sa = P.stage_a_state(self.rows(overrides={"1.4": P.FAIL}))
        self.assertTrue(sa["passed"])
        self.assertEqual(sa["stage_b_blocked_by"], ["1.4"])

    def test_no_record_is_written_for_a_failed_stage_a(self):
        ipa = self.ipa()
        self.assertIsNone(P.write_stage_a_record(self.result(ipa, self.rows(overrides={"3.3": P.FAIL}))))
        self.assertFalse(P.STAGE_A_DIR.exists())


class UploadGateTest(Sandbox):
    def test_refuses_without_any_checklist(self):
        self.assertIn("no pre-delivery checklist", P.gate_for_upload(REPO, self.ipa()))

    def test_passes_with_a_stage_a_record_for_this_exact_ipa(self):
        ipa = self.pass_stage_a()
        self.assertIsNone(P.gate_for_upload(REPO, ipa))

    def test_refuses_a_rebuilt_ipa_with_the_same_build_number(self):
        self.pass_stage_a()
        rebuilt = self.ipa(salt=b"different bytes")
        P.OUT_DIR.mkdir(parents=True)
        (P.OUT_DIR / f"{REPO}.json").write_text("{\"record\": {\"ipa_sha256\": \"0\"}, \"rows\": []}")
        self.assertIn("different IPA", P.gate_for_upload(REPO, rebuilt))

    def test_refuses_when_the_latest_run_on_this_ipa_failed_stage_a(self):
        ipa = self.ipa()
        res = self.result(ipa, self.rows(overrides={"2.3": P.FAIL, "3.6": P.FAIL}))
        (P.DIST / "predelivery").mkdir(parents=True)
        (P.DIST / "predelivery" / f"{REPO}.json").write_text(json.dumps(res))
        why = P.gate_for_upload(REPO, ipa)
        self.assertIn("Stage A not passed", why)
        self.assertIn("2.3, 3.6", why)

    def test_human_checks_unsigned_do_not_block_upload(self):
        ipa = self.pass_stage_a(rows=self.rows(human=P.HUMAN))
        self.assertIsNone(P.gate_for_upload(REPO, ipa))


# ==================================================================== Stage B + hold
class SignTest(Sandbox):
    def test_signature_is_bound_to_the_testflight_build_number(self):
        with redirect_stdout(io.StringIO()):
            P.sign(REPO, "5.1", BUILD, "tester", "iPhone 15", "installed from TestFlight")
        self.assertIn("5.1", P.signs_for_build(REPO, BUILD))
        self.assertEqual(P.signs_for_build(REPO, "202610151300"), {})

    def test_sign_requires_a_build_number(self):
        with self.assertRaises(SystemExit):
            P.sign(REPO, "5.1", None, "tester", "iPhone 15", "x")

    def test_auto_checks_cannot_be_signed(self):
        with self.assertRaises(SystemExit):
            P.sign(REPO, "3.3", BUILD, "tester", "iPhone 15", "x")

    def test_the_distinctness_review_can_be_signed(self):
        with redirect_stdout(io.StringIO()):
            P.sign(REPO, "D.1", BUILD, "qa-reviewer", "n/a", "compared with the portfolio")
        self.assertIn("D.1", P.signs_for_build(REPO, BUILD))


class SubmissionGateTest(Sandbox):
    def ready(self, **kw):
        self.pass_stage_a(**kw)
        self.sign_all()
        self.log()  # an empty, existing submission log

    def test_passes_when_stage_b_is_complete_and_the_hold_allows_it(self):
        self.ready()
        self.assertIsNone(self.gate())

    def test_refuses_without_a_stage_a_record_for_the_build(self):
        self.sign_all()
        self.log()
        self.assertIn("no passing Stage A record for build", self.gate())

    def test_refuses_while_human_checks_are_unsigned(self):
        self.pass_stage_a()
        self.sign_all(skip=("5.1", "5.4", "D.1"))
        self.log()
        why = self.gate()
        self.assertIn("not signed for build", why)
        for cid in ("5.1", "5.4", "D.1"):
            self.assertIn(cid, why)

    def test_checks_a_precondition_made_na_need_no_signature(self):
        self.pass_stage_a(rows=self.rows(overrides={"1.4": P.NA, "4.3": P.NA}))
        self.sign_all(skip=("1.4", "4.3"))
        self.log()
        self.assertIsNone(self.gate())

    def test_refuses_a_build_whose_precondition_failed(self):
        self.pass_stage_a(rows=self.rows(overrides={"1.4": P.FAIL}))
        self.sign_all()
        self.log()
        self.assertIn("fails measured preconditions", self.gate())

    def test_signatures_for_another_build_do_not_count(self):
        self.pass_stage_a()
        self.sign_all(build="202610140900")
        self.log()
        self.assertIn("not signed for build", self.gate())

    def test_refuses_a_build_uploaded_before_the_last_lib_commit(self):
        self.ready()
        why = self.gate(uploaded="2026-10-13T08:00:00+00:00")
        self.assertIn("before the last lib/ commit", why)
        self.assertIn(self.lib_commit[:9], why)

    def test_a_commit_outside_lib_does_not_count(self):
        self.ready()
        # README changed 2026-10-15 09:00, lib/ on 10-14: an upload in between passes.
        self.assertIsNone(self.gate(uploaded="2026-10-14T18:00:00+00:00"))

    def test_upload_date_falls_back_to_asc_build_state(self):
        self.ready()
        (P.M / "docs/asc-build-state.json").write_text(json.dumps(
            [{"repo": REPO, "version": BUILD, "uploaded_at": "2026-10-10T00:00:00-07:00"}]))
        self.assertIn("before the last lib/ commit", self.gate(uploaded=None))

    def test_refuses_when_the_upload_date_is_unknown(self):
        self.ready()
        self.assertIn("upload date of build", self.gate(uploaded=None))

    def test_refuses_when_the_checked_commit_lacks_the_last_lib_commit(self):
        old = self.git("rev-parse", "--short", "HEAD~1")  # the first lib/ commit (HEAD is the README one)
        self.assertEqual(self.git("rev-parse", "HEAD~1"), self.lib_commit)
        newer = self.commit("mobile/lib/main.dart", "v2", "2026-10-15T11:00:00+00:00")
        self.ready(commit=old)  # Stage A ran on the older commit
        why = self.gate(uploaded="2026-10-15T12:00:00+00:00")
        self.assertIn("does not contain the last lib/ commit", why)
        self.assertIn(newer[:9], why)

    def test_refuses_when_the_app_is_not_a_git_checkout(self):
        self.ready()
        subprocess.run(["rm", "-rf", str(self.repo_dir / ".git")], check=True)
        self.assertIn("not a git checkout", self.gate())

    def test_refuses_the_fourth_app_in_seven_days(self):
        self.ready()
        self.log(*[{"at": "2026-10-14T18:57:00+00:00", "repo": r, "status": "resubmitted"} for r in ("A", "B", "C")])
        self.assertIn("3 other app(s) were submitted in the last 7 days", self.gate())

    def test_allows_a_third_app(self):
        self.ready()
        self.log(*[{"at": "2026-10-14T18:57:00+00:00", "repo": r, "status": "submitted"} for r in ("A", "B")])
        self.assertIsNone(self.gate())

    def test_the_same_app_and_refusals_and_old_submissions_do_not_count(self):
        self.ready()
        self.log({"at": "2026-10-15T00:00:00+00:00", "repo": REPO, "status": "submitted"},
                 {"at": "2026-10-15T00:00:00+00:00", "repo": "A", "status": "refused-by-gate"},
                 {"at": "2026-10-01T00:00:00+00:00", "repo": "B", "status": "submitted"},
                 {"at": "2026-10-15T00:00:00+00:00", "repo": "C", "status": "submitted"},
                 {"at": "2026-10-15T00:00:00+00:00", "repo": "C", "status": "resubmitted"})
        self.assertIsNone(self.gate())

    def test_app_store_connect_submissions_count(self):
        self.ready()
        asc = [{"repo": r, "at": "2026-10-14T18:57:04.556Z", "state": "UNRESOLVED_ISSUES"} for r in ("A", "B", "C", "D")]
        self.assertIn("4 other app(s)", self.gate(asc=asc))

    def test_refuses_when_there_is_no_submission_history_at_all(self):
        self.pass_stage_a()
        self.sign_all()
        self.assertIn("cannot prove the 3-apps-per-week limit", self.gate())

    def test_app_store_connect_alone_is_enough_history(self):
        self.pass_stage_a()
        self.sign_all()
        self.assertIsNone(self.gate(asc=[]))

    def test_legacy_results_are_backfilled_into_the_log_and_counted(self):
        self.pass_stage_a()
        self.sign_all()
        legacy = P.LEGACY_SUBMISSION_FILES[0]
        legacy.write_text(json.dumps({r: {"status": "resubmitted"} for r in ("A", "B", "C")}))
        stamp = ts("2026-10-14T19:00:00").timestamp()
        os.utime(legacy, (stamp, stamp))
        self.assertIn("3 other app(s)", self.gate())
        self.assertTrue(P.SUBMISSION_LOG.exists())
        self.assertEqual(len(P.SUBMISSION_LOG.read_text().splitlines()), 3)

    def test_record_submission_appends(self):
        self.log()
        P.record_submission("A", BUILD, "submitted", "test")
        P.record_submission("B", BUILD, "resubmitted", "test")
        lines = [json.loads(x) for x in P.SUBMISSION_LOG.read_text().splitlines()]
        self.assertEqual([x["repo"] for x in lines], ["A", "B"])

    def test_cli_exit_status(self):
        self.ready()
        argv = ["predelivery.py", "--gate-submission", REPO, "--build", BUILD,
                "--uploaded-at", "2026-10-15T10:00:00+00:00"]
        with mock.patch.object(sys, "argv", argv), \
                mock.patch.object(P, "last_lib_commit", lambda a, fetch=True: P._real_llc(a, fetch=False)), \
                redirect_stdout(io.StringIO()) as out:
            self.assertEqual(P.main(), 0)
        self.assertIn("PASS", out.getvalue())
        argv[-1] = "2026-10-01T10:00:00+00:00"
        with mock.patch.object(sys, "argv", argv), \
                mock.patch.object(P, "last_lib_commit", lambda a, fetch=True: P._real_llc(a, fetch=False)), \
                redirect_stdout(io.StringIO()) as out:
            self.assertEqual(P.main(), 3)
        self.assertIn("REFUSED", out.getvalue())


if __name__ == "__main__":
    unittest.main()
