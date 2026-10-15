# DriftDate moderation: reports, hiding, bans (24-hour SLA)

DriftDate is a real dating app (founder, 2026-10-14). App Store guideline 1.2
requires the developer to act on reports of objectionable content **within 24
hours**, by removing the content and ejecting the user who posted it. This is
how a person does that. Everything below exists in Backend PR #1 (branch
`driftdate-schema`, `supabase/migrations/20261014_driftdate_3_safety.sql`), and
**none of it works until PR #1 is merged and deployed** (issue #19).

Who answers reports is a founder decision (Charter §7, spec question F5).
Until a named person is assigned, the office cannot meet the SLA. The SQL
below is run by that person in the Supabase SQL editor. The AI office does
not run SQL on production (company/policies.md); it can prepare the
statements and read the email.

## The SLA

- Every report must be **actioned or dismissed within 24 hours of
  `created_at`**. `moderation_queue()` returns `due_at` (created + 24 h) and
  `overdue`.
- Check the queue **at least twice a day** (morning and evening, US time),
  even when no email arrived. The email is a prompt, not the system of record:
  the `driftdate.reports` table is.
- Child safety and threats of violence go first, the moment they are seen.

## How a report reaches a person

1. A member reports a profile, a photo (`photo_path`) or a message
   (`message_id`, with the text copied into `message_text` at report time).
   Reporting also blocks the person for the reporter.
2. Trigger `driftdate.reports_notify` posts the report id to the Edge Function
   `driftdate-report-notify`, which emails **support@americangroup.ai** with the
   reason, the reported member's id, the deadline and the commands below. The
   email holds no message text, photo or reporter id. This needs the one-time
   setup below. Without it, nothing is emailed and the twice-daily check is the
   only path.
3. **Auto-hide.** When 3 distinct members with a confirmed email or phone have
   open reports against the same person, that profile is hidden at once:
   nobody sees it, and it cannot wave or send messages until a moderator
   decides. The trigger writes `moderation_actions` row `auto_hide`.

## One-time setup (founder)

1. Merge PR #1 into `dev` and approve the deploy (issue #19 / MA-044).
2. Database → Extensions: enable **pg_net**. (Vault is on by default.)
3. Pick a mail provider. The function is written for **Resend**
   (`api.resend.com`). No provider is configured on this project today, and
   the office has not signed up for one. Whether it costs money depends on
   the plan and volume: check the provider's pricing before choosing.
   Verify `americangroup.ai` (or a subdomain) with the provider so mail can be
   sent from it.
4. Deploy the function and set its secrets. Never paste a secret into git or
   chat:
   ```
   supabase functions deploy driftdate-report-notify --no-verify-jwt --project-ref smvvjivvlprjhzhoizym
   supabase secrets set --project-ref smvvjivvlprjhzhoizym \
     DRIFTDATE_REPORT_WEBHOOK_SECRET=<long random string> \
     RESEND_API_KEY=<key from the provider> \
     REPORT_MAIL_FROM='DriftDate safety <safety@americangroup.ai>' \
     REPORT_MAIL_TO=support@americangroup.ai
   ```
5. SQL editor: store the same secret and the function URL in Vault:
   ```sql
   select vault.create_secret('https://smvvjivvlprjhzhoizym.supabase.co/functions/v1/driftdate-report-notify',
                              'driftdate_report_notify_url');
   select vault.create_secret('<the same long random string>', 'driftdate_report_notify_secret');
   ```
6. Name the moderators. Their DriftDate account id comes from Authentication →
   Users:
   ```sql
   insert into driftdate.moderators (user_id, note) values ('<auth user id>', 'safety on-call');
   ```
   The SQL editor works without this (a session with no JWT counts as a
   moderator). The row is for moderating from a signed-in session.
7. Test it: report a test profile from a second staff account, then check the
   email arrived and `select notified_at from driftdate.reports order by created_at desc limit 1;`
   is not null.

## Daily review (SQL editor, project smvvjivvlprjhzhoizym)

```sql
-- Open reports, oldest first; overdue ones are past 24 hours.
select report_id, created_at, due_at, overdue, reason, target_name, target_id,
       target_hidden, open_reports, message_text, photo_path, note
  from driftdate.moderation_queue();

-- Everything, including what was already decided.
select * from driftdate.moderation_queue(include_resolved => true) limit 100;
```

Context for a decision:

```sql
-- The whole conversation around a reported message. This works after an
-- unmatch too: the thread is kept for moderation, unreadable by the members.
select m.created_at, p.display_name, m.text
  from driftdate.messages m
  join driftdate.profiles p on p.id = m.author_id
 where m.conversation_id = '<conversation_id from the queue>'
 order by m.created_at;

-- The reported member's profile and history.
select id, display_name, dob, created_at, hidden_at, hidden_reason, banned_at
  from driftdate.profiles where id = '<target_id>';
select created_at, reason, status, resolution
  from driftdate.reports where target_id = '<target_id>' order by created_at;
```

A reported photo: Storage → bucket `driftdate-photos` → open `photo_path` (the
bucket is private; the dashboard makes a short-lived link). Do not download,
forward or copy it, especially if it may involve a minor.

## Decide and act

```sql
select driftdate.moderate_report('<report_id>', 'dismiss',        '<why>');
select driftdate.moderate_report('<report_id>', 'remove_content', '<why>');
select driftdate.moderate_report('<report_id>', 'ban',            '<why>');
```

| Decision | What it does |
|---|---|
| `dismiss` | No violation. Closes this report. If the profile was auto-hidden and fewer than 3 confirmed reporters still have open reports, it is shown again. |
| `remove_content` | Deletes the reported message, or detaches the reported photo and lists its path in `removed_photos` so it cannot be re-attached. Closes this report. Needs a message or photo report. |
| `ban` | Ejects the member: `profiles.banned_at`, hidden from everyone, `auth.users.banned_until` set 100 years ahead so they cannot sign in again, and every open report against them closed. RLS cuts off their current session at once. |

Every decision is written to `driftdate.moderation_actions` with who decided,
when and the note.

What to choose (zero tolerance, as the in-app terms promise):

| Report | Action |
|---|---|
| Sexual content involving a minor, or a member who appears to be under 18 with evidence | `ban` at once. For apparent child sexual abuse material, US law (18 U.S.C. § 2258A) requires the provider to report it to NCMEC's CyberTipline. Preserve, do not delete the evidence first, and escalate to the founder the same day. The exact reporting procedure needs the founder's legal review; it is not set up yet. |
| Threats, violence, stalking | `ban`. If someone is in danger, tell the reporter to contact 911 / local police; escalate to the founder. |
| Scam, requests for money, gift cards or crypto | `ban`. |
| Fake profile, impersonation, stolen photos | `ban` (or `remove_content` for one stolen photo if the rest of the profile is genuine). |
| Nudity or sexual photo | `remove_content`; `ban` if it is repeated or the profile exists for it. |
| Harassment, hate speech, explicit messages | `remove_content` for a single message; `ban` if severe, repeated, or more than one reporter. |
| Spam / solicitation | `ban`. |
| Nothing breaks the terms | `dismiss`, with a note. |

The reporter is not notified in the app. If they also emailed
contact@americangroup.ai or support@, reply that the report was reviewed and
acted on, without saying what happened to the other account.

## Other tasks

Hide someone without a report (for example after an email complaint), then
decide within 24 hours:

```sql
update driftdate.profiles set hidden_at = now(), hidden_reason = 'manual: <why>' where id = '<id>';
```

Undo a ban or a hide (only with a note in the issue saying why):

```sql
update driftdate.profiles set banned_at = null, hidden_at = null, hidden_reason = null where id = '<id>';
update auth.users set banned_until = null where id = '<id>';
```

A banned member asks for their data to be deleted (they cannot sign in to do
it in the app): Authentication → Users → delete the user. Everything in
`driftdate.*` cascades; their reports *about others* stay without the
reporter, and `moderation_actions` keeps the bare id and decision.

Photo files left in storage after an account deletion (the app removes them
first; this finds any it could not):

```sql
select o.name from storage.objects o
 where o.bucket_id = 'driftdate-photos'
   and not exists (select 1 from auth.users u where u.id::text = (storage.foldername(o.name))[1]);
```

Delete them from the Storage dashboard or the Storage API, not with SQL
`delete`: Supabase says to delete objects through Storage, and a SQL delete
of the row does not remove the stored file.

Is the email path working?

```sql
select count(*) filter (where notified_at is null) as not_emailed, count(*) as open
  from driftdate.reports where status = 'pending';
```

If `not_emailed` keeps growing, check Edge Functions → driftdate-report-notify
→ Logs. A `503` means the mail secrets are not set.

## Not built (options, all founder decisions)

- **Automated nudity / CSAM detection.** There is none. Photos are checked on
  the device only for quality (`photo_quality.dart`), not for content. Options
  that cost money and need a key: a moderation API (Amazon Rekognition content
  moderation, Google Cloud Vision SafeSearch, Hive, Sightengine), and for CSAM,
  hash matching (Microsoft PhotoDNA, Thorn Safer), which needs an application
  and an agreement. Charter §3/§4.
- **A moderation screen.** Moderation is SQL today. A small admin page or an
  in-app moderator view would call the same two functions.
- **Messaging rate limits and blocking links or phone numbers in the first
  messages.** The spec does not ask for them, so they were not built. They are
  recommended against spam and scams.
