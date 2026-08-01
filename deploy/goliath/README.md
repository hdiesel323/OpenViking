# Private Goliath Profile: Dialectic Memory Fork

This profile is an additive deployment artifact for the `hdiesel323/OpenViking`
fork branch `feat/red-3052-dialectic-memory`. It is not a deployment action.

## Operator Contract

- Use an immutable private image digest through `OPENVIKING_IMAGE`; do not use
  a mutable tag or `latest`.
- Mount one persistent host directory at `/app/.openviking`.
- Put `ov.conf`, `ovcli.conf`, and workspace data in that mounted directory.
- Keep VikingBot disabled with `OPENVIKING_WITH_BOT=0`.
- Attach only to the existing private `canister-network`; this profile publishes
  no host port, so Kanister is the only supported caller.
- Probe liveness with `GET /health` and readiness with `GET /ready`.
- Store all secrets outside this repo and outside the compose file.

## Example

```sh
export OPENVIKING_IMAGE=ghcr.io/hdiesel323/openviking@sha256:<image-digest>
export OPENVIKING_DATA_DIR=/opt/openviking-dialectic
export OPENVIKING_ROOT_API_KEY="$(infisical secrets get OPENVIKING_ROOT_API_KEY --projectId <project-id> --env dev --path /kanister-memory --plain)"
docker compose -f deploy/goliath/dialectic-memory.compose.yml up -d
docker run --rm --network canister-network curlimages/curl:8.12.1 \
  -fsS http://openviking-dialectic:1933/health
docker run --rm --network canister-network curlimages/curl:8.12.1 \
  -fsS http://openviking-dialectic:1933/ready
```

The mounted `ov.conf` must reference `${OPENVIKING_ROOT_API_KEY}` and be
provisioned by the operator's secret/config system. Do not persist the exported
shell value; the example is intended for a short-lived Infisical-backed deploy
process. This repository intentionally contains no root API key, embedding key,
VLM key, Infisical token, or machine credential.

## Resource Defaults

- CPU: `2.0`
- Memory: `4g`
- PID limit: `512`
- Logs: json-file, five files, ten megabytes each

Increase these limits only after measuring local vectorization, parser, and
session-commit workload on the target host.
