"""Serialization, normalization and schema export helpers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Type

from pydantic import BaseModel


def canonical_json(value: Any) -> str:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json", exclude_none=True)
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def dump_json(model: BaseModel, path: str | Path) -> None:
    Path(path).write_text(
        json.dumps(model.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_model(model_type: Type[BaseModel], path: str | Path) -> BaseModel:
    return model_type.model_validate_json(Path(path).read_text(encoding="utf-8"))


def export_schemas(model_types: list[Type[BaseModel]], output_dir: str | Path) -> list[Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for model_type in model_types:
        path = output / f"{model_type.__name__}.schema.json"
        path.write_text(json.dumps(model_type.model_json_schema(), indent=2, sort_keys=True) + "\n")
        paths.append(path)
    return paths


def normalize_number(value: float | int, unit: str) -> tuple[float, str]:
    """Canonical numeric units used by deterministic scoring."""
    if unit == "minutes":
        return float(value) * 60.0, "seconds"
    if unit == "percent":
        return float(value) / 100.0, "fraction"
    return float(value), unit


def normalize_value(value: Any) -> Any:
    """Normalize JSON-like answer values without changing missingness semantics."""
    if isinstance(value, dict):
        return {key: normalize_value(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [normalize_value(item) for item in value]
    if isinstance(value, float) and value == 0:
        return 0.0
    return value

