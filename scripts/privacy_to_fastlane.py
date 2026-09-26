#!/usr/bin/env python3
"""Render store/privacy/<repo>.json into the shape fastlane's
`upload_app_privacy_details_to_app_store` actually reads.

The files here are keyed by data type, which is how Apple's questionnaire reads
to a person. The action wants a flat list of usage entries with plain string
values, and feeding it the other shape dies with "no implicit conversion of
String into Integer" from its own array indexing.

    python3 scripts/privacy_to_fastlane.py            # -> store/privacy/fastlane/<repo>.json
"""
import json, pathlib

M = pathlib.Path(__file__).resolve().parent.parent
SRC = M / "store/privacy"
OUT = SRC / "fastlane"
OUT.mkdir(exist_ok=True)

written = 0
for p in sorted(SRC.glob("*.json")):
    d = json.loads(p.read_text())
    entries = []
    for item in d.get("data_protections", []):
        dtype = item.get("data_type")
        if dtype == "DATA_NOT_COLLECTED":
            entries = [{"data_protections": ["DATA_NOT_COLLECTED"]}]
            break
        entries.append({
            "category": dtype,
            "purposes": item.get("purposes", []),
            "data_protections": item.get("protections", []),
        })
    if not entries:
        entries = [{"data_protections": ["DATA_NOT_COLLECTED"]}]
    (OUT / p.name).write_text(json.dumps(entries, indent=1) + "\n")
    written += 1
print(f"wrote {written} file(s) -> {OUT}")
