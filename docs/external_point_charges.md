# External Point Charges

QCchem supports a compatibility QM/MM-like electrostatic embedding path through
`problem.external_point_charges`. New quantum-algorithm-oriented embedding work
should prefer `problem.environment_embedding`, which adds Gaussian damping,
effective-Hamiltonian provenance, boundary diagnostics, and cache fingerprints.

Included terms:

- electron and external point-charge interaction in the one-electron Hamiltonian
- QM nucleus and external point-charge Coulomb constant

Excluded terms:

- MM-MM energy
- van der Waals terms
- polarizable embedding
- environment relaxation or bonded MM terms

Example:

```yaml
problem:
  external_point_charges:
    enabled: true
    unit: angstrom
    source_file: configs/data/h2_environment.xyzq
    charges:
      - label: inline_probe
        coords: [0.0, 0.0, -2.0]
        charge: 0.25
```

The `source_file` format is XYZQ text. Blank lines and `#` comments are ignored.
Rows may be either `x y z q` or `label x y z q`.

Energy reporting uses:

```text
total_energy = solver_energy + constant_energy_correction
             + nuclear_repulsion_energy
             + external_point_charge_nuclear_interaction_energy
             + boundary_embedding_constant_energy
```

For molecular electronic-structure and cavity-QED runs, PySCF `qmmm.mm_charge`
adds the static environment potential before QCchem maps the Hamiltonian. For
lattice-QED runs, external charges are added as a finite-cutoff scalar onsite
potential only; Gauss-law background charges are not modified.

When only `problem.external_point_charges` is configured, QCchem records an
`environment_embedding` result section in `external_point_charges_compatibility_alias`
mode. That path remains undamped to preserve existing input semantics.
