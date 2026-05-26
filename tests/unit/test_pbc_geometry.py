from __future__ import annotations

import pytest

from qcchem.pbc.geometry import (
    cart_to_frac,
    cell_from_lengths_angles,
    frac_to_cart,
    minimum_image_displacement,
    validate_cell,
    wrap_positions,
)


def test_cell_from_lengths_angles_builds_orthorhombic_vectors() -> None:
    cell = cell_from_lengths_angles(10.0, 20.0, 30.0, 90.0, 90.0, 90.0)

    expected = (
        (10.0, 0.0, 0.0),
        (0.0, 20.0, 0.0),
        (0.0, 0.0, 30.0),
    )
    for actual_row, expected_row in zip(cell, expected):
        assert actual_row == pytest.approx(expected_row, abs=1.0e-12)
    assert validate_cell(cell) == cell


def test_fractional_cartesian_round_trip_for_tilted_cell() -> None:
    cell = cell_from_lengths_angles(8.0, 9.0, 10.0, 80.0, 75.0, 70.0)
    frac = (0.25, 0.5, 0.75)

    cart = frac_to_cart(frac, cell)

    assert cart_to_frac(cart, cell) == pytest.approx(frac, abs=1.0e-12)


def test_wrap_positions_respects_axis_flags() -> None:
    cell = cell_from_lengths_angles(10.0, 10.0, 10.0, 90.0, 90.0, 90.0)
    positions = [(11.5, -0.5, 12.0)]

    wrapped = wrap_positions(positions, cell, pbc=(True, False, True))

    assert wrapped[0] == pytest.approx((1.5, -0.5, 2.0), abs=1.0e-12)


def test_minimum_image_displacement_uses_periodic_axes_only() -> None:
    cell = cell_from_lengths_angles(10.0, 10.0, 10.0, 90.0, 90.0, 90.0)

    displacement = minimum_image_displacement(
        (9.5, 9.5, 9.5),
        (0.5, 0.5, 0.5),
        cell,
        pbc=(True, True, False),
    )

    assert displacement == pytest.approx((1.0, 1.0, -9.0), abs=1.0e-12)


def test_validate_cell_rejects_singular_cells() -> None:
    with pytest.raises(ValueError, match="non-zero volume"):
        validate_cell(((1.0, 0.0, 0.0), (2.0, 0.0, 0.0), (0.0, 0.0, 1.0)))
