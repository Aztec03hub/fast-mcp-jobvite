#!/usr/bin/env bash
# CONTROLS and AMPUTATIONS for scripts/check-mirror-liveness.py.
#
# The subject exists to notice that a workflow has stopped running. Its own
# failure mode is therefore the one it hunts: it prints a green line, and it
# prints it because a branch stopped being reached rather than because the
# mirror is alive. So the positive rows below assert each DISTINCT exit code,
# and the amputation rows DELETE the branch that produces one and require the
# same fixture to stop producing it.
#
# EVERY ROW FEEDS INJECTED JSON. `--workflow-json` and `--runs-json` exist for
# exactly this: no row reaches the network, so no row can pass because a live
# API happened to agree with it, and none can fail because GitHub was slow.
# `--now` is pinned so the ages below are literals rather than a clock.
#
# THE FIXTURES AND THE CHECKER COPY BOTH LIVE IN A TEMP DIR. Nothing here
# writes to the working tree; `git status --porcelain` after a run is the check
# that says so, and two commits on this project captured an amputated source
# because a harness was killed mid-row.
set -uo pipefail

# shellcheck source=lib/harness-result.sh
. "$(dirname "${BASH_SOURCE[0]}")/lib/harness-result.sh"

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHECKER_REL="scripts/check-mirror-liveness.py"
WORK="$(mktemp -d)"
trap 'harness_result_emit; rm -rf "$WORK"' EXIT

export PYTHONDONTWRITEBYTECODE=1

# The instant every age below is measured against. Pinned, so "47.9h" is a
# property of the fixture and not of when the harness happened to run.
NOW="2026-09-02T00:00:00Z"

FIRED=0
TOTAL=0

mkdir -p "$WORK/fx"
cat >"$WORK/fx/active.json" <<'JSON'
{"id": 344103800, "path": ".github/workflows/mirror.yml", "state": "active"}
JSON
cat >"$WORK/fx/disabled.json" <<'JSON'
{"id": 344103800, "path": ".github/workflows/mirror.yml", "state": "disabled_inactivity"}
JSON
cat >"$WORK/fx/no-state.json" <<'JSON'
{"id": 344103800, "path": ".github/workflows/mirror.yml"}
JSON

# 2h before NOW.
cat >"$WORK/fx/fresh.json" <<'JSON'
{"total_count": 1, "workflow_runs": [{"id": 1, "created_at": "2026-09-01T22:00:00Z"}]}
JSON
# 72h before NOW - three missed daily schedules.
cat >"$WORK/fx/stale.json" <<'JSON'
{"total_count": 1, "workflow_runs": [{"id": 1, "created_at": "2026-08-30T00:00:00Z"}]}
JSON
# 47.9h and 48.1h: the two sides of the default window, six minutes apart.
cat >"$WORK/fx/under.json" <<'JSON'
{"total_count": 1, "workflow_runs": [{"id": 1, "created_at": "2026-08-31T00:06:00Z"}]}
JSON
cat >"$WORK/fx/over.json" <<'JSON'
{"total_count": 1, "workflow_runs": [{"id": 1, "created_at": "2026-08-30T23:54:00Z"}]}
JSON
cat >"$WORK/fx/empty.json" <<'JSON'
{"total_count": 0, "workflow_runs": []}
JSON
# Newest LAST. The API documents no ordering guarantee, and a checker that
# reads the head of the list would call this stale.
cat >"$WORK/fx/unordered.json" <<'JSON'
{"total_count": 2, "workflow_runs": [{"id": 1, "created_at": "2026-08-30T00:00:00Z"}, {"id": 2, "created_at": "2026-09-01T22:00:00Z"}]}
JSON
cat >"$WORK/fx/no-runs-key.json" <<'JSON'
{"total_count": 1}
JSON
cat >"$WORK/fx/bad-stamp.json" <<'JSON'
{"total_count": 1, "workflow_runs": [{"id": 1, "created_at": "the day before yesterday"}]}
JSON

# row <name> <expected-exit> <checker> <workflow-json> <runs-json> [must-contain]
#
# The optional sixth argument exists because EXIT CODES COLLIDE. AMP-EMPTY
# below expects a crash, and an uncaught exception exits 1 - the same 1 as
# STALE. A row that read only the code would score an amputation as fired when
# the amputated tool had merely reported the wrong thing successfully.
row() {
  local name="$1" want="$2" checker="$3" wf="$4" runs="$5" needle="${6-}"
  TOTAL=$((TOTAL + 1))
  local out rc
  out="$(python3 "$checker" --now "$NOW" \
      --workflow-json "$wf" --runs-json "$runs" 2>&1)"
  rc=$?
  if [ "$rc" -ne "$want" ]; then
    echo "::error::  FAIL  $name: exit $rc (want $want)"
    echo "$out" | sed 's/^/          /'
    return
  fi
  # A HERE-STRING, NOT A PIPE. Under `pipefail` a `printf ... | grep -q`
  # returns 141 when grep matches early and exits before printf finishes, so
  # a string that IS present reports as ABSENT. There is a checker for that
  # shape and it caught this line the first time it ran over this file.
  if [ -n "$needle" ] && ! grep -qF -- "$needle" <<<"$out"; then
    echo "::error::  FAIL  $name: exit $rc as wanted, but the output does not contain"
    echo "::error::        '$needle' - the right code for the wrong reason."
    echo "$out" | sed 's/^/          /'
    return
  fi
  FIRED=$((FIRED + 1))
  echo "  PASS  $name: exit $rc (want $want)"
}

CHECKER="$REPO/$CHECKER_REL"

echo "POSITIVE ROWS - each distinct exit code, from the real checker:"
row "FRESH     a run 2h old is alive"              0 "$CHECKER" "$WORK/fx/active.json"   "$WORK/fx/fresh.json"
row "STALE     a run 72h old is not"               1 "$CHECKER" "$WORK/fx/active.json"   "$WORK/fx/stale.json"
row "UNDER     47.9h is inside the 48h window"     0 "$CHECKER" "$WORK/fx/active.json"   "$WORK/fx/under.json"
row "OVER      48.1h is outside it"                1 "$CHECKER" "$WORK/fx/active.json"   "$WORK/fx/over.json"
row "NEVER     zero runs is its own state"         2 "$CHECKER" "$WORK/fx/active.json"   "$WORK/fx/empty.json"
row "DISABLED  disabled_inactivity, whatever the age" 3 "$CHECKER" "$WORK/fx/disabled.json" "$WORK/fx/fresh.json"
row "UNORDERED newest last still reads as fresh"   0 "$CHECKER" "$WORK/fx/active.json"   "$WORK/fx/unordered.json"

echo "UNMEASURABLE ROWS - an instrument that cannot see says so, and fails:"
row "NO-STATE  workflow payload without state"     4 "$CHECKER" "$WORK/fx/no-state.json" "$WORK/fx/fresh.json"
row "NO-RUNS   runs payload without workflow_runs" 4 "$CHECKER" "$WORK/fx/active.json"   "$WORK/fx/no-runs-key.json"
row "BAD-STAMP an unparseable created_at"          4 "$CHECKER" "$WORK/fx/active.json"   "$WORK/fx/bad-stamp.json"
row "MISSING   a fixture path that does not exist" 4 "$CHECKER" "$WORK/fx/active.json"   "$WORK/fx/nope.json"

# ---------------------------------------------------------------------------
# THE TRANSPORT, which nothing here touched until R18-H2 said so.
#
# Every row above passes BOTH --workflow-json and --runs-json, so `_load` takes
# its file branch and `_gh` IS NEVER CALLED. R18 proved it by planting a
# `raise SystemExit` as _gh's first statement: the tripwire fired ZERO times
# and this harness still reported 14/14 status=ok. Three of the five things
# that can raise UnmeasurableError live in _gh, and the live CI step exercises
# only the happy path - so the file's stated blind spot (the URL shape) was
# real but NARROWER than the truth. The whole transport was untested.
#
# These two rows go through `_gh` for real, without a network: one with PATH
# emptied so `shutil.which` finds no `gh`, one with a stub `gh` on PATH that
# exits non-zero. Both must reach COULD NOT MEASURE, which is the branch a
# fixture can never produce.
# ---------------------------------------------------------------------------
echo "TRANSPORT ROWS - these actually enter _gh:"

# The interpreter is resolved to an ABSOLUTE path FIRST, because emptying PATH
# also removes `python3` - the first version of this row exited 127 with
# "python3: No such file or directory" and was measuring the shell, not the
# checker. PATH then points at an empty directory: `shutil.which("gh")` must
# find nothing while the interpreter still runs.
PY_ABS="$(command -v python3)"
mkdir -p "$WORK/empty" "$WORK/bin"
cat >"$WORK/bin/gh" <<'STUB'
#!/usr/bin/env bash
# A stub that is NOT the network: it refuses the way an unauthenticated or
# rate-limited `gh` does, so the row measures the checker's handling of a
# failed call rather than GitHub's mood.
echo "gh: Bad credentials (HTTP 401)" >&2
exit 1
STUB
chmod +x "$WORK/bin/gh"

# transport <name> <PATH to run under> <expected-exit> <must-contain>
#
# A NAMED FUNCTION, not two inline blocks, and that is not tidiness.
# `docs/reviews/check-row-floor-exactness.py` counts a harness's rows by
# matching its ROW-INVOCATION line, so rows written inline are invisible to it:
# the first version of these two made the live count 16 while the static count
# stayed 14, and the exactness checker refused the floor. A row the floor
# checker cannot see is a row that can be deleted with CI green.
transport() {
  local name="$1" path="$2" want="$3" needle="$4"
  TOTAL=$((TOTAL + 1))
  local out rc
  out="$(PATH="$path" "$PY_ABS" "$CHECKER" --now "$NOW" --repo o/r 2>&1)"
  rc=$?
  if [ "$rc" -ne "$want" ]; then
    echo "::error::  FAIL  $name: exit $rc (want $want)"
    printf '%s\n' "$out" | sed 's/^/          /'
    return
  fi
  if ! grep -qF -- "$needle" <<<"$out"; then
    echo "::error::  FAIL  $name: exit $rc as wanted, but without '$needle'"
    printf '%s\n' "$out" | sed 's/^/          /'
    return
  fi
  FIRED=$((FIRED + 1))
  echo "  PASS  $name: exit $rc (want $want)"
}

# The interpreter is resolved to an ABSOLUTE path above, because emptying PATH
# also removes `python3` - the first version of the NO-GH row exited 127 with
# "python3: No such file or directory" and was measuring the shell, not the
# checker.
transport "NO-GH     no gh on PATH reaches _gh and says so" "$WORK/empty" 4 "not on PATH"
transport "GH-FAILS  a refusing gh is reported, not swallowed" "$WORK/bin:/usr/bin:/bin" 4 "exited 1"

echo "AMPUTATIONS - delete the rule, require the finding to disappear:"

amputate() {
  local name="$1" pattern="$2" replacement="$3" want="$4" wf="$5" runs="$6" needle="${7-}"
  local copy="$WORK/amp-$name.py"
  cp "$CHECKER" "$copy"
  # A COUNTED substitution. `sed -i` with no match exits 0, which would make a
  # stale pattern look like a successful amputation - the shape that produced
  # three vacuous controls here in one evening.
  #
  # THE TWO FAILURE PHRASES BELOW ARE THE GATE'S VOCABULARY, not decoration.
  # scripts/ci-harness-gate.sh derives what it greps for from this file's own
  # source, and REFUSES a harness that can print none of them - so a harness
  # whose anchors have gone stale must be able to SAY that in words the gate
  # knows. It refused this one on its first wiring, which is the mechanism
  # working.
  if ! python3 - "$copy" "$pattern" "$replacement" <<'PY'
import sys
path, pattern, replacement = sys.argv[1], sys.argv[2], sys.argv[3]
text = open(path).read()
hits = text.count(pattern)
if hits == 0:
    print(f"MUTATION TARGET NOT FOUND: {pattern!r}")
    sys.exit(1)
if hits > 1:
    print(f"ANCHOR NOT UNIQUE: {pattern!r} matched {hits} times, want 1")
    sys.exit(1)
open(path, "w").write(text.replace(pattern, replacement))
PY
  then
    TOTAL=$((TOTAL + 1))
    echo "::error::  FAIL  $name: the anchor did not match exactly once, so nothing was amputated."
    return
  fi
  row "$name" "$want" "$copy" "$wf" "$runs" "$needle"
}

# Delete the age comparison: the STALE fixture must now read as alive.
amputate "AMP-AGE   without the age test, 72h is 'fresh'" \
  "if age > max_age:" "if False:" 0 "$WORK/fx/active.json" "$WORK/fx/stale.json"

# Delete the state test: a disabled workflow must now fall through to its age.
amputate "AMP-STATE without the state test, disabled reads alive" \
  'if state != "active":' "if False:" 0 "$WORK/fx/disabled.json" "$WORK/fx/fresh.json"

# Delete the empty-population branch: zero runs must stop being its own answer.
# `newest is None` then reaches the subtraction and raises - a CRASH, not a
# green. That is the point: the branch is what turns an empty population into a
# statement, and without it the tool cannot speak about one at all.
#
# NOTE THE SIXTH ARGUMENT. An uncaught exception exits 1, which is also STALE's
# code, so this row asserts the TypeError by name. Without that the arm would
# score a fire if the amputated tool had merely misreported.
amputate "AMP-EMPTY without the zero-run branch, an empty page crashes" \
  "if newest is None:" "if False:" 1 "$WORK/fx/active.json" "$WORK/fx/empty.json" \
  "TypeError"

harness_result_tally fired "$FIRED" "$TOTAL"

# THE ROW FLOOR. `FIRED -ne TOTAL` is satisfied by 0 == 0, so a harness whose
# rows stopped being counted reports fully green. DERIVED: 11 positive and
# unmeasurable rows plus 3 amputations, counted from the calls above at the
# commit that adds them.
ROW_FLOOR=16
harness_result_ran "$TOTAL" "$ROW_FLOOR"
if [ "$TOTAL" -lt "$ROW_FLOOR" ]; then
  echo "::error::$TOTAL/$ROW_FLOOR ROWS - THE HARNESS LOST ROWS."
  echo "         A harness with fewer rows than its floor is green for the wrong reason."
  exit 1
fi
if [ "$FIRED" -ne "$TOTAL" ]; then
  echo "::error::$FIRED of $TOTAL fired. Read WHICH row failed - an exit code alone"
  echo "         cannot tell a missing rule from a missing fixture."
  exit 1
fi
# The phrase is load-bearing, not decoration: check-harness-result.sh pairs a
# published `fired` field with a PRINTED tally by looking for "controls fired",
# and refused this harness when the line said "rows fired" - a field with no
# second reading beside it to disagree with.
echo "$FIRED/$TOTAL controls fired."
