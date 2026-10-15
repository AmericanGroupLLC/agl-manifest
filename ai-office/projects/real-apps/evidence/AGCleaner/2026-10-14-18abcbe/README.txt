AGCleaner at HEAD 18abcbe, 2026-10-14 (issue #39 follow-up, software-developer)

Simulator: agl-qa-iphone-2 (iPhone 17 Pro Max, iOS 27.0, UDID 1B68B3E5-8F14-4B4C-8416-BBB1A1EDA415).
Address book: two test cards added with `xcrun simctl addmedia` (Adaeze Okafor and
"Ada O.", same phone number) - simulator-only fixtures, nothing in the app.
Contacts access granted with `xcrun simctl privacy grant contacts`.

How the frames were taken: a temporary integration test (not committed, deleted
after the run) started the app's real main() with the real device services and
tapped Review contacts -> group -> Merge -> Merge (preview) -> Merge (sheet) ->
Settings -> Restore points -> Restore -> Restore (sheet) -> Close -> Remove merged
card. Screens were captured with `xcrun simctl io ... screenshot`.

01_merge_preview.png  - merge preview for the two cards (first run).
02_after_restore_sheet_restore_disabled_behind.png - second run, right after the
    restore: the "Remove the merged card?" sheet is up; behind it the point says
    Restored and the Restore button is greyed out.
03_restore_points_restore_disabled.png - third run (clean app install), after
    restore and "Remove merged card": state "Restored", Restore button disabled,
    Share and delete still enabled. The point lists three cards because the
    second run's restore had re-created the originals while its merged card was
    still in the address book, so the third scan grouped three cards.
android-merged-permissions.txt - merged manifest of `flutter build apk --debug`.

Not verified (needs a real device): iCloud/Gmail/Exchange source badges, and what
deleting an iOS unified (linked) contact does to linked cards in other containers.
