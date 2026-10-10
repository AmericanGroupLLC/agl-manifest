# Integrations

| System | How the office reaches it | Credential |
| --- | --- | --- |
| GitHub | `gh` CLI | founder's gh login / Actions `GITHUB_TOKEN` |
| App Store Connect | `scripts/testflight/env.sh` (API key) + `--session-only` web session | `~/agl/.secrets/AuthKey_*.p8`, fastlane session cookie |
| Google Play | `scripts/play_*.py` | `~/agl/.secrets/play-service-account.json` |
| Firebase | REST via `gcloud auth application-default` (the CLI breaks behind the proxy) | ADC |
| AdMob | `scripts/admob_setup.py` (read; writes refused) | ADC with admob scopes |
| Supabase | `scripts/supabase_accounts.py`, backend deploy.yml | `supabase` CLI login; repo secrets |
| HostGator | website deploy.yml over SSH | repo secret SSH_PRIVATE_KEY |
| Cloudflare | `scripts/cloudflare_dns.py` | `~/agl/.secrets/cloudflare-token` |

Schemas for structured hand-offs are in `schemas/`.
