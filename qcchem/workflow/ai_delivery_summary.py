"""Shared validation for compact AI delivery review handoff summaries."""

from __future__ import annotations

from typing import Any


AI_DELIVERY_REVIEW_RELEASE_GATE = "informational_only"
LATEST_REVIEW_EVENT_FIELDS = (
    "event_id",
    "timestamp",
    "delivery_id",
    "review_status",
    "reviewed_by",
    "review_source",
    "ticket_link_status",
)


def _is_nonnegative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_count_map(value: object, *, expected_total: int) -> bool:
    if not isinstance(value, dict):
        return False
    counts = []
    for key, count in value.items():
        if not isinstance(key, str) or not key.strip() or not _is_nonnegative_int(count):
            return False
        counts.append(count)
    return sum(counts) == expected_total


def _has_complete_latest_review_event(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    return all(isinstance(value.get(field), str) and str(value[field]).strip() for field in LATEST_REVIEW_EVENT_FIELDS)


def normalize_ai_delivery_review_summary(value: object) -> dict[str, Any]:
    """Return a release-readable AI review summary or an informational fallback."""
    unavailable = {
        "status": "not_available",
        "release_gate": AI_DELIVERY_REVIEW_RELEASE_GATE,
    }
    if not isinstance(value, dict):
        return unavailable

    available = value.get("available")
    source_path = value.get("source_path")
    delivery_count = value.get("delivery_count")
    review_event_count = value.get("review_event_count")
    latest_review_event = value.get("latest_review_event")
    provenance_log = value.get("review_provenance_log")
    if not (
        isinstance(available, bool)
        and isinstance(source_path, str)
        and source_path.strip()
        and _is_nonnegative_int(delivery_count)
        and _is_nonnegative_int(review_event_count)
        and isinstance(latest_review_event, dict)
        and isinstance(provenance_log, str)
        and provenance_log.strip()
    ):
        return unavailable

    assert isinstance(delivery_count, int)
    assert isinstance(review_event_count, int)
    if available != (delivery_count > 0):
        return unavailable
    if not _is_count_map(value.get("review_status_counts"), expected_total=delivery_count):
        return unavailable

    delivery_kind_counts = value.get("delivery_kind_counts")
    if delivery_kind_counts is not None and not _is_count_map(delivery_kind_counts, expected_total=delivery_count):
        return unavailable
    for field in ("linked_output_path_count", "return_note_count"):
        if field in value and not _is_nonnegative_int(value.get(field)):
            return unavailable

    if review_event_count == 0:
        if latest_review_event:
            return unavailable
    elif not _has_complete_latest_review_event(latest_review_event):
        return unavailable

    return {
        **value,
        "status": "available",
        "release_gate": AI_DELIVERY_REVIEW_RELEASE_GATE,
    }
