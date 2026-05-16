# Environment Effective Hamiltonian Embedding

QCchem's preferred QM/MM-like path for quantum algorithms is
`problem.environment_embedding`. It keeps the MM environment classical and
compresses its influence into the molecular Hamiltonian before mapping to
qubits.

The first implementation supports:

- Gaussian-damped external point charges through PySCF `qmmm.mm_charge(..., radii=...)`
- AO-basis environment potential audit from the PySCF `hcore` delta
- explicit QM-nucleus/environment constant-energy bookkeeping
- declared boundary-bond leakage diagnostics without link atoms
- cache fingerprints and `.npz` matrix artifacts for the effective-Hamiltonian audit
- unchanged solver surfaces for exact, VQE, LR-ACE, TC-QSCI, active-space, compression, and cavity-QED paths

Example:

```yaml
problem:
  environment_embedding:
    enabled: true
    mode: effective_hamiltonian
    point_charges:
      enabled: true
      unit: angstrom
      source_file: data/environment.xyzq
      damping:
        kind: gaussian
        default_radius: 0.40
        radius_unit: angstrom
        min_radius: 0.15
        overpolarization_warning_potential_au: 2.0
    boundary:
      enabled: false
      method: localized_orbital_freeze_project_downfold
      localization: iao_lowdin
      cut_bonds: []
      leakage_threshold: 0.05
      strict: true
    cache:
      enabled: true
      directory: artifacts/effective_hamiltonians
      refresh: false
```

`problem.external_point_charges` remains supported as a compatibility alias.
When only the legacy field is present, QCchem treats it as an undamped
environment point-charge source and records that compatibility mode in
`environment_embedding.provenance`.

Energy reporting uses:

```text
total_energy = solver_energy + constant_energy_correction
             + nuclear_repulsion_energy
             + external_point_charge_nuclear_interaction_energy
             + boundary_embedding_constant_energy
```

The MM environment is not quantumized, and the qubit count does not grow with
the number of MM point charges. The current boundary implementation is a
diagnostic gate: it records localized boundary leakage and rejects excessive
leakage in strict mode, while avoiding link atoms and leaving the correction
matrix zero until a validated boundary projector/downfolding plugin supplies a
nonzero correction.

## Trust-First Validation Loop

The reusable validation harness lives in `qcchem.validation.qmmm_embedding`.
It runs small QM/MM-like cases, compares energy bookkeeping against PySCF,
checks matrix hermiticity and cache reload equality, and writes:

- `qmmm_validation.json`
- `qmmm_validation.md`
- `metrics.csv`

Example:

```python
from pathlib import Path
from qcchem.validation import run_qmmm_embedding_validation

summary = run_qmmm_embedding_validation(Path("artifacts/qmmm_validation"), profile="full")
assert summary["overall_status"] == "passed"
```

The `smoke` profile covers exact, boundary diagnostics, and legacy alias
compatibility. The `full` profile also covers charge/radius scan, active-space,
compression, TC-QSCI, cavity-QED, and LR-ACE surfaces. Any algorithm change
should first fail or improve one of these trust gates before being accepted.
