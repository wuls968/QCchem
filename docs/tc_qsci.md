# TC-Kicked QSCI Exploratory Workflow

TC-kicked QSCI is implemented in QCchem as an exploratory determinant-selection workflow. It uses the normal PySCF / Qiskit Nature path to build the physical active-space Hamiltonian, uses a CAST-QC plugin Hamiltonian only to generate short-time sampling dynamics, then diagonalizes the selected determinant subspace with the physical Hamiltonian.

Run the small examples with:

```bash
qcchem exploratory run -c configs/exploratory/h2_tc_qsci.yaml
qcchem exploratory run -c configs/exploratory/lih_active_tc_qsci.yaml
```

The result artifact includes:

- `tc_qsci_result`
- `determinant_selection`
- `symmetry_sector`
- `cast_hamiltonian`
- `low_rank_resource_estimate`
- `qpe_resource_estimate`
- `error_budget`

## CAST-QC Plugins

Two built-in CAST model kinds are available in v1:

- `identity`: no-op baseline. It records CAST provenance while using the physical Hamiltonian for kicking.
- `npz_delta`: loads optional tensor corrections from an `.npz` file and adds them to the one-/two-body integrals before mapping. Supported keys are `h1_alpha_delta`, `h2_alpha_delta`, `h1_beta_delta`, `h2_beta_delta`, and `h2_beta_alpha_delta`.

All CAST operators are Hermitian-projected before quantum kicking. The anti-Hermitian norm is retained in `cast_hamiltonian` and repeated in the error budget.

## Boundaries

This workflow is not a validated chemistry claim. In v1, determinant sampling assumes Jordan-Wigner spin-orbital bitstrings. Bravyi-Kitaev and parity mappings are rejected for determinant sampling unless `tc_qsci.resource_estimation_only` is set.

The QPE section is only a resource-estimation interface. It reports qubit count, Pauli term count, LCU lambda, phase bits, first-order Trotter proxy costs, and a coarse T-count proxy; it is not a compiled fault-tolerant QPE circuit.
