"""Real-space grid helpers for exploratory lattice-QED models."""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product

import numpy as np

from qcchem.core import LatticeQEDSpec, MoleculeSpec

ATOMIC_NUMBERS = {
    "H": 1,
    "He": 2,
    "Li": 3,
    "Be": 4,
    "B": 5,
    "C": 6,
    "N": 7,
    "O": 8,
    "F": 9,
    "Ne": 10,
}


@dataclass(slots=True)
class LatticeSite:
    """One N-D grid site."""

    linear_index: int
    index: tuple[int, ...]
    coordinate: tuple[float, ...]
    real_space_coordinate: tuple[float, float, float]


@dataclass(slots=True)
class LatticeLink:
    """One oriented nearest-neighbor gauge link."""

    linear_index: int
    start_site: int
    end_site: int
    direction: int


@dataclass(slots=True)
class LatticePlaquette:
    """One oriented elementary plaquette."""

    linear_index: int
    anchor_site: int
    directions: tuple[int, int]
    link_indices: tuple[int, int, int, int]
    orientations: tuple[int, int, int, int] = (1, 1, -1, -1)


@dataclass(slots=True)
class LatticeGrid:
    """Discretized real-space lattice and molecular projection."""

    dimensions: int
    shape: list[int]
    spacing: list[float]
    boundary: str
    origin_real_space: tuple[float, float, float]
    axes: list[tuple[float, float, float]]
    sites: list[LatticeSite] = field(default_factory=list)
    links: list[LatticeLink] = field(default_factory=list)
    plaquettes: list[LatticePlaquette] = field(default_factory=list)
    nuclear_charge_by_site: list[float] = field(default_factory=list)
    projected_nuclei: list[dict[str, object]] = field(default_factory=list)

    @property
    def site_count(self) -> int:
        return len(self.sites)

    def site_linear_index(self, index: tuple[int, ...]) -> int:
        strides: list[int] = []
        stride = 1
        for size in reversed(self.shape[1:]):
            stride *= size
            strides.insert(0, stride)
        strides.append(1)
        return int(sum(component * strides[axis] for axis, component in enumerate(index)))


def _atom_charge(symbol: str) -> int:
    try:
        return ATOMIC_NUMBERS[symbol]
    except KeyError as exc:
        raise ValueError(f"Unsupported atom symbol for lattice-QED projection: {symbol}") from exc


def _molecule_coordinates(molecule: MoleculeSpec) -> np.ndarray:
    return np.asarray([atom.coords for atom in molecule.geometry], dtype=float)


def _origin(molecule: MoleculeSpec, origin: str) -> np.ndarray:
    coordinates = _molecule_coordinates(molecule)
    normalized = origin.strip().lower()
    if normalized == "molecule_center":
        return np.mean(coordinates, axis=0)
    if normalized == "zero":
        return np.zeros(3, dtype=float)
    raise ValueError(f"Unsupported lattice-QED grid origin: {origin}")


def _principal_axes(molecule: MoleculeSpec, dimensions: int) -> np.ndarray:
    coordinates = _molecule_coordinates(molecule)
    centered = coordinates - np.mean(coordinates, axis=0)
    if len(coordinates) >= 2 and np.linalg.norm(centered) > 1.0e-12:
        _, _, vh = np.linalg.svd(centered, full_matrices=True)
        candidates = [row for row in vh]
    else:
        candidates = []
    candidates.extend(np.eye(3))

    axes: list[np.ndarray] = []
    for candidate in candidates:
        vector = np.asarray(candidate, dtype=float)
        for existing in axes:
            vector = vector - np.dot(vector, existing) * existing
        norm = np.linalg.norm(vector)
        if norm <= 1.0e-12:
            continue
        axes.append(vector / norm)
        if len(axes) == dimensions:
            break
    if len(axes) < dimensions:
        raise ValueError("Could not construct enough real-space axes for lattice-QED grid.")
    return np.asarray(axes, dtype=float)


def _axes(molecule: MoleculeSpec, spec: LatticeQEDSpec) -> np.ndarray:
    if spec.dimensions > 3:
        raise ValueError("lattice-QED real-space grids currently support up to 3 dimensions.")
    normalized = spec.grid.axes.strip().lower()
    if normalized == "principal":
        return _principal_axes(molecule, spec.dimensions)
    if normalized == "cartesian":
        return np.eye(3, dtype=float)[: spec.dimensions]
    raise ValueError(f"Unsupported lattice-QED grid axes: {spec.grid.axes}")


def _site_coordinate(index: tuple[int, ...], shape: list[int], spacing: list[float]) -> np.ndarray:
    return np.asarray(
        [
            (float(component) - (float(shape[axis] - 1) / 2.0)) * float(spacing[axis])
            for axis, component in enumerate(index)
        ],
        dtype=float,
    )


def _build_links(shape: list[int], boundary: str) -> list[LatticeLink]:
    dimensions = len(shape)
    periodic = boundary.strip().lower() == "periodic"
    links: list[LatticeLink] = []
    index_to_linear = {index: order for order, index in enumerate(product(*[range(size) for size in shape]))}
    for index in product(*[range(size) for size in shape]):
        for direction in range(dimensions):
            neighbor = list(index)
            neighbor[direction] += 1
            if neighbor[direction] >= shape[direction]:
                if not periodic:
                    continue
                neighbor[direction] = 0
            links.append(
                LatticeLink(
                    linear_index=len(links),
                    start_site=index_to_linear[tuple(index)],
                    end_site=index_to_linear[tuple(neighbor)],
                    direction=direction,
                )
            )
    return links


def _build_plaquettes(shape: list[int], boundary: str, links: list[LatticeLink]) -> list[LatticePlaquette]:
    dimensions = len(shape)
    if dimensions < 2:
        return []
    periodic = boundary.strip().lower() == "periodic"
    index_to_linear = {index: order for order, index in enumerate(product(*[range(size) for size in shape]))}
    link_lookup = {(link.start_site, link.direction): link.linear_index for link in links}
    plaquettes: list[LatticePlaquette] = []
    ranges = [range(size if periodic else size - 1) for size in shape]
    for anchor in product(*ranges):
        anchor_site = index_to_linear[tuple(anchor)]
        for first in range(dimensions):
            for second in range(first + 1, dimensions):
                step_first = list(anchor)
                step_second = list(anchor)
                step_first[first] = (step_first[first] + 1) % shape[first]
                step_second[second] = (step_second[second] + 1) % shape[second]
                if not periodic and (
                    anchor[first] + 1 >= shape[first] or anchor[second] + 1 >= shape[second]
                ):
                    continue
                site_first = index_to_linear[tuple(step_first)]
                site_second = index_to_linear[tuple(step_second)]
                try:
                    plaquette_links = (
                        link_lookup[(anchor_site, first)],
                        link_lookup[(site_first, second)],
                        link_lookup[(site_second, first)],
                        link_lookup[(anchor_site, second)],
                    )
                except KeyError:
                    continue
                plaquettes.append(
                    LatticePlaquette(
                        linear_index=len(plaquettes),
                        anchor_site=anchor_site,
                        directions=(first, second),
                        link_indices=plaquette_links,
                    )
                )
    return plaquettes


def build_lattice_grid(molecule: MoleculeSpec, spec: LatticeQEDSpec) -> LatticeGrid:
    """Build an N-D real-space lattice and project nuclei onto nearest sites."""
    boundary = spec.grid.boundary.strip().lower()
    if boundary not in {"open", "periodic"}:
        raise ValueError(f"Unsupported lattice-QED grid boundary: {spec.grid.boundary}")
    origin = _origin(molecule, spec.grid.origin)
    axes = _axes(molecule, spec)
    sites: list[LatticeSite] = []
    for linear_index, index in enumerate(product(*[range(size) for size in spec.grid.shape])):
        coordinate = _site_coordinate(tuple(index), spec.grid.shape, spec.grid.spacing)
        real_space = origin + coordinate @ axes
        sites.append(
            LatticeSite(
                linear_index=linear_index,
                index=tuple(int(value) for value in index),
                coordinate=tuple(float(value) for value in coordinate),
                real_space_coordinate=tuple(float(value) for value in real_space),
            )
        )

    links = _build_links(spec.grid.shape, boundary)
    plaquettes = _build_plaquettes(spec.grid.shape, boundary, links)
    nuclear_charge_by_site = [0.0 for _ in sites]
    projected_nuclei: list[dict[str, object]] = []
    for atom in molecule.geometry:
        atom_position = np.asarray(atom.coords, dtype=float)
        distances = [
            float(np.linalg.norm(atom_position - np.asarray(site.real_space_coordinate, dtype=float)))
            for site in sites
        ]
        site_index = int(np.argmin(distances))
        charge = float(_atom_charge(atom.symbol))
        nuclear_charge_by_site[site_index] += charge
        projected_nuclei.append(
            {
                "symbol": atom.symbol,
                "charge": charge,
                "site_index": site_index,
                "distance_to_site": distances[site_index],
            }
        )

    return LatticeGrid(
        dimensions=spec.dimensions,
        shape=list(spec.grid.shape),
        spacing=list(spec.grid.spacing),
        boundary=boundary,
        origin_real_space=tuple(float(value) for value in origin),
        axes=[tuple(float(value) for value in axis) for axis in axes],
        sites=sites,
        links=links,
        plaquettes=plaquettes,
        nuclear_charge_by_site=nuclear_charge_by_site,
        projected_nuclei=projected_nuclei,
    )
