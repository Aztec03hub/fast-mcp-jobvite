#!/usr/bin/env bash
# Task #240: does the coverage-derived covering set actually HOLD UP a real row?
#
# The map says http_hardening.py is covered by 156 of 888 tests. That is a
# claim about coverage, not about the harness: a mutation-selection lever is
# only worth anything if running JUST those 156 still turns the row RED. So
# this replays U9 row A1 - the pole harness's first amputation, which disables
# every bearer-token check on the HTTP transport - two ways:
#
#   ARM 1 (NEGATIVE CONTROL, intact tree): the 156 selected tests must PASS.
#          Without this, a red in ARM 2 could be the selection being broken
#          rather than the amputation being caught.
#   ARM 2 (the real question, amputated tree): the same 156 must go RED.
#          A green here means the covering set does NOT hold the row and
#          per-mutation selection would silently weaken the gate.
#
# Both arms are timed, so the report can put "row cost under selection" beside
# "row cost today" without modelling either.
#
# THE TREE. The amputation is applied to a real tracked file, so this follows
# the harness discipline that exists because a killed run left exactly this
# mutation live once: a pristine copy is taken first, an EXIT trap restores it
# on ANY exit including a signal-driven one, `cmp` proves the restore, and
# `git status --porcelain` is printed at the end for the reader to check.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO" || exit 3
export PYTHONDONTWRITEBYTECODE=1

# REQUIRED by scripts/check-pytest-bounded.sh: an unbounded pytest that hangs
# produces no result lines, so ARM2 would read as "nothing failed" - the exact
# false green this probe exists to rule out.
ARM_TIMEOUT=900

DATA="${DATA:-/tmp/prof240/.coverage-ctx}"
SUBJECT="src/fast_mcp_jobvite/http_hardening.py"
IDS=$(mktemp)
PRISTINE=$(mktemp)
cp "$SUBJECT" "$PRISTINE" || exit 3
trap 'cp "$PRISTINE" "$SUBJECT"; rm -f "$IDS" "$PRISTINE"' EXIT

# ---- the covering set, run-phase only -------------------------------------
DATA="$DATA" SUBJECT="$SUBJECT" python3 - >"$IDS" <<'PY'
import os, sqlite3
con = sqlite3.connect(f"file:{os.environ['DATA']}?mode=ro", uri=True)
fid = con.execute(
    "SELECT id FROM file WHERE path LIKE ?", ("%/" + os.environ["SUBJECT"],)
).fetchone()
if fid is None:
    raise SystemExit(f"MUTATION TARGET NOT FOUND in coverage data: {os.environ['SUBJECT']}")
ids = {
    ctx.split("|", 1)[0]
    for (ctx,) in con.execute(
        "SELECT DISTINCT c.context FROM arc a JOIN context c ON c.id = a.context_id "
        "WHERE a.file_id = ? AND c.context LIKE '%|run'",
        (fid[0],),
    )
}
print("\n".join(sorted(ids)))
PY
n=$(wc -l <"$IDS")
echo "SELECTED $n node ids covering $SUBJECT (run phase)"
if [ "$n" -lt 2 ]; then
  echo "::error::BROKEN CONTROL - $n selected ids. A near-empty selection would make"
  echo "         both arms meaningless. Check the coverage data at $DATA."
  exit 2
fi

t0=$(date +%s)
# shellcheck disable=SC2046
timeout "$ARM_TIMEOUT" uv run --frozen pytest -q -p no:cacheprovider $(tr '\n' ' ' <"$IDS") >/tmp/prof240/arm1.txt 2>&1
rc1=$?
t1=$(date +%s)
echo "ARM1 intact  rc=$rc1  seconds=$((t1 - t0))  $(tail -1 /tmp/prof240/arm1.txt)"
if [ "$rc1" -ne 0 ]; then
  echo "::error::BROKEN CONTROL - the selected tests are red on the INTACT tree."
  exit 2
fi

# ---- U9 row A1's exact anchor ---------------------------------------------
OLD='    if settings.mcp_transport != "http":
        return None
    if settings.http_tokens is None:'
NEW='    if True:
        return None
    if settings.http_tokens is None:'
if ! OLD="$OLD" NEW="$NEW" FILE="$SUBJECT" python3 - <<'PY'
import os, pathlib, sys
p = pathlib.Path(os.environ["FILE"])
s = p.read_text()
old, new = os.environ["OLD"], os.environ["NEW"]
n = s.count(old)
if n != 1:
    print(f"ANCHOR NOT UNIQUE ({n} hits)", file=sys.stderr)
    sys.exit(1)
p.write_text(s.replace(old, new))
PY
then
  echo "COULD NOT APPLY - the anchor moved. Fix the probe against U9 row A1."
  exit 2
fi
cmp -s "$SUBJECT" "$PRISTINE" && { echo "AMPUTATION DID NOT LAND"; exit 2; }
echo "AMPUTATION APPLIED (U9 row A1)"

t2=$(date +%s)
# shellcheck disable=SC2046
timeout "$ARM_TIMEOUT" uv run --frozen pytest -q -p no:cacheprovider -rf $(tr '\n' ' ' <"$IDS") >/tmp/prof240/arm2.txt 2>&1
rc2=$?
t3=$(date +%s)
echo "ARM2 amputated  rc=$rc2  seconds=$((t3 - t2))  $(tail -1 /tmp/prof240/arm2.txt)"
grep -E '^FAILED ' /tmp/prof240/arm2.txt | head -5

cp "$PRISTINE" "$SUBJECT"
if ! cmp -s "$SUBJECT" "$PRISTINE"; then
  echo "::error::RESTORE FAILED. DO NOT COMMIT FROM THIS TREE."
  exit 3
fi
echo "RESTORED (cmp clean)"
git -C "$REPO" status --porcelain

if [ "$rc2" -eq 0 ]; then
  echo "VERDICT: the covering set does NOT hold U9 row A1. Selection would weaken the gate."
  exit 1
fi
echo "VERDICT: the covering set HOLDS U9 row A1 - selection preserves the verdict."
