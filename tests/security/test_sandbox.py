from __future__ import annotations

import pytest

from src.systems.sandbox import SandboxConfig, SandboxError, sandbox_command, run_generated_python


def test_sandbox_command_contains_required_restrictions(tmp_path) -> None:
    command = sandbox_command(SandboxConfig(), tmp_path / "fixture.json", tmp_path / "main.py")
    joined = " ".join(command)
    for required in ("--network none", "--read-only", "--cap-drop=ALL", "no-new-privileges", "--pids-limit", "--memory", "--user 65532:65532"):
        assert required in joined


def test_credential_reference_is_rejected_before_container(tmp_path) -> None:
    with pytest.raises(SandboxError):
        run_generated_python({}, "print(AUD_SUD_API_KEY)")

