# Security

- Secrets: `~/agl/.secrets/` (chmod 600) and GitHub repo secrets only. Gitignored everywhere: `*.p8`, keystores, `SFG-*.xlsx`.
- Anything pasted into a chat must be rotated (open item: the Cloudflare token, 2026-10-09).
- Scan: `for r in ~/agl/*/; do git -C "$r" ls-files | grep -E '\.p8$|\.jks$|keystore|SFG-.*xlsx'; done` (expect nothing).
- Purpose strings and tracking: `python3 scripts/testflight/privacy_scan.py --all`.
