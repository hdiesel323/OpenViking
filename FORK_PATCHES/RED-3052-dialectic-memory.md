# RED-3052 / RED-3054 Dialectic Memory Patch

## Added Surfaces

- `openviking/prompts/templates/memory/dialectic_proposals.yaml` registers an
  additive agent memory type for proposal capture.
- `openviking/session/memory/dialectic.py` defines deterministic proposal
  schema validation and low-risk promotion eligibility helpers.
- `examples/codex-memory-plugin/extensions/dialectic-memory/` documents how
  session memory-diff integrations can emit proposal candidates without
  mutating skills.
- `deploy/goliath/dialectic-memory.compose.yml` provides a private container
  profile with VikingBot disabled, persistent state, pinned image selection,
  health/readiness probes, and bounded resources.

## Promotion Guard

Low-risk eligibility requires all of the following:

- confidence is at least `0.90`
- at least two independent successful receipts exist
- no unresolved contradiction exists
- all eval gates pass
- the scope is reversible
- risk class is `low`
- no protected category is in scope

Protected categories always require approval: identity, permissions,
credentials, policy, production behavior, destructive actions, and skill code.
