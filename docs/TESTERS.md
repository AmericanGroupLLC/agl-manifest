# Who can install, and who cannot

Measured from App Store Connect on 2026-09-30.

## App Store Connect account users

These six are users on the account. Internal TestFlight groups have
`hasAccessToAllBuilds = true`, so **these people can install any build
today** — no Beta App Review, no contract needed. Sign in to TestFlight
with the Apple ID below.

| Email | Name | Role |
| --- | --- | --- |
| `aadiboddapati@gmail.com` | Aadi Boddapati | ADMIN, CLOUD_MANAGED_DEVELOPER_ID |
| `nehuwakhare04@gmail.com` | Neha Wakhare | ADMIN |
| `rainbow472.sri@gmail.com` | Srikanth Patchava | ADMIN |
| `sirishapatchava@gmail.com` | sirisha Pachava | ADMIN, CLOUD_MANAGED_DEVELOPER_ID |
| `srikanth.patchava@outlook.com` | Srikanth Patchava | ACCOUNT_HOLDER, ADMIN |
| `suresh.alaparti@gmail.com` | Suresh A | DEVELOPER, SALES |

## TestFlight testers

Ten unique addresses across all groups. An address in an *internal*
group installs immediately; one in an *external* group installs only
after Beta App Review, which is blocked — see MA-019.

| Email | Account user | Groups |
| --- | --- | --- |
| `aadiboddapati@gmail.com` | yes | AGL Internal, AGL Testers, Internal testers, QA-Team, Test, Testing |
| `nehuwakhare04@gmail.com` | yes | AGL Internal, AGL Testers, Internal testers, QA-Team, Test |
| `pranathim95@gmail.com` | no | AGL Testers, Kinnav |
| `rainbow472.sri@gmail.com` | yes | AGL Internal, AGL Testers, Internal testers, QA-Team, Test, Testing |
| `rashmi.advani@gmail.com` | no | AGL Testers |
| `siddarthaandalu@gmail.com` | no | AGL Testers |
| `sirishapatchava@gmail.com` | yes | AGL Internal, AGL Testers, Internal testers, QA-Team, Test, Testing |
| `srikanth.patchava@outlook.com` | yes | AGL Internal, AGL Testers, Internal testers, Me, QA-Team, Test, Testing |
| `suresh.alaparti@gmail.com` | yes | AGL Internal, AGL Testers, Internal testers, QA-Team, Test |
| `vspatel24@gmail.com` | no | AGL Testers, Kinnav |

## The four who currently cannot install

In external groups only, and not users on the account:

- `pranathim95@gmail.com` — AGL Testers, Kinnav
- `rashmi.advani@gmail.com` — AGL Testers
- `siddarthaandalu@gmail.com` — AGL Testers
- `vspatel24@gmail.com` — AGL Testers, Kinnav

They see *"requested app not available or doesn't exist"*. Two ways to
fix it, either is enough:

1. Accept the agreement (MA-019) so external builds pass Beta App Review.
2. Add them as users in App Store Connect -> Users and Access, which puts
   them in the internal group and works immediately.

