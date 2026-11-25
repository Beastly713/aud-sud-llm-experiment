"""Disposable offline Docker runner for System C generated Python."""

from __future__ import annotations

import json
import os
import re
import selectors
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path


class SandboxError(RuntimeError):
    pass


class SandboxConfigurationError(SandboxError):
    pass


_DIGEST_RE = re.compile(r"^.+@sha256:[0-9a-f]{64}$")


@dataclass(frozen=True)
class SandboxConfig:
    image: str = "python:3.12.8-slim@sha256:development-pin-required"
    timeout_seconds: int = 10
    stdout_limit: int = 1_048_576
    stderr_limit: int = 1_048_576
    memory: str = "256m"
    cpus: str = "1.0"
    pids_limit: int = 32

    @property
    def has_valid_digest(self) -> bool:
        return bool(_DIGEST_RE.fullmatch(self.image))

    def require_valid(self) -> None:
        if not self.has_valid_digest:
            raise SandboxConfigurationError("System C requires an approved image reference with a 64-hex sha256 digest")
        if self.timeout_seconds <= 0 or self.stdout_limit <= 0 or self.stderr_limit <= 0:
            raise SandboxConfigurationError("sandbox timeout and output limits must be positive")

    @classmethod
    def from_protocol(cls, root: Path | None = None) -> "SandboxConfig":
        root = root or Path(__file__).resolve().parents[2]
        config_path = root / "configs" / "protocol.yaml"
        try:
            import yaml
        except ImportError as exc:
            raise SandboxConfigurationError("PyYAML is required to load sandbox configuration") from exc
        try:
            document = yaml.safe_load(config_path.read_text(encoding="utf-8"))
            sandbox = document["sandbox"]
        except (OSError, KeyError, TypeError) as exc:
            raise SandboxConfigurationError(f"invalid sandbox configuration: {config_path}") from exc
        try:
            return cls(
                image=os.environ.get("AUD_SUD_SANDBOX_IMAGE", sandbox["image"]),
                timeout_seconds=int(sandbox["timeout_seconds"]),
                stdout_limit=int(document.get("program_stdout_byte_cap", 1_048_576)),
                stderr_limit=int(document.get("program_stderr_byte_cap", document.get("program_stdout_byte_cap", 1_048_576))),
                memory=str(sandbox["memory"]),
                cpus=str(sandbox["cpus"]),
                pids_limit=int(sandbox["pids_limit"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise SandboxConfigurationError(f"incomplete sandbox configuration: {config_path}") from exc


def sandbox_command(config: SandboxConfig, fixture_path: Path, script_path: Path) -> list[str]:
    return [
        "docker", "run", "--rm", "--network", "none", "--read-only",
        "--cap-drop=ALL", "--security-opt", "no-new-privileges:true",
        "--pids-limit", str(config.pids_limit), "--memory", config.memory,
        "--cpus", config.cpus, "--user", "65532:65532",
        "--tmpfs", "/tmp:rw,noexec,nosuid,size=16m",
        "-v", f"{fixture_path}:/work/fixture.json:ro",
        "-v", f"{script_path}:/work/main.py:ro",
        config.image, "python", "/work/main.py",
    ]


def _kill_and_wait(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is None:
        process.kill()
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=2)


def run_generated_python(fixture: dict[str, object], script: str, config: SandboxConfig | None = None) -> dict[str, object]:
    config = config or SandboxConfig.from_protocol()
    config.require_valid()
    if "AUD_SUD_API_KEY" in script or "OPENAI_API_KEY" in script or "DOCKER_HOST" in script:
        raise SandboxError("credential or Docker socket access is not permitted")
    with tempfile.TemporaryDirectory(prefix="aud-sud-sandbox-") as directory:
        root = Path(directory)
        fixture_path = root / "fixture.json"
        script_path = root / "main.py"
        fixture_path.write_text(json.dumps(fixture, sort_keys=True), encoding="utf-8")
        script_path.write_text(script, encoding="utf-8")
        # The container runs as a numeric non-root UID, so the disposable bind
        # mount must be traversable/readable without broadening any host access.
        os.chmod(root, 0o755)
        os.chmod(fixture_path, 0o644)
        os.chmod(script_path, 0o644)
        command = sandbox_command(config, fixture_path, script_path)
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError as exc:
            raise SandboxError(f"sandbox failed to start: {exc}") from exc
        selector = selectors.DefaultSelector()
        assert process.stdout is not None and process.stderr is not None
        selector.register(process.stdout, selectors.EVENT_READ, "stdout")
        selector.register(process.stderr, selectors.EVENT_READ, "stderr")
        stdout = bytearray()
        stderr = bytearray()
        deadline = time.monotonic() + config.timeout_seconds
        timed_out = False
        output_exceeded: str | None = None
        try:
            while selector.get_map():
                if time.monotonic() >= deadline:
                    timed_out = True
                    _kill_and_wait(process)
                    break
                for key, _ in selector.select(timeout=0.05):
                    chunk = os.read(key.fileobj.fileno(), 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    target = stdout if key.data == "stdout" else stderr
                    target.extend(chunk)
                    limit = config.stdout_limit if key.data == "stdout" else config.stderr_limit
                    if len(target) > limit:
                        output_exceeded = key.data
                        _kill_and_wait(process)
                        break
                if timed_out or output_exceeded:
                    break
            if process.poll() is None:
                _kill_and_wait(process)
            else:
                process.wait()
        finally:
            selector.close()
            if process.poll() is None:
                _kill_and_wait(process)
        if timed_out:
            raise SandboxError("sandbox execution timed out; container was terminated")
        if output_exceeded:
            raise SandboxError(f"sandbox {output_exceeded} exceeded the configured output limit; container was terminated")
        if process.returncode != 0:
            message = bytes(stderr)[-4000:].decode(errors="replace")
            raise SandboxError(message or f"sandbox exited {process.returncode}")
        try:
            value = json.loads(bytes(stdout).decode())
        except json.JSONDecodeError as exc:
            raise SandboxError("sandbox did not emit valid JSON") from exc
        if not isinstance(value, dict):
            raise SandboxError("sandbox result must be a JSON object")
        return value


@dataclass
class DockerSandbox:
    config: SandboxConfig
    is_mock: bool = False

    def run(self, fixture: dict[str, object], script: str) -> dict[str, object]:
        return run_generated_python(fixture, script, self.config)


class MockSandbox:
    """Local workflow test double; no generated code is executed on the host."""

    is_mock = True

    def run(self, fixture: dict[str, object], script: str) -> dict[str, object]:
        return {"mock_execution": True, "script_sha256": __import__("hashlib").sha256(script.encode()).hexdigest()}

