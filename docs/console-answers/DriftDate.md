# Play Console answers — DriftDate

`com.americangroupllc.driftdate`

Four of these five have no API; they are Console forms. Every answer is taken
from what this repository already measures, so this is transcription rather
than judgement.

## App access
**Some functionality is restricted.** This app signs in and has no guest path, so Play needs working reviewer credentials — and MA-036 records that the documented test accounts do not authenticate. Fix that first.

## Ads
**No, this app does not contain ads.** It does not link the Google Mobile Ads SDK.

## Content rating (IARC questionnaire)
Category: see store/apps/DriftDate.json
This app has at least one non-default content answer; read store/ratings/DriftDate.json and mirror it.
User-generated content: Yes — the app accepts user content.

## Target audience and content
Target age group: **18 and over** unless the listing says otherwise.
Appeals to children: **No**.

## Data safety
Collected data types:\n  - Personal info > Email address\n  - Personal info > Name\n  - Personal info > User IDs

For each: collected **Yes**, shared **No**, processed ephemerally **No**,
collection is **required**. Purpose: *App functionality* and *Analytics*;
add *Advertising* for the advertising row.
Encrypted in transit: **Yes**. Users can request deletion: **Yes** —
https://www.safecodeg.com/policy/driftdate/delete-account.html

## After the forms
The production release is already staged as a draft with a signed bundle.
Once App content is complete the app leaves Draft and the release can be
rolled out — `python3 scripts/play_release.py DriftDate` or the Console.
