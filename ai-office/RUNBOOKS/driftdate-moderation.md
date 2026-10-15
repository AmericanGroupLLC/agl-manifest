# DriftDate moderation: reports, hiding, bans (24-hour SLA)

DriftDate is a real dating app (founder, 2026-10-14). App Store guideline 1.2
requires the developer to act on reports of objectionable content **within 24
hours**, by removing the content and ejecting the user who posted it. This is
how a person does that. Everything below exists in Backend PR #1 (branch
`driftdate-schema`: `supabase/migrations/20261014_driftdate_3_safety.sql` and
`.github/workflows/driftdate-moderation-alerts.yml`), and **none of it works
until PR #1 is merged and deployed** (issue #19).

**Moderator: the founder (GitHub `srpatcha`) by default.** Office decision,
2026-10-14, under the amended charter. Alerts arrive as a GitHub issue in the
private repository AmericanGroupLLC/AmericanGroupLLC-Backend. Per-report
email through Resend is **optional** and not set up: it needs a vendor
account nobody has created. The moderator runs the SQL below in the Supabase
SQL editor. The AI office does not run SQL on production
(company/policies.md); it can prepare the statements and read the issue.

## The SLA

- Every report must be **actioned or dismissed within 24 hours of
  `created_at`**. `moderation_queue()` returns `due_at` (created + 24 h) and
  `overdue`.
- The alert issue is checked every 30 minutes. GitHub can start scheduled
  runs late, by minutes and sometimes longer, so act on the issue the day it
  appears, not at hour 23. Also look at the queue **at least once a day**
  even with no alert: the issue is a prompt, the `driftdate.reports` table
  is the system of record.
- Child safety ("Appears to be under 18") and threats of violence go first,
  the moment they are seen. The issue marks under-18 reports "review first".

## How a report reaches a person

1. A member reports a profile, a photo (`photo_path`) or a message
   (`message_id`, with the text copied into `message_text` at report time).
   Reporting also blocks the person for the reporter.
2. **GitHub issue.** Every 30 minutes the workflow *DriftDate — moderation
   alerts* (Backend repo → Actions) reads `driftdate.moderation_queue()` and
   keeps one open issue, **"DriftDate: reports waiting for review"**, label
   `moderation`, assigned to the moderators:
   - first open report: the issue is created and the moderators are
     @-mentioned. GitHub emails them (new issue, assignment, mention);
   - every run: the table in the issue is rewritten (report id, reason, age,
     due time in UTC, overdue);
   - a report that is new since the last run, or that has just passed 24
     hours: **one comment** naming it, with an @-mention, which emails the
     moderators again. (Editing the table alone sends no email.);
   - queue empty: the workflow comments and closes the issue. The next
     report opens a new one.

   The issue holds **no personal data**: only opaque report ids, the reason
   (one of the app's fixed reasons; anything typed in by a client shows as
   "Other (custom text…)"), ages and due times. No names, member or
   reporter ids, notes, message text or photos. Keep it that way: never
   paste a name, message or screenshot into an issue comment. The decision
   note goes into `moderate_report(…, '<why>')`.

   If the database secret is missing, the connection fails or the query
   fails, the run goes **red**, and GitHub emails whoever last changed the
   workflow's schedule (normally the founder's account). A red
   run means nobody is being alerted: fix it the same day (see "Is the alert
   path working?").
3. **Auto-hide.** When 3 distinct members with a confirmed email or phone have
   open reports against the same person, that profile is hidden at once:
   nobody sees it, and it cannot wave or send messages until a moderator
   decides. The trigger writes `moderation_actions` row `auto_hide`.
4. Optional: per-report email (see the end of the setup section). Without
   it, a report insert still always succeeds; the database skips the email
   silently.

## One-time setup

1. Merge PR #1 into `dev` and approve the deploy (issue #19 / MA-044).
   Scheduled workflows only run from the default branch (`dev`), so the
   alerts start with the merge. Until the migrations are deployed, each run
   is red ("moderation_queue() failed"), which is intended.
2. The repository secret **`DATABASE_URL_SESSION`** must hold a working
   Session pooler connection string (Supabase → Connect → Session pooler),
   the same secret `deploy.yml` uses. This is the founder's connection-string
   step for the deploy. Nothing else is needed: the workflow uses only the
   built-in `GITHUB_TOKEN`.
3. The moderator makes sure GitHub emails reach them: Settings →
   Notifications → Email enabled for "Participating, @mentions and custom".
   Assignment and @-mentions notify even without watching the repository.
4. Test it: Actions → *DriftDate — moderation alerts* → Run workflow. Green
   with "open reports: 0" means the connection works. Then report a test
   profile from a second staff account, run it again, and check that the
   issue and the email arrive. Dismiss the test report; the next run closes
   the issue.
5. Optional, only to moderate from a signed-in app session (the SQL editor
   does not need it; a session with no JWT counts as a moderator). The
   DriftDate account id comes from Authentication → Users:
   ```sql
   insert into driftdate.moderators (user_id, note) values ('<auth user id>', 'safety on-call');
   ```

### Add another moderator later

1. GitHub: give the person at least **Read** access to
   AmericanGroupLLC-Backend (the repository is private). Then set the
   repository variable `DRIFTDATE_MODERATORS` (Settings → Secrets and
   variables → Actions → Variables) to a comma-separated list of logins,
   keeping the founder: `srpatcha,<their-login>`. The next run assigns and
   @-mentions everyone in the list. A login without access is skipped with a
   warning in the run log.
2. Supabase: invite them to the project (Organization → Team) so they can
   open the SQL editor, or add their DriftDate account to
   `driftdate.moderators` (step 5 above) once there is an in-app moderator
   view.
3. Removing someone: take them out of the variable and the team, and
   `delete from driftdate.moderators where user_id = '<id>';`.

### Optional: per-report email (Resend)

The Edge Function `driftdate-report-notify` and the trigger
`driftdate.reports_notify` stay in the code. They send one email per report
to support@americangroup.ai with the reason, the reported member's id and the
deadline. Without the steps below the trigger does nothing, and a report insert
never fails: covered by `supabase/tests/driftdate_rls_pglite.mjs` (no pg_net,
pg_net without Vault, Vault without secrets, only the URL secret, an
unreadable Vault, a failing call). The migration does not enable pg_net,
because the alert issue does not need it. Only if email is wanted as well:

1. Database → Extensions: enable **pg_net**. (Vault is on by default.)
2. A Resend account (`api.resend.com`), with `americangroup.ai` or a
   subdomain verified. Not created: it needs a sign-up with the founder's
   identity. Check Resend's pricing first.
3. Deploy the function and set its secrets. Never paste a secret into git or
   chat:
   ```
   supabase functions deploy driftdate-report-notify --no-verify-jwt --project-ref smvvjivvlprjhzhoizym
   supabase secrets set --project-ref smvvjivvlprjhzhoizym \
     DRIFTDATE_REPORT_WEBHOOK_SECRET=<long random string> \
     RESEND_API_KEY=<key from the provider> \
     REPORT_MAIL_FROM='DriftDate safety <safety@americangroup.ai>' \
     REPORT_MAIL_TO=support@americangroup.ai
   ```
4. SQL editor: store the same secret and the function URL in Vault:
   ```sql
   select vault.create_secret('https://smvvjivvlprjhzhoizym.supabase.co/functions/v1/driftdate-report-notify',
                              'driftdate_report_notify_url');
   select vault.create_secret('<the same long random string>', 'driftdate_report_notify_secret');
   ```
5. Report a test profile and check
   `select notified_at from driftdate.reports order by created_at desc limit 1;`
   is not null.

## Review a report from the issue

1. Open the issue, oldest row first. Under-18 and threat reports come first
   whatever their age.
2. In the Supabase SQL editor, look up the report by its id (queries below):
   who was reported, the message text or photo path, and how many open reports
   the person has.
3. Read the context (the conversation, the profile, the photo) and choose
   `dismiss`, `remove_content` or `ban` with the table in "Decide and act".
4. Run `moderate_report` with a short note. Within 30 minutes the report
   leaves the issue; when the last one is decided, the issue closes itself.

## Daily review (SQL editor, project smvvjivvlprjhzhoizym)

```sql
-- Open reports, oldest first; overdue ones are past 24 hours.
select report_id, created_at, due_at, overdue, reason, target_name, target_id,
       target_hidden, open_reports, message_text, photo_path, note
  from driftdate.moderation_queue();

-- One report from the issue.
select * from driftdate.moderation_queue() where report_id = '<report id from the issue>';

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

Is the alert path working?

- Backend repo → Actions → *DriftDate — moderation alerts*: the runs should
  be green every ~30 minutes. A red run says why in its log:
  - "secret DATABASE_URL_SESSION is missing or empty": set the secret.
  - "could not connect with DATABASE_URL_SESSION": the connection string or
    password is wrong, or Supabase moved the project to another pooler.
    Copy the Session pooler string again from Supabase → Connect.
  - "moderation_queue() failed": the DriftDate migrations are not deployed
    (or a migration broke the function).
- No runs at all: scheduled workflows run only from `dev`; check that the
  workflow file is on `dev` and the workflow is not disabled in the Actions
  tab.

Optional email path only (if it was set up):

```sql
select count(*) filter (where notified_at is null) as not_emailed, count(*) as open
  from driftdate.reports where status = 'pending';
```

If `not_emailed` keeps growing, check Edge Functions → driftdate-report-notify
→ Logs. A `503` means the mail secrets are not set.

## Not built (options)

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
