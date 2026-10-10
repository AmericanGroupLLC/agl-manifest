# Play Console answers — yourtube

`com.americangroupllc.yourtube`

Four of these five have no API; they are Console forms. Every answer is taken
from what this repository already measures, so this is transcription rather
than judgement.

## App access
**Some functionality is restricted.** This app signs in and has no guest path, so Play needs working reviewer credentials — and MA-036 records that the documented test accounts do not authenticate. Fix that first.

## Ads
**Yes, this app contains ads.** It links the Google Mobile Ads SDK (AdMob ca-app-pub-3940256099942544~3347511713).

## Content rating (IARC questionnaire)
Category: see store/apps/yourtube.json
Answer **No** to every content question — violence, sexuality, language, controlled substances, gambling, horror. These are the same answers already accepted by Apple, in store/ratings/.
User-generated content: Yes — the app accepts user content.

## Target audience and content
Target age group: **18 and over** unless the listing says otherwise.
Appeals to children: **No**.

## Data safety
Collected data types:\n  - App activity > App interactions (advertising)\n  - Device or other IDs > Device or other IDs\n  - Personal info > Email address\n  - Personal info > Name\n  - Personal info > User IDs

For each: collected **Yes**, shared **No**, processed ephemerally **No**,
collection is **required**. Purpose: *App functionality* and *Analytics*;
add *Advertising* for the advertising row.
Encrypted in transit: **Yes**. Users can request deletion: **Yes** —
https://www.americangroup.ai/policy/yourtube/delete-account.html

## After the forms
The production release is already staged as a draft with a signed bundle.
Once App content is complete the app leaves Draft and the release can be
rolled out — `python3 scripts/play_release.py yourtube` or the Console.
