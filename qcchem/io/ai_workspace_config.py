"""AI workspace configuration loading."""

from __future__ import annotations

from pathlib import Path

import yaml

from qcchem.core.ai_workspace import AIProviderSpec

SUPPORTED_PROVIDER_KINDS = {"openai_compatible", "anthropic", "gemini", "local_compatible"}


def _parse_bool(value: object, *, field_name: str, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "1", "on"}:
            return True
        if normalized in {"false", "no", "0", "off"}:
            return False
    raise ValueError(f"{field_name} must be a boolean or boolean-like string.")


def load_ai_provider_spec(path: Path) -> AIProviderSpec:
    """Load a provider spec from a YAML file."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Expected top-level mapping with an 'ai_provider' entry.")
    provider_raw = raw.get("ai_provider")
    if not isinstance(provider_raw, dict):
        raise ValueError("Expected top-level mapping with an 'ai_provider' entry.")

    provider_kind = str(provider_raw.get("provider_kind", "openai_compatible")).strip()
    if provider_kind not in SUPPORTED_PROVIDER_KINDS:
        raise ValueError(f"provider_kind must be one of {sorted(SUPPORTED_PROVIDER_KINDS)}")

    capabilities = provider_raw.get("capabilities", [])
    if not isinstance(capabilities, list):
        raise ValueError("ai_provider.capabilities must be a list when provided.")

    return AIProviderSpec(
        provider_name=str(provider_raw.get("provider_name", "")).strip(),
        provider_kind=provider_kind,
        base_url=str(provider_raw.get("base_url", "")).strip(),
        api_key_ref=str(provider_raw.get("api_key_ref", "")).strip(),
        model=str(provider_raw.get("model", "")).strip(),
        timeout_seconds=int(provider_raw.get("timeout_seconds", 60)),
        default_temperature=float(provider_raw.get("default_temperature", 0.1)),
        default_max_tokens=int(provider_raw.get("default_max_tokens", 2000)),
        capabilities=[str(item) for item in capabilities],
        enabled=_parse_bool(provider_raw.get("enabled"), field_name="ai_provider.enabled", default=True),
    )
