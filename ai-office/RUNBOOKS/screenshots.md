# Screenshots

1. Capture: `python3 scripts/screenshots.py <apps>` — signs in with the QA account, unlocks Face ID, vets every frame (screenshot_audit classifier).
2. Local audit: `python3 scripts/screenshot_audit.py --local <App>`.
3. Upload: `python3 scripts/deliver_metadata.py --screenshots-only <apps>` — refuses failing sets and sets older than the last `lib/` change.
4. Prove: `bundle exec ruby scripts/testflight/asc_screenshots.rb <apps> && python3 scripts/screenshot_audit.py <apps>`.
Always look at a sample of the images before uploading.
