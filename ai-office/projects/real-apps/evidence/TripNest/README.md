# TripNest — M1 "done when" grep, 2026-10-14 (app head 436ecf5, no code change)

```
$ grep -rniE "coming soon|this build|not connected|not available yet|not switched on|sample|BEST VALUE|LOWEST PRICE|QUICKEST|fromEnvironment|remoteConfig|americangroupllc\.com" mobile/lib
mobile/lib/core/ads/ad_config.dart:44:      String.fromEnvironment('ADMOB_BANNER_ANDROID');
mobile/lib/core/ads/ad_config.dart:46:      String.fromEnvironment('ADMOB_BANNER_IOS');
```

Resolved the way the spec intends: M1 targets the `TRIPNEST_*` feature switches, which are gone,
and "No build-time or remote switch may change what the app shows". The two remaining defines
supply the production banner unit ids at release build time, gate no feature or content, and
follow the portfolio convention (`scripts/agl_paths.py` `admob_defines`). Two other ways out were
rejected. Committing the unit ids would break `test/ads_test.dart` "no production unit id is
committed in lib/" (weakening a test). Hiding the token from grep would be dishonest. So
`specs/TripNest.md` M1 "Done when" now records this exception (same as RoomCraft M7 and
Uscis-Case M1(a)). `test/release_shape_test.dart` already pins
`{ADMOB_BANNER_ANDROID, ADMOB_BANNER_IOS}` as the only defines, in that one file.
The decision is recorded in `company/decision-log.md` (2026-10-14).

Re-run at 436ecf5 in `TripNest/mobile`: `flutter analyze` → `No issues found! (ran in 58.8s)`;
`flutter test` → `00:41 +306: All tests passed!`.
