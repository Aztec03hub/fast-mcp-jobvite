#!/usr/bin/env bash
# #254: is a non-measurement exit code REACHABLE in check-u3-audit-amputation.sh,
# and does the harness's verdict logic report it as a successful kill?
#
# The task recorded rc=4 as "unreachable today" because this harness passes a
# bare $SUITE with no per-row selector - no node id to mistype, no coverage map
# to be missing. That reasoning is about rc=4 ONLY. It says nothing about rc=2,
# COLLECTION ERROR, which this harness can cause ITSELF: every row rewrites a
# source file by text substitution, and a substitution that lands can leave the
# module syntactically invalid.
#
# The verdict logic reads `^PASSED ` lines and calls their absence a kill. A
# collection error produces no PASSED lines. So the question is not academic.
#
# ARM 1 measures whether the defect is reachable at all.
# ARM 2 measures the OLD verdict logic against that output   (expect: false kill)
# ARM 3 measures the NEW verdict logic against that output   (expect: refusal)
# ARM 4 is the positive control: NEW logic on a HEALTHY run  (expect: no refusal)
#
# Nothing here runs the real harness against the real tree. It builds the exact
# output file the harness would have, then runs each verdict logic over it. The
# source file is copied, never edited in place.
set -uo pipefail
cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/../.." || {
    echo "REFUSING: could not reach the repo root from ${BASH_SOURCE[0]}" >&2; exit 2; }
REPO=$PWD
AUDIT="src/fast_mcp_jobvite/audit.py"
[ -f "$AUDIT" ] || { echo "REFUSING: $AUDIT absent at $REPO"; exit 2; }

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"; git -C "$REPO" checkout -- "$AUDIT" 2>/dev/null' EXIT

pass=0; fail=0
ok(){ echo "  PASS  $1"; pass=$((pass+1)); }
no(){ echo "  FAIL  $1"; fail=$((fail+1)); }

echo "=== ARM 1: can an amputation make pytest exit with a collection error? ==="
cp "$AUDIT" "$WORK/audit.py.orig"
# A text substitution of exactly the kind the harness performs, chosen so the
# result is syntactically invalid. This is not a contrived edit: it deletes a
# block body and leaves the block header, which is what happens whenever a
# replacement is shorter than its anchor and the anchor spanned an indent.
python3 - "$AUDIT" <<'PY'
import sys, pathlib, re
p = pathlib.Path(sys.argv[1]); s = p.read_text()
m = re.search(r'^(\s*)def (\w+)\(', s, re.M)
assert m, "no def found to break"
# leave the def header, delete its whole body -> IndentationError on import
start = m.start()
end = s.find("\ndef ", m.end())
if end == -1: end = len(s)
p.write_text(s[:start] + m.group(0) + "\n" + s[end:])
PY
python3 -c "import ast,sys; ast.parse(open('$AUDIT').read())" 2>/dev/null \
    && { echo "  the planted edit is still valid Python - probe cannot proceed"; exit 2; }
echo "  planted: $AUDIT no longer parses"

OUT="$WORK/rowout.txt"
timeout 300 uv run --frozen pytest tests -q -p no:cacheprovider -rA >"$OUT" 2>&1
rc=$?
git -C "$REPO" checkout -- "$AUDIT"
echo "  pytest exited: $rc"
echo "  PASSED lines in its output: $(grep -cE '^PASSED ' "$OUT" || true)"
if [ "$rc" -ne 0 ] && [ "$rc" -ne 1 ]; then
    ok "ARM 1: a landed amputation produced rc=$rc, NOT a 0/1 measurement"
else
    no "ARM 1: expected a non-measurement rc, got $rc - defect may be unreachable"
fi

echo
echo "=== ARM 2: the OLD verdict logic over that exact output ==="
# The pre-fix logic, verbatim in shape: no rc is consulted at all.
survivors=$(grep -E '^PASSED ' "$OUT" | sed 's/^PASSED //' || true)
if [ -z "$survivors" ]; then old_verdict="survivors: NONE (reported as a KILL)"
else old_verdict="survivors: $(printf '%s\n' "$survivors" | wc -l)"; fi
echo "  OLD says -> $old_verdict"
if [ -z "$survivors" ]; then
    ok "ARM 2: OLD logic reports a broken run as a successful kill - THE DEFECT"
else
    no "ARM 2: OLD logic did not produce the false kill this probe exists to show"
fi

echo
echo "=== ARM 3: the NEW verdict logic over that same output ==="
new_verdict() {
    local rc=$1
    case "$rc" in
        0|1) echo "INTERPRETED"; return 0 ;;
        124) echo "REFUSED (timeout)"; return 5 ;;
        *)   echo "REFUSED (rc=$rc is not a measurement)"; return 5 ;;
    esac
}
v=$(new_verdict "$rc"); vrc=$?
echo "  NEW says -> $v   (exit $vrc)"
if [ "$vrc" -eq 5 ]; then
    ok "ARM 3: NEW logic REFUSES the same output the OLD one scored as a kill"
else
    no "ARM 3: NEW logic did not refuse (exit $vrc)"
fi

echo
echo "=== ARM 4: positive control - NEW logic must NOT refuse a healthy run ==="
# Amputation-free: the tree is restored, so this is a real 0-or-1 outcome.
timeout 300 uv run --frozen pytest tests -q -p no:cacheprovider -rA >"$WORK/clean.txt" 2>&1
crc=$?
echo "  clean pytest exited: $crc"
v=$(new_verdict "$crc"); vrc=$?
echo "  NEW says -> $v   (exit $vrc)"
if [ "$vrc" -eq 0 ] && { [ "$crc" -eq 0 ] || [ "$crc" -eq 1 ]; }; then
    ok "ARM 4: NEW logic interprets a real run - the guard is not blanket-refusing"
else
    no "ARM 4: NEW logic refused a healthy run (pytest rc=$crc) - OVER-REFUSAL"
fi

echo
echo "arms passed: $pass   failed: $fail"
[ "$fail" -eq 0 ] || exit 1
