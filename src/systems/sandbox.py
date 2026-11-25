"""Disposable offline Docker runner for System C generated Python."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


class SandboxError(RuntimeError):
    pass


@dataclass(frozen=True)
class SandboxConfig:
    image: str = "python:3.12.8-slim@sha256:development-pin-required"
    timeout_seconds: int = 10
    stdout_limit: int = 1_048_576
    memory: str = "256m"
    cpus: str = "1.0"
    pids_limit: int = 32


def sandbox_command(config: SandboxConfig, fixture_path: Path, script_path: Path) -> list[str]:
    return [
        "docker", "run", "--rm", "--network", "none", "--read-only",
        "--cap-drop=ALL", "--security-opt", "no-new-privileges",
        "--pids-limit", str(config.pids_limit), "--memory", config.memory,
        "--cpus", config.cpus, "--user", "65532:65532",
        "--tmpfs", "/tmp:rw,noexec,nosuid,size=16m",
        "-v", f"{fixture_path}:/work/fixture.json:ro",
        "-v", f"{script_path}:/work/main.py:ro",
        config.image, "python", "/work/main.py",
    ]


def run_generated_python(fixture: dict[str, object], script: str, config: SandboxConfig | None = None) -> dict[str, object]:
    config = config or SandboxConfig()
    if "AUD_SUD_API_KEY" in script or "DOCKER_HOST" in script:
        raise SandboxError("credential or Docker socket access is not permitted")
    with tempfile.TemporaryDirectory(prefix="aud-sud-sandbox-") as directory:
        root = Path(directory)
        fixture_path = root / "fixture.json"
        script_path = root / "main.py"
        fixture_path.write_text(json.dumps(fixture, sort_keys=True), encoding="utf-8")
        script_path.write_text(script, encoding="utf-8")
        command = sandbox_command(config, fixture_path, script_path)
        try:
            completed = subprocess.run(command, capture_output=True, text=True, timeout=config.timeout_seconds, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise SandboxError(f"sandbox failed to start or timed out: {exc}") from exc
        if len(completed.stdout.encode()) > config.stdout_limit:
            raise SandboxError("sandbox stdout exceeded the configured limit")
        if completed.returncode != 0:
            raise SandboxError(completed.stderr[-4000:] or f"sandbox exited {completed.returncode}")
        try:
            value = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise SandboxError("sandbox did not emit valid JSON") from exc
        if not isinstance(value, dict):
            raise SandboxError("sandbox result must be a JSON object")
        return value


class MockSandbox:
    """Local workflow test double; no generated code is executed on the host."""

    def run(self, fixture: dict[str, object], script: str) -> dict[str, object]:
        return {"mock_execution": True, "script_sha256": __import__("hashlib").sha256(script.encode()).hexdigest()}

