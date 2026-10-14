# Approval request — RideZap becomes a racing game (style, prices, the build in review)

Date: 2026-10-14 · Prepared by: chief-of-staff (AI office) · App: RideZap (`com.americangroupllc.ridezap`, repo `RideZap/mobile`)

## Decision needed

The founder asked (2026-10-14, chat) to turn RideZap into a racing video game, with a choice of cars and bikes and their "flavours" (liveries/colours), ads, rewarded ads, paid points for premium cars, and a subscription that removes ads. The references were Forza Horizon 5, The Crew 2 / Motorfest and Test Drive Unlimited Solar Crown (large open worlds).
Four things in that request are founder decisions (Charter: pricing, store records, submissions). Each one has the office's recommendation marked.

| # | Decision | Options | Office recommends |
|---|---|---|---|
| R1 | Game style | **a)** Top-down open world, built with Flutter and the Flame engine: one large map with city, highway, desert, coast and mountain regions, free roam, checkpoint races, AI rivals, day/night and weather. **b)** Pseudo-3D behind-the-car road racer (OutRun style) on long routes. **c)** True 3D in Unity. | **a.** It fits the Flutter pipeline, the CI and the gates every other app goes through, and it can be built and tested here. **c** leaves the stack: new engine, new CI, large assets, and it can't be verified to the same standard. |
| R2 | Prices | **a)** Coins $0.99 / $4.99 / $9.99 / $19.99; Remove ads $2.99/month, $19.99/year, or $4.99 once. **b)** Lower: coins $0.99 / $2.99 / $4.99; Remove ads $1.99/month or $9.99/year. **c)** Placeholders now; the founder sets prices in App Store Connect and Play Console. | **a.** Every car and bike can also be earned by racing. Nothing is pay-only, which avoids "pay to win" complaints and review trouble. |
| R3 | The fare-app RideZap now **Waiting for Review** at Apple (submission resubmitted 2026-10-14) | **a)** Let it run. If approved, it goes live, and the game ships as version 2.0 with category Games → Racing. **b)** Withdraw it from review now and submit only the game. | **b.** Launching a product we are replacing gives users a fare app that turns into a game, which earns bad reviews. The fare app was also rejected under 5.6 on 2026-10-08 (`.dist/rejections.json`), so approval is unlikely anyway. |
| R4 | Store products | The office creates the in-app purchases (4 consumable coin packs, 1 non-consumable "Remove ads forever", 1 auto-renewing subscription group with monthly and yearly) in App Store Connect and Play Console via the API at the approved prices. It then changes the category to Games → Racing and redoes the age rating questionnaire (expected 4+: no violence, no gambling, no user content). | Approve. The Paid Applications agreement must be active. Apple accepted resubmissions on 2026-10-14, but in-app purchase availability itself is **not verified**. |

## Why now / what it unblocks

- It settles open decision **D1** in `projects/real-apps/overlap.md`: retire RideZap into TripNest, or keep it. The fare-app spec (`projects/real-apps/specs/RideZap.md`) says the current product cannot work, because there is no fare API. A game is clearly distinct from the other 42 apps, which answers Apple 4.3 / 4.2.6.
- The game spec (`projects/real-apps/specs/RideZap-game.md`) is being written now and needs no decision. Building starts once R1 is answered. R2–R4 are needed before release, not before building.

## Exact action

Answer R1–R4 in chat or on the linked issue: for example "R1 a, R2 a, R3 b, R4 approve". Once answered, the office will:
1. Product-manager finishes the spec. Software-developer builds it in `RideZap/mobile` (new `lib/game/` on Flame). QA-reviewer, store-compliance and the release-quality-gate follow.
2. For R3 b: withdraw the review submission through the App Store Connect API (`reviewSubmissions` PATCH `canceled: true`). The office does this **only** after approval.
3. For R4: create the products and the subscription group, then update the category and age rating.

## Evidence

- Current product and state: `projects/real-apps/specs/RideZap.md` §1. Apple 5.6 rejection on 2026-10-08. Play `PRODUCTION_DRAFT_STAGED`.
- Apple state on 2026-10-14: `WAITING_FOR_REVIEW`, attached build SDK `23F81a` (an accepted SDK). Source: `bundle exec ruby /tmp/agl-attachedsdk.rb`, run in chat.
- Last fare-app commits: `62109ef` ("your usual fare") and `f2b733c` (`git -C RideZap log`).
- Trademark: Forza, The Crew and Test Drive are third-party marks. Real car and bike brands need licences. The game will use **fictional** vehicles and must not use those names in store copy (Apple 5.2.1, Play IP policy).

## Risks / how to undo

- Apple 4.3 also applies to games: a generic racer in a crowded category can still be called spam. The spec must give RideZap its own identity: open-world region map, cars **and** bikes, and liveries.
- In-app purchases add review items: a restore-purchases button, and terms and privacy links on the subscription screen (3.1.2). The spec includes them.
- Undo: R3 b can't be undone for that submission, but the fare-app build stays in App Store Connect and can be resubmitted. Products can be removed from sale. The bundle id never changes.
