# ADR-0018: `os._exit(0)` in the `finally` reports a crash as a clean stop

**Status:** Accepted
**Type:** Design change

> **Accepted and APPLIED.** This changed the §7.4 shutdown block, which was frozen, and it changed
> shipped behaviour in `__main__.py`. U1 built **what the frozen design specified** and did not
> apply it; like ADR-0017 it carried an argument someone might reject, so it was reviewed rather
> than sequenced. Mutation **M14** in `scripts/check-u1-boot-controls.sh` now holds the constant in
> place, and M12 - the forced exit removed entirely - is untouched and still fires.

## Context

Found by **building U1**, not by reading. `DESIGN.md:990-1008` gives the shutdown mitigation
verbatim, and the block is the specification rather than an illustration:

> ```python
> # in main(), after mcp.run(...) inside try/except KeyboardInterrupt:
> finally:
>     sys.stdout.flush(); sys.stderr.flush()
>     os._exit(0)   # a non-daemon AnyIO thread blocks sys.exit() on stdio
> ```

The forced exit is necessary and its justification is measured: on stdio a non-daemon AnyIO worker
thread blocks interpreter shutdown, so even an explicit `sys.exit(0)` never completes
(`DESIGN.md:979-981`). U1's shutdown case reproduces both halves and both go red when `os._exit` is
removed.

**The defect is the constant, not the call.** `finally` runs on *every* exit from the `try`, not
only on the `KeyboardInterrupt` path the surrounding prose is about. So:

| How `mcp.run` ends | What the process reports |
|---|---|
| SIGTERM / SIGINT, teardown complete | exit 0 - correct |
| Port already bound, TLS misconfigured downstream, an unhandled exception in a tool registry, an AnyIO cancellation escaping | **exit 0** |

A supervisor cannot tell the two apart. Docker restart policies, Kubernetes `restartPolicy`,
systemd `Restart=on-failure` and every alerting rule anyone will write against this server read the
exit status, and `0` means *finished normally, do not restart, do not alarm*. The crash also
disappears from the only signal that survives log rotation.

**This is the same failure shape §8 #18 already reasons about, on the other side.** That case
refuses to assert shutdown by the exit code, "since a process that dies uncleanly can still exit 0"
(`DESIGN.md:1338-1339`). The design identified that an exit code can lie about an unclean death and
then, four hundred lines earlier, specified the code that makes it lie.

**What the design does not claim, and why this is not a reading error.** `DESIGN.md:1009` says only
"Teardown completes before `os._exit`, so skipping atexit handlers costs nothing we rely on". That
sentence disposes of the *atexit* consequence. The exit *status* is not mentioned anywhere in §7.4,
so this is a gap rather than a decision recorded against a rejected alternative.

## Decision

Keep `os._exit`; make its status the one the run actually earned.

```python
status = 0
try:
    mcp.run(...)
except KeyboardInterrupt:
    logger.info("shutting down")
except BaseException:
    logger.exception("the server terminated abnormally")
    status = 70          # EX_SOFTWARE
    raise
finally:
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(status)
```

`os._exit` still runs unconditionally, so the stdio hang the workaround exists for is still closed
and nothing about the SIGTERM mitigation changes. Only the constant moves.

**A note on the `raise`:** it never reaches a caller, because the `finally` forces the exit first.
It is there so the traceback is not swallowed if the `finally` is ever removed - the logging call is
what actually records the failure.

## Consequences

- **A crash becomes visible to a supervisor**, which is the whole point. Deployments with
  `Restart=on-failure` begin restarting on a fault they currently ignore.
- **A deployment that currently looks healthy may start reporting failures.** That is the correct
  direction and it should be expected on first rollout rather than treated as a regression.
- **The status must be tested by the SIDE EFFECT it is meant to produce**, not by asserting `70`
  against a synthetic exception in a unit test - the same reasoning §8 #18 applies to teardown. A
  case that forces `mcp.run` to fail for a real reason (a bound port is the cheapest) and reads the
  process's exit status is what would discharge this.

## What this ADR does not settle

- **It does not choose the value.** `70` is `EX_SOFTWARE` from `sysexits.h`, matching the
  `EXIT_CONFIGURATION_REFUSED = 78` (`EX_CONFIG`) U1 already uses on the refusal path. A reviewer may
  prefer a plain `1`. The argument here is that the status must not be `0`; which non-zero value it
  is, is a smaller question.
- **It does not claim the crash paths are enumerated.** The table above lists shapes that are
  plausible for this server; none has been executed, because nothing that can crash `mcp.run` exists
  yet. U9's HTTP hardening is where a bound port becomes reachable.
- **It does not touch the refusal path.** That path returns before the `try` and already carries a
  distinct status.
- **It does not remove `os._exit`.** `DESIGN.md:979-981`'s measurement stands, and U1's mutation
  control M12 confirms the stdio arm goes red without it.
