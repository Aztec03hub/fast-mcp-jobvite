# BASH-STANDARD - report

**Agent:** `bash-standard` · **Task:** #24 · **Branch:** `chore/bash-standard` · **Base:** `eb4d254`
**Standard:** `evolv-coder-standards/standards/devops/bash.md`, v1.0.2, `priority: required`,
`applicable_to: [bash, shell, ci-cd, automation]`

---

## 1. The shellcheck measurement, before anything was changed

**Install.** shellcheck was not on this host. Installed from the upstream release tarball rather
than a package manager, so the version is pinned and reproducible:

```
https://github.com/koalaman/shellcheck/releases/download/v0.10.0/shellcheck-v0.10.0.linux.x86_64.tar.xz
sha256  6c881ab0698e4e6ea235245f22832860544f17ba386442fe7e9d629f8cbedf87
version 0.10.0
```

v0.10.0 is not an arbitrary choice: it is the `rev:` the standard's own pre-commit block pins at
`bash.md:764`. Never `uv run --with shellcheck` - it is a Haskell binary, not a Python dependency,
and that path resolves outside the lock (ADR-0015).

**Run, over all 15 scripts, at default severity:**

```
shellcheck -f json scripts/*.sh          exit 1
```

| Severity | Count |
|---|---|
| **error** | **0** |
| **warning** | **3** |
| info | 10 |
| style | 2 |
| **total** | **15** |

By code:

| Severity | Code | n | Message |
|---|---|---|---|
| info | SC2086 | 8 | Double quote to prevent globbing and word splitting |
| warning | SC2155 | 2 | Declare and assign separately to avoid masking return values |
| style | SC2001 | 2 | See if you can use `${variable//search/replace}` instead |
| info | SC2016 | 2 | Expressions don't expand in single quotes |
| warning | SC2034 | 1 | `SKIP_TOP` appears unused |

Six of the fifteen scripts are completely clean: `check-suite-floor.sh`, `check-u1-pid1-shutdown.sh`,
`check-u11-advisory-controls.sh`, `check-u15-gate-controls.sh`, `check-u4-client-amputation.sh`,
`check-u4-client-controls.sh`.

### The number that decides the task

The brief's test was "if it is noisy, do not wire it". **It is not noisy.** And the decisive figure
is not the 15 above - it is the count at the threshold the standard itself specifies. `bash.md:741`
gives the CI form and `:767` the pre-commit args, and **both are `--severity=warning`**:

```
shellcheck --severity=warning --format=gcc scripts/*.sh          exit 1

scripts/check-u0-test-controls.sh:72:1:  warning: SKIP_TOP appears unused.                    [SC2034]
scripts/check-u5-jobs-amputation.sh:75:9: warning: Declare and assign separately...           [SC2155]
scripts/check-u5-jobs-controls.sh:66:9:  warning: Declare and assign separately...            [SC2155]
```

| Threshold | Findings |
|---|---|
| `--severity=error` | **0** |
| `--severity=warning` (**the specified gate**) | **3** |
| `--severity=info` | 13 |
| `--severity=style` | 15 |

**Three findings, in two files, across 3374 lines.** This is the wire-it case, not the fourth
refusal. The gate is one small commit away from landing green, and all three are one-line fixes.

**I did not make those three fixes.** They are in `scripts/*.sh` content, which `harness-gates` owns
this round; the dispatch said to message rather than edit. The proposal is in §5.

### One of the three is a real defect, not lint noise

`SC2034` at `check-u0-test-controls.sh:72` is worth reading on its own:

```bash
SKIP_TOP=(.git .venv venv node_modules)
```

`grep -rna 'SKIP_TOP' . --exclude-dir=.git` returns **that one line and nothing else**. It is
declared and never read.

It is a refactor vestige, and the comment block immediately above it (`:60-71`) still describes it as
the live mechanism - *"THE UNIT OF STAGING IS NOW THE TREE, with a deny-list of things that must not
be copied"*. There is no deny-list. `stage()` uses `git ls-files`, which needs none, and the comment
even says so two sentences later. So the prose documents a mechanism the code does not have.

Nothing is broken today - `git ls-files` is genuinely the right answer and the dead array changes no
behaviour. But this is the inoperative-code shape, and it is exactly what a linter is for: it was
sitting in a file that eight review rounds have passed over, and shellcheck found it in 0.2 seconds
on first run.

**Suggested fix:** delete line 72, and reword `:65-66` from *"with a deny-list of things that must
not be copied"* to *"and the tree is enumerated by `git ls-files`, so nothing has to be listed at
all"* - which is what the code actually does and what the rest of the comment already argues.

### The other two, with fixes

**SC2155 x2** - `check-u5-jobs-amputation.sh:75` and `check-u5-jobs-controls.sh:66`, same shape:

```bash
local backup="$BACKUP_DIR/$(echo "$file" | tr / _)"
```

`local` returns its own status, masking the substitution's. Here the masked command is `echo | tr`,
which does not meaningfully fail, so **the risk is theoretical**. I am not going to inflate it. It
is worth fixing anyway for a reason specific to this repository: masked exit codes are the failure
class these harnesses exist to detect, and a suppression here would read badly.

**Suggested fix**, two lines each:

```bash
local backup
backup="$BACKUP_DIR/$(echo "$file" | tr / _)"
```

### The twelve below the threshold, and why I am not proposing to fix them

`SC2086` (8) and `SC2016` (2) are `info`; `SC2001` (2) is `style`. The specified gate does not see
them. I read all twelve. **One deserves a second look and eleven do not:**

`check-u1-boot-controls.sh:73` is `uv run --frozen pytest $named -q` - an intentionally unquoted
`$named`, because it is a word list that must split. That is correct as written and quoting it would
break it; if the gate is ever raised to `--severity=info` this is the site that needs an explicit
`# shellcheck disable=SC2086` with the justification `bash.md:743` requires. Recording it now so
whoever raises the threshold does not have to re-derive it.

---

## 2. `bash.md:40` read at source, and the ADR decision

### The clause, quoted

`bash.md:36-41`:

> Every script MUST begin with:
>
> ```bash
> #!/usr/bin/env bash
> set -euo pipefail
> ```

**There is no exception clause anywhere in the document.** I searched the whole file for one - every
occurrence of `set -e`, `set +e`, `errexit`, `exit code` and `$?`. The nearest candidate is
`:277-278` and it points the *other* way:

> ```bash
> # Let set -e handle most failures. Use explicit checks for
> # commands that are allowed to fail.
> ```

That is the standard answering this exact question, and its answer is **keep `-e`, guard the
individual command**. `:802` does say "`set -e` has surprising edge cases", but under the heading
**"When NOT to Use Bash"** - it is an argument for writing the thing in Python, not for writing bash
without `-e`.

**So it is a deviation, not compliance. The clause does not admit it.** The brief asked me to decide
this rather than assume it, and the honest answer is the less convenient one.

### What is actually in the tree

Measured at `eb4d254`, grepping whole files:

```
grep -n '^set ' scripts/*.sh        -> 15 files, all `set -uo pipefail`
grep -l '^set -euo pipefail$' ...   -> 0
head -1 -q scripts/*.sh | sort -u   -> #!/usr/bin/env bash    (15/15 compliant)
```

The shebang half of the same clause is met by every script. Only `-e` is missing.

*(The dispatch's warning about `head -12` reproduces: these files carry long comment prologues and
the `set` line sits between lines 17 and 54, so a header-only grep reports 0 of 15 carrying any
strict-mode line and fits a tempting "nobody applied this" story. Whole-file grep gives 15 of 15.)*

### Why `-e` is not cosmetic here, measured in both arms

I did not take "these harnesses need to continue past a failing run" on trust. The probe is committed
at `docs/reviews/probe-set-e-vs-harness.sh` - runnable, rather than described:

```
ARM A: set -uo pipefail          # the tree today
    captured rc=1  out=boom
    RESTORE RAN
    outer sees exit=0

ARM B: set -euo pipefail         # what bash.md:40 mandates
    outer sees exit=1
    (no rc captured, no output captured, RESTORE never ran)
```

Same body, one flag different. Two consequences, and the second is the one that changes the verdict:

1. **The measurement is destroyed.** Twelve sites use `out=$(cmd); rc=$?`
   (`grep -n '=\$?' scripts/*.sh`). Under `-e` the assignment's non-zero status exits the shell
   before `rc=$?` runs, so the harness cannot distinguish a fired mutation from an unfired one.
2. **The mutation is left in the working tree.** In `check-u1-boot-controls.sh` the `restore` call
   is at `:76`, right after `rc=$?` at `:75`. Under `-e` the shell dies at `:73-74` and `restore`
   never runs. The script's own next lines (`:77-79`, `RESTORE FAILED - the mutation is still in the
   tree`, `exit 3`) exist because that state is recognised as serious - and `-e` would produce it
   silently rather than report it.

So `-e` would not merely turn survivors into crashes. It would leave edited source on a developer's
checkout.

### Decision

**ADR-0023, `Proposed`**, at `docs/adr/0023-harnesses-drop-e-from-strict-mode.md`, indexed in
`docs/adr/README.md`.

**The brief said the next free ADR number was 0022. It is not - `0022-no-cookie-jar-is-a-disable-
not-an-omission.md` exists**, added by `a39bd2a`. I used **0023**. Flagging it because a retyped
constant decaying is the failure `PREAMBLE.md` is itself about, and the next brief will carry the
same stale number unless somebody changes it.

The ADR records the deviation honestly, states the standard-conformant alternative
(`rc=0; out=$(cmd) || rc=$?`, which is `-e`-safe) and says why it is not taken *in this pass* rather
than pretending it is unavailable: it is a twelve-site edit across the harnesses every other gate
depends on, and a mis-converted site is invisible until the day a mutation genuinely survives. It
scopes itself to the fifteen harnesses and explicitly does not license omitting `-e` generally, and
it names the obligation the deviation creates (harnesses must assert their own preconditions, as
`stage()` already does, since `-e` is not there to catch them).

---

## 3. Obligation rows

`bash.md` had **zero** coverage. Confirmed independently: `grep -c "bash.md" docs/OBLIGATIONS.md`
-> 0, and `grep -rl "bash.md" --include="*.md" .` at `eb4d254` returned only the brief itself.

Two rows added, and **the ids are `BASH-n`, not `B107`/`B108`.** `bash.md` is not in CONF-6's corpus
at all - `grep -i bash docs/reviews/CONF-6-PROPAGATION-AUDIT.md` returns nothing, which is precisely
*why* it arrived with no coverage. Numbering its clauses into that corpus would assert a census that
never enumerated them. `check-obligations.py`'s `ROW` regex was widened to admit the namespace, with
the reasoning in a comment beside the existing `B49b` one.

| Row | Class | Clause | Why |
|---|---|---|---|
| **BASH-1** | SUPERSEDED | `devops/bash.md:36-41` | Artifact is ADR-0023. Records the strict-mode deviation, so it stops being invisible |
| **BASH-2** | ABSENT | `devops/bash.md:734` | "All scripts MUST pass ShellCheck with zero warnings." Artifact `-`, because nothing runs it. The note carries the by-severity counts so the next reader does not re-measure |

**A control, because the new namespace is exactly the kind of thing that passes vacuously.**
`check-obligations.py`'s own `ROW` comment warns about "a row that looks tracked and is never
verified", and a silently-skipped row is invisible in a green run. `docs/reviews/probe-bash-namespace-
amputation.sh` deletes BASH-1's subject from the ADR and requires the checker to go red **and name
BASH-1**:

```
mutation landed
restored
checker exit under amputation = 1
    Mappings: 31 | anchors verified against their subject: 22 | recorded as absent: 8
    FAIL: BASH-1: 'the clause admits no exception' is nowhere in
    docs/adr/0023-harnesses-drop-e-from-strict-mode.md. ...
CONTROL FIRED: the BASH-* namespace is parsed and verified.
```

Verified count drops 23 -> 22 under the amputation, so BASH-1 was among the verified. Restore checked
against **git**, not against the backup alone: `git diff --quiet HEAD -- <adr>` is clean.

**A negative arm, because a control that only ever passes proves nothing about what it is testing.**
`/tmp` script, not committed: revert `ROW` to `B\d+[a-z]?` and re-run the probe. It **must** fail.

```
mutation landed (regex reverted to B-only)
restored
probe exit with the namespace REMOVED = 1
    CONTROL DID NOT FIRE: a BASH-* row is being SILENTLY SKIPPED.
NEGATIVE ARM CORRECT: the probe notices the namespace being dropped.
```

So the probe is falsifiable both ways: it fires when the anchor breaks, and it fails when the
namespace it exists to guard is removed.

### The probe went vacuous within the hour, and this is how I found out

Worth recording, because it is the sharper of the two lessons in this section and it happened to me
rather than to the codebase.

The first version of this probe **hard-coded** the anchor `` Keep `set -uo pipefail` in ``. When the
clause-citation bug above forced me to change BASH-1's subject to `the clause admits no exception`,
the probe kept amputating the old literal - **which still existed elsewhere in the ADR**, in the
Decision section. So the mutation landed, the checker correctly stayed green (I had not touched the
real anchor), and the probe reported `CONTROL DID NOT FIRE`.

The failure was silent in the sense that matters: nothing about the probe's own output said *"you
edited the fixture and this literal no longer refers to it"*. It said the namespace was broken, which
was false. I only caught it because I re-ran everything after an unrelated edit to the ADR's scope
paragraph, and something that had passed twenty minutes earlier now failed.

**Fixed by removing the class rather than the instance:** the probe now reads the artifact and
subject **out of the BASH-1 row itself**, so there is exactly one place either value lives. A
hard-coded copy of a value that lives somewhere else is a second list, and it decays the moment the
first one moves.

### The bug this control caught in passing

My first BASH-1 anchor was `` Keep `set -uo pipefail` in ``. `check-obligations.py` verified it
happily. `check-clause-citations.py` **silently dropped the row** - its count stayed at 22 while the
other checker said 31 mappings / 8 absent. Its `ROW` regex (`:53-56`) requires a backticked
artifact *and* a backticked subject, and my subject contained backticks of its own.

I noticed only because I compared two numbers that had no reason to be compared. I fixed my anchor
(a backtick-free unique subject) rather than loosening someone else's regex, and the clause now
resolves in both: **22 -> 23**, and the text it prints back is the MUST I quoted in §2, which is the
read-back that proves the citation says what the row claims.

**But the general defect is still there, and it is worse for the rows I did not add.** Filed as
**task #31**: `check-clause-citations.py` cannot parse an ABSENT row at all, because an ABSENT row
must carry `-` in the artifact and subject cells. **All 8 ABSENT rows** - B16, B61, B74, B76, B79,
B84, B96 and my BASH-2 - have a clause citation that no checker has ever resolved. For a MET row the
citation rotting still leaves the row tethered to an artifact; for an ABSENT row **the citation is
the entire row**, and it is the one column with no check.

### Clauses of `bash.md` that got no row, and why

Following the `docs/CODE-REVIEW-CHECKLIST.md:124-145` convention - recorded, not dropped, so a
reader can tell "considered" from "overlooked".

| Clause | Why no row |
|---|---|
| `:36-41` shebang half | **Met, 15/15**, but by accident: no artifact in the tree enforces it. A MET row needs an artifact and there is none. **A wired shellcheck becomes that artifact** (SC2148 et al.), which is a second reason to wire it |
| `:748-756` `shfmt` | No subject. `shfmt` is not installed, not in any config, and the scripts are not formatted to `-i 4`. Adopting it is a reformat of 3374 lines and a separate decision from shellcheck; I am not smuggling it in |
| `:758-774` pre-commit block | Half-subject. `.pre-commit-config.yaml` **exists** (2 hooks: committed-file-types, detect-secrets) but carries neither shellcheck nor shfmt. Folded into BASH-2 rather than given its own row - it is the same obligation's delivery mechanism, not a separate obligation |
| `:780-791` anti-pattern table | **Compliant, verified, no row.** `function name {` -> 0. Unquoted `$@` -> 0. Legacy backticks -> 4 hits, **all inside comments** as markdown quoting, none command substitution. Nothing to anchor and nothing to fix |
| `:320-338` sysexits constants | No subject. The harnesses use bare 0/1/3. Cosmetic, and `EXIT_CONFIGURATION_REFUSED = 78` in `__main__.py` already follows the convention where it matters |
| `:300-318` `trap cleanup EXIT` | **Deliberately not filed as a finding**, and I want to be explicit that I considered it. The harnesses restore inline after each mutation rather than via an EXIT trap. A trap would be more robust against an interrupt mid-mutation. But changing teardown in the scripts whose teardown correctness everything else depends on is not a standards-coverage task, and it interacts with ADR-0023. Left for whoever does the `\|\| rc=$?` conversion |

### One clause I could not resolve, and am not going to pretend I did

`bash.md:799`, under **"When NOT to Use Bash"**:

> - **>100 lines of logic** — rewrite in Python or Go

**14 of the 15 scripts exceed 100 lines.** Measured:

```
 54  check-suite-floor.sh          <- the only one under
100  check-suite-floor-amputation.sh
...
354  check-u1-boot-controls.sh
469  check-u1-boot-amputation.sh
```

I am reporting this rather than filing it, for two reasons. It sits under a heading the document
itself frames as guidance (`:807` calls the neighbouring line a "**Guideline**"), not under a MUST.
And the remedy - rewriting 3374 lines of working, controlled harness in Python - is enormously larger
than any defect it would fix. **But I am not going to record it as compliant either.** It is a
`priority: required` document saying, in plain terms, that this code should not be bash. Somebody
with more standing than me should decide whether that is a real obligation here or a clause aimed at
a different kind of script. I have not created a task for it because I do not think I should be the
one framing the question.

---

## 4. Gates, by exit code, each on its own line

Run in `/tmp/bash-work` at branch head `c9669f4`:

```
python3 docs/reviews/check-obligations.py                    exit 0
    Mappings: 31 | anchors verified against their subject: 23 | recorded as absent: 8
    Every mapped anchor still contains its subject. OK.

python3 docs/reviews/check-obligations.py --controls         exit 0
    8/8 controls fired.
    negative control "artifact shifted by five lines (B49)":  tolerated
    post-run re-check of the real OBLIGATIONS.md: exit=0

python3 docs/reviews/check-clause-citations.py               exit 0
    Clause citations: 23 | unresolvable: 0

bash docs/reviews/probe-bash-namespace-amputation.sh         exit 0
    CONTROL FIRED

bash docs/reviews/probe-set-e-vs-harness.sh                  exit 0
    both arms as quoted in §2

shellcheck --severity=warning docs/reviews/probe-*.sh        exit 0
```

**My own two probes are shell, so the gate I am proposing would judge them.** They pass it. At
default severity they carry 2 findings - one `SC2016`, one `SC2001` - both below the specified
threshold and both in categories already present in `scripts/`. I checked rather than assumed:
proposing a gate and quietly exempting my own contribution from it would make the proposal
worthless.

Two defects in my own files, caught by that check and by the re-run, fixed before delivery:
`probe-set-e-vs-harness.sh` as first committed **had no strict-mode line at all** - a file arguing
about `set -euo pipefail` that carried no `set` line - and its header cited **ADR-0022**, the stale
number from the brief, copied before I renumbered.

**Row count verified against git, not against memory**: `29 -> 31` rows, `git diff --stat eb4d254`
shows `docs/OBLIGATIONS.md | 2 ++`. Exactly the two rows I added, no more.

**I did not run `pytest`.** Nothing I changed is importable by the suite: three docs, one probe pair,
and a regex in a script that CI does not run. Saying so rather than reporting a number I did not
produce.

---

## 5. What I am proposing but did NOT do, because another agent owns the file

`harness-gates` owns `scripts/*.sh` content and `ci.yml` this round. Everything below is a proposal.

**Step 1 - three one-line fixes** (`scripts/check-u0-test-controls.sh`,
`check-u5-jobs-amputation.sh`, `check-u5-jobs-controls.sh`), exactly as spelled out in §1. After
them, `shellcheck --severity=warning scripts/*.sh` exits **0**.

**Step 2 - wire it, in the pre-commit file that already exists**, using the standard's own block
(`bash.md:762-767`) at the rev it names:

```yaml
  - repo: https://github.com/koalaman/shellcheck-precommit
    rev: v0.10.0
    hooks:
      - id: shellcheck
        args: ['--severity=warning']
```

`.pre-commit-config.yaml` is not in `harness-gates`' territory and I could have added this
unilaterally. **I deliberately did not**, because wiring the hook without step 1 lands a gate that is
red on a clean tree - and that file already records, in its own comments at `:61-67`, that this
exact failure (D3) has happened here before on the secret gate. Landing it again in the commit that
cites the lesson would be poor.

**Order matters and it is one commit, not two.** Fixes and wiring together, so the hook is never
knowingly red - the pattern `f0c3764` used for B49b's W505.

**On CI as well as pre-commit:** `bash.md:741` gives a CI form. I would leave CI alone for now.
Task #22 (actionlint) is already queued against `ci.yml` and task #27 is restructuring how its steps
are written; adding a third change to that file this round invites the collision the dispatch warned
about. Pre-commit first, CI when `ci.yml` settles.

---

## 6. What I did NOT verify

Things I could not settle, not things I skipped.

- **Whether `-e` is safe at the other nine `=$?` sites.** Twelve exist. I read three in full
  (`check-u0-test-controls.sh:110`, `check-u1-boot-controls.sh:73-76`,
  `check-u15-gate-controls.sh:49`) and the probe generalises the *mechanism*, but I did not audit
  the remaining nine for what else `-e` would have caught in them. ADR-0023 says so in its own
  limits section rather than implying a full audit.
- **Whether the three fixes actually take shellcheck to 0 at `--severity=warning`.** I could not run
  the fixed files - I did not make the edits. The claim follows from the rule definitions and from
  the fact that no other warning exists, but it is a prediction, not a measurement. **Whoever makes
  the edits should re-run and quote the exit code**, not cite this report.
- **`ci.yml`'s shell.** `bash.md` is `applicable_to: ci-cd` and **every `run:` block in the workflow
  is shell that no strict-mode line governs at all**. That is a genuine and completely unmeasured
  gap - shellcheck over `scripts/*.sh` does not see one line of it. I did not open the file, because
  two agents are live in it. It probably deserves its own task once they land; I have not filed one
  because I have not measured it and would be filing a guess.
- **Whether the 8 ABSENT clause citations in task #31 actually resolve.** I identified that nothing
  checks them; I did not resolve them by hand. Turning that check on may land red, which is the
  finding, and I flagged the risk in the task rather than discovering it for someone mid-fix.
- **`shfmt`.** Not installed and not run. I know the scripts are not `-i 4` formatted from reading
  them, but I did not measure the diff size, so I cannot say how large adopting `:748-756` would be.
- **The `:799` >100-lines clause.** Measured (14 of 15 over), deliberately not adjudicated. See §3.

---

## 7. Housekeeping

- Branch `chore/bash-standard`, **5 commits** on `eb4d254`. **I did not push and did not merge.**
  (That count is derived by the command that wrote this line, not typed: it said "3" for about
  twenty minutes after it stopped being true.)
- Worktree `/tmp/bash-work` is removed immediately after this commit, and `git worktree list` is
  quoted in my report message to the team lead. It is asserted there rather than here, because a
  committed file cannot honestly describe a step that happens after the commit.
- **Task #31 filed** (the 8 ABSENT rows whose clause column nothing verifies). Task #24 marked
  `completed`.
- Delivered: ADR-0023 + index row, 2 obligation rows, 1 regex widening, 2 committed probes, this
  report. **No `scripts/*.sh` and no `ci.yml` were touched** - see §5.
