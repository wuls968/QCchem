"""Read-only environment diagnostics; no credentials or provider calls."""

from __future__ import annotations

import os
import platform
import re
import sys
from importlib import metadata, util
from pathlib import Path

from qcchem import __version__

REQUIRED = ("numpy", "scipy", "PyYAML", "qiskit", "qiskit-aer", "qiskit-algorithms", "qiskit-nature", "pyscf")
OPTIONAL = {"workbench": "dash", "runtime": "qiskit-ibm-runtime", "cudaq": "cudaq", "ai": "openai", "hdf5": "h5py"}
MINIMUM_VERSIONS = {
    "numpy": "1.24", "scipy": "1.10", "PyYAML": "6.0", "qiskit": "2.3.0",
    "qiskit-aer": "0.17.2", "qiskit-algorithms": "0.4.0", "qiskit-nature": "0.7.0",
    "pyscf": "2.5.0", "dash": "2.18", "qiskit-ibm-runtime": "0.46.0",
    "cudaq": "0.14.2", "openai": "1.76.0", "h5py": None,
}


def _version_at_least(actual: str, minimum: str) -> bool:
    try:
        from packaging.version import Version, InvalidVersion
    except ImportError:
        # The core installation need not include packaging. Compare stable
        # numeric releases only; unknown/pre-release formats stay unverified.
        if not re.fullmatch(r"\d+(?:\.\d+)*", actual):
            return False
        actual_parts = tuple(int(part) for part in actual.split("."))
        minimum_parts = tuple(int(part) for part in minimum.split("."))
        size = max(len(actual_parts), len(minimum_parts))
        return actual_parts + (0,) * (size - len(actual_parts)) >= minimum_parts + (0,) * (size - len(minimum_parts))
    try:
        return Version(actual) >= Version(minimum)
    except InvalidVersion:
        return False


def environment_diagnostics() -> dict:
    packages = {}
    for name in (*REQUIRED, *OPTIONAL.values()):
        try:
            packages[name] = {"installed": True, "version": metadata.version(name)}
        except metadata.PackageNotFoundError:
            packages[name] = {"installed": False, "version": None}
        packages[name]["minimum_version"] = MINIMUM_VERSIONS[name]
        minimum = MINIMUM_VERSIONS[name]
        packages[name]["compatible"] = packages[name]["installed"] and (
            minimum is None or _version_at_least(packages[name]["version"], minimum)
        )
    missing = [name for name in REQUIRED if not packages[name]["installed"]]
    incompatible = [name for name in REQUIRED if packages[name]["installed"] and not packages[name]["compatible"]]
    try:
        installed_version = metadata.version("QCchem")
    except metadata.PackageNotFoundError:
        installed_version = None
    warnings = []
    if installed_version != __version__:
        warnings.append("Installed QCchem metadata differs from the imported source version.")
    return {
        "schema_version": "qcchem.doctor.v1",
        "status": "missing_required_dependencies" if missing else "incompatible_dependencies" if incompatible else "ready",
        "python": {"executable": sys.executable, "version": platform.python_version(), "prefix": sys.prefix},
        "platform": {"system": platform.system(), "machine": platform.machine()},
        "qcchem": {"source": str(Path(__file__).resolve().parent), "source_version": __version__,
                   "installed_version": installed_version},
        "dependencies": packages,
        "missing_required": missing,
        "incompatible_required": incompatible,
        "optional_features": {feature: packages[package]["compatible"] for feature, package in OPTIONAL.items()},
        "threads": {key: os.environ.get(key) for key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")},
        "conda": {"shell_environment": os.environ.get("CONDA_DEFAULT_ENV"),
                  "interpreter_environment": Path(sys.prefix).name,
                  "using_conda_python": (Path(sys.prefix) / "conda-meta").is_dir()},
        "warnings": warnings,
        "backend_importable": {"cudaq": util.find_spec("cudaq") is not None},
    }
