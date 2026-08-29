# R6-FIXES - three Highs on U7, one of which the library does to us

**Read `docs/briefs/PREAMBLE.md` first.** Tools, isolation, evidence standards, gates and delivery
rules are there and are not repeated here.

Your agent name is `r6-fixes`. Your branch is `fix/r6-findings`. Your report goes to
`docs/worklogs/R6-FIXES-REPORT.md`, committed on your branch.

`docs/reviews/REVIEW-R6.md` is merged on `main`. **It is the authority, not this brief.** Every
finding carries a measurement and a suggested fix, and its probes are reproduced in full at the end.

## H1 is the one that matters, and I verified it in the library's source myself

`circuitbreaker` 2.1.3, `.venv/lib/python3.12/site-packages/circuitbreaker.py:113-120`:

```python
def __exit__(self, exc_type, exc_value, _traceback):
    if exc_type and self.is_failure(exc_type, exc_value):
        self._last_failure = exc_value
        self.__call_failed()
    else:
        self.reset()          # <-- and reset() sets _failure_count = 0
    return False
```

**So `_is_outage` returning `False` does not mean "this failure is not evidence". It means "this
call SUCCEEDED".** A 4xx, an exhausted budget, and the private `_RetryableUpstream` each CLOSE the
breaker and zero the counter. Measured 4 -> 0, with a mechanism-matched control showing 4 -> 5 when
the last call is a real outage.

**`DESIGN.md:354-355` says a 4xx "must not trip it". NOT TRIPPING IT AND HEALING IT ARE DIFFERENT
BEHAVIOURS, and the code has the second.** Under traffic that mixes 4xx with outages - a partially
degraded upstream, or a tool suite hitting stale ids - the breaker can never reach its threshold.

The budget arm is worse in kind. `JobviteRetryLaterError`'s docstring argues
`counts_toward_breaker=False` because *"counting it would let one slow invocation trip a breaker for
every other caller"*. The reasoning is right; the implementation does the opposite of neutral -
**one slow invocation now CLOSES the breaker for every other caller**, including from `half_open`,
with no successful call having reached Jobvite.

**The fix must make "not evidence of failure" distinct from "evidence of health".** R6 proposes one;
weigh it rather than pasting it. Whatever you choose, **the control is the probe R6 committed**: run
it before and after and put both readings in your report.

## H2 and H3

- **H2**: `_attempt` wraps a retryable status in the module-private `_RetryableUpstream` **regardless
  of HTTP method**. The retrying branch converts it back; **the non-retrying branch has no
  converter**, so a `POST` meeting a 5xx or 429 raises the private type out of `request()` and the
  caller gets `/problems/internal-error` 500. The class docstring states the invariant this breaks:
  *"Module-private and it never reaches a caller ... nothing else may see it."* **This is the only
  path a write can take.**
- **H3**: a SURVIVING MUTATION. `return exc.counts_toward_breaker` -> `return False` and **all 500
  tests pass**. A 429 can stop counting toward the breaker with nothing noticing. Anchor asserted
  unique first, landing proved by `git diff --stat`, restored by `cp` with `cmp: IDENTICAL`.

## M2 is about a control I praised, and I was wrong to

**Arm 1c of `scripts/probe-breaker-call-path.py` is TAUTOLOGICAL.** It searches the probe's own
source for `SCHEDULING_NAMES` - which is defined in that same source. R6's falsifying case: a file
containing *only* the term list, with zero scheduling code, passes the control 8/8.

Four of the eight terms appear only as their own definition; `sched` is a substring hit on the words
*scheduling*/*scheduled*; the probe genuinely exercises **three**.

**I called arm 1c "the discipline I most wanted" when U7 delivered it.** It is the right idea with an
implementation that cannot fail, which is precisely the defect this project keeps finding, and I
missed it because the idea was correct. **The fix is a control that reads a file which really
schedules** - not the probe itself.

## Standing requirements

- **Every fix ships with the mutation or amputation that proves the test can fail** - write the
  control, run it against the UNFIXED code, watch it survive, then fix, then watch it die. **H3 is
  already a surviving mutation: it must die.**
- **A MUTATION HARNESS OWNS THE WORKING TREE FOR ITS WHOLE RUN.** Do not read that tree, run the
  suite against it, or edit it while one runs - measured four times in one day by two agents.
  Restore with `cp`, verify with `cmp`. **Never `git stash`, never `git checkout <path>`.**
- **Run `ruff format` BEFORE your final harness run**, then re-run the harnesses AND
  `scripts/check-harness-anchors.py`.
- `docs/DESIGN.md` is FROZEN at `c15b138`. **If the fix needs the design to say something it does
  not, that is a Proposed ADR** - ADR-0026 is the next free number.
- **Both floors are DERIVED, never retyped.** Report them; **the `ci.yml` edits are MINE.**
- **No `Co-Authored-By:` or "Generated with" trailer. Ever.**

## Isolation

You own `src/fast_mcp_jobvite/services/jobvite_client.py`, `scripts/probe-breaker-call-path.py`,
`scripts/check-u7-resilience-*.sh`, and `tests/test_resilience.py`.

**`u9-http` is live in `server.py` and the HTTP half of `config.py`.** Do not touch either. If a fix
needs a new setting, say so and I will route it.

## How to deliver

Commit and push your branch. **Do NOT merge to main and do NOT push main.** `SendMessage` to
`"team-lead"` as your FINAL action: per finding what you measured before, what you changed, and the
control proving it; the H1 probe's readings on both sides; gate exit codes read from the terminal;
the new floors; and **what you could not settle**.
