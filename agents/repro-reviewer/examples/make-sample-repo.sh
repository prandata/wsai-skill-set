#!/usr/bin/env bash
# Builds "tinyshop", a tiny Python repo with three branches, one planted problem each:
#   real-bug     split_bill rewrite that loses cents (the tests still pass)
#   false-alarm  parse_duration gains a "d" unit; a bot comment claims a bug that isn't there
#   cannot-run   receipt links now last 30 days; S3 only honours presigned URLs up to 7 days
# Fixed author, committer and dates, so the commit SHAs are the same on every machine.
#   bash make-sample-repo.sh /tmp/tinyshop
set -euo pipefail

dir=${1:?usage: make-sample-repo.sh <new-directory>}
if [ -e "$dir" ] && [ -n "$(ls -A "$dir" 2>/dev/null)" ]; then
  echo "refusing: $dir exists and is not empty" >&2
  exit 2
fi
mkdir -p "$dir"
cd "$dir"

export GIT_AUTHOR_NAME="Sample Author" GIT_AUTHOR_EMAIL="author@example.com"
export GIT_COMMITTER_NAME="Sample Author" GIT_COMMITTER_EMAIL="author@example.com"
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
git init -q -b main .
git config commit.gpgsign false

commit() {  # commit <date> <message>
  export GIT_AUTHOR_DATE="$1 +0000" GIT_COMMITTER_DATE="$1 +0000"
  git add -A
  git commit -q -m "$2"
}

mkdir -p tinyshop tests
: > tinyshop/__init__.py

cat > tinyshop/pricing.py <<'EOF'
def split_bill(total_cents, people):
    """Split a bill into whole-cent shares that add up to total_cents.

    The first (total_cents % people) shares get one extra cent.
    """
    if people < 1:
        raise ValueError("people must be at least 1")
    base, rem = divmod(total_cents, people)
    return [base + 1 if i < rem else base for i in range(people)]
EOF

cat > tinyshop/durations.py <<'EOF'
import re

_PART = re.compile(r"(\d+)([hms])")
_UNIT = {"h": 3600, "m": 60, "s": 1}


def parse_duration(text):
    """Parse '1h30m' or '90s' into seconds.

    Units may repeat and are summed: '1m1m' is 120. Anything else raises ValueError.
    """
    pos = total = 0
    for m in _PART.finditer(text):
        if m.start() != pos:
            break
        total += int(m.group(1)) * _UNIT[m.group(2)]
        pos = m.end()
    if pos == 0 or pos != len(text):
        raise ValueError(f"bad duration: {text!r}")
    return total
EOF

cat > tinyshop/links.py <<'EOF'
def download_link(s3, bucket, key, days=1):
    """Presigned GET URL for a receipt PDF, made with a boto3 S3 client."""
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=days * 86400,
    )
EOF

cat > tests/__init__.py <<'EOF'
EOF

cat > tests/test_pricing.py <<'EOF'
import unittest
from tinyshop.pricing import split_bill


class SplitBill(unittest.TestCase):
    def test_even(self):
        self.assertEqual(split_bill(900, 3), [300, 300, 300])

    def test_no_people(self):
        with self.assertRaises(ValueError):
            split_bill(900, 0)


if __name__ == "__main__":
    unittest.main()
EOF

cat > tests/test_durations.py <<'EOF'
import unittest
from tinyshop.durations import parse_duration


class ParseDuration(unittest.TestCase):
    def test_mixed(self):
        self.assertEqual(parse_duration("1h30m"), 5400)

    def test_bad(self):
        for text in ["", "h", "10", "1x", "1h 30m"]:
            with self.assertRaises(ValueError):
                parse_duration(text)


if __name__ == "__main__":
    unittest.main()
EOF

cat > tests/test_links.py <<'EOF'
import unittest
from tinyshop.links import download_link


class FakeS3:
    def generate_presigned_url(self, op, Params, ExpiresIn):
        self.call = (op, Params, ExpiresIn)
        return "https://example.invalid/signed"


class DownloadLink(unittest.TestCase):
    def test_default_expiry(self):
        s3 = FakeS3()
        download_link(s3, "receipts", "r1.pdf")
        self.assertEqual(s3.call[2], 86400)


if __name__ == "__main__":
    unittest.main()
EOF

cat > README.md <<'EOF'
# tinyshop

Sample repo for the repro-reviewer examples. Run the tests with `python3 -m unittest`.
EOF

commit "2026-01-05T09:00:00" "tinyshop: split_bill, parse_duration, download_link"

# real-bug: a "simpler" split_bill. 900/3 still passes; 1000/3 gives 999 cents.
git checkout -q -b real-bug
cat > tinyshop/pricing.py <<'EOF'
def split_bill(total_cents, people):
    """Split a bill into whole-cent shares that add up to total_cents."""
    if people < 1:
        raise ValueError("people must be at least 1")
    share = round(total_cents / people)
    return [share] * people
EOF
commit "2026-01-06T09:00:00" "pricing: simpler split_bill

One expression instead of divmod. Shares still add up to the total."

# false-alarm: adds days. The regex already takes several digits.
git checkout -q main
git checkout -q -b false-alarm
python3 - <<'EOF'
p = "tinyshop/durations.py"
s = open(p).read()
s = s.replace('r"(\\d+)([hms])"', 'r"(\\d+)([dhms])"')
s = s.replace('_UNIT = {"h": 3600', '_UNIT = {"d": 86400, "h": 3600')
s = s.replace("Parse '1h30m' or '90s'", "Parse '2d', '1h30m' or '90s'")
open(p, "w").write(s)
p = "tests/test_durations.py"
s = open(p).read()
s = s.replace("    def test_bad(self):", "    def test_days(self):\n        self.assertEqual(parse_duration(\"2d\"), 172800)\n\n    def test_bad(self):")
open(p, "w").write(s)
EOF
commit "2026-01-07T09:00:00" "durations: accept days (2d)"

# cannot-run: 30-day links. Only S3 itself can show that it refuses them.
git checkout -q main
git checkout -q -b cannot-run
python3 - <<'EOF'
p = "tinyshop/links.py"
s = open(p).read().replace("days=1", "days=30")
open(p, "w").write(s)
p = "tests/test_links.py"
s = open(p).read().replace("86400)", "30 * 86400)")
open(p, "w").write(s)
EOF
commit "2026-01-08T09:00:00" "links: receipt links last 30 days

Customers asked for links that work for a month."

git checkout -q main
git log --all --format='%h %d %s' --date-order
