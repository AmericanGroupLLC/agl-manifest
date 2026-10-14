# Spec v2: Uscis-Case — live USCIS status, alerts, I-94, FOIA and Adjustment of Status

Author: product-manager, with technical-architect, store-compliance and privacy-engineer (AI office), 2026-10-14
Founder request (2026-10-14): "make Uscis-Case the best USCIS app". Use the official USCIS developer APIs. Add I-94 and CBP, Adjustment of Status (I-485), FOIA requests and their status, email to support, information and notifications, and the fields the leading apps offer.
Project: real-apps (`../plan.md`, criteria 1–7; GitHub issue #24).
Repo: `/Users/spatchava/agl/Uscis-Case` (Flutter at the repo root). Backend: `/Users/spatchava/agl/AmericanGroupLLC-Backend` (Supabase project `smvvjivvlprjhzhoizym`).

**This spec contains no app code.** Another agent is building v1 (`Uscis-Case.md`) in the same repo right now. When I read the repo on 2026-10-14, `git status` showed 15 modified `lib/` files and new untracked `lib/domain/`, `lib/content/`, `lib/utils/receipt.dart`, `lib/services/federal_register_client.dart` and others. `HEAD` was still `c4b30ab` (2026-10-12).

**Order of work.**
- v2 app work starts after v1's M1–M9 have landed and passed QA. v2 builds on v1's case fields (M2), its window engine (M3), the Docket (M7) and the encrypted-storage gap that v1 leaves open.
- The backend items (B-items in M8, M10) live in a different repo, so they can start now. They still need the founder actions in §10 before anything reaches production.

**What v2 overturns in v1.** v1 §3 and §6 say live status is not possible ("needs registered credentials we do not have"), and that push and accounts are out of scope. That is no longer true:
- The founder's developer.uscis.gov team has an **approved** app with two sandbox products enabled, "Case Status API - Sandbox" and "first-case-sbox" (founder message relayed 2026-10-14).
- v2 adds live status, server-side alerts and an **anonymous** server identity. It still has no sign-in.
- Everything else in v1 stands.

---

## 0. Evidence base and how to read the markers

- **The developer.uscis.gov pages were fetched with curl on 2026-10-14 and returned HTTP 200.** WebSearch/WebFetch are off in this session, but plain curl through the machine's proxy worked. Every API fact marked **[fetched]** is quoted from one of these:
  - `/apis` (catalogue)
  - `/api/case-status` and its OpenAPI file `/sites/default/files/apidoc_specs/swagger_3.yaml` ("Case Status API", version 1.0.0, 276 lines)
  - `/api/foia-request-and-status` and its OpenAPI file `/sites/default/files/apidoc_specs/swagger_1.yaml` ("FOIA Request and Status API", version 1.2.0)
  - `/faqs`
  - `/get-started/{introduction,sign-up,sandbox,production-access,go-live}`
  - `/get-started/production-access/{request,affidavit,demo-id,demo}`
  - `/article/how-get-access-tokens-client-credentials`
  - `/article/api-key-management-policy`
- **VERIFY-n** marks anything I could not confirm: "verify against developer.uscis.gov docs (web access is off)", or against the named source. §12 lists them all.
- **Not fetched:** the USCIS Terms of Use. The FAQ links to `https://myaccount.uscis.gov/legal-terms#tos-tos`, which returned HTTP 403 to curl.
- **No credential was used.** I made no call to `api-int.uscis.gov`. Every response shape below comes from the published OpenAPI files, not from a live response.
- **Founder identity rule.** This document does not contain, and the build must never commit, the founder's portal username, team name or any key value. Credentials are referred to only by the secret names `USCIS_CLIENT_ID` and `USCIS_CLIENT_SECRET`.

## 1. Problem, user, positioning

**User:** the same as v1, a family in the US with several USCIS filings over several years. v2 adds the adjustment-of-status (I-485) applicant: someone in the US on a visa or I-94, waiting on an I-485 with its companion I-765 (work permit) and I-131 (advance parole), whose admit-until date and EAD/AP expiry matter while the case is pending.

**The gap v1 left.** v1 is a family case file with windows, but the user still copies statuses by hand. As the store measures it, every leader fetches status. iTunes Search API, re-run 2026-10-14 (`term=uscis case status`; descriptions only, apps not run):

| App | Ratings | Last update | What its description claims (relevant parts) |
|---|---|---|---|
| Case Tracker for USCIS & NVC (Immivision, id921827126) | 318,475 | 2026-10-05 | status-change notifications; NVC; Visa Bulletin; "Search a range of cases" |
| MigraConnect Case Tracker (id6596770726) | 194,604 | 2026-09-27 | USCIS cases, Immigration Court hearings, Asylum Clock and **FOIA requests**; alerts; full case history |
| Lawfully Case Tracker (id1435063223) | 173,528 | 2026-10-04 | USCIS, NVC, DOL and EOIR (by A-Number); processing times; visa bulletin; family; Spanish; lawyer consultations (paid) |
| Case Status (Case Status, Inc, id1268078389) | 45,242 | 2026-10-09 | a law-firm client portal ("communicate with your team, submit documents") |
| Case Tracker for USCIS Status (Kevin Horvath, id1585545181) | 21,695 | 2023-09-21 | "NOT an official USCIS application" |

**v2 positioning, as an honest and checkable claim:** live status from USCIS's own Case Status API, kept in a family case file that also knows the filing windows (v1). On top of that:
- I-94 admit-until reminders;
- an I-485 timeline built from the user's receipts;
- FOIA tracking;
- Spanish status text straight from USCIS (the API returns `current_case_status_text_es` **[fetched]**);
- no sign-in.

**Claims we must not make:**
- "the only app that uses the official API". Unverified: competitors may hold the same access ("connects to the official USCIS public system", says id6753734232).
- "first with FOIA". MigraConnect already claims FOIA tracking.
- anything that implies USCIS endorses the app.

## 2. What the official APIs offer (fetched 2026-10-14)

### 2.1 Catalogue
`/apis` lists exactly two products:
- **Case Status API**: "Provides case status information to USCIS customers and their representatives who require regular access to case status information."
- **FOIA Request and Status API**: "allows consumers to create a Freedom of Information Act (FOIA) or Privacy Act (PA) request, for Alien File material, about or on behalf of the subject of record. You can check the status of the FOIA/PA Alien File Request by using the Request Number returned from the newly created case."

There is **no** processing-times, visa-bulletin, NVC or I-94 API in the catalogue.

**"first-case-sbox" is the FOIA sandbox.** I checked this, so it is no longer a guess. The FOIA OpenAPI `servers:` entry is `https://api-int.uscis.gov/first-case-sbox/`, and the token-endpoint example response in the access-token article lists `"api_product_list_json": ["Case Status API - Sandbox", "first-case-sbox"]` **[fetched]**. That matches the two products the founder sees enabled.

What is still open is whether the founder's app may call FOIA **create**, **status** or both: the spec declares `security: api_oauth: [write, read]` (**VERIFY-1**).

### 2.2 Case Status API [fetched unless marked]
- **Sandbox base:** `https://api-int.uscis.gov/case-status`. Call: `GET /{receiptNumber}` with `Authorization: Bearer <token>`. Operation id `callWebServiceForCrisWebData`.
- **OAuth2 client credentials.** `POST https://api-int.uscis.gov/oauth/accesstoken`, `Content-Type: application/x-www-form-urlencoded`, body `grant_type=client_credentials&client_id=…&client_secret=…`.
  - The response carries `access_token`, `token_type: "Bearer"`, `expires_in: "1799"` (a **string**), `issued_at` (epoch ms, as a string), `api_product_list_json` and `status: "approved"`.
  - "OAuth Access Tokens Expire every 30 mins". There is no refresh token (`refresh_token_expires_in: "0"`).
- **Production URLs are not published.**
  - The production token URL is "Available when you Pass your Demo".
  - The go-live page says an official letter gives "Production Keys, API Production Endpoints, Production OAuth 2.0 Access Token URL", and that "A new Developer App will be created containing your Production Client Credentials".
  - So production uses a **different** client ID and secret from sandbox.
- **Client-side calls are prohibited.**
  - Demo criteria: "All keys, secrets, and tokens used to access our APIs must be securely stored within your infrastructure. Request originating from any client applications are prohibited."
  - Token article: "We will require use of a back end mediator that routes request through a secure backend service that your company/organization controls … Never store your Client Credentials in a front-end application … (e.g. web applications or mobile apps)."
- **Receipt format.** "13-character identifier that consists of three letters and 10 numbers. Omit dashes." The documented regexes are `[a-zA-Z]{3}[0-9]{10}` **and** `[a-zA-Z]{3}\*[0-9]{9}`. The asterisk form's meaning is not documented (**VERIFY-2**). The current app's `receiptRegex` (`lib/utils/receipt.dart:3`, `^[A-Z]{3}\d{10}$`) rejects it.
- **Success schema** (`case_status`):
  - `receiptNumber`, `formType` (e.g. "I-130");
  - `submittedDate` and `modifiedDate`, as "09-05-2023 14:28:46" (MM-dd-yyyy, time zone not stated, **VERIFY-3**);
  - `current_case_status_text_en|es` and `current_case_status_desc_en|es`;
  - `hist_case_status[] {date "2023-09-05", completed_text_en, completed_text_es}`, which may be `null` (the access-token article's example shows `"hist_case_status" : null`);
  - plus a top-level `message`, which **echoes the receipt number** ("Query was successful for payload {'receipt_number': …}").
  - `desc_en` contains **HTML anchors** (the example includes `<a href="https://www.uscis.gov/addresschange" target="_blank">`).
- **IOE receipts** use a variant without `submittedDate` and `modifiedDate`.
- **`modifiedDate` caveat:** "Internal or administrative updates that do not impact the outcome of a case may also cause a `modifiedDate` update." So `modifiedDate` alone must not trigger an alert.
- **Errors documented in the OpenAPI:**
  - 401: "Invalid Access Token" (keys not enabled, or token wrong or expired).
  - 404: "Case Status Online does not recognize the receipt number entered…". **Also returned for individuals protected under 8 U.S.C. 1367**, who must be pointed to the USCIS Contact Center.
  - 422: not 13 characters, or an invalid prefix.
  - 429: "Spike Arrest Violation".
  - 503: the **sandbox** is unavailable outside "M-F 7:00AM EST - 8:00 PM EST".
- **Two error formats:**
  - the OpenAPI shows `{code, message}` / `{message}`;
  - the sandbox page says errors follow RFC 9457, as `{"errors":[{"code","message","category","reference","status","traceId"}]}`.
  - The function must parse both. The demo requires that "The error.message must be displayed on the front or back end of your application".
- **Quotas:**
  - Sandbox: 1,000 requests a day and 5 TPS for Case Status; 3,500 a day and 5 TPS for FOIA (sandbox page).
  - Production: the Case Status OpenAPI description says "Daily Quota is limited to 400,000 request and resets everyday at -04:00 UTC (Midnight EST)" and "Concurrency limit is set to 10 Transactions Per Second". The sandbox page says "Production Daily Quota and Throughput will be shared when production access is granted". Treat both figures as **VERIFY-4** until the go-live letter.
- **Sandbox test receipts.** 25 staging receipts **with** history (e.g. `EAC9999103403`, `LIN9999106498`, `SRC9999102777`) and 25 **without** (e.g. `EAC9999103400`, `SRC9999132694`). The full lists are in `swagger_3.yaml`.
  - **Production rejects them:** "Staging Receipt Numbers are not supported".
- **Cost:** the pages I fetched mention no price (**VERIFY-5**).

### 2.3 FOIA Request and Status API [fetched]
- **Sandbox base:** `https://api-int.uscis.gov/first-case-sbox/`, with the same token URL.
- **`POST /case`** ("Create a FOIA case on behalf of someone else.").
  - The payload includes `alienNumber(s)`, `subject` (domestic or international), `family` (mother and father **required**), `aliases`, `requester`, `receiptNumbers[]`, `representiveRoleToSubjectOfRecord` (`ATTORNEY` | `OTHERFAMILY`), `digitalDelivery` (`MY_ACCOUNT` | `LEGACY`), `preferredConsentMethod` (`NOTARIZED` | `EMAIL` | `SMS`), `courtProceedings`, `recordsRequested[]` and `documents[]`.
  - Documents are base64 PDF/JPG, at most 25 pages or 10 MB.
  - It returns `requestNumber` (e.g. `NRC123456789REQ`).
  - A 400 means the requester email has no USCIS account ("Enter valid MyAccount email…").
- **`GET /case-status?caseControlNumber=…`** or **`?requestNumber=…`** (examples `NRC2022000001`, `NRC2022000001REQ`).
  - It returns `caseControlNumber`, `requestNumber`, `queueLength`, `placeInQueue`, `requestReceivedTimestamp`, `estCompletionDate`, `requestDescription`, `topic`, `publicStatusCode.display` and `status{code, display, description}`.
- **Status codes**, each documented with a "Fetch Status" Yes/No: `CONSENT_REQUIRED` (Yes), `REQUEST_CANCELED_SUBJECT_DENIED` (No), `REQUEST_CANCELED_SUBJECT_SUGGESTED_CHANGES` (No), `REQUEST_CANCELED_EXPIRED` (No), `SUBMITTED` (Yes), `USCIS_REVIEWING` (Yes), `RESPONSE_ISSUED` (No). "Third-party software developers can choose to check the FOIA case status API as often as daily".
- **Required in-app text.** USCIS gives four text blocks that an app using the FOIA API **must** show: #1 a general message at the start, #2 email-address guidance, #3 required documents, #4 status and action text. Production access requires "Have successfully included the required text in your application".
- **Delivery and portal.** Since 2026-01-22, uscis.gov says "all Freedom of Information Act (FOIA)/Privacy requests for USCIS records should be submitted online … at first.uscis.gov". Source: `uscis.gov/records/request-records-through-the-freedom-of-information-act-or-privacy-act`, HTTP 200.
- **Open question:** can the status endpoint look up a control number that the user filed **directly on first.uscis.gov**, rather than through our app (**VERIFY-6**)?

### 2.4 Production access process [fetched]
1. **Prerequisites:**
   - a developer account;
   - a Developer App for the sandbox product;
   - "Minimum of 5 consecutive calendar days of API traffic";
   - "Success and Error Responses; 200 and 4xx HTTPS responses tested";
   - for FOIA, also the required text.
2. **Request.** Email `developersupport@uscis.dhs.gov`. USCIS replies with a **Developer Portal Affidavit**:
   - the primary contact must be "an authorized signatory who can legally bind your company";
   - the company must be US-incorporated ("software development organizations incorporated within the United States", FAQ);
   - a business website, privacy policy and terms of service;
   - agreement to the Terms of Use.
   - USCIS checks the website and policies for readability (14 px or larger, WCAG contrast 4.5:1, grade level 12 or below) and for a long list of privacy-policy contents (§8.4).
3. **Demo ID.** A 4-digit `demo_id` request header, confirmed by screenshot or code snippet.
4. **Demo.**
   - Slots are Wednesdays and Thursdays, 1–2 PM EST: Case Status takes 30 min, FOIA 60 min.
   - It is an end-to-end live demo of "ALL documented response codes" using "your staging environment, ensuring that all PII is removed", and is rated Pass/Fail.
   - Results come within 2 business days; re-demos are 15-minute office hours.
5. **Go live.** An official USCIS letter gives the production keys, endpoints and token URL.
- **Key policy:**
  - keys must be rotated every 365 days, with a 14-day grace period in which both keys work;
  - "Consumers who do not send traffic during the previous 365-day period will not receive new keys";
  - keys are "immediately revoked if compromise is suspected or upon user request";
  - sharing keys by email or chat breaks the policy ("Avoid sharing API keys in public repositories, email or other communication channels").
- **The keys must be rotated now.** The founder says two keys were issued on 2026-07-01 and were then exposed in chat. They must be **rotated before first use** (§10 F1).

### 2.5 I-94 / CBP [fetched]
- There is no CBP API in the USCIS catalogue, and none is used.
- `https://i94.cbp.dhs.gov/` is a single-page app (title "I94 - Official Website"). It returns the same shell (md5 `a90975f4…`) for **any** path, including a made-up one, so an HTTP 200 proves nothing about a route.
- The route names come from the site's own `main-BUT3MNCZ.js` (fetched 2026-10-14), via its `routerLink`s:
  - `/search/recent-search` ("Get most recent I-94/I-95");
  - `/search/history-search` ("view travel history");
  - `/search/compliance-search` ("view compliance");
  - `/payment/document-apply` ("Apply for new I-94");
  - `/home`, `/help`.
- These are link targets only. The app never reads, submits or parses anything from this site.
- **CBP One:** `https://www.cbp.gov/about/mobile-apps-directory/cbpone` redirected (HTTP 200) to `…/mobile-apps-directory/cbplink`. The app links to the **final** URL and names it the way that page does (**VERIFY-7**: the current name, CBP One or CBP Link).

### 2.6 Adjustment of status [fetched]
`uscis.gov/green-card/green-card-processes-and-procedures/adjustment-of-status` (HTTP 200, "Last Reviewed/Updated: 07/24/2026") lists nine steps:
1. determine eligibility;
2. an immigrant petition is filed (I-130 / I-140 / I-730 / I-589 …), with "concurrent filing" possible;
3. check visa availability;
4. file Form I-485;
5. the Application Support Center (biometrics) appointment ("we will mail you a notice … date, time, and location");
6. the interview, if applicable;
7. respond to any request for evidence: "The request will also tell you … the date by when you must respond";
8. check case status (the USCIS Contact Center is 800-375-5283, TTY 800-767-1833);
9. receive a decision.

It also says: "If you change your address, you must tell us within 10 days of moving."

`uscis.gov/i-485` (HTTP 200) says:
- the current edition is **09/18/26**, with "no grace period";
- the filing location changed on Oct. 7, 2026;
- "When you file Form I-485, you must also submit Form I-693".

The app links to these pages. It does not restate edition or filing-address rules, which change.

## 3. Architecture decision record (technical-architect)

**Context.** USCIS forbids client-side calls and client-held secrets (§2.2). The app has no accounts, and v1 removes the sign-in wall. Push needs a server that remembers which device tracks which receipt.

**Options considered.**
- (a) The app calls USCIS directly. **Rejected:** USCIS prohibits it.
- (b) An Edge Function with the Supabase anon key only, rate-limited by IP. Rejected as the primary design: there is no stable identity for alert subscriptions or for deletion, and the shared anon key makes abuse cheap.
- (c) **Chosen:** an Edge Function behind **Supabase anonymous sign-in**. Each install gets an anonymous JWT, created lazily the first time the user asks for a live lookup, never at launch. Every server row hangs off `auth.uid()` with `ON DELETE CASCADE`.
  - **Dependency:** anonymous sign-ins must be enabled on the project. MA-040 (`docs/MANUAL_ACTIONS.md:1836`) recorded `"Anonymous sign-ins are disabled"`, and `supabase/config.toml` says `enable_anonymous_sign_ins = true`, but config.toml is local config and must never be pushed.
  - I did **not** test the current production state, because the test would create a production auth user (**VERIFY-8**).
  - If the toggle stays off, fall back to (b) for lookups only, and leave alerts (M10) blocked.
- (d) SHOULD S5: Apple App Attest / Play Integrity on function calls, as abuse protection on top of (c).

**Consequences.**
- v1 founder question Q2 ("remove Supabase entirely if no legacy accounts") is **constrained by v2**: the app keeps a Supabase client, or a minimal HTTP auth client, for anonymous auth and function calls.
- The anonymous session must be stored in the encrypted store from M2, not in plain `shared_preferences`. That means a custom `LocalStorage` for `supabase_flutter`.
- No new host appears in the app except `smvvjivvlprjhzhoizym.supabase.co`, which is already in `docs/api-hosts.json`. `api-int.uscis.gov` and the production host are contacted only by the server.

**Files a build will touch** (named here, not written):
- Backend:
  - `supabase/functions/uscis-case-status/index.ts`: app-facing; routes `lookup`, `track`, `untrack`, `device`, `forget`.
  - `supabase/functions/uscis-refresh/index.ts`: cron only.
  - `supabase/functions/_shared/uscis.ts`: token cache, client, error normalisation, encryption.
  - Deno tests next to each.
  - `supabase/migrations/2026MMDD_uscis_case.sql`.
  - A new deploy step for functions. `.github/workflows/deploy.yml` deploys **migrations only** today (read 2026-10-14), and `supabase/functions/` does not exist yet.
- App:
  - `lib/services/uscis_backend.dart` (function client);
  - `lib/domain/receipt_info.dart` (prefix decode);
  - `lib/domain/uscis_status.dart` (parser and stage mapper);
  - `lib/domain/aos_timeline.dart`;
  - `lib/domain/i94.dart`;
  - `lib/domain/foia.dart`;
  - `lib/services/secure_store.dart`;
  - `lib/services/reminders.dart`;
  - `lib/services/push.dart`;
  - screens under `lib/screens/` for I-94, AOS, FOIA and Help;
  - `ios/Runner/Runner.entitlements` (`aps-environment`);
  - Android manifest (`POST_NOTIFICATIONS`).
- **Podfile.lock trap (v1 header).** `firebase_messaging`, `flutter_local_notifications` and `flutter_secure_storage` all add pods. Do not commit `ios/Podfile.lock` while another owner's uncommitted `COCOAPODS: 1.17.0` edit is still there; report it instead.

## 4. Acceptance criteria — MUST

The order is deliberate. **M1–M7 need no USCIS credentials** and can be built and tested now, once v1 has landed. M8–M10 need the rotated sandbox keys in Supabase secrets. M11–M12 lead to production.

### M1. Receipt intelligence and the status parser (no credentials)
- **Validation.** `normalizeReceipt` strips spaces and dashes and upper-cases. It accepts both documented forms: `^[A-Z]{3}[0-9]{10}$` and `^[A-Z]{3}\*[0-9]{9}$`. The second form is accepted and sent through unchanged, URL-encoded (VERIFY-2). The error is inline, as "3 letters and 10 digits, as printed on your I-797". Nothing invalid is ever sent to the server.
- **Prefix decoding** (`receipt_info.dart`, pure Dart). Map the prefix to an office name: EAC → Vermont Service Center; WAC → California Service Center; LIN → Nebraska Service Center; SRC → Texas Service Center; NBC → National Benefits Center; MSC → National Benefits Center (formerly Missouri Service Center); IOE → USCIS online/ELIS (electronic); YSC → Potomac Service Center.
  - **This table is from general knowledge, not a fetched page (VERIFY-9).** It must be checked against a uscis.gov page, and that page's URL stored next to the table, before it ships.
  - Unknown prefixes (field-office codes and others) show "Office code XXX", with no invented name.
  - The UI labels it "Based on the receipt prefix".
  - Nothing is decoded from the digits. The year and workday reading that some apps show is a community convention, not a USCIS rule, and is out of scope.
- **Parser** (`uscis_status.dart`). It turns the function's normalised JSON (M8) into `CaseSnapshot {receipt, formType, statusEn, statusEs, descEn, descEs, submittedAt?, modifiedAt?, history[], fetchedAt, source:'uscis-api'}`.
  - It handles `hist_case_status: null`, the IOE variant without dates, and both error formats.
  - `desc_*` HTML is turned into plain text plus tappable links, and **only** `https://*.uscis.gov` and `https://*.dhs.gov` links are kept. No WebView and no HTML renderer.
- **Stage mapper.** Maps known status titles to stages: Received, Biometrics, Interview, RFE, Decision-approved, Decision-denied, Card, Other.
  - Seeds: the 12 wordings already in `lib/widgets/case_status_tools.dart`, plus the titles in the OpenAPI examples ("Case Was Approved", "Case Approval Was Affirmed").
  - Anything unmapped → "Other update". **The app never guesses a stage.**
- **Acceptance:**
  - unit tests on fixtures copied **verbatim** from `swagger_3.yaml` and the access-token article (both success variants, null history, and the 401, 404, 422, 429 and 503 examples, in both error formats);
  - an HTML-anchor test (only uscis.gov/dhs.gov links survive);
  - validation tests for both regexes;
  - a prefix-table test.
  - Fixtures recorded from the sandbox replace the copied ones in M9.

### M2. Encrypted on-device store and privacy mask (no credentials)
- **Sensitive values move to an encrypted store:** receipts, status snapshots, A-numbers, I-94 fields, passport expiry, FOIA numbers, AOS checklist, notes, people's names and the Supabase session.
  - A random 256-bit key lives in Keychain/Keystore through `flutter_secure_storage`. On iOS it uses `first_unlock` accessibility, **not** `this_device`, so encrypted device backups restore it. The trade-off is documented in code.
  - The data is a single AES-GCM blob in the app's documents directory, written with a pure-Dart crypto package. The package version and its Keystore behaviour are VERIFY-10.
- **Migration.** On first launch after the update, existing `shared_preferences` keys move into the encrypted store and the plaintext keys are deleted. The migration is idempotent, and if it fails it keeps the old data and retries; data is never lost.
- **Privacy mask.** A Settings toggle (default off) shows receipts and A-numbers as `EAC •••• ••• 3403` throughout the app and in exports. It serves screen sharing and the store screenshots (§9).
- **Acceptance:**
  - a migration test with v1-format prefs: values are readable afterwards, and `shared_preferences` no longer holds them;
  - a corrupt-blob test that shows an error state, not a crash, and keeps the encrypted file for retry;
  - mask-on golden strings;
  - `grep -rn "SharedPreferences" lib` hits only non-sensitive settings (theme, locale, onboarding-seen), each listed in the commit.

### M3. I-94 and CBP (no credentials)
- **"My I-94" per person.** Manual entry of: I-94 record number (11 characters; format VERIFY-11), most recent date of entry, class of admission (free text with common chips: B-2, F-1, H-1B, L-1, J-1, K-1, …), admit-until date **or** "D/S" (duration of status), and an optional note.
  - The field labels follow the CBP printout ("Admission (I-94) Record Number", "Most Recent Date of Entry", "Class of Admission", "Admit Until Date"). These labels are from knowledge (VERIFY-11).
- **Links, opened in the system browser:**
  - "Get my most recent I-94" → `https://i94.cbp.dhs.gov/search/recent-search`;
  - "My travel history" → `…/search/history-search`;
  - "Check compliance" → `…/search/compliance-search`;
  - "CBP's I-94 site" → `https://i94.cbp.dhs.gov/home`;
  - the CBP mobile-app page → the final URL from §2.5.
  - Under the links: "Copy the details from CBP's site into the fields below — this app does not connect to CBP."
- **Docket integration** (v1 M3 window engine gets a new kind, `i94`). Admit-until events at 90, 60, 30 and 7 days before, plus "on the day". "D/S" shows no countdown and says "Duration of status — no date to count down to; your status depends on your visa terms." No rule is computed beyond the date the user typed; it is labelled "date you entered from your I-94".
- **Trips (v1 M3).** "Add trip from this I-94" pre-fills a return date from the entry date. The user confirms it; nothing is inferred silently.
- **No scraping, no WebView, no automated form fill of CBP pages.**
- **Acceptance:**
  - unit tests for admit-until event dates, including month ends;
  - a "D/S" test;
  - a widget test: enter an admit-until date 45 days ahead → the Docket shows it under "Next 90 days" with the "date you entered" label;
  - a test that each I-94 link equals its constant;
  - the developer opens each link on the iOS simulator and takes a screenshot. Each route was verified only in the site's JS, not by rendering it.

### M4. Local reminders (no credentials)
- **Package:** `flutter_local_notifications`, on-device only.
- **What it reminds about:**
  - notice deadlines the user typed (RFE response due, biometrics, interview, oath);
  - I-94 admit-until (M3);
  - EAD (I-765) renewal window opening and the "at least 90 days" marker;
  - advance parole (I-131) expiry. This is a new document type with "expiry you entered" only, since no rule quote was fetched for AP;
  - green-card I-90 and I-751 windows (v1 rules);
  - FOIA "check status" (M6).
- **Permission flow (Apple 4.5.4, 5.1.1(ii); Play POST_NOTIFICATIONS).**
  - Never at launch. The first time a user saves a dated item, an in-app sheet explains what the reminder will say. The OS prompt comes only after "Turn on reminders".
  - If permission is denied, everything still works, and a Settings row explains how to enable reminders.
- **Content:** titles and bodies are generic and show **no receipt, A-number or status**. For example, "A date in your case file is coming up: Biometrics appointment in 3 days." The person label appears only if the user opts in under Settings, "Show names in reminders" (default off), because notifications appear on the lock screen.
- **Scheduling:**
  - Android uses inexact scheduling (`inexactAllowWhileIdle`) with **no** `SCHEDULE_EXACT_ALARM` / `USE_EXACT_ALARM` permission (catalogue "Exact alarms").
  - iOS keeps at most 60 pending notifications, nearest first, and re-plans on every app open. The iOS limit of 64 pending local notifications is from knowledge (VERIFY-12).
- **Acceptance:**
  - a unit test of the planner (inputs → the list of `(id, fireAt, title, body)`), with a fixed clock;
  - a test that no planned body contains a receipt pattern, `A\d{8,9}` or a status title;
  - a merged-manifest check: `POST_NOTIFICATIONS` present, no exact-alarm permission;
  - a widget test that the permission sheet appears only after the first dated save.

### M5. Adjustment of Status (I-485) guided timeline (no credentials)
- **Creating a packet.** "Start an AOS file" for a person. It links existing receipts by form type, or adds the I-485, I-765, I-131 and the petition (I-130/I-140/other).
- **Timeline.** Nine steps, with the titles and one-line summaries taken from the §2.6 page, each linked to its uscis.gov URL:
  1. Eligibility;
  2. Petition;
  3. Visa availability (links to the v1 priority-date view and the Visa Bulletin);
  4. File I-485 (filed date = the I-485 receipt date);
  5. Biometrics (date from the notice, M4 reminder);
  6. Interview (date and office from the notice, reminder);
  7. RFE (due date from the notice: "The request will also tell you … the date by when you must respond");
  8. Check status (live status, M9, or recorded);
  9. Decision.
- **How steps get marked done.** By the user, or by the M1 stage mapper when a live or recorded status maps to that step. The mapping shows its source ("from USCIS status 'Case Was Approved' on 2026-11-02").
  - Unmapped statuses never advance the timeline.
  - The app never predicts dates or durations.
- **Companions.** I-765 (EAD) and I-131 (AP) appear as side-tracks with their own statuses and expiry reminders.
- **Document checklist.** Encrypted on the device (M2); each item has done/not done, a note and a date.
  - Items come only from the official Form I-485 instructions PDF, which is linked; the edition date is shown: "Checklist from the 09/18/26 instructions — check the current edition."
  - Initial list: I-693 (required with I-485, quoted §2.6), I-864 where applicable, birth certificate, passport and I-94, two passport photos, and evidence of the petition or its receipt. **Every item must be verified against the instructions PDF on the build day (VERIFY-13)**, and its page reference stored.
  - No legal judgement about which items apply: "Your category's page lists what applies to you" (link).
- **Official links per form:**
  - `uscis.gov/i-485`, `/i-765`, `/i-131`, `/i-693`, `/i-864` (all HTTP 200 on 2026-10-14);
  - `uscis.gov/forms/filing-fees` (200);
  - `uscis.gov/addresschange` (200), with the "within 10 days of moving" quote.
- **Acceptance:**
  - a domain test: receipts with form types → a packet with the right side-tracks; status "Case Was Approved" on the I-485 → step 9 done, with its source;
  - an unmapped-status test (no advance);
  - checklist persistence and encryption (through M2);
  - a widget test from an empty state to a packet with 3 receipts;
  - all links equal their constants.

### M6. FOIA tracker (no credentials; API status plugs in at S1)
- **"My FOIA requests."** Add a request by control number (`^[A-Z]{3}\d{10}$`; example `NRC2022000001` [fetched]) and/or request number (`…REQ`), plus who it is for and a note.
- **Before any API use:** a "Check status on USCIS FIRST" button opens `https://first.uscis.gov/` (HTTP 200) with the control number copied. The user records the status from a picker built from the **official status table** (§2.3: display text and description, shown verbatim). A reminder to check comes every 14 days (user-adjustable) while the status's "Fetch Status" is Yes, and stops at a terminal status.
- **"How to request records"** links to the uscis.gov FOIA page (§2.3) and quotes its alert that requests go online at first.uscis.gov. It also notes the page's line that **I-94 records come from CBP, not USCIS** ("Form I-94 records … Contact U.S. Customs and Border Protection").
- **No FOIA request is created through our app or server in v2.** That is founder decision FD-2: it would send A-numbers, dates of birth, family names and signed declarations through our backend, and USCIS requires its four text blocks and a 60-minute demo.
- **Acceptance:**
  - control-number validation tests;
  - the status picker equals the documented enum (a test against a constant copied from `swagger_1.yaml`);
  - the reminder stops on a terminal status;
  - a widget test for the add → record → reminder flow.

### M7. Support, help and information (no credentials)
- **"Email support".** Opens `mailto:support@americangroup.ai?subject=Case Tracker for USCIS — support`. The body is prefilled with the app version, OS and locale **only**, plus a line: "Please don't include receipt numbers, A-numbers or documents."
  - **Gate:** MA-045 step 2 (`docs/MANUAL_ACTIONS.md:2058`) asks the account holder to "Create contact@, careers@, internships@, india@ and support@americangroup.ai (or forwarders)". Whether support@ exists is **not verified**: `dig MX americangroup.ai` timed out from this machine, and I sent no test email (Charter §5).
  - Until the founder confirms that a test message to support@ arrived (F8), the build uses `contact@americangroup.ai`. That address is the live support page's mailto (`americangroup.ai/client/public/policy/uscis-case-tracker/support.html`) and the App Review contact. It is one constant either way.
- **Help and FAQ.** Static and offline, extending v1's `kFaqEntries`. New entries:
  - "Where does the status come from?" (USCIS Case Status API; the time it was fetched is shown);
  - "Why can't the app find my receipt?" (wrong format; IOE vs paper; **8 U.S.C. 1367 protected cases return 'not found' — contact the USCIS Contact Center**, quoting the API documentation's sentence);
  - "Is this USCIS?" (no);
  - "What do you store?" (the M2 and §8 summary);
  - "How do I delete my data?";
  - I-94, FOIA and AOS basics, each linking its official page.
- **Official contacts.** USCIS Contact Center 800-375-5283 and TTY 800-767-1833 (quoted from the AOS page), as `tel:` links. Plus `uscis.gov/contact` and `uscis.gov/addresschange`.
- **Non-affiliation.** Keep v1's text ("Not affiliated with USCIS or any government agency. Not legal advice.") on the Docket footer, onboarding, Sources, export, every live-status result and the Help header. Extend it to "…USCIS, DHS, CBP or the Department of State." Listing text as in §9. Required by Google Play's Government apps rule and catalogue "Government".
  - No USCIS/DHS seal or look-alike icon.
  - Live results carry "Source: USCIS Case Status API, fetched <time>".
- **Acceptance:**
  - a test that the mailto body has no receipt pattern;
  - the support address comes from one constant;
  - the non-affiliation string appears on the listed screens (widget tests);
  - `tel:` links equal their constants;
  - `legal.affiliation` is identical in all 9 locales (`compliance_test.dart`).

### M8. Edge Function `uscis-case-status`, sandbox (needs F1–F3)
- **Secrets** (Supabase Edge Function secrets only; names fixed here, values never in git or chat):
  - `USCIS_CLIENT_ID`, `USCIS_CLIENT_SECRET`;
  - `USCIS_TOKEN_URL` (sandbox: `https://api-int.uscis.gov/oauth/accesstoken`);
  - `USCIS_CASE_STATUS_BASE` (sandbox: `https://api-int.uscis.gov/case-status`);
  - `USCIS_FOIA_BASE` (sandbox: `https://api-int.uscis.gov/first-case-sbox`);
  - `USCIS_MAX_TPS` (sandbox 4, production per the letter, ≤ 8 until confirmed);
  - `USCIS_DAILY_QUOTA` (sandbox 1000);
  - `USCIS_DEMO_ID` (set only during the USCIS demo, then removed);
  - `USCIS_DATA_KEY` (32-byte AES key for cached and tracked data);
  - `CRON_SECRET`.
  - Moving to production changes **secrets only, never app code**. The app has no environment switch.
- **Auth.** `verify_jwt = true`: the caller must present a valid Supabase JWT (anonymous user, §3). Unauthenticated → 401 with "Sign-in token missing — reopen the app."
- **`POST /lookup {receipt}`.** The receipt goes in the **JSON body, never in the URL or query**, because platform request logs record paths.
  1. Validate it (M1 regexes) → 422 locally, without calling USCIS.
  2. Check the cache (encrypted row keyed by `HMAC-SHA256(USCIS_DATA_KEY, receipt)`, TTL 15 min) → return it with `cachedAt`.
  3. Check the per-user limits: at most 1 upstream call per receipt per 10 min (otherwise serve the cache), at most 30 upstream calls per user per hour, at most 25 tracked receipts per user → 429 with `retryAfter`.
  4. Take the global token bucket at `USCIS_MAX_TPS` and the daily budget at 90% of `USCIS_DAILY_QUOTA` → 503 "Busy, try later" when exhausted.
  5. Get the OAuth token: reuse the isolate-memory token until `issued_at + expires_in − 60 s`. On a 401 from USCIS, refresh once and retry once. Whether token calls count against quota is VERIFY-14.
  6. `GET {base}/{receipt}`, timeout 10 s, adding `demo_id` only if `USCIS_DEMO_ID` is set.
  7. Normalise the response to `{ok, snapshot | error{httpStatus, code, message, category?, traceId?}}`, accepting both error formats (§2.2). Pass USCIS's `message` text through verbatim, since the demo requires it to be shown. **Strip the top-level `message` from successes**, because it echoes the receipt.
  8. Store the encrypted cache row and return.
- **Error mapping**, as the app shows it, always with USCIS's own message underneath:
  - 401 upstream (after retry) → "Our connection to USCIS failed — try later" (alert the office, not the user);
  - 404 → "USCIS doesn't recognise this receipt number. Check it against your notice. If your case is protected under 8 U.S.C. 1367, USCIS answers only through its Contact Center (800-375-5283)";
  - 422 → format/prefix message;
  - 429 (ours or USCIS's) → "Too many checks — try again in N min";
  - 503 → "USCIS's service is unavailable right now" (in sandbox, plus the documented hours);
  - timeout or network → "Couldn't reach our server", with a retry.
- **Logging (privacy-engineer).**
  - Each request logs one structured line, `{evt, route, upstreamStatus, cache:hit|miss, ms, rl:ok|user|global}`.
  - **No** receipt, HMAC, user id, IP, token, status text or USCIS `message` ever appears in logs.
  - A Deno test captures `console.*` during the 200, 404 and 422 paths and asserts that no `[A-Z]{3}\d{10}` pattern, no `Bearer` and no `case_status` appears.
- **Database** (migration; all tables in schema `uscis`, which PostgREST does not expose; RLS on with **no** policies; `revoke all` from anon and authenticated; only the functions' service role reads or writes them):
  - `uscis.lookup_cache(receipt_hmac pk, payload_enc bytea, fetched_at)`. Purged after 6 h by cron.
  - `uscis.rate(user_id, bucket, window_start, count)`.
  - `uscis.tracked(user_id uuid references auth.users on delete cascade, receipt_hmac, receipt_enc bytea, last_status_hash, last_checked_at, last_changed_at, created_at, primary key(user_id, receipt_hmac))`.
  - `uscis.devices(user_id … on delete cascade, platform, token_enc, locale, last_seen_at)`.
- **Synthetic sandbox monitor.** A cron job calls `/lookup`, through the cron-secret path, on staging receipts: 4 with history and 4 without, plus 1 invalid (422) and 1 unknown (404). It runs about 20 times a day on weekdays inside the sandbox's documented hours (M-F 7AM–8PM EST, ≈200 calls a day, under the 1,000 quota).
  - This provides "Minimum of 5 consecutive calendar days of API traffic" with 200 and 4xx results.
  - Whether weekend 503s break "consecutive" is VERIFY-15. Ask USCIS in the production request.
  - It keeps running after go-live as an uptime check, which also preserves key renewal ("no traffic in 365 days → no new keys").
- **Acceptance:**
  - Deno unit tests with a mocked upstream: the token cache and expiry, refresh-on-401, each error mapping in both formats, the cache hit and the 10-minute rule, per-user and global limits, quota guard, receipt-in-body, the logging assertion and `demo_id` header presence or absence;
  - a migration test (local `supabase db reset`) for RLS: anon and authenticated get `permission denied` on every `uscis.*` table;
  - **after F1–F3:** a deployed sandbox run with real calls to `api-int.uscis.gov` using the staging receipts above, recording one 200 with history, one 200 without, a 404 and a 422, with the function log lines quoted in the PR (no personal data in them). These recorded responses become the app's fixtures (M9).

### M9. Live status in the app (needs M8 deployed)
- **The first "Check with USCIS"** on a case shows a one-time disclosure (Play User Data "prominent disclosure"; Apple 5.1.1(ii)): "To check live, the app sends this receipt number to American Group's server, which asks USCIS's Case Status API. We keep a short-lived encrypted copy (up to 15 minutes) to avoid repeat calls. Nothing else about you is sent." Buttons: [Check with USCIS] [Not now].
  - The anonymous sign-in happens here, not before.
  - Declining keeps the v1 manual path; nothing breaks.
- **The result** shows:
  - the current status in the app language: Spanish uses `text_es`/`desc_es`, every other locale uses English, labelled "USCIS provides English and Spanish";
  - the description with safe links (M1);
  - the form type: the API's `formType` fills the case's `formType` if it is empty, and asks before overwriting a user value;
  - the submitted and modified dates (absent for IOE, shown as "not provided by USCIS for online-filed cases");
  - "Fetched <relative time>" / "Saved copy from <time>".
- **History.** `hist_case_status` entries merge into the v1 status log as `source: uscis`, de-duplicated by `(date, completed_text_en)`. User entries stay. A null history shows "USCIS returned no history for this case."
- **"Check all".** Throttled client-side to one request per 300 ms, and respects the server's 429.
- **Offline:** shows the last snapshot with "offline".
- **The manual "Check on USCIS website" link remains** (egov.uscis.gov), so the user can always compare.
- **Acceptance:**
  - the parser runs on **recorded sandbox fixtures** from M8;
  - widget tests for each error state (401/404 with the 1367 text/422/429/503/timeout/offline);
  - the Spanish-locale test uses the `_es` fields;
  - the disclosure appears once and "Not now" leaves no server call (mock client, zero calls);
  - history merge without duplicates;
  - an IOE snapshot without dates;
  - developer screenshots on the simulator against the **sandbox** function with staging receipts: internal, never a store asset (§9).

### M10. Status-change alerts (needs M8 plus F9 for push)
- **Opt-in per receipt.** "Alert me when USCIS updates this case" with a disclosure: "Your receipt number will be stored encrypted on our server so it can be checked about 4 times a day. Turn this off any time to delete it."
  - Turning it on calls `/track` (stores `receipt_enc` and `receipt_hmac`), then asks for OS notification permission if it has not been granted (never at launch), then calls `/device {platform, fcmToken, locale}`.
  - Turning it off calls `/untrack`, which deletes the row at once.
- **Server refresh (`uscis-refresh`).**
  - Supabase cron (pg_cron + pg_net, VERIFY-16: whether these extensions are enabled on the project) calls it every hour with `CRON_SECRET`.
  - Each run takes tracked rows with `last_checked_at` older than 6 h, oldest first, within a run budget of 10% of the daily quota.
  - It looks each one up through the shared client (which writes the cache, so the app's next open is free).
  - It computes `status_hash = sha256(statusEn + "|" + history length + "|" + last history date)`, which deliberately ignores `modifiedDate` (§2.2 caveat).
  - **Only when the hash changes:** set `last_changed_at` and send a push.
  - It deletes rows whose user has `devices.last_seen_at` older than 90 days (the app sends a heartbeat on open), and deletes rows 30 days after a terminal stage (approved, denied, card delivered).
- **Push** goes through FCM HTTP v1 for both platforms (the app already uses Firebase project `americangroupllc-agl3`, per `ios/Runner/GoogleService-Info.plist` `PROJECT_ID` and `android/app/google-services.json`).
  - Secret: `FCM_SERVICE_ACCOUNT_JSON`.
  - Body, localised from `devices.locale`: title "Case update", body "A case you track has a new status. Open the app to see it."
  - Data payload `{"t":"case_update"}` only. **No receipt, status, name or HMAC in the push.**
  - Tapping it opens the Cases list and refreshes.
  - Tokens are refreshed on every app open; FCM `UNREGISTERED` deletes the device row.
- **App and stores:**
  - iOS: Push Notifications capability on App ID `com.americangroupllc.usciscase`, plus `aps-environment` in `ios/Runner/Runner.entitlements`. Xcode/export sets `production` for App Store builds, and the provisioning profiles are regenerated.
  - **No `UIBackgroundModes`**: alerts are visible pushes, not silent pushes.
  - APNs auth key uploaded to Firebase project `americangroupllc-agl3` (F9).
  - Android: `POST_NOTIFICATIONS` (API 33+) and a notification channel "Case updates".
  - Apple 4.5.4: push is not required to use the app; there are no marketing pushes, ever; no sensitive data goes in pushes.
  - Note from office memory: the GoogleService-Info.plist on disk may not be the one Xcode bundles. Check the IPA's bundled plist `PROJECT_ID` before testing push (VERIFY-17).
- **"Delete my data on our server"** in Settings calls `/forget`, which deletes every `uscis.*` row for `auth.uid()` and then deletes the anonymous auth user through the admin API with the service role. This path **does not** depend on the `delete_user` RPC that MA-044 is waiting on. "Delete everything on this phone" (v1 M5) also calls `/forget` if a session exists.
- **Acceptance:**
  - Deno tests: the hash ignores a `modifiedDate`-only change; a push happens only on a hash change; the payload contains no receipt or status (assertion on the built FCM request); inactivity and terminal purges; `/forget` removes all rows and the user (local stack);
  - app tests: opt-in order (disclosure → track → permission → device), opt-out deletes, no permission prompt at launch (an integration test boots the app and asserts no permission request);
  - an end-to-end sandbox check on a physical device. **This is a human step**: track a staging receipt, then the office resets that row's stored `last_status_hash` to a stale value through a route that accepts only `CRON_SECRET` (never callable from the app), and the next real sandbox refresh must deliver the push. Until then, report it as **not verified**.

### M11. Privacy, policy and store paperwork (written by the office; applied per Charter)
- Data inventory (§8) committed as `docs/privacy-inventory/Uscis-Case.md` or the office's existing location.
- `store/privacy/Uscis-Case.json` and `docs/console-answers/Uscis-Case.md` updated to the §8.3 deltas. `ios/Runner/PrivacyInfo.xcprivacy` gets any required-reason APIs that the new plugins bring (checked with `scripts/testflight/privacy_scan.py`).
- Privacy policy and terms **draft** covering every USCIS affidavit item (§8.4), as an approval request (Charter §6). The live page is not edited.
- Listing copy, review notes and screenshots list (§9) prepared in `store/apps/Uscis-Case.json` **only after** live status reaches production. Before that, the listing must not claim live status.
- **Acceptance:**
  - `python3 scripts/store_policy_audit.py Uscis-Case` shows no FAIL that this work introduces, and 4.5.4 moves from n-a to HUMAN or PASS with evidence;
  - `python3 scripts/privacy_details.py` and `privacy_scan.py --all` are clean for Uscis-Case;
  - the approval request is filed under `ai-office/reports/approvals/`.

### M12. Production readiness and release gate
- **Demo kit**, in `ai-office/projects/real-apps/uscis-demo.md`:
  - a script that walks through every documented response code (200 with and without history, 401, 404, 422, 429, 503) on the **staging** environment with staging receipts only (no PII), as the demo agenda requires;
  - where `error.message` is shown in the app UI;
  - how `demo_id` is set (secret `USCIS_DEMO_ID`) and removed afterwards;
  - who attends: the founder as the primary contact and authorised signatory, plus a technical lead.
- **Release gate.** No App Store or Play build that shows "Check with USCIS" is submitted or promoted until:
  - (1) the production secrets are set and the function is redeployed;
  - (2) one production lookup of a **real receipt held by a consenting person** succeeds and is logged without personal data;
  - (3) §9's review-notes path has been run on that build.
  - Before then, live status is exercised only in debug and TestFlight-internal builds against the sandbox function. They are the same binary as release, because the environment is server-side. The store submission simply waits.
  - This keeps the store build free of hidden switches (5.6) and of features that fail for real users.
- **Key hygiene:**
  - put the key's age in the office calendar: day 344 notice, day 351 grace, day 365 expiry (key policy);
  - the function reads one credential pair, and rotation is a secret swap inside the 14-day grace window.
- **Acceptance:** the demo kit is committed; the gate is written into `ai-office/projects/real-apps/continue/Uscis-Case.json` notes and into the review-notes draft; the founder confirms that the demo passed (the USCIS email, not quoted in git).

## 5. SHOULD (in order, after the MUSTs)

- **S1. FOIA status via API.** `uscis-case-status` route `foia-status {controlNumber | requestNumber}` → `GET {USCIS_FOIA_BASE}/case-status`. It shows `status.display` and `status.description` verbatim (USCIS requirement #4), plus `placeInQueue`/`queueLength` and `estCompletionDate` labelled "USCIS estimate". It is polled at most daily, and only while "Fetch Status" is Yes.
  - Only after VERIFY-1 (read scope allowed) and VERIFY-6 (works for portal-filed requests), checked in the sandbox.
  - The FOIA production demo is a separate 60-minute demo (§2.4).
- **S2. Home-screen widgets** (iOS WidgetKit, Android Glance). Each shows "Next date in your file: 12 days" and "Cases updated today: 1". **No receipts, names or status text** (lock screen, StandBy). **No ads** (2.5.18). It reads a minimal app-group value written by the app. Catalogue 2.5.16 and 4.4 apply.
- **S3. Document attachments for the AOS checklist.** Camera or photos into an encrypted file per item. Needs `NSCameraUsageDescription` and `NSPhotoLibraryUsageDescription` with specific purpose strings (5.1.1(ii), ITMS-90683). Never uploaded.
- **S4. NVC case entry.** Manual NVC case number and invoice ID per person, linking to `ceac.state.gov` (HTTP 403 to curl on 2026-10-14; open it on the simulator). There is no NVC API, so nothing is fetched. v1's NVC guide stays.
- **S5. App Attest / Play Integrity** tokens verified by the function, as abuse protection for the free quota.
- **S6. Visa Bulletin server feed.** v1 Q3, unchanged: travel.state.gov returned 403 to curl again on 2026-10-14. It needs a founder decision and a migration.
- **S7. `.ics` export of Docket dates** (v1 S5) and a share sheet (v1 S4).

## 6. Fields from the leaders: scope and data source

| Field / feature (leader that claims it) | v2 scope | Data source | API we lack? |
|---|---|---|---|
| Multiple receipts (all) | **In** (exists) | user | — |
| Family members / person per case (Lawfully "family") | **In** (v1 M2 `person`) | user | — |
| Form type (all) | **In** | Case Status API `formType` [fetched]; else user | — |
| Service centre (common) | **In** (M1) | receipt prefix table (VERIFY-9) | — |
| Live status and description (all) | **In** (M9) | Case Status API | — (sandbox now, production pending) |
| Case-history timeline (Lawfully, MigraConnect) | **In** (M9) | API `hist_case_status` (may be null) + user log | — |
| Spanish status text (Lawfully, MigraConnect) | **In** (M9) | API `*_es` fields [fetched] | — |
| Status-change push alerts (Immivision, Lawfully) | **In** (M10) | server refresh + FCM | — |
| Priority date + category (Lawfully, 1Point3Acres) | **In** (v1 M2) | user | — |
| Visa Bulletin (Immivision, Lawfully) | **Partial**: user-recorded cutoffs (v1 M2) | user, link to travel.state.gov | **Yes**: no official API; page 403 to curl (S6) |
| Processing times (Lawfully) | **Partial**: user-recorded (v1 M2) | user, link to egov | **Yes**: not in the USCIS API catalogue; egov 403 to curl |
| Notes (common) | **In** (exists) | user | — |
| Documents / checklist (Lawfully) | **In**: checklist (M5); attachments S3 | official I-485 instructions (VERIFY-13); user | — |
| I-94 (Techno GYM "information on the I-94") | **In** (M3): manual + links + reminders | user; i94.cbp.dhs.gov links | **Yes**: no public CBP API |
| AOS / I-485 tracking (Lawfully lists I-485) | **In** (M5) | uscis.gov AOS page; user receipts; API status | — |
| FOIA tracking (MigraConnect) | **In** (M6), manual; API status S1 | user; FOIA API (sandbox enabled) | No: FOIA API exists (§2.3); production pending |
| FOIA request creation | **Out**: FD-2 | FOIA API `POST /case` | — (privacy/legal, not technical) |
| Widgets (civics apps) | **SHOULD** (S2) | on-device | — |
| NVC case (Immivision, Lawfully) | **SHOULD** (S4), manual | user; ceac.state.gov link | **Yes**: no NVC API |
| Neighbour / range search (Immivision) | **Out** | — | Would query strangers' receipts; burns shared quota; outside "customers and their representatives" |
| EOIR court by A-Number (Lawfully, MigraConnect) | **Out** | — | **Yes**: no API in the USCIS catalogue; DOJ system |
| DOL / PERM (Lawfully) | **Out** | — | **Yes** |
| Case analysis / predictions / AI assistant (Lawfully Pro, others) | **Out** | — | No data; legal-advice risk (v1 §6) |
| Lawyer consultations (Lawfully) | **Out** | — | Regulated service; not our business |
| Civics test (Immivision, civics apps) | **In** (exists) | official USCIS lists | — |
| Immigration news (Immivision) | **In** (v1 M4, Federal Register by form) | federalregister.gov API | — |

## 7. Out of scope (v2)

- Scraping or automating any government site (egov.uscis.gov, i94.cbp.dhs.gov, ceac.state.gov, travel.state.gov, first.uscis.gov). Links only.
- Calling USCIS from the app, or holding any USCIS credential in the app or the repo.
- FOIA request creation (FD-2), and uploading any document to our server.
- Neighbour or range lookups; predictions; AI advice; EOIR, DOL and NVC fetching.
- Email/password or social accounts. The only server identity is anonymous.
- Marketing or promotional pushes; push bodies with case data; ads in notifications or widgets.
- Storing names, A-numbers, I-94 data, passport data or documents on the server.
- The web, RN and Electron code in the repo (as v1).

## 8. Privacy and security (privacy-engineer)

### 8.1 Data inventory (v2)

| Data | Where it lives | Leaves the device? | To whom | Retention |
|---|---|---|---|---|
| Receipt numbers | device, encrypted (M2) | on "Check with USCIS" (body of an HTTPS POST) and if alerts are on | our Edge Function → USCIS | cache 15 min (purged by 6 h); tracked rows until opt-out, 90 days inactivity, or 30 days after a terminal stage |
| Status text and history | device, encrypted | no (comes **from** USCIS) | — | cache as above |
| Person labels / names | device, encrypted | **no** | — | until the user deletes them |
| A-numbers (optional field) | device, encrypted | **no** | — | until the user deletes them |
| I-94 record no., class, dates; passport/EAD/AP expiry | device, encrypted | **no** | — | until the user deletes them |
| AOS checklist (+ S3 attachments) | device, encrypted | **no** | — | until the user deletes them |
| FOIA control/request numbers | device, encrypted | only with S1 | Edge Function → USCIS | not stored server-side (pass-through) |
| Anonymous Supabase user id | device (encrypted session) + Supabase auth | yes | Supabase (our processor) | until `/forget` or inactivity purge |
| FCM token, locale | server `uscis.devices`, encrypted | yes | Supabase; Google FCM / Apple APNs for delivery | until opt-out, `/forget`, `UNREGISTERED`, or 90 days |
| IP address / request metadata | Supabase platform logs | yes | Supabase | platform retention (VERIFY-18); our code logs none |
| Ads / crash / analytics | unchanged from v1 (AdMob, Crashlytics, Analytics) | yes | Google | unchanged |

### 8.2 Controls (acceptance lives in M2, M8, M10)
- **Encryption.** Encrypted at rest on the device (Keychain/Keystore key, AES-GCM). On the server, sensitive columns are AES-GCM under `USCIS_DATA_KEY`, and lookups use an HMAC, so the database never holds a plaintext receipt.
- **Exposure.** The `uscis` schema has no PostgREST exposure; RLS is on with no policies; only the service role touches it.
- **Logs.** No personal data in function logs (tested). No receipt in URLs. USCIS's echo `message` is stripped.
- **Push.** No sensitive data in push bodies (tested), and no names in local reminders unless the user opts in.
- **Deletion.** `/forget` is server-side deletion that does not depend on MA-044. "Delete everything on this phone" also clears the encrypted blob and Keychain key.
- **Crash reports.** Crashlytics custom keys and logs must not carry receipts. Test: grep `lib/` for `recordError`/`log(` calls carrying case objects. **Fix, not waive.**

### 8.3 Label and form deltas (proposed; publishing is store-compliance, Play forms are founder)
- **Apple App Privacy** (`store/privacy/Uscis-Case.json`):
  - add **User ID** (the anonymous id) — linked, App Functionality;
  - add **Device ID** for the push token (App Functionality), alongside the existing advertising one;
  - add **Other User Content** or **Other Data Types** for receipt numbers sent for lookups and alerts — linked, App Functionality. The category choice is VERIFY-19 against Apple's definitions;
  - nothing used for tracking.
  - EMAIL_ADDRESS and NAME stay or go according to v1 Q2 (legacy accounts), not v2.
- **Play Data safety** (`docs/console-answers/Uscis-Case.md`):
  - Personal info → Other info (receipt numbers): collected, not shared, not processed ephemerally (cached), required only for the optional live features;
  - Device or other IDs (push token, anonymous id): collected;
  - encrypted in transit: yes; deletion: in-app (`/forget`) and via the existing deletion URL.
  - Whether sending the receipt to USCIS **at the user's request** counts as "sharing" is VERIFY-20 against Play's user-initiated-transfer exemption.
- **Privacy manifest:** run `privacy_scan.py` after adding `firebase_messaging`, `flutter_local_notifications` and `flutter_secure_storage`. Their SDK manifests must be present (ITMS-91061).

### 8.4 Privacy policy must cover (USCIS affidavit list, fetched; legal text → founder approval)
- Data types collected.
- How data is used, including de-identified data.
- The named entities data is shared with: Supabase, Google FCM, Apple APNs, USCIS, AdMob, Firebase.
- "no data is sold".
- Sharing choices and risks.
- Third-party use prohibited without active consent.
- Third parties bound by the policy.
- Breach notification.
- Retention, including dormant accounts (90 days).
- How to permanently delete, and **how soon** deletion happens (immediately for server rows; backup retention VERIFY-21).
- CCPA where applicable.
- Change of ownership.
- Account closure.
- Notice of ownership changes.
- Active consent and a plain-language summary for policy changes.
- Readability: 14 px or larger, contrast 4.5:1, grade 12 or below.

Today's page (`/policy/uscis-case-tracker/`, HTTP 200, title "Case Tracker for USCIS — Privacy Policy & Government Disclaimers") and `terms.html` (HTTP 200) exist. Whether they meet this list is **not verified**; I did not audit their text.

## 9. Store impact (store-compliance)

**Positioning** (applied only after the M12 gate; until then the listing keeps v1's honest "does not fetch statuses" text).
- **Subtitle candidates** (≤30): "Live USCIS status & deadlines" (29) — note it puts "USCIS" in the subtitle; "Case status, I-94 & deadlines" (29).
- **Opening line:** "Live case status from USCIS's Case Status API, in a family case file that also tracks your I-94, filing windows, I-485 steps and FOIA requests."
- **Allowed claims:** "uses USCIS's Case Status API"; "English and Spanish status text from USCIS"; "alerts when a tracked case changes"; "no sign-in".
- **Forbidden claims:** "official", "only", "first", "faster than", USCIS or DHS seals or colours, and any wording implying endorsement.
- **Government source disclosure in the description** (Play Government apps; catalogue "Government"): "Not affiliated with, endorsed by or operated by USCIS, DHS, CBP or the Department of State. Status information comes from USCIS (uscis.gov); I-94 links go to CBP (i94.cbp.dhs.gov)." The exact Play wording requirement is VERIFY-22.
- **Name:** still v1 Q1. "USCIS" in the store name raises the impersonation risk (catalogue 2.3.7, Play "Impersonation").

**Screenshots** (retake; iPhone 6.9", iPad 13", Play phone and tablet):
1. Live status result with history, with the privacy mask on.
2. Docket with an I-94 admit-until and an EAD window.
3. AOS timeline with steps done from USCIS statuses.
4. Alerts opt-in sheet (the disclosure text).
5. FOIA tracker.
6. Help & support with the non-affiliation statement.

They are captured from the **production** build after the M12 gate, on a consenting person's real receipt with the mask on, so no receipt is legible. Sandbox staging data is **not** used for store screenshots, because it is test data from USCIS's staging system and would show a case that is not the user's own (2.3.3 / 1.1.6 risk).

**Review notes** (draft; replaces v1's):
- **What it does:** as positioning. "The app never contacts USCIS directly: lookups go through our server (Supabase Edge Function), which holds USCIS-issued credentials, as USCIS requires."
- **How to test live status.**
  - USCIS's production API does **not** accept USCIS's published sandbox test receipts ("Staging Receipt Numbers are not supported", developer.uscis.gov), so **a sandbox receipt cannot be offered to App Review**.
  - Option A (founder decision F10): a real receipt from a consenting person, entered **only** in App Store Connect's review notes, never in git.
  - Option B: a screen recording of a live lookup attached in ASC, plus the always-available manual path. Any receipt typed in the 3-letters-plus-10-digits format shows the documented "not recognised" message, which demonstrates the error handling.
  - No reviewer detection, no demo mode (5.6).
- **Push:** "Optional. Open a case → 'Alert me when USCIS updates this case' → allow notifications. Pushes contain no case data."
- **Accounts:** "No sign-in. An anonymous identifier is created only when the user first checks live status, and Settings → 'Delete my data on our server' deletes it and all server data immediately."
- **External services:** Supabase (our server), USCIS Case Status API (through our server), Firebase Cloud Messaging / APNs, AdMob, Crashlytics, Analytics, Federal Register API. Links to uscis.gov, egov.uscis.gov, first.uscis.gov, i94.cbp.dhs.gov, cbp.gov, travel.state.gov, ceac.state.gov.
- **Test devices:** only those actually used. The physical-device push test is human (M10).

**Catalogue rules** (`store/policy/catalogue.json`) that v2 touches. "Today" is the 2026-10-14 audit (`docs/store-policy/Uscis-Case.md`); "v2 needs" is the evidence to produce:
- **4.5.4 Push** (n-a → applies): not required; no marketing; no sensitive data; no prompt at launch (M10 tests).
- **5.1.1(ii) Permission:** notification prompt only after opt-in; camera/photos purpose strings only if S3 ships.
- **5.1.1(v) Account sign-in & deletion** (FAIL today because of MA-044): v2's anonymous id gets `/forget`. The legacy-account FAIL stays v1 Q2 / MA-044.
- **5.1.2 Data use and sharing:** no tracking; the label is updated (§8.3).
- **5.1.1(ix) Regulated fields:** the app is a tool, not a legal or government service. No legal advice, no filing on users' behalf (FOIA create is out). The non-affiliation statement is everywhere (M7).
- **5.2.2 Third-party services:** USCIS API Terms of Use. **Not read (HTTP 403)**; the founder accepts them in the affidavit (F6). Whether ads and commercial use are permitted is VERIFY-23.
- **1.6 Data security:** server encryption, RLS, no secrets in the binary (`apple_requirements.py` secret scan).
- **2.5.4 Background modes:** none added (visible push only).
- **2.4.2 Power:** no background polling on the device.
- **2.1 Information needed:** review notes as above.
- **2.3 / 2.3.7 Accurate metadata and name:** claims gated on production; no competitor names in keywords.
- **2.3.3 Screenshots:** retake as above.
- **4.2 / 4.3 / 4.2.6:** v2 adds real, server-backed functionality distinct from the portfolio. The differentiation statement §3 must be rewritten with the §1 table (descriptions only, apps not run).
- **2.5.16 / 4.4 Extensions, 2.5.18 Ads:** only if S2 widgets ship (no ads in widgets).
- **Play:**
  - Data safety (FOUNDER form), User Data (prominent disclosure, M9 and M10);
  - Permissions (`POST_NOTIFICATIONS`); Exact alarms (none);
  - Account deletion (anonymous id and `/forget`);
  - Government (disclosure plus source);
  - Impersonation (name, icon); Deceptive behaviour (claims gated);
  - Background (server-side refresh only);
  - Device and network abuse (USCIS terms, rate limits);
  - App access (no login).

## 10. Founder actions (Charter §2, §4, §5, §6; the office prepares, the founder decides)

The founder's developer.uscis.gov account and developer team **exist**, and the app is **approved** with "Case Status API - Sandbox" and "first-case-sbox" (FOIA sandbox, §2.1) enabled. Its two keys were issued on 2026-07-01, sandbox only.

- **F1. Rotate both exposed keys now**, before any use. In the portal: the team → Apps → the app → regenerate the credentials. The exact portal steps are VERIFY-24. To force immediate revocation, email `developersupport@uscis.dhs.gov` ("revoked … upon user request", key policy). That email is external contact, so the founder sends it.
- **F2. Put the new values only into Supabase Edge Function secrets** on project `smvvjivvlprjhzhoizym`, as `USCIS_CLIENT_ID` and `USCIS_CLIENT_SECRET`, through the dashboard (Edge Functions → Secrets) or `supabase secrets set --project-ref smvvjivvlprjhzhoizym` typed locally.
  - Never paste them in chat, git, an issue or a file.
  - Also set `USCIS_DATA_KEY`, generated and set without printing it (e.g. `supabase secrets set USCIS_DATA_KEY="$(openssl rand -base64 32)"`), `CRON_SECRET` the same way, and later `FCM_SERVICE_ACCOUNT_JSON` (F9).
  - The non-secret endpoints (`USCIS_TOKEN_URL`, `USCIS_CASE_STATUS_BASE`, `USCIS_FOIA_BASE`, `USCIS_MAX_TPS`, `USCIS_DAILY_QUOTA`) can be set by the founder or with the office's command once secrets access is granted.
- **F3. Approve the backend deploys:**
  - (a) the `uscis` migration, through `deploy.yml`'s `production` environment approval;
  - (b) the new functions-deploy step and its first run;
  - (c) the pg_cron/pg_net schedule if the extensions need enabling (VERIFY-16).
  - Never `supabase config push`.
- **F4. Anonymous sign-ins** (MA-040): confirm they are enabled on the project, or approve enabling them. The office has not tested this, to avoid creating a production user (VERIFY-8).
- **F5. Request production access** after M8 has shown ≥5 consecutive calendar days of sandbox traffic with 200s and 4xx:
  1. email `developersupport@uscis.dhs.gov` (external contact);
  2. complete the **Developer Portal Affidavit** as an authorised signatory. It needs US incorporation of American Group LLC (please confirm state and entity), the business website, privacy policy and terms (F7);
  3. send the `demo_id` confirmation (the office sets `USCIS_DEMO_ID` and provides the screenshot);
  4. book and attend the demo (Wed/Thu, 1–2 PM EST, 30 min for Case Status) with the office's technical lead;
  5. on go-live, set the **production** client credentials (a new app, new secrets) and production URLs from the USCIS letter.
  - FOIA production (S1) is a separate 60-minute demo and requires the four USCIS text blocks.
- **F6. Read and accept the USCIS Terms of Use** in the affidavit (`myaccount.uscis.gov/legal-terms`, not readable by the office: HTTP 403). Confirm they allow an **ad-supported** consumer app, and whether any branding or attribution rules apply (VERIFY-23). Confirm there is no fee (VERIFY-5).
- **F7. Approve the privacy policy and terms rewrite** (legal text, §8.4) before the affidavit. USCIS audits these pages.
- **F8. support@americangroup.ai:** confirm the mailbox or forwarder exists (MA-045 step 2) by sending it a test message. Until then the app uses contact@.
- **F9. Push setup:**
  - enable Push Notifications on App ID `com.americangroupllc.usciscase` (Apple Developer);
  - create or upload an APNs auth key to Firebase project `americangroupllc-agl3`;
  - create a Firebase service account with FCM send rights and store its JSON as `FCM_SERVICE_ACCOUNT_JSON` (secret).
- **F10. Reviewer receipt:** decide between Option A (a consenting person's real receipt, typed only into ASC review notes) and Option B (screen recording).
- **F11. Store consoles:** publish the updated App Privacy label (store-compliance prepares it), Play Data safety, and the Advertising ID and App access forms.
- **F12. Still open from v1:** Q1 (name / keep), Q2 (legacy accounts; constrained by §3), Q3 (bulletin feed), Q4 (ads), Q5 (resubmission under the 5.6 freeze, MA-043), Q6 (beta statement).
- **FD-2. FOIA request creation through our server.** It would mean processing A-numbers, dates of birth, family names and signed declarations, a 60-minute USCIS demo, and the four required text blocks. The recommendation is **no** for v2.

## 11. MUST / SHOULD summary

**MUST** (M1–M7 need no credentials; M8–M10 need F1–F4, and M10 also F9; M11–M12 lead to production):
1. **M1** Receipt intelligence and status parser (both receipt regexes, prefix table, safe HTML, stage mapper; fixtures from the OpenAPI).
2. **M2** Encrypted on-device store + migration from `shared_preferences` + privacy mask.
3. **M3** I-94 / CBP: manual record, verified CBP route links, admit-until in the Docket.
4. **M4** Local reminders (notices, I-94, EAD/AP/I-90/I-751, FOIA) with consent after opt-in, inexact alarms and no case data in bodies.
5. **M5** AOS (I-485) nine-step timeline tied to receipts, companion I-765/I-131, encrypted checklist, official links.
6. **M6** FOIA tracker (control/request number, first.uscis.gov link, official status vocabulary, reminders). No creation.
7. **M7** Support (`mailto`, no PII; support@ gated on F8), Help/FAQ (including the 8 U.S.C. 1367 note), official contacts, non-affiliation everywhere.
8. **M8** Edge Function `uscis-case-status` on the sandbox: OAuth client credentials server-side, cache, limits, error normalisation, no-PII logs, `uscis` schema with RLS, synthetic 5-day sandbox traffic.
9. **M9** Live status in the app (disclosure, en/es, history merge, every error state, offline).
10. **M10** Status-change alerts (opt-in, `uscis-refresh` cron, FCM with a generic body, `/forget`, purges).
11. **M11** Privacy inventory, label and Data safety deltas, policy draft for approval, store copy prepared behind the gate.
12. **M12** USCIS demo kit, production switch by secrets only, store release gate, key-rotation calendar.

**SHOULD:** S1 FOIA status via API; S2 widgets (no case data, no ads); S3 encrypted document attachments; S4 NVC manual entry; S5 App Attest / Play Integrity; S6 Visa Bulletin feed (v1 Q3); S7 `.ics` and share sheet.

**Out of scope:** §7.

## 12. VERIFY list (everything this spec could not confirm)

Each is "verify against developer.uscis.gov docs (web access is off)" unless another source is named.

1. Whether the founder's app may use FOIA **status** (read) without **create** (write); the spec declares `[write, read]`.
2. What the documented second receipt format `[a-zA-Z]{3}\*[0-9]{9}` means and how to send it (URL-encoding of `*`).
3. The time zone of `submittedDate`/`modifiedDate` ("MM-dd-yyyy HH:mm:ss").
4. Production quota and TPS: the OpenAPI says 400,000 a day and 10 TPS; the sandbox page says they are shared at go-live.
5. Any fee for API use (none stated on the pages fetched).
6. Whether FOIA status works for requests filed directly on first.uscis.gov.
7. The current name and URL of CBP's mobile app (`/cbpone` redirected to `/cbplink`).
8. The production state of Supabase anonymous sign-ins (MA-040). Not tested, to avoid creating a user.
9. The receipt-prefix → office table (from knowledge; needs a uscis.gov source).
10. The `flutter_secure_storage` and crypto package versions and their Keystore/Keychain behaviour.
11. I-94 record-number format and printout field labels (from knowledge).
12. The iOS limit of 64 pending local notifications (from knowledge).
13. Every AOS checklist item against the 09/18/26 Form I-485 instructions PDF.
14. Whether OAuth token requests count against the daily quota.
15. Whether sandbox weekend/after-hours 503s break "5 consecutive calendar days of traffic".
16. Whether pg_cron/pg_net (and Vault) are enabled on project `smvvjivvlprjhzhoizym`.
17. Which GoogleService-Info.plist Xcode actually bundles (check the IPA's `PROJECT_ID`).
18. Supabase platform log retention for Edge Function request metadata on the project's plan.
19. Apple App Privacy category for receipt numbers (Other User Content vs Other Data Types).
20. Play Data safety: whether a user-initiated transfer to USCIS counts as "sharing".
21. Supabase backup retention (to state "how soon" deletion completes in the policy).
22. The exact Play Government-apps disclosure wording for the listing.
23. The USCIS Terms of Use (HTTP 403): commercial and ad-supported use, attribution and branding.
24. The exact portal steps to regenerate client credentials for an existing team app.
