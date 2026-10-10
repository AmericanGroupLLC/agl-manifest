export const meta = {
  name: 'release-train',
  description: 'Gate, build, upload to TestFlight/Play internal, and prove arrival at Apple and Google',
  phases: [{ title: 'Gate' }, { title: 'Ship' }, { title: 'Prove' }],
}
phase('Gate')
const gate = await agent('Run release-train skill step 1. Return which apps pass every gate and which fail (with the failing check).',
  { label: 'gate', phase: 'Gate', agentType: 'release-manager' })
phase('Ship')
const ship = await agent(`Gate result:\n${String(gate).slice(0, 8000)}\nRun release-train steps 2-3 for the passing apps; fix pipeline failures within your authority and re-run. Never submit for review.`,
  { label: 'ship', phase: 'Ship', agentType: 'release-manager' })
phase('Prove')
return await agent(`Ship result:\n${String(ship).slice(0, 8000)}\nIndependently prove arrival (check_build.rb until VALID; Play version codes). Report per app, iOS and Android separately, with evidence.`,
  { label: 'prove', phase: 'Prove', agentType: 'qa-reviewer' })
