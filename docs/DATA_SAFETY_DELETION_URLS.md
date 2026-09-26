# Play Data safety — account deletion URLs

Google flagged VirtuBand on 2026-09-21: the account-deletion URL in its Data
safety form returns 404 because it points at `americangroupllc.github.io`,
which is retired. Deadline **2026-09-24**.

The Data safety form is console-only — there is no Play API for it — so these
must be pasted by hand, per app, at:

  Play Console → the app → Policy → App content → Data safety →
  *Data collection and security* → **Account deletion URL**

Every URL below was generated from the live site checkout and all 43 pages are
committed to the website's `deploy` branch. **They go live only after cPanel →
Git Version Control → Deploy HEAD Commit is run** — verify one in a browser
before pasting the rest.

Do not trust an HTTP 200 when checking these. The host serves an SPA catch-all,
so an absent page still answers 200 with the marketing homepage; compare the
response body against a path you know does not exist.

The per-app URL list is the `Account/Data Deletion URL` column of
[`status.csv`](../status.csv) — all 43 are populated and every one was checked
against a nonsense control path by `scripts/verify_policy_urls.py`, because the
site is a single-page app that answers any path with a 200.
