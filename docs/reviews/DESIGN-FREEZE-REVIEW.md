# DESIGN freeze review

Reviewer: `design-freeze-review`, fresh. Wrote none of this.
Date: 2026-08-28 02:55 PM CDT.
Scope: `git diff fe226b6..HEAD -- docs/DESIGN.md .env.example` (commits `cc94459`, `8814d69`).
Everything else: **OUT OF SCOPE, NOT ASSESSED.**

## Verdict

**DO NOT FREEZE.**

**TALLY: 0 Critical / 0 High / 3 Medium / 3 Low.**
§11's must-mitigate table is empty (`DESIGN.md:1804` reads `*(none)*`), so that half of the freeze
condition holds. The review half does not: three Mediums stand.

All three suggested fixes are small and local. This is not a "the delta is wrong" verdict - the
delta is mostly right, and two of its three headline claims verified clean at source. It is a
"three sentences overstate what was measured, and one of them is the same species of overclaim the
delta was written to retract" verdict.

## Gates, re-run from the repo root

| Gate | Result |
|---|---|
| `python3 docs/reviews/check-coupling.py` | exit 0, PASS |
| `python3 docs/reviews/check-coupling-controls.py` | exit 0, **34/34 controls fired**, baseline green before and after |
| `python3 docs/reviews/check-coupling-sweep.py` | exit 0, 184 substitutions, **0 escapes are holes**, 6 escapes are the designed Medium/Low exemption |

The controls file's own claim of 34 was verified by reading the run, not the number.

---

## Findings

### M-1 (Medium). §8's SIGTERM bullet overstates GATE-2's bar, and the mutation that proves it is the bullet's own

`docs/DESIGN.md:1308` says:

> GATE-2 now requires every case to name its owner, which stops a case's justification being
> quietly stripped

**Measured, by mutating the document and running the gate:**

| Mutation | Gate |
|---|---|
| M1: delete the whole SIGTERM bullet from §8 | **exit 0** - deletion invisible, as the text says |
| M2: replace the bullet with a bare `- lifespan teardown runs on SIGTERM, on both transports;` | exit 1, GATE-2 fires |
| **M3: delete the real owner citations (`§7.4 stated the requirement`, `§7.4, §12 item 5 and this bullet`, `the uvicorn implementation detail §12 item 5 records`), keeping the gate-discussion prose** | **exit 0** |
| M4: strip the owner citation from the `create_candidate` bullet | exit 1, GATE-2 fires |

M3 is the finding. GATE-2's actual bar is `re.search(r"\bB\d{1,3}\b|§\d", flat)`
(`check-coupling.py:336`, condition at `:334`) - **any** section-shaped or B-shaped token anywhere
in the bullet. After M3 the surviving references in that bullet are `§11` and `§8`: the retraction
prose's references to the *gate machinery itself*. The paragraph explaining that the gate cannot
protect this case is what makes the gate green for this case. Every substantive owner can be
deleted and nothing fails.

So for the one bullet where the sentence is written, the sentence is false. The justification *can*
be quietly stripped. This is the same species as the two claims already retracted here - a claim
about the gate's purchase that nobody ran the gate against - and it is the third.

I checked whether this generalises. It does not, today: of the 24 §8 bullets, 17 are owned by a §11
row naming them, 6 cite real external owners (B42/§5.3, §5.3, B19/B108/§2.2/§4.3, B37/§4.3, §4.2,
§7.3/§8), and only the SIGTERM bullet contains self-referential `§8`/`§11` prose. The defect is
narrow. The false sentence is not.

**Suggested fix (MY SUGGESTION, verify before adopting).** Replace the clause with what the check
actually enforces:

> GATE-2 now requires every case to cite a B-number or a section, which catches a case stripped to a
> bare unattributed line; it does not check that the citation names an *owner*, and this bullet's own
> references to §8 and §11 satisfy it, so stripping §7.4 and §12 item 5 from here would still pass.
> **It does not make deletion visible.**

### M-2 (Medium). §7.1 still names nothing that configures certificates - B15's defect, third instance, in the paragraph the same commit edited

`docs/DESIGN.md:779-783` states a supported startup path:

> binding a non-loopback address without either TLS terminated in front (declared via
> `JOBVITE_TLS_TERMINATED_BY_PROXY=true`) **or certificates configured here** is a startup failure

`grep -rni "certfile\|keyfile\|ssl_\|tls_cert" .env.example docs/DESIGN.md` returns **nothing**.
"Configured here" names no variable, and `.env.example` - which §12 calls *"the single enumeration
... the file an operator copies"* - has no way to express it. `docs/DESIGN.md:1255` builds the §8
case on the same phrase (*"no certificates configured here"*).

This is precisely the defect `8814d69` was written to fix, four lines above it: *"an earlier
revision said 'unless told otherwise' and named nothing that does the telling"* (`:752-753`). The
sweep that produced `JOBVITE_MCP_HOST` and `JOBVITE_MCP_PORT` stopped at the sentence it was reading
and did not reach the next paragraph.

Mitigating: the §8 *refusal* arm is buildable now (bind off-loopback, no certs, no proxy flag), and
a positive control exists via `JOBVITE_TLS_TERMINATED_BY_PROXY=true`. So this does not block the
test. It blocks the deployment shape the design says is supported, and freezing it means an ADR to
add a variable that should have been in this commit.

**Suggested fix (MY SUGGESTION, verify before adopting).** Either name them, at `:760-761`:

> ... without either TLS terminated in front (declared via `JOBVITE_TLS_TERMINATED_BY_PROXY=true`)
> or certificates configured via `JOBVITE_TLS_CERTFILE` and `JOBVITE_TLS_KEYFILE`, both unset by
> default, is a startup failure, not a warning.

(with both added to `.env.example` in the same edit), **or** cut the arm and say so:

> ... without `JOBVITE_TLS_TERMINATED_BY_PROXY=true` is a startup failure, not a warning. **This
> server terminates no TLS of its own**: there is no certificate configuration and none is planned,
> because a proxy in front is the only deployment shape §7.1 supports.

The second is cheaper and matches what `.env.example` actually offers today. Which one is right is
a design call, not mine.

### M-3 (Medium). §12 still says two variables had no name; §7.1 now says two more did

`docs/DESIGN.md:1527-1528`:

> **The two variables that had no name now have one, because leaving them unnamed made
> `.env.example` incomplete by construction and blocked `config.py` (B15).**

followed at `:1491` by *"Both are now in `.env.example`, which closes B15's blocking half."* The
bullet then lists `JOBVITE_MAX_RESULTS` and `JOBVITE_OUTBOUND_RATE_LIMIT`.

`docs/DESIGN.md:774-777`, added in the same window, records two more variables that had no name and
that blocked the build the same way (`JOBVITE_MCP_HOST`, `JOBVITE_MCP_PORT`), plus a third
(`JOBVITE_HTTP_TOKENS`). `docs/plans/IMPLEMENTATION-PLAN.md:623` says it outright: *"That is B15's
defect in three more variables, and draft 2 failed to run over the rest of the variable set."*

So the document asserts "the two variables that had no name" and, 700 lines earlier, that there were
more. That is the shape `fe226b6` was written to remove ("two rows asserting a thing and its
negation"), reappearing in prose rather than in a table. §12's bullet is also the one place whose
entire subject is *"a hand-kept list goes stale on the first change"* - and it went stale on the
first change.

A second, softer edge of the same unswept enumeration: `:1468-1469` insists **"There are five"**
credential variables, while `:781-782` describes `JOBVITE_HTTP_TOKENS` as secret-class and *"absent
from `.env.example`'s filled values like every other credential"*. The five are defensible if read
as *§7.3's tool-requirements table* (upstream Jobvite credentials), which is how `:1470` scopes
them, but a reader arriving from §7.2 counts six. Worth one clause, not a separate finding.

**Suggested fix (MY SUGGESTION, verify before adopting).** Rewrite `:1477-1478` in place (do not
append):

> **Five variables had no name, and all five have one now** - `JOBVITE_MAX_RESULTS` and
> `JOBVITE_OUTBOUND_RATE_LIMIT` below, and `JOBVITE_MCP_HOST`, `JOBVITE_MCP_PORT` and
> `JOBVITE_HTTP_TOKENS` in §7.1 and §7.2 - **because leaving them unnamed made `.env.example`
> incomplete by construction and blocked `config.py` (B15). The first two were found by the
> conformance sweep and the last three by someone trying to start the unit, which is why a sweep
> over the whole variable set, not over the sentence being edited, is what closes this.**

and at `:1469` narrow the five: *"There are five **upstream Jobvite credentials**"*, so the
server-side bearer tokens of §7.2 are visibly a different set.

### L-1 (Low). §7.2 leans on a fail-fast posture §7.3 explicitly does not state

`docs/DESIGN.md:805-806`: *"the same fail-fast posture §7.3 applies to every required variable."*
`docs/DESIGN.md:910`: *"Fail-fast validates what each *enabled* tool requires, **never the union**"*,
and the table at `:891-896` is keyed by tool. There is no row, and no rule, for a requirement
conditioned on the *transport*. An implementer building `config.py` from §7.3 finds no home for
"`JOBVITE_HTTP_TOKENS` is required when `JOBVITE_MCP_TRANSPORT=http`", and §7.3 tells them the
opposite of "every".

**Suggested fix (MY SUGGESTION, verify before adopting).** Add a row and a sentence to §7.3 after
`:896`, and point §7.2 at it:

> | the `http` transport | `JOBVITE_HTTP_TOKENS`, plus `JOBVITE_TLS_TERMINATED_BY_PROXY=true` when the bind address is not loopback |
>
> **Two requirements are conditioned on the transport rather than on a tool**, and they are in the
> table for the same reason the tool rows are: fail-fast validates what the running configuration
> needs, which is the enabled tools plus the selected transport, and still never the union.

Then §7.2:783-784 becomes *"a startup failure, not an open server - §7.3's table carries it as a
transport-conditioned requirement."*

### L-2 (Low). Two §11 rows carry an unbalanced `**` after the emphasis fix

`docs/DESIGN.md:1704` (C3-I1) and `:1697` (C6-D1) each contain three `**` markers on one line. The
fix removed two of the four leading asterisks and left the trailing pair, so the Mitigation cell
renders emphasis from `(B15)` onward or shows literal asterisks. Checked the whole file: these are
the only two single-line rows with an odd count; every other odd line is a bold span wrapping across
two source lines, which is fine.

**Suggested fix (MY SUGGESTION, verify before adopting).** Delete the trailing `**` on both lines,
so each cell ends `...which only a live tenant settles (B15) | unmitigated (B15) |`.

### L-3 (Low, nit). B15 is cited at §7.1 for a defect class its source clause does not cover

`docs/DESIGN.md:775`: *"That is the same defect as B15, found the same way."* B15 at source
(`docs/research/STANDARDS.md:180`) is **"Tool result size is bounded to a documented maximum before
return"** - a result-size obligation, not a rule about naming configuration variables. The document
has used "B15" as shorthand for *the unnamed-default defect* since §12, so the usage is internally
consistent, but a reader chasing the citation to the corpus lands on something else.

**Suggested fix (MY SUGGESTION, verify before adopting).** Make the referent explicit at `:753`:

> That is the same defect the B15 work exposed - a default the design named nowhere - found the same
> way, by someone trying to build against it. B15 itself is the result-size obligation
> (`STANDARDS.md:180`); what recurs here is the naming failure that blocked it, not the obligation.

---

## Checked and clean

These were hunted specifically and hold.

- **The retraction's factual core is now correct.** Measured: deleting the SIGTERM case leaves
  `check-coupling.py` at exit 0 (mutation M1), while deleting a case a §11 row names is caught
  (controls 4 and 9 fire). *"The gate resolves §11 rows to §8 cases and not the reverse"* -
  confirmed against the code at `check-coupling.py:305-339`.
- **"It does not make deletion visible" is true and is still stated**, in bold, at `:1258`. GATE-2's
  limits are not overstated in that direction. The overstatement is M-1, in the other clause.
- **"No threat row models a resource leak on shutdown"** - confirmed. `grep -ni
  "shutdown\|lifespan\|teardown\|SIGTERM"` over §11's tables returns nothing.
- **The B47 correction is right at source.** `circuitbreaker ^2` is blessed at
  `architecture/reference-architecture.md:95` (the row B47 cites), and B37
  (`STANDARDS.md:316-318`) requires one breaker per dependency *"using `circuitbreaker`"*. The
  earlier *"no library is selected yet (B47)"* was wrong, and the replacement characterisation -
  one experiment against the blessed candidate, inline fallback if it fails - is accurate. This is
  not one wrong characterisation swapped for another.
- **The new B37 citation resolves.** `docs/DESIGN.md:1316` cites `backend/resilience.md:166-168`
  for the 4xx clause. Read at source: file lines 166-168 are *"Count **only outage-class errors**
  toward the breaker via `expected_exception` - a caller error (4xx) is not an outage and MUST NOT
  trip it."* Exact. (Note `STANDARDS.md:316-317` cites both `:159-161` and `:166-168`; the design
  picked the tighter of the two, correctly.)
- **The three bare cases now have owners that survive mutation.** `create_candidate` (M4), the 4xx
  case (control 22) and the `eId`/`EId` case all lose their green when the citation is stripped.
  Only the SIGTERM bullet is immune, which is M-1.
- **`.env.example` and §7.1/§7.2 agree.** Host default `127.0.0.1`, port `8000`, `JOBVITE_HTTP_TOKENS`
  empty, comment and design both scope host/port to the `http` transport. Fifteen variables, no
  count stated anywhere that would go stale except the two in M-3.
- **`JOBVITE_HTTP_TOKENS` does not contradict §7.1's TLS refusal.** They are orthogonal gates:
  tokens are required whenever the transport is `http`; TLS is required whenever the bind address is
  not loopback. A loopback `http` deployment needs tokens and no TLS, which both sections permit.
- **§11's must-mitigate table is empty** (`:1750-1754`), and `:1813-1814`'s claim that C5-R1 and
  C5-E1 each name a §8 case the gate enforces is true - the sweep shows both lose their green when
  the reference is removed, and neither can use the Medium/Low exemption.
- **No other single-line table row carries unbalanced emphasis** (whole-file `**`-parity sweep).

## Not verified

- Whether `circuitbreaker ^2` evaluates half-open expiry on the call path or from a timer. That is
  the open experiment the design now correctly scopes; it needs the library installed, which is
  implementation.
- Whether `50` and `6/min` are the right defaults. Only a live tenant settles it, and the document
  says so.

---

## If this is frozen today, the thing most likely to be regretted

**§8's SIGTERM case.**

It is the one required case whose deletion the gate cannot see - measured, not argued (mutation M1,
exit 0). Its entire protection is that §7.4, §12 item 5 and the bullet itself point at each other,
and after M-1 we know even that is weaker than written: the citations can be stripped and the gate
stays green.

What makes it the regret rather than a curiosity is what it guards. Lifespan teardown *not* running
under SIGTERM was verified 3-of-3 in the wild (`:906`), the workaround is an `os._exit(0)` that
depends on a uvicorn implementation detail (`:921-923`), and the bullet says three of this
document's stated verification gaps close only on this case. It is simultaneously the most load-
bearing case in §8 and the only one with no structural owner.

The mechanism of the regret is mundane: someone implementing §8 works down the list, this case is
expensive (two transports, `/proc/<pid>/cmdline`, a side-effect assertion rather than an exit code),
and dropping it costs nothing anyone will notice - not CI, which does not exist yet (`:1380`), and
not the gate, which is green either way. The document already records that this is weaker than a
row. Freezing accepts it. That acceptance is correct as a decision and is the one most likely to be
regretted, so it belongs on the implementation risk register with a named owner, not in a bullet
that guards itself.

The cheap hedge, if wanted before the freeze: make the implementation plan's §8 checklist carry this
case as a named line item with a person against it, since the document cannot carry it.

---

## Addendum: Q5, where input models live

Routed in mid-round by the team lead as the one in-scope addition. Answered here, not folded into
the tally above, because it is not a defect in the two commits.

### 1. Does it block the freeze? **No.**

It is an **omission, not a false claim**, and that distinction is the whole answer. Every Medium
above is the document asserting something measurably untrue. Q5 is the document not asserting
anything - and nothing anywhere resolves against the missing answer:

- `check-coupling.py` never reads §3. I inserted the proposed lines below and re-ran all three
  gates: `check-coupling.py` exit 0, `check-coupling-controls.py` exit 0, `check-coupling-sweep.py`
  exit 0 with 0 holes. §3's layout block is outside every selector.
- No §8 case names a module for input validation. The three inbound cases (`:1205`, `:1209`,
  the schema case) assert *behaviour before dispatch*, not a file.
- §11's C3 is scoped **by concept**, not by module: `:1647` reads *"C3. Tool argument layer (input
  models, `strict=True`)"* with no path. Only one row names modules for this at all, and it already
  answers the question in passing - `:1638` (C2-T1) reads *"Payload shaping happens in the tools and
  in `models/`, which is C3 and C6"*, mapping **C3 to the tools** and C6 to `models/`.

So the design is not silent so much as under-written: it implies the answer in a threat-model row
and never records it in the map. Nothing built on it is wrong today, and the plan has a correct
sequential path. Freezing does not propagate a falsehood.

The lead's read is right, and I did not reach it by agreeing with the framing - I checked whether
anything resolves against the gap, and nothing does.

### 2. Is a one-line addition to §3 the right fix?

**Right in kind, wrong in count. It needs three edits, not one, and one of the three is an ADR.**

A single line saying where the input models live answers the smaller half. The half that actually
produced the collision is that **the shared inbound controls have no home either**, and they cannot
live in a per-tool model without being copied four times:

- the control-character and bidi rejection (`:151-158`), one rule for every string argument on every
  tool;
- three of the four structural limits (`:141-143`) - depth 5, list 1,000, dict keys 100.

The fourth limit is already placed: `:136-137` puts body size **at the middleware**, which is C2.
The other three and the character rule are not placed anywhere, and this document's own pattern for
a rule with many callers is a single enforcement point (§4.1: *"Enforced in one place,
`utils/redaction.py`"*). Naming where the models sit while leaving the validators unhoused re-runs
the same file-ownership ambiguity one layer down, which is exactly what broke the wave.

**The two edits I would make now** (MY SUGGESTION, verify before adopting). Replace `:268-270`:

```
  tools/candidates.py         search_candidates, get_candidate, create_candidate; their input models
  tools/jobs.py               search_jobs, get_job_feed; their input models
  models/                     allow-listed OUTPUT models, one per tool; no input model lives here
```

That is recording what `:1638` already implies rather than deciding something new, which is why it
belongs in §3 now: an input model has exactly one consumer, co-locating it with that consumer keeps
`models/` scoped to the output pipeline as §11's C6 has it, and it gives each `tools/*.py` sole
ownership of its own inputs - which is the property concurrent implementation needs.

**The alternative I would not take**: putting input models in `models/`. It merges C3's and C6's
module footprints while §11 keeps them as separate components with different ratings, and it is the
reading under which the plan's unit collides with three others.

### 3. The third edit belongs in an ADR, and I am saying so because it does, not because it was offered

The shared-constraint module is **not** a clarification. Adding

```
  utils/constraints.py        the shared inbound constraint types every input model reuses:
                              control-character and bidi rejection, and the depth/list/dict-key
                              limits (§2.1)
```

adds a **module** to a block whose closing sentence exists to enumerate the modules this design
refuses (`:276-277`: *"No cache module, no bulk module, no custom logging module"*). A section that
justifies its absences owes a justification for an addition. There is also a real alternative -
rescope `models/` to hold both input and output models and merge C3/C6's module footprint - which
deserves a recorded rejection rather than a silent one. That is the shape of a decision, and this
project's rule is that a decision goes in a numbered ADR.

**ADR-0012, `Type:` field and all.** That is not a failure mode; it is the mechanism working on its
first real customer, and it is cheaper to find out now whether the `Type:` field is usable than on
something contentious.

If the lead wants a single pre-freeze edit instead, take the `:268-270` replacement alone and file
the constraint module as ADR-0012 after. That ordering is coherent: the part that records an
existing implication lands in the map, the part that makes a new choice goes through the mechanism
built for new choices.

### One sibling to check, whichever answer is adopted

`:1597`'s data-inventory row lists `models/` among the places candidate personal data lives. If
`models/` becomes explicitly output-only, `create_candidate`'s **input** model - which carries a
candidate's name, email and phone by construction - is the PII location that row no longer names.
It is one clause, and it is the kind of sibling that goes stale exactly the way §12's variable count
did. Out of scope for this round; flagged so the edit does not create the next finding.
