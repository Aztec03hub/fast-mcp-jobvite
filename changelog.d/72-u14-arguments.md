### Added
- The three unimplemented structural limits of `DESIGN.md:162-164` - nesting depth 5, 1,000 list
  items, 100 dict keys - plus a 1 MiB bound on the serialised argument payload, in
  `utils/constraints.py`, applied to every tool input model through a shared `InboundModel` base.
  (task #72)
- `tests/test_arguments_sweep.py`: §8 #7, #8 and #9, swept over an input-model set discovered by
  two independent AST walks of `src/fast_mcp_jobvite/tools/` asserted equal, never over a list.
  (task #72)
- ADR-0029, recording that §2.1's body-size limit is placed at a middleware this design does not
  have, and that the payload cap is not it. (task #72)
