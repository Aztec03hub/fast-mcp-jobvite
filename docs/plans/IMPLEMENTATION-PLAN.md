# fast-mcp-jobvite - Implementation Plan

Status: **DRAFT 9, and the LAST draft of this review cycle** - see
[§10](#10-the-review-cycle-is-closed-at-round-7-and-what-replaces-it) for why it closes here and what
replaces it. Revised against `PLAN-REVIEW-R7.md` (0C / 1H / 1M / 5L); rounds 1-6 are answered in
drafts 3-8. **Which units are built is a volatile line, so derive it rather than trust it**:
`git log --oneline b53886e..HEAD` names them, and at `94330db` it names **U0, U15, U2 and U11** - it
named three of those four when this paragraph was first written, one working session earlier, which
is the whole reason it points at a command instead of a list. Round 7's High was the **eleventh**
collision; it bound **U5**, not U1, and it is
**closed in code at `1e67f9c`**.

**Every measurement this plan rests a decision on is a runnable probe, not a paragraph.**
`docs/reviews/check-plan-measurements.py` re-runs all four - each two-armed, treatment and control -
and exits non-zero when a plan claim stops reproducing. **Since `ff9461a` it runs in CI**, alongside
`check-obligations.py` and its `--controls` arm, in `ci.yml`'s `design-gates` job. Rounds 6 and 7
each re-ran some of these by hand and reproduced them, which is the right instinct and the wrong
mechanism: it does not survive the reviewer who does not think of it, and **there is no round 8.**
**Prose about a measurement decays into a claim about one.**
Written against `docs/DESIGN.md` at **revision 6**, frozen at `135c3ac` and **RE-FROZEN at `c15b138`**

> **THIS DOCUMENT HAS TWO REFERENCE FRAMES. THE CITATION'S FORM PREDICTS WHICH ONE, 130 TIMES OUT
> OF 131 - AND THE 131st IS IN THIS FILE.** Re-derive anything you rely on; the tendency is strong
> enough to plan by and not strong enough to trust.
>
> This paragraph has now been wrong three times, each time in the direction opposite the last. It
> said every citation resolves at `c15b138`; then that the FORM tells you which, with no measurement
> behind it; then that NOTHING tells you which, which was the same unmeasured mistake pointing the
> other way. The census below is the measurement that should have come first.
>
> **The frames are real.** Two citations 26 lines apart, each correct at its own blob and nonsense
> at the other:
>
> | citation | resolves at | text there | at the other blob |
> |---|---|---|---|
> | `:1220`, §1 table row 1 | **`135c3ac`** | `- the 200-with-401-body trap;` | a blank line at `c15b138` |
> | `DESIGN.md:1370-1371`, under that same table | **`c15b138`** | *"Every refusal-path test is paired with a positive control..."* | `]` at `135c3ac` |
>
> And they are not always paragraphs apart. **`:271-273` carries `DESIGN.md:1466-1472` and a bare
> `:1426` in ONE SENTENCE, in different frames**: `135c3ac:1426` is *"CI must run ..."*, and
> `c15b138:1426` is blank.
>
> ## The census
>
> **MEASURED AT `7e8adfa`, AND A DATED RECORD RATHER THAN A LIVE COUNT.** All 166 citations as this
> file stood at that blob, resolved at both `135c3ac` and `c15b138` by
> `docs/reviews/probe-218-frame-census.py`, which reports its own method and adjudicates by hand
> every citation its proxy could not place. **The blockquote you are reading has itself added
> citations since**, so the live commands below will return larger numbers than this table - that
> is the table being pinned, not the table being wrong:
>
> |  | resolves at `135c3ac` | at `c15b138` | identical at both | undecidable |
> |---|---|---|---|---|
> | **qualified** `DESIGN.md:NNNN` | **0** | 88 | 18 | 5 |
> | **bare** `:NNNN` | **42** | 3 | 1 | 9 |
>
> **ZERO of 111 qualified citations resolve at `135c3ac`**, at every threshold the probe sweeps and
> after hand-reading every doubtful row. That zero was checked for comparability before it was
> explained: the same code path, blob read and scoring function return 32 on the bare side, so the
> `135c3ac` arm demonstrably fires and the zero is not an artifact of construction.
>
> **THE ONE EXCEPTION IS A SINGLE CITATION, AND IT IS WHY THE RULE IS NOT A RULE.** The three bare
> `c15b138` hits are all `:300` - once at its site, twice where this blockquote quotes it. It lives
> in **the ADR-0012 discharge paragraph in §9's Wave C**, and its own sentence names its blob:
> *"`DESIGN.md:295` and `:300` at the frozen `c15b138`"*. Read a bare citation at `135c3ac` first;
> expect to be wrong about one of them.
>
> ## Reading a citation here, and what the numbers do not tell you
>
> **19 of the 166 are BYTE-IDENTICAL at both blobs.** For those, resolving at one blob proves
> nothing about the frame - roughly one citation in nine agrees with whichever blob you happen to
> open. That is why "re-derive" above means at BOTH blobs, not at one.
>
> **THE TWO COUNTS ARE FLOORS, NOT EXACT.** `:2261` writes `DESIGN.md:295,300`, whose `,300` half
> carries neither a colon-prefixed form nor a filename and so matches neither selector. Other
> shapes may exist; nobody has swept for them.
>
>     grep -o 'DESIGN\.md:[0-9]' docs/plans/IMPLEMENTATION-PLAN.md | wc -l    # the qualified population
>     grep -o '`:[0-9]'          docs/plans/IMPLEMENTATION-PLAN.md | wc -l    # the bare population
>
> **Both commands are `grep -o | wc -l` and both name this file, deliberately.** `grep -c` counts
> LINES, not citations, because at least one line here carries four bare citations at once; and
> `#111`'s repo-wide `grep -rno` returns thousands, of which 111 is this file's share. Earlier
> revisions of this paragraph published both of those errors - a mis-counting instrument inside the
> document about mis-counting instruments.
>
> ## Why no citation is repointed
>
> **`#111` IS APPLIED HERE, NOT OVERRULED.** It ruled `docs/plans` a RECORD: all sixteen units
> U0-U15 are built, nothing executes this document any more, and its citations stand as written,
> the same standing as a worklog. **Not one is moved.** What changes is the document's DECLARATION
> about them, a live claim of fact rather than a record of a past decision - and `#111`'s own reason
> is that a wrong sha *"would turn a document that is honestly out of date into one that is
> confidently wrong"*. A declaration naming one frame for a two-frame document already is that
> failure, read from the other end.
>
> Repointing the bare citations to `c15b138` was the other candidate remedy and is **REFUSED**: it
> is the move-the-orphan-to-match shape ADR-0017 rejected, and it would be correct only until
> `DESIGN.md` moved again. It has moved five times since `c15b138`, and the shas are written out
> because an endpoint like `HEAD` is reader-relative and goes stale the same way a count does:
>
>     git log --oneline c15b138..d1f1a52 -- docs/DESIGN.md
>     8a9d63c  aca9397  86ab20e  e3b5c97  d1f1a52
>
> If this plan ever becomes live again - a new unit is planned - the remedy is to replace the
> numbers with subject phrases, as `OBLIGATIONS.md` did at `afaf226` and `ci.yml` did at `b4ddc57`,
> not to repoint them.
>
> **The frames above concern citations into `DESIGN.md`.** This file also cites `tech-stack.md`,
> `STANDARDS.md` and `CREDENTIAL-CHECKLIST.md` in the bare form; neither blob has anything to say
> about those.
where the eight-ADR batch landed - no open Critical,
High or Medium findings and an empty must-mitigate table (`DESIGN.md:1846`). **The design being
frozen changes what this plan is:** from here only a numbered ADR may change `DESIGN.md`, so a
finding against the design is no longer an edit request - it is an ADR, and every open item below
is written that way.

**What draft 9 changed.** Round 7 returned **0C / 1H / 1M / 5L** and draft 9 applies all seven.

- **The HIGH was the eleventh collision, collision 10's twin, and it is CLOSED IN CODE at
  `1e67f9c`.** The collection guard ran collection **through the marker selector**, so a test file
  whose tests were ALL `credentialed` or all `network` read as an orphan and turned the suite red -
  and **U5 is scheduled to create exactly that file.** The guard's own docstring claimed the
  opposite and had never been tested, because `tests/credentialed/` held only a README. §4 had told
  units the trigger was a file *"outside `testpaths`"*; `tests/credentialed/` is **inside** it.
  **This was a defect in shipped code, not a gap in the plan** - `tests/` is U0's, and it was fixed
  as a U0 follow-up: the selector is gone, the docstring is rewritten in place, a regression test
  manufactures the file shape rather than waiting for U5, and **probe M4 has flipped from `OPEN` to
  `PASS`.** U5 now lands its arm into a guard that no longer traps it; what remains binding on U5 is
  the rule in §4's shared-file table that the guard must not be narrowed to buy a green.
- **The MEDIUM was a control that was not wired, and it is now wired.**
  `docs/reviews/check-obligations.py` landed with no CI step, no hook, and no ownership row, while
  its anchors sit in the files U1, U5, U11, U13 and U15 all edit. **This repository had built the
  same defect twice** - it is the file-type gate's `--all` mode with no CI step, one artifact
  later. **`ff9461a` wired it, its `--controls` arm, and `check-plan-measurements.py` into
  `ci.yml`'s `design-gates` job**, and wiring it turned it red immediately: adding steps to
  `ci.yml` moved five of the anchors, three of which point into `ci.yml` itself. **That red is the
  finding's real content** - a hand-maintained `file:line` map cannot survive without the gate that
  reads it.
- **Two Lows are draft 8's own corrections recreating the defect they corrected.** The
  count-behind-its-own-table error was fixed in two places and recreated one section away; and the
  verification command draft 8 offered to a doubting reader named `.github/workflows/ci.yml` rather
  than the directory - **the same name-one-file defect that had just let `mirror.yml` slip an entire
  C-1 sweep, appearing inside the remedy for it.**

**What draft 8 changed.** Round 6 returned **0C / 1H / 2M / 5L** and draft 8 applied all eight,
**plus five numeric errors draft 7 introduced and its own author found afterwards** (recorded in
`docs/worklogs/PLAN-DRAFT7-SELF-AUDIT.md`). Round 6 independently re-ran both pytest measurements
draft 7's §4 decision rests on, and both reproduce - so that decision stands on evidence a second
hand has checked, which is what a measurement reported by the author of the decision it justifies
requires.

- **The HIGH is the tenth collision, and it is unlike the nine before it.** `tests/test_manifest.py`
  asserts **exact set-equality** over the whole runtime dependency list; `loguru`, `tenacity`,
  `defusedxml` and `circuitbreaker` are absent from `uv.lock` entirely and this plan schedules all
  four, plus `pydantic-settings` in U1. Every other collision is two units wanting one file, fixed
  by partitioning it. **Here the collision is between each unit and an assertion**, and `uv.lock`
  regenerates whole, so partitioning does not exist. **It bites U1, the next unit to be dispatched.**
- **Two Mediums, one of which is draft 7 asserting the opposite of the tree.** U15's carried HIGH -
  `pre-commit` undeclared, so the gates did not exist on a fresh clone - **was closed at `80a7fd0`,
  one commit past the basis draft 7 measured at.** Draft 7 re-checked round 5's findings against the
  moved tree and did not re-check the paragraph it was itself writing. Two residues survive and are
  now the live items. The other Medium: **two** places gate on **"until ADR-0012 exists"** when it
  exists and is `Proposed` - **an agent discharges that gate with `ls`**, and builds the module the
  gate was written to prevent. Every ADR gate now reads **Accepted**.
- **Three of the five Lows were inherited unchanged from draft 6 and had survived every round.** The
  cross-reference carrying the four-lane Wave C claim pointed at the wrong collision **and in the
  wrong direction**; "eight collisions" sat above a nine-item list; and the footer still read
  *"Draft 6 … R4"*. **A reader who already believes a claim does not follow its pointer**, which is
  how a load-bearing citation stays wrong through four reviews.

**What draft 7 changed, and the one thing that made it different from every earlier draft.**
Draft 6's author was killed mid-session; only the reviewer was re-dispatched, so `PLAN-REVIEW-R5.md`
landed committed and **unapplied**, and **five** commits went in on top of it. **A finding written
against a tree that has since moved is not a finding until it is re-checked against the tree that
exists**, and re-checking round 5 changed the disposition of two of its six items:

- **H1 is CLOSED BY BUILD, not by argument.** The collection guard the review said existed nowhere is
  `tests/test_collection_guard.py`, landed at `35de193` as B58, in the thorough variant the review
  asked for. It is recorded below as done and named in U0's CI list. **The review was right and is
  now spent** - that is a different outcome from "the review was stale", and the plan says which.
- **M3 got stronger, not weaker.** The review called U15 a *possible* future writer of `ci.yml`
  because a `--all` mode existed with no CI step. U15 has since landed **three** steps in that file
  (`.github/workflows/ci.yml`, the *"Committed file types, whole tree"*, *"U15 gate controls"* and
  *"Secret scan hook runs clean"* steps). The hypothetical is now a fact in the tree, and U15 is on
  the `ci.yml` editor list below.

The other four applied as written: **H2** gives `tests/conftest.py` a shared-file rule and a
mechanism (**and this draft picks between the review's two options, on a measurement, rather than
leaving the choice open**); **M1** rewrites the per-module coverage floors around
`COMPLIANCE-SPEC.md` §2.3's existing ruling; **M2** adds `C7-I2`, which appeared nowhere in 1,543
lines while the frozen design puts it on the mitigate-before-production-release list; **L1** gives
every unit a `changelog.d` obligation.

**And round 5's headline recommendation has already been executed, which retires §8's largest
declared blind spot.** The review's judgement section said the unread `COMPLIANCE-SPEC.md` was where
the unlooked-at defects lived and asked for one pass by one agent with a diff. That pass ran:
`docs/reviews/COMPLIANCE-SPEC-PASS.md`, 78 obligations, **7 MISSING / 2 CONTRADICTED / 5 MET BY
ACCIDENT**. It was not a green, which is the strongest available confirmation that the review's
structural claim was right. **All nine of its defects are now disposed of**, across four commits and
not two - F-1/F-2/F-3/F-6/F-7 in `ff0bbdf`, F-4 and C-2 in `2d2e1a3`, F-5 in `35de193`, and C-1 in
`5519032`, which fixed five of the six places and **missed `mirror.yml:28`** (§4). *Draft 7 said "six
of its nine ... (`2d2e1a3`, `ff0bbdf`)", undercounting by three and omitting two commits.* **Two
further items land on this plan and are NOT among those nine** - the README's Contributing section
(**F-6**, one of the nine, whose plan-side half U13 owns) and the unowned changelog obligation
(**A-5**, which is a *MET BY ACCIDENT* row and not a defect at all). Both are folded into U13 and §4
below. *Draft 8 fixed this sentence's arithmetic and left its population wrong, calling A-5 one of
"the two" immediately after "all nine of its defects" - **a correction that repaired the number and
not the set it counted**, which is the same error one level down.* **§8's "I did not read `COMPLIANCE-SPEC.md`"
bullet is rewritten rather than left standing**, because a declared limitation that has since been
discharged is a false statement about the plan's own coverage.

**What draft 6 changed.** Round 4 verified the two classes that dominated rounds 2 and 3 as closed -
all 25 case anchors land on their own case, and **every unit has an arm that fails if the unit
builds nothing**, so there was no verification-shape finding at all. It also confirmed the U5/U6
correction draft 5 made against round 3's suggested fix.

**What it found instead came from the build, not from reading.** U0 shipped, and **two of the three
Highs were surfaces the ownership model could not express**: `models/` is one directory with three
writers, two of whom start at the same instant; and `.github/workflows/ci.yml` and `pyproject.toml`
are written by four units between them and appeared in **no ownership table at all** - while draft 5
called two units that must both edit them *"genuinely disjoint"*. **Enabling a commented CI step is
a write.** Collisions 7 and 8 are named, and §4 now carries a second kind of row for shared files.

**The third High was a decision that existed only in a message.** U0 declined the two commit-time
gates and asked for a ruling; the ruling was given and never written down, so the plan still listed
them under a unit that had declined them while `DESIGN.md:1811` names them as a **Critical** row's
mitigation. They are now **U15**.

The Mediums: U5 had no row in any wave table - the "U8 had no wave" defect one unit over, and the
*cause* of the `models/` collision; `DESIGN.md:413` was doing two jobs and was wrong at one of them;
the lane sentence named the wrong pair for the right count, on its fourth revision; the licence gate
landed as a deny-list while the plan still described an allow-list; and no rule covered **reading**
a file another unit is rewriting, which U5 and U6 do concurrently by design.

**Every `DESIGN.md:<line>` citation resolves against the `c15b138` git object** - the frozen text,
read with `git show` rather than off a working tree that four other agents were moving today.
**§11's threat rows are repointed by ROW ID, not by text** - matching `C3-I1` to the line that
begins that row - because text-identity matching is what let six §11 anchors go stale through two
drafts: when a cited line's text changes, the match fails, the repoint silently returns the original
number, and nothing reports it. Everything else is repointed by text identity. **The §1 table's
anchors are not repointed at all**: they are re-extracted from the frozen document, because
repointing a table that is itself the source of truth reintroduces the defect it exists to prevent.
A frozen design means these cites should now hold still.

**A limit on that check, stated because two drafts running have oversold it.** Draft 2 claimed all
84 cites *"land on non-blank content"*, and draft 3 repeated the check. Non-blankness is a much
weaker guarantee than it reads: it **cannot catch a cite that lands on the wrong paragraph**, and
across the two drafts eight did - two in draft 2 by never being right, six in draft 3 by a repoint
that failed silently. **Draft 4's check is subject-level**: every threat-row cite is verified to
land on that row's own line, and every `§8 #n` on that case's own text - `MockTransport` and the
`utils/redaction.py` coverage note were both off by seven lines at `9d65cc0` itself, so neither was
drift. Both are corrected.

**The strongest evidence that the non-blankness check is structurally too weak is what happened to
me while fixing it.** Folding a toolchain note into U0, I wrote a `DESIGN.md` line number from
memory of an earlier grep. It landed on a **non-blank but wrong line** - and it was the identical
defect I had finished correcting less than an hour earlier, in a paragraph I had just written
warning about it. The non-blankness check passed it. The subject check caught it. **The author who
had documented the weakness still failed it**, which is a better argument for subject-verification
than any assertion either a reviewer or I could make: a check that a motivated, freshly-warned
reader still slips past is not a check, it is a habit that looks like one.

**What was actually swept for draft 5, stated as a scope rather than as a claim of completeness.**
Three sets were checked subject by subject: every `§8 #n` against its case's own text, every
threat-row cite against that row's own line, and **every cite adjacent to a verbatim quotation** -
located by `grep -n` on the quoted fragment, which is the durable form, since a cite that quotes the
design can always be checked against what it quotes. Draft 4 claimed the first two and left the rest
on text identity; that gap is what round 3 found. Cites into §4-§7 prose that quote nothing still
carry the weaker text-identity guarantee, and that is now the whole of the residue rather than an
unbounded remainder.

**The design is authority.** Nothing here changes it. Where I believe the design is wrong or
incomplete, it is recorded in [§9 Questions for the design](#9-questions-for-the-design) and
nowhere else - there are no silent workarounds in this plan, and every open item that blocks a
work unit is named at the unit that it blocks.

**Scope of this document.** It is an ordered set of work units with dependencies and verification.
It contains no code. It does not estimate effort or duration.

---

## 0. Two facts about the repository, established before planning

**Both facts below were true when this plan was written and BOTH HAVE SINCE BEEN CHANGED BY U0 AND
U15, deliberately - they are the premises the ordering was derived from, not a description of the
tree.** They are kept in the past tense rather than deleted, because a reader who cannot see what
this plan assumed cannot tell which parts of the order were forced and which were chosen. The
current tree carries `src/fast_mcp_jobvite/`, a populated `tests/` and a real `ci.yml`; where this
section and the tree disagree, the tree is simply later.

**`src/` and `tests/` were empty. Zero files.** Everything below was greenfield.

**There was no CI, and the design says so once, plainly.** `.github/workflows/` contained exactly
one file, `mirror.yml`, which pushes to the mirror remote. Draft 1 reported this against a design
that used the present tense; `DESIGN.md:1466-1472` now states that **every "CI runs" sentence in
that document is a specification of what the pipeline must do, not a report of what it does**, and
that standing the pipeline up is the first unit of implementation. `:1426` reads *"CI **must** run"*
accordingly.

I ran all three gates by hand at **HEAD (`8814d69`)**:

```
check-coupling.py     exit 0   60 STRIDE rows, 17 Critical/High, 23 naming a §8 case
check-coupling-controls.py     exit 0   34/34 controls fired; post-run re-check exit=0
check-coupling-sweep.py        exit 0   0 escapes are holes
```

**The controls harness has now reported 21, 32 and 34 to three different readers** - its docstring
still narrates 21, draft 2 measured 32 at `9d65cc0`, and it reports 34 at HEAD after `cc94459` added
two. That is the point, not a footnote: **the count is a moving number, so nothing in this plan
asserts a literal one.** U0's CI assertion is the exit code and the *all fired* property. A plan
that hard-coded 34 would turn the harness growing into a red build, which is the same stale-count
defect one level up.

**Standing CI up was U0's first act**, before any other work in that unit, and it has happened. From
that point "the gates keep passing" is a machine constraint rather than a habit. All three run there:
the gate
alone is a checker that has only ever passed, which its own docstring names as the failure it
exists to avoid, and the sweep is what proves it can fail without choosing its own subject.

---

## 1. The count that governs the test plan

§8's required-cases list holds **25 bullets**. It was derived mechanically - extracting every
top-level bullet between the *"Required cases"* header and the *"Transport substitution uses"*
paragraph - rather than by incrementing draft 1's 24, because a hand-carried count is the defect
this project has spent the day repairing. **This sentence used to name a line span
against a third blob, and that span is DELETED because it resolved nowhere**: it held 0 top-level
bullets at the blob it named, 12 at `135c3ac` and 13 at `c15b138`, none of them 25. The digits are
not repeated here - quoting a deleted citation leaves it in the file and in every selector that
counts citations, which is the finding rebuilding itself inside its own remedy; `git log -p` has
them if anyone needs them.

The 25 is NOT deleted with the span, because it is checkable and it checks out: the table below
spans row 1 to row 25, and that same span at `135c3ac` holds exactly 25 top-level bullets. The new
member is **#18**, the SIGTERM teardown case Q2 added; everything below it shifted by one.

Several cases are multi-arm and are **not satisfiable by a single arm**, which the list says in its
own text:

| # | §8 line | Case | Arms it explicitly requires |
|---|---|---|---|
| 1 | `:1220` | the 200-with-401-body trap | - |
| 2 | `:1221` | a secret never reaching a log record, including the `jobFeed` URL | - |
| 3 | `:1222` | `.gitignore` covers the credential patterns, `.env.example` carries no real value | asserted against committed files |
| 4 | `:1226` | the audit event is emitted and carries its mandated fields | **positive on purpose**; paired with #5 |
| 5 | `:1232` | candidate PII never reaching a log or audit record | asserted **against the event #4 proves exists** |
| 6 | `:1236` | EEO fields never appearing in any tool result | asserted against the output models |
| 7 | `:1238` | an argument-schema violation failing closed | - |
| 8 | `:1240` | control character / bidi override rejected before dispatch | **+ positive control**: an ordinary name passes |
| 9 | `:1244` | argument payload exceeding a structural limit rejected | **four arms**: depth>5, list>1000, dict keys>100, body>1 MiB |
| 10 | `:1246` | off-loopback bind without TLS refuses to start | exits naming the reason, not a warning |
| 11 | `:1250` | manifest pins `mcp`; frozen resolve has no lock drift | `uv lock --check` + `==` pin present |
| 12 | `:1255` | an undeclared pytest marker fails collection | **+ positive control**: the declared marker still selects |
| 13 | `:1260` | retry and breaker lines carry the invocation's own `request_id` | **concurrent arm is the case**; single-call is insufficient. Also asserts no URL in a retry line |
| 14 | `:1266` | read-only-key requirement present in `CREDENTIAL-CHECKLIST.md` and in README | README arm **gated on file presence, never skipped** |
| 15 | `:1273` | an expired advisory-ignore entry fails the audit gate | **+ positive control**: an unexpired entry is honoured |
| 16 | `:1277` | `request_id` present on every result, success and error | **four arms**: successful read, successful write, audit-failure warning branch, error. Each **on the wire result**, not on `ToolResult` |
| 17 | `:1284` | trace context recorded when supplied, absent when not | **two arms, both required** |
| 18 | `:1289` | **lifespan teardown runs on SIGTERM, on both transports** | asserts **the teardown side effect**, not the exit code - a process that dies uncleanly can still exit 0 |
| 19 | `:1296` | untrusted-content fencing, including content closing its own fence | - |
| 20 | `:1297` | unknown non-string field dropped, not stringified | - |
| 21 | `:1298` | `create_candidate` not retrying on timeout | - |
| 22 | `:1299` | approval: deny, accept-carrying-false, no-handler, second leg consumes `input_responses` | **four arms** |
| 23 | `:1301` | a 4xx not tripping the circuit breaker | - |
| 24 | `:1302` | the `eId`/`EId` casing asymmetry pinned | - |
| 25 | `:1303` | approval on **both eras** | asserts **row count unchanged**, not error shape |

Plus the blanket rule at `DESIGN.md:1370-1371`: **every refusal-path test is paired with a positive
control showing the happy path still succeeds.** That applies to #1, #7, #8, #9, #10, #12, #15,
#21, #22, #23 and #25, not only where the bullet says so.

**And every unit carries BOTH of U0's harnesses, because specifying a positive control is not the
evidence U0 produced.** U0 ran two: **mutation** - break one thing, require the *named* test to go
red; eleven controls, all fired - and **amputation** - rebuild the tree with the subject removed and
require the assertion to fail. **Only the amputation found the one genuinely vacuous assertion** in
a suite that had already passed mutation: a test asserting no value in `.env.example` looks like a
credential passes over an empty file. **Reading a "Verified by" list tells you which arms exist;
only amputation tells you which are hollow** - and every verification-shape finding across this
plan's four review rounds was found by reading, which is the weaker instrument. Both harnesses are a
requirement of every unit below, not a suggestion, and neither substitutes for the other.

**Every `§8 #n` reference in §2 resolves against this table, and draft 1's numbering appears nowhere
below.** Both the table and the references were regenerated from `DESIGN.md` at HEAD and checked
subject by subject, because draft 2 renumbered the table and not the units - which is C1, and which
made `#18` mean SIGTERM in U1 and fencing in U8.

**Case #18 replaces draft 1's out-of-band note, and the assertion changed shape.** Draft 1 flagged
the §7.4 shutdown requirement as a required test living outside §8. It is now bullet #18. But it
does not assert what draft 1 scheduled: §7.4's prose asks for the teardown marker **and** that the
process exited, while `:1289-1295` asserts **the teardown side effect and deliberately not the exit
code**, because a process that dies uncleanly can still exit 0. **U1 follows the case, not the older
prose and not draft 1.** One residual on the machine-gate half of Q2 is measured at
[Q2](#q2---answered-and-the-residual-has-since-landed).

### Fixture tiers

`DESIGN.md:1251-1256`. Three tiers, and the split is load-bearing:

- **Recorded** - byte-exact captures of **real Jobvite error transport** (`DESIGN.md:1252`).
  **Five exist**, and the list is exhaustive: `error_auth_401.json`, `error_auth_200_body401.json`,
  `error_route_404.json`, `error_task_400.html`, `error_v1_auth_401.txt`. **Assert verbatim.**

  **Draft 2 put seven files in this tier and gave three different counts in one bullet.** The two
  malformed bodies are **not captures**: `malformed_not_json.txt` is the single line
  `this is not JSON at all`, and `malformed_truncated.json` is a truncated fragment carrying the
  placeholder id `TESTCND1` in the same style as every synthetic fixture. Putting invented files in
  the ground-truth tier, under an instruction to assert them byte-exact, is the precise confusion
  the three-tier split exists to prevent - which this plan says itself in §5. They are synthetic.
- **Structural** - the one genuine `200` (`JOBVITE-API.md:393-399`). **Its body cannot ship**, so
  there is no fixture file and there must never be one. This tier is a set of *shape assertions*
  written from the recorded description: the envelope is
  `{"candidates":[...],"total":<int>,"status":{"code":200,"messages":[]}}`, a success body **does**
  carry a `status` block, `total` is the full result-set size and not the page size, and `start=0`
  is accepted and returns records.
- **Synthetic** - `candidate_list_success.json`, `candidate_list_empty.json`,
  `candidate_create_success.json`, `job_list_success.json`, `job_list_empty.json`,
  `jobfeed_success.json`, `jobfeed_empty.json`, `candidate_list_injection.json`, **plus
  `malformed_not_json.txt` and `malformed_truncated.json`** - deliberately invalid bodies, invented,
  and belonging to this tier however they are asserted. **Hypotheses in JSON.**

**The sentence at `DESIGN.md:1258-1259` goes in the test module's own docstring, verbatim in
substance:** a suite passing only against synthetic fixtures proves the client is self-consistent,
not that it speaks Jobvite.

**Sequencing consequence that a naive plan gets backwards:** the structural assertions must be
written **before** the candidate output models (U8), or the models will encode the shape of
fixtures we invented rather than the one success envelope anyone has actually observed. This is the
single clearest place the credential-free constraint reorders the work.

### Zero skips

`DESIGN.md:1229-1249`. CI has zero skips; a skip is a failure. Credential-dependent tests are
excluded **by selection** through a declared marker under `--strict-markers`, and **the excluded
suite is still collected** (`--collect-only`, failing on a collection error). All three properties
land in U0, because every later unit that adds a credentialed arm depends on them existing.

**There are TWO selection markers, not one, and every later unit needs to know the second exists.**
U0 landed a **`network`** marker beside the credential-dependent one, and CI runs the network arm as
its own step. The reason is §8 #11's negative arm: proving the `fastmcp-slim` pin is load-bearing
requires a **real resolve**, while `DESIGN.md:1229` requires the default suite to run with **no
network**. **A unit that adds a network-touching arm without the marker puts a live resolve in the
default offline suite**, where it fails for the wrong reason or passes by accident depending on the
runner. Draft 5 described a single credentialed marker; this paragraph is rewritten rather than
appended to, because two contradictory statements about the marker set are worse than one stale one.

---

## 2. Work units, in order

Each unit states what it builds, the governing design section, what it depends on, and **how it is
verified**. No unit is verified by "it compiles".

---

### U0 - Repository skeleton, pinned manifest, test selection, CI

**BUILT AND MERGED** (`b53886e`), with `docs/worklogs/U0-REPORT.md` as its record. Its scheduled
assertions were confirmed correct in round 2, its resolve has been executed, and round 5 checked
this section against the shipped tree and found it agreeing. **Three later commits amended what U0
landed** and are described at the end of this section, because a section that describes only the
unit's own commit is stale the moment anyone fixes a defect in it.

**If the U0 agent's report contradicts anything in THIS U0 SECTION, the report wins** - a unit that
has been built beats a unit that has been described, and this section is corrected from the build.
**This precedence is bounded to this section and never reaches `docs/DESIGN.md`**, which is frozen:
a build that contradicts the design is an ADR, not a correction.

*Draft 4's version of this said only "anything specified below", which round 3 named as the single
sentence most likely to be misread by an agent working alone - "below" bounded to this section is
sensible, "below in this plan" hands one agent precedence over twelve hundred lines, and it had no
floor at all while every other deviation in this document routes through an ADR.*

**Its first act was standing up CI**, because nothing ran there before it (`DESIGN.md:1466-1472`)
and every gate below was hand-run. **That is now done**: `.github/workflows/ci.yml` exists and every
gate in this plan is a machine constraint rather than a habit. The reason it was first is the reason
it stays first for anyone rebuilding this order - until the workflow exists, no unit's verification
means anything durable, it means someone ran something once.

**Builds.** `pyproject.toml` with the verbatim three-pin block and `prerelease = "explicit"`
(`DESIGN.md:1409-1418`); `uv.lock` committed; `[tool.pytest.ini_options]` with
`addopts` carrying `--strict-markers`, the declared `markers` list including the
credential-dependent marker, `asyncio_mode = "auto"`, and coverage `branch = true`
(`DESIGN.md:1234-1235`); **the 80% overall coverage floor**; `.github/workflows/ci.yml`. CI's
coverage step stays off until U1 because `src/` holds only `__init__.py` at U0.

**The per-module coverage floors are enforced in REVIEW, not in configuration, and no unit writes a
coverage key.** `fail_under = 80` is the only mechanically enforced number. **ADR-0010's per-module
floors (85% `tools/`, 90% the client, 95% `utils/`, 95 line / 90 branch on critical paths) are a
reviewer's checklist item**, because `COMPLIANCE-SPEC.md:292-295` already ruled on the mechanism and
this plan is not entitled to re-open it: *"`fail_under = 80` is the only threshold that is
mechanically enforceable in one number; **[REC]** enforce the per-module targets in review (§5
checklist) rather than inventing a bespoke coverage plugin. Adding per-module gates is possible via
`coverage`'s `[tool.coverage.paths]` only awkwardly - not worth the machinery."* So: **no unit adds a
coverage key to `pyproject.toml`**; each unit's reviewer checks that unit's module against ADR-0010's
row, and **each unit reports its measured coverage in its worklog** so the check has a number to read.

*Draft 6 said the floors "land with the units that create those modules", which named no owner and
no mechanism, and `pyproject.toml`'s own comment says the same thing in the same words. Neither is a
build instruction: the only home configured today is `pyproject.toml`, a file §4 closes over
`{U0, U11, U1, U13}` while U5 ∥ U6 and U8 ∥ U12 run concurrently - so an agent acting on the old
sentence would have written into an unowned shared file, and an agent not acting on it would have
dropped the obligation. **`pyproject.toml`'s comment is U0's file and is left for a U0 follow-up to
correct**; this plan does not edit it, and the two now disagree until it does.*

CI runs, at minimum: `uv sync --frozen`; lint; format; types; the default suite;
**the collection-guard meta-test** (`backend/testing.md:138-141`, `devops/quality-gates.md:76-81`
API-03, `COMPLIANCE-SPEC.md:297-305` §2.4 - see the paragraph below, it is BUILT);
`--collect-only` against the credentialed suite; the **`network`-marked arms as their own step**;
**the `design-gates` job, which since `ff9461a` runs every document gate this project owns** -
`check-coupling.py docs/DESIGN.md`, `check-coupling-controls.py`, `check-coupling-sweep.py`,
**`check-obligations.py`, `check-obligations.py --controls` and `check-plan-measurements.py`**,
each asserting a non-empty population as well as an exit code, and the controls steps asserting
`fired == total` rather than a literal count so that a harness which grows does not red the build;
`pip-audit` behind
`scripts/check_advisories.py` (U11); CodeQL; TruffleHog with full history depth; SBOM in both
formats from the **frozen** resolve; **a link checker over `**/*.md`** and **a semantic PR-title
check** (its own workflow, `.github/workflows/pr-title.yml`); `pip-licenses` **deny-list on the standard's flag-list, with the allow-list conversion owed to ADR-0015** (U0-REPORT D3: `pip-licenses` reports fifteen spellings for six licences, so `--allow-only` on
the standard's five SPDX ids is **red on its first run against a clean tree** - the same
trains-everyone-to-ignore-it failure this plan warns about for `pip-audit`); `fastmcp inspect` emitted and
diffed between builds. **Every trigger above also fires on a WEEKLY `cron: '0 0 * * 0'` sweep**, because
every other trigger fires on a change: without it CodeQL, TruffleHog and the licence gate only ever
see the tree on the day someone pushes, and an advisory published against the pinned beta stack after
the last merge is invisible until the next one. **The two commit-time gates are NOT U0's** - U0 declined them and the ruling
is now written down: they are **U15** (`DESIGN.md:1627-1637`), for the reasons that unit states.

**Inherited limit, carried not resolved: the capability-drift diff.** `DESIGN.md:64-68` names
exactly **two** mechanisms in the whole design that *"sit among executed results and borrow their
credibility"* - the circuit breaker (U7) and the `fastmcp inspect` capability-drift diff, which
lands here. §10 carries the `UNVERIFIED:` marker at its point of use, it is a Residual Risk, and
C9-T1 is one of the seventeen Critical/High rows. **Standing it up in CI does not execute it:** a
diff that has never seen a real capability change has only ever compared a build to itself. Its
first genuine evidence is a dependency bump that actually moves the manifest - the `ResponseLimiting`
regression is the case it is modelled on, and nobody has replayed that bump against it. Until then
it is **scheduled, not verified**, and this plan does not let landing it in a workflow read as
having tested it. §6 lists it beside the breaker so the pair the design names stays a pair here.

**One ordering note, the same shape as the `pyproject.toml` one in §4.** The `pip-audit` step above
invokes `scripts/check_advisories.py`, which **U11 builds** - and U11 depends on U0. Either U0 lands
the step commented out with a `U11` reference and U11 enables it, or U0 lands a bare `pip-audit`
that U11 replaces with the wrapper. Landing the wrapper call against a file that does not exist
makes CI red from its first run, which trains everyone to ignore the thing this unit exists to make
authoritative.

**One line that is load-bearing and unstated until now: tests read the recorded fixtures from
`docs/research/fixtures/` by path, and they are NOT copied under `tests/`.** U4 asserts five of them
byte-exact, so the path is part of the contract - an agent that copies rather than references
creates a second copy of a ground truth that can drift from the first silently, which is the one
failure mode a byte-exact assertion cannot detect.

**Depends on.** Nothing.

**Verified by.** §8 cases **#11**, **#12** and **#3** - all three are runnable today with no `src/`
at all, and all three fail if their defence is removed:

- #11: assert `mcp` present with an `==` pin in `pyproject.toml`, and `uv lock --check` exits 0
  without amending `uv.lock`. **Plus the negative arm the executed resolve earned:** a manifest with
  the `fastmcp-slim` line removed **fails to resolve**. That is the control proving the pin is
  load-bearing rather than decorative, and without it nothing stops a future tidy-up deleting a line
  whose only justification is a comment.
- #12: invoke pytest against a file marked with a name absent from `markers`, require non-zero exit;
  positive control - the declared marker still selects its tests.
- #3: assert against the committed `.gitignore` (currently covers `.env`, `.env.*`, `*.key`,
  `*.pem`, `secrets/`), and that **every secret-class variable in `.env.example` carries an empty
  value** - the six that hold credential material: `JOBVITE_API_KEY`, `JOBVITE_API_SECRET`,
  `JOBVITE_FEED_KEY`, `JOBVITE_FEED_SECRET`, `JOBVITE_COMPANY_ID` and `JOBVITE_HTTP_TOKENS`.
  **Non-secret defaults may and do carry a value**, and the test must not forbid it.

  **Draft 2 said "every value is empty", which is false against the committed tree and dangerous.**
  **Seven** of the fifteen variables carry a value, and two of them - `JOBVITE_MAX_RESULTS=50` and
  `JOBVITE_OUTBOUND_RATE_LIMIT=6` - are the answer to Q1. Eight are empty, and **only six of those
  eight are secret-class**: `JOBVITE_TOOLS` and `JOBVITE_PAGINATION_START_BASE` are empty
  non-secrets, so **an assertion keyed on emptiness rather than on secret-class would admit them
  wrongly**, passing for the wrong reason. Draft 3 said nine - a wrong number inside the correction
  of a wrong number - so this one is counted off the committed file rather than carried. The cheapest way to make draft 2's
  assertion pass is to empty them, which un-answers Q1 and re-blocks U1, U6 and U7. The design says
  `.env.example` carries **no real value** (`DESIGN.md:1272`), meaning no real credential; draft 2
  tightened that into something else. Verified today: the six above are empty, and the list is
  derived from the file rather than remembered.

**Plus the collection guard, which is not a §8 case and is a corpus-level MUST that the design never
names. BUILT at `35de193`, as `tests/test_collection_guard.py`.** `backend/testing.md:138-141`
requires it and `devops/quality-gates.md:76-81` (API-03) makes its *absence* a CI failure in its own
right; `COMPLIANCE-SPEC.md:297-305` §2.4 had recorded the same obligation for this repository and it
had reached neither the design, this plan, nor the tree (tracked as **B58**). It landed in the
**thorough** variant, not the minimal one: the minimal form asserts only that `pytest --collect-only`
exits 0, which it does perfectly happily while a file sits outside `testpaths` and is never collected
- the exact defect API-03 names. The guard lives inside `tests/`, the single configured root, so its
own disappearance fails collection.

**Why this one mattered more here than as a checkbox, stated because the next fifteen units each add
test files.** This suite's entire strategy is selection-based - `-m "not credentialed and not
network"` in `addopts`, a `tests/credentialed/` subtree collected but never run, and a zero-skip
rule. That is precisely the configuration in which a file landing outside `testpaths`, or one marker
typo, produces **a green over fewer tests than anyone believes**. It is `--strict-markers`'s sibling
defence, and the plan called `--strict-markers` *"not housekeeping"* for the same reason.

**It is not a design finding and does not need an ADR.** `DESIGN.md` is silent on the guard rather
than contradicting it, and the plan is not the design. If a frozen design that enumerates every CI
gate should have named this one, that is a separate ADR about the design's completeness.

Plus, all three now running in CI rather than by hand. **What CI asserts is the exit code and the
harness's own *all fired* property, never a literal count** - the controls harness has reported 21,
32 and 34 to three readers in one day, so a hard-coded number turns the harness growing into a red
build. The gate exits 0; the controls harness exits 0 with every control it holds firing and a clean
post-run re-check; the sweep exits 0 with **0 escapes are holes**.

**The resolve is EXECUTED, not inherited, and U0's first act is no longer a risk item.** Draft 2
carried 72 as a figure quoted from `DESIGN.md:1409-1413` and listed reproducing it among what this
plan had not verified. It has since been run, in a scratch directory outside the repo, against a
probe manifest written verbatim from that block:

| | |
|---|---|
| Result | **72 packages resolved in 368ms** |
| Executed | 2026-08-28, Python **3.12.3**, uv **0.11.3** |
| Manifest | `fastmcp==4.0.0b4`, `fastmcp-slim==4.0.0b4`, `mcp==2.1.1`, `prerelease = "explicit"` |

The figure is **confirmed rather than propagated**, and it is recorded with its provenance rather
than as a bare number, because a count with nothing executed behind it is exactly what goes stale
silently here. `pydantic` holding at a stable 2.13.4 remains the design's claim; if the resolve ever
stops reproducing, that is a finding about the ecosystem and not a licence to unpin.

**The design's CAUSAL claim about `fastmcp-slim` was control-tested, which is the more useful
result.** The manifest comment reads *"transitive prerelease; must be named or resolution fails"*.
Removing **only** that line and re-running fails: *"Because there is no version of
`fastmcp-slim[client]==4.0.0b4` ... `--prerelease=allow`"*. So it is not a defensive pin somebody
added on a hunch - **an implementer who tidies the manifest by dropping an apparently redundant
transitive breaks the build immediately.** U0 carries the comment with the line, and since a pin
whose only justification is a comment is one refactor from deletion, **that removal arm belongs in
§8 #11's test beside its positive arm.**

**Toolchain confirmed at the same time**, so U0 does not discover it late: uv **0.11.3**, Python
**3.12.3** against the design's `>=3.12` floor (`DESIGN.md:1404`), git 2.43.0, gh 2.45.0. Both
`pyproject.toml` and `uv.lock` were created here and are committed.

**What has been amended in U0's files SINCE U0's own commit, because this section is otherwise a
description of a tree that no longer exists.** All of it is in `pyproject.toml`, `ci.yml` and
`tests/`, all of which U0 owns, and none of it reopens the unit:

| Commit | What changed in U0's files | Why |
|---|---|---|
| `db5c21e` (U15) | three steps added to `ci.yml`'s `test` job; `scripts/check-u0-test-controls.sh` repaired (6 insertions, 1 deletion) | U15's own gates, and a control U15 broke. **This is why U15 is now on the `ci.yml` editor list in §4** |
| `35de193` (B58) | `tests/test_collection_guard.py` added | the guard above |
| `2228f19` | `ci.yml`: TruffleHog pinned to a release tag, not a branch tip | **predates every other row here** and was missed by drafts 7, 8 and by round 6 - a table of amendments that begins after the first amendment |
| `2d2e1a3` | `pyproject.toml`: ruff `line-length` **88, not 100**; five further `[STD]` rule families selected - `W`, `N`, `D`, `DTZ`, `T20`, `ANN` - with `convention = "google"`; **`pip-licenses>=5` added to the dev group** | `COMPLIANCE-SPEC.md:513` lists `line-length = 100` as **do-not-copy item 16** and it had been inherited from `fast-mcp-jira` and never argued; the five families are `[STD]` and were unenforced; the licence gate had been running via `uv run --with pip-licenses`, resolving **unpinned outside `uv.lock`**, so the tool auditing the frozen resolve was itself unfrozen |
| `ff0bbdf` | `ci.yml`: a **weekly `cron: '0 0 * * 0'` sweep** and a `links` job; plus `.github/workflows/pr-title.yml`, `CONTRIBUTING.md` and `.github/pull_request_template.md` | five `COMPLIANCE-SPEC-PASS.md` findings. **`CONTRIBUTING.md` changes U13's obligation** - see that unit |
| `5519032` | `ci.yml`: `actions/checkout` `@v4` → `@v6` in **five** places; **ADR-0016** filed | `COMPLIANCE-SPEC-PASS` C-1. **It did not reach `mirror.yml:28`, which is still `@v4`** - see §4 |
| `80a7fd0` | `pyproject.toml` + `uv.lock`: **`pre-commit>=3.7` declared**; and this plan's draft 7 committed | closes `U15-REPORT.md` D7, the HIGH that said the gates did not exist on a fresh clone |
| `196512b` | `.gitignore`: coverage artifacts | the file-type gate had already caught them, which is the gate working |
| `6072f5a` (U2) | `src/fast_mcp_jobvite/errors.py`, `utils/correlation.py`, `utils/__init__.py`, two test modules | **the first `src/` module beyond `__init__.py`.** U1's coverage step is now unblocked in substance |
| `b993ada` | `docs/OBLIGATIONS.md` and `docs/reviews/check-obligations.py` landed | the obligation map itself, built and then run only by hand - which is what round 7 found |
| `b7fd35d` | `docs/OBLIGATIONS.md`, and **three U0-owned files edited from outside §4's closed editor lists** (`pyproject.toml`, `.env.example`, `.github/workflows/ci.yml`) | B-number comments naming the obligation beside each rule. The out-of-list edits are the shared-file rule being bypassed by a doc-side task, which is the rule's first live test and it did not hold |
| `1b7975b` | `.github/pull_request_template.md`, `CONTRIBUTING.md`, `docs/CODE-REVIEW-CHECKLIST.md`, `docs/OBLIGATIONS.md` | B101, the reviewer checklist the PR template never carried. **`CONTRIBUTING.md` is U13's obligation surface** - see that unit |
| `9ca76fe` | `.github/workflows/mirror.yml`: `checkout@v4` → `@v6`; **`tests/test_workflow_pins.py` added** | closes C-1 at **6 of 6**. Draft 8 reported this as an open residue; it landed while round 7 was running. **It also took the U0 controls harness down - see below** |
| `ff9461a` | `.github/workflows/ci.yml`: three steps added to `design-gates`; `docs/OBLIGATIONS.md`: eight anchors repointed | wires `check-obligations.py`, its `--controls` arm and `check-plan-measurements.py`. **Wiring it moved five of the anchors it checks, three of them into `ci.yml` itself**, and the checker named each new line rather than requiring an investigation |
| `d48c112` | `scripts/check-u0-test-controls.sh`: `.github` added to the staged subset | restores the U0 controls harness, which had been aborting since `9ca76fe` - see below |
| `3a49795` | `docs/OBLIGATIONS.md`: B78 and B81 repointed; this plan | lands draft 9 on `main` and repoints the two anchors the draft's own rewrite moved - **the same-commit rule in the row above, applied** |
| `1e67f9c` | `tests/test_collection_guard.py`, `docs/reviews/check-plan-measurements.py`, `docs/OBLIGATIONS.md` (B58 `139` → `163`) | **closes collision 11**: the guard was selecting rather than checking reachability. M4 flips from `OPEN` to `PASS`, and `KNOWN_OPEN` is now empty |
| `f4f69f9` (U11) | `.github/workflows/ci.yml` (the advisory step **enabled**), `scripts/check_advisories.py`, `scripts/check-u11-advisory-controls.sh`, `tests/test_advisory_gate.py` | U11 lands. **This is §4's "enabling a commented step is a write" rule discharged for the first time** - U11 owned exactly the block naming it |
| `94330db` | `docs/OBLIGATIONS.md`: B75 and B82 repointed | **the same-commit anchor rule again**, this time because enabling a `ci.yml` step moved two anchors inside `ci.yml`. That is now three consecutive commits where an ordinary edit shifted an anchor and the gate named the new line |
| `20e55ef` (U3) | `pyproject.toml` + `uv.lock` (`loguru`), `tests/test_manifest.py`, `docs/reviews/check-plan-measurements.py`, `docs/OBLIGATIONS.md` | **collision 10's rule discharged for the first time**, in one commit: pin, re-lock, widen the exact-set assertion. It also **renames the test whose name hid the collision** - which is the standing check above, applied to the test rather than to the reader |

**A gate was DOWN at `4e5a1b2` and draft 9 fixed it, because U1 is in flight and verifying against a
harness that aborts.** `tests/test_workflow_pins.py` walks `.github/workflows/` and carries a
positive control asserting the walk actually found `mirror.yml`.
`scripts/check-u0-test-controls.sh` stages a **named subset** of the tree into its scratch copy, and
`.github` was not in it - so the walk genuinely found nothing, **the control fired correctly**, the
baseline went red, and the harness aborted **before running a single control**. Eleven controls
stopped running and the failure reported a true fact about a tree the harness had built wrong.
Verified both arms: with `.github` staged, **11/11 fired**; with the one entry removed again, it
aborts. The fix is a one-entry data addition, which is what the file's own comment calls the
identical change U15 made for `scripts/`.

**That is the same defect three times in three artifacts, and it is worth stating as a rule rather
than fixed three times.** `mirror.yml` slipped a C-1 sweep because a rule named `ci.yml` instead of
`.github/workflows/`; draft 8's verification command named `ci.yml` for the same reason; the controls
harness names eight paths and misses the ninth. **An allow-list of paths selects for exactly the path
nobody thought of**, and each instance was found only after something downstream broke. Where a
deny-list is available - stage the whole tree minus `.git`, `.venv` and caches; glob the directory,
not the file - it is the safer default, and the harness comment now says so for the fourth occurrence.

***This is that lesson's FOURTH instance, and the amendment-table command above is the fourth.***
Draft 8's form named `.github/workflows/` rather than `.github/`, and omitted `.gitignore` and
`.env.example` - so it could not return `196512b`, **a commit sitting in the table it was printed
beside**. Widened in draft 9. **A verification command that disagrees with the table it verifies, in
both directions, is the clearest form this lesson has taken here**, and the table and the command
now agree exactly: run it, compare the two sets, and if the command returns a commit this table does
not have, **the table is wrong and the command is right**.

**This table is itself the thing it warns about, and draft 7 shipped it four commits stale.** It was
written naming three commits, in a section whose stated reason for existing is that a description of
a tree goes out of date the moment anyone fixes a defect in it. **A table of amendments needs a rule
for its own upkeep or it becomes another stale count**: whoever amends a U0 file adds the row, in the
same commit, exactly as the `changelog.d` rule works - and a reader who needs certainty runs
`git log --oneline b53886e..HEAD -- pyproject.toml uv.lock .github/ tests/ scripts/ docs/OBLIGATIONS.md .gitignore .env.example`,
which is the derivation this table is a convenience for and never a substitute for. **No count is
stated for it here**, because a number beside a command that computes the number is a second source
of truth nothing keeps in step - the rule this plan already applies to the threat rows and the
controls harness. **If the command returns a commit this table does not have, the table is wrong and
the command is right**; add the row.

*Draft 8 wrote this command naming `.github/workflows/ci.yml` and omitting `uv.lock`, so **the
verification step offered to a doubting reader carried the same name-one-file-in-a-directory defect
that had just let `mirror.yml` slip through an entire C-1 sweep** - the third instance of that one
lesson, inside the remedy for it. Draft 9 widened it again, for the same reason and a fourth time:
draft 8's form still named `.github/workflows/` rather than `.github/`, and omitted `.gitignore` and
`.env.example` - so it could not see `196512b`, **a commit already sitting in the table above it**.
A file list that names one file in a directory selects for the files it does not name, and a
verification command that disagrees with the table it verifies in BOTH directions is the clearest
form that lesson has taken here.*

**Two consequences later units must not discover by conflict.** The **88-column limit is live and
lints every file from U1 onward** - draft 6 was written against a 100-column tree, and at U8 the
change becomes a whole-tree diff rather than a one-file one. And **`pip-licenses` is now a declared
dev dependency**, so the licence gate runs under `uv run --frozen` like everything else.

---

### U1 - Boot: config, transport selection, TLS refusal, shutdown

**Builds.** `config.py` (pydantic-settings, `SecretStr`, per-enabled-tool required-variable
validation per `DESIGN.md:940-946`, `JOBVITE_TOOLS` allow-list with an unrecognised name as a
**startup failure**, the `JOBVITE_ENABLE_WRITES` AND `JOBVITE_TOOLS` conjunction in both
directions per `:903-907`); `__main__.py` (transport selection, `_install_shutdown_handler()`,
`os._exit(0)` in `finally`, logging configured before imports); `server.py` (the `FastMCP`
instance, `mask_error_details=True` set explicitly, lifespan via `from fastmcp.server.lifespan
import lifespan` with `|` composition); the off-loopback TLS refusal of `:778-782`;
`server.json` declaring every variable for registry consumers.

**The variable set is now complete and closed, which draft 2 could not say.** `8814d69` named the
three the review found missing - `JOBVITE_MCP_HOST` (default `127.0.0.1`), `JOBVITE_MCP_PORT`
(default `8000`) and secret-class `JOBVITE_HTTP_TOKENS`, a JSON token-to-scopes map, empty in the
template. **Fifteen variables, and `.env.example` and `DESIGN.md` hold the same fifteen** - I
diffed the two sets rather than counting them, which is the check `DESIGN.md:1546-1552` asks for and
the one that would have caught this gap in draft 2. `config.py` can therefore enumerate the full set
and `server.json` can declare every variable, both of which were unsatisfiable before.

**`JOBVITE_HTTP_TOKENS` unset while the transport is `http` is a startup failure**, not a server
that starts with no tokens - the same fail-fast posture as every other required variable, and the
failure direction that matters, since the alternative is an open server.

**Depends on.** U0.

**Verified by.**

- §8 **#10**: `JOBVITE_MCP_HOST` set to a non-loopback address, no certificates,
  `JOBVITE_TLS_TERMINATED_BY_PROXY` undeclared - the process **exits naming the reason**. Positive
  control: the default loopback bind starts; off-loopback with the assertion declared starts. Three
  High rows (C1-S1, C1-T1, C1-I1) rest on this refusal. **This bullet was unbuildable in draft 2** -
  no variable existed that could make the bind off-loopback - and `JOBVITE_MCP_HOST` is what closed
  it.
- §8 **#18**, on **both transports** (`DESIGN.md:1340-1346`): lifespan teardown runs on SIGTERM,
  asserted by **observing the teardown side effect** - the resource the lifespan opened is released
  - and **not** by the exit code, since a process that dies uncleanly can still exit 0. Where the
  test does resolve a PID (the stdio arm, whose distinctive failure is that the process survives
  teardown entirely, `DESIGN.md:981-983`), resolve the interpreter via `/proc/<pid>/cmdline` rather
  than a wrapper. **Only the stdio arm exercises the `os._exit(0)` half**; the HTTP arm passes on
  teardown alone, which is precisely why a single-transport test would have shipped this bug.
- Config fail-fast: per-tool required-variable matrix asserted row by row, including the negative -
  a deployment enabling only `search_candidates` must **not** be forced to supply
  `JOBVITE_COMPANY_ID`.
- An unrecognised `JOBVITE_TOOLS` name fails startup; positive control - a recognised name starts.
- `JOBVITE_ENABLE_WRITES=true` with `JOBVITE_TOOLS` unset does **not** register the write.

**Inherited limits, not quietly resolved.** `DESIGN.md:1026-1034` states two: the composed
handler-plus-`os._exit` snippet **has never been run end to end on HTTP**, and **PID 1 was never
simulated**. The test above is what closes both, and until it runs green the plan carries them as
open. §12 item 5 additionally records that shutdown depends on a uvicorn implementation detail.

**Unblocked by `9d65cc0` - draft 1 had this unit stalled.** `DESIGN.md:1549-1564` now names both
settings, and both are in `.env.example`, so `config.py` can enumerate the full set:

| Variable | Default | What the plan may say about it |
|---|---|---|
| `JOBVITE_MAX_RESULTS` | **50** | Not arbitrary. 50 is the figure already in the caller-facing string `showing 50 of 1,240` used by §4.5 and C3-I1, so any other value would make two parts of the document disagree about a number a caller reads |
| `JOBVITE_OUTBOUND_RATE_LIMIT` | **6** per minute | **A conservative guess, not a vendor figure.** Jobvite documents no numeric limit at all - its only stated envelope is prose. **Checklist row 9 is what replaces this with an observation** |

**Neither default is verified, and the plan does not describe them as such.** `DESIGN.md:1584-1585`
says it directly: what B15 closed is the *blocking* half - the names exist and the template is
complete - and **whether either default is right remains open and only a live tenant can settle
it.** U6 and U7 restate this at the point they consume the values.

**And the threat-model rows did not move.** C3-I1 (`DESIGN.md:1746`) and C6-D1 (`:1738`) still read
`unmitigated (B15)`, and both are still on the mitigate-before-production-release list (`:1830`).
Naming a variable is not mitigating the row. An implementer who reads `.env.example`, finds a
default, and treats C3-I1 as closed would be making exactly the substitution this design keeps
catching - so the plan carries both rows as open into production-release readiness.

---

### U2 - The error contract and the correlation ContextVar

**Builds.** `errors.py` - the exception hierarchy and RFC 9457 problem construction, with `type`
and `status` taken **from the registry at `error-contract.md:96-108`**, never from Jobvite
(`DESIGN.md:502-534`). `utils/correlation.py` - a single `ContextVar[str | None]` named
**`request_id_var`**, that name mandated verbatim by `ai/tool-calling.md:173-175`
(`DESIGN.md:604`).

**Depends on.** U0. (Independent of U1.)

**Verified by.**

- A table-driven test over all seven registry rows: a Jobvite 401 maps to
  `/problems/external-service-error` **502**, not 401; validation is **422**, not 400; unmapped is
  `about:blank`.
- `instance` is `urn:fast-mcp-jobvite:invocation:<request_id>` and `request_id` matches it.
- All seven members present: `type`, `title`, `status`, `detail`, `instance`, `request_id`,
  `timestamp`.
- Jobvite's own status and message appear in `detail` and are **not discarded**.
- A repository-wide assertion that **no `success: true/false` envelope exists anywhere**
  (`DESIGN.md:497`).
- Problem objects are **returned, never raised** - the property `DESIGN.md:538-540` says makes them
  the one error shape no configuration can distort.
- `request_id_var` resets in a `finally`; an id cannot leak into the next invocation on a reused
  worker task - **paired with the positive arm that makes it mean anything: inside a simulated
  invocation the var reads back the id that was set.** A `ContextVar` never set at any point passes
  the leak test perfectly. U3 mints it and U5 asserts it on the wire, but U2 is handed to an agent
  as a standalone unit and this list is what that agent builds to.

---

### U3 - Audit event and single-point redaction

**Builds.** `audit.py` (mints the UUIDv4, sets `request_id_var` **in the same statement**, emits
the event with the fields `ai/tool-calling.md:171-173` names, records the transport, the resolved
client id on HTTP and an explicit **attribution-unavailable** marker on stdio, reads trace context
from `ctx.request_context.meta`, and implements the three-branch audit-write-failure policy of
`DESIGN.md:711-727`); `utils/redaction.py` **secret redaction only** - the fencing half is U8.

**Depends on.** U2.

**Verified by.**

- §8 **#4** (positive) and **#5** (absence), **as a pair** - `DESIGN.md:1280-1283` requires them
  paired so neither can be satisfied by silence. #5 asserts against the event #4 proves exists.
- §8 **#2**: a secret never reaches a log record, **including the whole `jobFeed` URL**; `sc=`
  redacted at the one enforcement point - **asserted against a log stream proven non-empty**: the
  same call emits a log record carrying the request's non-secret attributes, and the `sc=` value is
  absent from *that record*. Against a misconfigured logger emitting nothing, the absence alone
  passes. The design solved this exact shape for the audit stream by pairing #4 with #5
  (`DESIGN.md:1280-1282`); **#2 has no such pair in the design and #4 does not supply one** - #4
  proves the audit event exists, a different stream from the `loguru` records #2 is about. This
  pairing is therefore the plan's rather than the design's, and it is raised as
  [Q6](#q6---8-2-asserts-an-absence-with-no-paired-positive-in-the-design).
- §8 **#17**: trace context recorded when a `traceparent` is in the request `_meta`, **absent** when
  it is not. **Both arms required** - a field always synthesised passes a single-arm test and is the
  failure that matters. `trace_id`/`span_id` are never synthesised.
- The audit-failure policy, three arms: before the side effect the call fails; on a read it logs to
  stderr and continues; after a successful write it returns **success with a `warnings` array in
  structured content, `is_error=False`, not a problem object**, and the warning goes to **stderr**,
  not to the audit stream that just failed.
- The stdio arm asserts the attribution marker and **not** the literal `"global"`
  (`DESIGN.md:698-703` - the implementer error this row exists to prevent).

**File-boundary note.** `utils/redaction.py` is shared with U8. See [§4](#4-what-can-run-in-parallel).

---

### U4 - Jobvite client, part 1: auth and the error-detection rule

**Builds.** `services/jobvite_client.py` - `httpx2` client construction, v2 header auth
(`x-jvi-api`, `x-jvi-sc`), the v1 `jobFeed` query-parameter exception with its URL classified
sensitive, and **the invariant**: a response is successful only if the body carries no
`status.code >= 400` **and** the HTTP status is below 400 - both, every call
(`DESIGN.md:332-333`). Three error encodings handled: JSON status envelope, plain text with no
`Content-Type`, Tomcat HTML. XML is a **hardened fallback** parsed with `defusedxml` and treated as
an error body, not a handled case.

**And one request entry point**, which draft 2 omitted and U5 needs: a single method that issues one
call, applies the invariant above to the response, and returns a decoded body or raises the typed
error. **Paging around that entry point is U6; U4 owns the one-call path**, and U5's end-to-end test
is what proves it exists. Without it, an agent handed U4 alone delivers an auth-and-error module
with no caller.

**Depends on.** U2, U3.

**Verified by.**

- §8 **#1**, the 200-with-401-body trap, against `error_auth_200_body401.json` **verbatim**. This is
  C5-S1, the only Critical on the client. Positive control: a synthetic 200 with
  `status.code == 200` succeeds.
- **The four remaining recorded fixtures asserted byte-exact**: `error_auth_401.json`,
  `error_route_404.json`, `error_task_400.html`, `error_v1_auth_401.txt`. The fifth and last
  recorded fixture is `error_auth_200_body401.json`, asserted by #1 above - **the recorded tier is
  five files, and that is all of them.**
- **Separately, the two synthetic malformed bodies** (`malformed_not_json.txt`,
  `malformed_truncated.json`) fail loudly rather than degrading to an empty result. They are
  invented rather than captured, so they are **not** asserted byte-exact and carry no ground-truth
  weight - see the fixture tiers in §1.
- A route-level `404 "Invalid URL Cannot find API."` is **not** reported as a record-level
  not-found (§9 hazard 7).
- A URL containing a secret is never constructed for v2; the v1 URL never appears whole in any log
  record (joins U3's #2).
- The cookie jar is CLEARED after every request, in a `finally` so a call that raised cannot leave one behind either (`JOBVITE-CONTRACT.md:2.3`, ADR-0022 - the `AWSALBAPP-*` values are the literal `_remove_`, and `httpx2` persists and resends them by default, so an omission ships the session Jobvite told us not to carry).

Transport substitution is `httpx2`'s built-in `MockTransport` (`DESIGN.md:1359-1360`, ADR-0007). No
third-party mocking library is added, at any point in this plan.

---

### U5 - **The first runnable server**: `search_jobs` end to end, plus the fencing-decision registry

**This is the smallest unit that produces a runnable server**, and it is deliberately the *jobs*
read rather than a candidate read.

**Builds.** `models/` for the job list, `tools/jobs.py` with `search_jobs` only, registration
wired to `JOBVITE_TOOLS`, **the in-tool half of the result cap** - `JOBVITE_MAX_RESULTS` applied to
a single page's items, reporting `showing N of total` from the envelope's own `total`, with the
`min(transport_cap, configured_result_cap)` composition left to U6 so one behaviour is not built
twice - `request_id` stamped into the result's `_meta` under
`com.evolvconsulting.fast-mcp-jobvite/requestId`, **and the mechanism that generates the fencing
paths from the output models** together with the test that fails when any model field has no
fencing decision (`DESIGN.md:202-205`).

**Depends on.** U1, U2, U3, U4.

**Why jobs and not candidates.** `search_jobs` is the **public job data** class
(`DESIGN.md:137`), so this slice exercises transport selection, config fail-fast, the error
contract, the audit path, the result cap and `_meta` **without** depending on EEO exclusion,
candidate PII redaction, or red-team fencing content. It is the smallest end-to-end path through
every cross-cutting mechanism on the least dangerous data class.

**Why the fencing-decision registry lands here and not in U8.** `DESIGN.md:202-205` requires the
fencing paths to be **generated from the output models**, with a test failing when any model field
has no fencing decision. That test binds the moment the *first* output model exists. Building the
mechanism against one small model is cheaper than retrofitting it across five, and it retires the
second-riskiest unit early (see [§6](#6-the-riskiest-unit)). Job fields take an explicit
"not free text" decision; U8 is where fencing actually fires.

**Verified by.**

- An in-process FastMCP `Client` calls `search_jobs` against `MockTransport` and gets a typed
  result; the same call against `error_auth_200_body401.json` returns
  `/problems/external-service-error` **502** with `is_error=True`.
- §8 **#16**, read arm: `request_id` present **on the wire result**, under the namespaced key,
  matched against the audit event's own id, **and** the structured content still validates against
  the output model. `DESIGN.md:1332-1334` is explicit that asserting on the `ToolResult` object
  would pass while the wire carried nothing.
- **U5 adds the FIRST credentialed arm, and tightens CI's credentialed-collect step from
  `exit 0 or 5` to `exit 0 with a non-zero count`.** U0 left it accepting 5 because it cannot tell
  *"the suite is empty"* from *"the suite is healthy"*, and recorded that the first unit adding an
  arm must tighten it - **"the first unit adding an arm" is not the name of a unit, and this is that
  unit.** Per the shared-file rule in §4, this is U5's one edit to `ci.yml` and it touches nothing
  else.
- **COLLISION 11 WAS THIS UNIT'S TRAP, AND IT WAS DISARMED BEFORE U5 WAS DISPATCHED - read this
  anyway, because the rule it leaves behind still binds.** The credentialed arm above is **the first
  test file in this repository whose tests are all marker-excluded**. Until `1e67f9c`,
  `tests/test_collection_guard.py` ran collection through the `-m "not credentialed and not
  network"` selector, so that file was discovered, not collected, and reported as an orphan under
  the message *"test files exist but are not reachable from `testpaths`"* - **a false diagnosis of a
  correctly-placed file**, since `tests/credentialed/` is inside `testpaths` (`pyproject.toml:69`)
  and the arm is exactly where `tests/credentialed/README.md` tells U5 to put it. `1e67f9c` dropped
  the selector, rewrote the docstring that asserted the opposite, and added a regression test that
  **manufactures** a wholly-credentialed file rather than waiting for this unit. **Probe M4 in
  `docs/reviews/check-plan-measurements.py` now PASSES**, and `check-plan-measurements.py` runs in
  CI. **What U5 must still not do:** add `credentialed` to `_SKIP_DIRS`, or put the arm in a file
  that also holds an unmarked test. Both green the guard by hiding from it the one subtree
  `DESIGN.md:1244-1249` exists to protect, and `1e67f9c`'s third arm - a genuine orphan outside
  `testpaths` still fails after the fix - is the assertion that says so. **If U5 changes this guard
  at all, it owes that arm.**
- §8 **#16, error arm** - the `error_auth_200_body401.json` call in the bullet above returns a
  problem object whose **own `request_id` member** matches the audit event's id, asserted on the
  wire. The error half travels in the problem object rather than in `_meta`
  (`DESIGN.md:632-638` distinguishes them), so this is a different assertion from the read arm
  rather than a repetition of it. **Draft 2 scheduled this arm in no unit at all.** With it, all
  four arms of #16 have an owner: read and error here, write and audit-failure-warning in U10.
- The result cap fires and reports `showing N of total` rather than truncating.
- Every field on the job model has a fencing decision; deleting a decision fails the suite.
- The server starts on stdio and on HTTP and lists exactly the enabled tools.

---

### U6 - Pagination

**Builds.** In `services/jobvite_client.py`: offset paging with **every scan starting at
`start=0`** (`DESIGN.md:455`), page cap 500 on v2 and 1000 on `/v1/jobFeed`, the per-scan seen-set
dropping duplicates, termination on a **short page** (`len(items) < count`) and never on `total`,
the completeness check against `total` **only on an exhaustive scan**, the per-resource base
configured separately with `JOBVITE_PAGINATION_START_BASE` as an override, and
`min(transport_cap, configured_result_cap)`.

**Depends on.** **U4, not U5.** U6 owns `services/jobvite_client.py`, which U4 writes and U5 does
not, so U6 may begin at U4-completion **concurrently with U5**. Draft 4's diagram and Wave C table
both said U5, which needlessly delayed U6 and therefore U8 and U12, both of which key off it.
**Sequential with U7** - same file, see [§4](#4-what-can-run-in-parallel).

**Verified by.**

- `start=0` on the first request of every scan, asserted at the transport.
- A clamped/overlapping page drops duplicates; a test proves de-duplication **cannot** recover a
  never-returned record, so the defence is starting at 0 and not de-duplicating harder
  (`DESIGN.md:465-468`).
- Termination on a short page; a `total` that lies does not terminate or extend the loop.
- The completeness check fires on an exhaustive scan with a missing record, and **does not fire** on
  a capped call - the capped call reports `showing 50 of 1,240` and is not logged as an anomaly
  (`DESIGN.md:469-477`). Both arms are required; wiring the check to every call is the failure this
  bullet exists to prevent.
- The structural assertion that `start=0` is accepted and returns records
  (`JOBVITE-API.md:399`).

**The result cap is now named:** `JOBVITE_MAX_RESULTS`, default **50** (`DESIGN.md:1572-1575`), and
it is the configured half of `min(transport_cap, configured_result_cap)`. 50 was chosen to agree
with the `showing 50 of 1,240` string a caller already reads, which makes it internally consistent
and **not** a measurement of anything. **U5 built the in-tool half; U6 adds the transport half and
the `min()` that composes them, and does not re-implement U5's reporting string.** It is one
behaviour split across two files, which is why neither unit may assume it owns all of it.

**Inherited ceiling.** Whether `start` is 0- or 1-based is unresolved as a fact about Jobvite
(§12 item 2), and whether 500 is a real server limit is unobserved. Checklist rows 2 and 3 settle
both. **C3-I1 and C6-D1 remain `unmitigated (B15)`** in the threat model even now the variable has
a name (`DESIGN.md:1746`, `:1738`), because what closed was the naming, not the exposure. The plan
ships the design's base-agnostic scan and does **not** treat any of these as established.

---

### U7 - Resilience: timeouts, retry, breaker, and correlated logging

**Builds.** Ordered timeout → retry → circuit breaker, all inside
`services/jobvite_client.py`: explicit per-phase timeouts (no SDK default, no single scalar);
`tenacity` with jitter for connection errors, timeouts and 5xx only; a **configured total outbound
budget** bounding all attempts for one tool invocation (`DESIGN.md:373-375`);
`create_candidate` excluded from retry **by construction**; one breaker for Jobvite with **4xx
excluded from tripping it**; open-breaker and outage both `/problems/service-unavailable` **503**
distinguished by `detail` plus a `retry_after` hint; a `429` retried then mapped to 503, honouring
`Retry-After`.

**Depends on.** U6 (same file). **This is the riskiest unit** - see [§6](#6-the-riskiest-unit).

**Verified by.**

- §8 **#13**, the concurrent arm: **two invocations driven in parallel**, each forced to retry, each
  log line matched to the invocation that produced it. `DESIGN.md:1313-1315` states that a
  single-call version passes against a module global, which is the bug `request_id_var` exists to
  prevent - **so the concurrent arm is the case and a single call does not satisfy it.** The same
  case asserts **no URL** appears in a retry line.
- Every breaker transition logs its direction (`closed->open`, `open->half_open`,
  `half_open->closed`), the triggering counter, and `request_id`.
- §8 **#23**: a 4xx does not trip the breaker. Positive control: repeated 5xx does trip it.
- §8 **`create_candidate` not retrying on timeout** (#21), asserted with a **row counter** as the
  control, not by inspecting configuration - the spike measured one call producing **four rows**
  (`DESIGN.md:353`), so the assertion is the row count.
- The total outbound budget bounds a slow upstream into a typed 503 rather than an unbounded wait.
- The self-throttle honours `JOBVITE_OUTBOUND_RATE_LIMIT`, default **6 requests per minute**
  (`DESIGN.md:1576-1583`). **Say what it is at the point it is used: a conservative guess, not a
  vendor figure.** Jobvite documents no numeric limit at all, only the prose envelope *call it on an
  as-needed basis, and anything more frequent than once a day must be filtered*. **Checklist row 9
  is what replaces the guess with an observation**, and row 9 carries its own safety condition -
  run it last, stop at the first `429`, never confirm a limit by exceeding it repeatedly. The README
  states the vendor envelope, because a user syncing hourly is outside what Jobvite documents.

**The library constraint that shapes this unit, and the fallback the design now sanctions.**
`DESIGN.md:617` requires the breaker to **evaluate transitions on the call path, not from a
background timer**: a ContextVar is per-Task, so a half-open expiry fired by a timer task has no
`request_id_var` set, would log `None`, and **would fail §8 #13**. Several Python breaker libraries
do exactly that, and **no library is selected yet (B47)**.

**`9d65cc0` answered draft 1's Q4, so this is no longer the plan's recommendation - it is the
design's decision.** `:602` now reads: *"If no library satisfies it, an inline breaker in
`services/jobvite_client.py` is the sanctioned fallback"* - a counter, a state and a timestamp
checked on entry - because *"adopting a library and then constraining its scheduler is the worse
trade, because the constraint would live in our code while the behaviour lived in theirs"*, and it
is stated there so the answer is not decided by whoever happens to implement it.

**And `8814d69` corrected a second thing draft 2 inherited faithfully: B47 does name a library.**
The blessed-library list reads *"Pydantic `>=2.10`, `httpx`, `tenacity ^9` + `circuitbreaker ^2`,
`uv` packaging, `ruff`/`mypy`/`pytest`"* (`STANDARDS.md:374-375`), and B37 (`STANDARDS.md:316`) requires one
breaker per dependency **using `circuitbreaker`**. `DESIGN.md`'s former *"no library is selected
yet"* turned a one-library rejection test into an open-ended survey, and this plan repeated it
faithfully - §8 records why, and it is the right place for it to have surfaced.

So the procedure here is fixed and small: **apply the rejection test to `circuitbreaker ^2` first**,
because B47 names it and testing the blessed candidate before surveying alternatives is both cheaper
and what B47 requires. **The single experiment is: does it evaluate half-open expiry on the call
path, or from a background timer?** If it fires from a timer it is rejected **on the record**, and
the inline breaker of `DESIGN.md:617` is taken with evidence rather than by preference. If it passes,
it is adopted and nothing further is owed, since it is already a blessed dependency. Confirm the
`^2` constraint is current **against the corpus** before pinning it: I read it at
`docs/research/STANDARDS.md:374-375`, **the local research digest, not the corpus**, which §8 says
is where every standards citation in this plan comes from. The digest is not the authority for
currency.

**Inherited limit.** The circuit breaker is one of the two mechanisms `DESIGN.md:64-68` names as
**never executed** and sitting among measured results, borrowing their credibility. It is
unevidenced until this unit's tests run.

---

### U8 - Candidate reads: models, normalisation, EEO exclusion, fencing

**Builds.** `models/` for candidates (allow-listed, `strict=True`, snake_case, **no EEO fields**);
`utils/normalise.py` (casing, epoch-ms dates, `""`/null unification); the **fencing** half of
`utils/redaction.py` - path-keyed with wildcards, camelCase Jobvite paths, delimiter-token
stripping, strings only, unknown non-string fields **dropped**; `tools/candidates.py` with
`search_candidates` and `get_candidate`.

**Depends on.** U5 (fencing-decision registry), U6, U3 (shares `utils/redaction.py`).

**Write the structural assertions first** (see [§1](#1-the-count-that-governs-the-test-plan)), or
the models encode invented fixtures rather than the one observed envelope.

**This is the unit I would least want to hand to an agent in isolation, and that is a change of
mind.** §6 still names U7 the riskiest by mechanism, and that stands - but U7 has the best
scaffolding in this document: a named rejection test, a named fallback, and a harness that retires
its unknown before the unit starts. **U8 has the opposite profile.** It half-owns
`utils/redaction.py` with U3; its three Critical-bearing arms were vacuous until the control above
was added; and it depends on a fencing-path mechanism §6 itself admits *"the design does not say
how"* to derive. Three of those four done correctly still ships a green suite over a tool that
returns nothing.

**Splitting it is worth considering and is not proposed here**, because the natural seam - fencing
into one unit, models and normalisation into another - runs straight through `utils/redaction.py`,
which is already collision 2. A split that puts two agents in that file trades a sequencing risk for
a concurrency one. **The mitigation taken instead is ordering: the positive control is written
first, so the arms that follow are asserted against a result proven non-empty**, and one agent owns
the whole unit.

**Verified by.**

- **Positive control FIRST, because without it three of the arms below are vacuous and two of them
  carry Criticals: a populated candidate record round-trips with every allow-listed field present
  and correctly normalised.** Against a `search_candidates` that returns an empty page every time,
  #6 passes (no EEO field appears), #5 passes (no PII is emitted) and #20 passes (no field is
  stringified) - **three green arms over a tool that returns nothing**, on the unit carrying C6-I1
  and C6-S1. #19's red-team cases and the normalisation arm do exercise real data, so the unit was
  never fully vacuous; the arms that were vacuous are precisely the ones the Criticals hang on.
  Draft 3 applied `DESIGN.md:1370-1371`'s blanket rule to U10 and U14 and skipped U8.
- §8 **#6**: EEO fields never appear in any tool result, **asserted against the output models**, not
  by inspection. C6-I1, Critical.
- §8 **#19**: fencing, including content that tries to **close its own fence** - the red-team cases
  are merge-gating (`DESIGN.md:754`). `candidate_list_injection.json` is the seed; it is not
  sufficient on its own.
- §8 **#20**: an unknown non-string field is dropped, not stringified.
- §8 **#24**: the `eId`/`EId` casing asymmetry pinned, so a later refactor cannot tidy it into a bug.
- §8 **#5** extended to the candidate path: PII reaches the audit *path* by construction and none of
  it is emitted in the clear.
- Path-keyed, not name-keyed: a test where `title` and `eId` appear at two depths and are decided
  differently - name-keying would collide (`DESIGN.md:747-749`).
- Two tools, not one, because output cardinality differs: `get_candidate` returns one record,
  `search_candidates` a page, and under `strict=True` one tool cannot have two return schemas.
- Date asymmetry and empty-string/null unification, both directions.

---

### U9 - HTTP transport hardening

**Unbuildable in draft 2, unblocked by `8814d69`.** The review could not build this unit at all,
and it was right: it is told to construct `StaticTokenVerifier` *"from environment"* and to act
*"whenever the bind is not loopback"*, and **no variable existed for a token, a scope, a bind
address or a port**. That is B15's defect in three more variables, and draft 2 failed to run over
the rest of the set the sweep it had run for the first two. The design named them rather than
letting an agent invent them: **`JOBVITE_MCP_HOST`** (`127.0.0.1`), **`JOBVITE_MCP_PORT`** (`8000`)
and secret-class **`JOBVITE_HTTP_TOKENS`**, a JSON token-to-scopes map, empty in the template, whose
absence while the transport is `http` is a **startup failure rather than an open server**. The
reviewer's guessed names happened to match and were correctly not adopted on that basis - naming
them was the design's call, which is the whole lesson of B15.

**Builds.** In `server.py`/`config.py`: `StaticTokenVerifier` built from `JOBVITE_HTTP_TOKENS` at
startup; `require_scopes` on the **three data classes of §4.1** (candidate PII, public job data, job
feed), with the scope names drawn from that map; `allowed_hosts`/`allowed_origins` whenever
`JOBVITE_MCP_HOST` is not loopback; `RateLimitingMiddleware`
with a **mandatory** `get_client_id`; `TimingMiddleware`; `StructuredLoggingMiddleware` with
`include_payloads=False`; inbound `X-Request-ID` **validated as a UUIDv4** before use and echoed.

**Depends on.** U1, U3, U5.

**Verified by.**

- A token lacking a scope: the tool is **absent from `tools/list`** and a direct call returns
  "Unknown tool", not a permission error - the confusing-but-correct behaviour the README must
  document.
- Two differently scoped tokens see different tool sets.
- Rate limiting is **per client**, not the framework default: two clients, one drains its bucket,
  the other is unaffected. The default keys everyone to the literal `"global"`
  (`FASTMCP-SPIKE-4.md:898`).
- A malformed inbound `X-Request-ID` (newlines, over-long) is replaced rather than used; C7-T1.
- **`JOBVITE_HTTP_TOKENS` unset with `JOBVITE_MCP_TRANSPORT=http` fails at startup naming the
  variable**, and does not start an unauthenticated HTTP server. Positive control: a well-formed
  token map starts and its tokens authenticate.
- `JOBVITE_MCP_PORT` and `JOBVITE_MCP_HOST` are honoured, and the non-loopback path sets
  `allowed_hosts`/`allowed_origins` rather than leaving them at the default.

**No §8 case owns this unit**, which is worth stating rather than leaving a reader to infer
coverage: §8 #10 (U1) is the only required case on the HTTP transport, and it covers the TLS
refusal alone. Everything above is a design obligation from §7.2 and §4.4 without a required case
behind it, so its tests are ours to specify and nothing in the coupling gate will miss them if they
are dropped.
- **`ResponseCachingMiddleware`, `ErrorHandlingMiddleware`, `ResponseLimitingMiddleware`,
  `RetryMiddleware` and `PingMiddleware` are absent** - assert their absence, since each was
  excluded for a measured reason (ADR-0004, `DESIGN.md:1177-1202`) and re-adding one is a silent
  regression.
- **Positive control for that absence assertion, and it is what gives the assertion meaning: the
  three adopted middleware are present in the constructed stack**, and `StructuredLoggingMiddleware`
  is constructed with `include_payloads=False` (C2-I1, `DESIGN.md:1732`). Five absences asserted
  against a stack never proven non-empty cannot tell *"excluded"* from *"no middleware at all"*.
  Draft 3 positively verified only `RateLimitingMiddleware`, leaving `Timing` and
  `StructuredLogging` - including the `include_payloads` value a threat row exists for - with no
  assertion at all.

**Inherited limits, carried not resolved.** Burst sizing is `desired_calls + 2` where the `2` is
**FastMCP's own client's connect sequence, not a protocol constant**, and under-provisions a
heavier client (`DESIGN.md:395-403`). Every limiter measurement was **sequential and single-client**
(ADR-0002); behaviour under simultaneous callers is unverified, and `limiters.clear()` was never
tested under load. The limiter has **never been exercised on stdio** at all - `DESIGN.md:413-416`
says so explicitly and calls that reasoning, not measurement.

---

### U10 - The write: dual-era approval guard and `create_candidate`

**Builds.** `approval.py` - the dual-era guard, keyed on
`ctx.request_context.protocol_version` compared against `('2026-07-28',)`; MRTR
(`InputRequiredResult` + `ctx.input_responses`) on sessionless; `ctx.elicit()` on handshake; the
conjunction `action == "accept" and content.get("approve") is True`; **an unidentifiable era
refuses the write and logs the observed value**. `create_candidate` in `tools/candidates.py`,
registered only under `JOBVITE_ENABLE_WRITES=true` **and** naming in `JOBVITE_TOOLS`, with
`send_email` defaulting to `false`, annotations `destructiveHint: true` / `idempotentHint: false` /
`readOnlyHint: false`, a `409` surfaced as `/problems/conflict` with the duplicate named in
`detail`, and the elicitation payload naming **the candidate, the target job, and whether
`send_email` is true**.

**Depends on.** U7 (no-retry), U8 (`tools/candidates.py`, models), U9 (era plumbing on HTTP).

**Verified by.**

- §8 **#22**, four arms: deny refuses; **accept-carrying-`approve: false` refuses**; no-handler
  fails closed; the second leg actually consumes `ctx.input_responses`.
- §8 **#25**, **both eras**, asserting **the row count did not change** and not the error shape -
  the no-handler arm **raises `MCPError` on sessionless and returns `is_error=True` on handshake**
  (`FASTMCP-SPIKE-4.md:2153-2165`), so an error-shape assertion passes on one era and fails on the
  other.
- **Positive control for #22 and #25, required by `DESIGN.md:1370-1371` and load-bearing here: an
  APPROVED write moves the row counter by exactly one, on both eras.** Without it, four refusal arms
  all asserting *the row count did not move* pass perfectly against a `create_candidate` that is
  broken and never writes at all - the guard-that-refuses-everything the blanket rule is named for.
  Draft 2 omitted it on the one case where the row counter makes its absence invisible.
- An unidentifiable/absent `protocol_version` **refuses** and logs the observed value; positive
  control - a recognised era approves. (That control belongs to the era test, **not** to #22 or #25,
  which is why the arm above is separate.)
- §8 **#16**, write arms: `request_id` on the wire for a successful write **and** for the
  audit-failure warning branch.
- `approval_state` and the mechanism that produced it are in the audit event; C4-R1.
- Neither `ctx.transport` nor `session_id` is used as the discriminator - both are **identical or
  populated on both eras** and are measured traps (`FASTMCP-SPIKE-4.md:2073-2074`). Assert the
  discriminator is `protocol_version`.
- **The whole harness rests on a server-side row counter as its control**, exactly as the spike ran
  it. Without a counter the refusal arms assert nothing; this is the lesson the spike records
  against itself at `FASTMCP-SPIKE-4.md:1431` (*"Positive-control failure I hit first, and why it is
  recorded"*).

**What may never be claimed.** *"The server requires an approval response from the host and refuses
to write without one"* - **never** *"a human approved this."* C4-S1 is a **High residual** and is
not mitigable server-side. An abandoned approval **hangs the call** with no server-side bound
(C4-D1). An authorised write can still be made twice (C4-D2); the idempotency-key remedy was
evaluated and **cannot be built** because nothing establishes Jobvite accepts one (B108,
`DESIGN.md:245-268`). None of these becomes a plan item; all three are disclosed in the README.

---

### U11 - `scripts/check_advisories.py`

**Builds.** The file `DESIGN.md:1516-1522` names as **the advisory-expiry owner** and which does not
exist. It reads the ignore table from `pyproject.toml`, **emits the `--ignore-vuln` flags
`pip-audit` actually takes** - the tool has no expiry concept and no `pyproject.toml` ignore section
of its own - and **exits non-zero on any expired entry**. The table is the single source for both
the flags and the expiry; hand-maintaining the flags beside it would be the two-lists defect the
design designs around elsewhere.

**Depends on.** U0 only. **Parallelisable from the start** - it touches `scripts/` and one
`pyproject.toml` table nothing else reads.

**Verified by.** §8 **#15**: an entry past its recorded expiry is **rejected**, with a positive
control showing an unexpired entry is **honoured** and its flag emitted. Additional arms: an entry
with no expiry is rejected; an expiry more than 30 days out is rejected; a blanket ignore is
rejected.

**The policy this enforces is four ordered steps** (`DESIGN.md:1505-1524`) and step 1 -
reachability - is **human judgement written down, not a tool output**. The script owns steps 3 and
4 only.

---

### U15 - The two commit-time gates

**BUILT AND MERGED** (`db5c21e`), with `docs/worklogs/U15-REPORT.md` as its record: both gates block
real commits in a throwaway clone with the hooks installed, 36 assertions, 15 mutation controls and 5
amputation trees, all fired. The same precedence rule U0 carries applies here and is bounded the same
way: **where this section and the build disagree, the build wins, and never past `docs/DESIGN.md`.**
One HIGH from that report is **not fixed and is carried below** rather than left in a worklog.

**Builds.** The two gates of `DESIGN.md:1627-1637`, both of which the design says exceed the
standard deliberately: **secret scanning pre-commit**, not only in CI, because on a public remote a
pushed secret is compromised the instant it lands; and the **committed-file-type gate** -
allowlist-first, extension denylist, magic-number sniffing, NUL-byte backstop, fail-closed, with
overrides only via an allowlist entry in the same commit so the exception is reviewable in the diff.

**Depends on.** U0 only. **Parallel with U11 throughout.** It owns `.pre-commit-config.yaml`,
`.secrets.baseline`, `scripts/check-committed-file-types.py`, `.file-type-allowlist`,
`tests/test_file_type_gate.py` and its two harnesses outright.

**It is NOT true that it touches no file any other unit writes, and draft 6 said so on the strength
of the design mandating only commit-time gates.** A pre-commit hook is bypassable with `--no-verify`
and is not installed at all on a fresh clone, so the server-side arm is worth having - and U15 built
it. **Three steps landed in `.github/workflows/ci.yml`** (*"Committed file types, whole tree"*,
running the gate with `--all`; *"U15 gate controls, all fired"*; *"Secret scan hook runs clean"*),
which makes U15 a writer of the file §4 gives to U0 with a closed later-editor list. **That is U15's
own block under §4's shared-file rule, and U15 is on the editor list there.** It is collision 7's
shape one unit later, which is the fix-one-miss-the-sibling failure this plan names about itself
three times - and this time the sibling landed before the rule did.

**Why it is a unit and not a bullet in U0.** Draft 5 listed both gates inside U0's CI paragraph.
**U0 declined them and asked for a ruling, correctly**: they are not a CI step, they are
allowlist-first magic-number sniffing with a NUL backstop and a fail-closed default - real software
with its own test surface, in a repository where **`DESIGN.md:1811` names these two gates as the
mitigation for C8-I1, a Critical row.** A control carrying a Critical, whose own design admits
(`DESIGN.md:1636-1637`) that it *"does nothing about confidential prose pasted into Markdown, which
is the incident we actually had"*, earns its own scrutiny rather than a line in another unit's
list.

**Verified by.**

- A file of a denied type is refused; **positive control: an ordinary source file commits.**
- **Magic-number sniffing beats the extension**: a PDF renamed `.md` is refused. This is the arm
  that matters, because the incident this gate is named for was a CONFIDENTIAL PDF, and an
  extension denylist alone would have passed it renamed.
- A NUL-bearing file with an allowed extension is refused by the backstop.
- The gate **fails closed** on its own error rather than admitting the file.
- An override requires an allowlist entry **in the same commit**, and an override without one is
  refused.
- Secret scanning refuses a staged credential pre-commit; positive control: a clean tree commits.
- **The stated ceiling is carried, not quietly dropped:** `DESIGN.md:1635-1637` says this gate stops
  a *file* of the wrong type and does nothing about confidential prose pasted into Markdown, which
  is the incident that actually occurred. Review and `JOBVITE-API.md` §0.2 cover that, and no test
  here may be written as though the gate closed it.

**CLOSED IN THE TREE, with two residues that are NOT closed.** `U15-REPORT.md` D7 raised a HIGH:
`pre-commit` was not a declared dependency, so on a fresh clone both gates silently did not exist -
`pre-commit install` is `command not found`, no hook is written to `.git/hooks`, and every commit
proceeds ungated with no error anywhere, **the whole control failing open one level above the gate's
own fail-closed behaviour, because a gate cannot fail closed if it was never installed.** That was
true and it has been fixed: `pyproject.toml:50` carries `"pre-commit>=3.7"` and `uv.lock:1150`
resolves it at **4.6.2**, landed at `80a7fd0`. **C8-I1's Critical mitigation IS in force for the
team.**

*Draft 7 asserted the opposite, in this unit's own "most important sentence", against a tree that had
already fixed it one commit past the basis draft 7 measured at. **That is precisely the failure draft
7 existed to correct** - it re-checked round 5's findings against the moved tree, and did not
re-check the paragraph it was itself writing. A carried finding is not exempt from the re-check just
because it arrived in a worklog rather than in a review.*

**Two residues survive and are the live items.** First, **the CI step still reads `uv tool run
pre-commit@4.6.2`** (`ci.yml:283`) rather than `uv run --frozen pre-commit`, so the one gate arm CI
actually runs resolves **outside the frozen lock** - quietly contradicting the `uv sync --frozen`
discipline this workflow builds two other assertions to guarantee. Second, **the declared floor is
`>=3.7` where `backend/tech-stack.md:157` and `:172` both read `"pre-commit>=4.0.0"`**, and nothing
records the deviation; `setup-uv@v5` earned ADR-0016 for a smaller gap. Both are U0's files.

**One measurement worth keeping even though its finding is closed**, because the instrument is
reused: `uv run --frozen --offline pre-commit --version` exits 0 **even when `pre-commit` is not
installed in the venv**, because `uv run` falls through to `PATH`. It reads as a green and is not
one. The correct probe is `ls .venv/bin/`, `importlib.metadata.version`, or a `grep` of `uv.lock`,
each with a declared dependency as a positive control.

**This unit exists because a decision that lived only in a message is not a decision.** The ruling
was made when U0 asked and was never written down; the plan still listed the gates under a unit that
had declined them, while a Critical row named them as its mitigation. That is the shape §0 exists to
prevent, one level up from citations.

---

### U12 - `get_job_feed`

**Builds.** `get_job_feed` in `tools/jobs.py`, the v1 base, the separate `JOBVITE_FEED_KEY` /
`JOBVITE_FEED_SECRET` / `JOBVITE_COMPANY_ID` credential class, and the `jobs`-keyed envelope (a
third name for one concept, §9 hazard 3). **It consumes U6's `/v1/jobFeed` page cap of 1000; it
does not implement it.** The design states that cap once, in §4.5, which is the client layer
(`DESIGN.md:434`, *"Page cap **500** on v2, **1000** on `/v1/jobFeed`"*), and §4 gives
`services/jobvite_client.py` to U6 exclusively with U12 holding
read access only - so a U12 that built the cap would have to write a file it does not own. Draft 3
made exactly this split for the result cap and missed its sibling one line away.

**Depends on.** U5, U6, U3.

**Verified by.** The `jobFeed` URL never reaching a log record whole, `sc=` redacted - C5-I1, a
**High**, and the one endpoint that structurally requires the secret in the query string.
**Asserted against a log stream proven non-empty by the same call, exactly as U3's #2 is**: the call
emits a log record carrying the request's non-secret attributes, and the `sc=` value is absent from
*that record*. Against a logger emitting nothing the absence alone passes, and this arm carries a
High. **This is Q6's shape one unit later** - draft 4 gave U3 the pairing and did not sweep for the
sibling, which is the fix-one-miss-the-sibling failure this plan names three times. The round-trip
arm below does not close it: it proves the tool returns data, not that the logger emitted
anything. Plus `jobfeed_success.json` / `jobfeed_empty.json` round-tripping, and the third envelope
key normalised.

**Why it is late rather than in U5.** It is the only endpoint whose *URL* is a secret, so it wants
U3's redaction enforcement point proven first; and it is `[OFFICIAL]` 1-based, so it wants U6's
per-resource base configured.

---

### U13 - README and the documentation obligations

**Builds.** The README, which `DESIGN.md:1534-1541` **deliberately withholds until now** because a
README describing an unbuilt system is a false claim in the present tense. All fourteen sections
with **headings matching exactly**; the Configuration table **checked against `.env.example`**
rather than hand-maintained; an `mcp-name:` string **added before the first PyPI upload, not after**;
the `com.evolvconsulting.fast-mcp-jobvite/requestId` key documented, since a caller cannot guess it
and an id a caller cannot reach discharges nothing; the **six behaviours** of `:1539-1555`; the
read-only-key requirement in the deployment section; and a **credential-free Quickstart in full,
exercised by CI on every merge** - install, start the server, list tools. `readme-standard.md:83`
forbids a Quickstart step requiring credentials, so anything needing a Jobvite key belongs in
Configuration and Usage.

**The Contributing section must LINK to `CONTRIBUTING.md`, and "the heading exists" does not
discharge it.** `readme-standard.md:56` reads *"12. **Contributing** - link to `CONTRIBUTING.md` or
equivalent. Repos without that file must inline the contribution rules under this heading."*
`CONTRIBUTING.md` now exists (`ff0bbdf`), so **this repository is on the link arm, not the inline
arm** - which is the cheaper obligation, and it is the reason draft 6 could not have scheduled it.
But U13 as written schedules only that the fourteen headings match exactly, and **an empty
`## Contributing` heading passes that assertion while discharging nothing**
(`COMPLIANCE-SPEC-PASS.md` F-6 names precisely this). The heading carries a working relative link to
`CONTRIBUTING.md`, and U13's heading test is not the assertion that covers it.

**U13 also owns the changelog obligation, which no unit owned.** `COMPLIANCE-SPEC.md:352-358` and
`changelog-standard.md` require Keep a Changelog 1.1.0, `## [Unreleased]` at top, the six fixed
subsections, `BREAKING:` plus a migration note on a major bump, a CVE on a Security entry where one
exists, and publication dates with backdating forbidden - clauses no human reliably remembers.
`CHANGELOG.md` satisfies the first two today and **nothing checks any of it**. U13 is the
documentation unit and takes it: it merges the accumulated `changelog.d` fragments (§4), and asserts
`## [Unreleased]` is present and that every release heading parses as `## [X.Y.Z] - YYYY-MM-DD`.
**A ruling is owed and is not U13's to make**: the current `[Unreleased]` block is largely design and
research activity, which is arguably the internal-only class `changelog-standard.md:94` forbids
outright.

**Depends on.** U1-U12.

**Verified by.** §8 **#14**'s README arm goes **live** here - `DESIGN.md:1318-1321` requires it
**gated on the file's presence rather than skipped**, because a skip is a green that tested nothing.
Heading text asserted exactly; the Configuration table asserted equal to `.env.example`'s
enumeration; CI runs the Quickstart commands.

**Carried, not resolved: C5-E1 stays a High residual after this unit.** Writing the read-only-key
requirement into the deployment section satisfies §8 #14, which asserts that the instruction exists
and is discoverable. It does **not** establish that Jobvite issues read-only keys at all - that is
`CREDENTIAL-CHECKLIST.md` row 0, a question to a human that nothing else settles, and if the answer
is no the exposure is undiminished by anything in this plan. A reader who sees #14 pass and treats
C5-E1 as discharged has over-credited a sentence.

**Carried, not removed.** The unverified-success-path caveat stays until
`CREDENTIAL-CHECKLIST.md` rows 1-4 close (`CREDENTIAL-CHECKLIST.md:96-97`). **A CI status badge
cannot be live until CI exists** (`readme-standard.md:70` forbids a static badge that does not
reflect reality; draft 2 wrote a bare `:70` whose nearest antecedent was `CREDENTIAL-CHECKLIST.md`,
where line 70 is blank) - U0
makes CI exist, so the badge becomes legitimate at U0 and not before.

---

### U14 - Argument-layer hardening

**Builds.** The three inbound controls of §2.1, all in the input models: `strict=True` with extra
keys forbidden, explicit `max_length` and identifier regexes; **UTF-8 validation rejecting C0/C1
control characters other than tab, newline and carriage return, and Unicode bidi overrides**; and
the four structural limits - depth 5, 1,000 list items, 100 dict keys, 1 MiB body.

**Depends on.** **U5, U8 and U12** - every unit that writes a tool's input models. U14 is the sweep
proving the inbound set is **complete**, so starting it before all three have landed sweeps an
incomplete set and passes: **a vacuous green on the unit whose entire job is completeness.** Draft 4
said U5 here while §4 and Q5 said U5+U8+U12, and an agent reads its own unit first. It cannot run in
parallel with U8.

**Verified by.** §8 **#7**, **#8** and **#9** (**four arms, one per limit**), plus **a re-run of
U2's repository-wide no-`success`-envelope sweep across the completed tool set.** U2 owns that rule
and asserts it where it lives, but at U2-completion the repository holds almost no code, so the
assertion passes over an empty corpus and keeps passing whether or not later units respect it. U14
is already the unit whose whole job is a completeness sweep after every tool has landed, so it is
where the rule acquires teeth.

**All three carry the blanket positive control of `DESIGN.md:1370-1371`**, and draft 2 stated it for
only one: a well-formed argument passes schema validation (#7); an ordinary name passes the
control-character check (#8); and **a payload sitting just inside each of the four structural limits
is accepted** (#9). A limit test with no accepting arm cannot tell a correct limit from a rejector.

**The thing a naive plan gets wrong here.** `DESIGN.md:181-190` is explicit: **none of these
rejections carries a problem object**, because they live in the input models, run **before the tool
body**, and are raised by the framework. An earlier design revision said 400; the registry says 422;
**and neither reaches the caller on this path at all.** The tests must assert fail-closed behaviour,
not a problem-object shape. The 422 row in the registry is not dead - it serves validation detected
*inside* the tool body - but it is unreachable pre-dispatch.

---

## 3. Dependency order at a glance

```
U0  skeleton / pins / markers / CI                                [BUILT b53886e]
 ├── U1  boot: config, transport, TLS refusal, shutdown
 ├── U2  errors.py + request_id_var
 │    └── U3  audit.py + redaction (secrets)
 │         └── U4  client: auth + the error rule
 │              ├── U6  pagination ──► U7  resilience  (same file: SEQUENTIAL; U6 needs only U4)
 │              └── U5  FIRST RUNNABLE SERVER: search_jobs + fencing-decision registry
 │                   ├── U9  HTTP hardening
 │                   ├── U8  candidate reads                     (needs U5 AND U6)
 │                   │    └── U10 approval + create_candidate    (needs U7, U9)
 │                   └── U12 get_job_feed                        (needs U5 AND U6)
 │                        └── U14 argument-layer sweep           (needs U5, U8 AND U12; owns no file)
 ├── U11 scripts/check_advisories.py                             (independent throughout)
 └── U15 the two commit-time gates              [BUILT db5c21e]  (parallel throughout, but it
                                                                  WRITES ci.yml - see §4)

     U13 README                                                  (needs U0-U12)
```

**`(independent throughout)` was wrong about U15 and is corrected here rather than only in §4**,
because §3 is the diagram an orchestrator reads when assigning a lane and §4 is the table it reads
when a conflict has already happened. U15 is schedule-independent and **not** file-independent.

---

## 4. What can run in parallel

Agents sharing a tree is how work gets lost here, so these are stated as **file ownership**, not as
topic areas. One owner per file, for the life of the unit.

### Wave A - immediately after U0

| Unit | Owns, exclusively | Reads but does not write |
|---|---|---|
| U1 | `src/fast_mcp_jobvite/config.py`, `__main__.py`, `server.py`, `server.json`, `.env.example` | - |
| U2 | `src/fast_mcp_jobvite/errors.py`, `utils/correlation.py` | - |
| U11 | `scripts/check_advisories.py`, the `[tool.*]` advisory-ignore table in `pyproject.toml` | - |
| *(U0, earlier)* | - | **`.env.example`** - U0's §8 #3 asserts against it and never writes it; U1 owns it |

**Two files U0 built are written by later units, and neither appeared in any ownership table until
now.** This was invisible from the plan and visible only from the build, which is the finding's real
lesson: **the ownership model is drawn on source modules, and both surfaces that actually collide
are ones nobody thought of as code.**

| Shared file | Rule |
|---|---|
| `.github/workflows/ci.yml` | **U0 owns the file.** It landed three steps commented out and addressed by name. **U1, U11, U13 and U15 each own exactly the block naming their unit and touch nothing else** - U11 the advisory audit, U1 the coverage floors and the capability-drift diff, U13 the Quickstart, **U15 its three commit-time-gate steps (landed at `db5c21e`)**. U5 additionally tightens the credentialed-collect step (L3 below). The blocks are non-adjacent by construction, so the edits are disjoint line ranges |
| `pyproject.toml` | **U0 owns the file.** U11 edits rows inside the advisory-ignore table U0 landed empty; **U1 adds `[project.scripts]`**, which U0 deliberately omitted because it names a function U1 writes; U13 adds `readme`. Same rule: touch your own key, nothing else. **No unit adds a coverage key** - see U0 and `COMPLIANCE-SPEC.md:292-295` |
| `.github/workflows/mirror.yml` and `pr-title.yml` | **U0 owns both, and they appeared in NO ownership row until draft 8.** A sweep that fixed `actions/checkout` in five places inside `ci.yml` did not reach `mirror.yml:28`, and the project recorded C-1 as closed while it was not. **`9ca76fe` has since closed it at 6 of 6** - `mirror.yml:28` is `@v6` today - so the residue is gone and **the row is what remains, which is what the finding was actually for**: `.github/workflows/` is the unit of ownership, not `ci.yml`, because a rule naming one file in a directory selects for the files it does not name |
| `docs/OBLIGATIONS.md` and `docs/reviews/check-obligations.py` | **U0 owns both. NOW WIRED in CI** (`ff9461a`, two steps: the anchors and the checker's own controls arm) - round 7 found it running by hand only, which is the `--all` file-type mode with no CI step one artifact later, **the same defect this repository has now built twice**. **Its anchors point INTO this plan and into `pyproject.toml`, `.env.example` and `CONTRIBUTING.md`, so U1, U5, U11, U13 and U15 all shift them by editing normally** - and a line-numbered anchor is not a claim about content, it is a claim about *position*. **Whoever moves a line repoints the anchor in the same commit**; draft 9 shifted two (B78, B81) and repointed both, and the checker names the new line for you |
| `tests/test_collection_guard.py` **and the marker set** | **U0 owns it. This was collision 11, and it is CLOSED at `1e67f9c`.** The guard passed the `-m "not credentialed and not network"` selector to its own `--collect-only` call, so it asked *"is this file SELECTED?"* when the property it exists to check is *"is this file REACHABLE?"* - and the two differ for exactly one shape of file, the one whose tests are all `credentialed` or all `network`. **U5 is scheduled to create the first one.** The selector is gone, the docstring that asserted the opposite is rewritten in place, and a regression test **manufactures** a wholly-credentialed file rather than waiting for U5. **The rule that survives, and binds every later unit: do not narrow this guard to buy a green.** Adding a directory to `_SKIP_DIRS`, or hiding a marker-excluded arm in a file that also holds an unmarked test, both green it by making it blind to the subtree `DESIGN.md:1244-1249` exists to keep from rotting. `1e67f9c`'s third measured arm - a genuine orphan outside `testpaths` still fails after the fix - is the assertion that the guard did not go blind, and any change here owes the same arm |
| `[project] dependencies` in `pyproject.toml`, **`uv.lock`, and `tests/test_manifest.py`** | **One surface, not three, and it has NO owner - this is the row that breaks U1.** `tests/test_manifest.py` asserts **exact set-equality** over the whole runtime dependency list against the three pins. **Every unit that adds a runtime dependency must, in ONE commit: add the pin, re-run `uv lock`, and widen that assertion** - U1 `pydantic-settings`, U3 `loguru`, U4 `defusedxml`, U7 `tenacity` and possibly `circuitbreaker`. **`uv.lock` is regenerated whole**, so §4's disjoint-line-ranges mechanism does not exist for it: two units adding a dependency concurrently conflict on the entire file. **Units adding a runtime dependency are therefore SEQUENCED on this surface, never concurrent** - and **this costs no lane**: under the wave tables below no two dependency-adding units are ever concurrent anyway, so the rule records a property the schedule already has rather than imposing one an orchestrator must enforce |
| `tests/conftest.py` | **U0 owns the file and it stays small.** It holds repo paths and the fixtures-directory accessor, and nothing else. **A unit that needs fixtures creates `tests/fixtures/<subject>.py` and registers it with one entry in `conftest.py`'s `pytest_plugins` list** - `tests/fixtures/transport.py` (U4), `tests/fixtures/tools.py` (U5), `tests/fixtures/http.py` (U9). One file per unit, write sets disjoint by construction, and the `pytest_plugins` entry is a row in a container, which is the same mechanism as the advisory-ignore table. **No unit adds a fixture body to `conftest.py`** |

**Enabling a commented step is a write.** Draft 5 called U1 and U11 *"genuinely disjoint"* in this
wave; they are not, and neither is U13. The mechanism is the one this section already invented for
U11's `pyproject.toml` table - **U0 lands the container, each later unit edits only its own row** -
extended to the workflow, where draft 5 had no mechanism at all. If that is judged too fine-grained
to trust to concurrent agents, the fallback is to sequence U1 and U11, which costs one lane out of
three. **The row is taken over the sequencing**, because the edits are non-overlapping line ranges
by construction rather than by care - but it is stated either way, because otherwise the first two
agents to land find out by conflict.

**Why `conftest.py` gets a rule at all, and why it gets THIS rule rather than the other candidate.**
Draft 6 named the hazard and stopped there - *"`tests/conftest.py` is the same shape waiting: U0 owns
it, every later unit adds fixtures to it, and no row here says so yet"* - which is a correct
diagnosis and not a rule. **An orchestrator reading that sentence acts on it; an agent handed U8
alone does not.** It reads §4, finds no `conftest.py` row, and writes. That asymmetry is the same one
this plan names for U0's precedence sentence. And the timing is the worst available: by the Wave C
table below, U5 and U6→U7 start at U4-landing, U9 at U5, and U8 and U12 together - **four to five
units overlapping in time, every one of which adds fixtures**, into a file that already holds
module-level shared state (`REPO_ROOT`, `FIXTURES_DIR`, `PYPROJECT`, `UV_LOCK`, `ENV_EXAMPLE`,
`GITIGNORE` and two session fixtures), not just fixture bodies.

**The alternative was conftest-per-directory** - `tests/client/conftest.py`, `tests/tools/conftest.py`
- which needs no shared line at all and is therefore the tidier-looking answer. **It is rejected on a
measurement, not on taste: a conftest fixture is visible only below its own directory, so it cannot
be shared between two units' directories.** Probed on this project's own interpreter, pytest 9.1.1:

```
tests/tools/conftest.py defines mock_transport
  tests/tools/test_t.py::test_here    PASSED
  tests/client/test_c.py::test_there  ERROR - fixture 'mock_transport' not found
```

That is fatal here specifically, because the fixtures that collide are the **shared** ones: U5 and U8
both need a `MockTransport` factory, and U4's recorded-fixture accessor is read by U4, U5, U6 and
U12. Under per-directory conftests every such fixture is either duplicated per directory - two copies
of a factory that must agree, which is the drift `conftest.py` exists to prevent - or hoisted back
into the root `conftest.py`, which **is** the collision, reached by a longer route.

**The plugin form was probed too, rather than assumed, because the obvious objection to it is real
elsewhere.** `pytest_plugins` is refused in non-rootdir conftests in some pytest lineages, and
`tests/conftest.py` is not the rootdir here (`pyproject.toml` at the repo root is). Measured on
pytest **9.1.1** with `tests/fixtures/transport.py` registered from `tests/conftest.py`: **passes,
and emits nothing under `-W error`.** If a future pytest bump makes that an error, the fallback is
`-p tests.fixtures.<name>` in `addopts`, which moves the shared line into `pyproject.toml` - a file
this section already governs by the same mechanism. **Neither fallback is per-directory conftests.**

**Why the dependency row is the one that breaks first, and why no earlier round saw it.**
`tests/test_manifest.py` reads, in its body, `assert set(_dependencies()) == {"fastmcp==4.0.0b4",
"fastmcp-slim==4.0.0b4", "mcp==2.1.1"}`. **Its NAME is
`test_fastmcp_and_fastmcp_slim_are_pinned_at_the_same_version`** - which is a claim about two pins
and says nothing about the set being closed. **A reader checking "does U1 break any test?" reads the
names, and no name in that file warns that adding a dependency turns it red.** Verified both arms:
adding `"loguru>=0.7"` to a copy of the manifest makes the assertion False, the unmutated copy True.
`loguru`, `tenacity`, `defusedxml` and `circuitbreaker` return **zero** hits in `uv.lock` - absent
even transitively - against a positive control of five hits for `pytest`, so this is a real absence
and not a bad search.

**The trap is the shape of the red, not the red itself.** The failure surfaces as a
manifest-integrity breach in a file whose siblings exist to stop exactly that, so **the cheapest way
to green is to widen the set literal** - which is a unit editing an assertion that guards U0's pins,
to make room for its own dependency, alone, at speed. That is why this is a scheduled obligation in
three parts and not a note. **`[project] dependencies` is not in the `pyproject.toml` row's key list
and `uv.lock` appears nowhere in §4 at all**, which is how a surface every implementing unit must
touch reached round six unowned.

**This is not an ADR.** `DESIGN.md:1416-1421` gives the three-pin block as the packaging recipe and
nowhere says the runtime dependency list is closed - the design names `loguru`, `tenacity` and
`defusedxml` itself. **The exact-set assertion is U0's build going past the design**, and the plan
records that rather than treating a test as authority.

**Two properties of the built test configuration that a unit adding test files must know, because
neither is discoverable from this section's tables.** First, **there are TWO selection markers, not
one**: U0 landed `network` beside `credentialed`, and CI runs the network arm as its own step. **A
unit that adds a network-touching arm without the marker puts a live resolve in the default offline
suite**, where it fails for the wrong reason or passes by accident depending on the runner - and
`--strict-markers` means a marker that is not in `pyproject.toml`'s `markers` list fails collection
outright, which is the intended behaviour and not a defect to work around. Second, **the collection
guard is live, and what it checks is REACHABILITY, not selection**: a `test_*.py` created anywhere
outside `testpaths` turns the suite red rather than being silently uncollected, **and a file inside
`testpaths` whose tests are all `credentialed` or all `network` is fine** - it is reachable, merely
deselected. *That second half was not true until `1e67f9c`. Until then the guard passed its own
marker selector to its `--collect-only` call, so it asked "is this SELECTED?" and reported the answer
as "not reachable from `testpaths`" - collision 11, and the case U5 hits by design. Drafts 7 and 8
stated only the first half, which is the case a unit will not hit.* **The rule that outlives the
fix: never narrow this guard to buy a green** - see its row in the shared-file table.

**Genuinely disjoint, restated for what the table now says.** In Wave A itself **the only files two
units touch are the ones in the shared-file table above - every row of it, and no others** - and each
is governed by a container-and-rows rule rather than by sequencing. **The table is the count and this
sentence does not repeat it.**

*This sentence has carried a wrong number in every draft that stated one, and each correction was
overtaken by the next row. Draft 6 said "the one shared file is `pyproject.toml`" under a table
already listing two. Draft 7 inherited it. Draft 8 corrected it to "three" under a table it had
itself grown to five - **recreating the defect inside its own correction**, one paragraph from where
it had just fixed two other count-behind-its-own-table errors. Draft 9 wrote "six", and collision
11's row made it seven before the draft was finished. **Draft 8 left the instruction "if a seventh
row lands, delete the number instead of incrementing it"; a seventh row landed, and this is that
deletion.** A count beside the list that computes it is a second source of truth nothing keeps in
step, and this is the cheapest possible demonstration of it: **the table was correct in every one of
those drafts, and only the sentence beside it was wrong.***

### Wave B - after U2

U3 (`audit.py`, `utils/redaction.py`) and U4 (`services/jobvite_client.py`) are disjoint **files**,
but U4 depends on U3's redaction point for its logging assertions. Run U3 first, or run them
together with U4 stubbing nothing - do **not** run them concurrently with two agents, because U4's
§8 #2 arm asserts against U3's implementation.

### Wave C - after U4, the widest genuine fan-out

| Unit | Owns, exclusively | Reads but does not write | Earliest start |
|---|---|---|---|
| U5 | `tools/jobs.py` (the `search_jobs` half, with its registration and input model), `models/job.py`, the fencing-decision registry | `services/jobvite_client.py` | **starts at U4** |
| U6→U7 | `services/jobvite_client.py` | - | **starts at U4** - U6 owns this file, which U5 does not write, so it need not wait for U5 |
| U9 | `server.py` (middleware + auth block), the HTTP half of `config.py` | `audit.py` | starts at U5 |
| U8 | `models/candidate.py`, `utils/normalise.py`, the fencing half of `utils/redaction.py`, `tools/candidates.py` | `services/jobvite_client.py` | **starts when U5 AND U6 have both completed** |
| U12 | the `get_job_feed` half of `tools/jobs.py`, `models/job_feed.py` | `services/jobvite_client.py` | **starts when U5 AND U6 have both completed** |

**`models/` is a directory of per-tool files and never a shared module.** Draft 5 gave the whole
directory to U8 while U12 needs an output model for `get_job_feed` and starts at the same instant -
so U12 had to write a directory U8 held exclusively. **`DESIGN.md:291` is what makes the split legal
without an ADR:** *"`models/` allow-listed OUTPUT models, **one per tool**; no input model lives
here."* One file per tool keeps the write sets disjoint. **The first agent to add a shared base
class re-creates the collision**, which is why the rule is stated rather than left to inference.

**U14 is not in this wave, and the frozen design has now settled why.** Draft 2 gave it exclusive
ownership of *"the input-model modules under `models/`"*, a module class that did not exist. The
freeze resolves it: `DESIGN.md:289-291` puts **input models beside their tools in `tools/*.py`** and
makes `models/` output-only, *"no input model lives here"*.

**That answers the ownership question and leaves the scheduling one unchanged**, which draft 3
conflated. U14 is the sweep proving the inbound set is complete across every tool, so it depends on
U5, U8 and U12 having written their input models - into `tools/*.py`, which those three units own.
**U14 therefore still owns no file exclusively and still runs last.** It is a dependency that keeps
it out of Wave C now, not a missing boundary.

**Eleven collisions to plan around, all real, and ELEVEN IS A FLOOR.** The count has been understated
six times - four in draft 3, five in draft 4, six in draft 5, eight in draft 6, nine in draft 7, ten
in draft 8 - and **every single correction found the next one**. Draft 7 predicted a tenth and round
6 found it; **draft 8 predicted an eleventh and round 7 found it, in the next round, on the first
look.** Treat eleven as the current floor and never as a ceiling. *Eleven is the count of the
numbered list below and is checkable against it; the series above is re-derived from the committed
objects in [§10.1](#101-the-collision-count-is-a-floor-and-it-always-was), which also records that
drafts 3-5 were never committed here and so their three counts cannot be re-derived at all.*

**Collisions 10 and 11 are one species and it is worth naming, because the mechanism predicts where
the twelfth is.** Both are **an assertion that closes a set the plan schedules units to grow**, and
in both the test's NAME describes something narrower than its body does:
`test_fastmcp_and_fastmcp_slim_are_pinned_at_the_same_version` closes the whole dependency list, and
a guard named for files *"outside `testpaths`"* actually fails on any file whose tests are all
deselected. **A reader auditing "what will U-next break?" reads names, and both names are true and
incomplete.** Round 7 enumerated every closed-set assertion in `tests/` and `scripts/` against what
this plan schedules and found the rest safe - **but that sweep is a fact about one moment, not a
property of the tree**, and it is superseded by the standing check below rather than inherited.

**THE STANDING CHECK - every unit runs this, and it replaces predicting the twelfth collision.**
Before writing code, each unit brief asks *"what will my change break?"* and answers it by
**grepping the test suite for assertions that close a set my change grows**:

```
grep -rn "== {\|== \[\|len(.*) ==\|frozenset(\|set(" tests/ scripts/
```

Then, for every hit: **open the body and read it. Do not read the test's name.** Both of the two
most expensive collisions found on this project were invisible from the name and obvious from the
body - `test_fastmcp_and_fastmcp_slim_are_pinned_at_the_same_version` closes the *whole* dependency
list, and `test_every_test_file_is_reachable_from_testpaths` fails on files that are inside
`testpaths` and merely deselected. **A test name is an unverified claim about its body.** A unit
that adds a closed-set assertion of its own writes the name to match the body, and adds a row here
if the plan schedules anything to grow that set. **Collisions 7, 8 and 9 were all
invisible from the plan and visible only from the build or from a reviewer reading a document the
plan had declared unread**, which is the pattern: the ownership model is drawn on source modules, and
the surfaces that actually collide are the ones nobody classified as code:

1. **U6 and U7 both live in `services/jobvite_client.py`.** §3's module layout fixes that file, so
   they **cannot** be parallelised. One owner, U6 then U7. Splitting the client into two modules to
   parallelise them would be a design change and is not proposed.

   **And one rule about READING that file, because §4's rules are write-ownership only.** U5 starts
   at U4-completion alongside U6 and its end-to-end test drives U4's single request entry point -
   inside the file U6 is at that moment restructuring for paging. **U6 may extend
   `services/jobvite_client.py` but may not change the signature or the error behaviour of U4's
   entry point while U5 is open; a change there is a message to U5's owner, not a merge.** Pinning
   U5 to U4's SHA instead would make U5 green against a client that no longer exists by the time U6
   merges - **worse than a conflict, because nothing reports it.** This plan makes exactly that
   argument against scheduling U12 early; the U5/U6 pair is the same relationship with reader and
   writer swapped, and it is scheduled concurrent on purpose.
2. **`utils/redaction.py` holds secret redaction (U3) and untrusted-content fencing (U8).**
   `DESIGN.md:1366-1368` names both, and ADR-0010 puts `utils/` at the standard's **95%** because of
   it. Two agents cannot both own it. Sequence U3 → U8, or give one agent both halves.
3. **U8 and U10 both write `tools/candidates.py`.** Sequential, U8 then U10.
4. **The `/v1/jobFeed` page cap of 1000 has one home and two claimants.** `DESIGN.md:434` puts it in
   §4.5, the client layer - *"Page cap **500** on v2, **1000** on `/v1/jobFeed`"* - so it lives in
   `services/jobvite_client.py`, **U6's file, which U12 may only read.** It is U6's outright; U12 consumes it. This is the result cap's sibling, and draft 3
   fixed one and not the other.
5. **Tool registration has no stated home and four claimants - and this is the one that breaks
   first.** U5, U8, U10 and U12 each add a tool that must be registered, and `create_candidate`'s
   registration is conditional on the `JOBVITE_ENABLE_WRITES` **and** `JOBVITE_TOOLS` conjunction
   (`DESIGN.md:925-929`). U8, U12 and U9 overlap in time by the table above, so if registration
   lived in `server.py` three concurrent units would need one file the table gives to U9 alone.

   **The frozen design settles this without an ADR, on its enumeration rather than on preference.**
   `DESIGN.md:283` gives `server.py` exactly *"FastMCP instance, middleware stack, lifespan"* -
   registration is not among them - while `:289-290` give `tools/*.py` their tools and, since Q5,
   their input models. **So each unit registers its own tools in its own `tools/*.py`, off the
   `FastMCP` instance imported from `server.py`, and applies the `JOBVITE_TOOLS` gate at that
   decorator site.** `server.py` holds the instance, the middleware stack and the lifespan only, and
   stays U9's exclusively in Wave C: **no unit but U1 and U9 writes `server.py`.**

   **If anyone wants registration centralised in `server.py` instead, that is an ADR**, not a
   preference to be exercised by whichever agent reaches it first - which is precisely the position
   an agent working alone would otherwise be left in.
6. **`models/` is one directory with three writers.** U5 adds the job model, U8 the candidate
   models, U12 the job-feed model, and U8 and U12 start at the same instant. `DESIGN.md:291` -
   *"one per tool; no input model lives here"* - makes the per-file split legal without an ADR, so
   the rule is **one file per tool and never a shared module**. Draft 5 gave the whole directory to
   U8 exclusively while U12 needed to write in it concurrently.
7. **`.github/workflows/ci.yml` and `pyproject.toml` are written by FIVE units between them and
   appeared in no ownership table.** U0 owns both; U1, U11, U13, U5 and **U15** each edit only the
   block or key naming their unit. See the Wave A shared-file table above. **Enabling a commented CI
   step is a write**, and draft 5 called two units that must both do it *"genuinely disjoint"*.

   **U15 is the fifth, and it is the one the plan got wrong twice.** Draft 6 wrote that U15
   *"touches no file any other unit writes"* while U15 was in flight; U15 then landed three steps in
   `ci.yml`. Round 5 caught it as a *possible* future write, from a `--all` mode documented in a
   script's usage block with no CI step behind it; by the time the finding was applied it was three
   committed steps. **Both readings were of the same file at different hours, which is why this
   collision is worth stating as a class rather than as five names**: a unit that builds a gate will
   want a server-side arm for it, and the server-side arm is always this file.
8. **U14's input-model checks share `tools/*.py` with the three units that write them.**
   `DESIGN.md:289-291` puts input models beside their tools, so U14's subject lives in files U5, U8
   and U12 own. It is **sequenced last rather than parallelised**. See
   [Q5](#q5---answered-and-landed-input-models-live-beside-their-tools), and note that **no unit
   plans a shared `utils/constraints.py`** until **ADR-0012 is ACCEPTED**. *Drafts 5-7 gated on
   existence, which an agent discharges by running `ls docs/adr/`: it would find the file and be
   licensed to build the very module this gate was written to prevent. **The operative property is
   Accepted, never existence**, and this was the same error in both places the plan gates on an ADR.*

   **THE GATE IS NOW DISCHARGED, and by the design rather than by this sentence.** ADR-0012 reads
   `Status: Accepted` as of `a39bd2a`, and - which is what actually settles it - `DESIGN.md:295` and
   `:300` at the frozen `c15b138` list `utils/constraints.py` and require every input model to import
   from it. The frozen design is the authority; this plan is subordinate to it. The module exists and
   U5 built on it, correctly reading the ADR and the design rather than this paragraph.
9. **`tests/conftest.py` is one file that every test-bearing unit must write, in the widest wave.**
   U0 owns it and it already carries module-level shared state, not just fixtures. U4 needs an
   accessor per recorded fixture; U5 and U8 both need a `MockTransport` factory; U9 needs a
   client-with-token factory - and four to five of those units overlap in time. **The rule is the
   `tests/fixtures/<subject>.py` plugin row in the Wave A shared-file table**, chosen over
   conftest-per-directory on a measurement recorded there. Draft 6 named this hazard in prose and
   wrote no rule, which is the one failure mode §4 opens by naming: **a diagnosis binds an
   orchestrator and does not bind an agent working alone.**
10. **The runtime dependency list is one surface spanning `pyproject.toml`, `uv.lock` and
    `tests/test_manifest.py`, and it had no owner while five units are scheduled to add to it.**
    U1 (`pydantic-settings`), U3 (`loguru`), U4 (`defusedxml`), U7 (`tenacity`, possibly
    `circuitbreaker`). See the fourth shared-file row above. **This one is different in kind from
    1-9 and that difference is the lesson:** every other collision is two units wanting one file,
    and the mechanism is to partition the file. Here **a test asserts a closed set**, so the
    collision is between each unit and an *assertion* - and because `uv.lock` regenerates whole,
    partitioning is not available at all. **It bites U1, which is the next unit to be dispatched**,
    and it survived six review rounds because the test's name describes two pins while its body
    asserts the whole list.
11. **The collection guard red the suite on the first wholly-credentialed test file, and U5 is
    scheduled to create one. CLOSED IN CODE at `1e67f9c`** - kept here because the species is the
    point and because the rule it leaves behind still binds U5. `tests/test_collection_guard.py`
    compared files found on disk against
    files pytest reported as collected - but `_collected_test_files()` ran collection **through the
    marker selector**, `-m "not credentialed and not network"`. **A file whose tests are ALL
    `credentialed`, or all `network`, was discovered and not collected, read as an orphan, and
    failed the guard.** The plan schedules exactly that file: U5 *"adds the FIRST credentialed
    arm"*, and each tool unit adds its own. **The guard's own docstring asserted the opposite** -
    that the credentialed subtree *"appears in `--collect-only` output"* - and it was false; it had
    never been tested, because `tests/credentialed/` held only `README.md` and the two `network`
    tests sit in `test_manifest.py` beside unmarked ones, so that file is collected anyway.

    **Reproduced both arms before it was fixed** (`docs/reviews/check-plan-measurements.py`, probe
    M4): planting a wholly-`credentialed` file failed the guard naming it; the same tree without it
    passed. **§4's only warning about the guard had said the trigger is a file "outside
    `testpaths`" - and `tests/credentialed/` is INSIDE `testpaths`**, so a unit reading the plan was
    told the opposite of what would happen to it.

    **This is collision 10's species, not collision 1-9's**: a name describing something narrower
    than the body, on a surface nobody classified as code. **It was a real defect in shipped code
    rather than a gap in this plan** - `tests/` is U0's - and it was closed as a U0 follow-up at
    `1e67f9c` rather than left for whichever unit tripped it first. **M4 now PASSES.** *The fix
    carried a third measured arm that is the part worth copying: a genuine orphan outside
    `testpaths` still fails after the change, so the guard was not made blind in the course of
    making it green.* **What still binds U5: do not narrow this guard.** Adding a directory to
    `_SKIP_DIRS`, or putting a marker-excluded arm in a file that also holds an unmarked test, both
    green it by hiding the subtree from it.

**Read this from the earliest-start column rather than from this sentence: Wave C is two lanes at
U4-landing - U5 and U6→U7 - stays two at U5-landing as U5 hands off to U9, and widens to FOUR when
U5 and U6 have both completed, as U8 and U12 unblock together.** Draft 5 said *"two lanes at
U4/U5-landing - U6→U7 and U9"*, naming a pair that fits only the second moment: the table gives U9
an earliest start of U5, so at U4-landing U9 cannot run. **This is the fourth revision of this
sentence**, which is itself the argument for deriving it from the column. Neither waits for U7. U8 and U12 have disjoint write
sets and may run concurrently with each other and with U7 and U9 - **which holds only because
collision 5 above puts registration in each unit's own `tools/*.py` rather than in `server.py`.**
If registration were centralised, U8, U12 and U9 would be three units in one file and this
four-lane claim would be wrong.

*Drafts 5, 6 and 7 all said "collision 6 below" here. Registration is **collision 5**, and the list
is **above** this paragraph, not below - two errors in the one cross-reference that carries the
four-lane claim, surviving four review rounds because a reader who already believes the claim never
follows the pointer. Collision 6 is `models/`, which would not support this sentence at all.*

**U8 had no wave at all in draft 4**, which is the lane count being understated a third time in the
same place, and in the mirror of draft 3's error: draft 3 scheduled a unit too early, draft 4 left
the plan's largest and riskiest read unit - the one §6 calls the one it would least want handed over
in isolation - with **no scheduled start**, so an orchestrator reading this table had no row to
assign it from.

**Disjoint write sets are necessary and not sufficient, which is what draft 3 got wrong.** U12
depends on U6 - this plan says so three times, in U12's own Depends line, in §3's diagram, and in
U12's prose about the per-resource base - and then scheduled it concurrent from U5-landing anyway.
An agent handed U12 at that moment needs the per-resource base U6 is at that instant building
inside a file U12 may only read. It either blocks or writes into U6's file, which is the exact
failure §4 opens by naming. **The earliest-start column above is now part of the table**, because
the table is what an orchestrator reads and the dependency was only ever in the prose.

The count has now been wrong twice in the same place - **four** in draft 2 on a boundary that did
not exist, **three** in draft 3 on a dependency it stated itself - so it is derived here rather
than asserted: a lane may start when every unit it depends on has completed, and U12's earliest
start is U6's completion.

**What the first built unit taught this section, carried here because it is a property of the model
and not of U0.** Two of the collisions above - `models/` and the CI-plus-manifest pair - were
**invisible from the plan and visible only from the build**. The reason is structural: **this
ownership model is drawn on source modules, and the surfaces that actually collide are the ones
nobody classified as code.** U0's deferrals are all future writes back into U0's own files, and a
table of "who owns which module" cannot express *"U11 later edits a file U0 owns"* - which is why
the shared-file table above exists as a second kind of row. **`tests/conftest.py` was the same shape
waiting and now has its row** (collision 9): U0 owns it, every later unit needs fixtures in it, and
the rule is the plugin-file mechanism rather than a coordination convention. Draft 6 stopped at the
sentence before this one, which is why it took an outside reader to convert a named hazard into a
rule.

**Two rules that cost nothing and prevent the failures that actually happen here.**

**No agent runs `git stash`**, and no agent switches branches on a tree another agent is working. If
two units must overlap in time on the same file, they get separate worktrees pinned to a SHA, not
turns in one checkout.

**Every unit that changes user-visible behaviour leaves a `changelog.d/<unit>-<slug>.md` fragment and
never edits `CHANGELOG.md`.** `changelog.d/README.md` is a committed convention with its own ruling
on what earns one, and the word "changelog" did not appear anywhere in draft 6 - fifteen units
shipping user-visible behaviour, none told to leave a record. **The mechanism already prevents the
collision, which is why this is a rule about a missing record and not about lost work.** Per that
file's own ruling: **CI changes, test-only changes, refactors, lint fixes and review documents get no
fragment** (`changelog-standard.md:94`, *"internal-only changes ... MUST NOT appear"* - two entries
have already been removed from `CHANGELOG.md` for breaching it). The line that is genuinely not
obvious on this repository, and that produced that breach: **a document published here IS
user-visible** and earns a fragment, while **the machinery that produces those documents is not**.
U13 merges the accumulated fragments and owns the `CHANGELOG.md` conformance clauses; when it is
ambiguous, leave it out.

---

## 5. Where the credential-free constraint reorders the work

The design's own front matter (`DESIGN.md:63`) says **no claim about a Jobvite success response
is verified, because none has ever been observed.** Five consequences for sequencing, each of which
inverts what I would otherwise do:

1. **The error path is built before the success path, and it is the only ground truth.** Normally
   the happy path comes first. Here the recorded fixtures are *all* error transport, so U4 - the
   error-detection rule - is the earliest unit with byte-exact evidence behind it, and the success
   models (U5, U8) come after and are explicitly hypotheses.

2. **The structural assertions are written before the candidate models, not after.** The one
   observed `200` cannot ship as a file. If the models are written first they will encode the
   synthetic fixtures - which we invented - and the structural tier will then be *derived from the
   models it was supposed to constrain*. That is circular, and it is the exact failure the
   three-tier split exists to prevent.

3. **The first slice is `search_jobs`, not `search_candidates`.** With no credential there is no way
   to discover a shape mistake at runtime, so the first end-to-end path should exercise the
   cross-cutting machinery on the data class where a mistake is cheapest. Public job data has no
   EEO exclusion, no PII redaction and no red-team fencing riding on it.

4. **`create_candidate` is last, and its verification is structurally different from every other
   unit's.** It can never be exercised against Jobvite - there is no sandbox, and
   `CREDENTIAL-CHECKLIST.md` row 10 requires customer agreement, a named test job and an agreed
   cleanup path *before* one real write. So U10's entire assurance is the approval guard plus a
   **server-side row counter** as the control, replicating the spike's harness. Every refusal arm
   asserts *the count did not move*; none of them asserts an error shape.

5. **The credentialed suite is written as the units land, and never run.** Each tool unit adds its
   credentialed arm behind the declared marker. CI **collects** it (`--collect-only`) so an import
   error or renamed fixture surfaces immediately rather than on the day a key finally arrives
   (`DESIGN.md:1246-1250`). Without this the excluded suite rots invisibly for the whole project.

Two things the constraint does **not** let us decide, which the plan therefore leaves open: the
`start` base (checklist row 2) and whether 500 is a real page cap (row 3). Both ship as configured
values with the design's base-agnostic scan around them.

---

## 6. The riskiest unit

**U7, resilience - specifically the circuit breaker and its correlated logging.** Four things
compound in one unit:

1. **It is one of only two mechanisms in the entire design that has never been executed.**
   `DESIGN.md:64-68` names the circuit breaker and the capability-drift diff as the pair that *"sit
   among executed results and borrow their credibility"*. Every other mechanism in this plan has a
   spike behind it. This one has a paragraph.
2. **Its dependency is unselected (B47) and the selection criterion eliminates the obvious
   candidates.** `DESIGN.md:617` requires transitions to be evaluated **on the call path, not from a
   background timer**, because a ContextVar is per-Task and a timer-fired half-open expiry would log
   `request_id=None`. Several Python breaker libraries do exactly that. So the library choice is
   made *by a test that does not exist yet*, against libraries nobody has surveyed. **`9d65cc0`
   removed the worst branch of this** by sanctioning an inline breaker where nothing passes, so the
   unit can no longer stall on the question - but the survey is still unrun and the mechanism is
   still unexecuted, which is what keeps it first on this list.
3. **A High that just came off the must-mitigate table depends on it.** C5-R1 left the table in
   revision 5 (`DESIGN.md:1867`) on the strength of `request_id_var` plus retry and breaker
   logging. If the breaker cannot carry `request_id`, that row reopens - and it reopens *after* the
   design was declared settled.
4. **Its required test is the hardest one in §8.** #13 demands two invocations in parallel, each
   forced to retry, each line attributed. A single-call version **passes against a module global**,
   which is precisely the bug being defended against. This is the one §8 case where a plausible,
   green, wrong test is easy to write by accident.

**What to build first to retire it.** Before U6 - in fact it can run concurrently with U3/U4 as a
throwaway - build **the concurrent correlation harness alone**: two `asyncio` tasks, each setting
`request_id_var`, each driving a fake retry hook and a fake breaker transition hook, asserting each
line matches its own task. It needs no Jobvite client, no tools, no server. It answers two
questions cheaply: does a ContextVar survive the call path each candidate library uses, and does
the test fail when the mechanism is swapped for a module global (the positive control that makes
the test non-vacuous). **Run the library survey against that harness, not against the finished
client.** If nothing passes, the design's sanctioned inline breaker (`DESIGN.md:617`) is taken with
evidence behind it rather than by default - which is exactly what that answer exists to prevent.

**Second, and it is the other half of a pair the design names: the capability-drift diff.**
`DESIGN.md:64-68` names exactly two never-executed mechanisms, and draft 2 gave one of them a full
risk section and the other two passing mentions. It is scheduled in U0 with an explicit
inherited-limit paragraph now: standing a diff up in CI does not execute it, because a diff that has
never seen a real capability change has only ever compared a build to itself. It carries C9-T1, a
Critical/High row, and `UNVERIFIED:` at its point of use. **It cannot be retired by building it** -
its first genuine evidence is a dependency bump that moves the manifest - which is exactly why it
must not read as settled once it is green in a workflow.

**Third: the generated fencing paths** (`DESIGN.md:202-205`). Also unexecuted, also carrying
Criticals (C6-S1, C6-I1), and it has a subtle failure mode - it must generate camelCase Jobvite
paths from snake_case models, which means the models have to *carry* their source path, and the
design does not say how. Retired early by building it in U5 against one small model, which is why
U5 is scoped that way.

---

## 7. Where the design leaves a real choice, and what I recommend

The design settles almost everything. These are the places it genuinely does not, and where I
believe an implementer would otherwise guess:

| Choice | Recommendation | Reasoning |
|---|---|---|
| ~~Circuit-breaker library vs inline~~ | **Settled by the design in `9d65cc0`, no longer a plan recommendation** | `DESIGN.md:617` sanctions the inline breaker as the fallback where no library evaluates transitions on the call path. Run the survey against the U7 harness; take the inline path if nothing passes. Listed here struck through rather than deleted, because a reader of draft 1 will look for it |
| How a model field carries its Jobvite path, for fencing-path generation | **A per-field alias or `json_schema_extra` entry naming the camelCase Jobvite path**, since aliases are needed for the casing normalisation anyway | `DESIGN.md:202-205` requires generation, not a second hand-kept list. Reusing the alias the model already needs means one source, which is the whole point of the clause |
| Logging library | **`loguru`**, named in §3's module layout | Already fixed by the design; recorded here so nobody re-opens it |
| Retry library | **`tenacity`**, named at `DESIGN.md:347` | Same |
| XML parsing | **`defusedxml`**, named at `DESIGN.md:339` | A hardened fallback only, for a route we do not call |
| Where the structural tier lives | **A test module of shape assertions, with no fixture file** | The body cannot ship. A file would either be empty or be a synthetic wearing a structural label, which is the confusion the three tiers exist to prevent |
| First tool | **`search_jobs`** | See [§5](#5-where-the-credential-free-constraint-reorders-the-work), point 3 |

---

## 8. What this plan does NOT cover

Stated plainly, because an unstated omission reads as coverage.

- **I did not read the standards corpus, WITH TWO EXCEPTIONS THAT ARE NAMED RATHER THAN LEFT TO
  CONTRADICT THIS BULLET.** Every `standards/...:line` citation is quoted **from `DESIGN.md` or an
  ADR**, not verified at its source, so if a design citation is wrong this plan repeats it. **The
  exceptions: U7 cites `docs/research/STANDARDS.md:374-375` and `:316` directly** (and says so at its
  point of use), and **draft 7 verified at source every standard it newly cited** - the collection
  guard's `backend/testing.md:138-141` and `devops/quality-gates.md:76-81`, `python.md:35`,
  `tech-stack.md:157`/`:172`, `readme-standard.md:56`, `changelog-standard.md:94`. *Drafts 1-7 stated
  this bullet absolutely while both exceptions were already in the document. The residue is real; the
  word "every" was not.*
- **I did not read `docs/DESIGN.md`'s supporting research in full.** I read `DESIGN.md` end to end,
  **the eleven ADRs that existed at the freeze** - `docs/adr/README.md`, `CREDENTIAL-CHECKLIST.md`
  and the fixtures with them. Of
  `FASTMCP-SPIKE-4.md` (2,354 lines) I read §§1.3, 3.2, 3.3, 10, 10.1, 12, 13.1-13.3, 20.3-20.8 and
  the closing *"What I could NOT verify"*. Of `JOBVITE-CONTRACT.md` I read §§2, 4 and the section
  index; of `JOBVITE-API.md`, §6.1 and the probe map. I did **not** read
  `LICENSING-SURVEY.md`, `DECISIONS.md`, or `data-inventory.md`. **`STANDARDS.md` and
  `docs/reviews/` are NOT blanket-unread** - U7 cites `STANDARDS.md` directly, and this plan cites
  `COMPLIANCE-SPEC-PASS.md` in §4 and §8. What remains unread in `docs/reviews/` is everything beyond
  the three gate scripts' docstrings, this plan's own review rounds, and that pass.
- **THE ADR REGISTER: there were eleven at the freeze and there are now SEVENTEEN, so this plan's
  reading of the ADRs is bounded at 0011.** The six that postdate it, with the only property that
  matters - **Accepted, not merely filed**:

  | ADR | Status | Where this plan stands |
  |---|---|---|
  | 0012 shared inbound constraints | **Proposed** | Gated on in collision 8 and Q5. **Gate is on Accepted**, and it is not |
  | 0013 secret-absence needs a pairing | **Proposed** | This is **Q6**, which asks for an ADR that now exists. Q6 is a disposition, not an open ask |
  | 0014 C8-I1 "empty values" is wrong | **Proposed** | Records U0's secret-class-not-emptiness argument, which this plan makes at length in U0's #3 and never cites by number |
  | 0015 licence gate is a deny-list | **Accepted** | Described correctly in U0's CI paragraph, **never cited by number** |
  | 0016 `setup-uv@v5` not the standard's `@v4` | **Accepted** | Not mentioned. CI-only, U0's file |
  | 0017 unmapped row → internal-error, not `about:blank` | **Proposed, `Type: Design change`** | **Contradicts U2's bullet in this plan.** See below |

  **Two of the six are Accepted and are therefore authority beside the frozen design, and this plan
  cites neither by number.** That is the defect: not that the plan ignores them - substantively it
  tracks 0012, 0013, 0014 and 0015 - but that **§8's bound on what was read was stated as eleven and
  left standing while the register grew by six.** A section whose only job is to stop an unstated
  omission reading as coverage cannot carry a stale count. It is corrected by naming them, **not by
  bumping eleven to seventeen**, which would assert a reading that never happened.
- **ADR-0017 is an OPEN ITEM this plan does not resolve and must not be read as having resolved.**
  It is `Proposed` with `Type: Design change` and it argues the unmapped-exception row should be
  `internal-error` rather than `about:blank`. **U2's bullet in §2 and the shipped
  `src/fast_mcp_jobvite/errors.py` agree with each other today**, so nothing is broken and no unit is
  blocked. But if 0017 is accepted, U2's bullet here and that module both change. **Whoever accepts
  it owns repointing both**; this plan records the dependency rather than pre-empting the ruling.
- **`COMPLIANCE-SPEC.md` HAS now been read in full, and it should never have been on the list above
  in the first place.** Drafts 1-6 grouped it with five background documents as one undifferentiated
  residue, and that framing is what hid it: **it is a 661-line specification of this exact
  repository's obligations** - a CI job table, pinned action versions *"(copy exactly)"*, the licence
  allow-list *"(verbatim)"*, `pyproject.toml` blocks *"ready to paste"*, the per-module coverage
  ruling, the test-discovery guard, the README's required sections in exact order, a do-not-copy
  list, a reviewer checklist. **It is the same subject matter as U0, U11, U13 and half of §4, written
  before all of them and consulted by none of them.** Round 5 named it and the pass ran:
  `docs/reviews/COMPLIANCE-SPEC-PASS.md`, 78 obligations, **41 MET, 7 MISSING, 2 CONTRADICTED, 5 MET
  BY ACCIDENT, 6 SCHEDULED**. It was not a green.
- **Why five review rounds missed it, kept because the mechanism generalises past this document.**
  Every round compared the plan to `DESIGN.md`, because the design is authority and this plan says so
  in its second paragraph. But `DESIGN.md` is itself downstream, and it was written by readers who had
  not opened `COMPLIANCE-SPEC.md` either. **A review that only ever compares two documents to each
  other can confirm consistency and can never find a shared omission** - which is this plan's own
  *"a unit reporting no defect has more probably not looked than found none"*, applied one level up.
  Round 4's best findings came from the built unit and round 5's from the unread upstream document:
  **both are places outside the plan-versus-design axis, and four rounds of reading never left it.**
- **No effort, duration or sequencing-in-time estimate.** The order is a dependency order.
- **No CI runner, Python matrix or workflow YAML is drafted.** U0 names what CI must run, not how.
  Note the spike ran only 3.11.15 and 3.12.3; the design sets `>=3.12`, so 3.13+ is unexercised.
- **No packaging or release process** beyond the pins, the lockfile and the `mcp-name` note. PyPI
  upload, versioning and `mcp-publisher` are untouched; the spike executed nothing from
  `FASTMCP.md` §12(b).
- **No plan for the twelve v2 resources we ship no tools for.** Checklist row 7 names that as the
  highest-yield expansion and it is out of scope.
- ~~`uv lock` reproducing the 72-package resolve~~ - **executed 2026-08-28, Python 3.12.3, uv
  0.11.3: 72 packages in 368ms, with the `fastmcp-slim` causal claim control-tested by removal.**
  Now recorded in U0. Struck through rather than deleted, because draft 2 listed it here.
- **No breaker-library survey was run**, and `circuitbreaker ^2` has not been tested against the
  call-path constraint. U7 names the one experiment; nobody has run it.
- **The threat ids named in §2 are not a coverage map and must not be read as one.** The rows named
  by no unit are **C1-R1, C2-R1, C4-E1, C7-I1, C7-I2 and C8-I1** - stated as a list, with no total, per
  `DESIGN.md:1848`'s own rule that a count in prose beside the thing it counts is a second source of
  truth nothing keeps in step. Most are covered in substance by a §8 case some unit does schedule:
  C8-I1 by #3 in U0, C4-E1 by #22's accept-carrying-false arm in U10, C7-I1 by #5 in U3. The two
  that were genuinely thin now have homes - C9-T1 in U0's inherited-limit paragraph and in §6, and
  C5-E1's ceiling in U13 - and are therefore **not** on the list above. **Draft 4's version of this
  bullet said "16 ids" and "seven rows", listed C9-T1 and C5-E1 among the unowned, and then named
  their owners four lines later** - a count carried through its own correction, contradicting itself
  inside one paragraph. **What is scheduled against every case is the §8 list, not the threat
  table**, and the plan's coverage claim is only ever the former.

  **`C7-I2` is added by draft 7 and appeared NOWHERE in draft 6's 1,543 lines** - not on this list,
  not in a unit, not once. That is worse than the ids that are here: the frozen design puts it on the
  *"Mitigate before production release"* list at `DESIGN.md:1881-1882` beside C3-I1, C6-D1 and C8-R1,
  and the plan carries the other three by name and with care - C3-I1 and C6-D1 in U1, U6 and Q1;
  C8-R1 in Q3, which explicitly declines to specify a mitigation and says so. **C7-I2 was dropped
  rather than declined**, so a reader got three tracked rows and no signal a fourth existed, from a
  sentence claiming to enumerate. It does not block implementation - the *"must mitigate before
  implementation proceeds"* table at `DESIGN.md:1846` is genuinely empty and that is verified - but
  the enumeration claimed a completeness it did not have.

  **Its disposition is Q3's, and this plan declines to specify it for the same reason.** `:1749`
  rates it Medium/`residual` and its action is *"State where the log goes, who can read it, and how
  long it is kept"*; `:1868` accepts it *"only until C7-I2's action is taken"*, adding that if the
  destination is a developer's local disk this is minor and if it is shipped anywhere it is not, and
  **nothing currently says which**. That is a deployment decision, not a code change: it belongs in
  **U13's deployment section beside the read-only-key requirement**, and specifying an unspecified
  mitigation is not a plan's job. Changing the design's answer would be an ADR.

**What was verified rather than asserted, and re-run at HEAD for draft 3.** All three gates: the
coupling gate exits 0, the controls harness exits 0 with every control firing and a clean post-run
re-check, and the sweep exits 0 with **0 escapes are holes**. The two-arm mutation behind
[Q2](#q2---answered-and-the-residual-has-since-landed) was run, not assumed. The §8 case list, its
25 line anchors, and every `§8 #n` reference in §2 were **generated from `DESIGN.md` and
cross-checked subject by subject** - all 25 cases have exactly one owning unit, except #16, whose
four arms are split between U5 and U10 by design. #5 is owned by U3 and **extended** to the
candidate path by U8, which is an additional assertion on the same case rather than a second owner. The fifteen-variable configuration set was
**diffed** between `.env.example` and `DESIGN.md` rather than counted, and the six secret-class
variables behind U0's #3 assertion were read off the committed file.

Draft 1 parked the gates here as unverified; they were cheap, and this list is for what cannot be
settled, not for what was not attempted.

**Re-run for draft 9, at `94330db`, because the tree keeps moving and a measurement is worth only the
SHA it was taken at.** `check-coupling.py` exit 0, 60 STRIDE rows, 17 Critical/High, 23 naming a §8
case; `check-coupling-controls.py` exit 0, **34/34 fired**, post-run re-check still green;
`check-coupling-sweep.py` exit 0, **0 escapes are holes**; `check-obligations.py` **28 mappings, 21
anchors verified, 7 recorded absent** - red on exactly the two anchors this draft's own rewrite
moved, reported below rather than repointed; `check-obligations.py --controls` exit 0, **9/9
fired**, clean post-run re-check; `check-plan-measurements.py` exit 0, **all four PASS**;
`scripts/check-u0-test-controls.sh` **11/11**; `scripts/check-u15-gate-controls.sh` **15/15** with a
clean post-run re-check; `uv run --frozen pytest -q` → **127 passed, 2 deselected, 0 skipped**.

*This draft ran the U0 controls harness at `ff9461a` and found it **aborting before a single control
fired** - "the unmutated copy is already red" - so the honest reading there was **0/11, not the
11/11 rounds 6 and 7 both correctly recorded** at a SHA before `9ca76fe`. `d48c112` has since fixed
it, and the amendment table above carries the diagnosis. The point that survives the fix: **`ci.yml`
gates on that harness, so it was a red build nobody had looked at, and it was found by running the
script rather than by reading anything.***

**The suite's trajectory is the number worth carrying, not any single reading:** round 5 measured 17
at `299cf8b`, draft 7 measured 56 at `ff0bbdf`, draft 8 measured 90 at `b7fd35d`, and this is 127 -
**the deselected count held at 2 and skips held at 0 throughout**, which is the property the
zero-skip rule actually asserts. *Draft 7 pinned this block to `ff0bbdf` and said the tree had moved
"seven" commits; it had moved five, and by the time anyone read the sentence it was six. The count is
dropped here in favour of the SHA, which is checkable.*

**The four measurements this plan rests decisions on are no longer described here; they are RUN.**
`python3 docs/reviews/check-plan-measurements.py` re-executes all four, each with a treatment arm
that must fail and a control arm that must pass, and exits non-zero when a claim stops reproducing.
At `94330db`: **M1 PASS** (`pytest_plugins` loads in a non-rootdir conftest under `-W error`, with
the unregistered control failing as required), **M2 PASS** (a per-directory conftest fixture is
invisible to a sibling directory, and visible in its own - so §4's rejection holds), **M3 PASS**
(adding a dependency breaks `test_manifest.py`'s set-equality; unmutated satisfies it), **M4 PASS**
- *it was the harness's single `KNOWN_OPEN` entry, documenting collision 11 rather than tolerating
it, and `1e67f9c` closed the defect, so the open set is now empty.* **An entry in `KNOWN_OPEN` means
"known broken", never "expected to fail forever": a probe that stays open is a comment with a test
harness attached.** Rounds 6 and 7 each re-ran some of these by hand and reproduced them;
**the script is what makes that survive a reviewer who does not think of it, and since `ff9461a` it
runs in `ci.yml`'s `design-gates` job, so it survives a reviewer who is never dispatched at all.** Round 6 also probed a case §4 does not require: registration works
**without** `tests/fixtures/__init__.py`, so the mechanism is more permissive than §4 claims. **Each `DESIGN.md` line cited by anything draft 7 or 8 touched was
re-derived by `grep -n` on the quoted fragment against `git show 135c3ac:docs/DESIGN.md`, never off
the working tree**, and `C7-I2`'s three anchors were matched by row id at line start; round 6
subject-verified 15 of them at source and found 15/15 on subject.

---

## 9. Questions for the design

Draft 1 raised four; `9d65cc0` answered three; `8814d69` answered the fourth open one raised by the
review. **All five below are dispositions rather than asks, except Q3 and Q5, which are open.** The
answers are folded into the units above rather than restated here.

Nothing here is worked around in the plan. The design is one procedural step from freeze; after
that, each of these needs a numbered ADR carrying a `Type:` field.

### Q1 - answered, U1 unblocked

`JOBVITE_MAX_RESULTS` default **50** and `JOBVITE_OUTBOUND_RATE_LIMIT` default **6/min**, both in
`.env.example` (`DESIGN.md:1549-1564`). U1 enumerates the full configuration set; U6 and U7 consume
the values and each says at the point of use that **6/min is a conservative guess and not a vendor
figure**, per `:1525-1532`.

**Two things the plan carries forward rather than treating as closed.** `DESIGN.md:1584-1585` says
what closed is B15's *blocking* half and that whether either default is right *"no amount of
specification settles and only a live tenant can"*. And **C3-I1 and C6-D1 still read `unmitigated
(B15)`** (`:1695`, `:1738`) and remain on the mitigate-before-production-release list (`:1830`).
Naming a variable did not mitigate those rows, and this plan does not let an implementer read a
default in `.env.example` and conclude otherwise.

### Q2 - answered, and the residual has since landed

**Answered.** The §7.4 shutdown requirement is now §8 case **#18** (`DESIGN.md:1340-1346`). It
asserts the **teardown side effect** rather than the exit code, which is a better assertion than the
one draft 1 scheduled - a process that dies uncleanly can still exit 0. U1 follows the case.

**The measurement draft 2 made, kept here because it is the evidence and not the ask.** Two arms
against temp copies of `DESIGN.md`, both confirmed non-identical to source so neither is vacuous:

| Arm | Mutation | `check-coupling.py` |
|---|---|---|
| Subject | delete case #18, the SIGTERM bullet | **exit 0 - the gate did not notice** |
| Positive control | delete case #1, the 200-with-401 trap, which C5-S1 names | **non-zero - caught** |

The gate resolves §11 row → §8 case and not the reverse, so a case no row names is an orphan and
deleting it is invisible.

**Landed at `cc94459`; nothing here remains open.** `check-coupling.py` now carries a 35-line block
labelled `2a-ter. EVERY §8 CASE HAS AN OWNER (GATE-2)` (`check-coupling.py:305`), requiring every
§8 case to be named by a §11 row or to cite a B-number or section as its owner. `DESIGN.md:1344`
records the same measured residual in case #18's own bullet, in the same terms this plan reached
independently: **GATE-2 stops a case's justification being quietly stripped, and it does not make
deletion visible.** Only a §11 row naming a case does that, and no threat row models a resource leak
on shutdown.

**Re-derived at HEAD rather than carried forward:** 25 cases, 18 distinct `§8:` references in §11,
and the orphan set is unchanged at **seven** - #12, #16, #17, #18, #21, #23 and #24. That is the
population GATE-2 now addresses. **An agent reading draft 2's version of this section would have
filed work that is done**, which is why it is rewritten in place rather than appended to.

### Q3 - stands, and that is the correct outcome

C8-R1, startup configuration logging, remains `unmitigated` (`DESIGN.md:1810`) and on the
mitigate-before-production-release list. The plan adds no startup log line, because specifying an
unspecified mitigation is not a plan's job and the ADR-0011 interaction is unresolved. Carried, not
worked around.

### Q4 - answered, U7 unblocked

`DESIGN.md:617` now sanctions an inline breaker in `services/jobvite_client.py` where no library
evaluates transitions on the call path. U7 states the survey-then-inline procedure and the §7
recommendation row is struck through, since it is the design's decision rather than the plan's.
The throwaway concurrent-correlation harness is retained as U7's risk-retirement step.

### Q5 - answered and landed: input models live beside their tools

**Landed in the frozen design.** `DESIGN.md:289-291` now reads:

```
  tools/candidates.py         search_candidates, get_candidate, create_candidate; their input models
  tools/jobs.py               search_jobs, get_job_feed; their input models
  models/                     allow-listed OUTPUT models, one per tool; no input model lives here
```

That records what C2-T1 already implied, and it closes the half of this question that was a gap in
the record. **U14 assumes per-tool input ownership.**

**It does not change U14's scheduling, and the reason is worth separating from the ownership
question.** U14 is the sweep proving the inbound set is complete across every tool, so it depends on
U5, U8 and U12 having written their input models - and those models now live in `tools/*.py`, which
those three units own. So U14 still owns no file exclusively and still runs last. **The ownership
question is answered; the dependency is what keeps it out of Wave C**, and draft 3 conflated the
two.

**The other half is NOT landing and must not be planned against.** A shared `utils/constraints.py`
holding the control-character rule and the three structural limits goes to **ADR-0012, after the
freeze** - it is a decision rather than a record, and §3's module block closes by enumerating the
modules this design refuses, so an addition owes a justification. **Until that ADR is ACCEPTED, no
unit here plans a shared constraints module**; U14 is specified against per-tool ownership. Written
down because the duplication is the first thing an implementer would factor out on sight, and because
after the freeze doing it without the ADR is a design change made by whoever happened to notice.

**ADR-0012 was filed `Proposed` (`fcc2341`), and that is exactly how this gate could have been
defeated.** An agent told "until that ADR exists" runs `ls docs/adr/`, sees
`0012-shared-inbound-constraints-module.md`, and builds the module - **discharging the gate by
finding the artifact that records the question, not the one that answers it.** The wording is
corrected here and in collision 8 to gate on **Accepted**.

**It is now Accepted (`a39bd2a`) and the gate is lifted.** The per-tool specification no longer
stands: `DESIGN.md:295,300` at the frozen `c15b138` list the module and require every input model to
import from it, so the shared module is the design, not a licence granted by this paragraph.

*One thing this text can no longer assert, and says so rather than implying it: the earlier wording
was "until **Phil** accepts it". Every commit in this repository carries Phil's git identity,
including those an agent authored, so **authorship does not establish who decided**. What can be
shown is that the status is Accepted and that the frozen design incorporates the module. If the
distinction matters for a future gate, the gate needs a signal git authorship cannot provide.*

### Q6 - §8 #2 asserts an absence with no paired positive in the design

**Open, and it is a plan-level fix today rather than a design change - raised so it can become one.**
`DESIGN.md:1280-1282` shows the design already knows this shape: #4 is *"positive on purpose"*
precisely so #5's absence *"cannot be satisfied by silence"*, and the two are explicitly paired.

**#2 has no such pair.** It asserts a secret never reaches a log record, and against a logger that
is misconfigured and emits nothing it passes. #4 does not cover it: #4 proves the **audit event**
exists, which is a different stream from the `loguru` records #2 is about, and the design's own
blanket positive-control rule (`DESIGN.md:1370-1371`) does not list #2 among the refusal-path cases.
U7's #13 does prove retry log lines exist, but that is four units later than U3.

U3 now carries the pairing as a **plan** decision: #2 is asserted against a log stream proven
non-empty by the same call. That is enough for the implementation. **What an ADR would settle is
whether the design wants the pairing stated where it states the other one**, so a future reader of
§8 sees #2 and #4 as the same construction rather than discovering the asymmetry in a plan.

---

## 10. The review cycle is closed at round 7, and what replaces it

**This is the last draft of this cycle.** Not because the plan is finished - it demonstrably is not,
and §10.1 says why that is the correct state to ship in - but because the reviews stopped being the
instrument that finds things.

### 10.1 The collision count is a floor, and it always was

Every draft that stated a collision count stated one that the next reader falsified, and **every
correction found the next collision**. Derived from the committed objects rather than recited -
`git log --format=%h --reverse -- docs/plans/IMPLEMENTATION-PLAN.md`, then reading line 3 and the
collisions headline out of each:

| Draft | Object | Collisions claimed |
|---|---|---|
| 6 | `299cf8b` | Eight |
| 7 | `80a7fd0` | Nine |
| 8 | `4e5a1b2` | Ten |
| 9 | `40959c8` | Eleven |

Drafts 3, 4 and 5 were never committed to this repository, so their counts - four, five and six -
are carried from §4's own record and **cannot be re-derived here**; that is stated rather than
papered over. **The derivable half of the series is monotone and every step of it was forced by an
outside reader.** Draft 7 wrote *"the next reader will find the tenth"* and round 6 found it; draft 8
predicted an eleventh and round 7 found it **in the next round, on the first look**.

**Draft 9 does not predict a twelfth.** A prediction that has come true twice running is not a
finding, it is a description of the process that produces it, and repeating it a third time buys
nothing. What draft 9 does instead is §4's **standing check**: every unit greps the suite for
assertions that close a set its change grows and **reads the bodies rather than the names**. The
twelfth collision is found by the unit that trips it, on the commit that trips it, which is where it
is cheapest to fix.

### 10.2 Why the cycle closes here: the findings changed kind

**The early rounds ran against a repository with no code in it** - `PLAN-REVIEW-R2.md`'s header
records *"`src/` and `tests/` empty"* - **so their findings could only come from reading, and they
did.** From round 5 onward every High came from the built tree or from a probe run against it, and
rounds 6 and 7 each returned exactly one High of the same species. Meanwhile the defects that
actually cost this project time were found by **attempting to build**:

- **U0** produced the `models/` collision and the CI-plus-manifest pair, neither visible from any
  draft (§4 says so at its own "what the first built unit taught this section" paragraph).
- **U15** produced the finding that the commit-time gates did not exist on a fresh clone, closed at
  `80a7fd0`.
- **U2** landed the first `src/` module beyond `__init__.py` at `6072f5a`, which is what unblocked
  U1's coverage step **in substance** rather than on paper - see the amendment table in U0.
- **Wiring `check-obligations.py` at `ff9461a` turned it red immediately** - five anchors moved,
  three of them into `ci.yml` itself. No review round had found that, and no review round could:
  it did not exist until the wiring existed.
- **`scripts/check-u0-test-controls.sh` was aborting at `ff9461a`, and this draft found it by
  running it** (§8, and the amendment table's `9ca76fe` and `d48c112` rows). Rounds 6 and 7 both
  recorded `11/11` and both were right when they measured; `9ca76fe` broke it afterwards. `ci.yml`
  gates on that harness, so it was **a red build nobody had looked at** - and no amount of reading
  the plan would have surfaced it.

**Another round would find a twelfth collision of the same species, and would not have found any of
the items in that list.** The plan's job now is to be executable.

### 10.3 What replaces the review

Two scripts, both wired into `ci.yml`'s `design-gates` job at `ff9461a`, so what used to depend on
whoever remembered now depends on a failing build:

- **`docs/reviews/check-plan-measurements.py`** re-runs the four measurements this plan rests
  decisions on, each two-armed. A claim that stops reproducing exits non-zero and prints `STALE`.
  Its `KNOWN_OPEN` set is **empty** since `1e67f9c`, and an entry there means *known broken*, never
  *expected to fail forever*.
- **`docs/reviews/check-obligations.py`** (and its `--controls` arm) verifies that every mapping in
  `docs/OBLIGATIONS.md` still resolves **to its subject**, not merely to a line that exists, and
  names the line a drifted subject moved to.

**What they do NOT cover, stated so the green is bounded:**

1. **`check-plan-measurements.py` checks four claims.** Every other number, citation and schedule
   in this document is unguarded. It cannot see a twelfth collision, because a collision is not a
   measurement until somebody writes the probe.
2. **`check-obligations.py` does not judge whether an obligation is MET** - its own docstring says
   so. A green means *"the map has not rotted"*, never *"the repository is conformant"*. Seven of
   its twenty-eight mappings are recorded **absent**, and absent rows assert nothing.
3. **Neither gate reads the plan's prose.** The count-behind-its-own-table defect - four drafts
   running - is invisible to both, which is why §4 now deletes counts rather than maintaining them.
4. **Nothing here runs the workflow jobs.** `links`, CodeQL, TruffleHog, the SBOM emitters and
   `pr-title.yml` are declared-unrun in §8 and remain so, and branch protection is out of tree
   entirely.
5. **A gate wired into CI can still be red without anyone noticing**, which is not hypothetical:
   `ci.yml` runs `scripts/check-u0-test-controls.sh` and gates on it, and that harness aborted from
   `9ca76fe` until `d48c112` - **`git rev-list --count 9ca76fe..d48c112` is five**, and one of those
   five is the commit that wired two *other* controls into the same job. **Wiring a control makes it
   enforceable; it does not make anyone read the run.**

### 10.4 The standing rule for every unit brief

From here, dispatching a unit means its brief carries **all four** of these, and a brief missing any
of them is incomplete:

1. **The collisions that bind ITS files** - copied in, not cited by number. §4's list is long, most
   of it is irrelevant to any one unit, and a unit told to "read §4" reads the headline.
2. **The amputation-harness requirement**: the unit's own tests must be shown able to fail, by
   mutation, in the shape `scripts/check-u0-test-controls.sh` and `scripts/check-u15-gate-controls.sh`
   already use. **A test that has never been seen red has not been seen.**
3. **The standing check from §4**: grep for closed-set assertions the change grows, and **read
   bodies, not names**.
4. **The instruction to expect a design defect.** Every item in §10.2's list above was found by
   building or by running something, and none by reading. A unit that finds one files an ADR
   (`DESIGN.md` is FROZEN at `c15b138` and only a numbered ADR moves it) and reports it - **finding
   one is the expected outcome of building, not evidence that the unit went wrong.**

---

*Draft 9 revised against `PLAN-REVIEW-R7.md` (0C/1H/1M/5L), 2026-08-28. Begun by
`impl-plan-draft7`, which landed the body of it at `40959c8`; completed, re-measured and closed by
`impl-plan-draft9`. Draft 8 answered `PLAN-REVIEW-R6.md` and its author's own audit of draft 7
(`docs/worklogs/PLAN-DRAFT7-SELF-AUDIT.md`). **All three coupling gates, both obligation arms, the
measurements harness and the full suite re-run at `ff9461a`** (§8 carries the readings, including
the one that came back red). Cited against the frozen `docs/DESIGN.md` at `135c3ac`, read from the
git object. `docs/DESIGN.md` was not edited by this draft, and this draft edited no file but this
one.*

*A note on this document's own git history, because a reader will trust the log and the log is
wrong twice. **`4e5a1b2` is titled "Land plan draft 7, with its six known defects held open for
draft 8" and its content is draft 8 with all six applied.** That was corrected forward in
`40959c8`'s message, which states the mislabel and its consequence - a second agent was briefed to
apply round 6 to a document that already had round 6 applied - so it needs no further litigation
here. **But `40959c8` then repeated the shape**: it is titled "Draft 8 final ... at 2,040 lines",
and the object it commits reads `Status: **DRAFT 9**` on its own line 3 and is 2,096 lines
(`git show 40959c8:docs/plans/IMPLEMENTATION-PLAN.md | sed -n 3p` and `| wc -l`). The commit
correcting a mislabelled draft is itself mislabelled, in both the draft number and the line count,
and the line count is a number that was asserted where a command was available. **The lesson is not
"read the status line before committing" - that was the lesson last time and it did not take. It is
that a commit message is prose about an object, and prose about an object decays into a claim about
one:** derive the draft number and the line count from the file being committed, in the same
command that writes the message.*

*The footer read "Draft 6 … `PLAN-REVIEW-R4.md`" through drafts 7 and 8's predecessor, byte-identical,
because a footer is the one line a reviewer reads last and an author never re-reads. It is the
cheapest possible instance of the defect this whole document is organised against: **a record that
describes a state the artifact left two revisions ago, sitting unchallenged because nothing points
at it.***
