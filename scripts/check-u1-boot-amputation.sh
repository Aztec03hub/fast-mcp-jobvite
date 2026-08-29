#!/usr/bin/env bash
# U1 AMPUTATION harness. A DIFFERENT question from the mutation harness.
#
#   Mutation asks: "break one rule - does the named test notice?"
#   Amputation asks: "remove the SUBJECT ENTIRELY - does anything still
#   report success?"
#
# In every unit built on this project so far, amputation found an assertion
# that survived mutation and was vacuous. A test that passes when its
# subject is not there is not a weak test, it is a false instrument.
#
# THIS HARNESS DOES NOT EXIT NON-ZERO ON SURVIVORS. Survivors are the
# OUTPUT: each row names every assertion that still reported success against
# a tree with the behaviour removed. It exits non-zero only if it could not
# run, or if the intact baseline is red.
#
# PYTHONDONTWRITEBYTECODE=1 on every run, and the tree is restored from a
# byte copy taken at the top (never `git checkout --`, which would revert
# uncommitted work along with the amputation).

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 3

CONFIG="src/fast_mcp_jobvite/config.py"
MAIN="src/fast_mcp_jobvite/__main__.py"
SERVER="src/fast_mcp_jobvite/server.py"
SUITE="tests/test_config.py tests/test_boot.py tests/test_shutdown.py tests/test_server.py"

WORK="$(mktemp -d)"
trap 'cp "$WORK/config.py" "$CONFIG"; cp "$WORK/__main__.py" "$MAIN"; \
      cp "$WORK/server.py" "$SERVER"; rm -rf "$WORK"' EXIT
cp "$CONFIG" "$WORK/config.py"
cp "$MAIN" "$WORK/__main__.py"
cp "$SERVER" "$WORK/server.py"

restore() {
  cp "$WORK/config.py" "$CONFIG"
  cp "$WORK/__main__.py" "$MAIN"
  cp "$WORK/server.py" "$SERVER"
}

report() {  # $1 = label
  local label="$1"
  echo "########## $label"
  # A HARD WALL-CLOCK CAP, because an amputated tree can HANG rather than
  # fail: removing a refusal let an in-process arm fall through to serving
  # forever, and a hang is indistinguishable from a slow run until someone
  # looks. The interlock in tests/test_server.py fixes that specific case;
  # this cap is what stops the NEXT one costing half an hour.
  timeout 300 env PYTHONDONTWRITEBYTECODE=1 uv run --frozen pytest $SUITE \
    -p no:cacheprovider -q -rA >"$WORK/out.txt" 2>&1
  if [ $? -eq 124 ]; then
    echo "  TIMED OUT after 300s - the amputated tree HANGS rather than failing"
  fi
  restore
  tail -1 "$WORK/out.txt"
  local survivors
  survivors=$(grep -E '^PASSED ' "$WORK/out.txt" | sed 's/^PASSED //' || true)
  if [ -z "$survivors" ]; then
    echo "  survivors: NONE - no assertion passed against this tree"
  else
    echo "  survivors (assertions that still reported success):"
    echo "$survivors" | sed 's/^/    /'
  fi
  echo
}

echo "########## BASELINE - the intact tree"
if ! PYTHONDONTWRITEBYTECODE=1 uv run --frozen pytest $SUITE -q \
     -p no:cacheprovider >"$WORK/base.txt" 2>&1; then
  echo "ABORT: the intact tree is red; amputation results would be meaningless."
  tail -20 "$WORK/base.txt"
  exit 3
fi
tail -1 "$WORK/base.txt"
echo

# --- A. config.py does not exist at all -----------------------------------
rm -f "$CONFIG"
report "A. config.py does not exist at all"

# --- B. config.py exists and is ZERO BYTES --------------------------------
# The clean-empty trap: the import of the MODULE succeeds, so anything that
# does not actually reach a name inside it keeps passing.
: > "$CONFIG"
report "B. config.py exists but is ZERO BYTES"

# --- C. validate_settings() runs and refuses NOTHING ----------------------
# Every refusal amputated at once, with the function, its name, its
# signature and its callers all still present. This is the shape a real
# regression takes: the module imports, boot succeeds, nothing is checked.
python3 - "$CONFIG" <<'PY'
import pathlib, re, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
s = re.sub(
    r"    reasons: list\[str\] = \[\]\n(?:.*?\n)*?        raise ConfigurationError\(reasons\)\n",
    "    return\n",
    s,
    count=1,
)
p.write_text(s)
PY
report "C. validate_settings() refuses nothing"

# --- D. the transport refusals are gone entirely --------------------------
# The TLS refusal and the token requirement both live in _check_transport.
# Removing the whole function is the amputation; M1 and M6 only disabled one
# branch each.
python3 - "$CONFIG" <<'PY'
import pathlib, re, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
s = s.replace("    _check_transport(settings, reasons)\n", "")
p.write_text(s)
PY
report "D. _check_transport is never called"

# --- E. the rule TABLE is empty, not the code -----------------------------
# Amputating the DATA. Every function is present and runs; the matrix it
# consults holds nothing, so no tool ever requires anything.
python3 - "$CONFIG" <<'PY'
import pathlib, re, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
s = re.sub(r"TOOL_REQUIREMENTS: Final\[dict\[str, tuple\[str, \.\.\.\]\]\] = \{\n.*?\n\}",
           "TOOL_REQUIREMENTS: Final[dict[str, tuple[str, ...]]] = {}",
           s, flags=re.S)
p.write_text(s)
PY
report "E. TOOL_REQUIREMENTS is an EMPTY table"

# --- F. the tool allow-list is empty --------------------------------------
python3 - "$CONFIG" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
s = s.replace("KNOWN_TOOLS: Final[frozenset[str]] = READ_TOOLS | WRITE_TOOLS",
              "KNOWN_TOOLS: Final[frozenset[str]] = frozenset()")
p.write_text(s)
PY
report "F. KNOWN_TOOLS is EMPTY"

# --- G. the shutdown handler does not exist -------------------------------
# Not "installs nothing" (that is M11) but "the function is gone", so a
# caller that referenced it would fail loudly rather than silently.
python3 - "$MAIN" <<'PY'
import pathlib, re, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
s = re.sub(r"def _install_shutdown_handler\(\) -> None:\n(?:.*?\n)*?    signal\.signal\(signal\.SIGTERM, _term\)\n",
           "def _install_shutdown_handler() -> None:\n    return\n", s, count=1)
s = re.sub(r"def _term\(signum: int, frame: FrameType \| None\) -> None:\n(?:.*?\n)*?    raise KeyboardInterrupt\n",
           "", s, count=1)
p.write_text(s)
PY
report "G. _term and the handler installation are GONE"

# --- H. the whole finally block is gone -----------------------------------
python3 - "$MAIN" <<'PY'
import pathlib, re, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
s = re.sub(r"    finally:\n        sys\.stdout\.flush\(\)\n        sys\.stderr\.flush\(\)\n.*?\n        os\._exit\(0\)\n",
           "", s, count=1, flags=re.S)
p.write_text(s)
PY
report "H. the finally block (flush + os._exit) is GONE"

# --- I. server.py builds a bare FastMCP -----------------------------------
# No lifespan, no mask_error_details, no settings. Everything server.py
# exists to configure, removed.
python3 - "$SERVER" <<'PY'
import pathlib, re, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
s = re.sub(r"    composed = make_base_lifespan\(settings\)\n(?:.*?\n)*?    \)\n",
           "    return FastMCP(name=SERVER_NAME)\n", s, count=1)
p.write_text(s)
PY
report "I. build_server returns a BARE FastMCP"

echo "########## END. Survivors above are the finding, not a failure."
