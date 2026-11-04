#!/usr/bin/env python3
"""Hook 5, env-guard. PreToolUse, matcher "Read|Edit|Write|Bash".

Keep Claude out of .env files, so secrets never reach the chat or get rewritten. Blocks a file
path or a shell command that names .env, .env.local, .env* or .ENV. .env.example stays readable.
Exit 2 blocks the tool call.
"""
import json
import re
import sys

inp = json.load(sys.stdin).get("tool_input", {})
target = inp.get("file_path") or inp.get("command") or ""
if re.search(r"(^|[\s/'\"=<>])\.env(?!\.example)(\.[\w-]+)?[*?]*(?=$|[\s'\";|&)])", target, re.I):
    print("Blocked by env-guard: .env holds secrets and is off limits. "
          "Ask the user for the value, or read .env.example.", file=sys.stderr)
    sys.exit(2)
