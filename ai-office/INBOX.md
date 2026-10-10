# Inbox — how work reaches the office

The work queue is **GitHub issues in AmericanGroupLLC/agl-manifest labelled
`ai-office`**. Anyone (founder, a monitor, a failing workflow) opens an issue;
the chief-of-staff assigns it to a role (`.claude/agents/`) in the issue body.

| Label | Meaning |
| --- | --- |
| `ai-office` | in the office's queue |
| `needs-founder` | waiting on a CHARTER decision — the office has stopped |
| `blocked` | waiting on something outside the office (Apple, Google, a vendor) |

Automatic sources: `domain-monitor.yml` (opens "Domain monitor: …" issues),
`ai-office-standup.yml` (daily report), the daily-standup skill (opens an
issue per new failure).

    gh issue list -R AmericanGroupLLC/agl-manifest -l ai-office
    gh issue create -R AmericanGroupLLC/agl-manifest -l ai-office -t "..." -b "..."
