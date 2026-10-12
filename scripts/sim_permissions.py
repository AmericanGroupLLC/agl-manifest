#!/usr/bin/env python3
"""Pre-answer an app's iOS permission prompts on a simulator, for store captures.

A fresh install shows the system prompt (microphone, location, photos, ...) the
first time the app asks, and an integration test cannot tap a system alert.
Found 2026-10-12: AGRecorder's script stops at "Microphone access is not
granted", iMaps' onboarding waits forever on the location prompt.

The grants are exactly the services the app declares in its Info.plist — what a
user who taps "Allow" would give it. Two passes, because they behave
differently (measured by the agents that fixed those two scripts):
  * microphone etc. granted while the app is not installed survive the install;
  * location granted before install does not — it has to be granted once the
    app's container exists, i.e. right after `flutter drive` installs it and
    before the app asks.

    from sim_permissions import services_for, grant, grant_after_install
"""
from __future__ import annotations

import pathlib
import plistlib
import subprocess
import threading
import time

# Info.plist usage key -> `simctl privacy` service.
KEY_TO_SERVICE = {
    "NSMicrophoneUsageDescription": "microphone",
    "NSLocationWhenInUseUsageDescription": "location",
    "NSLocationAlwaysAndWhenInUseUsageDescription": "location",
    "NSPhotoLibraryUsageDescription": "photos",
    "NSPhotoLibraryAddUsageDescription": "photos-add",
    "NSContactsUsageDescription": "contacts",
    "NSCalendarsUsageDescription": "calendar",
    "NSCalendarsFullAccessUsageDescription": "calendar",
    "NSRemindersUsageDescription": "reminders",
    "NSRemindersFullAccessUsageDescription": "reminders",
    "NSMotionUsageDescription": "motion",
    "NSAppleMusicUsageDescription": "media-library",
}


def services_for(app_dir: pathlib.Path) -> list[str]:
    """Services the app declares a purpose string for."""
    plist = app_dir / "ios/Runner/Info.plist"
    try:
        keys = plistlib.loads(plist.read_bytes()).keys()
    except Exception:
        return []
    return sorted({KEY_TO_SERVICE[k] for k in keys if k in KEY_TO_SERVICE})


def grant(udid: str, bundle_id: str, services: list[str]) -> None:
    for s in services:
        subprocess.run(["xcrun", "simctl", "privacy", udid, "grant", s, bundle_id],
                       capture_output=True, timeout=60)


def prepare(udid: str, bundle_id: str, app_dir: pathlib.Path, services: list[str],
            flutter: str, defines: list[str], env: dict | None = None) -> str:
    """Leave the app installed, never launched, with its permissions granted.

    Granting while the app runs terminates it (simctl: "Some permission changes
    will terminate the application if running"), and `flutter drive` launches
    the moment it has installed — so a grant raced after install killed iMaps'
    run on both devices (2026-10-12, 40-minute hangs). Instead: build the
    test target for the simulator, install it, grant, and let `flutter drive`
    reinstall over it — an over-install keeps the grants, and the app has
    still never run. Only needed for location; other grants survive install.
    Returns a short note for the log."""
    grant(udid, bundle_id, services)
    if "location" in services or "location-always" in services:
        # A fresh simulator has no position, so a granted app still never gets
        # a fix (iMaps: "Timed out after 25s waiting for a GPS fix"). Use a
        # real city so location-based screens show real local data.
        subprocess.run(["xcrun", "simctl", "location", udid, "set", "37.7749,-122.4194"],
                       capture_output=True, timeout=60)
    if "location" not in services and "location-always" not in services:
        return f"granted before install: {', '.join(services) or 'none'}"
    b = subprocess.run([flutter, "build", "ios", "--simulator", "--debug",
                        "--target=integration_test/store_screenshots_test.dart", *defines],
                       cwd=app_dir, capture_output=True, text=True, timeout=2400, env=env)
    apps = sorted((app_dir / "build/ios/iphonesimulator").glob("*.app"))
    if b.returncode != 0 or not apps:
        return "prebuild for location grant failed: " + (b.stdout + b.stderr).strip()[-200:]
    subprocess.run(["xcrun", "simctl", "install", udid, str(apps[0])], capture_output=True, timeout=300)
    grant(udid, bundle_id, services)
    return f"installed then granted (not launched): {', '.join(services)}"


def grant_after_install(udid: str, bundle_id: str, services: list[str],
                        timeout: float = 900) -> threading.Thread:
    """Grant again as soon as the app's container appears (flutter drive has
    installed it). Runs in the background; returns the thread."""
    def watch():
        end = time.time() + timeout
        while time.time() < end:
            r = subprocess.run(["xcrun", "simctl", "get_app_container", udid, bundle_id],
                               capture_output=True, text=True, timeout=30)
            if r.returncode == 0 and r.stdout.strip():
                grant(udid, bundle_id, services)
                return
            time.sleep(0.5)
    t = threading.Thread(target=watch, daemon=True)
    if services:
        t.start()
    return t
