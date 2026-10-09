#!/usr/bin/env python3
"""Find the Info.plist purpose strings an IPA needs, the way Apple finds them.

    python3 scripts/testflight/privacy_scan.py ~/agl/.dist/CalcMaster.ipa
    python3 scripts/testflight/privacy_scan.py --all        # every IPA in ~/agl/.dist

ITMS-90683 ("Missing purpose string in Info.plist") is decided by scanning the
compiled binary, not the app's own code: if any linked library references a
privacy-sensitive API, the key is required "even if your app never uses it".
store_checklist.py guessed instead — "geolocator => NSLocationWhenInUse" — and
missed that geolocator's iOS code also references requestAlwaysAuthorization,
which makes Apple demand NSLocationAlwaysAndWhenInUseUsageDescription.
CalcMaster build 202610081844 was delivered with exactly that warning.

This reads every Mach-O in the IPA (the app and its frameworks) for the same
API names Apple looks for, and reports each required key that the app's
Info.plist does not carry. transporter_upload.py refuses an IPA it flags, so
the warning is caught before delivery rather than in an email after it.
"""

from __future__ import annotations

import argparse
import pathlib
import plistlib
import re
import sys
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from agl_paths import DIST  # noqa: E402

# API name found in a binary -> purpose-string keys Apple requires for it.
RULES = [
    (b"requestAlwaysAuthorization", ["NSLocationAlwaysAndWhenInUseUsageDescription",
                                     "NSLocationWhenInUseUsageDescription"]),
    (b"requestWhenInUseAuthorization", ["NSLocationWhenInUseUsageDescription"]),
    (b"AVCaptureDevice", ["NSCameraUsageDescription"]),
    (b"AVAudioSession", []),  # playback alone needs no key; recording is below
    (b"requestRecordPermission", ["NSMicrophoneUsageDescription"]),
    (b"AVAudioRecorder", ["NSMicrophoneUsageDescription"]),
    (b"PHPhotoLibrary", ["NSPhotoLibraryUsageDescription"]),
    (b"PHAccessLevelAddOnly", ["NSPhotoLibraryAddUsageDescription"]),
    (b"UIImageWriteToSavedPhotosAlbum", ["NSPhotoLibraryAddUsageDescription"]),
    (b"CNContactStore", ["NSContactsUsageDescription"]),
    (b"EKEventStore", ["NSCalendarsUsageDescription"]),
    (b"EKEntityTypeReminder", ["NSRemindersUsageDescription"]),
    (b"CMMotionActivityManager", ["NSMotionUsageDescription"]),
    (b"CMPedometer", ["NSMotionUsageDescription"]),
    (b"SFSpeechRecognizer", ["NSSpeechRecognitionUsageDescription"]),
    (b"ATTrackingManager", ["NSUserTrackingUsageDescription"]),
    (b"HKHealthStore", ["NSHealthShareUsageDescription", "NSHealthUpdateUsageDescription"]),
    (b"CBCentralManager", ["NSBluetoothAlwaysUsageDescription"]),
    # Face ID is enforced at runtime (a crash on first use without the key),
    # not by the upload scan — CalcMaster's ITMS-90683 email did not list it
    # though the binary references LAContext. Reported as advisory below.
    (b"LAContext", ["NSFaceIDUsageDescription"]),
    (b"NFCNDEFReaderSession", ["NFCReaderUsageDescription"]),
    (b"MPMediaLibrary", ["NSAppleMusicUsageDescription"]),
]


def scan(ipa: pathlib.Path) -> tuple[dict, list[tuple[str, str]]]:
    """(info plist, [(missing key, the API that requires it)])."""
    with zipfile.ZipFile(ipa) as z:
        names = z.namelist()
        plist_name = next(n for n in names if re.fullmatch(r"Payload/[^/]+\.app/Info\.plist", n))
        info = plistlib.loads(z.read(plist_name))
        app = plist_name.rsplit("/", 1)[0] + "/"
        found: dict[str, str] = {}
        for n in names:
            if not n.startswith(app) or n.endswith("/"):
                continue
            # Mach-O executables: the app binary and each framework's binary.
            tail = n[len(app):]
            is_exec = "/" not in tail and "." not in tail          # Runner
            is_fw = re.search(r"Frameworks/[^/]+\.framework/[^/.]+$", tail)
            if not (is_exec or is_fw):
                continue
            data = z.read(n)
            if data[:4] not in (b"\xcf\xfa\xed\xfe", b"\xca\xfe\xba\xbe", b"\xfe\xed\xfa\xcf"):
                continue
            for needle, keys in RULES:
                if needle in data:
                    for k in keys:
                        found.setdefault(k, needle.decode())
    missing = [(k, api) for k, api in sorted(found.items())
               if not info.get(k) and k not in ADVISORY]
    return info, missing


# Reported, never blocking:
#  - Face ID is enforced at runtime, not by the upload scan (CalcMaster's
#    ITMS-90683 email did not list it although its binary references LAContext).
#  - Tracking: the AdMob SDK links ATTrackingManager in 17 apps, but only
#    CalcMaster requests tracking permission. Adding the key to an app that
#    never shows the prompt invites a 5.1.2 rejection ("we could not locate
#    the App Tracking Transparency request"), which is worse than the risk
#    this would cover. If Apple ever names it in an ITMS-90683 email, move it
#    out of this set.
ADVISORY = {"NSFaceIDUsageDescription", "NSUserTrackingUsageDescription"}


# Apple's automated "the app contains VPN functionality" analysis. It asks
# for a written answer, not a purpose string. WiFiTrail build 2 drew it with
# no VPN code at all: network_info_plus links NetworkExtension.framework to
# call NEHotspotNetwork.fetchCurrent for the Wi-Fi name (verified with
# otool -L). Of the 41 IPAs in DIST only WiFiTrail matches these.
VPN_NEEDLES = [
    b"/System/Library/Frameworks/NetworkExtension.framework/NetworkExtension",
    b"NEHotspotNetwork", b"NEHotspotConfigurationManager", b"NEVPNManager",
    b"NETunnelProviderManager", b"NEPacketTunnelProvider", b"NEAppProxyProvider",
    b"NEFilterDataProvider", b"NEDNSProxyProvider",
]


def vpn_scan(ipa: pathlib.Path) -> list[str]:
    """['<binary>: <symbol>', ...] for each Mach-O that would draw the VPN question."""
    hits = []
    with zipfile.ZipFile(ipa) as z:
        for n in z.namelist():
            if not re.search(r"\.app/(Frameworks/[^/]+\.framework/[^/.]+|PlugIns/[^/]+\.appex/[^/.]+|[^/.]+)$", n):
                continue
            data = z.read(n)
            if data[:4] not in (b"\xcf\xfa\xed\xfe", b"\xca\xfe\xba\xbe", b"\xfe\xed\xfa\xcf"):
                continue
            for needle in VPN_NEEDLES:
                if needle in data:
                    hits.append(f"{n.rsplit('/', 1)[-1]}: {needle.decode().rsplit('/', 1)[-1]}")
                    break
    return hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("ipas", nargs="*")
    args = ap.parse_args()
    ipas = sorted(DIST.glob("*.ipa")) if args.all else [pathlib.Path(p) for p in args.ipas]
    bad = 0
    for ipa in ipas:
        try:
            info, missing = scan(ipa)
        except Exception as e:  # unreadable IPA is itself worth reporting
            print(f"  {ipa.name:28} cannot scan: {type(e).__name__}")
            bad += 1
            continue
        tag = f"build {info.get('CFBundleVersion')}"
        if missing:
            bad += 1
            print(f"  {ipa.name:28} {tag:16} MISSING " +
                  ", ".join(f"{k} (binary references {api})" for k, api in missing))
        else:
            print(f"  {ipa.name:28} {tag:16} ok")
    print(f"\n  {len(ipas)} IPA(s) scanned, {bad} would get ITMS-90683 or cannot be read")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
