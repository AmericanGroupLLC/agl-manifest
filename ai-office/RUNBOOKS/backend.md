# Backend (Supabase smvvjivvlprjhzhoizym, AWS us-east-2)

- Migrations: `AmericanGroupLLC-Backend/supabase/migrations/*.sql` on branch `dev`.
- Deploy: backend `.github/workflows/deploy.yml` — runs when migrations change or by hand; waits for the founder's approval (`production` environment); first run needs `baseline=true` (MA-044).
- Auth checks: `python3 scripts/supabase_accounts.py --check` / `--audit-config` (site_url must not be localhost — MA-042).
- Never: `supabase config push`, `supabase db push`, direct SQL on production.
