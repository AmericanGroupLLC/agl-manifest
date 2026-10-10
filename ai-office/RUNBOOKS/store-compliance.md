# Store compliance

| Need | Command |
| --- | --- |
| Read rejections (no 2FA) | `bundle exec ruby scripts/testflight/rejection_reasons.rb --session-only` (exit 3 = session expired: founder runs `fastlane spaceauth -u rainbow472.sri@gmail.com`) |
| Analysis | `python3 scripts/rejection_report.py` → docs/REJECTION_ANALYSIS.md |
| Every Apple requirement | `python3 scripts/apple_requirements.py [App]` → docs/APPLE_REQUIREMENTS.md |
| Binary scans (ITMS-90683/90737, VPN) | `python3 scripts/testflight/privacy_scan.py --all` |
| Review notes (keeps app-specific fields) | `bundle exec ruby scripts/testflight/review_notes.rb [App]` |
| Store URLs | `bundle exec ruby scripts/testflight/asc_urls.rb --check` |
| Holds / freeze | docs/store-holds.json, `scripts/testflight/account_freeze.rb` |
