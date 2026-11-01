#!/usr/bin/env bash
# ssh-key-audit: compare the SSH public keys GitHub publishes for a user
# (https://github.com/<user>.keys) with the public key files in ~/.ssh, and flag old key types.
#
# Read-only, always. It writes no file, changes no setting, uploads nothing and deletes nothing.
# --dry-run is accepted and is the default; there is no other mode.
#
# Exit codes:
#   0  every GitHub key has a matching local .pub file, and no key is an old type
#   1  findings: a GitHub key with no local .pub file, an old-type key, or a key it could not read
#   2  usage error, bad username, or a missing tool (curl, ssh-keygen, awk)
#   3  GitHub has no user with that name (HTTP 404)
#   4  network error, unexpected HTTP status, or a response that is not a key list
#   5  the user exists but has no SSH keys on GitHub, so there was nothing to compare
set -u
set -o pipefail

# The audit only reads public keys. It never needs your ssh-agent, so it drops the pointer to it.
unset SSH_AUTH_SOCK

PROG="audit.sh"
SSH_DIR="${HOME:-}/.ssh"
user=""

# There are no here-documents in this script: bash writes each one to a temporary file.
usage() {
  printf '%s\n' \
    'Usage: audit.sh [--dry-run] [--ssh-dir DIR] <github-username>' \
    '' \
    'Compares the SSH keys on https://github.com/<github-username>.keys with the *.pub files' \
    'in ~/.ssh (or DIR), by SHA256 fingerprint, and flags DSA keys and RSA keys under 3072 bits.' \
    '' \
    '  --dry-run      The default and only mode. Nothing is ever changed.' \
    '  --ssh-dir DIR  Read *.pub files from DIR instead of ~/.ssh.' \
    '  -h, --help     Show this help.' \
    '' \
    'Exit codes: 0 clean, 1 findings, 2 usage, 3 no such user, 4 network or bad response,' \
    '5 no SSH keys on GitHub.'
}

die() { # die <exit-code> <message>
  echo "$PROG: ERROR: $2" >&2
  exit "$1"
}

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) shift ;;
    --ssh-dir)
      [ $# -ge 2 ] || die 2 "--ssh-dir needs a directory"
      SSH_DIR="$2"; shift 2 ;;
    --ssh-dir=*) SSH_DIR="${1#*=}"; shift ;;
    -h|--help) usage; exit 0 ;;
    --apply|--fix|--delete|--remove|--write|--no-dry-run)
      die 2 "$1: there is no write mode. This script only reads. To remove a key, use GitHub Settings, then SSH and GPG keys." ;;
    -*) usage >&2; die 2 "unknown option: $1" ;;
    *)
      [ -z "$user" ] || die 2 "give one username, not several"
      user="$1"; shift ;;
  esac
done

[ -n "$user" ] || { usage >&2; die 2 "missing GitHub username"; }

# GitHub usernames: letters, digits and hyphens, at most 39 characters, not starting with a hyphen.
# Checking this first also stops anything else being put into the URL.
case "$user" in
  -*|*[!A-Za-z0-9-]*) die 2 "'$user' is not a valid GitHub username (letters, digits and hyphens only)" ;;
esac
[ "${#user}" -le 39 ] || die 2 "'$user' is longer than 39 characters, the GitHub limit"

for tool in curl ssh-keygen awk; do
  command -v "$tool" >/dev/null 2>&1 || die 2 "$tool is not installed or not on PATH"
done

NL='
'
TAB='	'

# old_reason <type> <bits>: prints why a key type is old, or nothing.
old_reason() {
  case "$1" in
    DSA) echo "DSA: GitHub no longer supports it, and OpenSSH 10.0 removed it" ;;
    RSA)
      if [ -n "$2" ] && [ "$2" -lt 3072 ] 2>/dev/null; then
        echo "RSA $2 bits: under 3072, the ssh-keygen default since OpenSSH 8.0"
      fi ;;
  esac
}

# fingerprint_line <one public key line>: prints "fingerprint<TAB>TYPE<TAB>bits" or fails.
# Uses ssh-keygen. For DSA keys, which OpenSSH 10 no longer parses, it computes the same
# SHA256 fingerprint (base64 of the SHA-256 of the key blob, no padding) with openssl.
fingerprint_line() {
  local line="$1" out bits fp type ktype blob
  if out=$(printf '%s\n' "$line" | ssh-keygen -E sha256 -lf - 2>/dev/null) && [ -n "$out" ]; then
    bits=$(printf '%s\n' "$out" | awk 'NR==1{print $1}')
    fp=$(printf '%s\n' "$out" | awk 'NR==1{print $2}')
    type=$(printf '%s\n' "$out" | awk 'NR==1{t=$NF; gsub(/[()]/, "", t); print t}')
    printf '%s\t%s\t%s\n' "$fp" "$type" "$bits"
    return 0
  fi
  ktype=$(printf '%s\n' "$line" | awk '{print $1}')
  blob=$(printf '%s\n' "$line" | awk '{print $2}')
  [ "$ktype" = "ssh-dss" ] || return 1
  command -v openssl >/dev/null 2>&1 || return 1
  # A real ssh-dss blob (RFC 4253, section 6.6) is the string "ssh-dss" then four numbers p, q, g, y,
  # each a 4-byte length and that many bytes, filling the blob exactly. Anything else is unreadable.
  case "$blob" in
    *[!A-Za-z0-9+/=]*) return 1 ;;
    AAAAB3NzaC1kc3M*) ;;
    *) return 1 ;;
  esac
  printf '%s' "$blob" | openssl base64 -d -A 2>/dev/null | od -An -v -tu1 | awk '
    { for (i = 1; i <= NF; i++) b[n++] = $i }
    END {
      pos = 0
      for (field = 0; field < 5; field++) {
        if (pos + 4 > n) exit 1
        len = ((b[pos] * 256 + b[pos+1]) * 256 + b[pos+2]) * 256 + b[pos+3]
        pos += 4
        if (len < 1 || pos + len > n) exit 1
        if (field == 0 && len != 7) exit 1
        if (field == 1 && len < 64) exit 1   # p: at least 512 bits
        pos += len
      }
      exit (pos == n ? 0 : 1)
    }' || return 1
  fp=$(printf '%s' "$blob" | openssl base64 -d -A 2>/dev/null | openssl dgst -sha256 -binary 2>/dev/null \
    | openssl base64 -A 2>/dev/null | tr -d '=')
  [ -n "$fp" ] || return 1
  printf 'SHA256:%s\tDSA\t\n' "$fp"
}

# ---------- 1. Fetch the GitHub side ----------
# -q must come first: it stops curl reading ~/.curlrc, which could otherwise add an output file,
# a cookie jar or a trace file to this run.
url="https://github.com/${user}.keys"
resp=$(curl -q -sS -L --proto '=https' --proto-redir '=https' --max-time 20 -w "${NL}%{http_code}" "$url")
rc=$?
if [ "$rc" -ne 0 ]; then
  die 4 "could not reach $url (curl exit $rc). Check your connection; the audit did not run."
fi
code="${resp##*$NL}"
body="${resp%"$NL"*}"
case "$code" in
  200) ;;
  404) die 3 "GitHub has no user named '$user' (HTTP 404). Check the spelling; the audit did not run." ;;
  *) die 4 "$url returned HTTP $code. The audit did not run." ;;
esac

body=$(printf '%s' "$body" | tr -d '\r')
gh_lines=""
# Split on newlines with globbing off (set -f), so no line is expanded as a file pattern.
# Empty lines drop out of the split.
set -f
IFS="$NL"
for line in $body; do
  case "$line" in
    ssh-*|ecdsa-sha2-*|sk-ssh-*|sk-ecdsa-*) gh_lines="${gh_lines}${line}${NL}" ;;
    *) die 4 "$url did not return an SSH key list (first bad line starts: '$(printf '%.20s' "$line")'). A proxy or login page may be in the way; the audit did not run." ;;
  esac
done
unset IFS
set +f

if [ -z "$gh_lines" ]; then
  die 5 "'$user' has no SSH keys on GitHub, so there is nothing to compare. If you push over SSH with this account, check that this is the right username."
fi

# ---------- 2. Read the local side ----------
local_rows=""   # fingerprint<TAB>TYPE<TAB>bits<TAB>file
local_count=0
local_warn=0
pub_files=0
if [ -d "$SSH_DIR" ]; then
  for f in "$SSH_DIR"/*.pub; do
    [ -e "$f" ] || continue
    pub_files=$((pub_files + 1))
    name=$(basename "$f")
    got_one=0
    while IFS= read -r kline || [ -n "$kline" ]; do
      kline=$(printf '%s' "$kline" | tr -d '\r')
      case "$kline" in ""|"#"*) continue ;; esac
      if row=$(fingerprint_line "$kline"); then
        local_rows="${local_rows}${row}${TAB}${name}${NL}"
        local_count=$((local_count + 1))
        got_one=1
      fi
    done < "$f"
    if [ "$got_one" -eq 0 ]; then
      echo "$PROG: warning: could not read a public key from $f; skipped" >&2
      local_warn=$((local_warn + 1))
    fi
  done
fi
if [ "$pub_files" -eq 0 ]; then
  echo "$PROG: warning: no *.pub files in $SSH_DIR, so every GitHub key will show as not found here" >&2
fi

# ---------- 3. Compare and report ----------
gh_count=0
unmatched=0
old=0
unread=0
gh_fps=""
report=""
set -f
IFS="$NL"
for line in $gh_lines; do
  unset IFS
  gh_count=$((gh_count + 1))
  ktype=$(printf '%s\n' "$line" | awk '{print $1}')
  if ! row=$(fingerprint_line "$line"); then
    unread=$((unread + 1))
    report="${report}  key $gh_count ($ktype): COULD NOT READ. Check it in GitHub Settings, then SSH and GPG keys.${NL}"
    continue
  fi
  fp=$(printf '%s' "$row" | cut -f1)
  type=$(printf '%s' "$row" | cut -f2)
  bits=$(printf '%s' "$row" | cut -f3)
  gh_fps="${gh_fps}${fp}${NL}"
  where=$(printf '%s' "$local_rows" | awk -F'\t' -v fp="$fp" '$1 == fp {print $4; exit}')
  if [ -n "$where" ]; then
    status="local: $where"
  else
    status="NOT IN LOCAL .pub FILES"
    unmatched=$((unmatched + 1))
  fi
  reason=$(old_reason "$type" "$bits")
  if [ -n "$reason" ]; then
    status="$status   OLD: $reason"
    old=$((old + 1))
  fi
  report="${report}  ${fp}  ${type}${bits:+ $bits}   ${status}${NL}"
done
unset IFS
set +f

local_only=""
local_old=""
set -f
IFS="$NL"
for lrow in $local_rows; do
  unset IFS
  # cut keeps empty fields (a DSA row has no bit count); read with IFS=tab would merge them.
  lfp=$(printf '%s' "$lrow" | cut -f1)
  ltype=$(printf '%s' "$lrow" | cut -f2)
  lbits=$(printf '%s' "$lrow" | cut -f3)
  lname=$(printf '%s' "$lrow" | cut -f4-)
  if ! printf '%s' "$gh_fps" | grep -qxF "$lfp"; then
    local_only="${local_only}  ${lfp}  ${ltype}${lbits:+ $lbits}   ${lname}${NL}"
  fi
  reason=$(old_reason "$ltype" "$lbits")
  if [ -n "$reason" ]; then
    local_old="${local_old}  ${lfp}  ${lname}   OLD: ${reason}${NL}"
    old=$((old + 1))
  fi
done
unset IFS
set +f

echo "ssh-key-audit: github.com/${user}.keys compared with ${SSH_DIR}/*.pub (read-only, nothing changed)"
echo "GitHub keys: $gh_count   Local public keys: $local_count"
echo
echo "On GitHub:"
printf '%s' "$report"
if [ -n "$local_only" ]; then
  echo
  echo "Only in local .pub files (not on this GitHub account; fine if you use them elsewhere):"
  printf '%s' "$local_only"
fi
if [ -n "$local_old" ]; then
  echo
  echo "Old-type local keys:"
  printf '%s' "$local_old"
fi
echo

unread=$((unread + local_warn))
findings=$((unmatched + old + unread))
if [ "$findings" -eq 0 ]; then
  echo "Result: clean. Every GitHub key has a .pub file here and none is an old type."
  echo "A matching .pub file does not prove the private key is still on this machine."
  exit 0
fi
echo "Result: $unmatched GitHub key(s) with no local .pub file, $old old-type key(s), $unread unreadable."
echo "Next: find each flagged SHA256 fingerprint in GitHub Settings, then SSH and GPG keys (same format)."
echo "Delete keys you can't explain there, then remove them from servers' authorized_keys too."
exit 1
