# INBOUND-SURFACE - the sweep enumerates a container narrower than its own claim

**Read `docs/briefs/PREAMBLE.md` first.** Task tools, isolation, evidence standards, gates and
delivery rules are there and are not repeated here.

Your agent name is `inbound-surface`. Your branch is `fix/inbound-surface`. Your report goes to
`docs/worklogs/INBOUND-SURFACE-REPORT.md`, committed on your branch. Your task record is **#88**.

**Read `docs/reviews/REVIEW-R8.md` first** - findings H1 and the Q1 answer are your whole subject.

## The finding, already measured, with a surviving mutation

`src/fast_mcp_jobvite/approval.py:95` `ApprovalAnswer` is an inbound model **outside `tools/`**,
populated from outside the server at `approval.py:419` via
`ctx.elicit(..., response_type=ApprovalAnswer)`.

`tests/test_arguments_sweep.py` discovers input models by two independent AST routes, both scoped to
`TOOLS_DIR` at `:61`. **Both miss it.** R8's mutation set `approval.py:108` `extra="forbid"` to
`extra="allow"` and the entire suite stayed green, exit 0.

## The lesson this carries, which matters more than the fix

**U14 did the right thing and it was still not enough.** It replaced a hand-kept LIST with an
enumerated CONTAINER - which is exactly what this project keeps asking for, and its report is
accurate about having done so. Then it picked a container **narrower than the property it asserts**:
the sweep claims the inbound surface, and enumerates one directory.

So: *enumerating a container is only as good as choosing the right container.* Your fix must not
repeat the shape one level further out. State plainly, in your report, what container you chose and
what is outside it.

## What to build

R8's suggestion, and it is a hypothesis you must measure rather than apply:

> Do **not** widen route B to all of `src/`. U14 is right that this sweeps `models/` and needs an
> input-vs-output rule that is not a name filter - and a name filter is a second hand-kept list
> wearing a naming convention as a disguise, which U14's own mutation M4 already kills.
>
> Instead add a **third route**: enumerate every `BaseModel` named as a `response_type=` or
> `requested_schema=` argument anywhere in the tree, and assert it is a subset of the swept set.
> Same exclude-by-USE rule route B already applies, aimed at the second way a model receives outside
> data. It should find exactly `ApprovalAnswer` and fail today.

**Confirm it fails today before you fix anything.** A new route that passes on first run has not
been shown to see the thing it was written for.

## THE SEVENTH PATH, which has no model at all

R8 found this answering Q1 and it is not optional scope. The MRTR leg at `approval.py:409-410` reads
`content.get("approve")` **straight off a raw dict**. No model, so no structural limit, no
`extra="forbid"`, no `strict=True`.

**A route that enumerates models cannot see a path that has none.** Decide what covers it and say so
explicitly. Leaving it unmentioned is the outcome to avoid: an unenumerated path that a future
reader assumes the sweep reached is exactly the shape you are here to close.

If the honest answer is "nothing covers it and here is why that is acceptable", write that down with
the reasoning. If it needs a model or a guard, that may be a design question - raise an ADR rather
than inventing a contract. **Run `python3 docs/reviews/check-adr-numbers.py` and take the number from
its `NEXT FREE ADR NUMBER` line**, which now scans every branch; the count above that line is only
this checkout and has already misled one reviewer.

## Already fixed - do NOT redo

**R8-H2 landed at `fd1057a`**: `strict=True` on `ApprovalAnswer`, with `tests/test_approval_strictness.py`
and both amputation arms. Do not touch that model's `strict=True` or that test file.

H2 is *why* H1 matters: the coercion divergence sat there because no sweep reached the model. **Fixing
H1 turns that class of defect into a test failure instead of a review finding** - so when you are
done, an `ApprovalAnswer` that loses `strict=True` or `extra="forbid"` should go red on your route,
not only on the file I added.

## Gates

Floors DERIVED from `ci.yml` by grep, never retyped - the suite floor is 782 as I write this and will
have moved by the time you read it. 0 skips. Full gate before folding, not after. `ci.yml` is the
orchestrator's; put any steps you need in your report.

`src/fast_mcp_jobvite/approval.py` is also being edited by `r7-fixes` (its module docstring) - keep
your changes away from the top of that file, and tell me if you cannot.

## In the report

The container you chose and what remains outside it. Proof the new route fails before the fix and
passes after. What you decided about the modelless MRTR path and why. Then what you could not settle.
