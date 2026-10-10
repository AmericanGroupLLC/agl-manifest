export const meta = {
  name: 'rejection-response',
  description: 'New store rejection: read it, root-cause it, fix and verify, then draft the reply for founder approval',
  phases: [{ title: 'Read' }, { title: 'Fix' }, { title: 'Verify' }, { title: 'Draft' }],
}
// args: { app: 'MyCard' } (optional — default: every app with a new rejection)
phase('Read')
const read = await agent(
  `Run the rejection-response skill steps 1-3 for ${args?.app || 'every app with a new rejection'}. Return, per app: guideline, Apple's words, root cause with evidence, the fix needed, and whether it is account-level (5.6/4.3 — escalate, do not fix).`,
  { label: 'read', phase: 'Read', agentType: 'store-compliance',
    schema: { type: 'object', properties: { items: { type: 'array', items: { type: 'object', properties: {
      app: { type: 'string' }, guideline: { type: 'string' }, cause: { type: 'string' },
      fix: { type: 'string' }, owner: { type: 'string' }, escalate: { type: 'boolean' } },
      required: ['app', 'guideline', 'cause', 'fix', 'owner', 'escalate'] } } }, required: ['items'] } })
const work = (read?.items || []).filter(i => !i.escalate)
const results = await pipeline(work,
  i => agent(`Fix for ${i.app} (${i.guideline}): ${i.fix}\nCause: ${i.cause}\nImplement it within your authority, add or extend the check in scripts/apple_requirements.py that enforces it, run it, and report evidence.`,
    { label: `fix:${i.app}`, phase: 'Fix', agentType: i.owner }),
  (fix, i) => agent(`Independently verify the fix for ${i.app} (${i.guideline}). Claimed: ${String(fix).slice(0, 6000)}\nRe-run the checks yourself; default to "not fixed" without evidence.`,
    { label: `verify:${i.app}`, phase: 'Verify', agentType: 'qa-reviewer' }).then(v => ({ i, fix, v })))
phase('Draft')
return await agent(
  `Draft truthful Resolution Center replies in store/replies/ for the verified fixes, and an approval request (approval-workflow skill) for the founder. Escalations (account-level): ${JSON.stringify((read?.items || []).filter(i => i.escalate))}. Results: ${JSON.stringify(results.filter(Boolean)).slice(0, 20000)}`,
  { label: 'draft', phase: 'Draft', agentType: 'store-compliance' })
