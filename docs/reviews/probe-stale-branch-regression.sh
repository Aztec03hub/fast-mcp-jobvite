#!/usr/bin/env bash
# Would merging this branch DELETE work from main?
#
# WHY THIS EXISTS. The handoff carried a hand-written warning that
# `review/r18` must not be merged, because its `probe-131-gate-state.sh`
# is the 190-line version and main's has grown to 356. That warning was
# correct and it was ALSO the wrong shape: it named ONE branch, it had
# to be re-derived by hand every time main moved, and it said nothing
# about the four other unmerged branches - all of which turned out to
# have exactly the same property.
#
# A branch that is behind main is not "unmerged work waiting to land".
# It is an ANCESTOR, and merging it replaces the newer side with the
# older one on every file where they disagree. `git merge` will do that
# without complaint and report no conflict, because there is none: one
# side simply has fewer lines and git has no opinion about which side
# is the improvement.
#
# WHAT IT MEASURES. Per file that differs, the line count on each side.
# Line count is a PROXY - a branch could be genuinely better AND shorter
# - so a REGRESSION verdict is a reason to read the diff, never on its
# own a reason to refuse.
#
# THE SURVEY'S FIRST RUN FOUND A HAZARD I DID NOT EXPECT, AND IT IS THE
# REASON THIS IS A SCRIPT AND NOT A HANDOFF SENTENCE. Of six unmerged
# branches, five regressed - four of them genuinely stale, and the fifth
# `fix/194-floor-firing-container` A BRANCH AN AGENT WAS STILL WORKING
# ON. It regresses `check-brief-report-refs-controls.sh` by 149 lines,
# not because the agent did anything wrong, but because two commits
# landed on main after it forked. Nothing about the branch changed; MAIN
# MOVED UNDER IT.
#
# So this is not a test for abandoned branches. Any long-running branch
# acquires the property silently while its author is heads-down, and it
# is invisible at merge time: git reports no conflict, because there is
# none. Run this before landing an agent's work, not only before landing
# an old one.
#
# USAGE
#   probe-stale-branch-regression.sh                 survey every unmerged
#                                                    branch, exit 0
#   probe-stale-branch-regression.sh <branch>        judge one branch;
#                                                    exit 1 if merging it
#                                                    would delete lines
#
# The one-branch form is the pre-merge question. Run it BEFORE `git
# merge`, not after: this project has already had a merge resolution put
# back damage a branch had fixed, and the reason it was caught was that
# somebody happened to look.
set -euo pipefail

BASE="${BASE:-main}"

judge() {
    local branch="$1" regressed=0 files=0
    git rev-parse --verify --quiet "$branch" >/dev/null || {
        echo "NO SUCH BRANCH: $branch" >&2
        return 2
    }
    printf '=== %s (%s commits not in %s)\n' \
        "$branch" "$(git rev-list --count "$BASE..$branch")" "$BASE"
    # -z + read -d '' because a path may contain whitespace.
    while IFS= read -r -d '' f; do
        files=$((files + 1))
        # A file the branch DELETES or ADDS is not a line-count question.
        git cat-file -e "$BASE:$f" 2>/dev/null || {
            printf '    only-on-branch   %s\n' "$f"
            continue
        }
        git cat-file -e "$branch:$f" 2>/dev/null || {
            printf '    DELETES on merge %s\n' "$f"
            regressed=$((regressed + 1))
            continue
        }
        local bn mn
        bn=$(git show "$branch:$f" | wc -l)
        mn=$(git show "$BASE:$f" | wc -l)
        if [ "$mn" -gt "$bn" ]; then
            printf '    REGRESSION -%-5s %s  (branch %s, %s %s)\n' \
                "$((mn - bn))" "$f" "$bn" "$BASE" "$mn"
            regressed=$((regressed + 1))
        else
            printf '    ahead      +%-5s %s\n' "$((bn - mn))" "$f"
        fi
    done < <(git diff -z --name-only "$BASE...$branch")

    if [ "$files" -eq 0 ]; then
        # A branch with commits but no differing files is fully absorbed.
        printf '    no differing files - already absorbed into %s\n' "$BASE"
    fi
    printf '    files=%s regressed=%s\n' "$files" "$regressed"
    [ "$regressed" -eq 0 ]
}

if [ $# -ge 1 ]; then
    # THREE outcomes, not two. `judge` returns 2 for a branch that does
    # not exist, and an if/else collapses that onto the REGRESSION arm -
    # so a typo in a branch name came back as a confident "merging would
    # delete lines from main" about a branch that is not there. Caught by
    # this probe's own ARM 3, which is why the arm exists: a refusal that
    # misdiagnoses is worse than a bare one, because it answers a
    # question you did not ask and sounds certain doing it.
    set +e
    judge "$1"
    verdict=$?
    set -e
    if [ "$verdict" -eq 2 ]; then
        printf '\nVERDICT %s: NO SUCH BRANCH. Nothing was measured.\n' "$1"
        printf 'This is not a merge judgement - the probe never ran one.\n'
        exit 2
    fi
    if [ "$verdict" -eq 0 ]; then
        printf '\nVERDICT %s: merging deletes nothing. Read the diff anyway.\n' "$1"
        exit 0
    fi
    printf '\nVERDICT %s: MERGING WOULD DELETE LINES FROM %s.\n' "$1" "$BASE"
    printf 'Line count is a proxy. Read the diff before you decide - but do\n'
    printf 'not merge on the assumption that a branch is newer than %s.\n' "$BASE"
    exit 1
fi

rc=0
found=0
while IFS= read -r branch; do
    [ "$branch" = "$BASE" ] && continue
    [ "$(git rev-list --count "$BASE..$branch")" -eq 0 ] && continue
    found=$((found + 1))
    judge "$branch" || rc=$((rc + 1))
    echo
done < <(git branch --format='%(refname:short)')

printf 'SURVEY: %s unmerged branches, %s would delete lines from %s.\n' \
    "$found" "$rc" "$BASE"
if [ "$found" -eq 0 ]; then
    printf 'Zero unmerged branches. That is a real answer, not a broken scan:\n'
    printf 'check with `git branch --format=%%(refname:short) | wc -l`.\n'
fi
exit 0
