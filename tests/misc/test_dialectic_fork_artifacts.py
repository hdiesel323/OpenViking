# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: AGPL-3.0

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_upstream_base_ledger_pins_requested_commit_and_branch():
    ledger = _read("FORK_PATCHES/UPSTREAM_BASE.md")

    assert "49ca3cdfe8336cd9f54a4c7d391b5846cb3f88f6" in ledger
    assert "feat/red-3052-dialectic-memory" in ledger
    assert "v0.4.11" in ledger


def test_goliath_compose_profile_disables_bot_and_uses_persistent_state():
    compose = _read("deploy/goliath/dialectic-memory.compose.yml")

    assert "OPENVIKING_WITH_BOT: \"0\"" in compose
    assert "OPENVIKING_IMAGE:?" in compose
    assert "target: /app/.openviking" in compose
    assert "curl -fsS http://127.0.0.1:1933/health" in compose
    assert "mem_limit: 4g" in compose


def test_goliath_profile_docs_keep_secrets_out_of_repo():
    docs = _read("deploy/goliath/README.md")

    assert "Store all secrets outside this repo" in docs
    assert "GET /ready" in docs
    assert "OPENVIKING_WITH_BOT=0" in docs
