#!/usr/bin/env python3
"""A row floor must EQUAL its harness's row count, not bound it.

    python3 docs/reviews/check-row-floor-exactness.py

**THE DEFECT, and it was found in this repository rather than
imagined.** `check-u7-resilience-controls.sh` carried 31 rows against
`ROW_FLOOR=26`. Five rows could have been deleted with CI silent.
Neither branch was wrong: the 26 was honestly derived on
`chore/row-floors`, the five extra rows arrived on `feat/scan-bound`,
and `git merge-base --is-ancestor` says neither commit is an ancestor of
the other. **The MERGE produced the slack floor, and no instrument in
the repository compared a floor to a live count.**

A floor that is too HIGH fails loudly on the next run. A floor that is
too LOW says nothing, forever, which is why this direction needs a
checker and the other one does not.

**THE TABLE IS NOT COPIED HERE.** The row-invocation pattern for each
harness is parsed out of `check-row-floor-controls.sh`, which already
carries it. A second copy of that table is precisely the defect the
floors themselves keep producing - a number typed twice diverges at the
first merge.

**THE SECOND CLAIM: TWO FLOORS FOR ONE HARNESS MUST AGREE.** A floor
lives in two places - `ROW_FLOOR=<n>` inside the harness, and
`--min-rows <n>` on its `ci-harness-gate.sh` line in `ci.yml`. They are
derived at different times by different people, so where a harness has
both, they are two independent opinions about one number and any
disagreement is a defect in at least one of them.

This is not hypothetical either: `check-critical-coverage-amputation.sh`
carried `ROW_FLOOR=18` against `--min-rows 15` for as long as both
existed, and the external floor tolerated the loss of three rows the
internal one would have caught.

**THE THIRD CLAIM: `--min-rows` TIMES THE STEP'S SHARD COUNT MUST EQUAL
THE LIVE ROW COUNT (R12-H2, #270).** The first two claims both read the
INTERNAL floor, so the eight harnesses whose only floor is `--min-rows`
in `ci.yml` were checked by neither - and `ci-harness-gate.sh` compares
with `-lt`, a LOWER bound. Measured when this claim was added: u14's
amputation printed 16 rows against `--min-rows 10` and u7's printed 22
against 19. Six and three rows deletable with CI green, in the two
harnesses that GREW after their step was wired. That is the same defect
the docstring opens with, on the layer the docstring's own fix could not
see, which is why the population is now the whole of `ci.yml`'s
`--min-rows` set.

**AND THE MULTIPLIER IS WHY THE CLAIM IS STILL AN EQUALITY.** The claim
was written as `--min-rows == live`, which is right for a step that runs
its harness once and WRONG for one that splits it across lanes: a shard
running half the rows passes `--min-rows 5` against 10 declared ones,
and this checker turned that into "SLACK by 5", exit 1. Planted and read
rather than reasoned about (#268 §5), and it blocked sharding entirely -
the gate is wired, so no sharded step could ever be green. The rule is
now `live == min_rows * shards`, with the shard count read off the
step's `env:` block, because `ci-harness-gate.sh` runs the harness with
NO arguments and a flag could not reach it.

**THAT IS A TIGHTENING, NOT A RELAXATION, AND THE DISTINCTION IS THE
POINT.** `>=` was tried on this project's other floor comparison and was
measurably blind - arms=10 against floor=9 reported status=ok and exit 0
(#223) - so slack is not what a sharded step gets. It gets a different
MULTIPLIER against the same equality. A deleted row still reds, because
9 != 5 * 2. An UNEVEN split still reds too: 11 != 5 * 2, and 11 is
not a multiple of 2 at all, so a harness whose rows do not divide by its
lane count has no exact `--min-rows` to write, and the equality says so
instead of rounding. `shards` defaults to 1 where no `env:` names it,
which is every step in `ci.yml` today, so the unsharded verdict and both
of its messages are unchanged - arm A26 pins that rather than assuming
it.

**HOW THE THIRD CLAIM COUNTS, and why it is not a fourth table.** It
reads the harness's own `echo "########## $label"` row opener, takes the
function that line sits in, collects that function's call sites, and
tests the line each one WILL print against the gate's own `--row-re`.
Nothing about any harness is listed here. A harness whose shape cannot
be read that way is an ERROR, never a skip: skipping is exactly how
those eight went unchecked.

**THE FOURTH CLAIM: THE CONTAINER IS A KIND, NOT A GLOB (#187).** The
sentence above - "the exactness claim reaches the harnesses the control
table names" - was the whole guarantee, and it rested on a second one
that had quietly stopped holding: that the table's set EQUALS every
harness carrying a floor. That equality was enforced over
`scripts/*.sh`, and in one night three floors arrived outside it -
`ROW_FLOOR=12` in `docs/reviews/probe-131-gate-state.sh`, a bare
`floor = 14` in `docs/reviews/probe-wired-checker-amputation.py`, and
`arm_floor = 9` in `scripts/check-secrets-baseline.py`. All three are
wired into CI. None was missing from the table; all three were outside
the CONTAINER by construction, so the equality had nothing to say and
reported a clean pass over 25 of 29 members. **A container bounded by
PATH plus SUFFIX decays the moment its members move**, which is #115's
kind-not-path ruling arriving from the other side.

So the population is now every tracked `.py`/`.sh` under
`docs/reviews/` and `scripts/` - the same two directories #153 widened
`check-checkers-are-wired.py` to - carrying an identifier whose NAME
contains `floor` assigned an integer LITERAL. **The spelling is derived,
not listed.** A list of the three live spellings would be blind to the
fourth, and my own first selector was: it required a character before
the word and could not see a bare `floor = 14`.

Three consequences worth stating, because each is a bound rather than a
guarantee:

* **A fourth LOCATION is a finding, not an absence.** The same selector
  runs over the whole repository and anything it finds outside the two
  directories fails the run. That reads zero today, and the zero is
  proved non-vacuous by `--self-test` arm A6, which plants a floor in
  `src/` and requires the tripwire to see it.
* **A floor of 0 is not a floor** - this repository's own rule, from
  `scripts/lib/harness-result.sh`: *"Pass 0 as the floor for a harness
  that has none; 0 is not a floor anything can breach."* Every zero
  site must be registered WITH A REASON and every registration must
  still resolve, so a harness whose floor regressed to 0 cannot leave
  the population quietly.
* **A row count that is COMPUTED at run time has no static answer, and
  the table says so per file rather than skipping it.** Two members
  build their count while running - one increments `TOTAL` from three
  different helpers, the other is literally
  `rows = len(ARMS) + 2 * halves`. **That is not a `.py` problem, which
  is what it looks like: one of the two is a `.sh`.** They carry the
  token `COMPUTED` in the table, so the equality still holds in both
  directions and the default for a NEW member stays red. Task #193
  closed the gap by asserting equality on the canonical line both
  publish, and #194 built the two mechanisms that WATCH those floors
  fire: `mode=computed` in `check-row-floor-controls.sh` for the `.sh`,
  which reads `rows=N` from a first run instead of predicting it, and a
  `--self-test` for the `.py`. The token is now the FIRST WORD of the
  cell rather than the whole of it, because that control's deletion ERE
  rides after it - see `is_computed()`.
* **A COMPUTED member may carry MORE THAN ONE floor, and nothing else
  may.** `probe-wired-checker-amputation.py` has `FLOOR` for its own
  arms and `arm_floor` for its `--self-test`: two harnesses in one file
  with two different watchers. Where a source-derived row count IS being
  compared, two floors make the comparison unattributable and stay a
  finding - `_row_exactness()` draws that line and arms A19/A20 hold it
  in both directions.

**WHAT THIS STILL DOES NOT COVER, stated because a partial check selects
for the form it cannot see.** The agreement claim reaches only the
harnesses carrying BOTH floors. The container's vocabulary is the WORD
`floor`, so a floor named `MIN_ROWS` would be outside it - arm A3 pins
that. **The program prints every count on every run** - read them there
rather than here, because the counts once written into this docstring
were stale within hours of being typed. It also cannot tell a floor
DERIVED from a run from one that was typed and happens to be right;
only running the harness answers that.
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
CONTROLS = ROOT / "docs/reviews/check-row-floor-controls.sh"
SCRIPTS = ROOT / "scripts"
CI = ROOT / ".github/workflows/ci.yml"

# =====================================================================
# THE CONTAINER (#187). See the docstring section of the same name.
# =====================================================================

#: The same two directories and two suffixes that
#: `check-checkers-are-wired.py` uses. Named here rather than imported
#: because that file is a script, not a module, and a `sys.path` hack
#: to reach it would be a worse coupling than two constants that a
#: self-test arm compares.
#:
#: `FLOOR_RE`, an anchored `^\s*ROW_FLOOR=(\d+)\s*$`, used to sit here
#: and is DELETED rather than left beside the new rule. It had three
#: call sites, `FLOOR_ASSIGN` replaced all three, and a second floor
#: regex kept "for the shell case" is the fix rebuilding its own defect
#: one column over. `check-row-floors.py` still carries that spelling
#: for its own narrower question, which is a different claim about a
#: different set.
CONTAINER_DIRS = ("docs/reviews", "scripts")
CONTAINER_SUFFIXES = (".py", ".sh")

#: A FLOOR ASSIGNMENT, and the vocabulary is DERIVED rather than listed.
#: The three spellings live in the repository today are `ROW_FLOOR=12`,
#: `arm_floor = 9` and a bare `floor = 14`; a list of those three would
#: be blind to the fourth, which is the defect this whole file exists
#: for one level up. So the rule is STRUCTURAL: an identifier whose name
#: contains `floor`, assigned an integer LITERAL, as the whole of the
#: line. `ROW_FLOOR=$TOTAL` is deliberately not matched - it equals the
#: count by construction and passes with every row deleted, which
#: `check-row-floors.py` records at its own `FLOOR` regex.
#:
#: `pre` may not carry a quote: that is what keeps a floor written
#: INSIDE a string (`STUB_TAIL='... floor=1 ...'`, prose in a docstring)
#: out of the population. Anchoring at `$` does most of that work
#: already - a docstring sentence continues past the digits - but a
#: quote check costs one clause and closes the rest.
FLOOR_ASSIGN = re.compile(
    r"^(?P<pre>[^#'\"\n]*?)\b(?P<name>[A-Za-z_][A-Za-z0-9_]*)"
    r"\s*=\s*(?P<val>\d+)\s*(?:#.*)?$",
    re.M,
)

#: A LITERAL ZERO IS NOT A FLOOR, and that is this repository's own
#: published rule rather than a convenience invented here:
#: `scripts/lib/harness-result.sh` says *"Pass 0 as the floor for a
#: harness that has none; 0 is not a floor anything can breach, and it
#: reads as absent"*, and `check-coverage-floors.py` acts on the same
#: reading with a `if line_floor == 0: continue`.
#:
#: **A ZERO IS NOT SILENTLY DROPPED.** Every zero-valued floor site must
#: appear here WITH ITS REASON, and every entry here must still resolve
#: to a zero-valued site on disk - a stale exemption is as red as an
#: unregistered zero. Without both directions this would be the named
#: list the container was widened to abolish, and a harness whose floor
#: regressed to 0 would leave the population looking like a pass.
ZERO_IS_ABSENT: dict[tuple[str, str], str] = {
    ("scripts/lib/harness-result.sh", "HR_FLOOR"): (
        "the shared publisher's initialiser, not a harness's own floor. "
        "It is set from the caller by `harness_result_ran <rows> "
        "<floor>`, and the 0 it starts at is the documented spelling of "
        "ABSENT - see the comment above `harness_result_ran`."
    ),
    ("docs/reviews/check-coverage-floors.py", "line_floor"): (
        "a per-module accumulator reset inside the loop, then raised by "
        "`max` over every family that applies. The 0 is the "
        "no-family-matched case, and the next statement after the "
        "raises is `if line_floor == 0: continue`."
    ),
    ("docs/reviews/check-coverage-floors.py", "branch_floor"): (
        "the same accumulator for the branch column; only a module with "
        "a DESIGN role ever raises it above 0, and 0 prints as `-`."
    ),
}


def _tracked(dirs: tuple[str, ...]) -> list[str]:
    """Tracked files under `dirs`, as repo-relative POSIX paths.

    `git ls-files`, not a filesystem walk: an untracked scratch file an
    agent left in a worktree is not part of the repository's container,
    and three worktrees on this project are live at any moment.
    """
    done = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", *dirs],
        capture_output=True,
        text=True,
        check=False,
    )
    if done.returncode != 0:
        raise SystemExit(f"git ls-files failed: {done.stderr.strip()}")
    return [
        p
        for p in done.stdout.splitlines()
        if pathlib.PurePath(p).suffix in CONTAINER_SUFFIXES
    ]


def floor_sites(
    dirs: tuple[str, ...] = CONTAINER_DIRS,
) -> list[tuple[str, str, int]]:
    """Every `(path, identifier, value)` floor assignment in scope.

    Zeroes included - the caller separates them, because a zero that
    nobody has registered is a FINDING and dropping it here would be the
    silent skip.
    """
    out: list[tuple[str, str, int]] = []
    for rel in _tracked(dirs):
        try:
            text = (ROOT / rel).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for m in FLOOR_ASSIGN.finditer(text):
            if "floor" not in m.group("name").lower():
                continue
            out.append((rel, m.group("name"), int(m.group("val"))))
    return sorted(out)


def table_path(name: str) -> str:
    """Column 1 of the table, as a repo-relative path.

    A bare name still means `scripts/<name>` - 25 of the 29 rows are
    written that way and rewriting them all would be a diff with no
    reader. A member outside `scripts/` writes its path in full, which
    is the form that made the container widening (#187) possible at all:
    the table used to be a list of NAMES under one directory, so a floor
    that moved to `docs/reviews/` could not be named in it even by hand.
    """
    return name if "/" in name else f"scripts/{name}"


def _table() -> list[tuple[str, str, int]]:
    """`(harness PATH, row-invocation ERE, rows the ERE cannot match)`.

    Split from the LAST delimiters inward, not the first: one ERE in the
    table is `^control (MUT|AMP) `, and a `cut -f2` would truncate it at
    the `|` inside its own alternation. The control script documents
    that trap and this parser has to honour it too.
    """
    body = re.search(r'TABLE="\n(.*?)\n"', CONTROLS.read_text(encoding="utf-8"), re.S)
    if body is None:
        return []
    rows: list[tuple[str, str, int]] = []
    for line in body.group(1).splitlines():
        if not line.strip():
            continue
        name, rest = line.split("|", 1)
        rest = rest.rsplit("|", 1)[0]  # drop mode
        rest = rest.rsplit("|", 1)[0]  # drop the floor-breach exit code
        rest, extra = rest.rsplit("|", 1)
        rows.append((table_path(name), rest, int(extra)))
    return rows


def static_rows(text: str, ere: str, extra: int) -> int:
    """Rows the table's ERE finds in a harness's source.

    **TWO COUNTING RULES, and the ERE itself says which one applies.**
    By default every match is a row, which is what 25 shell harnesses
    with a `^mutate "`-shaped opener need.

    A `(?P<label>...)` group switches it to counting DISTINCT LABELS.
    That exists because a harness may write one row at two mutually
    exclusive sites: `probe-gate-swallowed-exceptions.py` has eight
    `row(` calls and prints seven rows, because its E row is written
    once in the try branch and once in the except; `check-secrets-
    baseline.py` has eleven `arm(` calls and prints nine.
    Counting sites there reports SLACK that does not exist, and the
    honest correction is not a negative number in the EXTRA column -
    that would be a hand-kept constant beside a container, the shape
    this file exists to delete. The label is a signal the harnesses
    already carry: they name their rows `A.`..`G.` and `C1`..`C9`
    because a reader has to tell them apart.

    **The group must be NAMED.** An unnamed group would have silently
    changed the meaning of the two table EREs that already have one -
    `^control (MUT|AMP) ` would have counted 2 instead of 15.
    """
    rx = re.compile(ere, re.M)
    if "label" in rx.groupindex:
        return len({m.group("label") for m in rx.finditer(text)}) + extra
    return len(rx.findall(text)) + extra


#: THE SHARD COUNT, and it travels as `env:` because it CANNOT travel
#: as a flag. `scripts/ci-harness-gate.sh:190` runs
#: `bash "$HARNESS_PATH"` with NO arguments, so nothing a gate line
#: writes after the harness name ever reaches the harness. That is a
#: reading of the gate, not a preference between two workable
#: spellings (#268 §5).
#:
#: **ABSENT MEANS ONE, AND ONE IS THE ONLY SILENT DEFAULT.** A step with
#: no `env:` block is a single-lane step, which is what every step in
#: this file is today, so `shards = 1` reproduces the previous rule
#: exactly. Every OTHER reading failure is an ERROR rather than a
#: default - see `_shard_count()`, and A25 for the refusal.
SHARD_ENV = "HARNESS_SHARDS"

#: A YAML step is a list item, and the `env:` block belonging to a gate
#: line is the one inside the SAME item. Bounding the search that way is
#: what stops a sibling step's shard count being read against this
#: step's `--min-rows` - a join error that would report a reassuring
#: pass, which is the failure mode `_external_floors()` already guards
#: its own count against.
STEP_ITEM = re.compile(r"^(?P<indent>[ ]*)-[ ]", re.M)


def _step_block(raw: str, pos: int) -> str:
    """The text of the YAML list item containing offset `pos`.

    The item runs from its own `- ` to the next `- ` at the SAME or a
    shallower indent, which is where the step ends whether or not it is
    the last step in its job.
    """
    starts = [m for m in STEP_ITEM.finditer(raw) if m.start() <= pos]
    if not starts:
        return ""
    here = starts[-1]
    indent = len(here.group("indent"))
    for nxt in STEP_ITEM.finditer(raw, here.end()):
        if len(nxt.group("indent")) <= indent:
            return raw[here.start() : nxt.start()]
    return raw[here.start() :]


def _shard_count(name: str, block: str) -> int:
    """How many lanes this step splits its harness across.

    **A SHARDED STEP RUNS A SUBSET, SO ITS `--min-rows` IS A FRACTION OF
    THE HARNESS'S ROWS.** Before this existed the third claim compared
    `--min-rows` to the whole live count and turned red on any sharded
    step - measured at `--min-rows 5` against 10 declared rows, exit 1,
    "SLACK by 5" (#268 §5). It blocked sharding entirely.

    The claim STAYS AN EQUALITY: `live == min_rows * shards`. A deleted
    row still reds, because 9 != 5 * 2. What the shard count buys is the
    right multiplier, not any slack - `>=` was measurably blind (#223)
    and is not coming back.

    **EVERY UNREADABLE VALUE IS AN ERROR, NEVER A DEFAULT OF 1.** A
    static checker cannot multiply by `${{ matrix.shards }}`, and
    quietly treating an expression as "unsharded" would compare a
    2-shard step against the whole count and red it for a reason nobody
    would trace to this line - or, if the arithmetic happened to work
    out, pass a step whose real shard count nothing here has seen. So a
    non-literal is refused loudly and the shard count must be written as
    a plain integer.
    """
    found = re.findall(rf"^\s*{SHARD_ENV}\s*:\s*(.+?)\s*$", block, re.M)
    if not found:
        return 1
    if len(found) > 1:
        raise SystemExit(
            f"{name}: {len(found)} {SHARD_ENV} values in one step, so which "
            "one the row count should be multiplied by is undecidable here."
        )
    value = found[0]
    if not re.fullmatch(r"['\"]?\d+['\"]?", value):
        raise SystemExit(
            f"{name}: {SHARD_ENV} is {value!r}, which is not an integer "
            "literal. A static checker cannot multiply the row count by an "
            "expression evaluated at run time, and treating it as unsharded "
            "would silently compare against the wrong multiple."
        )
    shards = int(value.strip("'\""))
    if shards < 1:
        raise SystemExit(
            f"{name}: {SHARD_ENV} is {shards}, and a step runs at least one "
            "lane. A count of 0 would make every row count 'expected' equal "
            "0 and pass with the whole harness deleted."
        )
    return shards


def _min_rows_verdict(name: str, min_rows: int, shards: int, live: int) -> list[str]:
    """CLAIM 3's verdict: `live` must EQUAL `min_rows * shards`.

    Split out of `main()` so `--self-test` arms THE SAME rule rather
    than a second copy of it - the discipline `_row_exactness()` already
    follows one claim up.

    With `shards = 1` the arithmetic and BOTH messages are
    byte-identical to what they were before sharding was readable,
    which is what arm A26 pins: the unsharded population is every step
    in `ci.yml` today, and a change that quietly reworded their
    findings would be a change to 16 live verdicts.
    """
    expected = min_rows * shards
    if live == expected:
        return []
    # The multiplication is shown only where there IS one. An unsharded
    # step printing "--min-rows 10 x 1 shards = 10" would be noise on
    # every step in the file.
    per = f" x {shards} shards = {expected}" if shards > 1 else ""
    if live > expected:
        return [
            f"{name}: SLACK by {live - expected}. It prints {live} "
            f"rows and ci.yml passes --min-rows {min_rows}{per}, so "
            f"{live - expected} row(s) can be deleted without the "
            "gate noticing. --min-rows is a LOWER bound; it must "
            "EQUAL the live count."
        ]
    return [
        f"{name}: --min-rows {min_rows}{per} exceeds the {live} rows "
        "it prints, so this step cannot pass."
    ]


def _external_floors() -> dict[str, tuple[int, str, int]]:
    """`(--min-rows, --row-re, shards)` per harness, off its gate line.

    Continuations are folded first: every one of these invocations wraps
    with a trailing backslash, so a line-at-a-time scan sees the harness
    name and its flags as separate lines and pairs nothing.

    The count is asserted against the number of `--min-rows` FLAGS, not
    every occurrence of the string - three sit inside comments, and
    counting those made a correct join look broken.

    `--row-re` is captured too, because `ci-harness-gate.sh` refuses
    `--min-rows` without it, and the third claim below cannot count rows
    without knowing which printed lines the gate will accept.
    """
    raw = CI.read_text(encoding="utf-8")
    joined = re.sub(r"\\\n\s*", " ", raw)
    found: dict[str, tuple[int, str, int]] = {}
    for match in re.finditer(r"ci-harness-gate\.sh\s+(\S+)([^\n]*)", joined):
        name, tail = match.group(1), match.group(2)
        flag = re.search(r"--min-rows\s+(\d+)", tail)
        if not flag:
            continue
        row_re = re.search(r"--row-re\s+'([^']*)'", tail)
        if row_re is None:
            raise SystemExit(
                f"{name}: --min-rows with no --row-re. ci-harness-gate.sh "
                "refuses that pairing at run time, so finding it here means "
                "ci.yml and the gate disagree."
            )
        # THE SHARD COUNT IS READ OFF THE RAW TEXT, not `joined`.
        # Folding continuations moves every offset after the first
        # wrapped gate line, so a step block located in `joined`
        # coordinates would drift into a neighbouring step - silently,
        # and in the direction that pairs one step's `--min-rows` with
        # another's shard count.
        anchor = raw.find(f"ci-harness-gate.sh {name}")
        shards = _shard_count(name, _step_block(raw, anchor) if anchor >= 0 else "")
        found[name] = (int(flag.group(1)), row_re.group(1), shards)
    flags = sum(
        1
        for line in raw.splitlines()
        if "--min-rows" in line and not line.lstrip().startswith("#")
    )
    if len(found) != flags:
        raise SystemExit(
            f"parsed {len(found)} --min-rows values but ci.yml carries {flags} "
            "as flags. The join is wrong, and a wrong join here reports a "
            "reassuring zero rather than an error."
        )
    return found


#: The line every harness prints to open a row. DERIVED, not listed:
#: the emitting function's NAME is read back out of the harness, so a
#: harness that calls its row function something new is still counted.
EMIT = re.compile(r'^\s*echo "##########\s*\$(?:label|1)"', re.M)

#: A shell function definition, `name() {`.
FUNC = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\(\)\s*\{", re.M)


def _live_rows(text: str, row_re: str) -> int | str:
    r"""Rows `--row-re <row_re>` will match when this harness runs.

    Returns the count, or a string saying why it could not be derived.
    **A harness whose shape cannot be read is an ERROR, never a skip** -
    skipping is how the eight externally-floored harnesses went
    unchecked in the first place.

    The method: find the `echo "########## $label"` that opens a row,
    take the function it sits in, collect that function's call sites at
    column 0, and test the line each one WILL print against the gate's
    own regex. Testing the printed line rather than the call site is
    what makes `^########## A[0-9]+ ` and `^########## [A-N]\. ` both
    work, and what keeps the harness's `BASELINE` banner out of the
    count.
    """
    emit = EMIT.search(text)
    if emit is None:
        return 'no `echo "########## $label"` row opener'
    enclosing = [m for m in FUNC.finditer(text) if m.start() < emit.start()]
    if not enclosing:
        return "the row opener is not inside a function"
    fn = enclosing[-1].group(1)
    calls = re.findall(rf'^{re.escape(fn)}\s+"([^"]*)"', text, re.M)
    if not calls:
        return f"row function {fn}() has no call sites at column 0"
    matched = sum(1 for label in calls if re.search(row_re, f"########## {label}"))
    if not matched:
        return (
            f"{fn}() has {len(calls)} call site(s) and the gate's row regex "
            f"{row_re!r} matches NONE of the lines they print. A regex that "
            "matches nothing looks identical to a harness that ran nothing."
        )
    return matched


def is_computed(ere: str) -> bool:
    """Does this table cell declare a run-time row count?

    **THE TOKEN IS THE FIRST WORD, NOT THE WHOLE CELL.** It was an
    equality against the whole field, and `mode=computed` in
    `check-row-floor-controls.sh` (#194) now writes `COMPUTED <ere>`:
    the token first, so this selector still sees it, and a deletion ERE
    after it so that control can neutralise one row and watch the floor
    breach. Two consumers, one cell, and the token has to be readable by
    the one that cannot use the rest.

    An equality here read `COMPUTED ^row "` as an ordinary ERE, counted
    ZERO rows in the harness and reported the floor as impossible. That
    is a red for a reason nobody would have chased to this line, which
    is why the rule is a token test rather than a longer literal.
    """
    return ere.strip().split()[:1] == ["COMPUTED"]


def _row_exactness(
    rel: str,
    ere: str,
    extra: int,
    declared: list[tuple[str, int]],
    text: str,
) -> tuple[list[str], list[str]]:
    """One table row's verdict: `(findings, lines to print)`.

    Split out of `main()` so `--self-test` arms THE SAME rules rather
    than a copy of them, and so the two-floor case below can be measured
    without planting a floor in a tracked file.

    **A FILE MAY CARRY MORE THAN ONE FLOOR ONLY WHEN ITS ROW COUNT IS
    COMPUTED, AND THAT IS A NARROW PERMISSION, NOT A RELAXATION.** For a
    static row the ambiguity is real and fatal: this function compares a
    source-derived row count against A floor, and with two of them
    nothing says which. For a COMPUTED row it compares NOTHING - there
    is no static count to attribute - so the question the refusal asks
    has no referent.

    `probe-wired-checker-amputation.py` is the member that needs it and
    the reason is structural rather than convenient: `FLOOR` gates its
    ten arms plus its container halves, and `arm_floor` gates the arms
    of its own `--self-test` (#194). They are two harnesses in one file
    with two different watchers, and collapsing them into one number
    would make one of the two unwatched again.
    """
    if not declared:
        return ([f"{rel}: no literal floor assignment"], [])

    computed = is_computed(ere)
    if len(declared) > 1 and not computed:
        return (
            [
                f"{rel}: {len(declared)} floor assignments "
                f"({', '.join(n for n, _ in declared)}) and nothing says "
                "which one the table's row count is about."
            ],
            [],
        )
    if computed:
        return (
            [],
            [
                f"  {rel:52} floor {val:3}  rows   ?  "
                f"COMPUTED at run time - no static count (#193), `{name}`"
                for name, val in declared
            ],
        )

    floor = declared[0][1]
    rows = static_rows(text, ere, extra)
    lines = [f"  {rel:52} floor {floor:3}  rows {rows:3}"]
    if rows > floor:
        return (
            [
                f"{rel}: SLACK by {rows - floor}. It has {rows} rows and a "
                f"floor of {floor}, so {rows - floor} row(s) can be deleted "
                "without the floor noticing. This is the direction that "
                "never announces itself."
            ],
            lines,
        )
    if rows < floor:
        return (
            [
                f"{rel}: floor {floor} exceeds its {rows} rows, so the "
                "harness cannot pass its own floor."
            ],
            lines,
        )
    return ([], lines)


def _container_gap(table: list[tuple[str, str, int]]) -> list[str]:
    """Harnesses carrying a `ROW_FLOOR` that the table does not name.

    R12-M1. The table is not a copy of any number - that much the
    docstring already got right - but it IS a hand-kept LIST beside a
    container it never compared itself to, and the container had a
    member it did not: `check-u15-gate-amputation.sh`, `ROW_FLOOR=5`,
    exact but unchecked. Enumerating `scripts/*.sh` and requiring the
    two sets to be EQUAL is what stops the next harness being added
    without being covered, which is the only durable form of this.

    Both directions are reported. A table row with no `ROW_FLOOR` on
    disk is just as wrong as a floor with no table row, and the
    existing per-row check would call it "not on disk" only if the
    whole file were missing.
    """
    sites = floor_sites()

    gap: list[str] = []

    # -- THE FOURTH-LOCATION TRIPWIRE ---------------------------------
    # The container is bounded by two directories, and a bound nobody
    # watches is how this file got its finding: `scripts/*.sh` was
    # correct when it was written and silently stopped covering the set
    # three floors later. So the SAME selector is run over the whole
    # repository, and anything it finds outside `CONTAINER_DIRS` is a
    # finding rather than an invisible non-member.
    #
    # It measures ZERO today, repo-wide, on 2026-09-01 - which is the
    # only reason the container's two directories are the right two.
    # That zero is proved non-vacuous by arm A6 of `--self-test`, which
    # plants a floor in a third directory and watches this fire.
    outside = [
        (rel, name, val)
        for rel, name, val in floor_sites((".",))
        if (rel, name, val) not in sites
    ]
    for rel, name, val in outside:
        gap.append(
            f"{rel}: `{name} = {val}` is a floor in a FOURTH LOCATION - "
            f"outside {', '.join(CONTAINER_DIRS)}. Either widen "
            "CONTAINER_DIRS so this file's floor is covered like every "
            "other, or move the harness. A floor outside the container "
            "is not exempt; it is unwatched, which is the state #187 "
            "found three CI-wired floors in."
        )

    # -- THE ZERO SITES, BOTH DIRECTIONS ------------------------------
    zeros = {(rel, name) for rel, name, val in sites if val == 0}
    for key in sorted(zeros - set(ZERO_IS_ABSENT)):
        gap.append(
            f"{key[0]}: `{key[1]}` is a floor of 0, and nothing in "
            "ZERO_IS_ABSENT says why. A floor of 0 is satisfied by zero "
            "rows, so it is either a harness whose floor was lost - the "
            "exact silent direction this file exists for - or an "
            "initialiser that means ABSENT, and only the second one may "
            "be registered."
        )
    for key in sorted(set(ZERO_IS_ABSENT) - zeros):
        gap.append(
            f"{key[0]}: ZERO_IS_ABSENT registers `{key[1]}` as a "
            "0-means-absent site and there is no such site on disk any "
            "more. A stale exemption certifies whatever moved into its "
            "place, so it is red rather than ignored."
        )

    on_disk = {rel for rel, _, val in sites if val > 0}
    if not on_disk:
        dirs = ", ".join(f"{d}/" for d in CONTAINER_DIRS)
        return gap + [
            f"NO file under {dirs} carries a literal floor. An empty "
            "container and a fully-covered one are the same green, so this "
            "is a finding rather than a pass."
        ]

    named = {path for path, _, _ in table}

    for missing in sorted(on_disk - named):
        gap.append(
            f"{missing}: carries a literal floor and the control table "
            "does not name it, so its floor is never compared to a row "
            "count. Add a row to TABLE in check-row-floor-controls.sh: "
            "an ERE that matches its row openers, a `(?P<label>...)` ERE "
            "if it writes one row at more sites than it prints, or the "
            "literal token COMPUTED if its row count is built at run "
            "time and no static count exists."
        )
    for extra in sorted(named - on_disk):
        gap.append(
            f"{extra}: named by the control table but carries no literal "
            "floor. One of the two is wrong."
        )
    return gap


def self_test() -> int:
    r"""Plant the defects this file's container is supposed to catch.

        python3 docs/reviews/check-row-floor-exactness.py --self-test

    **WHY THE ARMS ARE IN-PROCESS AND MUTATE ALMOST NOTHING.** Every arm
    feeds a synthetic string to the same selector `main()` uses, or
    calls `floor_sites()` with a narrowed directory tuple. Only A6
    touches the tree, and it removes its plant in a `finally` that A7
    then checks - so this can run in CI beside the checker itself, which
    `check-row-floor-controls.sh` cannot because it must break its
    subject.

    **A6 IS THE ONE THAT MATTERS AND IT IS THE HARD ONE.** The
    fourth-location tripwire reports zero repo-wide, and a zero with a
    plausible story is exactly what shipped last time. A6 plants a floor
    in a third directory and requires the tripwire to see it, which is
    the difference between "there are none" and "I looked and there are
    none".
    """
    arms: list[tuple[str, bool, str]] = []

    def arm(name: str, ok: bool, meaning: str) -> None:
        arms.append((name, ok, meaning))

    def sites(text: str) -> list[tuple[str, int]]:
        return [
            (m.group("name"), int(m.group("val")))
            for m in FLOOR_ASSIGN.finditer(text)
            if "floor" in m.group("name").lower()
        ]

    # -- THE VOCABULARY IS DERIVED, NOT LISTED -----------------------
    arm(
        "A1 a spelling that exists NOWHERE in this repository is matched",
        sites("GATE_FLOOR_V2 = 3\n") == [("GATE_FLOOR_V2", 3)],
        "the three live spellings would be a list, and a list is blind "
        "to the fourth - which is the whole finding of #187",
    )
    arm(
        "A2 all three LIVE spellings are matched by the one rule",
        sites("ROW_FLOOR=12\narm_floor = 9\n    floor = 14\n")
        == [("ROW_FLOOR", 12), ("arm_floor", 9), ("floor", 14)],
        "a bare `floor = 14` is the one my own first selector missed, "
        "because it required a character before the word",
    )

    # -- THE BOUND, PINNED RATHER THAN ASSUMED ------------------------
    arm(
        "A3 NEGATIVE CONTROL: an identifier without `floor` is invisible",
        sites("GATE_MINIMUM = 3\n") == [],
        "this is the container's real bound and it is worth stating: "
        "the vocabulary is the WORD, so a floor named `MIN_ROWS` would "
        "be outside it. Not a defect to fix here - a limit to know.",
    )
    arm(
        "A4 a computed floor is NOT a floor",
        sites('ROW_FLOOR=$TOTAL\nROW_FLOOR="${ROW_FLOOR:-9}"\n') == [],
        "`ROW_FLOOR=$TOTAL` equals the count by construction and passes "
        "with every row deleted; `check-row-floors.py` refuses it too",
    )
    arm(
        "A5 a floor inside prose or a comment is NOT a floor",
        sites("# ROW_FLOOR=26 is what it used to be\n")
        + sites("carried `ROW_FLOOR=26`. Five rows could have gone.\n")
        + sites("STUB='echo \"rows=1 floor=1\"'\n")
        == [],
        "this file's own docstring names ROW_FLOOR=26 twice, and a "
        "selector that read them would report the checker as a harness",
    )

    # -- THE FOURTH-LOCATION TRIPWIRE IS NOT VACUOUS ------------------
    # THE PLANT IS THE POINT. The tripwire's zero has a story - the two
    # container directories really are where the harnesses live - and a
    # zero that explains itself is the shape that shipped last time.
    planted = ROOT / "src" / "_probe_187_fourth_location.py"
    fired = False
    try:
        planted.write_text("SMOKE_FLOOR = 3\n", encoding="utf-8")
        subprocess.run(
            ["git", "-C", str(ROOT), "add", "-N", str(planted)],
            capture_output=True,
            check=False,
        )
        fired = any(rel.endswith(planted.name) for rel, _, _ in floor_sites((".",)))
    finally:
        subprocess.run(
            ["git", "-C", str(ROOT), "rm", "--cached", "-q", str(planted)],
            capture_output=True,
            check=False,
        )
        planted.unlink(missing_ok=True)
    arm(
        "A6 a floor planted in a THIRD directory is SEEN repo-wide",
        fired,
        "without this the tripwire's zero is a claim about where I "
        "looked. The plant is removed in a `finally`, and A7 proves the "
        "tree came back.",
    )
    arm(
        "A7 the plant was REMOVED - the tree is as it was",
        not planted.exists(),
        "a harness that leaves its own mutation behind has cost this "
        "project four measured incidents",
    )
    arm(
        "A8 the same planted floor is NOT in the default container",
        not any(rel.endswith(planted.name) for rel, _, _ in floor_sites()),
        "if it were, A6 would be measuring the container rather than "
        "the tripwire and both arms would pass for one reason",
    )

    # -- CONTAINER_DIRS IS LOAD-BEARING -------------------------------
    both = {rel for rel, _, v in floor_sites() if v > 0}
    scripts_only = {rel for rel, _, v in floor_sites(("scripts",)) if v > 0}
    arm(
        "A9 trimming CONTAINER_DIRS back to scripts/ LOSES members",
        len(both - scripts_only) > 0,
        f"{len(both - scripts_only)} member(s) live under docs/reviews/ "
        "and would silently leave the population - the #187 defect "
        "reproduced by shrinking the constant",
    )

    # -- THE TWO COUNTING RULES ---------------------------------------
    control_rows = "control MUT a\ncontrol AMP b\ncontrol MUT c\n"
    arm(
        "A10 an UNNAMED group does not switch on distinct-label counting",
        static_rows(control_rows, r"^control (MUT|AMP) ", 0) == 3,
        "`^control (MUT|AMP) ` is a live table ERE; counting distinct "
        "captures there would report 2 rows against a floor of 15",
    )
    two_sites_one_row = 'row(\n    "E. x",\n)\nrow(\n    "E. y",\n)\n'
    arm(
        "A11 a NAMED `label` group counts DISTINCT labels",
        static_rows(two_sites_one_row, r'row\(\n\s*"(?P<label>[A-Z])\.', 0) == 1,
        "two mutually exclusive sites print one row; counting sites "
        "reports SLACK that does not exist",
    )

    # -- THE ZERO REGISTER, BOTH DIRECTIONS ---------------------------
    real = dict(ZERO_IS_ABSENT)
    try:
        ZERO_IS_ABSENT.clear()
        arm(
            "A12 an UNREGISTERED zero floor is a finding",
            any("floor of 0" in line for line in _container_gap(_table())),
            "a floor of 0 is satisfied by zero rows, so a harness whose "
            "floor was lost must not read as a non-member",
        )
        ZERO_IS_ABSENT.update(real)
        ZERO_IS_ABSENT[("docs/reviews/nothing-here.py", "GONE_FLOOR")] = "stale"
        arm(
            "A13 a STALE registration is a finding",
            any("no such site on disk" in line for line in _container_gap(_table())),
            "an exemption that outlives its site certifies whatever moved in behind it",
        )
    finally:
        ZERO_IS_ABSENT.clear()
        ZERO_IS_ABSENT.update(real)

    # -- THE TABLE/CONTAINER EQUALITY, BOTH DIRECTIONS ----------------
    full = _table()
    arm(
        "A14 a member the TABLE does not name is a finding",
        any(
            "does not name it" in line
            for line in _container_gap([r for r in full if "u7-resilience" not in r[0]])
        ),
        "this is R12-M1's claim and the direction that never announces itself",
    )
    arm(
        "A15 a TABLE row with no floor on disk is a finding",
        any(
            "carries no literal floor" in line
            for line in _container_gap([*full, ("scripts/ci-harness-gate.sh", "^x", 0)])
        ),
        "a table row pointing at a floorless file is just as wrong, and "
        "the per-row check would only have caught a MISSING file",
    )
    arm(
        "A16 the container is NOT empty",
        len(both) > 0,
        "an empty container and a fully-covered one are the same green",
    )

    # -- THE `COMPUTED` TOKEN, AND THE CELL THAT CARRIES MORE --------
    # #194 gave `check-row-floor-controls.sh` a `computed` mode, and the
    # deletion ERE it needs lives after the token in the SAME cell. An
    # equality test read that cell as an ordinary regex, matched zero
    # rows and called the floor impossible - a red nobody would have
    # traced back to a string comparison.
    arm(
        "A17 `COMPUTED <ere>` is still a COMPUTED cell",
        is_computed('COMPUTED ^row "') and is_computed("COMPUTED"),
        "the token is the FIRST WORD. Two consumers share this cell and "
        "the one that cannot use the ERE must still read the token.",
    )
    arm(
        "A18 NEGATIVE CONTROL: an ERE that merely mentions it is not",
        not is_computed('^row "COMPUTED'),
        "a substring test would make any harness whose row opener quoted "
        "the word exempt from the static comparison, silently",
    )

    # -- TWO FLOORS IN ONE FILE, BOTH DIRECTIONS ----------------------
    # `probe-wired-checker-amputation.py` carries `FLOOR` for its own
    # arms and `arm_floor` for its `--self-test` (#194): two harnesses
    # in one file with two different watchers. That is permitted ONLY
    # where no static count is being attributed to either.
    two = [("FLOOR", 14), ("arm_floor", 11)]
    arm(
        "A19 two floors are ACCEPTED on a COMPUTED row",
        _row_exactness("x.py", "COMPUTED", 0, two, "")[0] == [],
        "a COMPUTED row compares nothing, so 'which one is the row count "
        "about' has no referent - and collapsing the two would leave one "
        "of the file's two harnesses unwatched again",
    )
    arm(
        "A20 two floors are STILL a finding on a static row",
        any(
            "floor assignments" in line
            for line in _row_exactness("x.sh", '^row "', 0, two, "")[0]
        ),
        "this is the permission's bound. Where a source-derived row count "
        "IS compared, two floors make the comparison unattributable, and "
        "A19 must not have widened that away.",
    )

    # -- THE SHARD MULTIPLIER, BOTH DIRECTIONS (#270) -----------------
    # A wired gate that reds on every sharded step blocked the whole
    # sharding programme, and it was found by planting `--min-rows 5`
    # against 10 rows and reading exit 1 (#268 §5). These arms feed
    # `_min_rows_verdict()` - the SAME function `main()` calls - rather
    # than a second copy of the arithmetic.
    arm(
        "A21 a sharded step with the right arithmetic PASSES",
        _min_rows_verdict("h.sh", 5, 2, 10) == [],
        "10 rows across 2 lanes is --min-rows 5. Before this the checker "
        "compared 5 against 10 and called it SLACK by 5, exit 1, which "
        "is a red on every sharded step there could ever be.",
    )
    # A DELETED ROW MOVES `live` DOWN, so it lands on the CANNOT-PASS
    # message, not on SLACK. My first version of this arm asserted
    # "SLACK by 1" and FAILED, which is the arm doing its job: #268's
    # "9 != 5*2" is true about the arithmetic and says nothing about
    # which of the two messages the equality reaches for.
    short = _min_rows_verdict("h.sh", 5, 2, 9)
    arm(
        "A22 a sharded step ONE ROW SHORT still REDS",
        short != [] and "exceeds the 9 rows" in short[0],
        "THIS IS THE ARM THAT MATTERS. 9 != 5*2, so the equality still "
        "catches a deleted row. If sharding had been let in as a `>=` "
        "this arm would pass vacuously - #223 measured that blindness.",
    )
    arm(
        "A23 a sharded harness that GREW is SLACK, the other direction",
        any("SLACK by 2" in line for line in _min_rows_verdict("h.sh", 5, 2, 12)),
        "12 rows against 5 x 2 leaves 2 deletable unnoticed. This is the "
        "direction claim 3 was written for - u14 at 16 against 10 - and "
        "the multiplier must not have blinded it.",
    )
    arm(
        "A24 an UNEVEN split REDS rather than rounding",
        _min_rows_verdict("h.sh", 5, 2, 11) != [],
        "11 rows do not divide across 2 lanes, so no --min-rows is "
        "exact. Rounding would hand back the lower bound this whole "
        "claim exists to abolish.",
    )
    # A NON-LITERAL SHARD COUNT IS AN ERROR, NEVER A DEFAULT OF 1. A
    # static checker cannot multiply by an expression, and defaulting
    # would compare a real 2-shard step against the whole row count.
    expr_refused = False
    try:
        _shard_count(
            "h.sh",
            f"      - name: x\n        env:\n"
            f"          {SHARD_ENV}: ${{{{ matrix.n }}}}\n",
        )
    except SystemExit:
        expr_refused = True
    arm(
        "A25 a `${{ }}` shard count is REFUSED, not treated as unsharded",
        expr_refused,
        "silently reading an expression as 1 lane is the fail-open "
        "shape: it compares a sharded step against the whole count and "
        "reds it for a reason nobody would trace to this line",
    )
    # THE UNSHARDED POPULATION IS EVERY STEP IN ci.yml TODAY. A change
    # that reworded their findings would be a change to 16 live
    # verdicts, so the previous strings are pinned rather than assumed.
    arm(
        "A26 shards=1 leaves BOTH messages byte-identical",
        _min_rows_verdict("h.sh", 10, 1, 16)
        == [
            "h.sh: SLACK by 6. It prints 16 rows and ci.yml passes "
            "--min-rows 10, so 6 row(s) can be deleted without the gate "
            "noticing. --min-rows is a LOWER bound; it must EQUAL the "
            "live count."
        ]
        and _min_rows_verdict("h.sh", 17, 1, 14)
        == [
            "h.sh: --min-rows 17 exceeds the 14 rows it prints, so this "
            "step cannot pass."
        ],
        "this is the arm that would catch MY OWN change going wrong. "
        "u14 at 16 rows against 10 is the real measurement that put "
        "claim 3 here; the shard multiplier must not have reworded it.",
    )
    # THE `env:` READ IS BOUNDED BY THE STEP. A shard count belonging to
    # a neighbouring step, paired with this step's --min-rows, is a join
    # error that reports a reassuring pass.
    two_steps = (
        "      - name: sharded\n"
        "        env:\n"
        f"          {SHARD_ENV}: 2\n"
        "        run: bash scripts/ci-harness-gate.sh a.sh --min-rows 5\n"
        "      - name: plain\n"
        "        run: bash scripts/ci-harness-gate.sh b.sh --min-rows 9\n"
    )
    arm(
        "A27 a sibling step's shard count does NOT leak across",
        _shard_count("a.sh", _step_block(two_steps, two_steps.find("a.sh"))) == 2
        and _shard_count("b.sh", _step_block(two_steps, two_steps.find("b.sh"))) == 1,
        "reading the whole file for `HARNESS_SHARDS` would give b.sh a "
        "count of 2 and let 9 rows pass against --min-rows 9 x 2 = 18, "
        "or red it - either way a verdict about the wrong step",
    )

    failed = [a for a in arms if not a[1]]
    for name, ok, meaning in arms:
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"  -> {meaning}"))

    # THE ARM FLOOR. `failed == 0` is satisfied by zero arms - the exact
    # defect R19 measured on `check-secrets-baseline.py`, in a file with
    # no floor, which is one of the four members this widening exists
    # for. Writing this self-test without one would have rebuilt that
    # defect inside the fix for it.
    #
    # AND IT PUTS THIS FILE IN ITS OWN CONTAINER, which is the correct
    # outcome rather than an awkward one: the checker is a tracked `.py`
    # under `docs/reviews/` carrying a literal floor, so it needs a row
    # in the control table like every other member - and a run of
    # `main()` says so if it does not have one.
    arm_floor = 27
    status = "ok" if not failed and len(arms) >= arm_floor else "breach"
    print(
        f"\nHARNESS-RESULT name={pathlib.Path(__file__).name} "
        f"rows={len(arms)} floor={arm_floor} "
        f"fired={len(arms) - len(failed)}/{len(arms)} status={status}"
    )
    if len(arms) < arm_floor:
        print(
            f"::error::{len(arms)} arms against a floor of {arm_floor} - "
            "an arm was DELETED."
        )
        return 1
    return 1 if failed else 0


def main() -> int:
    table = _table()
    if not table:
        print(f"PARSED ZERO ROWS out of {CONTROLS.relative_to(ROOT)}.")
        print("An empty parse and a clean table are the same green, so")
        print("this is exit 2 rather than a pass.")
        return 2

    bad: list[str] = _container_gap(table)
    for rel, ere, extra in table:
        path = ROOT / rel
        if not path.exists():
            bad.append(f"{rel}: named by the control table but not on disk")
            continue
        text = path.read_text(encoding="utf-8")
        # THE FLOOR IS FOUND BY THE CONTAINER'S OWN RULE, not by
        # `ROW_FLOOR=` alone: two members spell it `arm_floor = 9` and
        # `floor = 14`, and an anchored `ROW_FLOOR` search would have
        # reported them as carrying no floor - which is the finding
        # this widening exists for, restated one column over.
        declared = [(nm, val) for r, nm, val in floor_sites() if r == rel and val > 0]

        # COMPUTED: THE CHECKER SAYS SO PER FILE RATHER THAN SKIPPING.
        # Two members build their row count at run time - `TOTAL` is
        # incremented from three different helpers in one, and the other
        # is literally `rows = len(ARMS) + 2 * halves`. No static count
        # of source sites can reach either number: the first has nine
        # increment sites and prints twelve rows.
        #
        # **THIS IS NOT THE `.py` PROBLEM IT LOOKS LIKE.** One of the
        # two is a `.sh`. The axis is whether the row count is a
        # property of the SOURCE at all, and for these it is not.
        #
        # The token is in the TABLE, not in a register beside it, so the
        # container equality still holds in both directions and the
        # DEFAULT for a new member stays RED. Task #193 closed the gap
        # by asserting equality on the canonical line these two publish,
        # and #194 built the two mechanisms that WATCH those floors
        # fire: `mode=computed` in the control for the `.sh`, and a
        # `--self-test` for the `.py`.
        #
        # The whole verdict is `_row_exactness()` so that `--self-test`
        # arms it rather than a second copy of these rules.
        findings, lines = _row_exactness(rel, ere, extra, declared, text)
        for line in lines:
            print(line)
        bad.extend(findings)

    external = _external_floors()
    paired = 0
    derived = 0
    print("\n  --min-rows, against the rows the harness will actually print:")
    for name in sorted(set(external)):
        min_rows, row_re, shards = external[name]
        # `ci-harness-gate.sh` builds `scripts/$harness` itself, so the
        # names on its lines are bare and always under scripts/. That is
        # the gate's rule, not this checker's, so it stays a join on
        # SCRIPTS rather than becoming a path.
        rel = f"scripts/{name}"
        path = SCRIPTS / name
        if not path.exists():
            bad.append(f"{name}: ci.yml passes it --min-rows but it is not on disk")
            continue
        text = path.read_text(encoding="utf-8")

        # CLAIM 3, R12-H2. `--min-rows` is a LOWER bound and nothing
        # compared it to a live count, so the eight harnesses with no
        # internal floor were unchecked in both directions. Measured
        # when this was written: u14's amputation held 16 rows against
        # 10 and u7's held 22 against 19 - six and three rows deletable
        # with CI green. Both grew AFTER their step was wired, which is
        # the merge-produced slack that put u7's CONTROLS at 26 v 31.
        live = _live_rows(text, row_re)
        if isinstance(live, str):
            bad.append(f"{name}: cannot derive a row count - {live}")
        else:
            derived += 1
            lanes = f"  x {shards} shards" if shards > 1 else ""
            print(f"  {name:42} --min-rows {min_rows:3}  rows {live:3}{lanes}")
            bad.extend(_min_rows_verdict(name, min_rows, shards, live))

        # THE SAME CONTAINER RULE AS CLAIM FOUR, not `ROW_FLOOR=` alone.
        # This is the fix rebuilding its own defect one column over if
        # it is left as it was: an anchored `ROW_FLOOR` search here
        # would read a harness spelling its floor `arm_floor = 9` as
        # carrying NO internal floor, skip the agreement check for it,
        # and not say so - which is the shape #187 is about, on the
        # layer #187 was not looking at.
        internal_floors = [v for r, _, v in floor_sites() if r == rel and v > 0]
        if not internal_floors:
            continue
        if len(internal_floors) > 1:
            bad.append(
                f"{name}: {len(internal_floors)} floor assignments, so "
                "which one ci.yml's --min-rows should agree with is "
                "undecidable here."
            )
            continue
        paired += 1
        internal = internal_floors[0]
        if internal != min_rows:
            bad.append(
                f"{name}: ROW_FLOOR={internal} but ci.yml passes "
                f"--min-rows {min_rows}. Two independent opinions "
                "about one number, and the lower one tolerates losing "
                f"{abs(internal - min_rows)} row(s) the other catches."
            )

    # THE CONTAINER CENSUS, PRINTED (#187). Never written into the
    # docstring: the counts that were once typed into it went stale
    # within hours, which the docstring itself now records.
    sites = floor_sites()
    zeros = sorted({(r, n) for r, n, v in sites if v == 0})
    members = sorted({r for r, _, v in sites if v > 0})
    named = {path for path, _, _ in table}
    computed = sorted(p for p, e, _ in table if is_computed(e))
    dirs = ", ".join(f"{d}/" for d in CONTAINER_DIRS)
    kinds = ", ".join(CONTAINER_SUFFIXES)
    print(f"\nCONTAINER: tracked {kinds} under {dirs} carrying a literal floor")
    print(f"  members (floor > 0)                                  {len(members):3}")
    print(f"  named by the control TABLE - EQUAL both directions    {len(named):3}")
    print(f"  of those, row count COMPUTED at run time (#193)       {len(computed):3}")
    for rel in computed:
        print(f"      {rel}")
    print(f"  0-means-absent sites, each registered with a reason   {len(zeros):3}")
    for rel, name in zeros:
        print(f"      {rel}  `{name}`")

    print(f"\nHarnesses checked for exactness: {len(table)}")
    print(f"Harnesses carrying BOTH floors, checked for agreement: {paired}")
    print(f"Harnesses whose --min-rows was compared to a live count: {derived}")
    if not bad:
        print("Every floor equals its harness's live row count. OK.")
        return 0

    print(f"\n{len(bad)} floor(s) wrong:")
    for line in bad:
        print(f"  {line}")
    print(
        "\nDerive the floor from a run of the harness and write that number "
        "in, rather\nthan adjusting it until this passes - the count and the "
        "floor agreeing for the\nwrong reason is how u7 reached 26 against 31."
    )
    return 1


if __name__ == "__main__":
    if "--self-test" in sys.argv[1:]:
        sys.exit(self_test())
    sys.exit(main())
