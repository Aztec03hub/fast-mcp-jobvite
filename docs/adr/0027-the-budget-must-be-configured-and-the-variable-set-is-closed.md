# ADR-0027: the design requires the budget "configured" and closes the variable set without it

**Status:** Proposed
**Type:** Design change

> `DESIGN.md:373-375` requires **"a total outbound budget, *configured*, that bounds all attempts for
> one tool invocation"**. The design also declares the environment-variable set, and that set does
> not contain a variable for it. **Both statements are in the frozen document and they cannot both be
> satisfied.** I tried to satisfy the first and a gate stopped me, correctly.

## Context

### How this surfaced, and it was a gate catching me

U7 built the budget and left it a `Final` in `services/jobvite_client.py` whose `#:` comment named
`JOBVITE_OUTBOUND_BUDGET_SECONDS` - a variable that does not exist. I found that with
`docs/reviews/check-env-vars-are-declared.py` (task #60), judged the budget's configurability
design-required, and wired it: a `Settings` field, `.env.example`, the README table, `server.json`,
and all three client factories.

**`tests/test_config.py::test_env_example_and_design_declare_the_same_variables` went red.** The
frozen design declares the variable surface, and `grep -c JOBVITE_OUTBOUND_BUDGET_SECONDS` over
`c15b138:docs/DESIGN.md` returns **0**.

**So the "fix" was a design change, and I reverted it.** This is the same move three units were told
to refuse - U6 and U7 both deleted branches they had written because the design stated no policy, and
U9's report says naming a variable is the design's call. I walked into it while closing a finding
about exactly that defect, and the gate is what stopped me rather than my own judgement.

### The conflict, stated precisely

- `DESIGN.md:373-375` - the budget is **configured**. Not "configurable in a later revision":
  configured, in the sentence that specifies it.
- The design's variable list does not name it, and `tests/test_config.py` holds the two documents
  equal. `tests/test_repo_hygiene.py:81` additionally hard-codes the count at fifteen.

An implementation can satisfy either. It cannot satisfy both, and choosing silently is what B15's
whole lesson forbids.

## Decision

**§7.6's variable list should gain `JOBVITE_OUTBOUND_BUDGET_SECONDS`, so that §4.3's "configured"
becomes true.** The alternative - amending `373-375` to drop the word - is available and is worse:
the budget is the only bound between a slow Jobvite and an unbounded wait, and a deployment that
cannot tune it has to accept 60 seconds chosen against no measurement.

**Three things must land together**, and the first is why this is not a one-line edit:

1. The design's list, so the two documents agree.
2. The `Settings` field, `.env.example`, the README table and `server.json` - the closed-set tests
   hold all four equal and will refuse any subset.
3. **All THREE client factories** - two in `tools/jobs.py`, one in `tools/candidates.py`. A field
   declared and passed by two of three is a knob that works for some tools, which is worse than one
   that works for none because nothing looks wrong.

### And the count in `test_repo_hygiene.py:81` must stop being a literal

`assert len(variables) == 15` is a POSITIVE CONTROL on the parser - its docstring says so, and the
control is right to exist. **But it is a retyped constant that a legitimate addition breaks**, and
the project has now watched a retyped constant decay in a brief, in two obligation rows, in a CI
comment and in three harness floors. Derive it from `Settings`, or assert `> 0` and let the
closed-set test carry the equality it already carries.

## Consequences

### What is fixed now, and what is not

**Removed at `<this commit>`**: three invented variable names from `jobvite_client.py`'s comments -
for the retry cap and the two breaker figures. The design names no variable for any of them,
inventing one in a comment is B15's defect from the other side, and a reader who sets one gets
nothing.

**NOT removed**: the budget's name, because unlike the other three it is a gap the design REQUIRES
closing. Leaving it named keeps `check-env-vars-are-declared.py` reporting one finding, which is the
honest state - and that checker is deliberately not wired, so nothing goes red on it.

### The explanation had to stop naming the thing it explains

My first rewrite of those comments said "this comment used to name `JOBVITE_RETRY_MAX_ATTEMPTS`" -
and the checker still found four names, because it matches literals. **An explanation that quotes an
invented name reproduces the finding it is explaining.** The comments now describe without quoting,
and say why. `r6-fixes` hit the identical shape in a docstring whose every candidate grep matched
itself.

### A second false-positive class for the checker

`JOBVITE_CANDIDATE_DATA` is the FENCE TAG `utils/redaction.py` wraps untrusted candidate content in -
not a variable at all. Exempted with that reason rather than narrowing the pattern, because a pattern
that tried to tell a tag from a variable would start guessing. The first such class was a private
module-level `_JOBVITE_BREAKER`.
