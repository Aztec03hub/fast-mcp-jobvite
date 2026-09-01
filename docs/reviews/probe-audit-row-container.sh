#!/usr/bin/env bash
# THE AUDIT-ROW CONTAINER PROBE (task #97).
#
# THE QUESTION. `event.result_status = "error"` is how every tool in
# this server records that an invocation failed. The audit row is the
# only surviving evidence anyone has afterwards, so a failure written
# down as a success is a record that lies - and NOTHING in the
# repository's gate stack can see it. Coverage cannot: every one of
# these lines is EXECUTED on every run, by cases that assert the
# caller-visible half (`is_error`, the problem object) on their way to
# asserting something else. `tools/candidates.py` reads 100.00% line
# AND 100.00% branch with two of its four such rows asserted by
# nothing at all.
#
# WHY A CONTAINER PROBE AND NOT FOUR CHOSEN SITES. Task #97's brief
# named two files and one arm. A hand-kept list of the places to look
# is blind to the member nobody added, so the population here is
# derived: `grep -rn 'result_status = "error"' src/` gives SIX sites
# and all six are rows below. `--list` prints the derived population
# against the rows so the two sets can be compared rather than trusted.
#
# THE VERDICT IS THE WHOLE SUITE'S EXIT CODE. A row that leaves the
# suite green is a behaviour the repository has no assertion about.
# Survivors are the OUTPUT, not a failure, so this probe REPORTS and
# exits 0 unless it could not run - the fix for a survivor is a test,
# and that is a task, not a build break.
#
# PYTHONDONTWRITEBYTECODE=1: `.pyc` invalidation keys on (mtime, size),
# and deleting one line can leave the same size inside one second, in
# which case stale bytecode runs and the row fakes a clean result.

set -uo pipefail

export PYTHONDONTWRITEBYTECODE=1

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT" || exit 3

JOBS="src/fast_mcp_jobvite/tools/jobs.py"
CANDIDATES="src/fast_mcp_jobvite/tools/candidates.py"
BACKUP_DIR=$(mktemp -d)
trap 'rm -rf "$BACKUP_DIR"' EXIT

# THIS GUARD DID NOT EXIST. Every sibling harness refuses to run on a tree
# somebody is mid-edit in; this one went straight to mutating `src/`. The
# restore here is `cp` from a backup, so nothing was ever DESTROYED - but a
# matrix run over an uncommitted edit reports on code nobody declared and
# calls it a measurement of HEAD.
if [ -n "$(git status --porcelain -- src/)" ]; then
  echo "ABORT: src/ has uncommitted changes (staged, unstaged or untracked)."
  echo "       This probe mutates src/; the rows would describe your edit,"
  echo "       not HEAD. Commit or stash first."
  exit 3
fi

ROWS=0
APPLIED=0
VACUOUS=0

# ---------------------------------------------------------------------------
# probe <label> <file> <old> <new>
# ---------------------------------------------------------------------------
probe() {
  local label="$1" file="$2" old="$3" new="$4"
  ROWS=$((ROWS + 1))

  local backup
  backup="$BACKUP_DIR/${ROWS}_$(echo "$file" | tr / _)"
  cp "$file" "$backup" || { echo "$label: COULD NOT BACK UP"; return; }

  # A non-unique anchor is REFUSED rather than applied to the first
  # hit: the `except` line appears three times in `candidates.py` and
  # twice in `jobs.py`, so a first-hit replacement would amputate a
  # DIFFERENT tool's audit row and produce a plausible wrong verdict.
  if ! OLD="$old" NEW="$new" FILE="$file" python3 - <<'PY'
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
    echo "$label: ANCHOR DID NOT APPLY - fix the probe, do not read a verdict"
    cp "$backup" "$file"
    return
  fi

  # A write that matched nothing succeeds silently, so LANDING is
  # compared against the backup rather than assumed from exit 0.
  if cmp -s "$file" "$backup"; then
    echo "$label: AMPUTATION DID NOT LAND despite a successful write"
    cp "$backup" "$file"
    return
  fi
  APPLIED=$((APPLIED + 1))

  local out rc
  out=$(timeout -k 30 900 uv run --frozen pytest -q -p no:cacheprovider 2>&1)
  rc=$?
  cp "$backup" "$file"

  # A HANG WOULD READ AS "NOT VACUOUS". The verdict below is `rc -eq 0` ->
  # VACUOUS, so a timeout (124) silently scores as the reassuring outcome:
  # the mutation looks caught by a test when nothing ran at all. Named and
  # refused rather than counted.
  if [ "$rc" -eq 124 ]; then
    printf '%-40s TIMED OUT after 900s - NEVER FINISHED\n' "$label"
    echo "    no verdict: a hang is not evidence the failure is recorded"
    return 1
  fi

  printf '%-40s exit %s  %s\n' "$label" "$rc" "$(printf '%s\n' "$out" | tail -1)"
  if [ "$rc" -eq 0 ]; then
    VACUOUS=$((VACUOUS + 1))
    echo "    *** VACUOUS: the failure is recorded by nobody ***"
  fi
}

if [ "${1:-}" = "--list" ]; then
  echo "THE DERIVED POPULATION - every site must appear as a row below:"
  grep -rn 'result_status = "error"' src/
  exit 0
fi

echo "THE DERIVED POPULATION:"
grep -rn 'result_status = "error"' src/
echo

probe "jobs.py search_jobs" "$JOBS" \
'                result = build_result(payload, settings.max_results)
            except Exception as exc:  # noqa: BLE001 - every failure becomes a problem
                event.result_status = "error"' \
'                result = build_result(payload, settings.max_results)
            except Exception as exc:  # noqa: BLE001 - every failure becomes a problem'

probe "jobs.py get_job_feed" "$JOBS" \
'                result = build_feed_result(payload, settings.max_results)
            except Exception as exc:  # noqa: BLE001 - every failure becomes a problem
                event.result_status = "error"' \
'                result = build_feed_result(payload, settings.max_results)
            except Exception as exc:  # noqa: BLE001 - every failure becomes a problem'

probe "candidates.py search_candidates" "$CANDIDATES" \
'                    result = build_result(payload, settings.max_results)
                except Exception as exc:  # noqa: BLE001 - every failure is a problem
                    event.result_status = "error"' \
'                    result = build_result(payload, settings.max_results)
                except Exception as exc:  # noqa: BLE001 - every failure is a problem'

probe "candidates.py get_candidate" "$CANDIDATES" \
'                    record = _one_record(payload)
                except Exception as exc:  # noqa: BLE001 - every failure is a problem
                    event.result_status = "error"' \
'                    record = _one_record(payload)
                except Exception as exc:  # noqa: BLE001 - every failure is a problem'

probe "candidates.py approval refusal" "$CANDIDATES" \
'                    event.result_status = "error"
                    emit(event, AuditPhase.BEFORE_SIDE_EFFECT)' \
'                    emit(event, AuditPhase.BEFORE_SIDE_EFFECT)'

probe "candidates.py create_candidate" "$CANDIDATES" \
'                    result = build_create_result(payload)
                except Exception as exc:  # noqa: BLE001 - every failure is a problem
                    event.result_status = "error"' \
'                    result = build_create_result(payload)
                except Exception as exc:  # noqa: BLE001 - every failure is a problem'

echo
echo "ROWS: $ROWS   APPLIED: $APPLIED   VACUOUS: $VACUOUS"

# THE TREE, not a claim about it. A probe that mutated six files and
# left one behind would poison every later measurement in the session.
if ! git diff --quiet -- src/; then
  echo "TREE LEFT DIRTY UNDER src/ - a restore failed. STOPPING."
  git diff --stat -- src/
  exit 3
fi
echo "TREE RESTORED CLEAN"

if [ "$ROWS" -ne "$APPLIED" ]; then
  echo "A ROW DID NOT APPLY. It measured nothing and said so."
  exit 1
fi
