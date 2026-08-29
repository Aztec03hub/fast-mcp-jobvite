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
SUITE="tests/test_config.py tests/test_boot.py tests/test_shutdown.py tests/test_server.py tests/test_logging_process.py"

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
s, n = re.subn(r"    finally:\n        sys\.stdout\.flush\(\)\n        sys\.stderr\.flush\(\)\n.*?\n        os\._exit\(status\)\n",
               "", s, count=1, flags=re.S)
assert n == 1, "amputation H found nothing to remove; the anchor moved"
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


# --- J. the log sink is never configured at all ---------------------------
# H-1's shipped tree, amputated rather than mutated: `configure_logging` is
# still defined, still importable and still documented - it is simply never
# called, which is exactly the shape the defect had. Everything that claims
# "the audit event carries its mandated fields" must die here.
python3 - "$MAIN" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
anchor = "\nconfigure_logging()\n"
assert s.count(anchor) == 1, "J anchor is not unique"
p.write_text(s.replace(anchor, "\n"))
PY
report "J. configure_logging() is never called"

# --- K. it is called and configures NOTHING -------------------------------
# The clean-empty trap on a function rather than a module: the call site is
# present, the name resolves, the body does nothing. Loguru's autoinit
# handler survives, so the stream is NOT silent - it carries the field-less
# line the review measured. An assertion that only proves the stream is
# non-empty passes here, and that is the survivor worth naming.
python3 - "$MAIN" <<'PY'
import pathlib, re, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
anchor = "    _loguru.remove()"
assert s.count(anchor) == 1, "K anchor is not unique"
start = s.index(anchor)
end = s.index("\n\n\nconfigure_logging()", start)
p.write_text(s[:start] + "    return" + s[end:])
PY
report "K. configure_logging() runs and configures NOTHING"

# --- L. the record FILTER redacts nothing ---------------------------------
# The RECORD half. `_redact_message` mutates `record["message"]`, which is
# what every handler in the process sees - including one this project did not
# install, and the suite itself is such a handler.
#
# THIS ROW ONCE SURVIVED 78/78 AND THE SURVIVAL WAS AN INSTRUMENT FAULT. Once
# the sink began redacting what it renders, every arm in this suite - all of
# which read the process's own stream - stopped being able to see the filter
# at all, and the filter was briefly deleted on that evidence. The full suite
# then went red on a foreign sink. The arm that fixes the instrument is
# tests/test_logging_process.py::test_a_sink_this_project_did_not_install_sees_a_redacted_record
# and it must die here.
python3 - "$MAIN" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
anchor = '    message = record.get("message")'
assert s.count(anchor) == 1, "L anchor is not unique"
p.write_text(s.replace(anchor, "    return True\n" + anchor))
PY
report "L. the record filter returns without redacting"

# --- N. the SINK-level redaction is bypassed ------------------------------
# The RENDERED half. `serialize` emits `record["exception"]` and a `text`
# carrying the formatted traceback, neither of which is `record["message"]`,
# so the filter above cannot reach them. Measured before this sink existed: a
# stdlib `logger.exception` published the feed URL twice, in the clear.
python3 - "$MAIN" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
anchor = "        _redacting_sink(sys.stderr),"
assert s.count(anchor) == 1, "N anchor is not unique"
p.write_text(s.replace(anchor, "        sys.stderr,"))
PY
report "N. the sink writes the serialised record without redacting it"

# --- M. stdlib logging is never bridged into loguru -----------------------
# Two logging systems again, both live, writing two shapes onto one fd.
python3 - "$MAIN" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); s = p.read_text()
anchor = "    logging.basicConfig("
assert s.count(anchor) == 1, "J anchor is not unique"
start = s.index(anchor)
end = s.index("    )\n", start) + len("    )\n")
p.write_text(s[:start] + "    return\n" + s[end:])
PY
report "M. stdlib logging is never bridged into loguru"
echo "########## END. Survivors above are the finding, not a failure."
