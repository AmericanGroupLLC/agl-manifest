# Website and domains

- Site: `/Users/spatchava/agl/americangroup.ai` (one branch `main`). Push deploys to `/home2/safecode/americangroup.ai`; `gh workflow run deploy.yml -R AmericanGroupLLC/americangroup.ai -f target=both` also refreshes safecodeg.com's folder (it 301s). No `--delete`, ever.
- Where each domain is served from: `gh workflow run hosting-info.yml -R AmericanGroupLLC/americangroup.ai`.
- Monitor: `python3 scripts/monitor_domains.py` (CI every 30 min, issue on failure).
- Store pages: `python3 scripts/verify_policy_urls.py` (147 URLs), `python3 scripts/verify_deletion_urls.py`.
- DNS: `python3 scripts/cloudflare_dns.py [--apply]` (zone pending until the founder switches nameservers — MA-046).
- App pages data: `python3 scripts/website_apps.py` (generated from store copy).
