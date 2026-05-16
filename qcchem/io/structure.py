"""Dependency-free molecular structure file parsing."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from qcchem.core import AtomSpec

SUPPORTED_STRUCTURE_FORMATS = {"xyz", "pdb", "mol", "sdf", "mol2"}

_EXTENSION_FORMATS = {
    ".xyz": "xyz",
    ".pdb": "pdb",
    ".ent": "pdb",
    ".mol": "mol",
    ".sdf": "sdf",
    ".mol2": "mol2",
}

_ELEMENTS = {
    "H",
    "He",
    "Li",
    "Be",
    "B",
    "C",
    "N",
    "O",
    "F",
    "Ne",
    "Na",
    "Mg",
    "Al",
    "Si",
    "P",
    "S",
    "Cl",
    "Ar",
    "K",
    "Ca",
    "Sc",
    "Ti",
    "V",
    "Cr",
    "Mn",
    "Fe",
    "Co",
    "Ni",
    "Cu",
    "Zn",
    "Ga",
    "Ge",
    "As",
    "Se",
    "Br",
    "Kr",
    "Rb",
    "Sr",
    "Y",
    "Zr",
    "Nb",
    "Mo",
    "Tc",
    "Ru",
    "Rh",
    "Pd",
    "Ag",
    "Cd",
    "In",
    "Sn",
    "Sb",
    "Te",
    "I",
    "Xe",
    "Cs",
    "Ba",
    "La",
    "Ce",
    "Pr",
    "Nd",
    "Pm",
    "Sm",
    "Eu",
    "Gd",
    "Tb",
    "Dy",
    "Ho",
    "Er",
    "Tm",
    "Yb",
    "Lu",
    "Hf",
    "Ta",
    "W",
    "Re",
    "Os",
    "Ir",
    "Pt",
    "Au",
    "Hg",
    "Tl",
    "Pb",
    "Bi",
    "Po",
    "At",
    "Rn",
}


@dataclass(slots=True)
class StructureParseResult:
    """Parsed atoms plus reproducibility metadata."""

    atoms: list[AtomSpec]
    provenance: dict[str, object]


def infer_structure_format(path: Path, explicit_format: str | None = None) -> str:
    """Infer a supported structure format from an explicit value or filename."""
    if explicit_format is not None:
        normalized = explicit_format.strip().lower()
        if normalized not in SUPPORTED_STRUCTURE_FORMATS:
            raise ValueError(
                f"Unsupported molecule.structure_format '{explicit_format}'. "
                f"Supported formats: {', '.join(sorted(SUPPORTED_STRUCTURE_FORMATS))}."
            )
        return normalized
    suffix = path.suffix.lower()
    if suffix not in _EXTENSION_FORMATS:
        raise ValueError(
            f"Cannot infer structure format from extension '{suffix}'. "
            "Set molecule.structure_format explicitly."
        )
    return _EXTENSION_FORMATS[suffix]


def normalized_geometry_sha256(atoms: list[AtomSpec]) -> str:
    """Hash a normalized geometry payload independent of input-file formatting."""
    payload = [
        {
            "symbol": atom.symbol,
            "coords": [round(float(value), 12) for value in atom.coords],
        }
        for atom in atoms
    ]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_inline_geometry_provenance(atoms: list[AtomSpec], *, unit: str) -> dict[str, object]:
    """Build a provenance record for existing inline YAML geometry inputs."""
    return {
        "kind": "inline_geometry",
        "format": "inline",
        "parser": "qcchem.io.config:_parse_atoms",
        "atom_count": len(atoms),
        "unit": unit,
        "normalized_geometry_sha256": normalized_geometry_sha256(atoms),
    }


def load_structure_file(
    path: Path,
    *,
    structure_format: str | None = None,
    source_path: str | None = None,
) -> StructureParseResult:
    """Load a molecular structure file and return atoms plus provenance."""
    resolved_path = path.expanduser().resolve()
    if not resolved_path.exists():
        raise ValueError(f"Structure file does not exist: {resolved_path}")
    raw_bytes = resolved_path.read_bytes()
    if not raw_bytes.strip():
        raise ValueError(f"Structure file is empty: {resolved_path}")
    text = raw_bytes.decode("utf-8")
    fmt = infer_structure_format(resolved_path, structure_format)
    parser = _PARSERS[fmt]
    atoms, selection = parser(text)
    _validate_atoms(atoms, fmt)
    provenance: dict[str, object] = {
        "kind": "structure_file",
        "format": fmt,
        "parser": f"qcchem.io.structure:{fmt}",
        "source_path": source_path or str(path),
        "resolved_path": str(resolved_path),
        "file_name": resolved_path.name,
        "file_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "normalized_geometry_sha256": normalized_geometry_sha256(atoms),
        "atom_count": len(atoms),
        "unit": "angstrom",
        "record_selection": selection,
    }
    return StructureParseResult(atoms=atoms, provenance=provenance)


def _validate_atoms(atoms: list[AtomSpec], fmt: str) -> None:
    if not atoms:
        raise ValueError(f"{fmt.upper()} structure contains no atoms.")
    for index, atom in enumerate(atoms, start=1):
        if atom.symbol not in _ELEMENTS:
            raise ValueError(f"Unsupported or invalid element symbol at atom {index}: {atom.symbol}")
        if len(atom.coords) != 3:
            raise ValueError(f"Atom {index} does not have exactly three coordinates.")


def _normalize_symbol(value: str) -> str:
    token = re.sub(r"[^A-Za-z]", "", value.strip())
    if not token:
        raise ValueError("Missing element symbol in structure file.")
    for size in (2, 1):
        candidate = token[:size].capitalize()
        if candidate in _ELEMENTS:
            return candidate
    return token.capitalize()


def _float_triplet(values: list[str], *, context: str) -> tuple[float, float, float]:
    if len(values) < 3:
        raise ValueError(f"{context} must contain three coordinates.")
    try:
        return (float(values[0]), float(values[1]), float(values[2]))
    except ValueError as exc:
        raise ValueError(f"{context} contains a non-numeric coordinate.") from exc


def _parse_xyz(text: str) -> tuple[list[AtomSpec], dict[str, object]]:
    lines = text.splitlines()
    if len(lines) < 2:
        raise ValueError("XYZ file must contain an atom-count line and a comment line.")
    try:
        atom_count = int(lines[0].strip())
    except ValueError as exc:
        raise ValueError("XYZ atom-count line must be an integer.") from exc
    if atom_count <= 0:
        raise ValueError("XYZ atom count must be positive.")
    atom_lines = lines[2 : 2 + atom_count]
    if len(atom_lines) != atom_count:
        raise ValueError("XYZ atom count does not match the available atom records.")
    atoms: list[AtomSpec] = []
    for index, line in enumerate(atom_lines, start=1):
        parts = line.split()
        if len(parts) < 4:
            raise ValueError(f"XYZ atom line {index} must contain symbol and x y z coordinates.")
        atoms.append(
            AtomSpec(
                symbol=_normalize_symbol(parts[0]),
                coords=_float_triplet(parts[1:4], context=f"XYZ atom line {index}"),
            )
        )
    return atoms, {"record_index": 1, "policy": "first_xyz_frame"}


def _parse_pdb(text: str) -> tuple[list[AtomSpec], dict[str, object]]:
    atoms: list[AtomSpec] = []
    saw_model = False
    in_first_model = False
    for line in text.splitlines():
        record = line[:6].strip().upper()
        if record == "MODEL":
            if saw_model:
                break
            saw_model = True
            in_first_model = True
            continue
        if record == "ENDMDL" and saw_model:
            break
        if record not in {"ATOM", "HETATM"}:
            continue
        if saw_model and not in_first_model:
            continue
        try:
            coords = (float(line[30:38]), float(line[38:46]), float(line[46:54]))
        except ValueError as exc:
            raise ValueError("PDB ATOM/HETATM record contains invalid coordinates.") from exc
        symbol = line[76:78].strip() if len(line) >= 78 else ""
        if not symbol:
            symbol = line[12:16].strip()
        atoms.append(AtomSpec(symbol=_normalize_symbol(symbol), coords=coords))
    if not atoms:
        raise ValueError("PDB file contains no ATOM/HETATM records.")
    return atoms, {"model_index": 1 if saw_model else None, "policy": "first_pdb_model"}


def _first_sdf_record(text: str) -> str:
    for record in text.split("$$$$"):
        if record.strip():
            return record
    return text


def _parse_mol_or_sdf(text: str) -> tuple[list[AtomSpec], dict[str, object]]:
    record = _first_sdf_record(text)
    lines = record.splitlines()
    if len(lines) < 4:
        raise ValueError("MOL/SDF V2000 file is too short.")
    counts = lines[3]
    if "V2000" not in counts:
        raise ValueError("Only MOL/SDF V2000 connection tables are supported.")
    try:
        atom_count = int(counts[0:3])
    except ValueError as exc:
        raise ValueError("MOL/SDF V2000 counts line must include an atom count.") from exc
    if atom_count <= 0:
        raise ValueError("MOL/SDF V2000 atom count must be positive.")
    atom_lines = lines[4 : 4 + atom_count]
    if len(atom_lines) != atom_count:
        raise ValueError("MOL/SDF V2000 atom count does not match atom records.")
    atoms: list[AtomSpec] = []
    for index, line in enumerate(atom_lines, start=1):
        parts = line.split()
        if len(parts) < 4:
            raise ValueError(f"MOL/SDF atom line {index} must contain x y z symbol.")
        atoms.append(
            AtomSpec(
                symbol=_normalize_symbol(parts[3]),
                coords=_float_triplet(parts[0:3], context=f"MOL/SDF atom line {index}"),
            )
        )
    return atoms, {"record_index": 1, "policy": "first_sdf_record"}


def _parse_mol2(text: str) -> tuple[list[AtomSpec], dict[str, object]]:
    atoms: list[AtomSpec] = []
    in_atom_section = False
    for line in text.splitlines():
        stripped = line.strip()
        upper = stripped.upper()
        if upper.startswith("@<TRIPOS>"):
            if upper == "@<TRIPOS>ATOM":
                if atoms:
                    break
                in_atom_section = True
                continue
            if in_atom_section:
                break
            continue
        if not in_atom_section or not stripped:
            continue
        parts = stripped.split()
        if len(parts) < 6:
            raise ValueError("MOL2 ATOM records must contain id, name, x, y, z, and type.")
        atom_type = parts[5].split(".", maxsplit=1)[0]
        symbol_source = atom_type if atom_type and atom_type.upper() != "DU" else parts[1]
        atoms.append(
            AtomSpec(
                symbol=_normalize_symbol(symbol_source),
                coords=_float_triplet(parts[2:5], context="MOL2 atom record"),
            )
        )
    if not atoms:
        raise ValueError("MOL2 file contains no @<TRIPOS>ATOM records.")
    return atoms, {"record_index": 1, "policy": "first_mol2_molecule"}


_PARSERS: dict[str, Callable[[str], tuple[list[AtomSpec], dict[str, object]]]] = {
    "xyz": _parse_xyz,
    "pdb": _parse_pdb,
    "mol": _parse_mol_or_sdf,
    "sdf": _parse_mol_or_sdf,
    "mol2": _parse_mol2,
}
