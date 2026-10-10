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
[`status.csv`](../status.csv), and the verified URLs are also committed as
[`deletion-urls.json`](deletion-urls.json).

**Read the slug, do not guess it.** The site is case-sensitive and several
slugs are not the lowercased repo name:

| Repo | Slug |
| --- | --- |
| iMaps | `iMaps` |
| iMeasure | `iMeasure` |
| TripNest | `TripNest` |
| daily-pulse | `dailypulse` |
| Uscis-Case | `uscis-case-tracker` |

`https://www.americangroup.ai/policy/imaps/delete-account.html` — lowercase —
returns HTTP 200 and 369,371 bytes, which is the marketing single-page app, not
a deletion page. The correct URL returns 11,364 bytes. Every check here
therefore compares byte length against a nonsense control path; a 200 on this
site proves nothing. All 43 verified that way on 2026-09-28.
