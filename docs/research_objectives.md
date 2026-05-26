# QCchem Research Objectives

Research Objectives connect a scientific question to the artifact evidence needed
to defend it. They are planning objects, not execution shortcuts.

Trust-First flow:

```text
Research Objective -> Run/Benchmark/Study/Scan/Campaign -> Evidence Capsule
-> Claim Compiler -> Workbench Research Console -> AI Ticket
-> Promotion Gate -> Release Audit
```

## Command

```bash
qcchem objective init \
  --name h2_local_validation \
  --claim "H2 local workflow stays inside chemical accuracy against an exact baseline." \
  -o configs/objectives/h2_local_validation.yaml

qcchem objective plan \
  -c configs/objectives/h2_local_validation.yaml \
  -o artifacts/objectives/h2_local_validation_plan

qcchem objective status \
  -c configs/objectives/h2_local_validation.yaml \
  -o artifacts/objectives/h2_local_validation_status
```

## Contract

The YAML records:

- `claim`: the scientific claim to compile later.
- `system_scope`: molecule, basis, active space, and hardware scope.
- `required_evidence`: checklist entries such as exact baseline, benchmark
  acceptance, measurement cost summary, and complete `evidence_summary`.
- `candidate_configs`: configs that can create missing evidence.
- `linked_artifacts`: existing artifact roots or result JSON files.
- `promotion_policy`: local validated, hardware claim, and exploratory
  promotion requirements.

Outputs use `schema_version: qcchem.objective.v0.1-alpha` and include `best evidence`,
`trust tier`, `baseline strength`, `chemical accuracy status`,
`runtime evidence status`, and `recommended next action`.

## Boundaries

Objective planning does not run chemistry, submit IBM Runtime jobs, or promote
exploratory artifacts. It only explains what evidence exists, what is missing,
and which next action is defensible.
