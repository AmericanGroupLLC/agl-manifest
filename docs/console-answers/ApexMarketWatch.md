# Play Console answers — ApexMarketWatch

`com.americangroupllc.apexmarketwatch`

Four of these five have no API; they are Console forms. Every answer is taken
from what this repository already measures, so this is transcription rather
than judgement.

## App access
**All functionality is available without a special access.**

## Ads
**No, this app does not contain ads.** It does not link the Google Mobile Ads SDK.

## Content rating (IARC questionnaire)
Category: see store/apps/ApexMarketWatch.json
Answer **No** to every content question — violence, sexuality, language, controlled substances, gambling, horror. These are the same answers already accepted by Apple, in store/ratings/.
User-generated content: No.

## Target audience and content
Target age group: **18 and over** unless the listing says otherwise.
Appeals to children: **No**.

## Data safety
**This app does not collect or share any user data.**

Encrypted in transit: **Yes**. Users can request deletion: **Yes** —
https://www.safecodeg.com/policy/apexmarketwatch/delete-account.html

## After the forms
The production release is already staged as a draft with a signed bundle.
Once App content is complete the app leaves Draft and the release can be
rolled out — `python3 scripts/play_release.py ApexMarketWatch` or the Console.
