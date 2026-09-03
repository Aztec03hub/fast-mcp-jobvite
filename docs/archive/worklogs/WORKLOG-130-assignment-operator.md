# WORKLOG — #130: an amputation that crashed, and read as a survivor

2026-09-01, Tier 0, on `main`.

## The defect

`docs/reviews/probe-audit-shape-container.py` amputates an `emit(...)`
site by deleting the STATEMENT that owns the call. At
`src/fast_mcp_jobvite/tools/candidates.py:832` the statement is

    warnings = emit(event, AuditPhase.AFTER_WRITE)

so deleting it unbinds `warnings`, and every test on that path dies with
a `NameError`. The probe scores a row by whether tests failed, so a
**crash it caused itself** read as a kill — or, when the crash landed in
a test that was not the assertion under study, as noise around a
survivor. Either way the row was measuring the mutation harness, not the
audit emission.

**This is the "amputate, don't only mutate" doctrine hitting its own
edge.** Deletion is the stronger operator and it is right almost
everywhere. It is wrong exactly where the deleted statement BINDS a name
the surrounding code still reads.

## The fix

`mutate()` now branches on the AST. When the `emit(...)` call is the
value of an `ast.Assign`, the CALL is replaced with `[]` and the
assignment target stays bound; otherwise the whole statement goes, as
before. `expect_stmt_delta` moves with it (0 and 1 respectively), so the
re-parse check still holds each shape to its own arithmetic.

## The measurement

    src/fast_mcp_jobvite/tools/candidates.py:832  emit(...)   exit 1
      replaced the emit(...) call with [] (assignment target kept bound)
      killed: tests/test_approval_write.py::
              test_case16_the_audit_failure_warning_branch_carries_request_id
      killed: tests/test_audit_phase_sites.py::
              test_each_audit_emission_passes_the_phase_the_design_assigns_it
              [create_candidate-written]

**832 IS KILLED, AND #104's HEADLINE OF TWO SURVIVORS WAS CORRECT** —
not understated by one, which is what #104 itself warned it might be.
The killing tests are audit tests, and the first of them asserts exactly
what the mutation destroys.

`probe-audit-shape-controls.py`: ALL FOUR CONTROLS PASS, population
restored to 13 emit sites.

## What went wrong while doing it, and it is #131 again

I ran the controls probe twice inside one `bash` call, hit my own
two-minute timeout, and the kill left the probe's two plant files in the
tree:

    src/fast_mcp_jobvite/_probe_control.py
    tests/test_probe_control_plant.py

The plant file's own docstring had predicted it: *"Written and deleted
by that script. If this file is present in a commit, the control script
died without cleaning up and the tree is dirty."*

That is **#131 and #146 reproduced by hand, by me, an hour after I
briefed an agent on them** — the third independent instance tonight. The
harness is not the problem; the SHAPE is. A mutation harness that must
be alive to restore the tree will one day not be alive. `--restore-only`
(#146) is the answer for the existing ones, and for anything new the
answer is not to mutate the tree at all: the coverage ratchet shipped
the same afternoon grew a `--backlog PATH` flag for exactly this reason,
and its eight arms all run against temporary files.

## Also fixed here

Three comment lines at 329-331 exceeded W505's 72 characters after my
reflow. Rewritten as a block, not spliced by line index — splicing is
how I mangled comment blocks three times earlier in this session.
