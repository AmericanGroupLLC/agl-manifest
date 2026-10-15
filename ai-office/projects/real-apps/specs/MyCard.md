# Spec: MyCard — a spare copy of your wallet, and a plan for the night you lose it

Author: product-manager (AI office), 2026-10-12
Project: real-apps (`../plan.md`, criteria 1–7)
Repo: `/Users/spatchava/agl/MyCard` (app in `mobile/`)
Base: `main` @ `ee1689c5c902eb5e3f7cee2c66d9042be3064564`. Source: `git -C /Users/spatchava/agl/MyCard rev-parse HEAD` and `git branch --show-current`, run 2026-10-12.
Baseline, run 2026-10-12 in `mobile/` against that base:
- `flutter analyze` → "No issues found! (ran in 16.0s)"
- `flutter test` → "+246: All tests passed!"

**Other people's uncommitted work is in this repo. Do not touch it.** `git status --short` shows:
- changes under `mobile/fastlane/**`: `review_information/notes.txt`, every phone/tablet screenshot, and 5 untracked new screenshots;
- `mobile/ios/Podfile.lock`. Its diff is one line: `COCOAPODS: 1.16.2` → `1.17.0`.

This spec changes none of those files.

**Trap.** Adding a native plugin makes CocoaPods rewrite `Podfile.lock`. Native plugins here means `share_plus`, `url_launcher` and the SHOULD-level `mobile_scanner` / `flutter_local_notifications`. Before adding one, run `git diff mobile/ios/Podfile.lock`. If the other edit is still there, do not commit `Podfile.lock`; report it and use the plugin-free fallback written next to each item. Every MUST below can be met with **pure-Dart packages only**. `barcode_widget` 2.0.4 is pure Dart: `pub.dev/api/packages/barcode_widget` shows dependencies `barcode` + `flutter`, and no `flutter.plugin` block.

---

## 1. Problem

**Apple's state.** `/Users/spatchava/agl/.dist/rejections.json` → "MyCard", in order:
- **2.1 Information Needed**, 2026-09-27T01:12Z.
- **Our reply**, 2026-09-29T16:46Z. It was the portfolio template and said "EXTERNAL SERVICES USED None. The app works entirely on the device and calls no external service." That was written before AdMob was added: commit `f39aeb6` "AdMob via agl_ads…" is dated 2026-10-12T11:13. Today's binary and notes do use AdMob and Crashlytics, so the next notes must say so.
- **2.3.3**, 2026-09-29T18:20Z: "The screenshots only display a login screen".
- **4.3(a)/(b) + 4.2.6**, 2026-10-05T21:25Z. Same text as the other 25 apps.

Google Play: PRODUCTION_DRAFT_STAGED.

**What is real today (read 2026-10-12). This is the strongest code in the portfolio, and the spec keeps all of it.**
- **Crypto.**
  - AES-256-GCM vault in `lib/core/crypto/vault_cipher.dart`: 96-bit random nonce, 128-bit tag, versioned header.
  - DEK in Keychain (`first_unlock_this_device`) or EncryptedSharedPreferences (`data_key_store.dart`).
  - Whole-wallet single-blob sealing with atomic write-then-rename (`core/storage/card_vault.dart`, `vault_blob_store.dart`).
  - A damaged vault is reported and never overwritten (`card_repository.dart` `VaultDamagedException`).
  - Erase is a crypto-shred.
- **Unlock.**
  - App-level biometric/passcode gate that re-locks on background and hides revealed fields (`features/auth/*`).
  - A per-card second gate for protected cards, including on edit and on "Remove protection" (`card_detail_screen.dart` `_ensureUnlocked`).
- **Cards.**
  - 37 kinds, with per-kind field layouts (`models/card_field.dart`).
  - Masked numbers with auto-hiding reveal and copy (`widgets/sensitive_field.dart`).
  - Search over non-secret fields only (`wallet_card.dart` `matchesQuery`).
  - Favourites, archive, category filters.
- **Honest copy.** Honest states for damaged vault, empty and filtered, plus an honest "What leaves this device" text (`settings_screen.dart:31`).

**Why Apple sees a template or "already widely available" (evidence):**
- **The core pitch is a commodity.** Apple's keyless iTunes Lookup API was run 2026-10-12. I read descriptions only and did not run any app.
  - **Secure Card Manager & Wallet** (Texode, id1405577445, 516 ratings): "Advanced Encryption Standard (AES) with a key length of 256 bits. This key is generated on your device", plus "Erase Data, Emergency PIN Code and Facedown Lock". This is our store description almost word for word.
  - **My Card Wallet: Secure Notes** (highglossy, id1259742455): "Store card numbers, expiration dates, and notes • Add cards by scanning them".
  - **Offline Card Vault: Holder** (id6475649492): "a private offline vault for storing important card details".
  - **Card Holder: Store Card Wallet** (id1618760047): barcode/QR loyalty cards, PIN lock.
  - 1Password (id1511601750, 42,620 ratings) and Bitwarden (id1137397744, 33,954) store cards and IDs too.
  - "Encrypted wallet on your phone" (our subtitle) is therefore 4.3(b) on its face.
- **It is a kitchen sink, not a product.**
  - "37 card types" is the headline in four places: `wallet_screen.dart:440`, `kind_picker_sheet.dart:67`, `settings_screen.dart:212`, and the store copy.
  - The 37 include **Task** and **Reminder**, which duplicate Apple Reminders. **Reminder never reminds**: the field is labelled "Remind me at" (`card_field.dart:137`), but there is no notification plugin in `pubspec.yaml`, so nothing ever fires. That is a dead control.
  - The list also includes developer secrets (API key, SSH key) that belong to a password manager.
- **"This build" tell.** `card_editor_screen.dart:398`: "Typed in manually — this build does not read NFC tags."
- **Stored barcodes are text only.** A loyalty, library or boarding-pass "Barcode value" is shown as a monospace string (`sensitive_field.dart:84`). No barcode is drawn, so the card cannot be scanned at a counter. The field exists, but the job it implies does not work.
- **No way out of the phone.**
  - There is no backup or export. "Erase is final" is said proudly, but a lost or broken phone also loses every card, and the app offers nothing for that.
  - `expiresAt` exists, but nothing surfaces upcoming expiries except an "Expired" tag after the fact.
- **Skin tells:**
  - The icon comes from the generator: `agl-manifest/scripts/generate_app_icons.py:72` `"MyCard": ("credit_card", "#212121", "#616161")`.
  - The splash is shared: `ios/Runner/Base.lproj/LaunchScreen.storyboard` shasum `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`, the same as 37 apps.
  - No typeface: `pubspec.yaml` has no `fonts:`.
  - Tailwind hexes in `app/theme.dart:21-33`: `10B981 F59E0B EF4444 3B82F6 F8FAFC E2E8F0 020617 0F172A 1E293B 334155`.
  - A diagonal two-colour gradient square on the lock screen (`AppTokens.primaryGradient`, `lock_screen.dart:31`).
  - Neon OKLCH kind accents (`theme.dart:72-76`).
  - Stock Material on iOS, with 0 `CupertinoIcons`.
- **Shell and copy tells:**
  - `AglAdBanner` is pinned in the `bottomNavigationBar` slot (`wallet_screen.dart:231`).
  - Generic tagline "Every card. Secured. Yours." (`lock_screen.dart:47`, `settings_screen.dart:212`).
  - The App Store name "iMyCard" uses both the portfolio's "i" prefix and its "My" prefix.
  - A large unrelated app is called **"MyCardWallet."** (Blackhawk Network, id1230221247, 96,473 ratings, per the iTunes Search API).
- **Store tells:**
  - The Play feature graphic shows the old "MC" monogram.
  - The privacy label is the shared 20-app label. It declares `PRODUCT_INTERACTION/ANALYTICS` and `PERFORMANCE_DATA` (`store/privacy/MyCard.json`), but the binary deactivates both: `Info.plist:290-293` `FIREBASE_ANALYTICS_COLLECTION_DEACTIVATED` true and `firebase_performance_collection_deactivated` true; `main.dart` deliberately skips `AglInsights.init`. The label over-declares.

## 2. User, core job, signature

**User.** An adult who carries a physical wallet (two to five payment cards, a driver's licence, a health-insurance card, a few loyalty, library or transit cards) and keeps a passport and other documents at home. Their nightmare is the evening the wallet is gone: who to call first, which numbers, what was even in it, and later what to tell the police or insurer. Secondary: someone travelling who needs their passport, insurance and boarding pass details at hand offline.

**Core job: keep a spare of your wallet and use it.** The user goes through their physical wallet once and adds each card. MyCard then:
1. holds everything encrypted on the phone (kept as is);
2. **shows any loyalty, library, membership, ticket or boarding-pass barcode at the counter**, drawn properly;
3. tells them **what expires soon**: cards, licence, passport (with a 6-month travel warning), insurance;
4. lets them **back the whole thing up** into a passphrase-sealed file they control, because there is no cloud.

**Signature feature: the Lost-wallet plan.**
- **Before.** Each card that lives in the physical wallet is marked **"In my wallet"** and carries **"If lost, call"**: the number printed on its back, typed by the user. The home screen shows plan readiness: "In your wallet: 9 · 7 have a lost-card number".
- **Trigger.** When the wallet goes missing, one visible button on the home screen ("My wallet is lost or stolen") starts a plan.
- **The plan:**
  - Every "In my wallet" card, ordered by urgency: payment cards, then identity, then health and insurance, then access/work, then the rest.
  - For each: last 4 digits only, the number to call, and status steps (Called → Frozen / Cancelled → Replacement ordered, or Found it), each with a timestamp and an optional reference number.
  - A progress header ("4 of 9 handled").
  - A **lost-wallet report** to share with police, insurer or bank: what was lost (titles, kinds, last 4 only), when, and every action taken, with times and reference numbers.
- **After.** Plans are kept encrypted in the vault, closed when everything is handled, and listed in history. Everything works in airplane mode.

**Competitor check** (iTunes Lookup/Search API, keyless, 2026-10-12; descriptions only). WebSearch is unavailable here: the hook returned "Internet mode is not enabled".

| App (id, ratings) | What its description offers | Lost/stolen response? |
|---|---|---|
| Secure Card Manager & Wallet (1405577445, 516) | AES-256 on-device key, Erase Data, Emergency PIN, Facedown Lock; subscription for backup/cloud sync | No. "lost"/"stolen" do not appear |
| My Card Wallet: Secure Notes (1259742455, 140) | card numbers, expiry dates, scanning, encrypted "Capsules" for a trusted person | No |
| Offline Card Vault: Holder (6475649492, 2) | offline card storage | No |
| Card Holder: Store Card Wallet (1618760047, 43) | barcode/QR loyalty cards, iCloud sync, PIN | No |
| CardStar (301460311, 889) | loyalty cards; "never have to worry about lost cards … cloud backup" | Only means the loyalty card itself is backed up |
| 1Password (1511601750, 42,620) / Bitwarden (1137397744, 33,954) | cloud-synced vault with card and ID items | 1Password mentions "even if your device is stolen" (data safety), not a wallet-loss plan |
| Document Expiry (1643313779, 22) | expiry tracking for passports, licences, insurance | No |

**Claimed gap, stated narrowly.** None of the descriptions read offer a guided, ordered, timestamped response to a lost physical wallet with an exportable incident report. Together with on-device barcodes, an expiry radar and a passphrase backup, with no account, cloud or subscription, that is the angle. Apple Wallet is built in and was not checked through the API. **Competitor behaviour beyond these descriptions is not verified.** The "encrypted card vault" part alone is crowded, so the signature, not the encryption, must lead the screenshots (§5).

**Must not duplicate.**
- MyFinance owns budgets and transactions. MyCard shows no balances, spending, statements or transactions, ever.
- MyHealth's insurance-card screen stores nothing (`insurance_card_screen.dart`), so this is no duplicate.
- Notes and tasks as a productivity feature go (M1).

## 3. Data sources

**Everything is on-device. No network call is added by this spec.** No Supabase, no public API, no account. The only things that leave the device stay as they are: the AdMob ad requests and Crashlytics crash reports already declared in `settings_screen.dart:31-49`.

| Data | Where | Notes |
|---|---|---|
| Cards, the new `inWallet` flag, `lostPhone`, `replaceAt`, card face colour | existing sealed vault (`CardVault`, AES-256-GCM) | `lostPhone`/`replaceAt` are metadata keys, so no schema change for cards. `inWallet` is a new top-level bool; when absent on read it gets the kind default (M3) |
| Lost-wallet plans (incidents) | same sealed vault, envelope `schemaVersion: 2` → `{schemaVersion, cards, incidents, lastBackupAt}` | v1 files still read (incidents = []). An old build reading v2 reads only `cards`, so nothing breaks; tested both ways |
| Card network label and checksum | pure Dart table in code (IIN prefixes: Visa 4; Mastercard 51–55, 2221–2720; Amex 34, 37; Discover 6011, 644–649, 65; JCB 3528–3589; Diners 300–305, 36, 38–39; UnionPay 62) plus Luhn | Text labels only, no network logos (trademarks). Prefix list from published ISO/IEC 7812 issuer ranges as commonly documented; not re-fetched today. Unit-tested with the public test numbers 4111111111111111, 5555555555554444, 378282246310005, 6011111111111117 |
| Barcodes and QR | drawn on the device by `barcode_widget` (pure Dart) | formats: QR, Code 128, Code 39, EAN-13, EAN-8, UPC-A, PDF417, Aztec, Data Matrix |
| Backup file | passphrase → PBKDF2-HMAC-SHA256 (pointycastle, already a dependency) → existing `VaultCipher` | no server; the file goes where the user puts it |

Nothing is seeded. A fresh install has an empty wallet with an honest empty state (M6). No sample cards and no fake numbers anywhere in `lib/`.

## 4. Acceptance criteria

### MUST (what Apple has to see to judge this a real, distinct app)

**M1. Remove the dead, dishonest and duplicative parts (criteria 1, 5).**
- **Add picker.** Remove **Task**, **Reminder** and **NFC Tag** from the Add picker (`kind_picker_sheet.dart`). Existing cards of those kinds still decode, render, edit and convert (`CardKind.fromWireName` and `convertedTo` stay, so no user data is lost). Their detail and editor show `reminderAt` as "Date", not "Remind me at".
  - Delete the "Typed in manually — this build does not read NFC tags." helper (`card_editor_screen.dart:398`). For a legacy NFC card the field is labelled "Tag ID".
  - Remove the "Reminders firing in the next 24 hours" rule from `CardSorter` only if nothing else needs it. Its tests change with it, and the commit names them.
- **Regroup the picker** around the user:
  - **In your wallet**: credit, debit, driver's licence, ID, insurance, health, loyalty, rewards, gift, transit, access, employee, student, library, membership.
  - **Travel & tickets**: boarding pass, event ticket, voucher, hotel key.
  - **At home**: passport, vaccination card, SIM card, Wi-Fi, business card, contact.
  - **Secure notes & logins**: note, password, crypto wallet, API key, SSH key, barcode, QR code, URL, custom.
- **Remove every "37 card types" string** (`wallet_screen.dart:440`, `kind_picker_sheet.dart:67`, `settings_screen.dart:212`) and the tagline "Every card. Secured. Yours." (`lock_screen.dart:47`, `settings_screen.dart:212`).
- **Acceptance:**
  - `grep -rniE "this build|37 card|Every card\. Secured|coming soon|not connected|unavailable in|Simulator mode|sample|demo|Remind me" mobile/lib` → 0 hits. `AuthOutcome.unavailable` is an enum name, not UI copy, and is allowed.
  - A widget test shows the picker has no Task, Reminder or NFC Tag entry.
  - A test decodes a v1 vault holding a reminder and a task and renders both.

**M2. Core job: add a card properly, and use it at the counter.**
- **Barcode at the counter.**
  - For every kind with `barcodeData`, the detail screen draws the code with `barcode_widget`. The free-text "Barcode format" field (`card_field.dart:128`) becomes a picker of the 9 formats in §3. Default: Code 128, or QR for the QR kind. Legacy free-text values map case-insensitively ("qr", "ean13", "code128"…); unknown values fall back to Code 128 with the original kept in metadata.
  - Invalid data for the chosen format (an EAN-13 with a bad check digit, letters in UPC-A) shows inline "This value isn't a valid EAN-13. Check the digits or choose Code 128." It never throws or draws a broken image.
  - A **"Show at counter"** button opens a full-screen page: white field, the code at full width, the value beneath in Azeret Mono, the card title, portrait. Protected cards stay behind the per-card gate first.
- **Card numbers.**
  - The editor formats as typed (4-4-4-4; Amex 4-6-5) and shows a text network label (Visa, Mastercard, American Express, Discover, JCB, Diners Club, UnionPay) from the §3 table.
  - It shows a non-blocking warning, "This number fails the card checksum. Check for a typo.", when Luhn fails on a payment-card kind.
  - The list tile shows "Visa •••• 1111".
- **Expiry text becomes a date.**
  - `cardExpiry` "MM/YY", "MM/YYYY" or "MM-YY" parses to the **last day of that month**, because cards are valid through the month. When `expiresAt` is empty it is filled from that; a value the user set explicitly is never overwritten.
  - Unparseable text stays as typed and simply is not on the radar (M4).
- **Clipboard hygiene.** After copying a card number or a secret, MyCard clears the clipboard after 60 s if the clipboard still holds that exact value and the app is still running. The snackbar says exactly that: "Copied. MyCard clears it in 60 seconds if it's still there." Plain fields are not auto-cleared.
- **Acceptance:**
  - Unit tests: format mapping, EAN-13/UPC-A validation, Luhn, the network table with the four test numbers plus a 2221-prefixed Mastercard, expiry parsing ("02/28" → 2028-02-29; "12/2030" → 2030-12-31; "13/28" → null).
  - A widget test draws a Code 128 loyalty card and opens Show at counter.
  - A widget test proves a protected card's Show at counter needs the unlock first.

**M3. Signature: the Lost-wallet plan.**
- **Model.**
  - `WalletCard.inWallet` (bool, persisted). Default is true for every kind in the M1 "In your wallet" group, false otherwise, and applied on read when the field is absent.
  - Metadata `lostPhone` (label "If lost, call", hint "The number on the back of the card", phone keyboard) on credit, debit, insurance, health, access, employee, transit, gift, loyalty, rewards and membership.
  - Metadata `replaceAt` (label "How to replace it", free text) on driver's licence, ID, passport, student and employee.
  - **No numbers are prefilled, suggested or looked up.**
  - `Incident {id, startedAt, note, closedAt?, items: [IncidentItem {cardId, title, kindWire, last4?, phone?, status, reference?, log: [{status, at}]}]}`. The title, last4 and phone snapshot are taken when the plan starts, so the report survives later edits or deletion of the card. Status is one of `todo | called | frozen | cancelled | replacementOrdered | found`.
- **Readiness, on home.** A plan tile reads "In your wallet: N cards · M have a lost-card number". When M < N it adds "Finish your plan", which opens a list of the in-wallet cards missing a number; each row opens that card's editor. With N = 0: "Mark the cards you carry as In my wallet, so MyCard knows what to cancel if it's lost."
- **Start.** A clearly labelled button on the plan tile, **"My wallet is lost or stolen"**. It is always visible when N ≥ 1 and is never behind a gesture, setting or date. It opens a sheet with an optional "Where and when (for your report)" note, then **Start plan**. Only one open plan at a time; when one is open, the home tile becomes "Lost-wallet plan in progress · 4 of 9 handled".
- **Plan screen.**
  - Ordered groups: Payment cards → ID & licences → Health & insurance → Access & work → Everything else. Within a group, by title. The ordering function is pure and unit-tested.
  - Each row: card title and kind, •••• last 4 (never more), the lost-card number in large Azeret Mono with **Copy number**. **Call** (a `tel:` link through `url_launcher`) is included only if the Podfile.lock check in the header is clear; otherwise Copy only, reported in the commit. For ID kinds the row shows `replaceAt` instead.
  - A status stepper (Called / Frozen / Cancelled / Replacement ordered / Found it), each tap time-stamped, plus a reference-number field.
  - Missing number: "No number saved. Look on your bank's app or website." Never an invented number.
- **Report.**
  - "Lost-wallet report" plain text: started date/time, note, then per item "Title — Kind — •••• 1234 — Cancelled 21:14 (ref ABC123); Called 21:09", then "Prepared with MyCard on this phone. Card numbers are shortened to the last 4 digits."
  - It never contains a full number, CVV, PIN, password or any `secret`.
  - Share through `share_plus` if the Podfile.lock check is clear. Otherwise, and always as a second action, **Copy report** (Flutter `Clipboard`).
- **Close and history.** "Mark plan finished" sets `closedAt`. Settings › "Lost-wallet plans" lists past plans read-only, with their reports. Deleting a plan needs confirmation. Erase all data removes plans with everything else.
- **No ads** on the readiness list, start sheet, plan screen or report.
- **Acceptance:**
  - Unit tests: kind defaults for `inWallet`, legacy-read default, ordering, status log timestamps, report text with a seeded card whose number is `4111111111111111` and secret `123` (asserts `4111111111111111`, `411111` and `123` do not appear, and `•••• 1111` does), and v2 envelope round trip with incidents.
  - A widget test runs the full flow: two in-wallet cards → start plan → mark one Cancelled with a reference → relaunch on the same in-memory vault → the plan is still open with that status → finish → it appears in history.

**M4. Depth: expiry radar, search and filter, empty/error states.**
- **Expiry radar (home "Coming up").** Cards with an `expiresAt` (explicit or parsed in M2) that is already past (danger colour, "Expired 3 Mar"), within 30 days, or within 90 days. Passports also appear from **6 months** out, with "Some countries require 6 months' passport validity. Check your destination's rules." Tapping opens the card. Archived cards are excluded. Nothing to show → the strip is not drawn; no empty card.
- **Search and filter** move off the home body to a **Search** page from an app-bar icon. It keeps the current search over non-secret fields and the Favourites, Protected, Archived and category filters, and adds two filters: **In my wallet** and **Expiring (90 days)**. The existing `CardQuery` tests keep passing, and new ones cover the two filters.
- **States kept and checked.** Damaged vault (banner + adding disabled), empty, filtered-empty, unprotected device banner. **New:** the empty home reads "Take out your wallet and add the first card. It stays encrypted on this phone." with **Add a card**.
- **Acceptance:** unit tests for the radar windows (boundary days 0/30/90, and the passport 6-month rule using an injected `now`). Widget tests for the two new filters and the new empty state.

**M5. Depth: passphrase-sealed backup and restore (export that fits a no-cloud vault).**
- **Export (Settings › Backup).**
  - Re-verify with biometrics or passcode first, as Erase does.
  - The user enters a passphrase twice (minimum 12 characters) and sees: "If you forget this passphrase, nobody can open this backup, including us."
  - Key: PBKDF2-HMAC-SHA256, random 16-byte salt, **600,000 iterations**. That is the OWASP Password Storage Cheat Sheet figure for PBKDF2-HMAC-SHA256; it was not re-fetched today. Run it in `compute`. **Measure it on the iOS simulator.** If it takes over 8 s, use the largest count under 3 s, record the measured time and count in the commit message, and keep the count in the file header so it can be raised later.
  - Plaintext is the full v2 envelope, sealed with the existing `VaultCipher`.
  - File layout: `MYCARDBK` (8 bytes) ‖ format 1 ‖ kdf id 1 ‖ iterations (u32 BE) ‖ salt (16) ‖ `VaultCipher` blob. Name: `MyCard-backup-YYYY-MM-DD.mycardbackup`.
- **Delivery.** `share_plus` if the Podfile.lock check is clear. Plugin-free paths, always available:
  - (a) **iOS:** write the file to the app's Documents folder and set `UIFileSharingEnabled` and `LSSupportsOpeningDocumentsInPlace` to true. Today both are `false` at `Info.plist:31-34`, and `Info.plist` has no uncommitted edits. The file then appears in Files › On My iPhone › MyCard. The vault itself stays in Application Support, which is not exposed.
  - (b) **Both platforms:** **Copy backup as text**, a base64 armour between `-----BEGIN MYCARD BACKUP-----` lines.
- **Restore (Settings › Restore).**
  - Pick from backups found in Documents (iOS), or **Paste backup text**, then enter the passphrase.
  - Wrong passphrase or tampered file → "That passphrase doesn't open this backup, or the file is damaged." Nothing is imported.
  - Merge by card id: same id → keep the newer `updatedAt`; new ids are added; incidents are merged by id.
  - Summary: "Restored 12 cards, 3 were already here (kept the newer copy)."
  - Restore follows the existing rule and is refused while the vault is damaged. The message points to Erase all data, then Restore, which becomes the honest recovery path for a damaged vault.
- **Status.** Settings shows "Last backup: 12 Oct 2026" or "Never backed up", from `lastBackupAt` in the envelope. When there are ≥ 5 cards and no backup, a one-line nudge appears on home, dismissible for 30 days.
- **Acceptance:**
  - Unit tests: round trip, wrong passphrase, one flipped byte, truncated file, header parse, merge rules, text armour round trip.
  - The exported bytes do not contain a seeded card number or title.
  - Iteration count read from the header is honoured.

**M6. Own identity: home layout, onboarding, palette, type, shape, icon, splash, iOS feel.**
- **Home layout, "Your wallet"** (replaces the search field + 10-chip filter bar + flat list scaffold). One scrolling page, top to bottom:
  1. **In your wallet**: the in-wallet cards drawn as **physical cards**. ISO/IEC 7810 ID-1 aspect ratio 85.60 × 53.98 (≈1.586:1), corner radius = 3.18/85.60 of the card width, in the user's chosen face colour. Kind and title, network label + •••• last 4, and a lock glyph if protected. Shown as an overlapping stack that fans out on tap.
  2. **Lost-wallet plan tile** (M3).
  3. **Coming up** (M4).
  4. **At home & everything else**: a compact list of cards that are not in the wallet.
  5. The single ad banner, inline at the end of the list (see below).

  App bar: title, Search, Lock now, Settings. The FAB "Add a card" stays.
- **Card face colours.** These replace the neon `KindPalette` (`theme.dart:72-76`). There are 8 named swatches, picked in the editor and stored in the existing unused `WalletCard.color` field. Defaults by M1 group:

  | Swatch | Hex |
  |---|---|
  | Cognac | `#8A4B1F` |
  | Oxblood | `#5E1F24` |
  | Ink | `#1F2A44` |
  | Forest | `#24402F` |
  | Slate | `#4A5560` |
  | Sand | `#C9B48A` (dark text) |
  | Plum | `#4B2A45` |
  | Graphite | `#2A2B2E` |

  Text on each face must reach ≥ 4.5:1, asserted in a test.
- **Palette "Cognac & brass".** A hand-built `ColorScheme`, not `fromSeed`; `ThemeMode.system`.
  - **Light:** surface `#E9EBEE`, cards `#FFFFFF`, text `#15191E`, **primary cognac `#8A4B1F`** (on-primary `#FFFFFF`), secondary brass `#B08D3C` (dark text; "in wallet" badges, stitch line), danger `#A4161A`, muted `#5A6068`.
  - **Dark:** surface graphite `#121314`, cards `#1C1D1F`, text `#ECE9E4`, primary `#D08A55` (on-primary `#121314`), brass `#D9B65E`, danger `#F07167`, muted `#A3A7AD`.
  - **Contrast, computed 2026-10-12 with the WCAG luminance formula.** Light: text/surface 14.78, on-primary/primary 6.76, primary/surface 5.66, danger/card 7.75, muted/surface 5.32. Dark: text/surface 15.36, on-primary/primary 6.60, primary/card 5.98, danger/card 5.83, muted/card 6.98. Assert all ≥ 4.5 in a test using `computeLuminance`.
  - **Uniqueness.** A `grep -rli` over `/Users/spatchava/agl` (`*.dart`, `*.md`) found none of these hexes in another app or spec.
  - **Acceptance:** `grep -rhoiE "10B981|F59E0B|EF4444|3B82F6|F8FAFC|E2E8F0|020617|0F172A|1E293B|334155|5B6CFF|8E5BFF|22D3EE|F472B6|00C9DA|2DD047|FF9F00|FB48CE|C240FF" mobile/lib` → 0, and `primaryGradient` is removed.
- **Typography.**
  - **Manrope** (variable, `wght`) for all UI. **Azeret Mono** (variable, `wght`) for card numbers, codes, expiry dates, lost-card phone numbers and reference numbers, with `FontFeature.tabularFigures()`. This replaces the `fontFamily: 'monospace'` at `sensitive_field.dart:104`.
  - Bundle under `assets/fonts/` with both `OFL.txt` files and declare them in `pubspec.yaml`. No `google_fonts`, no runtime fetch.
  - Sources verified 2026-10-12 with curl: `github.com/google/fonts/raw/main/ofl/manrope/Manrope[wght].ttf` 200 (164,700 B), `ofl/manrope/OFL.txt` 200 (4,387 B), `ofl/azeretmono/AzeretMono[wght].ttf` 200 (106,092 B), `ofl/azeretmono/OFL.txt` 200 (4,383 B).
  - No app under `/Users/spatchava/agl` and no spec in `specs/` uses either font: `grep -rli Manrope|Azeret` returned nothing.
- **Shape.**
  - Physical cards use the ID-1 proportional radius above.
  - Every other surface uses **4 px** corners: sheets, buttons, chips, fields. No 12/16/20 px pills.
  - "Stitch" motif: a 1 px brass dashed inset line drawn with `CustomPainter` on the plan tile and the onboarding cards.
  - Acceptance: `grep -rn "circular(12)\|circular(16)\|circular(20)\|radiusCard\|radiusLg" mobile/lib` → 0.
- **Onboarding** (3 pages, shown once, Skip on each, re-openable from Settings › "How MyCard works"):
  1. "Make a spare of your wallet". Take your wallet out and add each card; mark the ones you carry.
  2. "Write down who to call". The number on the back of each card powers the Lost-wallet plan.
  3. "Locked to you". Face ID / Touch ID / passcode, AES-256 on this phone, no account, no cloud; back up with a passphrase, because Erase is final.

  Final button: "Add a card from your wallet". No "Get started", "Welcome" or sign-in. Simple `CustomPainter` drawings, no stock art.
- **Lock screen.** Replace the gradient square, "MyCard" and tagline with the wallet mark on the surface colour, and "Locked. Your spare wallet opens with Face ID" (text adapts to capability, as now).
- **iOS feel.** On iOS: `CupertinoPageTransitionsBuilder` in `pageTransitionsTheme`, `CupertinoIcons` for app-bar actions, `.adaptive` switches and dialogs. Material stays on Android. Acceptance: `grep -c "CupertinoIcons" -r mobile/lib` ≥ 4, and a test asserts the iOS page-transition builder.
- **Icon.**
  - Hand-built art, flat with no gradient: a cognac wallet seen front-on, with a brass stitched edge and one card edge showing.
  - **Not from `generate_app_icons.py`.** Ask store-compliance to delete line 72 (`"MyCard": ("credit_card", ...)`) so a rerun cannot overwrite it; that file is in `agl-manifest`, not this repo.
  - Regenerate every `AppIcon.appiconset` size and the Android mipmaps.
- **Splash.** A new `LaunchScreen.storyboard` with background `#121314` and the mark; Android `launch_background.xml` uses the same; `LaunchImage` is replaced. Acceptance: shasum ≠ `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`.
- **Ads.**
  - Exactly one `AglAdBanner`, **inline at the end of the home scroll**, not in the `bottomNavigationBar` slot.
  - None on lock, onboarding, detail, editor, Show at counter, plan screens, backup/restore or Settings.
  - Acceptance: `grep -rn "AglAdBanner(" mobile/lib` → 1 hit. `ads_placement_test.dart` is updated to the new placement, not deleted, and adds a test that the plan screen and Show at counter have none.
- **Names.** `CFBundleDisplayName` (`Info.plist:10`), `android:label` (`AndroidManifest.xml:18`), `MaterialApp.title` and the pubspec description come from one `kAppName` constant. They stay "MyCard" until the founder answers Q1. A test reads `Info.plist` and asserts the display name equals `kAppName`.

**M7. Settings and copy that belong to this app.**

Settings, in this order:
- **Unlock & encryption**: the existing rows, kept verbatim where accurate.
- **Backup**: Back up, Restore, last-backup status.
- **Lost-wallet plans**.
- **What leaves this device**: existing `dataLeavingDeviceText`, kept.
- **Privacy choices**: the UMP row is kept as is; it is legally required.
- **How MyCard works**.
- **Your wallet**: counts by M1 group, replacing the CardCategory list.
- **Erase all data**: kept, and the copy adds "Backups you exported are not affected".
- **About**: "MyCard · American Group LLC".

No Language screen is added (the app is honestly English-only, `app.dart:9`). No generic "Get started", "Nothing saved yet" or "Your data" copy.

**M8. Proven.**
- `flutter analyze` is clean and `flutter test` passes, with the count reported against the baseline of 246.
- **New tests:** everything listed under M1–M7 acceptance, plus:
  - an identity test: fonts declared in `pubspec.yaml` and present on disk, no `google_fonts`, palette and face-colour contrast, storyboard shasum, display name;
  - a source-grep test for the M1 banned strings and the M6 banned hexes and radii.
- **Tests that change:**
  - `ads_placement_test.dart` (new placement);
  - `card_tile_test.dart` (tile becomes the physical-card face plus the compact row);
  - `foldable_layout_test.dart` and `responsive_layout_test.dart` (**rewritten** for the new home, plan screen and Show at counter at the same sizes they test now: 320×360, 730×320 at 3.0× text, 840×400 with keyboard);
  - `card_kind_test.dart` (picker groups);
  - `card_vault_test.dart` (v2 envelope plus v1 read).

  No test is deleted or skipped to go green. Any test removed together with the code it covers (for example the reminder sort rule) is named in the commit message.
- **Look at it.** Launch on the iOS simulator with a fresh install and screenshot:
  - onboarding page 1;
  - empty home;
  - home with 4 cards added by hand through the UI (use the public test numbers from §3 and your own made-up loyalty values; this is the developer's local test data, not shipped);
  - Show at counter for a Code 128 card;
  - the plan screen mid-flow;
  - the report text;
  - Backup;
  - dark mode.

  No white screen and no overflow.
- **Commit and push.** Commit path-limited (never `fastlane/`, and never `Podfile.lock` while it carries the other edit) and push to `main`. `store_screenshots_test.dart` in `integration_test/` must be updated to drive the new flow, or the commit must state that it was not.

### SHOULD (if time allows, in this order)

- **S1. Scan a barcode** into a loyalty, library or membership card with the camera (`mobile_scanner`, plus `NSCameraUsageDescription` "Scan the barcode on a loyalty or library card"). Same Podfile.lock rule; typed entry stays.
- **S2. Expiry notifications.** On-device local notifications (`flutter_local_notifications`) 30 days and 7 days before an expiry. Off until the user turns it on per card. Same Podfile.lock rule. Only once this ships may any copy say "reminds you".
- **S3. Replacement follow-through.** When a plan item is "Replacement ordered" and the user later changes that card's number, record "Replaced 14 Oct (was •••• 1111)" on the card and tick the item.
- **S4. Max brightness on Show at counter** (`screen_brightness`), restored on exit. Same Podfile.lock rule.

## 5. Store impact (proposed; store-compliance applies it later. Nothing was written to `store/` or `fastlane/`)

**Name.** Founder decision (Q1). "iMyCard" stacks the portfolio's "i" and "My" prefixes and sits next to Blackhawk's "MyCardWallet." (96,473 ratings). Candidates:
- "Spare Wallet: Lost Card Plan"
- "Wallet Twin"
- keep "MyCard" on Play.

An iTunes Search for "Spare Wallet" and "Wallet Twin" returned no app with those names in the top 5 (2026-10-12), but **App Store Connect name availability is not checked**. The bundle id is permanent either way.

**Category.** Primary `UTILITIES`, secondary `PRODUCTIVITY`, unchanged. Founder may prefer `FINANCE` (Texode, highglossy and the 1Password-style wallets list there), but Finance invites MyFinance overlap questions. Keep Utilities.

**Subtitle (≤30):** `Spare wallet + lost-card plan` (29)

**Play short description (≤80):** `Your wallet's cards, IDs and barcodes, encrypted, plus a plan if it's stolen.` (78)

**Promotional text (≤170):** `Lost your wallet? MyCard lists every card you carried, in the order to call, with the numbers you saved — and writes the report for the police or your bank.` (157)

**Description.** Draft. It drops the ALL-CAPS skeleton, the opening "<AppName> is…" line and the "37 card types" boast:
> Take your wallet out and put a spare of it on your phone: payment cards, driver's licence, insurance card, loyalty and library cards, transit and access cards. Mark the ones you carry and add the "if lost, call" number from the back of each.
>
> If your wallet is ever lost or stolen, tap "My wallet is lost or stolen". MyCard lists every card that was in it, payment cards first, with the number you saved for each. Tick off who you've called, what you've frozen or cancelled, and the reference numbers they gave you. When you're done, share a report of what was lost and what you did — last four digits only — with the police, your insurer or your bank.
>
> Day to day: show a loyalty, library or ticket barcode at the counter, copy a card number when you need it, and see what expires soon — including a warning when your passport gets inside six months.
>
> Everything is encrypted on your phone with AES-256 and opens with Face ID, Touch ID or your passcode. There is no account and no cloud copy. Back up the whole wallet into a file sealed with a passphrase only you know, and restore it on a new phone.
>
> MyCard is free with one Google AdMob banner at the bottom of the home screen; never on a card, the lost-wallet plan or Settings. Where the law requires it, you choose about ad personalisation first and can change it in Settings. Crash reports never contain card data.

**Keywords:** `lost wallet,stolen wallet,cancel cards,card vault,loyalty barcode,id wallet,passport expiry,encrypted,offline,backup`

**Screenshots to retake** (fixes 2.3.3). **Never the lock screen or the OS unlock prompt.** All captured from the real app with cards typed in through the UI at capture time: test card numbers and fictitious loyalty values, labelled as such nowhere in the UI because nothing is fake in the app itself. iPhone 6.9", iPad 13", Play phone/tablet:
1. The Lost-wallet plan mid-flow (3 of 6 handled, one reference number).
2. Home: physical-card stack, plan readiness, Coming up.
3. Show at counter with a Code 128 loyalty card.
4. The shared lost-wallet report text.
5. Backup with passphrase (fields empty).

The current fastlane screenshots carry someone else's uncommitted edits. Coordinate with their owner; do not overwrite them from this workstream.

**Play feature graphic.** Rebuild it from the new icon and a Manrope wordmark on `#121314`, replacing the old "MC" monogram.

**Review notes** (rewrite for this app only; drop the "2. DEVICES…" skeleton and the simulator / "a build that cannot start never ships" paragraph):
- **What it is and for whom:** "MyCard keeps an encrypted spare of the cards in your physical wallet and guides you through cancelling them if the wallet is lost or stolen. For adults who carry payment cards, a licence and an insurance card and want to be ready." This replaces the pasted subtitle.
- **Path, no login:** "Launch → Face ID (or passcode; the wallet opens without a prompt on a device with no screen lock) → onboarding → Add a card → Credit Card, number 4111 1111 1111 1111 (a public test number), If lost, call: any number → Save. On home, tap 'My wallet is lost or stolen' → Start plan → mark the card Cancelled → Share/Copy report. Add a Loyalty Card with barcode value 123456789012 → Show at counter."
- **Nothing hidden:** "The app has no hidden, remote-switched or region-dependent features. Every feature is on the home screen or in Settings."
- **External services, correcting the 2026-09-29 reply** (which said none; ads were added on 2026-10-12): Google AdMob (one banner, UMP consent, no ATT prompt) and Firebase Crashlytics (crash reports, no card data). Firebase Analytics and Performance are linked through a shared library but deactivated (`Info.plist` keys) and never started. No server of our own; card data never leaves the device except in a backup file the user exports themselves.
- **Test devices:** state only what was actually used. A physical-device run is a human step and is **not verified** here.
- **Language:** English only (`supportedLocales: [en]`). The current notes say "follows the device language for 12 locales", which contradicts `app.dart:9`; fix it.

**Privacy label.** Give MyCard **its own** label instead of the shared 20-app one: `DEVICE_ID` and `ADVERTISING_DATA` (third-party advertising, not linked) and `CRASH_DATA` (app functionality, not linked). **Remove `PRODUCT_INTERACTION/ANALYTICS` and `PERFORMANCE_DATA`.** Both are deactivated in the binary (`Info.plist:290-293`, `AndroidManifest.xml:66-67` for performance) and `AglInsights.init` is not called (`main.dart`). Store-compliance must confirm the Android Analytics deactivation key too: I found only the performance key in `AndroidManifest.xml` with my grep, so **Android analytics deactivation is not verified**. Exported backups are user-initiated files and are not collection. If S1 ships, camera frames stay on the device.

**differentiation (store json):**
- §1: rewrite to the new screens.
- §3: use §2's table and its "descriptions only" caveat. The gap is the Lost-wallet plan and report, not encryption.
- §6: "Not a feature of MyFinance (no balances or transactions) or MyHealth (stores no cards)."
- §4 beta and §9 client stay founder items.

## 6. Out of scope

- Payments, NFC/tap-to-pay, Apple Wallet pass (`.pkpass`) creation (needs a signing certificate; a founder and credentials decision), and reading NFC tags.
- Any issuer phone-number directory, bank lookup or BIN API. It would send card prefixes off the device, against the app's core promise, and no verified keyless source exists. Users type the number from their card.
- Cloud sync, accounts, Supabase, sharing cards with other people.
- Balances, transactions, budgets (MyFinance).
- OCR of card faces (S1 scans barcodes only).
- Translations beyond English.
- Contacting banks or the police on the user's behalf.

## 7. Not verified

- Competitor behaviour beyond their App Store descriptions; WebSearch was unavailable in this session. Apple Wallet was not checked.
- PBKDF2 at 600,000 iterations in pure-Dart pointycastle on a real device: speed is not measured. M5 sets the measurement rule.
- That iOS Files shows the Documents folder once the two `Info.plist` keys are flipped. This is standard iOS behaviour, but it was not run here.
- Android Firebase Analytics deactivation (see Privacy label).
- App Store Connect availability of any Q1 name.
- Physical-device behaviour, and whether Apple accepts a resubmission.

## 8. Founder questions (Charter decisions; the office does not take them)

- **Q1. Name.** Keep "iMyCard" or rename? Candidates are in §5; availability is not checked. Renaming changes the home-screen name, store listing and screenshots together.
- **Q2. Is this distinct enough to keep?** Encrypted card vaults are crowded (Texode, highglossy, Holder, 1Password, Bitwarden). This spec bets on the Lost-wallet plan plus counter barcodes, expiry radar and passphrase backup. If you judge that not enough under 4.3, the alternative is retiring or merging MyCard (Charter §8).
- **Q3. Ads in a security app.** One home-screen banner stays (money, Charter §3). Option: remove ads from MyCard entirely, which also simplifies the privacy label to crash data only.
- **Q4. Resubmission and reply.** Replying to Apple (including correcting the 09-29 "calls no external service" statement) and resubmitting stay frozen under the 5.6 hold (MA-043, Charter §1).
- **Q5. Beta testing statement.** differentiation §4 needs a true account (TestFlight shows 1 install, 0 feedback). Only you can give it.
