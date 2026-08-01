# Private Goliath Profile: Dialectic Memory Fork

This profile is an additive deployment artifact for the `hdiesel323/OpenViking`
fork branch `feat/red-3052-dialectic-memory`. It is not a deployment action.

## Operator Contract

- Use a pinned private image tag through `OPENVIKING_IMAGE`; do not use `latest`.
- Mount one persistent host directory at `/app/.openviking`.
- Put `ov.conf`, `ovcli.conf`, and workspace data in that mounted directory.
- Keep VikingBot disabled with `OPENVIKING_WITH_BOT=0`.
- Probe liveness with `GET /health` and readiness with `GET /ready`.
- Store all secrets outside this repo and outside the compose file.

## Example

```sh
export OPENVIKING_IMAGE=ghcr.io/hdiesel323/openviking:feat-red-3052-dialectic-memory
export OPENVIKING_DATA_DIR=/opt/openviking-dialectic
docker compose -f deploy/goliath/dialectic-memory.compose.yml up -d
curl -fsS http://127.0.0.1:1933/health
curl -fsS http://127.0.0.1:1933/ready
```

The mounted `ov.conf` must be provisioned by the operator's secret/config
system. This repository intentionally contains no root API key, embedding key,
VLM key, Infisical token, or machine credential.

## Resource Defaults

- CPU: `2.0`
- Memory: `4g`
- PID limit: `512`
- Logs: json-file, five files, ten megabytes each

Increase these limits only after measuring local vectorization, parser, and
session-commit workload on the target host.
