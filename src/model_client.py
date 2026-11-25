"""Hosted-model clients, provider-specific structured output and local validation."""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from typing import Any, Protocol, Type

from pydantic import BaseModel, ConfigDict, field_validator

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

    @field_validator("model_id")
    @classmethod
    def nonempty_model(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("AUD_SUD_MODEL_ID is required for live execution")
        return value

    @field_validator("provider")
    @classmethod
    def supported_provider(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"openai", "gemini"}:
            raise ValueError("AUD_SUD_PROVIDER must be openai or gemini")
        return normalized


class ModelResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: dict[str, Any]
    raw_text: str
    raw_response: str | None = None
    provider_response_id: str | None = None
    model_id: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    latency_ms: float
    transport_retries: int = 0


class LLMClient(Protocol):
    model_id: str
    is_mock: bool

    def generate(self, *, purpose: str, question: Question, payload: dict[str, Any], schema: Type[BaseModel]) -> ModelResponse:
        ...


class LiveExecutionDisabled(RuntimeError):
    pass


class LiveConfigurationError(RuntimeError):
    pass


def live_execution_authorized(config: ModelConfig, cli_live: bool = False) -> bool:
    return config.allow_live and cli_live and os.environ.get("AUD_SUD_ALLOW_LIVE_API", "false").lower() == "true"


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
    return isinstance(error, (TimeoutError, ConnectionError)) or any(
        token in text for token in ("429", "rate limit", "500", "502", "503", "504", "timeout", "temporarily unavailable")
    )


def _validate_structured(value: Any, schema: Type[BaseModel]) -> dict[str, Any]:
    validated = schema.model_validate(value)
    return validated.model_dump(mode="json")


@dataclass
class MockClient:
    """Deterministic structured-output mock used only by offline tests."""

    model_id: str = "mock-development-model"
    is_mock: bool = True

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
        value = _validate_structured(value, schema)
        raw = json.dumps(value, sort_keys=True)
        return ModelResponse(
            value=value,
            raw_text=raw,
            raw_response=raw,
            provider_response_id=f"mock-{purpose}-{question.question_id}",
            model_id=self.model_id,
            input_tokens=len(canonical_json(payload)) // 4,
            output_tokens=len(raw) // 4,
            total_tokens=(len(canonical_json(payload)) + len(raw)) // 4,
            latency_ms=(time.perf_counter() - started) * 1000,
        )


def _safe_provider_dump(response: Any) -> str | None:
    """Serialize provider metadata only; credentials are never part of responses."""
    try:
        if hasattr(response, "model_dump_json"):
            return response.model_dump_json()
        if hasattr(response, "to_json"):
            return response.to_json()
    except Exception:
        return None
    return None


def _gemini_schema(schema: Type[BaseModel]) -> dict[str, Any]:
    """Convert Pydantic JSON Schema to a conservative Gemini response schema.

    Gemini's response-schema dialect is not treated as a drop-in implementation of
    JSON Schema. References, discriminators, defaults and multi-branch unions are
    normalized before the request; the complete Pydantic model still validates the
    returned JSON locally.
    """
    source = schema.model_json_schema()
    definitions = source.get("$defs", {})

    def convert(node: Any, stack: tuple[str, ...] = ()) -> Any:
        if isinstance(node, list):
            return [convert(item, stack) for item in node]
        if not isinstance(node, dict):
            return node
        if "$ref" in node:
            name = node["$ref"].rsplit("/", 1)[-1]
            if name in stack:
                return {"type": "object"}
            return convert(definitions.get(name, {"type": "object"}), stack + (name,))
        if "anyOf" in node:
            branches = [branch for branch in node["anyOf"] if branch != {"type": "null"}]
            if len(branches) == 1:
                return convert(branches[0], stack)
            return {"type": "object"}
        if "oneOf" in node:
            branches = [convert(branch, stack) for branch in node["oneOf"]]
            objects = [branch for branch in branches if isinstance(branch, dict) and branch.get("type") == "object"]
            if objects:
                properties: dict[str, Any] = {}
                for branch in objects:
                    properties.update(branch.get("properties", {}))
                return {"type": "object", "properties": properties}
            return {"type": "object"}
        output: dict[str, Any] = {}
        for key, value in node.items():
            if key in {
                "$schema", "$defs", "title", "default", "description", "discriminator", "examples",
                "additionalProperties", "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum",
                "minLength", "maxLength", "pattern", "minItems", "maxItems", "uniqueItems",
                "readOnly", "writeOnly",
            }:
                continue
            if key == "const":
                output["enum"] = [value]
                continue
            output[key] = convert(value, stack)
        return output

    converted = convert({key: value for key, value in source.items() if key != "$defs"})
    if not isinstance(converted, dict) or converted.get("type") != "object":
        raise ValueError(f"Gemini response schema conversion did not produce an object for {schema.__name__}")
    return converted


class HostedModelClient:
    """Provider adapter gated by explicit environment and CLI authorization."""

    is_mock = False

    def __init__(self, config: ModelConfig, *, cli_live: bool = False):
        self.config = config
        self.model_id = config.model_id
        self.cli_live = cli_live
        if not live_execution_authorized(config, cli_live):
            raise LiveExecutionDisabled("live API calls require AUD_SUD_ALLOW_LIVE_API=true and --live")
        if not os.environ.get("AUD_SUD_API_KEY"):
            raise LiveConfigurationError("AUD_SUD_API_KEY is required for live execution")

    def generate(self, *, purpose: str, question: Question, payload: dict[str, Any], schema: Type[BaseModel]) -> ModelResponse:
        if self.config.provider == "openai":
            return self._generate_openai(purpose, question, payload, schema)
        if self.config.provider == "gemini":
            return self._generate_gemini(purpose, question, payload, schema)
        raise LiveConfigurationError(f"unsupported provider: {self.config.provider}")

    def _generate_openai(self, purpose: str, question: Question, payload: dict[str, Any], schema: Type[BaseModel]) -> ModelResponse:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise LiveConfigurationError("openai SDK is not installed") from exc
        client = OpenAI(api_key=os.environ["AUD_SUD_API_KEY"], base_url=self.config.api_base)
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
        value = _validate_structured(parsed.model_dump(mode="json") if isinstance(parsed, BaseModel) else parsed, schema)
        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "input_tokens", None)
        output_tokens = getattr(usage, "output_tokens", None)
        return ModelResponse(
            value=value,
            raw_text=getattr(response, "output_text", None) or json.dumps(value, sort_keys=True),
            raw_response=_safe_provider_dump(response),
            provider_response_id=getattr(response, "id", None),
            model_id=getattr(response, "model", None) or self.config.model_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=(input_tokens + output_tokens) if input_tokens is not None and output_tokens is not None else None,
            latency_ms=(time.perf_counter() - started) * 1000,
        )

    def _generate_gemini(self, purpose: str, question: Question, payload: dict[str, Any], schema: Type[BaseModel]) -> ModelResponse:
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise LiveConfigurationError("google-genai SDK is not installed") from exc
        client = genai.Client(api_key=os.environ["AUD_SUD_API_KEY"])
        started = time.perf_counter()
        config_kwargs: dict[str, Any] = {
            "response_mime_type": "application/json",
            "response_schema": _gemini_schema(schema),
            "max_output_tokens": self.config.max_output_tokens,
        }
        if self.config.temperature is not None:
            config_kwargs["temperature"] = self.config.temperature
        if self.config.top_p is not None:
            config_kwargs["top_p"] = self.config.top_p
        config = types.GenerateContentConfig(
            **config_kwargs,
        )
        response = client.models.generate_content(
            model=self.config.model_id,
            contents=json.dumps(payload, sort_keys=True),
            config=config,
        )
        raw_text = getattr(response, "text", None)
        if not raw_text:
            raise ValueError("Gemini returned no structured JSON text")
        try:
            value = _validate_structured(json.loads(raw_text), schema)
        except (json.JSONDecodeError, ValueError, TypeError) as exc:
            raise ValueError(f"Gemini structured output failed local {schema.__name__} validation") from exc
        usage = getattr(response, "usage_metadata", None)
        input_tokens = getattr(usage, "prompt_token_count", None)
        output_tokens = getattr(usage, "candidates_token_count", None)
        total_tokens = getattr(usage, "total_token_count", None)
        return ModelResponse(
            value=value,
            raw_text=raw_text,
            raw_response=_safe_provider_dump(response),
            provider_response_id=getattr(response, "response_id", None) or getattr(response, "id", None),
            model_id=self.config.model_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
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
        return self.underlying.model_id

    @property
    def is_mock(self) -> bool:
        return self.underlying.is_mock

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

