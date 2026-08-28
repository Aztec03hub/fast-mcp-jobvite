# fast-mcp-jobvite - Implementation Plan

Status: **DRAFT 6.** Revised against `PLAN-REVIEW-R4.md` (0C / 3H / 5M / 3L). Rounds 1-3 are
answered in drafts 3-5. **U0 is built and merged**, and round 4 is the first review with a shipped
unit to check the plan against.
Written against `docs/DESIGN.md` at **revision 6, FROZEN** at commit `135c3ac` - no open Critical,
High or Medium findings and an empty must-mitigate table (`DESIGN.md:1795`). **The design being
frozen changes what this plan is:** from here only a numbered ADR may change `DESIGN.md`, so a
finding against the design is no longer an edit request - it is an ADR, and every open item below
is written that way.

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
them under a unit that had declined them while `DESIGN.md:1760` names them as a **Critical** row's
mitigation. They are now **U15**.

The Mediums: U5 had no row in any wave table - the "U8 had no wave" defect one unit over, and the
*cause* of the `models/` collision; `DESIGN.md:407` was doing two jobs and was wrong at one of them;
the lane sentence named the wrong pair for the right count, on its fourth revision; the licence gate
landed as a deny-list while the plan still described an allow-list; and no rule covered **reading**
a file another unit is rewriting, which U5 and U6 do concurrently by design.

**Every `DESIGN.md:<line>` citation resolves against the `135c3ac` git object** - the frozen text,
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

**`src/` and `tests/` are empty. Zero files.** Everything below is greenfield.

**There is no CI, and the design now says so once, plainly.** `.github/workflows/` contains exactly
one file, `mirror.yml`, which pushes to the mirror remote. Draft 1 reported this against a design
that used the present tense; `DESIGN.md:1415-1421` now states that **every "CI runs" sentence in
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

**Standing CI up is U0's first act**, before any other work in that unit. From that point "the
gates keep passing" is a machine constraint rather than a habit. All three must run there: the gate
alone is a checker that has only ever passed, which its own docstring names as the failure it
exists to avoid, and the sweep is what proves it can fail without choosing its own subject.

---

## 1. The count that governs the test plan

§8's required-cases list holds **25 bullets**, spanning `DESIGN.md:1220` through `:1306`. I
re-derived this mechanically against `9d65cc0` - extracting every top-level bullet between the
*"Required cases"* header and the *"Transport substitution uses"* paragraph - rather than
incrementing draft 1's 24, because a hand-carried count is the defect this project has spent the
day repairing. The new member is **#18**, the SIGTERM teardown case Q2 added; everything below it
shifted by one.

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

Plus the blanket rule at `DESIGN.md:1319-1320`: **every refusal-path test is paired with a positive
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

`DESIGN.md:1207-1212`. Three tiers, and the split is load-bearing:

- **Recorded** - byte-exact captures of **real Jobvite error transport** (`DESIGN.md:1208`).
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

**The sentence at `DESIGN.md:1214-1215` goes in the test module's own docstring, verbatim in
substance:** a suite passing only against synthetic fixtures proves the client is self-consistent,
not that it speaks Jobvite.

**Sequencing consequence that a naive plan gets backwards:** the structural assertions must be
written **before** the candidate output models (U8), or the models will encode the shape of
fixtures we invented rather than the one success envelope anyone has actually observed. This is the
single clearest place the credential-free constraint reorders the work.

### Zero skips

`DESIGN.md:1185-1205`. CI has zero skips; a skip is a failure. Credential-dependent tests are
excluded **by selection** through a declared marker under `--strict-markers`, and **the excluded
suite is still collected** (`--collect-only`, failing on a collection error). All three properties
land in U0, because every later unit that adds a credentialed arm depends on them existing.

**There are TWO selection markers, not one, and every later unit needs to know the second exists.**
U0 landed a **`network`** marker beside the credential-dependent one, and CI runs the network arm as
its own step. The reason is §8 #11's negative arm: proving the `fastmcp-slim` pin is load-bearing
requires a **real resolve**, while `DESIGN.md:1185` requires the default suite to run with **no
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

**Being implemented now, in parallel, by a separate agent.** U0 is the one unit that does not
depend on the outstanding review findings: its scheduled assertions were confirmed correct in round
2 and its resolve has been executed.

**If the U0 agent's report contradicts anything in THIS U0 SECTION, the report wins** - a unit that
has been built beats a unit that has been described, and this section is corrected from the build.
**This precedence is bounded to this section and never reaches `docs/DESIGN.md`**, which is frozen:
a build that contradicts the design is an ADR, not a correction.

*Draft 4's version of this said only "anything specified below", which round 3 named as the single
sentence most likely to be misread by an agent working alone - "below" bounded to this section is
sensible, "below in this plan" hands one agent precedence over twelve hundred lines, and it had no
floor at all while every other deviation in this document routes through an ADR.*

**Its first act is standing up CI**, because nothing runs there today (`DESIGN.md:1415-1421`) and
every gate below is hand-run until it does. Until the workflow exists, no other unit's verification
means anything durable - it means someone ran something once.

**Builds.** `pyproject.toml` with the verbatim three-pin block and `prerelease = "explicit"`
(`DESIGN.md:1358-1367`); `uv.lock` committed; `[tool.pytest.ini_options]` with
`addopts` carrying `--strict-markers`, the declared `markers` list including the
credential-dependent marker, `asyncio_mode = "auto"`, and coverage `branch = true`
(`DESIGN.md:1190-1191`); **the 80% overall coverage floor**, which is the only one expressible as a
single `fail_under` - **ADR-0010's per-module floors (85% tools, 90% client, 95% `utils/`, 95 line /
90 branch on critical paths) land with the units that create those modules**, and CI's coverage step
stays off until U1 because `src/` holds only `__init__.py` at U0; `.github/workflows/ci.yml`.

CI runs, at minimum: `uv sync --frozen`; lint; format; types; the default suite;
`--collect-only` against the credentialed suite; `python3 docs/reviews/check-coupling.py
docs/DESIGN.md`; `check-coupling-controls.py`; `check-coupling-sweep.py`; `pip-audit` behind
`scripts/check_advisories.py` (U11); CodeQL; TruffleHog with full history depth; SBOM in both
formats from the **frozen** resolve; `pip-licenses` **deny-list on the standard's flag-list, with the allow-list conversion owed to an
ADR** (U0-REPORT D3: `pip-licenses` reports fifteen spellings for six licences, so `--allow-only` on
the standard's five SPDX ids is **red on its first run against a clean tree** - the same
trains-everyone-to-ignore-it failure this plan warns about for `pip-audit`); `fastmcp inspect` emitted and
diffed between builds. **The two commit-time gates are NOT U0's** - U0 declined them and the ruling
is now written down: they are **U15** (`DESIGN.md:1576-1586`), for the reasons that unit states.

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
  `.env.example` carries **no real value** (`DESIGN.md:1222`), meaning no real credential; draft 2
  tightened that into something else. Verified today: the six above are empty, and the list is
  derived from the file rather than remembered.

Plus, all three now running in CI rather than by hand. **What CI asserts is the exit code and the
harness's own *all fired* property, never a literal count** - the controls harness has reported 21,
32 and 34 to three readers in one day, so a hard-coded number turns the harness growing into a red
build. The gate exits 0; the controls harness exits 0 with every control it holds firing and a clean
post-run re-check; the sweep exits 0 with **0 escapes are holes**.

**The resolve is EXECUTED, not inherited, and U0's first act is no longer a risk item.** Draft 2
carried 72 as a figure quoted from `DESIGN.md:1358-1362` and listed reproducing it among what this
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
**3.12.3** against the design's `>=3.12` floor (`DESIGN.md:1353`), git 2.43.0, gh 2.45.0. **Neither
`pyproject.toml` nor `uv.lock` exists in the repo** - correct, and U0 creates both.

---

### U1 - Boot: config, transport selection, TLS refusal, shutdown

**Builds.** `config.py` (pydantic-settings, `SecretStr`, per-enabled-tool required-variable
validation per `DESIGN.md:918-923`, `JOBVITE_TOOLS` allow-list with an unrecognised name as a
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
diffed the two sets rather than counting them, which is the check `DESIGN.md:1495-1501` asks for and
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
- §8 **#18**, on **both transports** (`DESIGN.md:1289-1295`): lifespan teardown runs on SIGTERM,
  asserted by **observing the teardown side effect** - the resource the lifespan opened is released
  - and **not** by the exit code, since a process that dies uncleanly can still exit 0. Where the
  test does resolve a PID (the stdio arm, whose distinctive failure is that the process survives
  teardown entirely, `DESIGN.md:959-961`), resolve the interpreter via `/proc/<pid>/cmdline` rather
  than a wrapper. **Only the stdio arm exercises the `os._exit(0)` half**; the HTTP arm passes on
  teardown alone, which is precisely why a single-transport test would have shipped this bug.
- Config fail-fast: per-tool required-variable matrix asserted row by row, including the negative -
  a deployment enabling only `search_candidates` must **not** be forced to supply
  `JOBVITE_COMPANY_ID`.
- An unrecognised `JOBVITE_TOOLS` name fails startup; positive control - a recognised name starts.
- `JOBVITE_ENABLE_WRITES=true` with `JOBVITE_TOOLS` unset does **not** register the write.

**Inherited limits, not quietly resolved.** `DESIGN.md:982-990` states two: the composed
handler-plus-`os._exit` snippet **has never been run end to end on HTTP**, and **PID 1 was never
simulated**. The test above is what closes both, and until it runs green the plan carries them as
open. §12 item 5 additionally records that shutdown depends on a uvicorn implementation detail.

**Unblocked by `9d65cc0` - draft 1 had this unit stalled.** `DESIGN.md:1498-1513` now names both
settings, and both are in `.env.example`, so `config.py` can enumerate the full set:

| Variable | Default | What the plan may say about it |
|---|---|---|
| `JOBVITE_MAX_RESULTS` | **50** | Not arbitrary. 50 is the figure already in the caller-facing string `showing 50 of 1,240` used by §4.5 and C3-I1, so any other value would make two parts of the document disagree about a number a caller reads |
| `JOBVITE_OUTBOUND_RATE_LIMIT` | **6** per minute | **A conservative guess, not a vendor figure.** Jobvite documents no numeric limit at all - its only stated envelope is prose. **Checklist row 9 is what replaces this with an observation** |

**Neither default is verified, and the plan does not describe them as such.** `DESIGN.md:1533-1534`
says it directly: what B15 closed is the *blocking* half - the names exist and the template is
complete - and **whether either default is right remains open and only a live tenant can settle
it.** U6 and U7 restate this at the point they consume the values.

**And the threat-model rows did not move.** C3-I1 (`DESIGN.md:1695`) and C6-D1 (`:1738`) still read
`unmitigated (B15)`, and both are still on the mitigate-before-production-release list (`:1830`).
Naming a variable is not mitigating the row. An implementer who reads `.env.example`, finds a
default, and treats C3-I1 as closed would be making exactly the substitution this design keeps
catching - so the plan carries both rows as open into production-release readiness.

---

### U2 - The error contract and the correlation ContextVar

**Builds.** `errors.py` - the exception hierarchy and RFC 9457 problem construction, with `type`
and `status` taken **from the registry at `error-contract.md:96-108`**, never from Jobvite
(`DESIGN.md:496-519`). `utils/correlation.py` - a single `ContextVar[str | None]` named
**`request_id_var`**, that name mandated verbatim by `ai/tool-calling.md:173-175`
(`DESIGN.md:589`).

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
  (`DESIGN.md:491`).
- Problem objects are **returned, never raised** - the property `DESIGN.md:523-525` says makes them
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
`DESIGN.md:689-705`); `utils/redaction.py` **secret redaction only** - the fencing half is U8.

**Depends on.** U2.

**Verified by.**

- §8 **#4** (positive) and **#5** (absence), **as a pair** - `DESIGN.md:1229-1232` requires them
  paired so neither can be satisfied by silence. #5 asserts against the event #4 proves exists.
- §8 **#2**: a secret never reaches a log record, **including the whole `jobFeed` URL**; `sc=`
  redacted at the one enforcement point - **asserted against a log stream proven non-empty**: the
  same call emits a log record carrying the request's non-secret attributes, and the `sc=` value is
  absent from *that record*. Against a misconfigured logger emitting nothing, the absence alone
  passes. The design solved this exact shape for the audit stream by pairing #4 with #5
  (`DESIGN.md:1229-1231`); **#2 has no such pair in the design and #4 does not supply one** - #4
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
  (`DESIGN.md:676-681` - the implementer error this row exists to prevent).

**File-boundary note.** `utils/redaction.py` is shared with U8. See [§4](#4-what-can-run-in-parallel).

---

### U4 - Jobvite client, part 1: auth and the error-detection rule

**Builds.** `services/jobvite_client.py` - `httpx2` client construction, v2 header auth
(`x-jvi-api`, `x-jvi-sc`), the v1 `jobFeed` query-parameter exception with its URL classified
sensitive, and **the invariant**: a response is successful only if the body carries no
`status.code >= 400` **and** the HTTP status is below 400 - both, every call
(`DESIGN.md:326-327`). Three error encodings handled: JSON status envelope, plain text with no
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
- No cookie jar (`JOBVITE-CONTRACT.md:2.3` - the `AWSALBAPP-*` values are the literal `_remove_`).

Transport substitution is `httpx2`'s built-in `MockTransport` (`DESIGN.md:1308-1309`, ADR-0007). No
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
  the output model. `DESIGN.md:1281-1283` is explicit that asserting on the `ToolResult` object
  would pass while the wire carried nothing.
- **U5 adds the FIRST credentialed arm, and tightens CI's credentialed-collect step from
  `exit 0 or 5` to `exit 0 with a non-zero count`.** U0 left it accepting 5 because it cannot tell
  *"the suite is empty"* from *"the suite is healthy"*, and recorded that the first unit adding an
  arm must tighten it - **"the first unit adding an arm" is not the name of a unit, and this is that
  unit.** Per the shared-file rule in §4, this is U5's one edit to `ci.yml` and it touches nothing
  else.
- §8 **#16, error arm** - the `error_auth_200_body401.json` call in the bullet above returns a
  problem object whose **own `request_id` member** matches the audit event's id, asserted on the
  wire. The error half travels in the problem object rather than in `_meta`
  (`DESIGN.md:617-623` distinguishes them), so this is a different assertion from the read arm
  rather than a repetition of it. **Draft 2 scheduled this arm in no unit at all.** With it, all
  four arms of #16 have an owner: read and error here, write and audit-failure-warning in U10.
- The result cap fires and reports `showing N of total` rather than truncating.
- Every field on the job model has a fencing decision; deleting a decision fails the suite.
- The server starts on stdio and on HTTP and lists exactly the enabled tools.

---

### U6 - Pagination

**Builds.** In `services/jobvite_client.py`: offset paging with **every scan starting at
`start=0`** (`DESIGN.md:449`), page cap 500 on v2 and 1000 on `/v1/jobFeed`, the per-scan seen-set
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
  (`DESIGN.md:459-462`).
- Termination on a short page; a `total` that lies does not terminate or extend the loop.
- The completeness check fires on an exhaustive scan with a missing record, and **does not fire** on
  a capped call - the capped call reports `showing 50 of 1,240` and is not logged as an anomaly
  (`DESIGN.md:463-471`). Both arms are required; wiring the check to every call is the failure this
  bullet exists to prevent.
- The structural assertion that `start=0` is accepted and returns records
  (`JOBVITE-API.md:399`).

**The result cap is now named:** `JOBVITE_MAX_RESULTS`, default **50** (`DESIGN.md:1521-1524`), and
it is the configured half of `min(transport_cap, configured_result_cap)`. 50 was chosen to agree
with the `showing 50 of 1,240` string a caller already reads, which makes it internally consistent
and **not** a measurement of anything. **U5 built the in-tool half; U6 adds the transport half and
the `min()` that composes them, and does not re-implement U5's reporting string.** It is one
behaviour split across two files, which is why neither unit may assume it owns all of it.

**Inherited ceiling.** Whether `start` is 0- or 1-based is unresolved as a fact about Jobvite
(§12 item 2), and whether 500 is a real server limit is unobserved. Checklist rows 2 and 3 settle
both. **C3-I1 and C6-D1 remain `unmitigated (B15)`** in the threat model even now the variable has
a name (`DESIGN.md:1695`, `:1738`), because what closed was the naming, not the exposure. The plan
ships the design's base-agnostic scan and does **not** treat any of these as established.

---

### U7 - Resilience: timeouts, retry, breaker, and correlated logging

**Builds.** Ordered timeout → retry → circuit breaker, all inside
`services/jobvite_client.py`: explicit per-phase timeouts (no SDK default, no single scalar);
`tenacity` with jitter for connection errors, timeouts and 5xx only; a **configured total outbound
budget** bounding all attempts for one tool invocation (`DESIGN.md:367-369`);
`create_candidate` excluded from retry **by construction**; one breaker for Jobvite with **4xx
excluded from tripping it**; open-breaker and outage both `/problems/service-unavailable` **503**
distinguished by `detail` plus a `retry_after` hint; a `429` retried then mapped to 503, honouring
`Retry-After`.

**Depends on.** U6 (same file). **This is the riskiest unit** - see [§6](#6-the-riskiest-unit).

**Verified by.**

- §8 **#13**, the concurrent arm: **two invocations driven in parallel**, each forced to retry, each
  log line matched to the invocation that produced it. `DESIGN.md:1262-1264` states that a
  single-call version passes against a module global, which is the bug `request_id_var` exists to
  prevent - **so the concurrent arm is the case and a single call does not satisfy it.** The same
  case asserts **no URL** appears in a retry line.
- Every breaker transition logs its direction (`closed->open`, `open->half_open`,
  `half_open->closed`), the triggering counter, and `request_id`.
- §8 **#23**: a 4xx does not trip the breaker. Positive control: repeated 5xx does trip it.
- §8 **`create_candidate` not retrying on timeout** (#21), asserted with a **row counter** as the
  control, not by inspecting configuration - the spike measured one call producing **four rows**
  (`DESIGN.md:347`), so the assertion is the row count.
- The total outbound budget bounds a slow upstream into a typed 503 rather than an unbounded wait.
- The self-throttle honours `JOBVITE_OUTBOUND_RATE_LIMIT`, default **6 requests per minute**
  (`DESIGN.md:1525-1532`). **Say what it is at the point it is used: a conservative guess, not a
  vendor figure.** Jobvite documents no numeric limit at all, only the prose envelope *call it on an
  as-needed basis, and anything more frequent than once a day must be filtered*. **Checklist row 9
  is what replaces the guess with an observation**, and row 9 carries its own safety condition -
  run it last, stop at the first `429`, never confirm a limit by exceeding it repeatedly. The README
  states the vendor envelope, because a user syncing hourly is outside what Jobvite documents.

**The library constraint that shapes this unit, and the fallback the design now sanctions.**
`DESIGN.md:602` requires the breaker to **evaluate transitions on the call path, not from a
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
the inline breaker of `DESIGN.md:602` is taken with evidence rather than by preference. If it passes,
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
  Draft 3 applied `DESIGN.md:1319-1320`'s blanket rule to U10 and U14 and skipped U8.
- §8 **#6**: EEO fields never appear in any tool result, **asserted against the output models**, not
  by inspection. C6-I1, Critical.
- §8 **#19**: fencing, including content that tries to **close its own fence** - the red-team cases
  are merge-gating (`DESIGN.md:732`). `candidate_list_injection.json` is the seed; it is not
  sufficient on its own.
- §8 **#20**: an unknown non-string field is dropped, not stringified.
- §8 **#24**: the `eId`/`EId` casing asymmetry pinned, so a later refactor cannot tidy it into a bug.
- §8 **#5** extended to the candidate path: PII reaches the audit *path* by construction and none of
  it is emitted in the clear.
- Path-keyed, not name-keyed: a test where `title` and `eId` appear at two depths and are decided
  differently - name-keying would collide (`DESIGN.md:725-727`).
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
  excluded for a measured reason (ADR-0004, `DESIGN.md:1133-1158`) and re-adding one is a silent
  regression.
- **Positive control for that absence assertion, and it is what gives the assertion meaning: the
  three adopted middleware are present in the constructed stack**, and `StructuredLoggingMiddleware`
  is constructed with `include_payloads=False` (C2-I1, `DESIGN.md:1681`). Five absences asserted
  against a stack never proven non-empty cannot tell *"excluded"* from *"no middleware at all"*.
  Draft 3 positively verified only `RateLimitingMiddleware`, leaving `Timing` and
  `StructuredLogging` - including the `include_payloads` value a threat row exists for - with no
  assertion at all.

**Inherited limits, carried not resolved.** Burst sizing is `desired_calls + 2` where the `2` is
**FastMCP's own client's connect sequence, not a protocol constant**, and under-provisions a
heavier client (`DESIGN.md:389-397`). Every limiter measurement was **sequential and single-client**
(ADR-0002); behaviour under simultaneous callers is unverified, and `limiters.clear()` was never
tested under load. The limiter has **never been exercised on stdio** at all - `DESIGN.md:407-410`
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
- **Positive control for #22 and #25, required by `DESIGN.md:1319-1320` and load-bearing here: an
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
  it. Without a counter the refusal arms assert nothing; this is the §16.3 lesson the spike records
  against itself.

**What may never be claimed.** *"The server requires an approval response from the host and refuses
to write without one"* - **never** *"a human approved this."* C4-S1 is a **High residual** and is
not mitigable server-side. An abandoned approval **hangs the call** with no server-side bound
(C4-D1). An authorised write can still be made twice (C4-D2); the idempotency-key remedy was
evaluated and **cannot be built** because nothing establishes Jobvite accepts one (B108,
`DESIGN.md:245-268`). None of these becomes a plan item; all three are disclosed in the README.

---

### U11 - `scripts/check_advisories.py`

**Builds.** The file `DESIGN.md:1465-1471` names as **the advisory-expiry owner** and which does not
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

**The policy this enforces is four ordered steps** (`DESIGN.md:1454-1473`) and step 1 -
reachability - is **human judgement written down, not a tool output**. The script owns steps 3 and
4 only.

---

### U15 - The two commit-time gates

**Builds.** The two gates of `DESIGN.md:1576-1586`, both of which the design says exceed the
standard deliberately: **secret scanning pre-commit**, not only in CI, because on a public remote a
pushed secret is compromised the instant it lands; and the **committed-file-type gate** -
allowlist-first, extension denylist, magic-number sniffing, NUL-byte backstop, fail-closed, with
overrides only via an allowlist entry in the same commit so the exception is reviewable in the diff.

**Depends on.** U0 only. **Parallel with U11 throughout**, and it touches no file any other unit
writes.

**Why it is a unit and not a bullet in U0.** Draft 5 listed both gates inside U0's CI paragraph.
**U0 declined them and asked for a ruling, correctly**: they are not a CI step, they are
allowlist-first magic-number sniffing with a NUL backstop and a fail-closed default - real software
with its own test surface, in a repository where **`DESIGN.md:1760` names these two gates as the
mitigation for C8-I1, a Critical row.** A control carrying a Critical, whose own design admits
(`DESIGN.md:1585-1586`) that it *"does nothing about confidential prose pasted into Markdown, which
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
- **The stated ceiling is carried, not quietly dropped:** `DESIGN.md:1584-1586` says this gate stops
  a *file* of the wrong type and does nothing about confidential prose pasted into Markdown, which
  is the incident that actually occurred. Review and `JOBVITE-API.md` §0.2 cover that, and no test
  here may be written as though the gate closed it.

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
(`DESIGN.md:428`, *"Page cap **500** on v2, **1000** on `/v1/jobFeed`"*), and §4 gives
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

**Builds.** The README, which `DESIGN.md:1483-1490` **deliberately withholds until now** because a
README describing an unbuilt system is a false claim in the present tense. All fourteen sections
with **headings matching exactly**; the Configuration table **checked against `.env.example`**
rather than hand-maintained; an `mcp-name:` string **added before the first PyPI upload, not after**;
the `com.evolvconsulting.fast-mcp-jobvite/requestId` key documented, since a caller cannot guess it
and an id a caller cannot reach discharges nothing; the **six behaviours** of `:1539-1555`; the
read-only-key requirement in the deployment section; and a **credential-free Quickstart in full,
exercised by CI on every merge** - install, start the server, list tools. `readme-standard.md:83`
forbids a Quickstart step requiring credentials, so anything needing a Jobvite key belongs in
Configuration and Usage.

**Depends on.** U1-U12.

**Verified by.** §8 **#14**'s README arm goes **live** here - `DESIGN.md:1267-1270` requires it
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

**All three carry the blanket positive control of `DESIGN.md:1319-1320`**, and draft 2 stated it for
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
U0  skeleton / pins / markers / CI
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
 └── U15 the two commit-time gates                                (independent throughout)

     U13 README                                                  (needs U0-U12)
```

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
| `.github/workflows/ci.yml` | **U0 owns the file.** It landed three steps commented out and addressed by name. **U1, U11 and U13 each enable exactly the step naming their unit and touch nothing else** - U11 the advisory audit, U1 the coverage floors and the capability-drift diff, U13 the Quickstart. U5 additionally tightens the credentialed-collect step (L3 below). The blocks are non-adjacent by construction, so the edits are disjoint line ranges |
| `pyproject.toml` | **U0 owns the file.** U11 edits rows inside the advisory-ignore table U0 landed empty; **U1 adds `[project.scripts]`**, which U0 deliberately omitted because it names a function U1 writes; U13 adds `readme`. Same rule: touch your own key, nothing else |

**Enabling a commented step is a write.** Draft 5 called U1 and U11 *"genuinely disjoint"* in this
wave; they are not, and neither is U13. The mechanism is the one this section already invented for
U11's `pyproject.toml` table - **U0 lands the container, each later unit edits only its own row** -
extended to the workflow, where draft 5 had no mechanism at all. If that is judged too fine-grained
to trust to concurrent agents, the fallback is to sequence U1 and U11, which costs one lane out of
three. **The row is taken over the sequencing**, because the edits are non-overlapping line ranges
by construction rather than by care - but it is stated either way, because otherwise the first two
agents to land find out by conflict.

**Genuinely disjoint.** The one shared file is `pyproject.toml`: U0 writes it, U11 appends one
table. Have U0 land the empty table so U11 only edits rows inside it, or U11 waits for U0's commit.

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

**Eight collisions to plan around, all real.** The count has now been understated three times -
four in draft 3, five in draft 4, six in draft 5 - and every correction found the next one, so treat
this number as the current floor rather than as a ceiling. **Collisions 7 and 8 were both invisible
from the plan and visible only from the build**, which is the pattern worth carrying: the ownership
model is drawn on source modules, and the surfaces that actually collide are the ones nobody
classified as code:

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
   `DESIGN.md:1315-1317` names both, and ADR-0010 puts `utils/` at the standard's **95%** because of
   it. Two agents cannot both own it. Sequence U3 → U8, or give one agent both halves.
3. **U8 and U10 both write `tools/candidates.py`.** Sequential, U8 then U10.
4. **The `/v1/jobFeed` page cap of 1000 has one home and two claimants.** `DESIGN.md:428` puts it in
   §4.5, the client layer - *"Page cap **500** on v2, **1000** on `/v1/jobFeed`"* - so it lives in
   `services/jobvite_client.py`, **U6's file, which U12 may only read.** It is U6's outright; U12 consumes it. This is the result cap's sibling, and draft 3
   fixed one and not the other.
5. **Tool registration has no stated home and four claimants - and this is the one that breaks
   first.** U5, U8, U10 and U12 each add a tool that must be registered, and `create_candidate`'s
   registration is conditional on the `JOBVITE_ENABLE_WRITES` **and** `JOBVITE_TOOLS` conjunction
   (`DESIGN.md:903-907`). U8, U12 and U9 overlap in time by the table above, so if registration
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
7. **`.github/workflows/ci.yml` and `pyproject.toml` are written by four units between them and
   appeared in no ownership table.** U0 owns both; U1, U11, U13 and U5 each edit only the block or
   key naming their unit. See the Wave A shared-file table above. **Enabling a commented CI step is
   a write**, and draft 5 called two units that must both do it *"genuinely disjoint"*.
8. **U14's input-model checks share `tools/*.py` with the three units that write them.**
   `DESIGN.md:289-291` puts input models beside their tools, so U14's subject lives in files U5, U8
   and U12 own. It is **sequenced last rather than parallelised**. See
   [Q5](#q5---answered-and-landed-input-models-live-beside-their-tools), and note that **no unit
   plans a shared `utils/constraints.py`** until ADR-0012 exists.

**Read this from the earliest-start column rather than from this sentence: Wave C is two lanes at
U4-landing - U5 and U6→U7 - stays two at U5-landing as U5 hands off to U9, and widens to FOUR when
U5 and U6 have both completed, as U8 and U12 unblock together.** Draft 5 said *"two lanes at
U4/U5-landing - U6→U7 and U9"*, naming a pair that fits only the second moment: the table gives U9
an earliest start of U5, so at U4-landing U9 cannot run. **This is the fourth revision of this
sentence**, which is itself the argument for deriving it from the column. Neither waits for U7. U8 and U12 have disjoint write
sets and may run concurrently with each other and with U7 and U9 - **which holds only because
collision 6 below puts registration in each unit's own `tools/*.py` rather than in `server.py`.**
If registration were centralised, U8, U12 and U9 would be three units in one file and this
four-lane claim would be wrong.

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
and not of U0.** Two of the eight collisions above - `models/` and the CI-plus-manifest pair - were
**invisible from the plan and visible only from the build**. The reason is structural: **this
ownership model is drawn on source modules, and the surfaces that actually collide are the ones
nobody classified as code.** U0's deferrals are all future writes back into U0's own files, and a
table of "who owns which module" cannot express *"U11 later edits a file U0 owns"* - which is why
the shared-file table above exists as a second kind of row. **`tests/conftest.py` is the same shape
waiting**: U0 owns it, every later unit adds fixtures to it, and no row here says so yet.

**A rule that costs nothing and prevents the failure that actually happens here:** no agent runs
`git stash`, and no agent switches branches on a tree another agent is working. If two units must
overlap in time on the same file, they get separate worktrees pinned to a SHA, not turns in one
checkout.

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
   (`DESIGN.md:1202-1206`). Without this the excluded suite rots invisibly for the whole project.

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
   candidates.** `DESIGN.md:602` requires transitions to be evaluated **on the call path, not from a
   background timer**, because a ContextVar is per-Task and a timer-fired half-open expiry would log
   `request_id=None`. Several Python breaker libraries do exactly that. So the library choice is
   made *by a test that does not exist yet*, against libraries nobody has surveyed. **`9d65cc0`
   removed the worst branch of this** by sanctioning an inline breaker where nothing passes, so the
   unit can no longer stall on the question - but the survey is still unrun and the mechanism is
   still unexecuted, which is what keeps it first on this list.
3. **A High that just came off the must-mitigate table depends on it.** C5-R1 left the table in
   revision 5 (`DESIGN.md:1816`) on the strength of `request_id_var` plus retry and breaker
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
client.** If nothing passes, the design's sanctioned inline breaker (`DESIGN.md:602`) is taken with
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
| ~~Circuit-breaker library vs inline~~ | **Settled by the design in `9d65cc0`, no longer a plan recommendation** | `DESIGN.md:602` sanctions the inline breaker as the fallback where no library evaluates transitions on the call path. Run the survey against the U7 harness; take the inline path if nothing passes. Listed here struck through rather than deleted, because a reader of draft 1 will look for it |
| How a model field carries its Jobvite path, for fencing-path generation | **A per-field alias or `json_schema_extra` entry naming the camelCase Jobvite path**, since aliases are needed for the casing normalisation anyway | `DESIGN.md:202-205` requires generation, not a second hand-kept list. Reusing the alias the model already needs means one source, which is the whole point of the clause |
| Logging library | **`loguru`**, named in §3's module layout | Already fixed by the design; recorded here so nobody re-opens it |
| Retry library | **`tenacity`**, named at `DESIGN.md:341` | Same |
| XML parsing | **`defusedxml`**, named at `DESIGN.md:333` | A hardened fallback only, for a route we do not call |
| Where the structural tier lives | **A test module of shape assertions, with no fixture file** | The body cannot ship. A file would either be empty or be a synthetic wearing a structural label, which is the confusion the three tiers exist to prevent |
| First tool | **`search_jobs`** | See [§5](#5-where-the-credential-free-constraint-reorders-the-work), point 3 |

---

## 8. What this plan does NOT cover

Stated plainly, because an unstated omission reads as coverage.

- **I did not read the standards corpus.** Every `standards/...:line` citation in this plan is
  quoted **from `DESIGN.md` or an ADR**, not verified at its source in
  `evolv-coder-standards/standards/`. If a design citation is wrong, this plan repeats it.
- **I did not read `docs/DESIGN.md`'s supporting research in full.** I read `DESIGN.md` end to end,
  all eleven ADRs, `docs/adr/README.md`, `CREDENTIAL-CHECKLIST.md`, and the fixtures. Of
  `FASTMCP-SPIKE-4.md` (2,354 lines) I read §§1.3, 3.2, 3.3, 10, 10.1, 12, 13.1-13.3, 20.3-20.8 and
  the closing *"What I could NOT verify"*. Of `JOBVITE-CONTRACT.md` I read §§2, 4 and the section
  index; of `JOBVITE-API.md`, §6.1 and the probe map. I did **not** read `COMPLIANCE-SPEC.md`,
  `STANDARDS.md`, `LICENSING-SURVEY.md`, `DECISIONS.md`, `data-inventory.md`, or any of the 17
  documents in `docs/reviews/` beyond the three gate scripts' docstrings.
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
  by no unit are **C1-R1, C2-R1, C4-E1, C7-I1 and C8-I1** - stated as a list, with no total, per
  `DESIGN.md:1797`'s own rule that a count in prose beside the thing it counts is a second source of
  truth nothing keeps in step. Most are covered in substance by a §8 case some unit does schedule:
  C8-I1 by #3 in U0, C4-E1 by #22's accept-carrying-false arm in U10, C7-I1 by #5 in U3. The two
  that were genuinely thin now have homes - C9-T1 in U0's inherited-limit paragraph and in §6, and
  C5-E1's ceiling in U13 - and are therefore **not** on the list above. **Draft 4's version of this
  bullet said "16 ids" and "seven rows", listed C9-T1 and C5-E1 among the unowned, and then named
  their owners four lines later** - a count carried through its own correction, contradicting itself
  inside one paragraph. **What is scheduled against every case is the §8 list, not the threat
  table**, and the plan's coverage claim is only ever the former.

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

---

## 9. Questions for the design

Draft 1 raised four; `9d65cc0` answered three; `8814d69` answered the fourth open one raised by the
review. **All five below are dispositions rather than asks, except Q3 and Q5, which are open.** The
answers are folded into the units above rather than restated here.

Nothing here is worked around in the plan. The design is one procedural step from freeze; after
that, each of these needs a numbered ADR carrying a `Type:` field.

### Q1 - answered, U1 unblocked

`JOBVITE_MAX_RESULTS` default **50** and `JOBVITE_OUTBOUND_RATE_LIMIT` default **6/min**, both in
`.env.example` (`DESIGN.md:1498-1513`). U1 enumerates the full configuration set; U6 and U7 consume
the values and each says at the point of use that **6/min is a conservative guess and not a vendor
figure**, per `:1525-1532`.

**Two things the plan carries forward rather than treating as closed.** `DESIGN.md:1533-1534` says
what closed is B15's *blocking* half and that whether either default is right *"no amount of
specification settles and only a live tenant can"*. And **C3-I1 and C6-D1 still read `unmitigated
(B15)`** (`:1695`, `:1738`) and remain on the mitigate-before-production-release list (`:1830`).
Naming a variable did not mitigate those rows, and this plan does not let an implementer read a
default in `.env.example` and conclude otherwise.

### Q2 - answered, and the residual has since landed

**Answered.** The §7.4 shutdown requirement is now §8 case **#18** (`DESIGN.md:1289-1295`). It
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
§8 case to be named by a §11 row or to cite a B-number or section as its owner. `DESIGN.md:1293`
records the same measured residual in case #18's own bullet, in the same terms this plan reached
independently: **GATE-2 stops a case's justification being quietly stripped, and it does not make
deletion visible.** Only a §11 row naming a case does that, and no threat row models a resource leak
on shutdown.

**Re-derived at HEAD rather than carried forward:** 25 cases, 18 distinct `§8:` references in §11,
and the orphan set is unchanged at **seven** - #12, #16, #17, #18, #21, #23 and #24. That is the
population GATE-2 now addresses. **An agent reading draft 2's version of this section would have
filed work that is done**, which is why it is rewritten in place rather than appended to.

### Q3 - stands, and that is the correct outcome

C8-R1, startup configuration logging, remains `unmitigated` (`DESIGN.md:1759`) and on the
mitigate-before-production-release list. The plan adds no startup log line, because specifying an
unspecified mitigation is not a plan's job and the ADR-0011 interaction is unresolved. Carried, not
worked around.

### Q4 - answered, U7 unblocked

`DESIGN.md:602` now sanctions an inline breaker in `services/jobvite_client.py` where no library
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
modules this design refuses, so an addition owes a justification. **Until that ADR exists, no unit
here plans a shared constraints module**; U14 is specified against per-tool ownership. Written down
because the duplication is the first thing an implementer would factor out on sight, and because
after the freeze doing it without the ADR is a design change made by whoever happened to notice.

### Q6 - §8 #2 asserts an absence with no paired positive in the design

**Open, and it is a plan-level fix today rather than a design change - raised so it can become one.**
`DESIGN.md:1229-1231` shows the design already knows this shape: #4 is *"positive on purpose"*
precisely so #5's absence *"cannot be satisfied by silence"*, and the two are explicitly paired.

**#2 has no such pair.** It asserts a secret never reaches a log record, and against a logger that
is misconfigured and emits nothing it passes. #4 does not cover it: #4 proves the **audit event**
exists, which is a different stream from the `loguru` records #2 is about, and the design's own
blanket positive-control rule (`DESIGN.md:1319-1320`) does not list #2 among the refusal-path cases.
U7's #13 does prove retry log lines exist, but that is four units later than U3.

U3 now carries the pairing as a **plan** decision: #2 is asserted against a log stream proven
non-empty by the same call. That is enough for the implementation. **What an ADR would settle is
whether the design wants the pairing stated where it states the other one**, so a future reader of
§8 sees #2 and #4 as the same construction rather than discovering the asymmetry in a plan.


---

*Draft 6 by `impl-plan-draft`, 2026-08-28, revised against `PLAN-REVIEW-R4.md`, cited against the
frozen `docs/DESIGN.md` at `135c3ac`. `docs/DESIGN.md` was not edited and nothing was committed.*
