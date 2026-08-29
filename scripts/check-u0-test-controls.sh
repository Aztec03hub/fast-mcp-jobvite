#!/usr/bin/env bash
# Positive-control harness for U0's own tests.
#
# Why this exists. Every U0 test asserts a property of a FILE - the manifest, the
# marker config, `.env.example`, `.gitignore`, the fixtures directory. That class of
# test is the easiest in the world to write green and hollow: a glob at a path that
# does not exist returns a clean empty list, a membership check over a set nobody
# populated passes, and a parser that matched nothing satisfies every assertion
# written over its output. A green from tests/ is worth exactly what their failure
# modes are worth, so each one is broken here on purpose and required to go red.
#
# The rule the design gates already follow (DESIGN.md:1483-1488, and the reason
# check-coupling-controls.py exists): a checker that has only ever passed is the
# same failure as the sentence it replaced.
#
# Each control makes ONE mutation to a COPY of the tree and requires the suite to
# fail with the NAMED test - not merely to fail, since a mutation that breaks
# collection outright would turn every control green while testing nothing.
#
# The real repository is read and never written.
#
# Usage: scripts/check-u0-test-controls.sh
# Exit 0 when every control fires, 1 otherwise. CI asserts fired == held and
# never a literal count.

set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Prefer the project venv; fall back to whatever `uv run` provides in CI.
if [ -x "$REPO/.venv/bin/python" ]; then
  PY=("$REPO/.venv/bin/python")
else
  PY=(uv run --frozen --project "$REPO" python)
fi

BAD=0
TOTAL=0

# The subset of the tree the suite reads. docs/ is required: conftest.py points
# FIXTURES_DIR into docs/research/fixtures.
#
# scripts/ added by U15: tests/test_file_type_gate.py imports the gate from
# scripts/check-committed-file-types.py, so without it this harness's copied
# tree fails at COLLECTION and every control below aborts. This is a one-entry
# data addition, not a change to U0's harness logic.
#
# .github added after 9ca76fe: tests/test_workflow_pins.py walks
# .github/workflows/ and carries a positive control asserting the walk actually
# found mirror.yml. Without .github staged, that control fires CORRECTLY - the
# walk really did find nothing in the copied tree - the BASELINE goes red, and
# the harness aborts before running a single control. So the gate went down
# reporting a true fact about a tree this script had built wrong.
#
# THIS IS THE FOURTH TIME, AND THE PREVIOUS COMMENT SAID WHAT TO DO ABOUT IT.
# U1 landed server.json at the repository root and
# test_server_json_declares_every_variable reads it; server.json was not in the
# list, so the file was absent from the copy, the baseline went red with a
# FileNotFoundError, and all eleven controls stopped running again.
#
# So the allow-list is gone, as its own comment prescribed. THE UNIT OF STAGING
# IS NOW THE TREE, with a deny-list of things that must not be copied. An
# allow-list of paths selects for exactly the path nobody thought of, and it
# selected for .github, then for tests/credentialed, and now for server.json.
# A deny-list fails the other way: a new directory is copied unnecessarily,
# which costs a little time and breaks nothing.
#
# Everything tracked by git is staged, which also means the copy matches what CI
# checks out rather than what somebody remembered to name. Untracked build
# artifacts (.venv, caches, .pytest_cache) are excluded for free, because git
# does not track them.
SKIP_TOP=(.git .venv venv node_modules)

stage () {
  local dest="$1"
  # Every tracked file, reproduced with its directory structure. `git -C ... ls-files`
  # is the authority on what the repository contains, which is the whole point:
  # nobody has to remember to add anything.
  local n
  n=$(cd "$REPO" && git ls-files | wc -l)
  [ "$n" -gt 0 ] || { echo "    STAGING CONTROL: git ls-files returned nothing"; return 1; }
  (cd "$REPO" && git ls-files -z | tar --null -cf - -T -) | (cd "$dest" && tar -xf -) || return 1
  # Positive control on the staging itself: the three files whose absence has
  # broken this harness before must be present in the copy. A staging step that
  # silently copies nothing produces a baseline failure that reads like a real one.
  local probe
  for probe in pyproject.toml server.json .github/workflows/mirror.yml; do
    [ -e "$REPO/$probe" ] || continue
    [ -e "$dest/$probe" ] || { echo "    STAGING CONTROL: $probe missing from the copy"; return 1; }
  done
}

run_control () {
  local name="$1" mutate="$2" expect="$3"
  TOTAL=$((TOTAL + 1))
  local work; work=$(mktemp -d)
  stage "$work" || { echo "--- CONTROL $name"; echo "    STAGING ERROR"; BAD=$((BAD+1)); rm -rf "$work"; return; }

  local before after
  before=$(cd "$work" && find . -type f -newer /dev/null | sort | xargs md5sum 2>/dev/null | md5sum)
  ( cd "$work" && eval "$mutate" )
  after=$(cd "$work" && find . -type f | sort | xargs md5sum 2>/dev/null | md5sum)
  echo "--- CONTROL $name"
  if [ "$before" = "$after" ]; then
    echo "    MUTATION WAS A NO-OP; this control would be vacuous"
    BAD=$((BAD + 1)); rm -rf "$work"; return
  fi

  local out rc
  out=$(cd "$work" && "${PY[@]}" -m pytest -q -p no:cacheprovider 2>&1); rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "    DID NOT FIRE: the suite is still green after the mutation"
    BAD=$((BAD + 1))
  elif printf '%s\n' "$out" | grep -q "$expect"; then
    echo "    exit=$rc, '$expect' named in the failure -> CONTROL FIRED"
  else
    echo "    exit=$rc but '$expect' was NOT the failing test -> WRONG TEST FIRED"
    printf '%s\n' "$out" | grep -E '^(FAILED|ERROR)' | sed 's/^/      /'
    BAD=$((BAD + 1))
  fi
  rm -rf "$work"
}

# The baseline is not decoration: if the unmutated copy is already red, every
# control below "fires" for a reason that has nothing to do with its mutation.
echo "BASELINE: the unmutated copy"
BASE=$(mktemp -d); stage "$BASE"
base_out=$(cd "$BASE" && "${PY[@]}" -m pytest -q -p no:cacheprovider 2>&1); base_rc=$?
printf '%s\n' "$base_out" | tail -2
rm -rf "$BASE"
if [ "$base_rc" -ne 0 ]; then
  echo "ABORT: the unmutated copy is already red. Fix that before running controls."
  exit 1
fi
echo "================================================================"

run_control "empty a deliberate non-secret default (draft 2's 'fix')" \
  "sed -i 's/^JOBVITE_MAX_RESULTS=50/JOBVITE_MAX_RESULTS=/' .env.example" \
  "test_the_deliberate_non_secret_defaults_are_intact"

run_control "a secret-class variable carries a value" \
  "sed -i 's/^JOBVITE_API_KEY=/JOBVITE_API_KEY=sk-live-abc123/' .env.example" \
  "test_every_secret_class_variable_is_empty"

run_control "drop *.pem from .gitignore" \
  "sed -i '/^\*\.pem$/d' .gitignore" \
  "test_gitignore_covers_every_credential_pattern"

run_control "un-ignore a credential with an extra negation" \
  "printf '!secrets/prod.key\n' >> .gitignore" \
  "test_gitignore_does_not_negate_the_credential_patterns"

run_control "remove --strict-markers from addopts" \
  "sed -i '/\"--strict-markers\",/d' pyproject.toml" \
  "test_an_undeclared_marker_fails_collection"

run_control "remove the -m selection from addopts" \
  "sed -i '/\"not credentialed and not network\",/d; /^  \"-m\",$/d' pyproject.toml" \
  "test_the_default_selection_deselects_the_credentialed_arm"

run_control "loosen the mcp pin to >=" \
  "sed -i 's/\"mcp==2.1.1\"/\"mcp>=2.1.1\"/' pyproject.toml" \
  "test_mcp_is_pinned_with_a_double_equals"

run_control "delete the fastmcp-slim justification comment" \
  "sed -i 's|# transitive prerelease; must be named or resolution fails||' pyproject.toml" \
  "test_the_fastmcp_slim_justification_comment_survives"

run_control "point FIXTURES_DIR at a path that does not exist" \
  "sed -i 's|\"docs\" / \"research\" / \"fixtures\"|\"docs\" / \"research\" / \"fixtures-typo\"|' tests/conftest.py" \
  "test_fixtures_directory_resolves"

run_control "drop a variable from .env.example" \
  "sed -i '/^JOBVITE_PAGINATION_START_BASE=/d' .env.example" \
  "test_the_parser_actually_found_variables"

run_control "make uv.lock disagree with the manifest" \
  "sed -i 's/^version = \"0.1.0\"/version = \"0.2.0\"/' pyproject.toml" \
  "test_uv_lock_check_passes_without_amending_the_lockfile"

echo "================================================================"
echo "$((TOTAL - BAD))/$TOTAL controls fired."
[ "$BAD" -eq 0 ]
