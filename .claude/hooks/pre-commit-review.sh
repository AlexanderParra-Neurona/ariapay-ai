#!/usr/bin/env bash
# PreToolUse(Bash, git commit*) hook: runs a headless code review of the
# staged diff, logs the result, and blocks the commit on real findings.
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
LOG_FILE="$REPO_ROOT/.claude/review-log.md"
TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"

DIFF="$(git diff --cached)"
if [ -z "$DIFF" ]; then
  exit 0
fi

PROMPT="Review the following staged git diff for correctness bugs and significant quality issues. Read referenced files if needed for context.

Respond in this exact format:
VERDICT: OK or VERDICT: BLOCK
Then, if BLOCK, a short bullet list of issues, each with file:line and a one-line fix suggestion. If OK, one line saying why it's clean.

Be strict about only blocking on real problems (bugs, broken logic, security issues), not style preferences.

DIFF:
$DIFF"

REVIEW_OUTPUT="$(claude -p "$PROMPT" < /dev/null 2>&1)" || REVIEW_OUTPUT="VERDICT: BLOCK
- Review agent failed to run (see error below); fix the pre-commit hook or re-run.
$REVIEW_OUTPUT"

{
  echo "## $TIMESTAMP"
  echo
  echo "$REVIEW_OUTPUT"
  echo
  echo "---"
  echo
} >> "$LOG_FILE"

if echo "$REVIEW_OUTPUT" | grep -q "^VERDICT: BLOCK"; then
  echo "$REVIEW_OUTPUT" >&2
  echo "" >&2
  echo "Commit blocked by pre-commit review. Full log: $LOG_FILE" >&2
  exit 2
fi

exit 0
