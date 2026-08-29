#!/usr/bin/env bash
# Positive control for the BASH-* namespace in docs/OBLIGATIONS.md.
#
# WHAT IT GUARDS. check-obligations.py's ROW regex decides which table rows are
# obligations at all. A row the regex does not match is not reported as broken -
# it is not reported. Its own comment says so: "a row that looks tracked and is
# never verified". Adding the BASH-* namespace could therefore have produced two
# rows that verify nothing, and the run would have stayed green.
#
# METHOD. Delete BASH-1's subject from the artifact it cites. The checker MUST
# go red AND MUST name BASH-1.
#
# `-e` deliberately omitted, under ADR-0023: this probe reads the exit code of a
# checker that is EXPECTED to fail under the amputation.
set -uo pipefail
cd /tmp/bash-work 2>/dev/null || cd "$(git rev-parse --show-toplevel)" || exit 9

# No MAP variable here: one was declared and read by nothing. The artifact
# this probe edits is read out of the ROW below, which is the whole point of
# the paragraph under it.
BACKUP=$(mktemp)

# THE SUBJECT AND THE ARTIFACT ARE READ FROM THE ROW, NEVER HARD-CODED HERE.
#
# They were hard-coded in the first version of this file, and it went silently
# vacuous within the hour: BASH-1's subject was changed in OBLIGATIONS.md and
# this probe kept amputating the OLD literal, which still existed elsewhere in
# the ADR. So the mutation landed, the checker stayed green, and the probe
# reported "DID NOT FIRE" for a reason that had nothing to do with the property
# under test. A value that is measured once must appear once.
read -r ARTIFACT SUBJECT <<<"$(
  python3 - <<'PY'
import pathlib, re, sys
row = None
for line in pathlib.Path('docs/OBLIGATIONS.md').read_text(encoding='utf-8').splitlines():
    if re.match(r'^\|\s*BASH-1\s*\|', line):
        row = [c.strip() for c in line.split('|')[1:-1]]
        break
if row is None:
    sys.exit('no BASH-1 row found')
strip = lambda c: re.sub(r'^[`*]+|[`*]+$', '', c.strip()).strip()
print(strip(row[2]), strip(row[3]))
PY
)"
[ -n "${ARTIFACT:-}" ] && [ -n "${SUBJECT:-}" ] || { echo "could not read the BASH-1 row"; exit 9; }
echo "artifact: $ARTIFACT"
echo "subject:  $SUBJECT"

cp "$ARTIFACT" "$BACKUP" || { echo "COULD NOT BACK UP"; exit 9; }

# The anchor must be present and UNIQUE before we mutate it. A sed matching
# nothing succeeds silently.
n=$(grep -cF -- "$SUBJECT" "$ARTIFACT")
[ "$n" -eq 1 ] || { echo "ANCHOR NOT UNIQUE IN THE ARTIFACT ($n hits) - refusing"; exit 9; }

SUBJECT="$SUBJECT" ARTIFACT="$ARTIFACT" python3 - <<'PY'
import os, pathlib
p = pathlib.Path(os.environ['ARTIFACT'])
t = p.read_text(encoding='utf-8')
old = os.environ['SUBJECT']
assert t.count(old) == 1, f'expected exactly one occurrence, found {t.count(old)}'
p.write_text(t.replace(old, 'AMPUTATED subject'), encoding='utf-8')
PY

# Prove the mutation LANDED, by comparison against the backup - not by a grep
# that can match nothing and exit clean.
if cmp -s "$ARTIFACT" "$BACKUP"; then
  echo "MUTATION DID NOT LAND - byte-identical to the backup"
  cp "$BACKUP" "$ARTIFACT"
  exit 9
fi
echo "mutation landed"

rc=0
out=$(python3 docs/reviews/check-obligations.py 2>&1); rc=$?

cp "$BACKUP" "$ARTIFACT" || { echo "RESTORE FAILED"; exit 9; }
cmp -s "$ARTIFACT" "$BACKUP" || { echo "RESTORE FAILED"; exit 9; }
rm -f "$BACKUP"
echo "restored"
echo
echo "checker exit under amputation = $rc"
echo "$out" | sed 's/^/    /'
echo

if [ "$rc" -ne 0 ] && printf '%s' "$out" | grep -q 'BASH-1'; then
  echo "CONTROL FIRED: the BASH-* namespace is parsed and verified."
  exit 0
fi
echo "CONTROL DID NOT FIRE: a BASH-* row is being SILENTLY SKIPPED."
exit 1
