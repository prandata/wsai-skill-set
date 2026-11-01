#!/usr/bin/env bash
# Runs one repro-reviewer example on a fresh tinyshop and saves a readable log next to this script.
#   bash run-example.sh 01-real-bug       (or 02-false-alarm, 03-cannot-run)
# Needs Claude Code signed in. MODEL picks the model (default: opus).
#
# The run is isolated from your own setup, so the log shows only the agent:
#   CLAUDE_CODE_DISABLE_CLAUDE_MDS=1   no CLAUDE.md files (yours or any parent folder's)
#   --setting-sources project          no user settings: your hooks, plugins and output style stay out
#   --strict-mcp-config                no MCP servers
#   --disable-slash-commands           no skills
#   --agent repro-reviewer             the session runs as the agent: its prompt and its tool list
#   --permission-mode dontAsk + --allowedTools Bash Read
#                                      Bash and Read run without prompts; anything else is refused
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)
name=${1:?usage: run-example.sh 01-real-bug|02-false-alarm|03-cannot-run}
model=${MODEL:-opus}

case "$name" in
  01-real-bug)
    branch=real-bug
    prompt="Review the last commit on this branch." ;;
  02-false-alarm)
    branch=false-alarm
    prompt="Review the last commit on this branch. There is one comment on the pull request, from a lint bot: \"parse_duration('90s') returns 9, because the regex only captures a single digit. Please fix before merging.\"" ;;
  03-cannot-run)
    branch=cannot-run
    prompt="Review the last commit on this branch." ;;
  *) echo "unknown example: $name" >&2; exit 2 ;;
esac

work=$(mktemp -d)
repo="$work/tinyshop"
trap 'rm -rf "$work"' EXIT

bash "$here/make-sample-repo.sh" "$repo" > /dev/null
git -C "$repo" checkout -q "$branch"
mkdir -p "$repo/.claude/agents"
cp "$here/../repro-reviewer.md" "$repo/.claude/agents/"
echo ".claude/" >> "$repo/.git/info/exclude"   # keeps the review tree clean
sha=$(git -C "$repo" rev-parse HEAD)

run=(claude -p "$prompt" --agent repro-reviewer --model "$model"
     --setting-sources project --strict-mcp-config --disable-slash-commands
     --permission-mode dontAsk --allowedTools Bash Read
     --no-session-persistence --output-format stream-json --verbose)
limit=()
command -v timeout > /dev/null && limit=(timeout 1200)

started=$(date -u +%Y-%m-%dT%H:%M:%SZ)
set +e
(cd "$repo" && CLAUDE_CODE_DISABLE_CLAUDE_MDS=1 CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 \
  ${limit[@]+"${limit[@]}"} "${run[@]}" < /dev/null > "$work/stream.jsonl" 2> "$work/stderr.txt")
status=$?
set -e

python3 "$here/render_log.py" "$work/stream.jsonl" \
  --name "$name" --branch "$branch" --sha "$sha" --prompt "$prompt" \
  --started "$started" --exit "$status" --version "$(claude --version)" \
  --mask "$repo=/tmp/tinyshop" --mask "$work=/tmp/run" --mask "$HOME=~" --mask "$(id -un)=user" \
  > "$here/$name.log"
echo "exit $status; log: $here/$name.log"
[ "$status" -eq 0 ] || { tail -5 "$work/stderr.txt" >&2; exit "$status"; }
