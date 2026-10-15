"""build_ipa.py carries ios/Runner/Runner.entitlements into the exported IPA and refuses an IPA without them.

    python3 -m unittest discover -s scripts/tests -v
"""

from __future__ import annotations

import pathlib
import plistlib
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import build_ipa as B  # noqa: E402

ENT = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
\t<!-- a comment, as the app repos write them -->
\t<key>com.apple.developer.networking.wifi-info</key>
\t<true/>
</dict>
</plist>
"""


class AppEntitlementsTest(unittest.TestCase):
    def test_reads_runner_entitlements_with_comments(self):
        with tempfile.TemporaryDirectory() as t:
            ios = pathlib.Path(t)
            (ios / "Runner").mkdir()
            (ios / "Runner/Runner.entitlements").write_text(ENT)
            self.assertEqual(B.app_entitlements(ios), {"com.apple.developer.networking.wifi-info": True})

    def test_no_file_or_empty_dict_means_nothing_to_carry(self):
        with tempfile.TemporaryDirectory() as t:
            ios = pathlib.Path(t)
            self.assertEqual(B.app_entitlements(ios), {})
            (ios / "Runner").mkdir()
            (ios / "Runner/Runner.entitlements").write_bytes(plistlib.dumps({}))
            self.assertEqual(B.app_entitlements(ios), {})


class EntitlementsMissingTest(unittest.TestCase):
    def test_nothing_wanted_is_never_missing(self):
        self.assertEqual(B.entitlements_missing(pathlib.Path("/nonexistent.ipa"), {}), [])

    def test_an_unsigned_app_lacks_every_wanted_entitlement(self):
        with tempfile.TemporaryDirectory() as t:
            ipa = pathlib.Path(t) / "x.ipa"
            with zipfile.ZipFile(ipa, "w") as z:
                z.writestr("Payload/Runner.app/Info.plist", plistlib.dumps({"CFBundleExecutable": "Runner"}))
                z.writestr("Payload/Runner.app/Runner", b"not signed")
            self.assertEqual(B.entitlements_missing(ipa, {"aps-environment": "production"}), ["aps-environment"])

    def test_an_ipa_without_an_app_lacks_everything(self):
        with tempfile.TemporaryDirectory() as t:
            ipa = pathlib.Path(t) / "x.ipa"
            with zipfile.ZipFile(ipa, "w") as z:
                z.writestr("Payload/readme.txt", b"")
            self.assertEqual(B.entitlements_missing(ipa, {"a": True, "b": True}), ["a", "b"])


if __name__ == "__main__":
    unittest.main()
