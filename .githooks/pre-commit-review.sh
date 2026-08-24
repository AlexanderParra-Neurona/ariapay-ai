#!/usr/bin/env bash
# PreToolUse(Bash, git commit*) hook: runs a headless code review of the
# staged diff via a local Ollama model, logs the result, and blocks the
# commit on real findings.
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
LOG_FILE="$REPO_ROOT/.githooks/review-log.md"
TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"
OLLAMA_MODEL="${OLLAMA_REVIEW_MODEL:-ornith-1.5:9b}"

DIFF="$(git diff --cached)"
if [ -z "$DIFF" ]; then
  exit 0
fi

PROMPT="Review the following staged git diff for correctness bugs and significant quality issues.

Respond in this exact format:
VERDICT: OK or VERDICT: BLOCK
Then, if BLOCK, a short bullet list of issues, each with file:line and a one-line fix suggestion. If OK, one line saying why it's clean.

Be strict about only blocking on real problems (bugs, broken logic, security issues), not style preferences.

DIFF:
$DIFF"

REVIEW_OUTPUT="$(ollama run "$OLLAMA_MODEL" "$PROMPT" < /dev/null 2>&1)" || REVIEW_OUTPUT="VERDICT: BLOCK
- Review agent failed to run (see error below); fix the pre-commit hook or re-run.
$REVIEW_OUTPUT"

ENTRY="$(
  echo "## $TIMESTAMP"
  echo
  echo "$REVIEW_OUTPUT"
  echo
  echo "---"
  echo
)"

if [ -f "$LOG_FILE" ]; then
  printf '%s\n%s' "$ENTRY" "$(cat "$LOG_FILE")" > "$LOG_FILE"
else
  printf '%s\n' "$ENTRY" > "$LOG_FILE"
fi

if echo "$REVIEW_OUTPUT" | grep -q "^VERDICT: BLOCK"; then
  echo "$REVIEW_OUTPUT" >&2
  echo "" >&2
  echo "Commit blocked by pre-commit review. Full log: $LOG_FILE" >&2
  exit 2
fi

CHANGELOG_FILE="$REPO_ROOT/CHANGELOG.md"
TODAY="$(date '+%Y-%m-%d')"

CHANGELOG_PROMPT="Classify the user-facing effect of this staged git diff into Keep a Changelog categories: Added, Changed, Deprecated, Removed, Fixed, Security.

Output ONLY lines in this exact format, one per notable change, nothing else (no preamble, no markdown fences, no explanation):
Category: one-line human-readable description of the impact (not the implementation)

Rules:
- Category must be exactly one of: Added, Changed, Deprecated, Removed, Fixed, Security
- Skip formatting-only, CI config, test-only, chore/lint changes with no user-facing effect
- If nothing notable, output exactly: NONE

DIFF:
$DIFF"

CHANGELOG_LINES="$(ollama run "$OLLAMA_MODEL" "$CHANGELOG_PROMPT" < /dev/null 2>/dev/null || true)"

if [ -n "$CHANGELOG_LINES" ] && ! echo "$CHANGELOG_LINES" | grep -q "^NONE$"; then
  [ -f "$CHANGELOG_FILE" ] || printf '# Changelog\n\nAll notable changes to this project will be documented in this file.\n\nThe format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),\nand this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).\n\n## [Unreleased]\n' > "$CHANGELOG_FILE"

  grep -q "^## \[Unreleased\]" "$CHANGELOG_FILE" || sed -i.bak "1a\\
\\
## [Unreleased]
" "$CHANGELOG_FILE"

  CHANGELOG_LINES="$CHANGELOG_LINES" python3 - "$CHANGELOG_FILE" "$TODAY" <<'PYEOF'
import os, re, sys

path, today = sys.argv[1], sys.argv[2]
lines = os.environ["CHANGELOG_LINES"].strip().splitlines()

order = ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"]
entries = {}
for line in lines:
    if ":" not in line:
        continue
    cat, desc = line.split(":", 1)
    cat, desc = cat.strip(), desc.strip()
    if cat in order and desc:
        entries.setdefault(cat, []).append(desc)

if not entries:
    sys.exit(0)

text = open(path).read()
un_match = re.search(r"^## \[Unreleased\]\n", text, re.M)
if not un_match:
    sys.exit(0)

un_start = un_match.end()
next_version = re.search(r"^## \[", text[un_start:], re.M)
un_end = un_start + next_version.start() if next_version else len(text)
unreleased_block = text[un_start:un_end]

date_heading = f"### {today}\n"
date_match = re.search(rf"^{re.escape(date_heading)}", unreleased_block, re.M)

if date_match:
    day_start = date_match.end()
    next_day = re.search(r"^### ", unreleased_block[day_start:], re.M)
    day_end = day_start + next_day.start() if next_day else len(unreleased_block)
    day_block = unreleased_block[day_start:day_end]
else:
    day_block = ""
    day_start = day_end = None

existing_by_cat = {}
for cat in order:
    m = re.search(rf"^#### {re.escape(cat)}\n", day_block, re.M)
    if not m:
        continue
    b_start = m.end()
    next_cat = re.search(r"^#### ", day_block[b_start:], re.M)
    b_end = b_start + next_cat.start() if next_cat else len(day_block)
    bullets = [l for l in day_block[b_start:b_end].splitlines() if l.strip()]
    existing_by_cat[cat] = bullets

for cat, descs in entries.items():
    existing_by_cat.setdefault(cat, []).extend(f"- {d}" for d in descs)

day_block = "".join(
    f"#### {cat}\n" + "\n".join(existing_by_cat[cat]) + "\n\n"
    for cat in order
    if cat in existing_by_cat
)

if date_match:
    unreleased_block = unreleased_block[:day_start] + "\n" + day_block + unreleased_block[day_end:]
else:
    unreleased_block = "\n" + date_heading + "\n" + day_block + unreleased_block.lstrip("\n")

text = text[:un_start] + unreleased_block + text[un_end:]
open(path, "w").write(text)
PYEOF

  rm -f "$CHANGELOG_FILE.bak"
  git add "$CHANGELOG_FILE" 2>/dev/null || true
fi

exit 0
