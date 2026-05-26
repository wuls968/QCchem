"""Small dependency-free geometry helpers for periodic cells."""

from __future__ import annotations

import math
import hashlib
import json
from typing import Iterable

Vector3 = tuple[float, float, float]
Cell = tuple[Vector3, Vector3, Vector3]

_VOLUME_TOLERANCE = 1.0e-12


def validate_cell(cell: Iterable[Iterable[float]]) -> Cell:
    """Normalize and validate a 3x3 cell matrix stored as row lattice vectors."""
    rows = tuple(tuple(float(value) for value in row) for row in cell)
    if len(rows) != 3 or any(len(row) != 3 for row in rows):
        raise ValueError("Cell vectors must be a 3x3 matrix.")
    normalized = rows  # type: ignore[assignment]
    if abs(_det3(normalized)) <= _VOLUME_TOLERANCE:
        raise ValueError("Cell vectors must span a non-zero volume.")
    return normalized


def cell_volume(cell: Iterable[Iterable[float]]) -> float:
    """Return the absolute cell volume."""
    return abs(_det3(validate_cell(cell)))


def validate_pbc_flags(values: Iterable[object]) -> tuple[bool, bool, bool]:
    """Normalize and validate three axis PBC flags."""
    flags = tuple(bool(value) for value in values)
    if len(flags) != 3:
        raise ValueError("PBC flags must contain exactly three values.")
    return flags


def normalize_cell_unit(unit: str | None) -> str:
    """Normalize a supported cell length unit."""
    normalized = (unit or "angstrom").strip().lower()
    if normalized in {"ang", "a"}:
        return "angstrom"
    if normalized == "au":
        return "bohr"
    if normalized not in {"angstrom", "bohr"}:
        raise ValueError("Cell unit must be angstrom or bohr.")
    return normalized


def normalized_periodic_payload(
    *,
    enabled: bool = False,
    vectors: Iterable[Iterable[float]] | None = None,
    pbc: Iterable[object] = (True, True, True),
    unit: str | None = "angstrom",
    coordinate_mode: str = "cartesian",
    wrap_policy: str = "preserve",
    source: str | None = None,
    lengths: Iterable[float] | None = None,
    angles: Iterable[float] | None = None,
) -> dict[str, object]:
    """Build a stable JSON-friendly PBC metadata payload."""
    payload: dict[str, object] = {
        "enabled": bool(enabled),
        "pbc": validate_pbc_flags(pbc),
        "coordinate_mode": coordinate_mode.strip().lower(),
        "wrap_policy": wrap_policy.strip().lower(),
        "source": source,
    }
    if vectors is not None:
        cell: dict[str, object] = {
            "vectors": validate_cell(vectors),
            "unit": normalize_cell_unit(unit),
        }
        if lengths is not None:
            length_values = tuple(float(value) for value in lengths)
            if len(length_values) != 3:
                raise ValueError("Cell lengths must contain exactly three values.")
            cell["lengths"] = length_values
        if angles is not None:
            angle_values = tuple(float(value) for value in angles)
            if len(angle_values) != 3:
                raise ValueError("Cell angles must contain exactly three values.")
            cell["angles"] = angle_values
        payload["cell"] = cell
    return payload


def periodic_fingerprint(periodic: dict[str, object]) -> str:
    """Hash normalized PBC metadata for provenance comparisons."""
    encoded = json.dumps(
        _jsonable(periodic),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def cell_from_lengths_angles(
    a: float,
    b: float,
    c: float,
    alpha: float,
    beta: float,
    gamma: float,
) -> Cell:
    """Build row lattice vectors from lengths and angles in degrees."""
    lengths = (float(a), float(b), float(c))
    if any(value <= 0.0 for value in lengths):
        raise ValueError("Cell lengths must be positive.")
    alpha_rad = math.radians(float(alpha))
    beta_rad = math.radians(float(beta))
    gamma_rad = math.radians(float(gamma))
    sin_gamma = math.sin(gamma_rad)
    if abs(sin_gamma) <= _VOLUME_TOLERANCE:
        raise ValueError("Cell gamma angle must not be singular.")

    ax = lengths[0]
    bx = lengths[1] * math.cos(gamma_rad)
    by = lengths[1] * sin_gamma
    cx = lengths[2] * math.cos(beta_rad)
    cy = lengths[2] * (
        math.cos(alpha_rad) - math.cos(beta_rad) * math.cos(gamma_rad)
    ) / sin_gamma
    cz_sq = lengths[2] * lengths[2] - cx * cx - cy * cy
    if cz_sq <= _VOLUME_TOLERANCE:
        raise ValueError("Cell lengths and angles must span a non-zero volume.")
    return validate_cell(
        (
            (ax, 0.0, 0.0),
            (bx, by, 0.0),
            (cx, cy, math.sqrt(cz_sq)),
        )
    )


def frac_to_cart(frac: Iterable[float], cell: Iterable[Iterable[float]]) -> Vector3:
    """Convert one fractional coordinate to Cartesian coordinates."""
    f0, f1, f2 = _vector3(frac, name="Fractional coordinate")
    a, b, c = validate_cell(cell)
    return (
        f0 * a[0] + f1 * b[0] + f2 * c[0],
        f0 * a[1] + f1 * b[1] + f2 * c[1],
        f0 * a[2] + f1 * b[2] + f2 * c[2],
    )


def cart_to_frac(cart: Iterable[float], cell: Iterable[Iterable[float]]) -> Vector3:
    """Convert one Cartesian coordinate to fractional coordinates."""
    x, y, z = _vector3(cart, name="Cartesian coordinate")
    inv = _inverse3(validate_cell(cell))
    return (
        x * inv[0][0] + y * inv[1][0] + z * inv[2][0],
        x * inv[0][1] + y * inv[1][1] + z * inv[2][1],
        x * inv[0][2] + y * inv[1][2] + z * inv[2][2],
    )


def wrap_positions(
    positions: Iterable[Iterable[float]],
    cell: Iterable[Iterable[float]],
    pbc: tuple[bool, bool, bool] = (True, True, True),
) -> list[Vector3]:
    """Wrap Cartesian positions into the primary cell on periodic axes."""
    checked_cell = validate_cell(cell)
    flags = _pbc_flags(pbc)
    wrapped: list[Vector3] = []
    for position in positions:
        frac = list(cart_to_frac(position, checked_cell))
        for axis, enabled in enumerate(flags):
            if enabled:
                frac[axis] = frac[axis] % 1.0
        wrapped.append(frac_to_cart(frac, checked_cell))
    return wrapped


def minimum_image_displacement(
    start: Iterable[float],
    end: Iterable[float],
    cell: Iterable[Iterable[float]],
    *,
    pbc: tuple[bool, bool, bool] = (True, True, True),
) -> Vector3:
    """Return the shortest Cartesian displacement from start to end."""
    checked_cell = validate_cell(cell)
    flags = _pbc_flags(pbc)
    start_frac = cart_to_frac(start, checked_cell)
    end_frac = cart_to_frac(end, checked_cell)
    delta = [end_frac[index] - start_frac[index] for index in range(3)]
    for axis, enabled in enumerate(flags):
        if enabled:
            delta[axis] -= round(delta[axis])
    return frac_to_cart(delta, checked_cell)


def _vector3(values: Iterable[float], *, name: str) -> Vector3:
    vector = tuple(float(value) for value in values)
    if len(vector) != 3:
        raise ValueError(f"{name} must contain exactly three values.")
    return vector


def _pbc_flags(values: tuple[bool, bool, bool]) -> tuple[bool, bool, bool]:
    return validate_pbc_flags(values)


def _jsonable(value: object) -> object:
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, float):
        return round(value, 12)
    return value


def _det3(matrix: Cell) -> float:
    return (
        matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1])
        - matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0])
        + matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0])
    )


def _inverse3(matrix: Cell) -> Cell:
    det = _det3(matrix)
    if abs(det) <= _VOLUME_TOLERANCE:
        raise ValueError("Cell vectors must span a non-zero volume.")
    inv_det = 1.0 / det
    return (
        (
            (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1]) * inv_det,
            (matrix[0][2] * matrix[2][1] - matrix[0][1] * matrix[2][2]) * inv_det,
            (matrix[0][1] * matrix[1][2] - matrix[0][2] * matrix[1][1]) * inv_det,
        ),
        (
            (matrix[1][2] * matrix[2][0] - matrix[1][0] * matrix[2][2]) * inv_det,
            (matrix[0][0] * matrix[2][2] - matrix[0][2] * matrix[2][0]) * inv_det,
            (matrix[0][2] * matrix[1][0] - matrix[0][0] * matrix[1][2]) * inv_det,
        ),
        (
            (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0]) * inv_det,
            (matrix[0][1] * matrix[2][0] - matrix[0][0] * matrix[2][1]) * inv_det,
            (matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]) * inv_det,
        ),
    )
