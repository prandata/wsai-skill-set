#!/usr/bin/env bash
# The sample, run twice: run 1 is stopped with a STOP file right after its first checkpoint,
# run 2 resumes from HANDOFF.md and finishes. Works on a scratch copy of sample/, so the
# sample itself is never changed. Spends real money (the saved logs cost under $0.10 on sonnet).
# Usage: ./demo.sh [model]     (default model: sonnet)
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
model="${1:-sonnet}"
scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT
work="$scratch/todo-repo"
mkdir -p "$work" "$here/sample/logs"
cp "$here/sample/TASK.md" "$here/sample/TODO.md" "$work/"
limits=(--model "$model" --budget-usd 0.50 --total-budget-usd 1.00 --session-minutes 8)

snapshot() {  # $1 = log file
  { echo; echo "---- HANDOFF.md after this run ----"; cat "$work/HANDOFF.md"
    echo; echo "---- TODO.md after this run ----"; cat "$work/TODO.md"
    echo; echo "---- .overnight/runs.jsonl ----"; cat "$work/.overnight/runs.jsonl"; } >> "$1"
}

# Dry run first: creates HANDOFF.md, prints the command, calls nothing.
python3 "$here/run.py" "$work" --init --dry-run "${limits[@]}" > "$here/sample/logs/dry-run.txt"

# Run 1, interrupted. A second process watches HANDOFF.md and creates STOP at the first checkpoint.
log1="$here/sample/logs/run-1.txt"
echo "# run 1: interrupted with 'touch todo-repo/STOP' once HANDOFF.md shows Run: 1" > "$log1"
python3 "$here/run.py" "$work" --max-sessions 1 "${limits[@]}" >> "$log1" 2>&1 &
runner=$!
for _ in $(seq 1 480); do
  kill -0 "$runner" 2>/dev/null || break
  if grep -q '^Run: 1' "$work/HANDOFF.md"; then
    echo "[$(date +%H:%M:%S)] (demo) first checkpoint seen; touch todo-repo/STOP" >> "$log1"
    touch "$work/STOP"; break
  fi
  sleep 1
done
wait "$runner" || echo "(runner exit $?)" >> "$log1"
snapshot "$log1"

# Run 2: remove STOP, run again. It resumes from HANDOFF.md, not from run 1's transcript.
log2="$here/sample/logs/run-2.txt"
rm -f "$work/STOP"
echo "# run 2: STOP removed, same command again" > "$log2"
python3 "$here/run.py" "$work" --max-sessions 2 "${limits[@]}" >> "$log2" 2>&1 || echo "(runner exit $?)" >> "$log2"
snapshot "$log2"
echo "logs: sample/logs/run-1.txt sample/logs/run-2.txt"
