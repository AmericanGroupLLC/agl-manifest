# Policies

## Truth
- Talk only truth; show proof where proof is possible. Never claim a build,
  test, upload or deploy happened without its output.
- Separate *done*, *done and verified*, and *not verified*.

## No fake data
- Apps show real data (Supabase project smvvjivvlprjhzhoizym, or keyless
  public/sandbox APIs) or an honest empty/error state. No invented people,
  prices, ratings, metrics, reviews, statuses, timers or marketing numbers.
- No demo/test login buttons in release builds. Real users only; testing uses
  dev@ / qa@ / admin@americangroup.ai (Supabase test accounts; the @safecodeg.com trio was deleted on 2026-10-12 at the owner's request — App Review's demo login is qa@americangroup.ai).

## Stores
- Check what the store checks (the IPA, the uploaded screenshots, the live
  URL), not a proxy for it. Gates: `scripts/apple_requirements.py`,
  `scripts/screenshot_audit.py`, `scripts/testflight/privacy_scan.py`.
- One-pass rule for submissions: nothing goes to review while a check fails.

## Safety of production
- Never `rsync --delete` into hosting folders; never `supabase config push`;
  production database changes only through the approved backend deploy.
- Secrets live in `~/agl/.secrets/` (chmod 600) or GitHub secrets — never in
  git, never in chat. Anything pasted into a chat is rotated.

## Data protection
- Collect only business contact data from public sources; no personal data
  in git.
