# QCchem Task Model

## 为什么要有 task model

QCchem 不能只会做 ground-state energy。研究工作流会逐步需要：

- excited states
- properties
- scans
- 更复杂的 comparative study

task model 的作用，是让这些能力进入正式 schema，而不是散落在 solver 里。

## 当前 task

### Ground-state

这是当前最成熟的 task。run workflow 的主结果仍然是 ground-state energy 和 benchmark。

### Excited-state

当前对象：

- `ExcitedStateTaskSpec`
- `ExcitedStateTaskResult`
- `ExcitedStateLevelResult`

当前实现：

- `exact_spectrum`
  - 真实最小实现
  - 当前有 validated mini artifact：`artifacts/h2_excited_mini`
- `vqd`
  - exploratory skeleton
  - 当前用 exact spectrum proxy 落结果，并在 artifact 中明确标注

### Property

当前对象：

- `PropertyTaskSpec`
- `PropertyTaskResult`
- `PropertyValueResult`

当前实现：

- `dipole_moment`
  - validated on small exact tasks
- `transition_dipole`
  - exploratory，使用 exact transition matrix element 派生
- `oscillator_strength`
  - exploratory，使用 exact excitation energy 与 transition dipole 派生
- 其他 property
  - placeholder only

## 状态表达

task 层不是跟着 run 的总状态一起混掉，而是单独表达：

- `excited_state_result.verification_status`
- `property_result.verification_status`
- `property_result.properties[*].implementation_status`

这可以避免“ground-state validated”误导成“整份 artifact 全部 validated”。

## 当前边界

Validated：

- exact-spectrum excited-state mini baseline
- dipole moment exact-expectation

Exploratory：

- VQD 风格 excited-state interface
- transition dipole exact-derived path
- oscillator strength exact-derived path

Placeholder only：

- 其他尚未进入 formal implementation 的 property 项
