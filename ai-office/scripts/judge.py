#!/usr/bin/env python3
"""The AI office's judgment agent: answers permission prompts so the founder
does not have to click yes/no all day.

Wired as a Claude Code `PermissionRequest` hook (it runs only when a tool call
would otherwise pop up a prompt). Reads the request on stdin and prints

    {"hookSpecificOutput": {"hookEventName": "PermissionRequest",
                            "decision": {"behavior": "allow"}}}
or  ... "decision": {"behavior": "deny", "message": "<why, and what to do instead>"}

Three layers, cheapest first:
  1. DENY rules   — CHARTER.md's founder-only list and the destructive commands
                    that already cost something (rsync --delete into hosting,
                    supabase config push, force-push, account-freeze overrides).
  2. ALLOW rules  — the routine work the charter says the office may do without
                    asking: read, edit inside ~/agl, flutter/dart/git/gh, the
                    manifest's own scripts, simulators, TestFlight uploads.
  3. LLM judge    — anything else goes to `claude -p` with the charter, which
                    must answer allow or deny with a reason.
If every layer fails (judge timeout, bad JSON) it prints nothing, and Claude
Code falls back to its normal prompt — never a silent allow.

Every decision is appended to ~/agl/.dist/ai-office/judge.log.

    python3 ai-office/scripts/judge.py --test     # run the rule table self-test
"""

from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import re
import shlex
import subprocess
import sys

HOME = pathlib.Path.home()
AGL = HOME / "agl"
OFFICE = pathlib.Path(__file__).resolve().parents[1]
LOG = AGL / ".dist" / "ai-office" / "judge.log"
# The `claude` on PATH is a wrapper that applies sandbox-exec, which fails
# ("sandbox_apply: Operation not permitted") when started from inside a
# session that is already sandboxed — i.e. from this hook. The judge gets no
# tools, so it runs the underlying binary directly.
_NATIVE = "/usr/local/bin/claude_code/native/claude"
CLAUDE = os.environ.get("AGL_JUDGE_CLAUDE") or (_NATIVE if os.path.exists(_NATIVE) else "claude")

# --- 1. never, whatever the context (CHARTER "Always a human" + incidents) ---
DENY = [
    (r"\brsync\b[^|;&]*--delete", "rsync --delete into hosting wipes other sites' docroots"),
    (r"\bsupabase\s+(config\s+push|db\s+push|db\s+reset)", "production Supabase changes go through the backend deploy.yml approval (CHARTER 2)"),
    (r"\b(psql|pg_dump|pg_restore)\b.*(pooler\.supabase|supabase\.co|DATABASE_URL)", "direct production SQL is a founder decision (CHARTER 2)"),
    (r"\bgit\s+push\b[^|;&]*(\s--force\b|\s-f\b|--force-with-lease|\s\+\S)", "force-push rewrites shared history"),
    (r"\bgit\s+reset\s+--hard\b", "reset --hard discards work; commit or stash instead"),
    (r"\bgit\s+clean\s+-[a-z]*[fdx]", "git clean deletes untracked work"),
    (r"--override-account-freeze", "Apple 5.6 freeze: nothing is submitted until the account holder replies (MA-043)"),
    (r"\b(submit_production|resubmit_rejected|reply_rejections)\.rb\b", "App Review submission/replies are founder decisions (CHARTER 1)"),
    (r"\bwatch_resubmit\.sh\b", "automatic resubmission is a founder decision (CHARTER 1)"),
    (r"\bgh\s+(secret|variable)\s+(set|delete|remove)", "credentials are founder decisions (CHARTER 4)"),
    (r"\bgh\s+repo\s+(delete|archive|rename)", "removing/renaming products is a founder decision (CHARTER 8)"),
    (r"\bgh\s+api\b[^|;&]*(-X|--method)\s*DELETE", "deleting GitHub resources is a founder decision"),
    (r"\bgh\s+api\b[^|;&]*environments/production", "the production environment's reviewers are the founder's (CHARTER 2)"),
    (r"\b(sendmail|mailx?|msmtp)\b\s", "external contact is a founder decision (CHARTER 5)"),
    (r"\bdart\s+format\b", "dart format rewrites whole files (CLAUDE.md: once buried 216 changes under 5,048 lines)"),
    (r"\brm\s+-[a-z]*r[a-z]*f?\s+(/|~|\$HOME|/Users/spatchava)/?(\s|$|\*)", "recursive delete of a top-level directory"),
    (r"\brm\s+-[a-z]*r[a-z]*\s+[^|;&]*(/Users/spatchava/agl|~/agl)/?(\s|$)", "recursive delete of the whole mirror (never prune ~/agl)"),
    (r"\bsudo\b", "no sudo from the office"),
    (r"zones/[0-9a-f]+/[^\s]*(nameservers|ssl)|/zones\s*-X\s*(PATCH|DELETE)", "Cloudflare zone settings are founder decisions (CHARTER 4)"),
]
# Writes into secret stores or git-tracked credentials.
DENY_PATHS = [r"/\.secrets/", r"\.p8$", r"\.jks$", r"\.keystore$", r"keystores\.json$", r"/\.ssh/", r"/\.claude/settings"]

# --- 2. routine work the charter allows -------------------------------------
SAFE_FIRST = {
    "ls", "cat", "head", "tail", "wc", "grep", "rg", "egrep", "find", "sort", "uniq", "cut", "tr", "awk", "jq",
    "diff", "cmp", "file", "stat", "du", "df", "pwd", "echo", "printf", "true", "false", "test", "[", "date",
    "which", "command", "type", "basename", "dirname", "realpath", "readlink", "env", "sleep", "xargs", "tee",
    "mkdir", "touch", "cp", "mv", "ln", "unzip", "zip", "tar", "gzip", "shasum", "md5", "plutil", "defaults",
    "sed", "python3", "python", "ruby", "bundle", "pod", "flutter", "dart", "git", "gh", "xcrun", "open",
    "pgrep", "ps", "lsof", "uptime", "vm_stat", "sysctl", "sw_vers", "security", "codesign", "curl", "wget",
    "npm", "npx", "node", "java", "keytool", "adb", "emulator", "pkill", "kill", "timeout", "nice", "caffeinate",
    "source", ".", "export", "set", "cd", "for", "while", "do", "done", "if", "then", "else", "fi", "case", "esac",
    "launchctl", "osascript", "tesseract", "sips", "magick", "convert", "identify", "ffmpeg", "rtk", "rm",
}
FLUTTER_BIN = re.compile(r"(^|/)(flutter|dart)$")
# First words that are fine only with care: decided per-command below.
GIT_BAD = {"filter-branch", "filter-repo", "gc", "prune", "update-ref", "replace"}


def _segments(cmd: str) -> list[str]:
    # Split on shell control operators; good enough for policy, not for parsing.
    cmd = re.sub(r"\$\((.*?)\)|`([^`]*)`", lambda m: " ; " + (m.group(1) or m.group(2) or "") + " ; ", cmd)
    return [s.strip() for s in re.split(r"&&|\|\||;|\||\n|\(|\)|\{|\}", cmd) if s.strip()]


def _first_word(seg: str) -> str:
    try:
        words = shlex.split(seg, posix=True)
    except ValueError:
        words = seg.split()
    while words and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", words[0]):   # VAR=value prefixes
        words = words[1:]
    return words[0] if words else ""


def _rm_ok(seg: str) -> bool:
    # rm is routine for build output and temp files; only inside ~/agl, /tmp or a temp dir.
    try:
        words = shlex.split(seg)
    except ValueError:
        return False
    targets = [w for w in words[1:] if not w.startswith("-")]
    ok_roots = (str(AGL) + "/", "/tmp/", "/private/tmp/", "/var/folders/", "/private/var/folders/", str(HOME / "Library/Developer/Xcode/DerivedData"))
    for t in targets:
        p = os.path.expanduser(t)
        if not os.path.isabs(p):
            continue              # relative: cwd is checked by the caller
        if not p.startswith(ok_roots) or p.rstrip("/") in (str(AGL),):
            return False
    return bool(targets)


def rules(tool: str, inp: dict, cwd: str) -> tuple[str, str] | None:
    """('allow'|'deny', reason) from the fixed rules, or None for the LLM judge."""
    if tool == "Bash":
        cmd = inp.get("command", "")
        for pat, why in DENY:
            if re.search(pat, cmd):
                return "deny", why
        # Inline interpreter code can do anything; the judge reads it.
        if re.search(r"\b(python3?|ruby|node|perl|osascript)\b[^|;&]*(\s-[ce]\s|\s-\s*<<|<<-?\s*'?\w+)", cmd):
            return None
        segs = _segments(cmd)
        if not segs:
            return None
        for s in segs:
            w = _first_word(s)
            base = os.path.basename(w)
            if not (base in SAFE_FIRST or FLUTTER_BIN.search(w) or w.startswith(("./", str(AGL)))):
                return None
            if base == "git":
                sub = re.findall(r"\bgit\s+(?:-C\s+\S+\s+)?([a-z-]+)", s)
                if sub and sub[0] in GIT_BAD:
                    return None
            if base == "rm" and not (_rm_ok(s) and (cwd.startswith(str(AGL)) or cwd.startswith("/tmp"))):
                return None
            if base in ("launchctl", "osascript", "security", "kill", "pkill", "curl", "wget", "defaults"):
                return None   # system-level or outward: let the judge read it
        return "allow", "routine command"
    if tool in ("Read", "Glob", "Grep", "LS", "NotebookRead", "TodoWrite", "WebSearch", "ToolSearch"):
        return "allow", "read-only"
    if tool in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        path = inp.get("file_path") or inp.get("notebook_path") or ""
        if any(re.search(p, path) for p in DENY_PATHS):
            return "deny", "secrets, keys and Claude settings are edited by the founder only"
        if path.startswith((str(AGL) + "/", "/tmp/", "/private/tmp/", str(HOME / ".claude/projects/"))):
            return "allow", "edit inside the workspace"
        return None
    return None


def llm(tool: str, inp: dict, cwd: str) -> tuple[str, str] | None:
    charter = (OFFICE / "CHARTER.md").read_text(errors="ignore")
    prompt = f"""You are the judgment agent of the American Group LLC AI office. A coding agent
wants to run a tool call that needs permission. Decide ALLOW or DENY using the
charter below. ALLOW routine engineering work the charter permits (code, tests,
builds, TestFlight/Play internal uploads, screenshots, listing text, website
deploy without --delete, reading anything). DENY anything on the founder-only
list, anything destructive or irreversible outside ~/agl build output, anything
that sends messages to people, spends money, touches credentials, production
data, or App Review submission/replies. When unsure whether it is destructive,
DENY and say what safer step to take.

CHARTER:
{charter[:6000]}

REQUEST:
cwd: {cwd}
tool: {tool}
input: {json.dumps(inp)[:4000]}

Answer with ONE line of JSON only: {{"decision": "allow" or "deny", "reason": "<one sentence>"}}"""
    try:
        r = subprocess.run([CLAUDE, "-p", prompt, "--model", os.environ.get("AGL_JUDGE_MODEL", "haiku"),
                            "--max-turns", "1", "--disallowedTools", "Bash,Edit,Write,Read,Glob,Grep,WebFetch,WebSearch,Agent"],
                           capture_output=True, text=True, timeout=int(os.environ.get("AGL_JUDGE_TIMEOUT", "45")),
                           env={**os.environ, "AGL_JUDGE_ACTIVE": "1"})
        m = re.search(r"\{[^{}]*\"decision\"[^{}]*\}", r.stdout)
        if not m:
            return None
        d = json.loads(m.group(0))
        if d.get("decision") in ("allow", "deny"):
            return d["decision"], "judge: " + str(d.get("reason", ""))[:300]
    except Exception:
        return None
    return None


def log(entry: dict) -> None:
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a") as fh:
            fh.write(json.dumps(entry) + "\n")
    except OSError:
        pass


def main() -> int:
    if "--test" in sys.argv:
        return selftest()
    if os.environ.get("AGL_JUDGE_ACTIVE"):     # the judge's own claude -p must not recurse
        return 0
    try:
        req = json.load(sys.stdin)
    except Exception:
        return 0
    tool = req.get("tool_name", "")
    inp = req.get("tool_input") or {}
    cwd = req.get("cwd") or os.getcwd()
    verdict = rules(tool, inp, cwd)
    layer = "rules"
    if verdict is None:
        verdict, layer = llm(tool, inp, cwd), "llm"
    log({"at": dt.datetime.now().isoformat(timespec="seconds"), "tool": tool,
         "input": (inp.get("command") or inp.get("file_path") or json.dumps(inp))[:300],
         "cwd": cwd, "layer": layer, "verdict": verdict})
    if verdict is None:
        return 0                                   # fall back to the normal prompt
    behavior, reason = verdict
    decision = {"behavior": behavior}
    if behavior == "deny":
        decision["message"] = (f"AI office judge denied this: {reason}. If the founder must decide, "
                               "write it up with the approval-workflow skill instead of retrying.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PermissionRequest", "decision": decision}}))
    return 0


CASES = [
    ("Bash", {"command": "cd ~/agl/Verba && /Users/spatchava/agl/.flutter-sdk/bin/flutter test"}, "allow"),
    ("Bash", {"command": "git add lib/a.dart && git commit -m x -- lib/a.dart && git push"}, "allow"),
    ("Bash", {"command": "python3 scripts/store_health.py | tail -5"}, "allow"),
    ("Bash", {"command": "bundle exec ruby scripts/testflight/asc_urls.rb --check"}, "allow"),
    ("Bash", {"command": "rm -rf /Users/spatchava/agl/Verba/build"}, "allow"),
    ("Bash", {"command": "git push --force origin main"}, "deny"),
    ("Bash", {"command": "git push -f"}, "deny"),
    ("Bash", {"command": "rsync -az --delete dist/ host:public_html/"}, "deny"),
    ("Bash", {"command": "supabase config push --project-ref x"}, "deny"),
    ("Bash", {"command": "bundle exec ruby scripts/testflight/submit_production.rb --all"}, "deny"),
    ("Bash", {"command": "ruby resubmit_rejected.rb --override-account-freeze"}, "deny"),
    ("Bash", {"command": "gh secret set ASC_KEY_ID -b x"}, "deny"),
    ("Bash", {"command": "dart format lib/"}, "deny"),
    ("Bash", {"command": "rm -rf ~/agl"}, "deny"),
    ("Bash", {"command": "sudo launchctl load x"}, "deny"),
    ("Bash", {"command": "git reset --hard origin/main"}, "deny"),
    ("Bash", {"command": "launchctl load -w ~/Library/LaunchAgents/x.plist"}, None),
    ("Bash", {"command": "python3 - <<'EOF'\nimport shutil\nEOF"}, None),
    ("Bash", {"command": "python3 -c 'import os'"}, None),
    ("Bash", {"command": "terraform apply"}, None),
    ("Bash", {"command": "rm -rf /etc/hosts"}, None),
    ("Edit", {"file_path": "/Users/spatchava/agl/Verba/lib/main.dart"}, "allow"),
    ("Write", {"file_path": "/Users/spatchava/agl/.secrets/cloudflare-token"}, "deny"),
    ("Write", {"file_path": "/etc/hosts"}, None),
    ("Read", {"file_path": "/anything"}, "allow"),
]


def selftest() -> int:
    bad = 0
    for tool, inp, want in CASES:
        got = rules(tool, inp, str(AGL / "agl-manifest"))
        got = got[0] if got else None
        ok = got == want
        bad += not ok
        print(f"  {'ok ' if ok else 'BAD'} {tool:5} {want or 'judge':6} got {got or 'judge':6} {json.dumps(inp)[:80]}")
    print(f"\n  {len(CASES) - bad}/{len(CASES)} rule cases pass")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
