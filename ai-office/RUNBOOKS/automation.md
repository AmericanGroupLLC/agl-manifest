# Automation inventory

| Job | Where | Schedule | Check |
| --- | --- | --- | --- |
| Delivery (`ship.yml`) | agl-manifest Actions | daily 06:00 UTC + push | `gh run list --workflow ship.yml -R AmericanGroupLLC/agl-manifest` |
| Domain monitor | agl-manifest Actions | every 30 min | issue "Domain monitor: …" |
| Store health | agl-manifest Actions | daily 08:00 UTC | issue "Store health: checks failing" |
| AI office stand-up | agl-manifest Actions | daily 13:00 UTC | `ai-office/reports/` |
| AI office daily pass (Claude on this Mac, no API key) | this Mac (launchd `com.americangroupllc.aioffice`) | daily 07:45 local | `~/agl/.dist/ai-office/latest.log`, `ai-office/reports/<date>-office.md` |
| Store watch | this Mac (launchd `com.americangroupllc.storewatch`) | every 6 h | `~/agl/.dist/store-watch/latest.log` |
| Website deploy | americangroup.ai Actions | each push | deploy.yml |
| Backend CI / deploy | backend Actions | push to dev / migrations (approval) | ci.yml, deploy.yml |
