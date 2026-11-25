"""Hosted-model abstraction with explicit live-execution gating and mocks."""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from typing import Any, Protocol, Type

from pydantic import BaseModel, ConfigDict, Field

from .schema import CommonAnswer, GeneratedProgram, InvestigationPlan, Question
from .serialization import canonical_json


class ModelConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model_id: str
    provider: str = "openai"
    temperature: float | None = 0.0
    top_p: float | None = 1.0
    max_output_tokens: int = 4096
    allow_live: bool = False
    api_base: str | None = None


class ModelResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: dict[str, Any]
    raw_text: str
    provider_response_id: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: float
    transport_retries: int = 0


class LLMClient(Protocol):
    def generate(self, *, purpose: str, question: Question, payload: dict[str, Any], schema: Type[BaseModel]) -> ModelResponse:
        ...


def live_execution_authorized(config: ModelConfig, cli_live: bool = False) -> bool:
    return config.allow_live and cli_live and os.environ.get("AUD_SUD_ALLOW_LIVE_API", "false").lower() == "true"


class LiveExecutionDisabled(RuntimeError):
    pass


@dataclass
class SemanticCallBudget:
    max_calls: int = 3
    used: int = 0

    def consume(self) -> None:
        if self.used >= self.max_calls:
            raise RuntimeError("semantic call budget exhausted")
        self.used += 1


def is_transient_transport_error(error: Exception) -> bool:
    text = str(error).lower()
    return isinstance(error, (TimeoutError, ConnectionError)) or any(token in text for token in ("429", "rate limit", "500", "502", "503", "504", "timeout", "temporarily unavailable"))


@dataclass
class MockClient:
    """Deterministic structured-output mock used by all local workflow tests."""

    model_id: str = "mock-development-model"

    def generate(self, *, purpose: str, question: Question, payload: dict[str, Any], schema: Type[BaseModel]) -> ModelResponse:
        started = time.perf_counter()
        if schema is InvestigationPlan:
            value = payload.get(
                "mock_plan",
                {
                    "plan_id": "mock-plan",
                    "intent": "mock coverage",
                    "participant_scope": "authorized_context_only",
                    "steps": [
                        {"id": "obs", "tool": "query_observations", "args": {"metric": "heart_rate", "method": "chest_ecg"}},
                        {"id": "coverage", "tool": "analyze_intervals", "args": {"operation": "coverage", "observation_ref": "obs"}},
                    ],
                    "output": "coverage",
                },
            )
        elif schema is GeneratedProgram:
            value = payload.get("mock_program", {"code": "import json\nprint(json.dumps({'status': 'computed'}))"})
        elif schema is CommonAnswer:
            value = payload.get("mock_answer", {"status": "insufficient", "limitations": [{"claim": "mock", "reason_code": "mock"}]})
        else:
            value = payload.get("mock_value", {})
        raw = json.dumps(value, sort_keys=True)
        return ModelResponse(value=value, raw_text=raw, provider_response_id=f"mock-{purpose}-{question.question_id}", input_tokens=len(canonical_json(payload)) // 4, output_tokens=len(raw) // 4, latency_ms=(time.perf_counter() - started) * 1000)


class HostedModelClient:
    """Small provider adapter; it cannot issue a request without explicit authorization."""

    def __init__(self, config: ModelConfig, *, cli_live: bool = False):
        self.config = config
        self.cli_live = cli_live
        if not live_execution_authorized(config, cli_live):
            raise LiveExecutionDisabled("live API calls require AUD_SUD_ALLOW_LIVE_API=true and --live")

    def generate(self, *, purpose: str, question: Question, payload: dict[str, Any], schema: Type[BaseModel]) -> ModelResponse:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("the optional hosted API SDK is not installed") from exc
        client = OpenAI(api_key=os.environ.get("AUD_SUD_API_KEY"), base_url=self.config.api_base)
        started = time.perf_counter()
        response = client.responses.parse(
            model=self.config.model_id,
            input=[
                {"role": "system", "content": f"Return only the requested {schema.__name__} JSON."},
                {"role": "user", "content": json.dumps(payload, sort_keys=True)},
            ],
            text_format=schema,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            max_output_tokens=self.config.max_output_tokens,
        )
        parsed = response.output_parsed
        if parsed is None:
            raise ValueError("provider returned no structured output")
        value = parsed.model_dump(mode="json") if isinstance(parsed, BaseModel) else parsed
        usage = getattr(response, "usage", None)
        return ModelResponse(
            value=value,
            raw_text=json.dumps(value, sort_keys=True),
            provider_response_id=getattr(response, "id", None),
            input_tokens=getattr(usage, "input_tokens", None),
            output_tokens=getattr(usage, "output_tokens", None),
            latency_ms=(time.perf_counter() - started) * 1000,
        )


@dataclass
class RetryingClient:
    """Transport retry wrapper; retries never create new semantic feedback."""

    underlying: LLMClient
    max_transport_retries: int = 2
    backoff_seconds: tuple[float, ...] = (1.0, 2.0)

    @property
    def model_id(self) -> str:
        return getattr(self.underlying, "model_id", "hosted")

    def generate(self, *, purpose: str, question: Question, payload: dict[str, Any], schema: Type[BaseModel]) -> ModelResponse:
        retries = 0
        while True:
            try:
                response = self.underlying.generate(purpose=purpose, question=question, payload=payload, schema=schema)
                return response.model_copy(update={"transport_retries": retries})
            except Exception as exc:
                if retries >= self.max_transport_retries or not is_transient_transport_error(exc):
                    raise
                time.sleep(self.backoff_seconds[min(retries, len(self.backoff_seconds) - 1)])
                retries += 1


def prompt_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()

