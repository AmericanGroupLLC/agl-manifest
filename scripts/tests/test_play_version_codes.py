"""play_version_codes.read_codes: a failed Play read is ERROR, never 'highest=0' (ship run 38812509219).

    python3 -m unittest discover -s scripts/tests -v
"""

from __future__ import annotations

import pathlib
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import play_version_codes as V  # noqa: E402


def fake(responses):
    """call() stand-in: answers by (method, last path segment) from a queue per key."""
    calls = []

    def call(method, url, tok):
        key = (method, url.rstrip("/").rsplit("/", 1)[-1] if method == "GET" else method)
        calls.append(key)
        q = responses.get(key) or responses.get(method)
        return q.pop(0) if isinstance(q, list) else q
    return call, calls


class ReadCodesTest(unittest.TestCase):
    def setUp(self):
        p = mock.patch("time.sleep", lambda s: None)
        p.start()
        self.addCleanup(p.stop)

    def test_bundles_and_apks_both_count(self):
        call, _ = fake({"POST": (200, {"id": "e1"}), "DELETE": (204, {}),
                        ("GET", "bundles"): (200, {"bundles": [{"versionCode": 7}, {"versionCode": 3}]}),
                        ("GET", "apks"): (200, {"apks": [{"versionCode": 9}]})})
        with mock.patch.object(V, "call", call):
            self.assertEqual(V.read_codes("p", "t"), {"state": "OK", "highest": 9, "count": 3, "next": 10})

    def test_a_failed_bundles_read_is_retried_not_zero(self):
        call, calls = fake({"POST": (200, {"id": "e1"}), "DELETE": (204, {}),
                            ("GET", "bundles"): [(409, {"error": {"message": "edit deleted"}}),
                                                 (200, {"bundles": [{"versionCode": 7}]})],
                            ("GET", "apks"): (200, {"apks": []})})
        with mock.patch.object(V, "call", call):
            self.assertEqual(V.read_codes("p", "t")["highest"], 7)
        self.assertEqual(sum(1 for k in calls if k[0] == "POST"), 2)  # a fresh edit for the retry

    def test_persistent_failure_is_error(self):
        call, _ = fake({"POST": (200, {"id": "e1"}), "DELETE": (204, {}),
                        ("GET", "bundles"): (500, {"error": {"message": "backend"}}),
                        ("GET", "apks"): (200, {"apks": []})})
        with mock.patch.object(V, "call", call):
            r = V.read_codes("p", "t")
        self.assertEqual(r["state"], "ERROR")
        self.assertNotIn("highest", r)

    def test_no_listing(self):
        call, _ = fake({"POST": (404, {"error": {"message": "Package not found"}})})
        with mock.patch.object(V, "call", call):
            self.assertEqual(V.read_codes("p", "t")["state"], "NO_LISTING")

    def test_an_app_never_uploaded_has_no_codes(self):
        call, _ = fake({"POST": (200, {"id": "e1"}), "DELETE": (204, {}),
                        ("GET", "bundles"): (200, {}), ("GET", "apks"): (200, {})})
        with mock.patch.object(V, "call", call):
            self.assertEqual(V.read_codes("p", "t"), {"state": "OK", "highest": 0, "count": 0, "next": 1})


if __name__ == "__main__":
    unittest.main()
