# GroceryMatch — iOS evidence and the "Contains milk" failure, 2026-10-14

App at **6a30e26** (only the screenshot drive changed: 199951e, 6a30e26). Unit suite there:
`flutter analyze` → No issues found; `flutter test` → `00:25 +578: All tests passed!`.

## Why the drive failed at `expect(find.text('Contains milk'))`: the test, not the app
Diagnostics in the drive (removed afterwards) showed the household profile was
`{en:milk, en:gluten}` and the only open sheet after the Nutella lookup was the **Cheerios**
sheet again ("Barcode 0016000275287"). An assertion then proved the digits field still held
Cheerios' number: `Expected: '3017620422003' Actual: '0016000275287'`. `tester.enterText` only
sets the binding's `focusedEditable`, which does nothing for the same field as the previous
lookup, and the field had lost focus, so no text-input connection existed and the typed number
was dropped. Look up then searched Cheerios again. `lookUp` also accepted *any* product sheet.
`addTyped` had the same flaw (only "Bananas" was ever added). Fixed in the drive: tap the field
first (as a person does), assert the text arrived, wait for the previous sheet to close and
for "Barcode <code>". A real user tapping the field is not affected. Open Food Facts answers
Nutella with `allergens_tags [en:milk, en:nuts, en:soybeans]`, and the app shows "Contains milk".

Two more capture blockers, found on the way:
- Once the scan screen asks for the camera, the iOS permission alert stays on top of every app
  on the simulator (`simctl privacy` has no camera service). While it is up, every capture,
  binding or host, shows the launch image. Evidence runs therefore use
  `--dart-define=GM_NO_CAMERA=true`: the same two OFF products are linked from list rows
  ("Link a product" → barcode number) and the product sheet opens from "Product details".
- Stores waited for the OSM attribution, which is below 25 stores in a lazily built list and
  never built. It now waits for the "N of M stores" line.

## Frames (debug, `SCREENSHOT=true GM_NO_CAMERA=true`, fresh install, live network from the simulator)
`iphone17promax-ios27.0/` (`agl-qa-iphone-4`, 1320×2868): `02:13 +2: All tests passed!`
`ipadpro13-ios27.0/` (`agl-qa-ipad-4`, iPad Pro 13-inch (M5), 2064×2752): `01:26 +2: All tests passed!`
— this is also the M9 **iPad launch**. Each frame was looked at:

| File | What it shows (both devices) |
| --- | --- |
| 01_shopping_list | Aisle-grouped receipt list; "Oat cereal" linked to Cheerios ("My Bff" is that product's real OFF name), **Nutri-Score C** and red **Contains gluten**; "Hazelnut spread" linked to Nutella, **Nutri-Score E** and red **Contains milk**; "Allergen clashes (2)"; dock Scan · Start trip · Basket check |
| 02_basket_check | Nutri-Score mix C:1 E:1, "2 items contain your household's allergens"; better-graded alternatives "each checked against its own record" with Swap; iPad shows "2 search results were left out: its own record showed one of your allergens or a different grade. 1 left out for 'may contain' warnings." |
| 03_scan_result | Product sheet for barcode 0016000275287: photo, grade C, ALLERGENS "Contains gluten", "Contains: Gluten, Corn", ingredients, "Product data from Open Food Facts (ODbL)" |
| 04_stores_near_you | **Real Overpass results**: "Near Santa Clara, California · Approximate", 25 of 25 stores; "Open · closes 21:00", "Hours not listed", iPad also "Closed · opens tomorrow 09:00"; Directions / Shop here |
| 05_trip_mode | Trip at Patel Brothers: "2 of 7 in the basket", Bananas and Bread ticked (lime), "Screen stays on", Finish trip, no ad |
| 06_history | Trip history: Patel Brothers · 14 Oct · 2 items · Bananas, Bread |

Not covered: the camera scanner itself (no camera on a simulator; the typed-number path uses the
same lookup). The Android frames from the earlier round are not redone here (the emulator has no
HTTPS route on this Mac).
