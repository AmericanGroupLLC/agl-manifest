export const meta = {
  name: 'vendor-scout-per-app',
  description: 'Find app-specific affiliate programmes and data APIs for all 43 apps, by domain, with official sources',
  phases: [
    { title: 'Scout', detail: 'one researcher per app domain' },
    { title: 'Verify', detail: 'independent check of each domain list' },
  ],
}

const M = '/Users/spatchava/agl/agl-manifest'
const DOMAINS = args.domains
const ALREADY = 'Amazon Associates, Best Buy, Walmart Affiliates, Target Partners, eBay Partner Network, Levanta, Impact.com, CJ Affiliate, Awin/ShareASale'

const VENDOR_SCHEMA = {
  type: 'object',
  properties: {
    vendors: { type: 'array', items: { type: 'object', properties: {
      app: { type: 'string' }, vendor: { type: 'string' },
      kind: { type: 'string', enum: ['affiliate', 'data-api', 'affiliate+api', 'partner/referral', 'sdk/service'] },
      network: { type: 'string', description: 'in-house, or the network that runs the programme (Impact, CJ, Awin, Rakuten, Partnerize, FlexOffers, Travelpayouts, ...), or n/a' },
      what_it_gives_the_app: { type: 'string' },
      signup_url: { type: 'string' },
      commission: { type: 'string', description: 'as officially published, else "not published" / "not verified"' },
      api_or_feed: { type: 'string', description: 'product/data API or feed, access requirements, free tier — or "none found"' },
      mobile_apps_allowed: { type: 'string', description: 'yes / no / not stated, with source' },
      fit: { type: 'string', description: 'why it fits THIS app as it exists today (or what the app would need to add)' },
      effort: { type: 'string', enum: ['link-only', 'small', 'medium', 'large'] },
      sources: { type: 'array', items: { type: 'string' } },
      verified: { type: 'boolean', description: 'true only if signup URL and programme existence were confirmed on an official page this session' },
    }, required: ['app', 'vendor', 'kind', 'network', 'what_it_gives_the_app', 'signup_url', 'commission', 'api_or_feed', 'mobile_apps_allowed', 'fit', 'effort', 'sources', 'verified'] } },
    unverified_notes: { type: 'array', items: { type: 'string' } },
  },
  required: ['vendors', 'unverified_notes'],
}

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    checks: { type: 'array', items: { type: 'object', properties: {
      app: { type: 'string' }, vendor: { type: 'string' },
      verdict: { type: 'string', enum: ['confirmed', 'corrected', 'reject'] },
      correction: { type: 'string' }, evidence: { type: 'string' },
    }, required: ['app', 'vendor', 'verdict', 'evidence'] } },
  },
  required: ['checks'],
}

const results = await pipeline(DOMAINS,
  d => agent(`You are a market researcher for American Group LLC, which publishes 43 consumer mobile apps (Flutter, iOS + Android). Goal: find MORE vendors for each app below — affiliate programmes that pay commission for referrals from the app, and data APIs/feeds that would make the app's features real — specific to each app's domain.

Domain: **${d.name}**
Apps (repo | store category | what it does today):
${d.apps.map(a => `- ${a}`).join('\n')}

Rules:
- Use WebSearch and WebFetch. Each vendor must have its OFFICIAL signup/partner page URL, and you must confirm the programme exists on an official page (set verified=true only then). Today is 2026-10-12. Never fill facts from memory; write "not verified" / "not published" instead.
- Commission: only what the programme or its network officially publishes.
- Mobile apps allowed: state yes/no/not stated with a source.
- Prefer vendors that fit what the app does TODAY (see descriptions; current code facts are in ${M}/docs/api-vendor-directory.csv and ${M}/docs/api-vendor-usage.json — read them so you don't propose what is already wired, and so you can note where an existing link just needs an ID). It is fine to propose vendors that need a small feature added; say so in fit/effort.
- These big programmes are being researched separately — you may list them for an app when they fit, but do not research their terms (set commission "see network research"): ${ALREADY}.
- Aim for breadth: roughly 4–10 relevant vendors per app (fewer if the app genuinely has no commercial fit — e.g., an on-device utility — and say why). Include niche domain programmes (e.g., for music gear: Sweetwater, Guitar Center, Reverb; for plants: The Sill, Bloomscape; for finance: brokerage/credit referral programmes and their compliance limits; for travel: Agoda, GetYourGuide, Airalo, DiscoverCars, Omio, Klook; for health: telehealth/lab-test programmes and their medical-claims limits).
- Flag compliance limits (finance/health/dating/children) in fit.
- Do not sign up or submit any form. Read-only.`, { label: `scout:${d.name}`, phase: 'Scout', schema: VENDOR_SCHEMA }),
  (found, d) => {
    if (!found || !(found.vendors || []).length) return { d, found, verdict: null }
    return agent(`Independently verify this vendor list for the "${d.name}" apps of American Group LLC. For EACH entry: open the signup_url (WebFetch) and/or search, and check (1) the programme or API exists and the URL is the official one, (2) the commission and mobile-app statements match an official page, (3) the fit claim is not wrong about the app. Verdict: confirmed, corrected (give the correction), or reject (programme closed, wrong vendor, not official, unsupported claim). Default to reject when you cannot confirm existence. Today is 2026-10-12. Read-only.

Entries:
${JSON.stringify(found.vendors).slice(0, 60000)}`, { label: `verify:${d.name}`, phase: 'Verify', schema: VERDICT_SCHEMA }).then(verdict => ({ d, found, verdict }))
  },
)

const out = []
for (const r of results.filter(Boolean)) {
  const checks = new Map(((r.verdict && r.verdict.checks) || []).map(c => [`${c.app}|${c.vendor}`, c]))
  for (const v of (r.found && r.found.vendors) || []) {
    const c = checks.get(`${v.app}|${v.vendor}`)
    out.push({ ...v, domain: r.d.name, check: c ? c.verdict : 'unchecked', correction: c ? (c.correction || '') : '', check_evidence: c ? c.evidence : '' })
  }
}
return { vendors: out, notes: results.filter(Boolean).flatMap(r => (r.found && r.found.unverified_notes) || []) }