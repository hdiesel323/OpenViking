# Dialectic Memory Extension Notes

This extension note shows how Codex/OpenViking session capture can preserve
dialectic proposals without changing canonical skill ownership.

The existing Codex memory plugin appends session turns and commits through
normal OpenViking session APIs. With this fork, the memory extractor can emit
`dialectic_proposals` records through the bundled memory template. Promotion is
not automatic: callers must validate a stored proposal with
`openviking.session.memory.dialectic.low_risk_promotion_eligibility`.

Protected categories always require explicit approval before any behavior
change: identity, permissions, credentials, policy, production behavior,
destructive actions, and skill code.

See `session-memory-diff.example.json` for the payload shape a session-diff
extension can reference when constructing a proposal candidate.
