export const meta = {
  name: 'daily-standup',
  description: 'Refresh measured state, write the stand-up, and have each owning role triage its failures',
  phases: [{ title: 'Measure' }, { title: 'Triage' }, { title: 'Report' }],
}
// Run from agl-manifest/ai-office. Every claim must carry evidence.
phase('Measure')
const measured = await agent(
  'From /Users/spatchava/agl/agl-manifest run the daily-standup skill steps 1-2 (asc_build_state, asc_screenshots + screenshot_audit, apple_requirements, monitor_domains, then ai-office/scripts/standup.py). Return the report path and the list of failing items, each with its evidence line.',
  { label: 'measure', phase: 'Measure', agentType: 'operations-manager',
    schema: { type: 'object', properties: { report: { type: 'string' },
      failures: { type: 'array', items: { type: 'object', properties: {
        item: { type: 'string' }, owner: { type: 'string' }, evidence: { type: 'string' } },
        required: ['item', 'owner', 'evidence'] } } }, required: ['report', 'failures'] } })
phase('Triage')
const triaged = await parallel((measured?.failures || []).map(f => () => agent(
  `You own this failure: ${f.item}\nEvidence: ${f.evidence}\nDiagnose the root cause with evidence. If it is fixable within your authority, describe the fix and the check that proves it; otherwise say exactly what approval or input is needed. Open or update an ai-office issue for it (gh -R AmericanGroupLLC/agl-manifest).`,
  { label: `triage:${f.owner}`, phase: 'Triage', agentType: f.owner })))
phase('Report')
return await agent(
  `Consolidate the stand-up. Report path: ${measured?.report}. Triage results:\n${JSON.stringify(triaged.filter(Boolean)).slice(0, 20000)}\nWrite the final summary into the report: done (with evidence), in progress, blocked, and "Decisions needed from the founder".`,
  { label: 'consolidate', phase: 'Report', agentType: 'chief-of-staff' })
