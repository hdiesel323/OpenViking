# Fork Patch Ledger

- Fork: `https://github.com/hdiesel323/OpenViking`
- Upstream: `https://github.com/volcengine/OpenViking`
- Upstream tag: `v0.4.11`
- Upstream commit: `49ca3cdfe8336cd9f54a4c7d391b5846cb3f88f6`
- Working branch: `feat/red-3052-dialectic-memory`
- Parent issue: `RED-3052`
- Child implementation lane: `RED-3054`

## RED-3054: Additive Dialectic Memory

This fork adds a narrow dialectic/self-improvement proposal lane for private
Kanister/OpenViking evaluation. The patch is additive:

- no canonical Kanister ownership change
- no automatic skill mutation
- no credential, permission, policy, production-behavior, or destructive-action
  promotion without explicit approval
- no deployment performed by this repository patch

The fork keeps upstream AGPL notices intact and places fork-specific operational
notes under `FORK_PATCHES/` and `deploy/goliath/`.
