# Spec v2: PlantPulse → a plant and houseplant health app that works offline

Author: product-manager, with technical-architect, market-researcher, privacy-engineer and store-compliance (AI office), 2026-10-14
Founder decision (2026-10-14): PlantPulse becomes a plant and houseplant health app. It identifies plants and trees, monitors health, plans feeding and watering, offers an AI chat assistant that works offline, and reads plant tags and fertiliser labels with on-device OCR. Free API keys or vendors are fine where they help. **This replaces the smart-home TV/light remote** (`PlantPulse.md`, commits f66f8e6 / 73d30b4 / d2e62f0). The founder has approved retiring the remote (Charter §8).
Project: real-apps (`../plan.md`, criteria 1–7; GitHub issue #24).
Repo: `/Users/spatchava/agl/PlantPulse` (Flutter app in `mobile/`). The bundle id / package `com.americangroupllc.plantpulse` is **permanent**.

**This spec contains no code.** Only this file is written.

---

## 0. Evidence base and markers

**Read for this spec on 2026-10-14:**
- the office role files and `CHARTER.md`;
- `PlantPulse.md` (v1 spec), `plan.md`, `overlap.md`, `continue/PlantPulse.json`;
- `store/apps/PlantPulse.json`, `docs/store-policy/PlantPulse.md` (generated 2026-10-14T01:51), all 113 rules of `store/policy/catalogue.json`, `store/privacy/PlantPulse.json`;
- `status.csv`, `docs/play-production-blockers.json`, `store/vendors/{apps/PlantPulse.csv,playbook.json,registry.json}`, `docs/API_VENDORS_AND_AFFILIATES.md` §4, `scripts/store_policy_audit.py` (tag detectors);
- the PlantPulse app source, and Verba's source and history.

`diagnosis.md` does not exist (`find ai-office -name 'diagnosis*'` → nothing).

**No web access was used.** No curl, WebFetch or WebSearch. That follows the founder's pending decision on web use. Every vendor, model, licence, limit and competitor fact below comes from knowledge and carries a marker **[V-n]** ("verify against the vendor's official page before building"). §13 lists them all. Repo facts carry the path or command that showed them.

**Repo state when read:**
- **PlantPulse** `main` @ `d2e62f0` ("round spinner on the run sheet…"). The Real Apps workflow committed its remote work while this spec was being written; earlier in the session the tree had dirty `lib/`, ARB and test files, and now it does not.
  - Still dirty and **not ours**: `mobile/ios/Podfile.lock` (one line, the CocoaPods version), every fastlane screenshot, `metadata/*/description.txt` and `review_information/notes.txt`.
- **Verba** `main` @ `9fbbdf8` ("hidden features removed"), level with `origin/main`. That commit **deleted** `lib/core/llm/*`, `native/verba_llama/*`, `ios/VerbaKeyboard/*` and their tests. The last commit that still contains the llama.cpp shim is **`ef8be2c`**.

**Store state** (no public users exist):
- Apple: `apple: review_state = PREPARE_FOR_SUBMISSION`, build 2 uploaded 2026-10-04, never submitted (`status.csv`).
- Google Play: internal track versionCode 3 `completed` (testers only). Production versionCode 1 is a `draft`, state `PRODUCTION_DRAFT_STAGED` (`docs/play-production-blockers.json`).
- **So no production user has remote data to migrate** (M1).

## 1. What changes and why

**Today.** The app is "iPlantPulse", a LAN remote for Roku, WLED and webhooks: 10,033 lines of non-l10n Dart in `mobile/lib`, 42 files.
- The store JSON itself says "this app has nothing to do with plants" (`store/apps/PlantPulse.json` `_drafted.drawn_from`).
- The name has always promised plants. The founder now makes the product match the name instead of renaming it.
- The display name stays **iPlantPulse**. "PlantPulse" belongs to another developer on the App Store, and ASC answered 409 (`store/apps/PlantPulse.json` `_name_note`).

**Open audit failures** (`docs/store-policy/PlantPulse.md`), all addressed below:
- 4.2.6 / 4.3(a): no differentiation answers, QA verdict "partial".
- 5.1.1(i) and Play User Data: no in-app privacy-policy link.

**The Verba premise does not hold (technical-architect finding).** The brief says Verba "already runs an on-device LLM through one llama.cpp FFI shim". It never did:
- The Verba spec (`specs/Verba.md:40`) recorded: "Cannot run on either platform today. `native/llama.cpp` is absent and there is no `.gitmodules`, so the shim builds as the stub… On iOS the shim is not in the Runner target."
- At `ef8be2c`, `lib/core/llm/model_catalog.dart` lists three models, all with `sha256: ''`. So the download "verification" in `model_store.dart` had no digest to check against.
- As of `9fbbdf8` the code is gone from Verba.

What we can reuse is the **design and the source**, recovered from `ef8be2c`:
- the C ABI in `native/verba_llama/include/verba_llama.h`: `load / free / start / next_token / free_string / cancel / is_real / version`;
- its CMake file, with llama.cpp optional, the stub when absent, and `VERBA_HAS_LLAMA`;
- the Dart `LlmEngine` interface (streaming `generate`);
- `ModelStore`: `.part` file, rename only after digest, per-model status.

The real on-device engine has to be finished, not re-used: vendor llama.cpp, add the iOS build, fill in the digests. See D2 and M8.

## 2. User, core job, signature, positioning

**User.** Someone with 5–40 houseplants, maybe a balcony or small garden and a few trees. They forget when they last watered. They can't name half their plants. They panic at yellow leaves. They are tired of plant apps that need an account, a subscription and a signal in the back bedroom.

**Core job.** Know each plant, look after it on time, and react sensibly when it looks unwell, from a journal that lives on the phone.
1. **Add a plant.** Photograph it. The phone suggests what it is, offline, with an honest confidence. Or scan its nursery tag.
2. **Care plan.** Check-based watering and feeding reminders. They start from the plant's care type, then **learn from what the user logs** ("still moist, skip" / "dry, watered") and, for outdoor plants, from the weather.
3. **Health check.** A guided symptom checklist, read against the plant's own log and light readings. Result: likely causes and what to try, never a "diagnosis".
4. **Ask.** An offline AI assistant that knows this plant's profile, log and readings.

**Signature: measured, not guessed, and offline.**
- Identification, OCR and the assistant all run **on the phone**.
- Light is **measured**: the Android light sensor, or an iOS camera-exposure estimate labelled as an estimate. Soil comes from an optional Bluetooth sensor (SHOULD).
- The care plan shows **why** each date moved: "Moved 2 days later: 14 mm rain yesterday (Open-Meteo)", or "You skipped twice; this plant now dries in about 9 days".
- No account, no subscription, no cloud of ours for the MUST scope.

**Claims we must not make** (all unverified; see §10):
- "the only offline plant identifier";
- "accurate diagnosis" / "plant doctor";
- "plants purify your air";
- any oxygen figure;
- "the first app with a light meter" (Planta is believed to have one [V-30]).

**No overlap in the portfolio.** I grepped every spec for `plant|lux|light meter|ml kit|tflite|ocr|bluetooth`. "plant" matched only CarDeal's "assembly plant", and no other app does plant care. Photriya estimates the colour temperature of light (Kelvin), not illuminance for plants; that is a different job. CodeDeal S1 uses on-device OCR for coupon screenshots, a different domain.

## 3. Architecture decisions (technical-architect)

**D1. On-device vision stack: ML Kit first, spike before committing.**
- **Context.**
  - OCR is requested as Google ML Kit text recognition [V-8].
  - The classifier is a TFLite model, e.g. AIY "plants V1" [V-1].
  - ML Kit's custom image labeling can run a TFLite classifier with metadata [V-9]. That would put both on one stack.
  - Known risk: Google's ML Kit iOS pods have historically lacked arm64 **simulator** slices [V-10]. On this Apple-silicon Mac that can block "build it and look at it".
- **Decision.**
  - Default: `google_mlkit_text_recognition` (Latin script, bundled model) and `google_mlkit_image_labeling` with a local custom model [V-9]. These are community Flutter plugins over Google's SDK [V-11].
  - **Spike 0a** (first task, ≤ half a day): build both for the iOS simulator and an Android emulator on this Mac, and run one label photo and one plant photo through them.
  - If the iOS simulator build fails, the documented fallbacks are:
    - OCR on iOS through Apple Vision `VNRecognizeTextRequest`, via a small method channel (the CodeDeal S1 pattern);
    - the classifier through `tflite_flutter` [V-12].
  - Android keeps ML Kit. **Founder's choice of ML Kit stands unless the spike fails, and the spike output is quoted in the commit.** No silent switch.
- **Consequences.** Bigger binary: measure it and report the IPA/AAB sizes in M12. New pods. See D6 for the Podfile.lock rule.

**D2. Offline LLM: a shared package `packages/agl_llm`, built from Verba's shim at `ef8be2c`.**
- **Options.**
  - (a) Copy the shim into PlantPulse.
  - (b) Shared package in `agl-manifest/packages/` next to `agl_ads`, `agl_i18n` and `agl_observability`.
  - (c) A pub.dev wrapper: `llama_cpp_dart`, `fllama` or `flutter_gemma` [V-13].
- **Decision: (b).**
  - Verba no longer owns the code, and a second app (Verba's founder question Q1) may want it back. So it belongs in `packages/`.
  - Create it as a Flutter **FFI plugin** (`flutter create --template=plugin_ffi agl_llm`) holding:
    - `src/agl_llama.{h,cpp}` (the `verba_llama_*` ABI renamed `agl_llama_*`);
    - `CMakeLists.txt`;
    - an iOS/macOS podspec that compiles the shim plus llama.cpp with Metal [V-14];
    - Dart `LlmEngine`, `LlamaEngine`, `ModelStore`, `ModelCatalog`.
  - llama.cpp (MIT [V-15]) is pinned to one release tag. It comes in as a git submodule, or as CMake `FetchContent` with the tag and hash written in the repo. Never "latest".
  - `agl_llama_is_real()` must return 1 in every release build. **A stub build must fail CI for any app that depends on `agl_llm`**: a test asserts `is_real()==1` on device builds, and a build-script check greps for `AGL_HAS_LLAMA`. The stub stays for host unit tests only.
  - The ABI test (`llama_bindings_abi_test.dart` at `ef8be2c`) moves into the package.
  - (c) is rejected: the licences and maintenance of those wrappers are unverified [V-13], and the founder asked to reuse the Verba approach.
- **Consequences.**
  - Android ships `libagl_llama.so` for arm64-v8a (plus x86_64 for the emulator). It must be **16 KB page-aligned** (Play rule "16 KB pages"; NDK r28+ aligns by default [V-16]). Verify with `zipalign -c -P 16` / `check_elf_alignment.sh` [V-16].
  - iOS links statically and opens it with `DynamicLibrary.process()`.
  - `scripts/store_policy_audit.py` `AI_CODE` (line 784) does not match `package:agl_llm/`. store-compliance adds it so the AI rules apply (§10).

**D3. Storage: files on the device, no database plugin.**
- **Data.** Plants, spaces, events and readings are a few thousand small records. Photos are files.
- **Decision.**
  - JSON documents under `getApplicationSupportDirectory()/journal/` (`plants.json`, `spaces.json`, `events.v1.jsonl`, `readings.v1.jsonl`). Writes are atomic: write temp, then rename.
  - Photos go in `journal/photos/<plantId>/<ts>.jpg`, re-encoded to ≤ 2048 px with EXIF stripped (M2).
  - Settings stay in `SharedPreferences` (the existing `AppStore` pattern).
  - New plugin: `path_provider` only. It is already a transitive dependency in most apps [V-17]; confirm in `pubspec.lock`.
- **Consequences.** No migrations framework. Keys are version-suffixed, as `app_store.dart` already does.

**D4. Network and keys.**
- MUST scope talks only to **keyless** hosts: GBIF, Open-Meteo (or MET Norway, see D5) and Hugging Face for the model download.
- Any secret or quota-bearing key (Pl@ntNet, Kindwise, Perenual) lives **only** in a Supabase Edge Function on project `smvvjivvlprjhzhoizym` (`supabase secrets set`), per `docs/API_VENDORS_AND_AFFILIATES.md` §4. A key in the binary can be extracted and its quota burned.
- The app calls the function with the project's public anon key, passed by `--dart-define`.
- PlantPulse has no accounts, so the function rate-limits per salted-hash IP per day plus a global daily cap. That needs a small table, which is a production migration and a founder approval (Charter §2).
- Add every new host to `docs/api-hosts.json` via `scripts/verify_api_hosts.py`.

**D5. Weather.**
- Open-Meteo is keyless and already used by daily-pulse and iMaps (`specs/daily-pulse.md:85`, verified 200 there on 2026-10-12).
- Its free API is, as I know it, **for non-commercial use**; commercial use needs a paid key [V-20]. AGL apps carry ads, so they are commercial. `store/vendors/registry.json` already says "Free (check commercial terms)".
- **Decision.** Build against a `WeatherSource` interface. Default implementation: Open-Meteo. Ready alternative: **MET Norway Locationforecast** (keyless, CC BY 4.0, requires an identifying `User-Agent`, commercial use allowed with attribution [V-21]).
- The founder decides (F2) whether to pay Open-Meteo or switch. A paid Open-Meteo key is secret, so it goes server-side.

**D6. Plugins and the Podfile.lock trap.**
- New plugins: `camera`, `image_picker`, `google_mlkit_text_recognition`, `google_mlkit_image_labeling` (or the D1 fallbacks), `flutter_local_notifications` + `timezone`, `connectivity_plus`, `share_plus`, `archive` (pure Dart), and `agl_llm`. SHOULD scope adds `flutter_reactive_ble`.
- All of these rewrite `ios/Podfile.lock`, which currently carries someone else's one-line edit.
- **Before the first iOS build, ask chief-of-staff to have its owner commit or revert it.** v2 must commit `Podfile.lock`, because new pods are real dependencies. Never commit someone else's line.
- Raise `platform :ios` (today `'16.0'`, `ios/Podfile:6`) only if ML Kit demands it [V-10].

**D7. No account, no sync.** Everything is on the device. Export (M2) is the way to move phones.

## 4. Data sources

| Data | Source | Key | Offline? | Notes |
|---|---|---|---|---|
| Species suggestion from a photo | Bundled TFLite classifier, AIY plants V1 [V-1] | none | yes | Label map = scientific names. Coverage of common houseplants is **unknown** [V-2] and is measured in M3 |
| Taxonomy, family, common names | GBIF API `api.gbif.org/v1/species/match`, `/species/{key}`, `/species/{key}/vernacularNames`, `/species/suggest` [V-4] | none | cached | Attribution and licence per GBIF terms [V-5] |
| Offline taxonomy for every model label | `assets/taxa.v1.json`, generated once by a new `agl-manifest/scripts/plant_taxa.py` from GBIF (label → usageKey, family, order, vernacular names in the 12 app languages where GBIF has them) | none | yes | Script lives in agl-manifest per the API rule in `../CLAUDE.md`. It needs web access, so it waits on founder decision F15 |
| Care starting values | Bundled `assets/care_types.v1.json`: about 10 care types (§M5), each with **cited** sources | none | yes | Values in this spec are drafts [V-C] |
| Weather (outdoor spaces only) | Open-Meteo forecast `daily=precipitation_sum,temperature_2m_max,temperature_2m_min,et0_fao_evapotranspiration&past_days=2&forecast_days=3&timezone=auto` [V-19] + geocoding search; or MET Norway (D5) | none (free tier) | cached 6 h | Coordinates rounded to 0.1° before sending |
| Season / day length | Computed locally from latitude and date | none | yes | — |
| Light | Android `Sensor.TYPE_LIGHT`; iOS camera exposure (ISO, exposure duration, aperture) → EV → lux **estimate** | none | yes | M7 |
| Label text | ML Kit text recognition, on-device [V-8] | none | yes | M4 |
| Assistant | `agl_llm` + a GGUF model downloaded from Hugging Face, e.g. Qwen2.5-1.5B-Instruct Q4_K_M (about 1.1 GB per Verba's `ef8be2c` catalogue; Apache-2.0 [V-23]) | none | yes, after download | M8 |
| Online second opinion (SHOULD) | Pl@ntNet API via Edge Function [V-6] | secret, server-side | no | S1 |
| Soil readings (SHOULD) | Flower Care-type BLE sensor (HHCC / "Mi Flora" HHCCJCY01 [V-26]) | none | yes | S2 |
| Journal | On-device files (D3) | — | yes | M2 |

**Nothing is seeded.** A fresh install has no plants and no invented readings, and says so with a real empty state.

---

## 5. MUST (12): buildable now with no paid service

Order: **Spike 0** (D1 and D2 spikes) → M1 → M2 → M3/M4 → M5 → M6/M7 → M8 → M9 → M10 → M11 → M12.

### M1. Retire the remote (code-hygiene) and start clean

**Remove** from `mobile/lib`, and every test that tests only that code, in the **same commit**, each file listed in the commit message:
- `features/{roku,wled,scan,scenes,devices,history}/*`;
- `services/{lan,lan_scanner,legacy_migration,roku_ecp_transport,wled_transport,webhook_transport,device_transport,scene_runner,setup_transfer}.dart`;
- `models/{device,roku,wled,scene,remote_command}.dart`;
- `widgets/{d_pad,rocker,color_wheel,glow_slider,glyphs,deck_widgets,line_art}.dart`;
- `tool/lan_harness.py`.
- **Tests:** `test/fixtures/doc_samples.dart`, `test/models/*`, `test/services/{command_rollback,devices_controller,history_filter,lan_scanner,lan,scene_runner,setup_transfer,transport,device_repository}_test.dart`, and `test/widgets/{history_page,lights_page,scan_page,scene_flow,tv_remote_page}_test.dart`.
- Tests that mix remote and generic behaviour are **rewritten**, not deleted: `app_smoke_test.dart`, `foldable_layout_test.dart`, `home_page_test.dart`, `ads_placement_test.dart`, `identity_test.dart`, `source_grep_test.dart`. `l10n_test.dart` keeps its rules unchanged.

**Platform files:**
- Remove `NSLocalNetworkUsageDescription` and `NSAppTransportSecurity › NSAllowsLocalNetworking` (`Info.plist:303-311`).
- Remove `android:networkSecurityConfig` and `res/xml/network_security_config.xml`. Everything is HTTPS now.
- Keep `INTERNET`.
- Remove the portrait lock in `main.dart`. Its reason was the handset layout. iPad must support all orientations (2.4.1).

**Strings:** delete every `deck`/Roku/WLED/scene/webhook key from all 12 ARBs and regenerate l10n.

**Old data:** on first v2 launch, delete the `deck.*` and `omnicontrol.*` SharedPreferences keys. They hold internal testers' device IPs and webhook URLs. No migration and no note: no production user exists (§0).

**Keep and re-theme:**
- `core/haptics.dart`;
- `widgets/tactile.dart`, the generic press physics;
- `widgets/adaptive.dart`, with the icons renamed and replaced;
- `services/app_store.dart`, the settings-only prefs pattern;
- the startup in `main.dart` (`AglCrash.runGuarded`, AdMob ids `ca-app-pub-8528784688453695~9438850163` / `~1504519820`);
- the structure of the l10n, crash-reporting and identity tests.

**Not reusable:** the web prototype at the repo root (`client/`, `server/`, `drizzle/`). It is the Manus tRPC template behind "OmniControl" (`README.md:1`). Leave it untouched; deleting it is a separate hygiene item.

**Acceptance:**
- `grep -rniE "roku|wled|webhook|scene|keypress|8060|json/state|couchdeck|deck\.|lan_scanner|LocalNetwork" mobile/lib mobile/ios/Runner/Info.plist mobile/android/app/src/main` → 0. One exception: the one-time key-cleanup literal, `deck.` prefix only.
- `flutter analyze` is clean.

### M2. Plant journal (the data foundation)

**Model:**
- `Space {id, name, kind: indoor|outdoor|balcony, lightBand?}`.
- `Plant {id, nickname, taxonKey?, scientificName?, commonName?, careType, spaceId, potDiameterCm?, potHasDrainage?, acquiredOn?, tender (frost-sensitive) bool, coverPhotoId?, notes, createdAt, updatedAt}`.
- `Event {id, plantId, at, type: watered|checkedMoist|fed|repotted|pruned|treatedPests|moved|photo|note|health|measurement, payload}`.
- `Reading {id, plantId|spaceId, at, kind: lux|soilMoisture|soilEc|soilTemp, value, unit, source: androidSensor|iosCameraEstimate|bleSensor(name)}`.

**Screens:**
- **Plants:** search over nickname and scientific/common name; filter by space, "needs a check", care type.
- **Plant detail:**
  - cover photo;
  - names, with the scientific name in italics;
  - care strip (water / feed / light, each with the next date and the reason);
  - **timeline**: photos and events by date;
  - latest readings;
  - health entries;
  - **Ask about this plant**.
- **Photo timeline:** a grid by date, plus SHOULD S10 to compare two dates side by side.
- **Log:**
  - one-tap Water / Skip (moist) / Feed from Today and from detail;
  - a long form for the other event types.

**Photos:**
- Captured with `camera` / `image_picker` (camera, or the system photo picker: PHPicker on iOS, the Android Photo Picker). So the app declares **no** `READ_MEDIA_IMAGES` and asks for no photo-library permission [V-18].
- Re-encoded on save with EXIF removed. This drops location tags even on device, so an export cannot leak them.

**Export:**
- Settings › Export journal → share sheet with `plantpulse-journal-<date>.zip` containing:
  - `journal.json` (`{"format":"plantpulse-journal","version":1,…}`);
  - `events.csv`;
  - `photos/`.
- Import is SHOULD S7.

**Delete everything:** Settings, behind a confirmation. It removes files, prefs and the downloaded model.

**Acceptance:**
- Unit tests: JSON round trip for every type; atomic write survives a simulated crash (temp file left over → ignored); corrupt file → empty plus a visible "Couldn't read your journal file" with **Export what's readable**, never a crash; search and filters; zip contents and CSV columns.
- A test asserts that a photo saved with an EXIF GPS block comes back with none (fixture JPEG with GPS).

### M3. Identification, offline first, no invented answers

**Model:**
- Bundle AIY plants V1 TFLite with its label map [V-1]. Recorded and quoted in the commit: input 224×224, quantised uint8, about 2,100 classes, licence Apache-2.0 per TF Hub/Kaggle [V-1]. Also bundle `assets/taxa.v1.json` (§4).
- **Spike 0b** prints and quotes:
  - class count;
  - the background class index;
  - asset size;
  - how many labels resolve in GBIF;
  - how many fall in typical houseplant families (Araceae, Asparagaceae, Moraceae, Cactaceae, Crassulaceae, Orchidaceae, Marantaceae, Polypodiopsida).
  - It is trained on iNaturalist wild observations [V-2]. If cultivated houseplants turn out poorly covered, the product copy says "plants and trees", not "houseplants", until a better-licensed model is found (founder question F17).

**Flow:**
- Camera with an organ hint ("leaf / flower / whole plant / bark") → classify on device → top 5.
- **Result rules:** constants in one file, starting values to be tuned on the evaluation set below.
  - **Likely:** top-1 ≥ 0.60 and top-1 − top-2 ≥ 0.15. Shows "Likely *Monstera deliciosa* · 72% model confidence · on this phone", plus 2 alternatives.
  - **Not sure:** 0.30 ≤ top-1 < 0.60, or the margin is too small. Shows "Not sure. It could be one of these" with the top 3 as choices, each with a GBIF photo link when online. **Nothing is pre-selected.**
  - **Can't tell:** top-1 < 0.30, or top-1 is the background class. Shows "I can't identify this plant from this photo", with tips (one leaf or flower, in focus, in daylight), **Search by name** and, if S1 is built, **Ask Pl@ntNet (online)**.
- **Never saved without the user tapping a species.** The confidence label always reads "model confidence", never "accuracy".
- **Search by name:** offline over the label map plus cached common names; online via GBIF `species/suggest`.
- **On confirm:** GBIF `species/match?name=<sci>&strict=true` fills family and vernacular names in the app language and caches them. Offline, `taxa.v1.json` fills them. Attribution in Settings › Sources: "Taxonomy: GBIF Backbone Taxonomy" [V-5].

**Evaluation (honest numbers only):**
- A human photographs ≥ 30 real plants of known species (F9). They go in `mobile/tool/eval/`, never bundled.
- `tool/eval_classifier.dart` reports top-1/top-3 hit rate and the share landing in each branch.
- The numbers go in the commit message and the QA report. **They are never used in store copy.**

**Acceptance:**
- Unit tests for the three branches at the boundaries (0.299/0.30/0.599/0.60, margin 0.149/0.15) and the background class.
- A widget test with a fake classifier for each branch; "Not sure" pre-selects nothing.
- `source_grep_test`: no "accurate", "100%", "guarantee" or "diagnos" in `lib/` or the ARBs.

### M4. On-device OCR for plant tags and fertiliser labels

**Scan label** (from Add plant, Plant detail › Feeding, and Log › Fed):
- camera or photo picker → ML Kit text recognition, Latin, bundled model, on device [V-8] (or the D1 fallback);
- raw text plus parsed **chips** the user confirms or edits.

**Parsers** (pure Dart, unit-tested):
- **N-P-K:** `10-10-10`, `NPK 20-20-20`, `N-P-K 3-1-2`, `N 3% P 1% K 2%`, `3–1–2` with an en dash. Rejects dates and phone numbers. This happens only when the user is on a fertiliser screen.
- **Botanical name:** a capitalised genus plus a lowercase epithet, optional cultivar in quotes (`Ficus elastica 'Tineke'`), validated against the label map or `taxa.v1.json`, or GBIF match when online.
- **Care symbols in text:** "full sun", "partial shade", "keep moist", pot size "12 cm" / "5 in".
- **Dose text:** stored **verbatim** as the user confirmed it ("1 tsp per gallon every 2 weeks"). **The app never computes or rescales a dose.**

**Saves to:**
- the plant profile (name, light hint, pot);
- a **Feeding product** `{name, npk, form: liquid|granular|slow-release|stick, labelDoseText, labelPhotoId}`, reused across plants.

**Acceptance:**
- Parser tests with ≥ 25 label strings typed from real labels a human photographs (F9). Strings, not invented examples, with negatives (dates, barcodes, phone numbers).
- A widget test that confirming chips writes the plant and product.
- On-device run: one real tag and one real fertiliser label on the iOS simulator (photo-library image) and on the Android emulator, screenshots in the QA report.

### M5. Care plan: water, feeding, light, reminders

**Care types** in `care_types.v1.json`:
- cactus;
- succulent;
- tropical foliage / aroid;
- fern;
- epiphytic orchid;
- flowering houseplant;
- herb;
- palm;
- potted citrus / fruit;
- outdoor established shrub or tree (weather-driven only);
- vegetable / annual.

**Each type has:**
- `waterWhen` text (e.g. "top 2–3 cm dry");
- starting check interval for summer/winter in days;
- min and max interval;
- feeding months and frequency;
- dormant flag;
- light band (low / medium / bright indirect / direct sun) with a lux range;
- `sources[]`.

Draft starting intervals (summer/winter, days) are **[V-C] and must be checked against cited horticultural sources** (university extension publications) before shipping:

| Care type | Summer | Winter |
|---|---|---|
| cactus | 14 | 28 |
| succulent | 10 | 21 |
| aroid | 7 | 12 |
| fern | 4 | 7 |
| orchid | 7 | 12 |
| flowering | 5 | 9 |
| herb | 3 | 5 |
| palm | 7 | 12 |
| citrus | 5 | 10 |

A care type ships only with `sources` filled.

**Choosing a type:**
- Suggested from the GBIF family with the reason shown: Cactaceae → cactus, Crassulaceae → succulent, Araceae → aroid, Orchidaceae → orchid, Polypodiopsida → fern, Arecaceae → palm.
- "Suggested because it's in the cactus family. Change it" (one tap).
- Unknown family → the user picks.

**Reminders are checks, not commands.** "Check Fern's soil" with **Dry → watered** / **Still moist → skip**.

**Learning:**
- Dry → watered records the observed interval: `estimate = round(0.7·estimate + 0.3·observed)`, clamped to [min, max].
- Moist → skip postpones by `ceil(0.3·estimate)` days and nudges the estimate up.
- Detail shows "Usually dries in about 9 days (learned from 4 checks)".

**Season:**
- Northern or southern hemisphere from the space's latitude; the user's city is required only for outdoor spaces or seasons, otherwise taken from the device locale's region with an override.
- Summer/winter values apply in their months.
- The feeding months flip for the southern hemisphere.

**Weather** (outdoor/balcony spaces only, `WeatherSource`, D5). Each rule writes a visible reason line with its source:
- rain ≥ 10 mm in the last 48 h → check postponed 2 days;
- forecast max ≥ 30 °C → check 1 day earlier;
- forecast min ≤ 2 °C in the next 48 h and the plant is `tender` → frost alert (opt-in).
- Offline or failed fetch → no adjustment, with "Weather not checked: offline". Never stale data presented as current.

**Location:** a city typed into Open-Meteo geocoding (keyless). Store the name and coordinates rounded to 0.1°. **No location permission in MUST** (S9 adds "use my location").

**Feeding:** a reminder in feeding months only: "Feed Monstera: <labelDoseText>". If no product has been set: "Feed per your fertiliser's label".

**Notifications:**
- `flutter_local_notifications`, **off until the user turns reminders on** (opt-in screen, then the OS prompt).
- One daily digest at a user-chosen time ("3 plants to check: Fern, Pilea, Basil"), not one per plant.
- **Inexact** scheduling (`AndroidScheduleMode.inexactAllowWhileIdle` [V-24]). **No `SCHEDULE_EXACT_ALARM` / `USE_EXACT_ALARM`.**
- Rescheduled on app open. `RECEIVE_BOOT_COMPLETED` only if the plugin requires it [V-24].
- No remote push.

**Acceptance:**
- Unit tests with a fake clock and recorded weather fixtures (JSON shaped like the vendor docs, cited in the fixture header): smoothing and clamps, skip postponement, hemisphere flip, each weather rule and its reason text, offline case, digest grouping.
- A test asserts the merged release manifest has no exact-alarm permission.
- A widget test for the opt-in path; denial leaves the app fully usable with "Reminders are off".

### M6. Health check: honest about uncertainty

**Guided checklist**, 4 steps, each skippable:
1. **Where:** new leaves / old leaves / whole plant / stems at soil / undersides.
2. **What:**
   - yellowing;
   - brown crispy tips or edges;
   - brown or black soft spots;
   - mushy stem base;
   - white powder;
   - sticky residue;
   - fine webbing;
   - small insects (flying / crawling);
   - wilting;
   - leaf drop;
   - pale, stretched growth;
   - holes.
3. **Soil right now:** dry / moist / wet / don't know (or the latest BLE reading, S2).
4. **Recent changes:** moved / repotted / new plant / none.

**Rules engine.** `assets/health_rules.v1.json`, each rule with `sources[]` [V-C]. It combines the answers with **the plant's own log and readings**:
- days since watering;
- the learned interval;
- latest lux vs the care type's band;
- pot drainage;
- season.

Output: **up to 3 "possible causes"**, each with the evidence used and "what to try":
> **Possible cause: too much water.** Why: soil is wet, watered 2 days ago, usually dries in 9 days, pot has no drainage hole. **Try:** let the top 3 cm dry before watering; check roots for brown, soft sections; move to a pot with drainage.

**Copy rules:**
- Header: "Possible causes, not a diagnosis."
- Pests are named only at the group level ("spider mites or similar", "scale or mealybugs"), with "inspect leaf undersides with a magnifier".
- Treatments name no product and no dose beyond "follow the product label".
- No human or pet medical statements.

**Saved** as a `health` event with an optional photo. A follow-up check reminder after 7 days asks "Better, same, worse?". Health history sits on Plant detail.

**On-device leaf-disease model: not in MUST.** PlantVillage-style models cover mostly **crops** (about 14 species such as tomato, potato, grape and apple) on lab backgrounds and are known to degrade on field photos [V-27]. They say nothing about houseplants. See S5.

**Acceptance:**
- Unit tests: each rule fires on its fixture and stays silent otherwise; at most 3 causes, ordered by matched evidence; the evidence text names the real log values.
- `source_grep_test` bans `diagnos(is|e|ed)` everywhere except the one string "not a diagnosis", plus `cure`, `guarantee`, `vet`, `doctor`.

### M7. Measurements the phone can honestly provide (and no oxygen)

**Light meter** (Plant detail › Measure light, or Space › Measure):
- **Android:**
  - `Sensor.TYPE_LIGHT` through a small `EventChannel` in the app (no plugin).
  - Median of 3 s of samples.
  - Shown as "1,240 lx · phone light sensor".
  - Devices without the sensor fall back to the camera estimate.
- **iOS:**
  - There is no public ambient-light API, so it uses a camera **estimate**: a front-camera preview held at leaf height, screen up.
  - A method channel reads `AVCaptureDevice` `iso`, `exposureDuration` and `lensAperture` → EV100 → illuminance with one calibration constant [V-28].
  - Shown as "≈ 1,200 lx · **estimate** from the camera" and rounded to 2 significant figures.
  - Before calibration is verified on a device against a reference lux meter (F8), the UI shows **only the band** (low / medium / bright indirect / direct sun), not the number.
- **Saved** as a `Reading`. Compared with the care type's band: "Below what aroids usually like (bright indirect)."
- **Acceptance:**
  - Unit tests: EV and lux math against hand-computed values; band mapping at the edges; median filter.
  - A widget test with a fake sensor stream.
  - A test that iOS copy always contains "estimate".

**Phone capabilities.** What the spec allows the app to show, and why:

| Quantity | Shown? | Why |
|---|---|---|
| Illuminance | yes | Android sensor, or iOS camera estimate |
| Soil moisture, soil temperature, soil EC, light at the plant | only from a BLE sensor (S2) | The phone cannot measure them |
| Air temperature / humidity | no | Phone sensors for these are rare and read the phone, not the room |
| pH | no | No phone or Flower Care-type sensor measures it [V-26] |
| **Oxygen / CO₂** | **never** | No phone or these sensors can measure it. Showing a value would be a false feature (Apple 1.1.6 / 2.3.1, Play Deceptive behavior) |

**Oxygen** gets one FAQ entry only, under Settings › How measurements work:
> Why doesn't PlantPulse show oxygen? Phones and plant sensors can't measure oxygen, and figures for how much oxygen a houseplant makes are estimates we won't present as readings.

- Also **no "air purifying" claims** anywhere, in the app or the store.
- **Acceptance:** `source_grep_test` bans `oxygen|\bO2\b|O₂|CO2|CO₂|purif|clean air` in `lib/`, the ARBs and `store/apps/PlantPulse.json`. Allowed: only the ARB keys `faqOxygenTitle` / `faqOxygenBody`.

### M8. Offline AI assistant (agl_llm)

**Package:** `packages/agl_llm` per D2. Real llama.cpp on iOS (Metal [V-14]) and Android arm64.

**Model catalogue:**
- Default: Qwen2.5-1.5B-Instruct Q4_K_M, about 1.1 GB.
- Low-RAM: Qwen2.5-0.5B-Instruct Q4_K_M, about 0.4 GB.
- Both Apache-2.0 [V-23], from Hugging Face direct URLs (as in Verba `ef8be2c`), unless the founder chooses our own hosting (F3).
- **`sha256` and byte size filled in from the downloaded files** and checked after download. The empty digests from Verba are not acceptable.

**Download:**
- Only after an explicit sheet: "Download the assistant: 1.1 GB, Wi-Fi only, stays on this phone".
- Wi-Fi only via `connectivity_plus`; it pauses on leaving Wi-Fi.
- Resumable with HTTP Range into `.part`, renamed only after the digest matches.
- Stored in Application Support and **excluded from iCloud backup** (`NSURLIsExcludedFromBackupKey` via a channel [V-25]).
- Foreground only, so no foreground service and no background mode.
- RAM gate: physical memory via a channel. Below the model's `minRamMb`, offer the smaller one or explain.
- Deletable in Settings, with its size shown.

**Without the model:** the Assistant shows the download card and what it will do. **The rest of the app is complete without it.** There is no cloud fallback and no canned "AI" text.

**Grounding.** Every request carries a system prompt plus a **plant card** built from the journal:
- names, care type and `waterWhen`;
- learned interval;
- last 10 events;
- latest readings with source and date;
- latest health check result;
- weather reason lines;
- the care-type text.

Budget: 2,048 context tokens, max 256 reply tokens, temperature 0.3. Small models are weak, so the grounding text does the work.

**Scope rules:**
- Plant care only.
- Fixed **app messages, not model output**, for:
  - toxicity or edibility for people or pets → "I can't answer whether a plant is safe to eat or touch. Check a poison-control service or the ASPCA toxic and non-toxic plant list", with a link [V-29];
  - pesticide dosing → "follow the product label";
  - human or animal health.
- A keyword pre-check routes these before the model runs; a post-filter blocks offensive output (word list) and replaces it with "I can't help with that".

**Labels:**
- Every model message carries "AI · on this phone · can be wrong".
- A one-time notice on first use.
- **Report this message** on each AI message (Play AI-generated content; the wording also matches `apple_requirements.py:276` `REPORT`). Reporting:
  - hides the message;
  - saves it locally;
  - offers **Email it to us**: a user-initiated `mailto:contact@americangroup.ai`, prefilled with the message text only. No photos, no journal.
  - Whether email reporting satisfies Play is [V-31].

**History:** per plant, on device; clear per plant or all. The assistant does not see photos (text model) and never says it does.

**Acceptance:**
- Package tests: ABI test; digest mismatch rejects and deletes `.part`; resume from an offset; Wi-Fi gate; `is_real()==1` asserted in an integration test on a device build.
- App tests:
  - plant-card builder output (golden text);
  - routing of toxicity, dosing and medical questions to the fixed messages without calling the engine (fake engine records zero calls);
  - every AI bubble has the label and the report control.
- **On device:** iPhone (physical, F9) and the Android emulator (x86_64, or an arm64 device). Download, ask "When should I water this?" for a real journal plant, and quote the answer and tokens/s in the QA report. Not verified until then.

### M9. Own identity

- **Name:** `kAppName = 'iPlantPulse'` stays (App Store 409 on "PlantPulse"). Store name proposal in §10.

**Palette "Potting bench".** Hand-built `ColorScheme`, `ThemeMode.system`.
- **Light:**
  - surface `#EFF0E4`;
  - card `#FBFBF5`;
  - text `#1C2419`;
  - **primary leaf `#2F5E3C`** (on `#FFFFFF`);
  - secondary terracotta `#9A4A2C` (on `#FFFFFF`);
  - water `#2D5F7A`;
  - feed `#7A5A12`;
  - danger `#9E1F2A`;
  - muted `#535C4E`.
- **Dark:**
  - surface `#121611`;
  - card `#1B2119`;
  - text `#E7EBDD`;
  - primary `#8FC79A` (on `#121611`);
  - terracotta `#E39A79` (on `#121611`);
  - water `#8CC2DF`;
  - feed `#D9B65C`;
  - danger `#F08A8F`;
  - muted `#A3AC9B`.
- **Contrast**, computed 2026-10-14 with the WCAG relative-luminance formula (script `/tmp/pp_contrast.py`):
  - Light: text/surface 13.87, text/card 15.37, on-primary/primary 7.53, primary/surface 6.55, primary/card 7.25, on-secondary/secondary 6.19, secondary/card 5.96, water/card 6.67, feed/card 6.13, danger/card 7.54, muted/surface 6.07, muted/card 6.72.
  - Dark: 15.08, 13.55, 9.41, 9.41, 8.45, 7.98, 7.17, 8.53, 8.45, 6.84, 7.78, 6.99.
  - Assert all ≥ 4.5 in a test.
- **Uniqueness:** `grep -rIoiE` of all 18 hexes over `/Users/spatchava/agl` (`*.dart`, `*.md`, `*.json`, `*.xml`, excluding SDK and build output) → 0 hits.

**Typography:**
- **Gelasio** (variable weight, plus its italic) for headings and every scientific name, in italics.
- **Commissioner** (variable) for UI, with `FontFeature.tabularFigures()` on readings and dates [V-32].
- Bundled under `assets/fonts/` with `OFL.txt`, no `google_fonts`. Downloading them waits on F15.
- Portfolio check:
  - "Gelasio": `grep -rlI` over `*.dart`, `*.md` and `pubspec.yaml` → 0 hits.
  - "Commissioner": hits only the English word in 3 compliance and civics files, and no `family:` in any pubspec.
- **Remove** Saira and Space Mono, the remote's fonts.

**Shape language: "nursery tag".**
- Plant cards are tall tags with 4 px corners and a punched hole (a 6 px circle) top-centre.
- Chips are pills.
- Sheets have 4 px corners.
- No keycap bevels (remove the `bevel`/`highlight` tokens).

**Home = "Today on the bench"**, one scroll, **no bottom tab bar**:
1. App bar: iPlantPulse, Assistant, Settings.
2. **Needs a check today**: rows with photo, nickname, italic Latin name, reason, and **Dry → watered** / **Still moist** buttons.
3. **Spaces**: horizontal shelves of plant tags per room or garden.
4. A pinned **Identify** pill (camera) at the bottom centre.
5. The single banner at the end of the scroll (M10).

Empty Home: "Add your first plant. Take a photo, scan its tag, or type its name", with three buttons.

**Onboarding** (3 pages, once, Skip on each, re-openable from Settings):
1. "Know your plant, even offline."
2. "Care that learns how fast your plants dry."
3. "Measure light, don't guess."

Final button: **Add your first plant**. Line art is `CustomPainter` in the palette.

**iOS feel:** Cupertino transitions, icons and adaptive controls, extending `adaptive.dart`.

**Icon and splash:**
- Rewrite `tool/make_brand_assets.py` (hand-drawn with PIL): a cream nursery tag `#FBFBF5` with one leaf in `#2F5E3C` and a terracotta hole ring, on `#121611`.
- Regenerate all AppIcon sizes and Android mipmaps.
- New `LaunchScreen.storyboard`, `#121611` plus the mark.
- Ask store-compliance to remove `scripts/generate_app_icons.py:83` and `scripts/generate_launcher_icon.py:43` (`"PlantPulse": ("#1E40AF", "OC")`) so a rerun cannot overwrite the icon.

**Acceptance:** `identity_test` covers fonts on disk and declared, palette contrast, the storyboard shasum differing from today's, display name = `kAppName`, and no remote palette hex (`ECE8DF|A8431A|2F5D50|141311|…` → 0).

### M10. Privacy, permissions, ads, in-app policy link

- **Settings › What leaves this phone** (rewritten to match §8 exactly).
- **Settings › Privacy policy** link to `https://www.americangroup.ai/policy/plantpulse/`. This fixes the 5.1.1(i) and Play User Data FAILs. The page text is legal, so it is drafted and goes to the founder (F10).
- **Settings › Sources:** GBIF, the weather provider, AIY model licence, model licence, llama.cpp licence, font OFLs (via `LicenseRegistry`).
- **Purpose strings** (also in all 12 ARB/InfoPlist localisations if the app localises plist strings):
  - `NSCameraUsageDescription`: "Takes photos of your plants to identify them, read plant tags and fertiliser labels, and estimate light. Photos stay on this iPhone unless you choose to send one for an online second opinion."
  - No `NSPhotoLibraryUsageDescription` if the PHPicker path needs none. **Spike 0a checks** whether Apple's static scan of the `image_picker` binary requires it [V-18]. If it is required, add "Lets you choose plant photos you already took."
  - No location, Bluetooth or local-network strings in MUST.
- **Android permissions:**
  - `CAMERA` (from the plugin);
  - `INTERNET`;
  - `ACCESS_NETWORK_STATE`;
  - `POST_NOTIFICATIONS`, requested at reminder opt-in;
  - `RECEIVE_BOOT_COMPLETED` only if required.
  - **None of:** `READ_MEDIA_*`, location, exact alarms, foreground service.
  - The audit's merged-manifest check confirms this.
- **Ads:**
  - Exactly **one `AglAdBanner`**, at the end of the Today scroll.
  - None on the camera, identification results, OCR, health check, light meter, assistant or onboarding.
  - **No interstitial**: remove the `AglAds.onTransition()` call (`home_page.dart:32`) pending F12.
  - `ads_placement_test` asserts this.
- **PrivacyInfo.xcprivacy:** keep CrashData and OtherDiagnosticData. Add nothing for MUST: photos, journal and chat never leave the device, and weather requests carry rounded coordinates the app does not collect. privacy-engineer confirms with `scripts/testflight/privacy_scan.py`. The required-reason APIs are re-derived from the new IPA (ITMS-91053).

### M11. Store artefacts written (store-compliance applies them)

- `store/apps/PlantPulse.json` gets the copy in §10 and the differentiation answers 1–3 and 6. 4 and 9 stay founder items.
- Review notes are rewritten for this app (§10). The `_drafted` warning and the remote text are removed.
- `store/privacy/PlantPulse.json` becomes its own label (§8).
- `docs/console-answers/PlantPulse.md` gets the Data safety answers (§8).
- The office does not touch the dirty fastlane files until their owner commits (§0).

### M12. Proven

- `flutter analyze` clean; `flutter test` all green, with the count reported against the baseline taken at the v2 start commit. Deleted tests are listed (M1).
- New tests: everything in M2–M10 acceptance.
- `cd packages/agl_llm && flutter test` is green.
- **Look at it.** Fresh install on the iOS simulator (iPhone and iPad 13") and the Android emulator. Screenshot:
  - onboarding;
  - empty Today;
  - Add plant;
  - identification in each of the 3 branches (simulator photo library with F9's real photos);
  - label scan;
  - care plan with a reason line;
  - health check result;
  - light meter (the Android emulator's virtual light sensor; iOS shows the camera-unavailable state on the simulator);
  - assistant download card;
  - dark mode.
  - No white screen, no overflow at text scale 2.0.
- **On a physical iPhone and Android phone** (F9): camera identification, iOS light estimate, assistant answer. Until then, reported as **not verified**.
- Re-run `python3 scripts/store_policy_audit.py PlantPulse` and `scripts/apple_requirements.py`. Quote the counts; no FAIL may remain that M1–M11 cover.
- Report IPA and AAB sizes, and 16 KB alignment of every `.so`.
- **Commit path-limited** (`git add mobile/lib mobile/test mobile/integration_test mobile/assets mobile/tool mobile/pubspec.yaml mobile/pubspec.lock mobile/ios/Runner mobile/android/app`). Plus `mobile/ios/Podfile.lock` **only after** the other edit is resolved (D6). Never `fastlane/`. Push to `main`.
- Update `integration_test/store_screenshots_test.dart` to the new flow, or say in the commit that it was not updated.

---

## 6. SHOULD (in order)

- **S1. Online second opinion via Pl@ntNet.**
  - Edge Function `plant-identify`, secret `PLANTNET_API_KEY`.
  - Pl@ntNet `v2/identify/{project}` with up to 5 images plus organs [V-6]. Free tier believed to be 500 identifications per day [V-6].
  - The app sends JPEGs **re-encoded with EXIF stripped, ≤ 1280 px**, only after a per-use sheet: "Send this photo to Pl@ntNet for an online opinion? It leaves your phone." The function stores no image.
  - Results are shown side by side with the on-device result, attributed "Pl@ntNet" [V-7].
  - Daily global cap below the free limit; a salted-IP daily limit (D4). When the cap is reached: "Online ID is busy today. On-device ID still works."
  - Needs F4 and F5.
- **S2. Bluetooth soil sensors (Flower Care-type).** `flutter_reactive_ble` (BSD-3 [V-33]; `flutter_blue_plus` licence terms changed, [V-33]).
  - Scan by name "Flower care" or service data 0xFE95 (MiBeacon). Connect, write `0xA0 0x1F` to `00001a00-…`, read 16 bytes from `00001a01-…`:
    - temperature int16 LE ÷10 °C;
    - light uint32 LE lux;
    - moisture %;
    - conductivity uint16 LE µS/cm.
  - Firmware and battery from `00001a02-…`.
  - **All community reverse-engineered, not vendor-documented [V-26].**
  - Shown as "Soil moisture 18% · Flower care sensor · 10:42". Conductivity is labelled "Soil salts (EC), a fertiliser-level indicator", **never "fertility %"**.
  - Learns a personal watering point from moisture at "Dry → watered" logs.
  - Permissions:
    - iOS `NSBluetoothAlwaysUsageDescription`: "Reads soil moisture, temperature and light from plant sensors you pair."
    - Android 12+ `BLUETOOTH_SCAN` (with `neverForLocation` only if MiBeacon adverts are not filtered by it [V-34]) and `BLUETOOTH_CONNECT`.
    - Android ≤ 11 `ACCESS_FINE_LOCATION` with `maxSdkVersion="30"`, plus a prominent disclosure before the prompt.
  - No "Xiaomi" or "Mi Flora" in the name, icon or screenshots. Description only: "works with Flower Care-type sensors (HHCCJCY01)" [V-26].
  - Needs hardware (F8).
- **S3. Kindwise plant.id identification and health assessment.** Paid, with free trial credits [V-35]. Same Edge Function pattern, secret `KINDWISE_API_KEY`. Founder money decision (F6).
- **S4. Perenual care enrichment.** Free key believed to allow about 100 requests per day, with species IDs 1–3000 only [V-36]. Server-side `PERENUAL_API_KEY` with a cache table. Shown as "Perenual says…" next to our care type, never silently overriding the user's learned interval. Commercial terms [V-36]. Needs F7.
- **S5. On-device leaf-disease model for edible crops only** (tomato, potato, pepper, grape, apple…) when the identified species is in the model's list. PlantVillage licence and model licence [V-27]. Labelled "trained on lab photos of crop leaves".
- **S6. Daily light integral estimate** from repeated readings, with a light-source selector [V-28].
- **S7. Import a journal export** (`file_picker` makes Apple 2.5.15 applicable).
- **S8. Home-screen widget** "Plants to check today" (makes 2.5.16 / 4.4 applicable; no ads in the widget, 2.5.18).
- **S9. "Use my location"** for outdoor spaces: when-in-use, coarse only. iOS `NSLocationWhenInUseUsageDescription`; Android `ACCESS_COARSE_LOCATION`. Makes 5.1.5 applicable.
- **S10. Compare two photos** of a plant side by side.

## 7. Out of scope

- Accounts, cloud sync, sharing or community feeds (that would add 1.2 UGC).
- Any cloud LLM.
- Oxygen, CO₂, pH or air-quality figures.
- "Air purifying" content.
- Pest identification to species.
- Pesticide dose calculators.
- Toxicity databases (link out only).
- AR plant measurement (iMeasure's job).
- Paid subscriptions or IAP.
- Selling plants, or affiliate links.
- Smart-plug or irrigation control.
- Desktop or web.
- The repo-root web prototype.

## 8. Privacy and security (privacy-engineer)

**Data inventory, v2 MUST:**

| Data | Source | Stored | Leaves device? | To whom | Label |
|---|---|---|---|---|---|
| Plant photos | camera / photo picker | app files, EXIF stripped | **No** (S1: only on explicit send) | S1: our Edge Function → Pl@ntNet | MUST: none. S1: Photos, App Functionality, not linked, if Pl@ntNet retains images [V-7] |
| Label photos and OCR text | camera | app files | No | — | none |
| Journal (plants, events, readings, chat) | user | app files | No (export is user-initiated share) | — | none |
| City / rounded coordinates (0.1°) | typed city | prefs | Yes, in weather requests | Open-Meteo or MET Norway | Not collected by us; the third party's retention is [V-20]/[V-21]. Conservative option: declare Coarse Location, App Functionality, not linked |
| Species names | user's confirmed ID | app files | Yes, GBIF lookups | GBIF | none (not personal) |
| IP address | network | — | to GBIF, weather, Hugging Face (model download), AdMob, Crashlytics | — | covered by the SDK rows |
| Crash reports | Crashlytics | — | Yes | Google | CRASH_DATA, App Functionality, not linked (existing) |
| Ads identifiers | AdMob | — | Yes | Google | DEVICE_ID + ADVERTISING_DATA, Third-party advertising, not linked (existing). UMP before ads; no ATT |
| BLE sensor id (S2) | sensor | prefs | No | — | none |

**App Privacy label** (`store/privacy/PlantPulse.json`):
- Keep DEVICE_ID, ADVERTISING_DATA and CRASH_DATA.
- **Remove PRODUCT_INTERACTION/ANALYTICS and PERFORMANCE_DATA.** They are deactivated (`Info.plist:317-320`, `AndroidManifest.xml` meta-data) and `AglInsights.init` is absent (`main.dart:22-28`). Same finding as v1.
- Add Photos only when S1 ships, and Coarse Location if the founder takes the conservative reading.

**Play Data safety:**
- Device or other IDs: shared for advertising.
- Crash logs: collected.
- Approximate location: processed ephemerally by the weather provider, collected = no [V-37].
- S1 adds Photos, sent to a service provider and processed ephemerally if Pl@ntNet does not retain them [V-7].
- Data encrypted in transit: yes (HTTPS only after M1).
- Deletion: Settings › Delete everything (no account).

**Security:**
- HTTPS only; no cleartext config.
- No secret in the binary (D4).
- Model and classifier integrity checked by sha256.
- The export zip is unencrypted user data, so warn when sharing it: "Contains your plant photos and notes".

## 9. What is removed, what is reused

Removed: everything listed in M1, plus the fonts Saira and Space Mono, the "Bone & signal" palette, `tool/lan_harness.py`, the Local Network and cleartext configuration, the interstitial trigger, and the remote store copy and review notes.

Reused:

| Item | From | Use in v2 |
|---|---|---|
| `main.dart` startup, AdMob ids, crash bootstrap | PlantPulse | unchanged |
| `adaptive.dart`, `haptics.dart`, `tactile.dart` | PlantPulse | re-themed |
| `app_store.dart` prefs pattern | PlantPulse | settings |
| `setup_transfer.dart` format/version idea | PlantPulse | export format |
| `identity_test`, `source_grep_test`, `l10n_test`, `crash_reporting_test`, `ads_placement_test`, `foldable_layout_test` structure | PlantPulse | rewritten content |
| llama.cpp shim, `LlmEngine`, `ModelStore` | Verba @ `ef8be2c` | `packages/agl_llm` (D2) |

## 10. Store (store-compliance, market-researcher)

- **Name:** "iPlantPulse: Plant ID & Care" (28). ASC availability is not checked.
- **Subtitle (≤ 30):** "Offline ID, light meter, care" (29).
- **Play short (≤ 80):** "Identify plants offline, measure light, and get watering that learns each plant." (80).
- **Category:** LIFESTYLE primary, EDUCATION secondary. Competitors' categories are [V-30]. Founder or store-compliance confirms.
- **Promotional text:** "Photograph a plant to identify it on your phone, scan its tag, and get watering checks that learn how fast it really dries."
- **Description draft:** no ALL-CAPS, no "X is…" opener, no oxygen or air claims.
  > Point your camera at a plant and PlantPulse suggests what it is, on your phone, with no signal needed. When it isn't sure, it says so and shows you the candidates instead of guessing.
  >
  > Scan a nursery tag or a fertiliser label and the name, light needs and N-P-K numbers drop into your plant's page. Watering reminders are checks: tell the app "still moist" or "dry, watered" and it learns how fast each plant really dries. Outdoor plants also follow the rain and frost forecast.
  >
  > Measure the light where a plant stands: Android phones use their light sensor; on iPhone the camera gives an estimate, clearly labelled. Yellow leaves? A short checklist reads your plant's own watering and light history and suggests possible causes and what to try.
  >
  > An optional on-device assistant (a one-time download on Wi-Fi) answers care questions about your plants, without sending your journal anywhere.
  >
  > No account and no subscription. Your photos and notes stay on your phone. One Google AdMob banner appears at the bottom of the home screen. Where the law requires it you choose about ad personalisation first, and you can change it in Settings.
- **Keywords (≤ 100):** `plant care,plant identifier,houseplant,watering reminder,light meter,garden,offline,succulent,fern` (98).
  - No competitor names (2.3.7).
- **Competitors** (all from knowledge, **[V-30]**; the iTunes Search API was not run because web use is pending):
  - **PictureThis**: photo ID, diagnosis, care reminders; subscription; cloud ID.
  - **PlantNet**: free, citizen-science ID; network needed; no care plan.
  - **Planta**: care schedules, reminders, a light meter, "Dr. Planta" diagnosis; subscription.
  - **Greg**: schedules computed from plant, pot, light and location; community; subscription.
- **4.3 differentiation (draft):**
  - §1: the screens in M2–M8.
  - §2: the user in §2.
  - §3 gap, stated narrowly and unverified: "identification, label OCR and an assistant that all run on the device with no account; watering that adapts to the user's own checks with every adjustment explained; light measured by the phone rather than chosen from a list; health suggestions that read the plant's own history and say they are not a diagnosis."
  - §6: "No other app in the account does plant care" (spec grep, §2).
- **Screenshots:** iPhone 6.9", iPad 13", Play phone and tablet. **Real plants, real photos by us (F9). Never stock or generated images (5.2.1, 2.3.3).**
  1. Today with real plants;
  2. a "Likely" ID with "on this phone";
  3. a "Not sure" ID (honesty);
  4. label scan → N-P-K chips;
  5. care plan with reason lines;
  6. light reading;
  7. assistant answer with the AI label.
  - Rebuild the Play feature graphic from the new icon.
- **Review notes** (this app only):
  - **What and for whom:** "PlantPulse is a plant journal for people with houseplants and gardens: on-device identification, label OCR, adaptive watering checks, a light meter and an optional on-device assistant."
  - **Access:** "No login. Every feature is reachable from the home screen. To try identification without plants, choose a photo from the library."
  - **The assistant:** "It downloads a ~1.1 GB open-weights language model (data, not code) on Wi-Fi after the user agrees. It answers plant care only, every answer is labelled AI, and each can be reported. Questions about toxicity and health get fixed app messages, not model output."
  - **Light:** "On iPhone, light is an estimate from camera exposure and is labelled so."
  - **External services:** GBIF (taxonomy), Open-Meteo or MET Norway (weather for outdoor plants, city-level), Hugging Face (model download), Firebase Crashlytics, Google AdMob (one banner, UMP consent, no ATT). S1 adds Pl@ntNet, via our server, on explicit send.
  - **Permissions:** camera (on Identify / Scan / Measure); notifications (only when reminders are turned on).
  - No hidden or remote-switched features.
- **Catalogue rules** (all 113 in `store/policy/catalogue.json`; how v2 handles each applicable one):

| Rule | v2 handling |
|---|---|
| 1.1, 4.0, 4.1, 2.3.8 | Own art; plant photos by us |
| 1.1.6, 2.3.1, 5.6, Play Deceptive behavior | No oxygen, air-purifying or "accurate diagnosis" claims (M6/M7 greps); the assistant is visible, not hidden. `firebase_remote_config` is in `pubspec.lock` via `agl_observability` (audit 2.3.1): code-hygiene to remove |
| 1.4 / 1.4.1 / 5.1.3 / Play Health | Not applicable: plant health, not human. The `health` tag only fires on the `health` package or HealthKit (`store_policy_audit.py:848`). No human or pet medical statements (M8 fixed messages) |
| 1.5, Play Contact details | Existing PASS |
| 2.1(a), 2.4.1 | iPhone + iPad launch (M12); all orientations on iPad (M1) |
| 2.2, 2.3, 2.3.3, 2.3.4, 2.3.7, 2.3.10, Play Metadata, Play Impersonation | §10 copy; real screenshots; no competitor or brand names; no "Android" in iOS copy |
| 2.3.6, Play IARC | Re-answer for an AI assistant (F14) |
| 2.4.2, 2.5.4, Play Background | No background modes; inexact local notifications; downloads in the foreground only |
| 2.5.1 | Public APIs only (AVCaptureDevice properties are public) |
| 2.5.2 | Model weights are data; no code download (review note) |
| 2.5.18, Play Ads, Play Ads ID | One banner, no interstitial (M10), UMP |
| 4.2, 4.2.6, 4.3(a), 4.3(b), Play Spam | §2 signature, M2–M8 depth, §10 differentiation |
| 4.5.4 | Local notifications only, opt-in, no marketing |
| 4.7, Play AI-generated content | AI label, report control, scope filter (M8). store-compliance adds `package:agl_llm/` to `AI_CODE` (`store_policy_audit.py:784`) so these rules apply |
| 5.1.1(i)–(iv), Play User Data | In-app policy link (M10); purpose strings; works when every permission is denied (no camera → search by name; no notifications → in-app Today list) |
| 5.1.2 | No tracking; UMP |
| 5.1.5, Play Location | n-a in MUST (no location API); applies with S9 |
| 5.2.1, 5.2.2, Play Device and network abuse | Licences: AIY model [V-1], Qwen [V-23], llama.cpp [V-15], fonts OFL, GBIF attribution [V-5]; API terms: Open-Meteo commercial (F2), Hugging Face [V-22], Pl@ntNet [V-6] |
| 5.2.5 | No Apple marks |
| 5.6.1 | No rating prompts |
| ITMS-91053 / 91061 / 90683 | Re-derived from the new IPA; ML Kit and TFLite pods' privacy manifests [V-10] |
| Export compliance | HTTPS only; `ITSAppUsesNonExemptEncryption=false` stays valid |
| Play Target API, 16 KB pages, App bundle | targetSdk 36; every `.so` (ML Kit, llama) aligned (M12) |
| Play Data safety | §8 answers (founder submits) |
| Play Permissions, Photo/video, All files, Package visibility, Accessibility, Install packages, Foreground services, Exact alarms | Photo picker, no `READ_MEDIA_*`, no exact alarms, no FGS (M10) |
| Play Families | Target audience 13+ or 18+ because of the AI chat (F14) |
| Play Malware/MUwS, Play Integrity | Data safety matches the code; read the pre-launch report |

  - **Not applicable in v2 MUST:** 1.2, 1.3, 1.6, 1.7, 2.1(b), 2.1 Information Needed, 2.4.5, 2.5.6, 2.5.14, 2.5.15 (S7), 2.5.16/4.4 (S8), 3.1.1–3.2.2(ii), 4.8, 4.9, 5.1.1(v), 5.1.1(ix), 5.1.4, 5.2.3, 5.3, 5.4, 5.5. On Play: Account deletion, Background location, SMS/Call log, Financial, Payments, Subscriptions, Gambling, News, Dating, Government, UGC, App access.

## 11. Vendors and founder actions

**Vendors.** All facts are from knowledge; every free tier and licence is **[V]**.

| Vendor | Use | MUST/SHOULD | Key? | Where the key lives | Free tier (verify) |
|---|---|---|---|---|---|
| AIY plants V1 (TF Hub / Kaggle Models) | on-device ID | MUST | no | bundled asset | free, Apache-2.0 [V-1] |
| Google ML Kit text recognition (+ custom image labeling) | OCR (+ classifier runtime) | MUST | no | — | free, on-device, ML Kit terms [V-8][V-9] |
| GBIF API | taxonomy, common names | MUST | no | — | free, attribution [V-4][V-5] |
| Open-Meteo forecast + geocoding | weather for outdoor plants, city search | MUST (or MET Norway) | no for the free tier; a paid key would be secret | Edge Function if paid | free **non-commercial**, ~10k calls/day; commercial = paid [V-19][V-20] |
| MET Norway Locationforecast | weather alternative | MUST alternative | no (User-Agent required) | — | free, CC BY 4.0, commercial OK [V-21] |
| Hugging Face (Qwen2.5 GGUF) | model download | MUST | no (public repos) | — | free download; model Apache-2.0 [V-22][V-23] |
| llama.cpp | inference library | MUST | no | — | MIT [V-15] |
| Pl@ntNet API | online second opinion | SHOULD (S1) | yes (free account) | Supabase Edge Function secret `PLANTNET_API_KEY` | ~500 identifications/day; commercial terms and image retention [V-6][V-7] |
| Kindwise plant.id (+ health) | online ID and health | SHOULD (S3) | yes | Edge Function secret `KINDWISE_API_KEY` | trial credits, then paid [V-35] |
| Perenual | care data enrichment | SHOULD (S4) | yes (free) | Edge Function secret `PERENUAL_API_KEY` | ~100 req/day, species ≤ 3000 on free [V-36] |
| Supabase (existing `smvvjivvlprjhzhoizym`) | Edge Functions for S1/S3/S4 | SHOULD | anon key public (`--dart-define`); secrets server-side | existing project | existing plan |
| Flower Care-type BLE sensors (HHCC) | soil readings | SHOULD (S2) | no | — | hardware purchase [V-26] |
| Firebase Crashlytics, Google AdMob | existing | existing | existing | existing | existing |
| Trefle | — | not recommended | — | — | service status unknown [V-38] |

The founder signs up for every key (Charter §4). Keys are never pasted in chat; the founder or office sets them with `supabase secrets set`. Record each signup in `store/vendors/playbook.json` and `apps/PlantPulse.csv` (vendor-scout), with no key material.

**Founder actions** (Charter section in brackets):
- **F1 (§8, done; §1)** Retiring the remote is approved. Confirm the order of work: the Real Apps remote build has now committed (`d2e62f0`). v2 deletes that work in M1, and the remote's QA "must-fix" items should be **dropped, not finished**.
- **F2 (§3)** Open-Meteo commercial use: pay for a key, or switch to MET Norway. This also affects daily-pulse and iMaps.
- **F3 (§3)** Model hosting: Hugging Face direct (free, recommended at launch) or our own storage (egress cost).
- **F4 (§4)** Sign up for a Pl@ntNet API key (S1).
- **F5 (§2)** Approve the Supabase migration (rate-limit table) and the Edge Function deploy (S1/S3/S4).
- **F6 (§3)** Kindwise: buy credits or not (S3).
- **F7 (§4)** Perenual: sign up for a free key (S4).
- **F8 (§3)** Buy 1–2 Flower Care-type sensors and one reference lux meter, for S2 and the M7 iOS calibration.
- **F9 (human)** Photograph ≥ 30 real plants of known species and ≥ 25 real tags and labels (M3/M4 evaluation and screenshots). Provide a physical iPhone and Android phone run.
- **F10 (§6)** Approve the privacy-policy text for `/policy/plantpulse/` (office drafts it).
- **F11 (§1)** Play Console: discard the staged production draft (versionCode 1, the remote) so it can never be published. New builds use Apple build ≥ 3 and Play versionCode ≥ 4.
- **F12 (§3)** Interstitials: none (recommended) or keep.
- **F13** `agl_llm` lives in `agl-manifest/packages/`, built from Verba `ef8be2c`. This is consistent with Verba's removal in `9fbbdf8` and any later decision on Verba Q1. Confirm.
- **F14 (§1/§4)** Age rating and Play target audience with an AI assistant: 13+ or 18+.
- **F15** Web/curl use for the developer: model files, fonts, AIY model, licences, GBIF taxa generation, and the [V] checks. MUST work is blocked until this is allowed.
- **F16** Store name "iPlantPulse: Plant ID & Care" and LIFESTYLE category.
- **F17** If Spike 0b shows poor houseplant coverage: accept "plants and trees" positioning until a better-licensed model exists, or fund S3.
- **Submission** stays frozen under the 5.6 hold (MA-043, Charter §1).

## 12. Not verified

- Every [V] item in §13.
- Houseplant coverage and accuracy of the AIY model.
- ML Kit on the arm64 iOS simulator.
- llama.cpp speed and memory on real phones.
- iOS camera lux calibration.
- The BLE protocol on current sensor firmware.
- Competitor features and categories.
- ASC availability of the store name.
- Whether email-based AI reporting satisfies Play.
- All horticultural values [V-C].

## 13. Verify list (from knowledge, no web used)

- **V-1** AIY "plants V1" classifier: TF Hub / Kaggle Models handle, Apache-2.0 licence, ~2,100 classes, 224×224 uint8, label map format, background class, asset size.
- **V-2** Training data (iNaturalist 2017) and houseplant coverage.
- **V-4** GBIF endpoints `species/match`, `species/{key}`, `vernacularNames`, `species/suggest`; no key; rate etiquette.
- **V-5** GBIF Backbone Taxonomy licence and attribution text.
- **V-6** Pl@ntNet API `my-api.plantnet.org/v2/identify/{project}`, `api-key` parameter, images and organs, free quota (~500/day), commercial-use terms.
- **V-7** Pl@ntNet attribution requirement and whether submitted images are retained or reused.
- **V-8** ML Kit text recognition v2: on-device, bundled Latin model, no key, ML Kit terms; Flutter plugin `google_mlkit_text_recognition`.
- **V-9** ML Kit custom image labeling with a local TFLite model plus metadata (`google_mlkit_image_labeling`), and AIY model compatibility.
- **V-10** ML Kit iOS minimum version, arm64 simulator support, pod privacy manifests.
- **V-11** Maintainer and licence of the `google_mlkit_*` Flutter plugins.
- **V-12** `tflite_flutter` / LiteRT plugin status, licence and iOS simulator support.
- **V-13** Licences and maintenance of `llama_cpp_dart`, `fllama`, `flutter_gemma`.
- **V-14** Building llama.cpp for iOS with Metal through a podspec, or the release xcframework.
- **V-15** llama.cpp MIT licence; the pinned tag.
- **V-16** Android 16 KB page alignment: NDK version, verification commands.
- **V-17** Versions of `path_provider`, `camera`, `image_picker`, `connectivity_plus`, `share_plus`, `archive`, `flutter_local_notifications`, `timezone`.
- **V-18** `image_picker` uses PHPicker and the Android Photo Picker without permissions; whether Apple's scan still demands `NSPhotoLibraryUsageDescription`.
- **V-19** Open-Meteo daily variables `precipitation_sum`, `temperature_2m_max/min`, `et0_fao_evapotranspiration`, `past_days`.
- **V-20** Open-Meteo terms: non-commercial free tier, limits, commercial plan, data retention.
- **V-21** MET Norway Locationforecast terms: CC BY 4.0, User-Agent, commercial use.
- **V-22** Hugging Face terms for direct app downloads of public files.
- **V-23** Qwen2.5-0.5B/1.5B-Instruct licence (Apache-2.0), GGUF file names, sizes, sha256.
- **V-24** `flutter_local_notifications` inexact scheduling mode name; whether it needs `RECEIVE_BOOT_COMPLETED`.
- **V-25** iOS backup exclusion API for large downloaded files (Apple Data Storage Guidelines).
- **V-26** Flower Care / Mi Flora (HHCCJCY01): GATT UUIDs, the 0xA01F mode write, byte layout, MiBeacon 0xFE95, no pH sensor, trademark owners.
- **V-27** PlantVillage dataset licence, class and crop list, field-photo generalisation.
- **V-28** Exposure-to-illuminance formula and calibration constant; lux→PPFD factors for S6.
- **V-29** ASPCA toxic and non-toxic plants URL and linking terms.
- **V-30** PictureThis, PlantNet, Planta, Greg: features, pricing, categories, offline behaviour.
- **V-31** Play AI-generated content policy: whether an in-app control that opens an email counts as in-app reporting.
- **V-32** Gelasio and Commissioner: file names on github.com/google/fonts, axes, tabular figures support.
- **V-33** Licences of `flutter_reactive_ble` and `flutter_blue_plus`.
- **V-34** Android `neverForLocation` beacon filtering and MiBeacon adverts.
- **V-35** Kindwise plant.id v3 endpoint, health assessment, trial credits, pricing.
- **V-36** Perenual endpoints, free limits, species-ID restriction, commercial terms.
- **V-37** Play Data safety "processed ephemerally" for weather coordinates.
- **V-38** Trefle service status.
- **V-C** Every care-type interval, light band, feeding month and health rule. Each needs a cited horticultural source before it ships.
