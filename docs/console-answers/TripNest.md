# Play Console answers — TripNest

`com.americangroupllc.tripnest`

Four of these five have no API; they are Console forms. Every answer is taken
from what this repository already measures, so this is transcription rather
than judgement.

## App access
**All functionality is available without a special access.**

## Ads
**Yes, this app contains ads.** It links the Google Mobile Ads SDK (AdMob ca-app-pub-8528784688453695~8044208178).

## Content rating (IARC questionnaire)
Category: see store/apps/TripNest.json
Answer **No** to every content question — violence, sexuality, language, controlled substances, gambling, horror. These are the same answers already accepted by Apple, in store/ratings/.
User-generated content: No.

## Target audience and content
Target age group: **18 and over** unless the listing says otherwise.
Appeals to children: **No**.

## Data safety
Collected data types:\n  - App activity > App interactions (advertising)\n  - Device or other IDs > Device or other IDs

For each: collected **Yes**, shared **No**, processed ephemerally **No**,
collection is **required**. Purpose: *App functionality* and *Analytics*;
add *Advertising* for the advertising row.
Encrypted in transit: **Yes**. Users can request deletion: **Yes** —
https://www.safecodeg.com/policy/tripnest/delete-account.html

## After the forms
The production release is already staged as a draft with a signed bundle.
Once App content is complete the app leaves Draft and the release can be
rolled out — `python3 scripts/play_release.py TripNest` or the Console.
