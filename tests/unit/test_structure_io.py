from __future__ import annotations

from pathlib import Path

import pytest

from qcchem.io.structure import infer_structure_format, load_structure_file


XYZ_TEXT = """2
hydrogen
H 0.0 0.0 0.0
H 0.0 0.0 0.735
"""

PDB_TEXT = """MODEL        1
HETATM    1  H1  H2      1       0.000   0.000   0.000  1.00  0.00           H
HETATM    2  H2  H2      1       0.000   0.000   0.735  1.00  0.00           H
ENDMDL
MODEL        2
HETATM    1  H1  H2      1       9.000   9.000   9.000  1.00  0.00           H
ENDMDL
"""

PDB_CRYST1_TEXT = """CRYST1   12.000   13.000   14.000  90.00 100.00 120.00 P 1           1
HETATM    1  O   HOH A   1       1.000   2.000   3.000  1.00  0.00           O
HETATM    2  H1  HOH A   1       1.700   2.000   3.000  1.00  0.00           H
HETATM    3  H2  HOH A   1       1.000   2.700   3.000  1.00  0.00           H
END
"""

MOL_TEXT = """
  QCchem

  2  1  0  0  0  0            999 V2000
    0.0000    0.0000    0.0000 H   0  0  0  0  0  0  0  0  0  0  0  0
    0.0000    0.0000    0.7350 H   0  0  0  0  0  0  0  0  0  0  0  0
  1  2  1  0  0  0  0
M  END
"""

SDF_TEXT = MOL_TEXT + "$$$$\n" + MOL_TEXT.replace("0.7350", "9.0000") + "$$$$\n"

MOL2_TEXT = """@<TRIPOS>MOLECULE
H2
2 1 0 0 0
SMALL
NO_CHARGES
@<TRIPOS>ATOM
1 H1 0.0000 0.0000 0.0000 H 1 H2 0.0
2 H2 0.0000 0.0000 0.7350 H 1 H2 0.0
@<TRIPOS>BOND
1 1 2 1
"""


@pytest.mark.parametrize(
    ("filename", "text", "expected_format"),
    [
        ("h2.xyz", XYZ_TEXT, "xyz"),
        ("h2.pdb", PDB_TEXT, "pdb"),
        ("h2.mol", MOL_TEXT, "mol"),
        ("h2.sdf", SDF_TEXT, "sdf"),
        ("h2.mol2", MOL2_TEXT, "mol2"),
    ],
)
def test_load_structure_file_parses_supported_formats(
    tmp_path: Path,
    filename: str,
    text: str,
    expected_format: str,
) -> None:
    path = tmp_path / filename
    path.write_text(text, encoding="utf-8")

    parsed = load_structure_file(path)

    assert [atom.symbol for atom in parsed.atoms] == ["H", "H"]
    assert parsed.atoms[1].coords[2] == pytest.approx(0.735)
    assert parsed.provenance["format"] == expected_format
    assert parsed.provenance["atom_count"] == 2
    assert parsed.provenance["file_sha256"]
    assert parsed.provenance["normalized_geometry_sha256"]
    assert parsed.provenance["resolved_path"] == str(path.resolve())


def test_explicit_structure_format_overrides_extension(tmp_path: Path) -> None:
    path = tmp_path / "h2.structure"
    path.write_text(XYZ_TEXT, encoding="utf-8")

    parsed = load_structure_file(path, structure_format="xyz", source_path="inputs/h2.structure")

    assert parsed.provenance["format"] == "xyz"
    assert parsed.provenance["source_path"] == "inputs/h2.structure"


def test_infer_structure_format_rejects_unknown_extension(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Cannot infer structure format"):
        infer_structure_format(tmp_path / "h2.cif")


def test_load_structure_file_rejects_empty_file(tmp_path: Path) -> None:
    path = tmp_path / "empty.xyz"
    path.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="empty"):
        load_structure_file(path)


def test_load_structure_file_rejects_xyz_atom_count_mismatch(tmp_path: Path) -> None:
    path = tmp_path / "bad.xyz"
    path.write_text("3\nbad\nH 0 0 0\nH 0 0 1\n", encoding="utf-8")

    with pytest.raises(ValueError, match="atom count"):
        load_structure_file(path)


def test_load_structure_file_rejects_pdb_without_atoms(tmp_path: Path) -> None:
    path = tmp_path / "bad.pdb"
    path.write_text("HEADER no atoms\n", encoding="utf-8")

    with pytest.raises(ValueError, match="no ATOM/HETATM"):
        load_structure_file(path)


def test_load_structure_file_parses_pdb_cryst1_cell_and_hashes_pbc(tmp_path: Path) -> None:
    path = tmp_path / "water.pdb"
    path.write_text(PDB_CRYST1_TEXT, encoding="utf-8")

    parsed = load_structure_file(path)

    assert parsed.periodic is not None
    assert parsed.periodic["cell"]["lengths"] == pytest.approx((12.0, 13.0, 14.0))
    assert parsed.periodic["cell"]["angles"] == pytest.approx((90.0, 100.0, 120.0))
    assert parsed.periodic["pbc"] == (True, True, True)
    assert parsed.provenance["periodic"]["source"] == "pdb_cryst1"
    assert parsed.provenance["normalized_geometry_sha256"]


def test_load_structure_file_rejects_non_v2000_mol(tmp_path: Path) -> None:
    path = tmp_path / "bad.mol"
    path.write_text(MOL_TEXT.replace("V2000", "V3000"), encoding="utf-8")

    with pytest.raises(ValueError, match="V2000"):
        load_structure_file(path)
