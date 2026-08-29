# Agent briefs

**These live in the repository because the alternative destroyed real work.**

A sudden restart emptied the session scratchpad. Every brief written there was lost, and so was a
48KB code-review report carrying nineteen open findings with their evidence and their suggested
fixes. The only surviving record was a summary somebody happened to have copied onto the task board.

The rule that follows, and it applies to both directions of an agent's work:

- **A brief goes here**, committed, before the agent is dispatched.
- **A report goes in `docs/worklogs/` or `docs/reviews/`**, committed on the agent's branch. Never
  only into a worktree, and never only into `/tmp` - both vanish with the agent.

This is the same lesson the project already learned about measurements: *prose about a measurement
decays into a claim about one, so commit the script.* A brief in `/tmp` is a plan nobody can re-run.

Briefs are kept after the unit lands rather than deleted. They record what the agent was told, which
is the only way to tell a defect in the work from a defect in the instructions - and several
findings this project has recorded were the latter.
