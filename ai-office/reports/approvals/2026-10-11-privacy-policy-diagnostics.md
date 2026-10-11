# Approval: privacy policies must disclose crash/analytics data

- **Decision needed:** approve (merge) https://github.com/AmericanGroupLLC/americangroup.ai/pull/1, and give wording for 3 hand-written policies.
- **Why now:** App Privacy labels for 40 apps were corrected and published on 2026-10-11 to declare crash (and analytics) data. 26 live policy pages still say "no analytics and no crash reports" — a Guideline 5.1.1 contradiction a reviewer can see.
- **Exact action:** merge PR #1 (deploys automatically). For agrammarly, herjourney, radiotune (hand-written pages) either reply "use the generated wording" or edit the Third-parties / Analytics paragraph to name Firebase Crashlytics (all three) and Analytics + Performance (herjourney, radiotune).
- **Evidence:** generator fix in agl-manifest `scripts/policy_pages.py`; after `policy_pages.py --force`, no generated page contains the false sentence; labels per app in `store/privacy/*.json` (`_derived_from.crash/analytics`); publish proof in `<DIST>/privacy-upload.json` (Apple `last_published` timestamps).
- **Risks / undo:** revert the merge commit; the website redeploys the previous pages.
