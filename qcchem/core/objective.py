"""Research Objective domain objects for Trust-First research loops."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


OBJECTIVE_SCHEMA_VERSION = "qcchem.objective.v0.1-alpha"


@dataclass(slots=True)
class ResearchObjectiveSpec:
    """Research objective loaded from a Trust-First objective YAML."""

    name: str
    title: str
    claim: str
    system_scope: dict[str, Any] = field(default_factory=dict)
    required_evidence: list[str] = field(default_factory=list)
    candidate_configs: list[Path] = field(default_factory=list)
    optional_configs: list[Path] = field(default_factory=list)
    linked_artifacts: list[Path] = field(default_factory=list)
    promotion_policy: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, str] = field(default_factory=dict)
    source_path: Path | None = None

    def to_record(self) -> dict[str, Any]:
        """Return a JSON-safe record."""
        record = asdict(self)
        record["candidate_configs"] = [str(path) for path in self.candidate_configs]
        record["optional_configs"] = [str(path) for path in self.optional_configs]
        record["linked_artifacts"] = [str(path) for path in self.linked_artifacts]
        record["source_path"] = None if self.source_path is None else str(self.source_path)
        return record
