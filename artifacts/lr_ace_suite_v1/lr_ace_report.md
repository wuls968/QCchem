# QCchem LR-ACE Suite v1

- algorithm: `LR-ACE` (`Low-Rank Adaptive Chemistry Eigensolver`)
- status: `exploratory`
- validated_scope: `local exact-baseline gates for H2 and LiH active-space only`
- hardware_scope: `retrieved IBM Runtime H2 probes; hardware_verified does not imply chemistry validated`
- recommended_action: `pause_runtime_spend_and_analyze_bias`

## Cases

| Case | Qubits | Params | Local error (Ha) | Runtime shots | Runtime error (Ha) | Runtime std (Ha) | Depth | 2Q |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| h2_lr_ace | 2 | 1 | 4.77500483597737e-10 | None | None | None | None | None |
| lih_active_lr_ace | 2 | 5 | 6.617701941991072e-10 | None | None | None | None | None |
| h2_lr_ace_runtime_real | 2 | 1 | 4.77500483597737e-10 | 4096 | 0.003446986692515086 | 0.005774758847564092 | 12 | 2 |
| h2_lr_ace_runtime_highshots | 2 | 1 | 4.77500483597737e-10 | 65536 | 0.001698796357201715 | 0.004686430902491931 | 12 | 2 |
| h2_lr_ace_runtime_ultra | 2 | 1 | 4.77500483597737e-10 | 131072 | 0.0025783161795416287 | 0.0014218733640510401 | 12 | 2 |

## Best Runtime Evidence

- case: `h2_lr_ace_runtime_highshots`
- error: `0.001698796357201715` Ha
- shots: `65536`
- meets_chemical_accuracy: `False`

## Boundary

LR-ACE is currently a QCchem-native exploratory algorithm. The local H2/LiH active-space results pass exact-baseline chemical-accuracy gates, but the hardware probes remain exploratory because no retrieved Runtime result crossed the 0.0016 Ha threshold.
