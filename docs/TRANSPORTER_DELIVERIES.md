# Why Transporter.app shows an empty Delivered list

Measured 2026-10-04.

## The short answer

**Transporter.app's "Delivered" list only shows deliveries made through its own
window.** Uploads made with `iTMSTransporter`, the command-line tool inside the
same app bundle, do not appear there. The GUI keeps its history locally, and on
this Mac that history is empty:

```
~/Library/Preferences/com.apple.TransporterApp.plist
    NSNavPanelExpandedSizeForOpenMode, NSWindow Frame ActivityWindow   ← window geometry only
~/Library/Caches/com.apple.amp.itmstransporter/upload-tracking-files/  ← empty
```

The tracking directory is where an in-flight CLI upload is journalled, and it is
cleared on success — so a finished CLI delivery leaves nothing for the GUI to
list. Nothing is wrong with the uploads; the two halves of Transporter simply do
not share a history.

**The authoritative list is App Store Connect → TestFlight → Builds**, which is
what the table below is read from.

## What Apple actually holds

All 43 apps have a VALID build. 33 of them were delivered by
`scripts/testflight/transporter_upload.py` on 2026-10-03/04.

The remaining 10 kept an older build, and that is expected rather than a
failure: the IPA in `.dist` for those apps carries a **lower** build number than
the one CI had already uploaded, so Apple kept the newer one. CalcMaster is the
clearest case — the local IPA is version 4.0.2 build `5`, while App Store
Connect holds build `202609250224`.

| Still on the September CI build | Local IPA build |
| --- | --- |
| CalcMaster, CarDeal, daily-pulse, DriftDate, iMaps, Kinnav, Photriya, TripNest, Uscis-Case, VirtuBand | lower than what is already live |

To deliver those through Transporter too, rebuild their IPAs with a higher
build number first; the ones on disk are stale.

## To see a delivery in the GUI

Open Transporter.app, sign in as `srikanth.patchava@outlook.com`, and drag an
`.ipa` onto the window. That delivery — and only that kind — appears under
Delivered.
