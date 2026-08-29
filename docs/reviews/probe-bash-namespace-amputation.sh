#!/usr/bin/env bash
# Positive control for the BASH-* namespace: a row in the NEW id namespace must
# be VERIFIED, not silently skipped. The failure this guards is the exact one
# check-obligations.py's own ROW comment warns about - "a row that looks tracked
# and is never verified" - and it is invisible in a green run.
#
# Amputation: delete BASH-1's subject from the artifact it cites. The checker
# MUST go red AND MUST name BASH-1.
set -uo pipefail
cd /tmp/bash-work || exit 9

ADR=docs/adr/0023-harnesses-drop-e-from-strict-mode.md
BACKUP=/tmp/sc/adr.backup
cp "$ADR" "$BACKUP" || { echo "COULD NOT BACK UP"; exit 9; }

# Prove the anchor is present and unique BEFORE mutating.
n=$(grep -cF -- 'Keep `set -uo pipefail` in' "$ADR")
[ "$n" -eq 1 ] || { echo "ANCHOR NOT UNIQUE ($n hits) - refusing to mutate"; exit 9; }

python3 - <<'PY'
import pathlib
p = pathlib.Path('/tmp/bash-work/docs/adr/0023-harnesses-drop-e-from-strict-mode.md')
t = p.read_text(encoding='utf-8')
old = 'Keep `set -uo pipefail` in'
assert t.count(old) == 1
p.write_text(t.replace(old, 'AMPUTATED subject line for'), encoding='utf-8')
PY

# Prove the mutation LANDED, against the backup, not against a grep that can
# match nothing and succeed.
if cmp -s "$ADR" "$BACKUP"; then
  echo "MUTATION DID NOT LAND - file is byte-identical to the backup"
  cp "$BACKUP" "$ADR"
  exit 9
fi
echo "mutation landed"

rc=0
out=$(python3 docs/reviews/check-obligations.py 2>&1); rc=$?
cp "$BACKUP" "$ADR"
cmp -s "$ADR" "$BACKUP" || { echo "RESTORE FAILED"; exit 9; }
echo "restored"
echo
echo "checker exit under amputation = $rc"
echo "$out" | sed 's/^/    /'
echo
if [ "$rc" -ne 0 ] && printf '%s' "$out" | grep -q 'BASH-1'; then
  echo "CONTROL FIRED: the BASH-* namespace is parsed and verified."
else
  echo "CONTROL DID NOT FIRE: a BASH-* row is being SILENTLY SKIPPED."
  exit 1
fi
