"""Validate statement payloads for Elasticsearch-compatible dict keys.

Elasticsearch rejects some JSON object keys at indexation time (e.g. empty strings).
Dots in field names are also problematic because ES treats them as nested paths.
When the LRS backend is Elasticsearch, we reject such keys during API validation
so clients get an explicit error instead of a bulk indexation failure.
"""

from __future__ import annotations

from typing import Any, List, Optional

from rfc3987 import parse

from ralph.conf import settings


class ElasticsearchKeyValidationError(ValueError):
    """Raised when a statement contains dict keys incompatible with Elasticsearch."""


def elasticsearch_key_validation_enabled() -> bool:
    """Return whether ES key validation should run for incoming statements."""
    return (
        settings.RUNSERVER_BACKEND == "es"
        and settings.LRS_ELASTICSEARCH_VALIDATE_KEYS
    )


def _is_valid_iri(key: str) -> bool:
    """Return whether *key* is a valid RFC 3987 IRI (xAPI extension map keys)."""
    try:
        parse(key, rule="IRI")
        return True
    except (ValueError, TypeError):
        return False


def _invalid_key_reason(key: str) -> Optional[str]:
    if key == "":
        return "empty string"
    if "." in key and not _is_valid_iri(key):
        return "'.'"
    return None


def find_invalid_elasticsearch_keys(payload: Any) -> List[str]:
    """Return human-readable reasons for each invalid dict key in *payload*."""
    invalid: List[str] = []

    def walk(obj: Any, path: str) -> None:
        if isinstance(obj, dict):
            for key, value in obj.items():
                key_str = str(key)
                location = f"{path}.{key_str}" if path else key_str
                reason = _invalid_key_reason(key_str)
                if reason == "empty string":
                    parent = path or "root"
                    invalid.append(
                        f"elasticsearch-incompatible key: empty string at {parent}"
                    )
                elif reason == "'.'":
                    invalid.append(
                        f"elasticsearch-incompatible key: '.' in {location!r}"
                    )
                walk(value, location)
        elif isinstance(obj, list):
            for index, item in enumerate(obj):
                walk(item, f"{path}[{index}]")

    walk(payload, "")
    return invalid


def validate_elasticsearch_keys(payload: Any) -> None:
    """Raise :class:`ElasticsearchKeyValidationError` if *payload* has invalid keys."""
    invalid = find_invalid_elasticsearch_keys(payload)
    if invalid:
        if len(invalid) == 1:
            raise ElasticsearchKeyValidationError(invalid[0])
        raise ElasticsearchKeyValidationError(
            f"{invalid[0]} (+{len(invalid) - 1} more)"
        )
