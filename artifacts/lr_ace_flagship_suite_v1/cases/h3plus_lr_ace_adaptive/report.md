# QCchem Report: H3plus-LR-ACE-flagship-adaptive

## Report Cover

> Scientific Atelier framing for export-grade review: lead with chemistry confidence, runtime evidence, and the minimum context needed to defend the result.

- molecule: `H3plus-LR-ACE-flagship-adaptive`
- basis: `sto3g`
- method: `lr_ace / {'kind': 'lr_ace', 'rotation_blocks': ['ry', 'rz'], 'entanglement_blocks': 'cz', 'entanglement': 'full', 'reps': 16, 'lr_ace': {'algorithm_name': 'LR-ACE', 'low_rank_aware': True, 'selection_rule': 'adaptive_score_weight_locality_reference_mixing', 'source_terms': [{'pauli': 'XXXX', 'weight': 0.03594452854855405, 'coefficient_real': 0.03594452854855405, 'coefficient_imag': 0.0}, {'pauli': 'XXYY', 'weight': 0.03594452854855405, 'coefficient_real': -0.03594452854855405, 'coefficient_imag': 0.0}, {'pauli': 'YYXX', 'weight': 0.03594452854855405, 'coefficient_real': -0.03594452854855405, 'coefficient_imag': 0.0}, {'pauli': 'YYYY', 'weight': 0.03594452854855405, 'coefficient_real': 0.03594452854855405, 'coefficient_imag': 0.0}, {'pauli': 'IXIX', 'weight': 0.0359445220444363, 'coefficient_real': 0.0359445220444363, 'coefficient_imag': 0.0}, {'pauli': 'IXZX', 'weight': 0.0359445220444363, 'coefficient_real': -0.0359445220444363, 'coefficient_imag': 0.0}, {'pauli': 'ZXIX', 'weight': 0.0359445220444363, 'coefficient_real': 0.0359445220444363, 'coefficient_imag': 0.0}, {'pauli': 'ZXZX', 'weight': 0.0359445220444363, 'coefficient_real': -0.0359445220444363, 'coefficient_imag': 0.0}, {'pauli': 'IXXI', 'weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0}, {'pauli': 'IXXZ', 'weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0}, {'pauli': 'XIIX', 'weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0}, {'pauli': 'XIZX', 'weight': 0.022837714407336514, 'coefficient_real': 0.022837714407336514, 'coefficient_imag': 0.0}, {'pauli': 'XZIX', 'weight': 0.022837714407336514, 'coefficient_real': 0.022837714407336514, 'coefficient_imag': 0.0}, {'pauli': 'XZZX', 'weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0}, {'pauli': 'ZXXI', 'weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0}, {'pauli': 'ZXXZ', 'weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0}, {'pauli': 'XXZI', 'weight': 0.022837491239045354, 'coefficient_real': 0.022837491239045354, 'coefficient_imag': 0.0}, {'pauli': 'YYZI', 'weight': 0.022837491239045354, 'coefficient_real': -0.022837491239045354, 'coefficient_imag': 0.0}, {'pauli': 'ZIXX', 'weight': 0.022837491239045354, 'coefficient_real': -0.022837491239045354, 'coefficient_imag': 0.0}, {'pauli': 'ZIYY', 'weight': 0.022837491239045354, 'coefficient_real': 0.022837491239045354, 'coefficient_imag': 0.0}, {'pauli': 'XXZZ', 'weight': 0.022837079428386947, 'coefficient_real': 0.022837079428386947, 'coefficient_imag': 0.0}, {'pauli': 'YYZZ', 'weight': 0.022837079428386947, 'coefficient_real': -0.022837079428386947, 'coefficient_imag': 0.0}, {'pauli': 'ZZXX', 'weight': 0.022837079428386947, 'coefficient_real': 0.022837079428386947, 'coefficient_imag': 0.0}, {'pauli': 'ZZYY', 'weight': 0.022837079428386947, 'coefficient_real': -0.022837079428386947, 'coefficient_imag': 0.0}, {'pauli': 'XIXI', 'weight': 0.01821108073582051, 'coefficient_real': 0.01821108073582051, 'coefficient_imag': 0.0}, {'pauli': 'XIXZ', 'weight': 0.01821108073582051, 'coefficient_real': 0.01821108073582051, 'coefficient_imag': 0.0}, {'pauli': 'XZXI', 'weight': 0.01821108073582051, 'coefficient_real': -0.01821108073582051, 'coefficient_imag': 0.0}, {'pauli': 'XZXZ', 'weight': 0.01821108073582051, 'coefficient_real': -0.01821108073582051, 'coefficient_imag': 0.0}, {'pauli': 'IZXX', 'weight': 7.080767526787017e-07, 'coefficient_real': 7.080767526787017e-07, 'coefficient_imag': 0.0}, {'pauli': 'IZYY', 'weight': 7.080767526787017e-07, 'coefficient_real': -7.080767526787017e-07, 'coefficient_imag': 0.0}, {'pauli': 'XXIZ', 'weight': 7.080767526787017e-07, 'coefficient_real': -7.080767526787017e-07, 'coefficient_imag': 0.0}, {'pauli': 'YYIZ', 'weight': 7.080767526787017e-07, 'coefficient_real': 7.080767526787017e-07, 'coefficient_imag': 0.0}, {'pauli': 'IIXX', 'weight': 3.0351623270207856e-07, 'coefficient_real': -3.0351623270207856e-07, 'coefficient_imag': 0.0}, {'pauli': 'IIYY', 'weight': 3.0351623270207856e-07, 'coefficient_real': 3.0351623270207856e-07, 'coefficient_imag': 0.0}, {'pauli': 'XXII', 'weight': 3.0351623270207856e-07, 'coefficient_real': -3.0351623270207856e-07, 'coefficient_imag': 0.0}, {'pauli': 'YYII', 'weight': 3.0351623270207856e-07, 'coefficient_real': 3.0351623270207856e-07, 'coefficient_imag': 0.0}], 'candidate_generators': [{'pauli': 'IYIX', 'source_pauli': 'IXIX', 'source_weight': 0.0359445220444363, 'coefficient_real': 0.0359445220444363, 'coefficient_imag': 0.0, 'adaptive_score': 0.0359445220444363, 'locality': 2, 'reference_mixing_relevance': 1.0, 'candidate_index': 0}, {'pauli': 'IXIY', 'source_pauli': 'IXIX', 'source_weight': 0.0359445220444363, 'coefficient_real': 0.0359445220444363, 'coefficient_imag': 0.0, 'adaptive_score': 0.0359445220444363, 'locality': 2, 'reference_mixing_relevance': 1.0, 'candidate_index': 1}, {'pauli': 'IYXI', 'source_pauli': 'IXXI', 'source_weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.022837714407336514, 'locality': 2, 'reference_mixing_relevance': 1.0, 'candidate_index': 2}, {'pauli': 'IXYI', 'source_pauli': 'IXXI', 'source_weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.022837714407336514, 'locality': 2, 'reference_mixing_relevance': 1.0, 'candidate_index': 3}, {'pauli': 'YIIX', 'source_pauli': 'XIIX', 'source_weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.022837714407336514, 'locality': 2, 'reference_mixing_relevance': 1.0, 'candidate_index': 4}, {'pauli': 'XIIY', 'source_pauli': 'XIIX', 'source_weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.022837714407336514, 'locality': 2, 'reference_mixing_relevance': 1.0, 'candidate_index': 5}, {'pauli': 'IYZX', 'source_pauli': 'IXZX', 'source_weight': 0.0359445220444363, 'coefficient_real': -0.0359445220444363, 'coefficient_imag': 0.0, 'adaptive_score': 0.019969178913575723, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 6}, {'pauli': 'IXZY', 'source_pauli': 'IXZX', 'source_weight': 0.0359445220444363, 'coefficient_real': -0.0359445220444363, 'coefficient_imag': 0.0, 'adaptive_score': 0.019969178913575723, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 7}, {'pauli': 'ZYIX', 'source_pauli': 'ZXIX', 'source_weight': 0.0359445220444363, 'coefficient_real': 0.0359445220444363, 'coefficient_imag': 0.0, 'adaptive_score': 0.019969178913575723, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 8}, {'pauli': 'ZXIY', 'source_pauli': 'ZXIX', 'source_weight': 0.0359445220444363, 'coefficient_real': 0.0359445220444363, 'coefficient_imag': 0.0, 'adaptive_score': 0.019969178913575723, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 9}, {'pauli': 'YIXI', 'source_pauli': 'XIXI', 'source_weight': 0.01821108073582051, 'coefficient_real': 0.01821108073582051, 'coefficient_imag': 0.0, 'adaptive_score': 0.01821108073582051, 'locality': 2, 'reference_mixing_relevance': 1.0, 'candidate_index': 10}, {'pauli': 'XIYI', 'source_pauli': 'XIXI', 'source_weight': 0.01821108073582051, 'coefficient_real': 0.01821108073582051, 'coefficient_imag': 0.0, 'adaptive_score': 0.01821108073582051, 'locality': 2, 'reference_mixing_relevance': 1.0, 'candidate_index': 11}, {'pauli': 'YXXX', 'source_pauli': 'XXXX', 'source_weight': 0.03594452854855405, 'coefficient_real': 0.03594452854855405, 'coefficient_imag': 0.0, 'adaptive_score': 0.017972264274277026, 'locality': 4, 'reference_mixing_relevance': 1.0, 'candidate_index': 12}, {'pauli': 'XYXX', 'source_pauli': 'XXXX', 'source_weight': 0.03594452854855405, 'coefficient_real': 0.03594452854855405, 'coefficient_imag': 0.0, 'adaptive_score': 0.017972264274277026, 'locality': 4, 'reference_mixing_relevance': 1.0, 'candidate_index': 13}, {'pauli': 'XXYX', 'source_pauli': 'XXXX', 'source_weight': 0.03594452854855405, 'coefficient_real': 0.03594452854855405, 'coefficient_imag': 0.0, 'adaptive_score': 0.017972264274277026, 'locality': 4, 'reference_mixing_relevance': 1.0, 'candidate_index': 14}, {'pauli': 'XXXY', 'source_pauli': 'XXXX', 'source_weight': 0.03594452854855405, 'coefficient_real': 0.03594452854855405, 'coefficient_imag': 0.0, 'adaptive_score': 0.017972264274277026, 'locality': 4, 'reference_mixing_relevance': 1.0, 'candidate_index': 15}, {'pauli': 'YXYY', 'source_pauli': 'XXYY', 'source_weight': 0.03594452854855405, 'coefficient_real': -0.03594452854855405, 'coefficient_imag': 0.0, 'adaptive_score': 0.017972264274277026, 'locality': 4, 'reference_mixing_relevance': 1.0, 'candidate_index': 16}, {'pauli': 'XYYY', 'source_pauli': 'XXYY', 'source_weight': 0.03594452854855405, 'coefficient_real': -0.03594452854855405, 'coefficient_imag': 0.0, 'adaptive_score': 0.017972264274277026, 'locality': 4, 'reference_mixing_relevance': 1.0, 'candidate_index': 17}, {'pauli': 'YYYX', 'source_pauli': 'YYXX', 'source_weight': 0.03594452854855405, 'coefficient_real': -0.03594452854855405, 'coefficient_imag': 0.0, 'adaptive_score': 0.017972264274277026, 'locality': 4, 'reference_mixing_relevance': 1.0, 'candidate_index': 18}, {'pauli': 'YYXY', 'source_pauli': 'YYXX', 'source_weight': 0.03594452854855405, 'coefficient_real': -0.03594452854855405, 'coefficient_imag': 0.0, 'adaptive_score': 0.017972264274277026, 'locality': 4, 'reference_mixing_relevance': 1.0, 'candidate_index': 19}, {'pauli': 'ZYZX', 'source_pauli': 'ZXZX', 'source_weight': 0.0359445220444363, 'coefficient_real': -0.0359445220444363, 'coefficient_imag': 0.0, 'adaptive_score': 0.013479195766663614, 'locality': 4, 'reference_mixing_relevance': 0.5, 'candidate_index': 20}, {'pauli': 'ZXZY', 'source_pauli': 'ZXZX', 'source_weight': 0.0359445220444363, 'coefficient_real': -0.0359445220444363, 'coefficient_imag': 0.0, 'adaptive_score': 0.013479195766663614, 'locality': 4, 'reference_mixing_relevance': 0.5, 'candidate_index': 21}, {'pauli': 'IYXZ', 'source_pauli': 'IXXZ', 'source_weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.012687619115186953, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 22}, {'pauli': 'IXYZ', 'source_pauli': 'IXXZ', 'source_weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.012687619115186953, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 23}, {'pauli': 'YIZX', 'source_pauli': 'XIZX', 'source_weight': 0.022837714407336514, 'coefficient_real': 0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.012687619115186953, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 24}, {'pauli': 'XIZY', 'source_pauli': 'XIZX', 'source_weight': 0.022837714407336514, 'coefficient_real': 0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.012687619115186953, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 25}, {'pauli': 'YZIX', 'source_pauli': 'XZIX', 'source_weight': 0.022837714407336514, 'coefficient_real': 0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.012687619115186953, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 26}, {'pauli': 'XZIY', 'source_pauli': 'XZIX', 'source_weight': 0.022837714407336514, 'coefficient_real': 0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.012687619115186953, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 27}, {'pauli': 'ZYXI', 'source_pauli': 'ZXXI', 'source_weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.012687619115186953, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 28}, {'pauli': 'ZXYI', 'source_pauli': 'ZXXI', 'source_weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.012687619115186953, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 29}, {'pauli': 'YXZI', 'source_pauli': 'XXZI', 'source_weight': 0.022837491239045354, 'coefficient_real': 0.022837491239045354, 'coefficient_imag': 0.0, 'adaptive_score': 0.012687495132802975, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 30}, {'pauli': 'XYZI', 'source_pauli': 'XXZI', 'source_weight': 0.022837491239045354, 'coefficient_real': 0.022837491239045354, 'coefficient_imag': 0.0, 'adaptive_score': 0.012687495132802975, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 31}, {'pauli': 'ZIYX', 'source_pauli': 'ZIXX', 'source_weight': 0.022837491239045354, 'coefficient_real': -0.022837491239045354, 'coefficient_imag': 0.0, 'adaptive_score': 0.012687495132802975, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 32}, {'pauli': 'ZIXY', 'source_pauli': 'ZIXX', 'source_weight': 0.022837491239045354, 'coefficient_real': -0.022837491239045354, 'coefficient_imag': 0.0, 'adaptive_score': 0.012687495132802975, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 33}, {'pauli': 'YIXZ', 'source_pauli': 'XIXZ', 'source_weight': 0.01821108073582051, 'coefficient_real': 0.01821108073582051, 'coefficient_imag': 0.0, 'adaptive_score': 0.010117267075455837, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 34}, {'pauli': 'XIYZ', 'source_pauli': 'XIXZ', 'source_weight': 0.01821108073582051, 'coefficient_real': 0.01821108073582051, 'coefficient_imag': 0.0, 'adaptive_score': 0.010117267075455837, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 35}, {'pauli': 'YZXI', 'source_pauli': 'XZXI', 'source_weight': 0.01821108073582051, 'coefficient_real': -0.01821108073582051, 'coefficient_imag': 0.0, 'adaptive_score': 0.010117267075455837, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 36}, {'pauli': 'XZYI', 'source_pauli': 'XZXI', 'source_weight': 0.01821108073582051, 'coefficient_real': -0.01821108073582051, 'coefficient_imag': 0.0, 'adaptive_score': 0.010117267075455837, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 37}, {'pauli': 'YZZX', 'source_pauli': 'XZZX', 'source_weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.008564142902751194, 'locality': 4, 'reference_mixing_relevance': 0.5, 'candidate_index': 38}, {'pauli': 'XZZY', 'source_pauli': 'XZZX', 'source_weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.008564142902751194, 'locality': 4, 'reference_mixing_relevance': 0.5, 'candidate_index': 39}, {'pauli': 'ZYXZ', 'source_pauli': 'ZXXZ', 'source_weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.008564142902751194, 'locality': 4, 'reference_mixing_relevance': 0.5, 'candidate_index': 40}, {'pauli': 'ZXYZ', 'source_pauli': 'ZXXZ', 'source_weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.008564142902751194, 'locality': 4, 'reference_mixing_relevance': 0.5, 'candidate_index': 41}, {'pauli': 'YXZZ', 'source_pauli': 'XXZZ', 'source_weight': 0.022837079428386947, 'coefficient_real': 0.022837079428386947, 'coefficient_imag': 0.0, 'adaptive_score': 0.008563904785645105, 'locality': 4, 'reference_mixing_relevance': 0.5, 'candidate_index': 42}, {'pauli': 'XYZZ', 'source_pauli': 'XXZZ', 'source_weight': 0.022837079428386947, 'coefficient_real': 0.022837079428386947, 'coefficient_imag': 0.0, 'adaptive_score': 0.008563904785645105, 'locality': 4, 'reference_mixing_relevance': 0.5, 'candidate_index': 43}, {'pauli': 'ZZYX', 'source_pauli': 'ZZXX', 'source_weight': 0.022837079428386947, 'coefficient_real': 0.022837079428386947, 'coefficient_imag': 0.0, 'adaptive_score': 0.008563904785645105, 'locality': 4, 'reference_mixing_relevance': 0.5, 'candidate_index': 44}, {'pauli': 'ZZXY', 'source_pauli': 'ZZXX', 'source_weight': 0.022837079428386947, 'coefficient_real': 0.022837079428386947, 'coefficient_imag': 0.0, 'adaptive_score': 0.008563904785645105, 'locality': 4, 'reference_mixing_relevance': 0.5, 'candidate_index': 45}, {'pauli': 'YZXZ', 'source_pauli': 'XZXZ', 'source_weight': 0.01821108073582051, 'coefficient_real': -0.01821108073582051, 'coefficient_imag': 0.0, 'adaptive_score': 0.006829155275932692, 'locality': 4, 'reference_mixing_relevance': 0.5, 'candidate_index': 46}, {'pauli': 'XZYZ', 'source_pauli': 'XZXZ', 'source_weight': 0.01821108073582051, 'coefficient_real': -0.01821108073582051, 'coefficient_imag': 0.0, 'adaptive_score': 0.006829155275932692, 'locality': 4, 'reference_mixing_relevance': 0.5, 'candidate_index': 47}, {'pauli': 'IZYX', 'source_pauli': 'IZXX', 'source_weight': 7.080767526787017e-07, 'coefficient_real': 7.080767526787017e-07, 'coefficient_imag': 0.0, 'adaptive_score': 3.9337597371038975e-07, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 48}, {'pauli': 'IZXY', 'source_pauli': 'IZXX', 'source_weight': 7.080767526787017e-07, 'coefficient_real': 7.080767526787017e-07, 'coefficient_imag': 0.0, 'adaptive_score': 3.9337597371038975e-07, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 49}, {'pauli': 'YXIZ', 'source_pauli': 'XXIZ', 'source_weight': 7.080767526787017e-07, 'coefficient_real': -7.080767526787017e-07, 'coefficient_imag': 0.0, 'adaptive_score': 3.9337597371038975e-07, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 50}, {'pauli': 'XYIZ', 'source_pauli': 'XXIZ', 'source_weight': 7.080767526787017e-07, 'coefficient_real': -7.080767526787017e-07, 'coefficient_imag': 0.0, 'adaptive_score': 3.9337597371038975e-07, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 51}, {'pauli': 'IIYX', 'source_pauli': 'IIXX', 'source_weight': 3.0351623270207856e-07, 'coefficient_real': -3.0351623270207856e-07, 'coefficient_imag': 0.0, 'adaptive_score': 3.0351623270207856e-07, 'locality': 2, 'reference_mixing_relevance': 1.0, 'candidate_index': 52}, {'pauli': 'IIXY', 'source_pauli': 'IIXX', 'source_weight': 3.0351623270207856e-07, 'coefficient_real': -3.0351623270207856e-07, 'coefficient_imag': 0.0, 'adaptive_score': 3.0351623270207856e-07, 'locality': 2, 'reference_mixing_relevance': 1.0, 'candidate_index': 53}, {'pauli': 'YXII', 'source_pauli': 'XXII', 'source_weight': 3.0351623270207856e-07, 'coefficient_real': -3.0351623270207856e-07, 'coefficient_imag': 0.0, 'adaptive_score': 3.0351623270207856e-07, 'locality': 2, 'reference_mixing_relevance': 1.0, 'candidate_index': 54}, {'pauli': 'XYII', 'source_pauli': 'XXII', 'source_weight': 3.0351623270207856e-07, 'coefficient_real': -3.0351623270207856e-07, 'coefficient_imag': 0.0, 'adaptive_score': 3.0351623270207856e-07, 'locality': 2, 'reference_mixing_relevance': 1.0, 'candidate_index': 55}], 'selected_generators': [{'pauli': 'IYIX', 'source_pauli': 'IXIX', 'source_weight': 0.0359445220444363, 'coefficient_real': 0.0359445220444363, 'coefficient_imag': 0.0, 'adaptive_score': 0.0359445220444363, 'locality': 2, 'reference_mixing_relevance': 1.0, 'batch_index': 0}, {'pauli': 'IYXI', 'source_pauli': 'IXXI', 'source_weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.022837714407336514, 'locality': 2, 'reference_mixing_relevance': 1.0, 'batch_index': 1}, {'pauli': 'YIIX', 'source_pauli': 'XIIX', 'source_weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.022837714407336514, 'locality': 2, 'reference_mixing_relevance': 1.0, 'batch_index': 2}, {'pauli': 'IYZX', 'source_pauli': 'IXZX', 'source_weight': 0.0359445220444363, 'coefficient_real': -0.0359445220444363, 'coefficient_imag': 0.0, 'adaptive_score': 0.019969178913575723, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'batch_index': 3}, {'pauli': 'ZYIX', 'source_pauli': 'ZXIX', 'source_weight': 0.0359445220444363, 'coefficient_real': 0.0359445220444363, 'coefficient_imag': 0.0, 'adaptive_score': 0.019969178913575723, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'batch_index': 4}, {'pauli': 'YIXI', 'source_pauli': 'XIXI', 'source_weight': 0.01821108073582051, 'coefficient_real': 0.01821108073582051, 'coefficient_imag': 0.0, 'adaptive_score': 0.01821108073582051, 'locality': 2, 'reference_mixing_relevance': 1.0, 'batch_index': 5}, {'pauli': 'YXXX', 'source_pauli': 'XXXX', 'source_weight': 0.03594452854855405, 'coefficient_real': 0.03594452854855405, 'coefficient_imag': 0.0, 'adaptive_score': 0.017972264274277026, 'locality': 4, 'reference_mixing_relevance': 1.0, 'batch_index': 6}, {'pauli': 'YXYY', 'source_pauli': 'XXYY', 'source_weight': 0.03594452854855405, 'coefficient_real': -0.03594452854855405, 'coefficient_imag': 0.0, 'adaptive_score': 0.017972264274277026, 'locality': 4, 'reference_mixing_relevance': 1.0, 'batch_index': 7}, {'pauli': 'ZYZX', 'source_pauli': 'ZXZX', 'source_weight': 0.0359445220444363, 'coefficient_real': -0.0359445220444363, 'coefficient_imag': 0.0, 'adaptive_score': 0.013479195766663614, 'locality': 4, 'reference_mixing_relevance': 0.5, 'batch_index': 8}, {'pauli': 'IYXZ', 'source_pauli': 'IXXZ', 'source_weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.012687619115186953, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'batch_index': 9}, {'pauli': 'YIZX', 'source_pauli': 'XIZX', 'source_weight': 0.022837714407336514, 'coefficient_real': 0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.012687619115186953, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'batch_index': 10}, {'pauli': 'YZIX', 'source_pauli': 'XZIX', 'source_weight': 0.022837714407336514, 'coefficient_real': 0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.012687619115186953, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'batch_index': 11}], 'selected_factor_count': 12, 'method_role': 'flagship', 'profile': 'flagship_adaptive', 'validation_mode': 'trust_first', 'ansatz_parameter_count': 12, 'optimized_parameters': [0.005193794265729109, -0.0024115055830804645, 0.0044027507796745085, 0.007522498666850932, -0.0026913599323835956, 0.1097947842319337, -0.08136862983133683, 0.003943730254731841, -0.00998098798981236, 0.07758976908456741, -0.09910265969373332, -0.002522510311704415], 'adaptive': {'enabled': True, 'target_error_hartree': 0.0016, 'max_wall_time_seconds': 1200.0, 'candidate_pool_policy': 'residual_guided', 'candidate_scan_limit': 64, 'residual_batch_size': 8, 'residual_scan_angles': [-0.15, -0.05, 0.05, 0.15], 'min_energy_improvement_hartree': 0.0002, 'max_adaptive_expansions': 3, 'exact_reference_available': True, 'exact_solver_energy': -3.0315347675539805, 'stages': [{'stage_index': 0, 'schedule_index': 0, 'generator_count': 12, 'parameter_count': 12, 'optimizer_maxiter': 1500, 'initial_point_strategy': 'zeros', 'restart_index': 0, 'energy': -3.0315333755722658, 'exact_error_hartree': 1.3919817147822755e-06, 'converged': True, 'iterations': 154, 'evaluations': 154, 'optimizer_message': 'Optimization terminated successfully.'}], 'expansions': [], 'scheduled_generator_counts': [12, 16], 'original_generator_schedule_length': 2, 'best_stage_index': 0, 'best_energy': -3.0315333755722658, 'best_exact_error_hartree': 1.3919817147822755e-06, 'trust_label': 'passed_exact_reference', 'uncompressed_check_triggered': True, 'compression_proxy_error_hartree': 1.1941071340615395e-06, 'uncompressed_exact_solver_energy': -3.0315347675539783, 'uncompressed_lr_ace_error_hartree': 1.9787457850029e-07, 'combined_error_vs_uncompressed_exact_hartree': 1.3919817125618295e-06}, 'low_rank_method': 'modified_cholesky', 'factor_rank': 6, 'compression_threshold': 1e-10, 'compression_reconstruction_error': 1.5700924586837752e-16, 'pre_term_count': 52, 'post_term_count': 52, 'local_accuracy_gate': {'passed': True, 'threshold_hartree': 0.0016, 'absolute_error_hartree': 1.3919817214436137e-06}, 'validation_gate': {'trust_label': 'passed_exact_reference', 'verification_status': 'validated', 'validated': True, 'target_error_hartree': 0.0016, 'exact_available': True, 'local_exact_error_hartree': 1.3919817147822755e-06, 'compression_enabled': True, 'compressed_solver_energy': -3.0315333755722658, 'uncompressed_solver_energy': -3.0315345696794, 'uncompressed_exact_solver_energy': -3.0315347675539783, 'runtime_attempted': False, 'runtime_accuracy_met': None, 'blocking_reason': None}}}`
- mapping_kind: `parity_two_qubit_reduction`
- num_qubits: `4`
- verification_status: `validated`
- hardware_verified: `False`
- hardware_evidence_tier: `None`
- benchmark_absolute_error: `0.000001194107` Hartree
- best_available_assessment: `local_execution`
- backend_kind: `statevector`

## Hero

- headline_total_energy: `-1.267583467433` Hartree
- headline_correlation_energy: `-0.025254848494` Hartree
- headline_absolute_error: `0.000001194107` Hartree
- comparison_target: `compressed_vs_uncompressed`
- active_space_metadata: `None`
- runtime_backend: `None`
- runtime_job_id: `None`

## Evidence Summary

- result_identity: `{'artifact_kind': 'run', 'artifact_name': 'h3plus_lr_ace_adaptive', 'molecule_name': 'H3plus-LR-ACE-flagship-adaptive', 'basis': 'sto3g', 'backend_kind': 'statevector', 'mapping_kind': 'parity_two_qubit_reduction', 'field_model_kind': None}`
- primary_scientific_claim: `H3plus-LR-ACE-flagship-adaptive stays within chemical accuracy against compressed_vs_uncompressed for the defended local execution path.`
- primary_baseline: `{'baseline_kind': 'exact', 'baseline_source': 'exact_diagonalization', 'baseline_scope': 'single_run', 'baseline_strength': 'strong'}`
- primary_error_metric: `{'metric_kind': 'absolute_error_hartree', 'value': 1.1941071340615395e-06, 'units': 'Hartree', 'threshold': 0.0016, 'comparison_target': 'compressed_vs_uncompressed'}`
- chemical_accuracy_status: `met`
- runtime_evidence_status: `none`
- trust_tier: `validated`
- recommended_action: `promote_validated_result`

## Claim

- primary_scientific_claim: `H3plus-LR-ACE-flagship-adaptive stays within chemical accuracy against compressed_vs_uncompressed for the defended local execution path.`
- trust_tier: `validated`
- recommended_action: `promote_validated_result`

## Chain

- reduction: `none` / transformers=`[]`
- compression: `modified_cholesky` / status=`validated`
- correction: `None` / delta=`None`
- comparison_evidence: `{'comparison_target': 'compressed_vs_uncompressed', 'absolute_error': 1.1941071340615395e-06, 'relative_error': 9.420334359450455e-07, 'statistical_error': None, 'baseline_strength': 'strong', 'compressed_vs_uncompressed': {'available': True, 'method': 'modified_cholesky', 'rank': 6, 'threshold': 1e-10, 'pre_term_count': 52, 'post_term_count': 52, 'compressed_solver_energy': -3.0315333755722658, 'uncompressed_solver_energy': -3.0315345696794, 'compressed_total_energy': -1.2675834674326278, 'uncompressed_total_energy': -1.267584661539762, 'absolute_error': 1.1941071340615395e-06, 'relative_error': 9.420334359450455e-07, 'compressed_solve_wall_time_seconds': 0.398849000048358, 'uncompressed_solve_wall_time_seconds': 0.34311766701284796}}`

## Proof

- execution_evidence: `{'wall_time_seconds': 0.9209322920069098, 'shots': None, 'measurement_strategy': 'low_rank_lr_ace_adaptive_local', 'measurement_group_count': 7, 'measured_shot_usage': None, 'runtime_backend': None, 'runtime_job_id': None, 'field_model_kind': None}`
- trust_judgment: `{'verification_status': 'validated', 'module_origin': 'core', 'hardware_verified': False, 'hardware_evidence_tier': None, 'verification_notes': ['validation_scope=lr_ace adaptive local exact-baseline gate'], 'scientific_risk_notes': ['LR-ACE adaptive scheduling is flagship-local and gated by exact-reference evidence.', 'Adaptive generator and optimizer budgets do not imply general publication-validated scaling.'], 'lr_ace_trust_label': 'passed_exact_reference', 'lr_ace_validation_gate': {'trust_label': 'passed_exact_reference', 'verification_status': 'validated', 'validated': True, 'target_error_hartree': 0.0016, 'exact_available': True, 'local_exact_error_hartree': 1.3919817147822755e-06, 'compression_enabled': True, 'compressed_solver_energy': -3.0315333755722658, 'uncompressed_solver_energy': -3.0315345696794, 'uncompressed_exact_solver_energy': -3.0315347675539783, 'runtime_attempted': False, 'runtime_accuracy_met': None, 'blocking_reason': None}}`
- provenance_timestamp: `2026-05-17T10:50:41.753164+00:00`
- runtime_job_id: `None`
- artifact_root: `artifacts/lr_ace_flagship_suite_v1/cases/h3plus_lr_ace_adaptive`

## Chemical Accuracy Frame

- available_assessments: `['local_execution']`
- best_available_assessment: `local_execution`
- status: `validated`
- meets_chemical_accuracy: `True`
- absolute_error_hartree: `0.000001391982` Hartree
- threshold_hartree: `0.0016`
- distance_to_chemical_accuracy: `0.0`
- statistical_error: `None`
- notes: `['Meets chemical accuracy threshold.']`

## Runtime Evidence

> Runtime evidence is surfaced explicitly so exported reports separate chemistry confidence from execution provenance.

- hardware_verified: `False`
- hardware_evidence_tier: `None`
- service: `None`
- provider: `None`
- backend_name: `None`
- job_id: `None`
- verification_status: `None`
- layout_strategy: `None`
- selected_layout: `[]`
- transpiled_depth: `None`
- transpiled_two_qubit_gate_count: `None`

## Verification

- verification_status: `validated`

## Validation Boundary

- Module Origin: `core`
- Capability Tier: `flagship`
- Verification Notes: `['validation_scope=lr_ace adaptive local exact-baseline gate']`
- Scientific Risk Notes: `['LR-ACE adaptive scheduling is flagship-local and gated by exact-reference evidence.', 'Adaptive generator and optimizer budgets do not imply general publication-validated scaling.']`

## Energy Summary

- electronic_energy: `-3.031533375572` Hartree
- nuclear_repulsion_energy: `1.763949908140` Hartree
- external_point_charge_nuclear_interaction_energy: `0.000000000000` Hartree
- boundary_embedding_constant_energy: `0.000000000000` Hartree
- total_energy: `-1.267583467433` Hartree
- hf_reference_energy: `-1.242328618938` Hartree
- solver_energy: `-3.031533375572` Hartree (raw solver-Hamiltonian energy, before QCchem constant-shift correction)
- exact_ground_energy: `-3.031534767554` Hartree (raw exact baseline in the same solver-Hamiltonian convention)
- correlation_energy: `-0.025254848494` Hartree
- energy_units: `Hartree`
- constant_energy_correction: `0.000000000000` Hartree
- energy_formula: `total_energy = solver_energy + constant_energy_correction + nuclear_repulsion_energy + external_point_charge_nuclear_interaction_energy + boundary_embedding_constant_energy; electronic_energy = solver_energy + constant_energy_correction`

## Field Definitions

- `solver_energy` is the raw energy returned by the configured solver on the mapped qubit Hamiltonian.
- `exact_ground_energy` is the raw exact-diagonalization energy of that same mapped Hamiltonian.
- `electronic_energy` is QCchem's corrected electronic energy after adding any non-nuclear Hamiltonian constants, such as active-space offsets.
- `external_point_charge_nuclear_interaction_energy` is the explicit QM nuclei/static point-charge Coulomb constant; MM-MM and non-electrostatic environment terms are not included.
- `boundary_embedding_constant_energy` is the explicit constant generated by boundary embedding; the first implementation records a zero constant unless a nonzero boundary projector is supplied.
- `total_energy` is reconstructed from the explicit `energy_formula`, so active-space and transformed problems remain auditable.
- `hf_reference_energy` is the Hartree-Fock total reference energy exposed by Qiskit Nature.
- `correlation_energy` is `total_energy - hf_reference_energy` and therefore measures post-HF improvement in the total-energy convention.

## Exact Baseline

- available: `True`
- source: `exact_diagonalization`
- solver_hamiltonian_energy: `-3.031534767554` Hartree
- electronic_energy: `-3.031534767554` Hartree
- total_energy: `-1.267584859414` Hartree

## Benchmark

- exact_available: `True`
- comparison_target: `compressed_vs_uncompressed`
- exact_electronic_energy: `-3.031534767554` Hartree
- exact_total_energy: `-1.267584859414` Hartree
- absolute_error: `0.000001194107` Hartree
- relative_error: `9.420334359450455e-07`
- statistical_error: `None`
- absolute_error_threshold: `0.0016`
- relative_error_threshold: `0.0016`
- within_uncertainty: `None`
- meets_threshold: `True`

## Problem Summary

- Basis: `sto3g`
- Charge: `1`
- Multiplicity: `1`
- Num particles: `(1, 1)`
- Num spatial orbitals: `3`
- Active space metadata: `None`
- Transformers applied: `[]`
- Hamiltonian constants: `{'nuclear_repulsion_energy': 1.763949908139638}`
- Electronic constant correction: `0.000000000000` Hartree
- Point-group metadata: `{'enabled': True, 'status': 'available', 'group': 'C2v', 'topgroup': 'C2v', 'irrep_names': ['A1', 'B2'], 'irrep_ids': [0, 3], 'notes': [], 'orbital_irreps': ['A1', 'B2', 'A1'], 'orbital_occupations': [2.0, 0.0, 0.0], 'orbital_energies': [-1.1991874098289883, -0.03257669398306218, -0.032554358488141574], 'requested_mode': 'auto', 'requested_subgroup': 'auto', 'reduction_mode': 'audit', 'active_irreps': [], 'remove_irreps': []}`

## Mapping

- Mapping kind: `parity_two_qubit_reduction`
- Qubit count: `4`
- Fermionic Hamiltonian terms: `174`
- Qubit Hamiltonian terms: `52`
- Raw qubit count: `4`
- Raw qubit Hamiltonian terms: `52`
- Symmetry tapered qubits: `0`
- Z2 symmetry count: `0`
- Z2 tapering values: `None`
- Symmetry reduction status: `disabled`
- Symmetry reduction validation: `{}`
- Symmetry reduction notes: `['Z2 tapering disabled by mapping.symmetry_reduction.z2.', 'Z2 tapering skipped for LR-ACE in auto mode because its trust-first provenance currently targets untapered parity-reduced workloads.']`

## Backend

- Backend kind: `statevector`
- Precision: `None`
- Shots: `None`
- Seed: `2051`
- Repetitions: `1`
- Abelian grouping: `True`
- Noise enabled: `False`
- Runtime enabled: `False`

## Backend Capability

- backend_kind: `statevector`
- statevector: `True`
- shot_based: `False`
- exact_baseline: `True`
- runtime_ready: `False`
- session_ready: `False`
- batch_ready: `False`
- mitigation_ready: `False`
- noise_model_ready: `False`
- supports_grouping: `False`
- supports_repetitions: `False`
- supports_confidence_metrics: `False`

## Execution Policy

- name: `benchmark`
- default_shots: `None`
- default_repetitions: `5`
- exact_baseline_required: `True`
- confidence_rule: `require exact baseline when available; use repeated sampling for shot backends`
- mitigation_posture: `symmetry-check preferred`
- runtime_ready_expected: `False`
- session_ready_expected: `False`
- batch_ready_expected: `False`
- noise_ready_expected: `False`

## Chemical Accuracy (Local Execution)

- available: `True`
- assessment_target: `local_execution`
- status: `validated`
- meets_chemical_accuracy: `True`
- absolute_error_hartree: `0.000001391982` Hartree
- absolute_error_kcal_mol: `0.0008734817178406965`
- threshold_hartree: `0.0016`
- threshold_kcal_mol: `1.0040151583999999`
- statistical_error: `None`
- notes: `['Meets chemical accuracy threshold.']`

## Compressed vs Uncompressed

- available: `True`
- method: `modified_cholesky`
- rank: `6`
- threshold: `1e-10`
- pre_term_count: `52`
- post_term_count: `52`
- compressed_solver_energy: `-3.031533375572` Hartree
- uncompressed_solver_energy: `-3.031534569679` Hartree
- compressed_total_energy: `-1.267583467433` Hartree
- uncompressed_total_energy: `-1.267584661540` Hartree
- absolute_error: `0.000001194107` Hartree
- relative_error: `9.420334359450455e-07`
- compressed_solve_wall_time_seconds: `0.398849000048358`
- uncompressed_solve_wall_time_seconds: `0.34311766701284796`

## Reduction Audit

- original_num_particles: `(1, 1)`
- original_num_spatial_orbitals: `3`
- reduced_num_particles: `(1, 1)`
- reduced_num_spatial_orbitals: `3`
- transformers_applied: `[]`
- active_space_metadata: `None`
- selection_mode: `none`
- selection_reason: `No active-space reduction requested.`
- selected_active_orbitals: `[]`
- selected_active_orbitals_original: `[]`
- frozen_core_orbitals: `[]`
- removed_orbitals: `[]`
- hamiltonian_constants: `{'nuclear_repulsion_energy': 1.763949908139638}`
- constant_energy_correction: `0.000000000000` Hartree
- nuclear_repulsion_energy: `1.763949908140` Hartree
- external_point_charge_nuclear_interaction_energy: `0.000000000000` Hartree
- boundary_embedding_constant_energy: `0.000000000000` Hartree
- total_constant_correction: `1.763949908140` Hartree
- energy_formula: `total_energy = solver_energy + constant_energy_correction + nuclear_repulsion_energy + external_point_charge_nuclear_interaction_energy + boundary_embedding_constant_energy; electronic_energy = solver_energy + constant_energy_correction`
- point_group_metadata: `{'enabled': True, 'status': 'available', 'group': 'C2v', 'topgroup': 'C2v', 'irrep_names': ['A1', 'B2'], 'irrep_ids': [0, 3], 'notes': [], 'orbital_irreps': ['A1', 'B2', 'A1'], 'orbital_occupations': [2.0, 0.0, 0.0], 'orbital_energies': [-1.1991874098289883, -0.03257669398306218, -0.032554358488141574], 'requested_mode': 'auto', 'requested_subgroup': 'auto', 'reduction_mode': 'audit', 'active_irreps': [], 'remove_irreps': []}`

## Reduction Plan

- enabled: `True`
- mode: `disabled`
- strategy: `none`
- recommended_changes: `{}`
- notes: `['No reduction planning inputs were requested.']`
- provenance: `{'source': 'qcchem.chem.reduction_planner', 'policy_name': 'benchmark'}`

## Compression Audit

- enabled: `True`
- method: `modified_cholesky`
- rank: `6`
- threshold: `1e-10`
- max_rank: `9`
- apply_to_solver: `True`
- execution_enabled: `True`
- original_num_qubits: `4`
- compressed_num_qubits: `4`
- original_fermionic_term_count: `174`
- original_qubit_term_count: `52`
- compressed_term_count_estimate: `52`
- pre_term_count: `52`
- post_term_count: `52`
- primary_rank: `6`
- secondary_rank: `None`
- reconstruction_error_frobenius: `1.5700924586837752e-16`
- reconstruction_error: `1.5700924586837752e-16`
- verification_status: `validated`
- notes: `['Modified-Cholesky compression reconstructed the two-electron pair matrix for execution.']`

## Measurement Plan

- strategy: `low_rank_lr_ace_adaptive_local`
- grouping_policy: `low_rank_factor_aware`
- execution_mode: `estimator`
- low_rank_aware: `True`
- term_count: `52`
- group_count: `7`
- estimated_shot_cost: `70000.0`
- runtime_precision_target: `0.01`
- uncompressed_group_count: `13`
- uncompressed_estimated_shot_cost: `130000.0`
- cost_reduction_ratio: `0.5384615384615384`
- notes: `["Measurement groups estimated with strategy 'low_rank_lr_ace_adaptive_local'.", 'Per-group shot estimate derived from precision target 0.01.', 'Compressed Hamiltonian enabled low-rank-aware grouping and cost estimation.']`

## Local Calibration Summary

> This section covers executed-solver calibration only; runtime-derived hardware evidence is tracked separately below.

- available: `True`
- measured_wall_time_seconds: `0.398849000048358`
- measured_shot_usage: `None`
- precision_target: `0.01`
- achieved_error: `0.000001194107` Hartree
- estimated_measurement_cost: `70000.0`
- estimated_vs_measured_cost: `None`
- reference_target: `compressed_vs_uncompressed`
- notes: `['Measured wall time is taken from the executed solver path, not full workflow overhead.', 'Measured shot usage is derived from backend shots, repeat count, and measurement group count.']`

## Hardware Execution

- hardware_verified: `False`
- hardware_evidence_tier: `None`
- attempted: `None`
- submitted: `None`
- succeeded: `None`
- service: `None`
- mode: `None`
- session_requested: `None`
- batch_requested: `None`
- backend_name: `None`
- provider: `None`
- layout_strategy: `None`
- selected_layout: `[]`
- layout_score: `None`
- transpiled_depth: `None`
- transpiled_two_qubit_gate_count: `None`
- transpilation_options: `{}`
- job_id: `None`
- session_id: `None`
- batch_id: `None`
- submission_wall_time_seconds: `None`
- usage_estimation: `{}`
- job_metrics: `{}`
- failure_category: `None`
- failure_message: `None`
- verification_status: `None`
- options_snapshot: `{}`
- returned_job_metadata: `{}`
- result_provenance: `{}`

## Variational Result

- available: `True`
- solver_kind: `lr_ace`
- optimizer: `{'kind': 'COBYLA', 'maxiter': 3000, 'tol': None}`
- ansatz: `{'kind': 'lr_ace', 'rotation_blocks': ['ry', 'rz'], 'entanglement_blocks': 'cz', 'entanglement': 'full', 'reps': 16, 'lr_ace': {'algorithm_name': 'LR-ACE', 'low_rank_aware': True, 'selection_rule': 'adaptive_score_weight_locality_reference_mixing', 'source_terms': [{'pauli': 'XXXX', 'weight': 0.03594452854855405, 'coefficient_real': 0.03594452854855405, 'coefficient_imag': 0.0}, {'pauli': 'XXYY', 'weight': 0.03594452854855405, 'coefficient_real': -0.03594452854855405, 'coefficient_imag': 0.0}, {'pauli': 'YYXX', 'weight': 0.03594452854855405, 'coefficient_real': -0.03594452854855405, 'coefficient_imag': 0.0}, {'pauli': 'YYYY', 'weight': 0.03594452854855405, 'coefficient_real': 0.03594452854855405, 'coefficient_imag': 0.0}, {'pauli': 'IXIX', 'weight': 0.0359445220444363, 'coefficient_real': 0.0359445220444363, 'coefficient_imag': 0.0}, {'pauli': 'IXZX', 'weight': 0.0359445220444363, 'coefficient_real': -0.0359445220444363, 'coefficient_imag': 0.0}, {'pauli': 'ZXIX', 'weight': 0.0359445220444363, 'coefficient_real': 0.0359445220444363, 'coefficient_imag': 0.0}, {'pauli': 'ZXZX', 'weight': 0.0359445220444363, 'coefficient_real': -0.0359445220444363, 'coefficient_imag': 0.0}, {'pauli': 'IXXI', 'weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0}, {'pauli': 'IXXZ', 'weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0}, {'pauli': 'XIIX', 'weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0}, {'pauli': 'XIZX', 'weight': 0.022837714407336514, 'coefficient_real': 0.022837714407336514, 'coefficient_imag': 0.0}, {'pauli': 'XZIX', 'weight': 0.022837714407336514, 'coefficient_real': 0.022837714407336514, 'coefficient_imag': 0.0}, {'pauli': 'XZZX', 'weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0}, {'pauli': 'ZXXI', 'weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0}, {'pauli': 'ZXXZ', 'weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0}, {'pauli': 'XXZI', 'weight': 0.022837491239045354, 'coefficient_real': 0.022837491239045354, 'coefficient_imag': 0.0}, {'pauli': 'YYZI', 'weight': 0.022837491239045354, 'coefficient_real': -0.022837491239045354, 'coefficient_imag': 0.0}, {'pauli': 'ZIXX', 'weight': 0.022837491239045354, 'coefficient_real': -0.022837491239045354, 'coefficient_imag': 0.0}, {'pauli': 'ZIYY', 'weight': 0.022837491239045354, 'coefficient_real': 0.022837491239045354, 'coefficient_imag': 0.0}, {'pauli': 'XXZZ', 'weight': 0.022837079428386947, 'coefficient_real': 0.022837079428386947, 'coefficient_imag': 0.0}, {'pauli': 'YYZZ', 'weight': 0.022837079428386947, 'coefficient_real': -0.022837079428386947, 'coefficient_imag': 0.0}, {'pauli': 'ZZXX', 'weight': 0.022837079428386947, 'coefficient_real': 0.022837079428386947, 'coefficient_imag': 0.0}, {'pauli': 'ZZYY', 'weight': 0.022837079428386947, 'coefficient_real': -0.022837079428386947, 'coefficient_imag': 0.0}, {'pauli': 'XIXI', 'weight': 0.01821108073582051, 'coefficient_real': 0.01821108073582051, 'coefficient_imag': 0.0}, {'pauli': 'XIXZ', 'weight': 0.01821108073582051, 'coefficient_real': 0.01821108073582051, 'coefficient_imag': 0.0}, {'pauli': 'XZXI', 'weight': 0.01821108073582051, 'coefficient_real': -0.01821108073582051, 'coefficient_imag': 0.0}, {'pauli': 'XZXZ', 'weight': 0.01821108073582051, 'coefficient_real': -0.01821108073582051, 'coefficient_imag': 0.0}, {'pauli': 'IZXX', 'weight': 7.080767526787017e-07, 'coefficient_real': 7.080767526787017e-07, 'coefficient_imag': 0.0}, {'pauli': 'IZYY', 'weight': 7.080767526787017e-07, 'coefficient_real': -7.080767526787017e-07, 'coefficient_imag': 0.0}, {'pauli': 'XXIZ', 'weight': 7.080767526787017e-07, 'coefficient_real': -7.080767526787017e-07, 'coefficient_imag': 0.0}, {'pauli': 'YYIZ', 'weight': 7.080767526787017e-07, 'coefficient_real': 7.080767526787017e-07, 'coefficient_imag': 0.0}, {'pauli': 'IIXX', 'weight': 3.0351623270207856e-07, 'coefficient_real': -3.0351623270207856e-07, 'coefficient_imag': 0.0}, {'pauli': 'IIYY', 'weight': 3.0351623270207856e-07, 'coefficient_real': 3.0351623270207856e-07, 'coefficient_imag': 0.0}, {'pauli': 'XXII', 'weight': 3.0351623270207856e-07, 'coefficient_real': -3.0351623270207856e-07, 'coefficient_imag': 0.0}, {'pauli': 'YYII', 'weight': 3.0351623270207856e-07, 'coefficient_real': 3.0351623270207856e-07, 'coefficient_imag': 0.0}], 'candidate_generators': [{'pauli': 'IYIX', 'source_pauli': 'IXIX', 'source_weight': 0.0359445220444363, 'coefficient_real': 0.0359445220444363, 'coefficient_imag': 0.0, 'adaptive_score': 0.0359445220444363, 'locality': 2, 'reference_mixing_relevance': 1.0, 'candidate_index': 0}, {'pauli': 'IXIY', 'source_pauli': 'IXIX', 'source_weight': 0.0359445220444363, 'coefficient_real': 0.0359445220444363, 'coefficient_imag': 0.0, 'adaptive_score': 0.0359445220444363, 'locality': 2, 'reference_mixing_relevance': 1.0, 'candidate_index': 1}, {'pauli': 'IYXI', 'source_pauli': 'IXXI', 'source_weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.022837714407336514, 'locality': 2, 'reference_mixing_relevance': 1.0, 'candidate_index': 2}, {'pauli': 'IXYI', 'source_pauli': 'IXXI', 'source_weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.022837714407336514, 'locality': 2, 'reference_mixing_relevance': 1.0, 'candidate_index': 3}, {'pauli': 'YIIX', 'source_pauli': 'XIIX', 'source_weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.022837714407336514, 'locality': 2, 'reference_mixing_relevance': 1.0, 'candidate_index': 4}, {'pauli': 'XIIY', 'source_pauli': 'XIIX', 'source_weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.022837714407336514, 'locality': 2, 'reference_mixing_relevance': 1.0, 'candidate_index': 5}, {'pauli': 'IYZX', 'source_pauli': 'IXZX', 'source_weight': 0.0359445220444363, 'coefficient_real': -0.0359445220444363, 'coefficient_imag': 0.0, 'adaptive_score': 0.019969178913575723, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 6}, {'pauli': 'IXZY', 'source_pauli': 'IXZX', 'source_weight': 0.0359445220444363, 'coefficient_real': -0.0359445220444363, 'coefficient_imag': 0.0, 'adaptive_score': 0.019969178913575723, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 7}, {'pauli': 'ZYIX', 'source_pauli': 'ZXIX', 'source_weight': 0.0359445220444363, 'coefficient_real': 0.0359445220444363, 'coefficient_imag': 0.0, 'adaptive_score': 0.019969178913575723, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 8}, {'pauli': 'ZXIY', 'source_pauli': 'ZXIX', 'source_weight': 0.0359445220444363, 'coefficient_real': 0.0359445220444363, 'coefficient_imag': 0.0, 'adaptive_score': 0.019969178913575723, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 9}, {'pauli': 'YIXI', 'source_pauli': 'XIXI', 'source_weight': 0.01821108073582051, 'coefficient_real': 0.01821108073582051, 'coefficient_imag': 0.0, 'adaptive_score': 0.01821108073582051, 'locality': 2, 'reference_mixing_relevance': 1.0, 'candidate_index': 10}, {'pauli': 'XIYI', 'source_pauli': 'XIXI', 'source_weight': 0.01821108073582051, 'coefficient_real': 0.01821108073582051, 'coefficient_imag': 0.0, 'adaptive_score': 0.01821108073582051, 'locality': 2, 'reference_mixing_relevance': 1.0, 'candidate_index': 11}, {'pauli': 'YXXX', 'source_pauli': 'XXXX', 'source_weight': 0.03594452854855405, 'coefficient_real': 0.03594452854855405, 'coefficient_imag': 0.0, 'adaptive_score': 0.017972264274277026, 'locality': 4, 'reference_mixing_relevance': 1.0, 'candidate_index': 12}, {'pauli': 'XYXX', 'source_pauli': 'XXXX', 'source_weight': 0.03594452854855405, 'coefficient_real': 0.03594452854855405, 'coefficient_imag': 0.0, 'adaptive_score': 0.017972264274277026, 'locality': 4, 'reference_mixing_relevance': 1.0, 'candidate_index': 13}, {'pauli': 'XXYX', 'source_pauli': 'XXXX', 'source_weight': 0.03594452854855405, 'coefficient_real': 0.03594452854855405, 'coefficient_imag': 0.0, 'adaptive_score': 0.017972264274277026, 'locality': 4, 'reference_mixing_relevance': 1.0, 'candidate_index': 14}, {'pauli': 'XXXY', 'source_pauli': 'XXXX', 'source_weight': 0.03594452854855405, 'coefficient_real': 0.03594452854855405, 'coefficient_imag': 0.0, 'adaptive_score': 0.017972264274277026, 'locality': 4, 'reference_mixing_relevance': 1.0, 'candidate_index': 15}, {'pauli': 'YXYY', 'source_pauli': 'XXYY', 'source_weight': 0.03594452854855405, 'coefficient_real': -0.03594452854855405, 'coefficient_imag': 0.0, 'adaptive_score': 0.017972264274277026, 'locality': 4, 'reference_mixing_relevance': 1.0, 'candidate_index': 16}, {'pauli': 'XYYY', 'source_pauli': 'XXYY', 'source_weight': 0.03594452854855405, 'coefficient_real': -0.03594452854855405, 'coefficient_imag': 0.0, 'adaptive_score': 0.017972264274277026, 'locality': 4, 'reference_mixing_relevance': 1.0, 'candidate_index': 17}, {'pauli': 'YYYX', 'source_pauli': 'YYXX', 'source_weight': 0.03594452854855405, 'coefficient_real': -0.03594452854855405, 'coefficient_imag': 0.0, 'adaptive_score': 0.017972264274277026, 'locality': 4, 'reference_mixing_relevance': 1.0, 'candidate_index': 18}, {'pauli': 'YYXY', 'source_pauli': 'YYXX', 'source_weight': 0.03594452854855405, 'coefficient_real': -0.03594452854855405, 'coefficient_imag': 0.0, 'adaptive_score': 0.017972264274277026, 'locality': 4, 'reference_mixing_relevance': 1.0, 'candidate_index': 19}, {'pauli': 'ZYZX', 'source_pauli': 'ZXZX', 'source_weight': 0.0359445220444363, 'coefficient_real': -0.0359445220444363, 'coefficient_imag': 0.0, 'adaptive_score': 0.013479195766663614, 'locality': 4, 'reference_mixing_relevance': 0.5, 'candidate_index': 20}, {'pauli': 'ZXZY', 'source_pauli': 'ZXZX', 'source_weight': 0.0359445220444363, 'coefficient_real': -0.0359445220444363, 'coefficient_imag': 0.0, 'adaptive_score': 0.013479195766663614, 'locality': 4, 'reference_mixing_relevance': 0.5, 'candidate_index': 21}, {'pauli': 'IYXZ', 'source_pauli': 'IXXZ', 'source_weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.012687619115186953, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 22}, {'pauli': 'IXYZ', 'source_pauli': 'IXXZ', 'source_weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.012687619115186953, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 23}, {'pauli': 'YIZX', 'source_pauli': 'XIZX', 'source_weight': 0.022837714407336514, 'coefficient_real': 0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.012687619115186953, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 24}, {'pauli': 'XIZY', 'source_pauli': 'XIZX', 'source_weight': 0.022837714407336514, 'coefficient_real': 0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.012687619115186953, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 25}, {'pauli': 'YZIX', 'source_pauli': 'XZIX', 'source_weight': 0.022837714407336514, 'coefficient_real': 0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.012687619115186953, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 26}, {'pauli': 'XZIY', 'source_pauli': 'XZIX', 'source_weight': 0.022837714407336514, 'coefficient_real': 0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.012687619115186953, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 27}, {'pauli': 'ZYXI', 'source_pauli': 'ZXXI', 'source_weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.012687619115186953, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 28}, {'pauli': 'ZXYI', 'source_pauli': 'ZXXI', 'source_weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.012687619115186953, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 29}, {'pauli': 'YXZI', 'source_pauli': 'XXZI', 'source_weight': 0.022837491239045354, 'coefficient_real': 0.022837491239045354, 'coefficient_imag': 0.0, 'adaptive_score': 0.012687495132802975, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 30}, {'pauli': 'XYZI', 'source_pauli': 'XXZI', 'source_weight': 0.022837491239045354, 'coefficient_real': 0.022837491239045354, 'coefficient_imag': 0.0, 'adaptive_score': 0.012687495132802975, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 31}, {'pauli': 'ZIYX', 'source_pauli': 'ZIXX', 'source_weight': 0.022837491239045354, 'coefficient_real': -0.022837491239045354, 'coefficient_imag': 0.0, 'adaptive_score': 0.012687495132802975, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 32}, {'pauli': 'ZIXY', 'source_pauli': 'ZIXX', 'source_weight': 0.022837491239045354, 'coefficient_real': -0.022837491239045354, 'coefficient_imag': 0.0, 'adaptive_score': 0.012687495132802975, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 33}, {'pauli': 'YIXZ', 'source_pauli': 'XIXZ', 'source_weight': 0.01821108073582051, 'coefficient_real': 0.01821108073582051, 'coefficient_imag': 0.0, 'adaptive_score': 0.010117267075455837, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 34}, {'pauli': 'XIYZ', 'source_pauli': 'XIXZ', 'source_weight': 0.01821108073582051, 'coefficient_real': 0.01821108073582051, 'coefficient_imag': 0.0, 'adaptive_score': 0.010117267075455837, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 35}, {'pauli': 'YZXI', 'source_pauli': 'XZXI', 'source_weight': 0.01821108073582051, 'coefficient_real': -0.01821108073582051, 'coefficient_imag': 0.0, 'adaptive_score': 0.010117267075455837, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 36}, {'pauli': 'XZYI', 'source_pauli': 'XZXI', 'source_weight': 0.01821108073582051, 'coefficient_real': -0.01821108073582051, 'coefficient_imag': 0.0, 'adaptive_score': 0.010117267075455837, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 37}, {'pauli': 'YZZX', 'source_pauli': 'XZZX', 'source_weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.008564142902751194, 'locality': 4, 'reference_mixing_relevance': 0.5, 'candidate_index': 38}, {'pauli': 'XZZY', 'source_pauli': 'XZZX', 'source_weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.008564142902751194, 'locality': 4, 'reference_mixing_relevance': 0.5, 'candidate_index': 39}, {'pauli': 'ZYXZ', 'source_pauli': 'ZXXZ', 'source_weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.008564142902751194, 'locality': 4, 'reference_mixing_relevance': 0.5, 'candidate_index': 40}, {'pauli': 'ZXYZ', 'source_pauli': 'ZXXZ', 'source_weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.008564142902751194, 'locality': 4, 'reference_mixing_relevance': 0.5, 'candidate_index': 41}, {'pauli': 'YXZZ', 'source_pauli': 'XXZZ', 'source_weight': 0.022837079428386947, 'coefficient_real': 0.022837079428386947, 'coefficient_imag': 0.0, 'adaptive_score': 0.008563904785645105, 'locality': 4, 'reference_mixing_relevance': 0.5, 'candidate_index': 42}, {'pauli': 'XYZZ', 'source_pauli': 'XXZZ', 'source_weight': 0.022837079428386947, 'coefficient_real': 0.022837079428386947, 'coefficient_imag': 0.0, 'adaptive_score': 0.008563904785645105, 'locality': 4, 'reference_mixing_relevance': 0.5, 'candidate_index': 43}, {'pauli': 'ZZYX', 'source_pauli': 'ZZXX', 'source_weight': 0.022837079428386947, 'coefficient_real': 0.022837079428386947, 'coefficient_imag': 0.0, 'adaptive_score': 0.008563904785645105, 'locality': 4, 'reference_mixing_relevance': 0.5, 'candidate_index': 44}, {'pauli': 'ZZXY', 'source_pauli': 'ZZXX', 'source_weight': 0.022837079428386947, 'coefficient_real': 0.022837079428386947, 'coefficient_imag': 0.0, 'adaptive_score': 0.008563904785645105, 'locality': 4, 'reference_mixing_relevance': 0.5, 'candidate_index': 45}, {'pauli': 'YZXZ', 'source_pauli': 'XZXZ', 'source_weight': 0.01821108073582051, 'coefficient_real': -0.01821108073582051, 'coefficient_imag': 0.0, 'adaptive_score': 0.006829155275932692, 'locality': 4, 'reference_mixing_relevance': 0.5, 'candidate_index': 46}, {'pauli': 'XZYZ', 'source_pauli': 'XZXZ', 'source_weight': 0.01821108073582051, 'coefficient_real': -0.01821108073582051, 'coefficient_imag': 0.0, 'adaptive_score': 0.006829155275932692, 'locality': 4, 'reference_mixing_relevance': 0.5, 'candidate_index': 47}, {'pauli': 'IZYX', 'source_pauli': 'IZXX', 'source_weight': 7.080767526787017e-07, 'coefficient_real': 7.080767526787017e-07, 'coefficient_imag': 0.0, 'adaptive_score': 3.9337597371038975e-07, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 48}, {'pauli': 'IZXY', 'source_pauli': 'IZXX', 'source_weight': 7.080767526787017e-07, 'coefficient_real': 7.080767526787017e-07, 'coefficient_imag': 0.0, 'adaptive_score': 3.9337597371038975e-07, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 49}, {'pauli': 'YXIZ', 'source_pauli': 'XXIZ', 'source_weight': 7.080767526787017e-07, 'coefficient_real': -7.080767526787017e-07, 'coefficient_imag': 0.0, 'adaptive_score': 3.9337597371038975e-07, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 50}, {'pauli': 'XYIZ', 'source_pauli': 'XXIZ', 'source_weight': 7.080767526787017e-07, 'coefficient_real': -7.080767526787017e-07, 'coefficient_imag': 0.0, 'adaptive_score': 3.9337597371038975e-07, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'candidate_index': 51}, {'pauli': 'IIYX', 'source_pauli': 'IIXX', 'source_weight': 3.0351623270207856e-07, 'coefficient_real': -3.0351623270207856e-07, 'coefficient_imag': 0.0, 'adaptive_score': 3.0351623270207856e-07, 'locality': 2, 'reference_mixing_relevance': 1.0, 'candidate_index': 52}, {'pauli': 'IIXY', 'source_pauli': 'IIXX', 'source_weight': 3.0351623270207856e-07, 'coefficient_real': -3.0351623270207856e-07, 'coefficient_imag': 0.0, 'adaptive_score': 3.0351623270207856e-07, 'locality': 2, 'reference_mixing_relevance': 1.0, 'candidate_index': 53}, {'pauli': 'YXII', 'source_pauli': 'XXII', 'source_weight': 3.0351623270207856e-07, 'coefficient_real': -3.0351623270207856e-07, 'coefficient_imag': 0.0, 'adaptive_score': 3.0351623270207856e-07, 'locality': 2, 'reference_mixing_relevance': 1.0, 'candidate_index': 54}, {'pauli': 'XYII', 'source_pauli': 'XXII', 'source_weight': 3.0351623270207856e-07, 'coefficient_real': -3.0351623270207856e-07, 'coefficient_imag': 0.0, 'adaptive_score': 3.0351623270207856e-07, 'locality': 2, 'reference_mixing_relevance': 1.0, 'candidate_index': 55}], 'selected_generators': [{'pauli': 'IYIX', 'source_pauli': 'IXIX', 'source_weight': 0.0359445220444363, 'coefficient_real': 0.0359445220444363, 'coefficient_imag': 0.0, 'adaptive_score': 0.0359445220444363, 'locality': 2, 'reference_mixing_relevance': 1.0, 'batch_index': 0}, {'pauli': 'IYXI', 'source_pauli': 'IXXI', 'source_weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.022837714407336514, 'locality': 2, 'reference_mixing_relevance': 1.0, 'batch_index': 1}, {'pauli': 'YIIX', 'source_pauli': 'XIIX', 'source_weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.022837714407336514, 'locality': 2, 'reference_mixing_relevance': 1.0, 'batch_index': 2}, {'pauli': 'IYZX', 'source_pauli': 'IXZX', 'source_weight': 0.0359445220444363, 'coefficient_real': -0.0359445220444363, 'coefficient_imag': 0.0, 'adaptive_score': 0.019969178913575723, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'batch_index': 3}, {'pauli': 'ZYIX', 'source_pauli': 'ZXIX', 'source_weight': 0.0359445220444363, 'coefficient_real': 0.0359445220444363, 'coefficient_imag': 0.0, 'adaptive_score': 0.019969178913575723, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'batch_index': 4}, {'pauli': 'YIXI', 'source_pauli': 'XIXI', 'source_weight': 0.01821108073582051, 'coefficient_real': 0.01821108073582051, 'coefficient_imag': 0.0, 'adaptive_score': 0.01821108073582051, 'locality': 2, 'reference_mixing_relevance': 1.0, 'batch_index': 5}, {'pauli': 'YXXX', 'source_pauli': 'XXXX', 'source_weight': 0.03594452854855405, 'coefficient_real': 0.03594452854855405, 'coefficient_imag': 0.0, 'adaptive_score': 0.017972264274277026, 'locality': 4, 'reference_mixing_relevance': 1.0, 'batch_index': 6}, {'pauli': 'YXYY', 'source_pauli': 'XXYY', 'source_weight': 0.03594452854855405, 'coefficient_real': -0.03594452854855405, 'coefficient_imag': 0.0, 'adaptive_score': 0.017972264274277026, 'locality': 4, 'reference_mixing_relevance': 1.0, 'batch_index': 7}, {'pauli': 'ZYZX', 'source_pauli': 'ZXZX', 'source_weight': 0.0359445220444363, 'coefficient_real': -0.0359445220444363, 'coefficient_imag': 0.0, 'adaptive_score': 0.013479195766663614, 'locality': 4, 'reference_mixing_relevance': 0.5, 'batch_index': 8}, {'pauli': 'IYXZ', 'source_pauli': 'IXXZ', 'source_weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.012687619115186953, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'batch_index': 9}, {'pauli': 'YIZX', 'source_pauli': 'XIZX', 'source_weight': 0.022837714407336514, 'coefficient_real': 0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.012687619115186953, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'batch_index': 10}, {'pauli': 'YZIX', 'source_pauli': 'XZIX', 'source_weight': 0.022837714407336514, 'coefficient_real': 0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.012687619115186953, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'batch_index': 11}], 'selected_factor_count': 12, 'method_role': 'flagship', 'profile': 'flagship_adaptive', 'validation_mode': 'trust_first', 'ansatz_parameter_count': 12, 'optimized_parameters': [0.005193794265729109, -0.0024115055830804645, 0.0044027507796745085, 0.007522498666850932, -0.0026913599323835956, 0.1097947842319337, -0.08136862983133683, 0.003943730254731841, -0.00998098798981236, 0.07758976908456741, -0.09910265969373332, -0.002522510311704415], 'adaptive': {'enabled': True, 'target_error_hartree': 0.0016, 'max_wall_time_seconds': 1200.0, 'candidate_pool_policy': 'residual_guided', 'candidate_scan_limit': 64, 'residual_batch_size': 8, 'residual_scan_angles': [-0.15, -0.05, 0.05, 0.15], 'min_energy_improvement_hartree': 0.0002, 'max_adaptive_expansions': 3, 'exact_reference_available': True, 'exact_solver_energy': -3.0315347675539805, 'stages': [{'stage_index': 0, 'schedule_index': 0, 'generator_count': 12, 'parameter_count': 12, 'optimizer_maxiter': 1500, 'initial_point_strategy': 'zeros', 'restart_index': 0, 'energy': -3.0315333755722658, 'exact_error_hartree': 1.3919817147822755e-06, 'converged': True, 'iterations': 154, 'evaluations': 154, 'optimizer_message': 'Optimization terminated successfully.'}], 'expansions': [], 'scheduled_generator_counts': [12, 16], 'original_generator_schedule_length': 2, 'best_stage_index': 0, 'best_energy': -3.0315333755722658, 'best_exact_error_hartree': 1.3919817147822755e-06, 'trust_label': 'passed_exact_reference', 'uncompressed_check_triggered': True, 'compression_proxy_error_hartree': 1.1941071340615395e-06, 'uncompressed_exact_solver_energy': -3.0315347675539783, 'uncompressed_lr_ace_error_hartree': 1.9787457850029e-07, 'combined_error_vs_uncompressed_exact_hartree': 1.3919817125618295e-06}, 'low_rank_method': 'modified_cholesky', 'factor_rank': 6, 'compression_threshold': 1e-10, 'compression_reconstruction_error': 1.5700924586837752e-16, 'pre_term_count': 52, 'post_term_count': 52, 'local_accuracy_gate': {'passed': True, 'threshold_hartree': 0.0016, 'absolute_error_hartree': 1.3919817214436137e-06}, 'validation_gate': {'trust_label': 'passed_exact_reference', 'verification_status': 'validated', 'validated': True, 'target_error_hartree': 0.0016, 'exact_available': True, 'local_exact_error_hartree': 1.3919817147822755e-06, 'compression_enabled': True, 'compressed_solver_energy': -3.0315333755722658, 'uncompressed_solver_energy': -3.0315345696794, 'uncompressed_exact_solver_energy': -3.0315347675539783, 'runtime_attempted': False, 'runtime_accuracy_met': None, 'blocking_reason': None}}}`
- initial_point_strategy: `adaptive_schedule`
- initial_point_reused: `False`
- initial_point_source: `None`
- initial_point_fallback_reason: `None`
- initial_point_provenance: `{'effective_strategy': 'adaptive_schedule', 'reused': False}`
- parameter_count: `12`
- converged: `True`
- iterations: `154`
- evaluations: `154`
- final_objective_energy: `-3.031533375572` Hartree
- optimizer_message: `Optimization terminated successfully.`

## LR-ACE Exploratory Algorithm

- algorithm_name: `LR-ACE`
- low_rank_method: `modified_cholesky`
- factor_rank: `6`
- selected_factor_count: `12`
- local_accuracy_gate: `{'passed': True, 'threshold_hartree': 0.0016, 'absolute_error_hartree': 1.3919817214436137e-06}`
- selected_generators: `[{'pauli': 'IYIX', 'source_pauli': 'IXIX', 'source_weight': 0.0359445220444363, 'coefficient_real': 0.0359445220444363, 'coefficient_imag': 0.0, 'adaptive_score': 0.0359445220444363, 'locality': 2, 'reference_mixing_relevance': 1.0, 'batch_index': 0}, {'pauli': 'IYXI', 'source_pauli': 'IXXI', 'source_weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.022837714407336514, 'locality': 2, 'reference_mixing_relevance': 1.0, 'batch_index': 1}, {'pauli': 'YIIX', 'source_pauli': 'XIIX', 'source_weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.022837714407336514, 'locality': 2, 'reference_mixing_relevance': 1.0, 'batch_index': 2}, {'pauli': 'IYZX', 'source_pauli': 'IXZX', 'source_weight': 0.0359445220444363, 'coefficient_real': -0.0359445220444363, 'coefficient_imag': 0.0, 'adaptive_score': 0.019969178913575723, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'batch_index': 3}, {'pauli': 'ZYIX', 'source_pauli': 'ZXIX', 'source_weight': 0.0359445220444363, 'coefficient_real': 0.0359445220444363, 'coefficient_imag': 0.0, 'adaptive_score': 0.019969178913575723, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'batch_index': 4}, {'pauli': 'YIXI', 'source_pauli': 'XIXI', 'source_weight': 0.01821108073582051, 'coefficient_real': 0.01821108073582051, 'coefficient_imag': 0.0, 'adaptive_score': 0.01821108073582051, 'locality': 2, 'reference_mixing_relevance': 1.0, 'batch_index': 5}, {'pauli': 'YXXX', 'source_pauli': 'XXXX', 'source_weight': 0.03594452854855405, 'coefficient_real': 0.03594452854855405, 'coefficient_imag': 0.0, 'adaptive_score': 0.017972264274277026, 'locality': 4, 'reference_mixing_relevance': 1.0, 'batch_index': 6}, {'pauli': 'YXYY', 'source_pauli': 'XXYY', 'source_weight': 0.03594452854855405, 'coefficient_real': -0.03594452854855405, 'coefficient_imag': 0.0, 'adaptive_score': 0.017972264274277026, 'locality': 4, 'reference_mixing_relevance': 1.0, 'batch_index': 7}, {'pauli': 'ZYZX', 'source_pauli': 'ZXZX', 'source_weight': 0.0359445220444363, 'coefficient_real': -0.0359445220444363, 'coefficient_imag': 0.0, 'adaptive_score': 0.013479195766663614, 'locality': 4, 'reference_mixing_relevance': 0.5, 'batch_index': 8}, {'pauli': 'IYXZ', 'source_pauli': 'IXXZ', 'source_weight': 0.022837714407336514, 'coefficient_real': -0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.012687619115186953, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'batch_index': 9}, {'pauli': 'YIZX', 'source_pauli': 'XIZX', 'source_weight': 0.022837714407336514, 'coefficient_real': 0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.012687619115186953, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'batch_index': 10}, {'pauli': 'YZIX', 'source_pauli': 'XZIX', 'source_weight': 0.022837714407336514, 'coefficient_real': 0.022837714407336514, 'coefficient_imag': 0.0, 'adaptive_score': 0.012687619115186953, 'locality': 3, 'reference_mixing_relevance': 0.6666666666666666, 'batch_index': 11}]`

## Mitigation

- symmetry_check: `{'requested': True, 'performed': False, 'status': 'hook_available_not_implemented', 'strategy': 'parity_placeholder'}`
- readout_mitigation: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- zne: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- pec: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- applied_methods: `[]`

## Input Provenance

- source_1: kind=`inline_geometry` format=`inline` atom_count=`3` source_path=`None` resolved_path=`None` file_sha256=`None` normalized_geometry_sha256=`0b4d09ceda090567c315ec27a02c8da5ceaf27962b9459064a6344f41ccfd3da`

## Provenance

- Schema version: `qcchem.result.v0.8-alpha`
- Timestamp: `2026-05-17T10:50:41.753164+00:00`
- Wall time (s): `0.9209322920069098`
- Git commit: `a7c0893f8c2b2a07e7c911c49536761ba5ebb250`
- Git commit short: `a7c0893f8c2b`
- Git branch: `codex/lr-ace-flagship`
- Git describe: `a7c0893-dirty`
- Git remote origin: `https://github.com/wuls968/QCchem.git`
- Repo root: `.`
- Workspace dirty: `True`
- Git status summary: `{'staged': 0, 'unstaged': 22, 'untracked': 6}`
- Workspace fingerprint: `0683df35fb04411f9733d07abfc77ee9d6c4ab5519da5887ce07a9a9b1ca397a`
- Dependency versions: `{'python': '3.12.2', 'qiskit': '1.4.0', 'qiskit_nature': '0.7.2', 'numpy': '1.26.4', 'scipy': '1.13.1', 'pyscf': '2.8.0', 'qiskit_aer': '0.16.1'}`
- Seed: `2051`
- Source config: `configs/lr_ace/h3plus_adaptive.yaml`

## Artifacts

- result.json: `artifacts/lr_ace_flagship_suite_v1/cases/h3plus_lr_ace_adaptive/result.json`
- exact_result.json: `artifacts/lr_ace_flagship_suite_v1/cases/h3plus_lr_ace_adaptive/exact_result.json`
- report.md: `artifacts/lr_ace_flagship_suite_v1/cases/h3plus_lr_ace_adaptive/report.md`
- resolved_config.yaml: `artifacts/lr_ace_flagship_suite_v1/cases/h3plus_lr_ace_adaptive/resolved_config.yaml`
- run.log: `artifacts/lr_ace_flagship_suite_v1/cases/h3plus_lr_ace_adaptive/run.log`
- calibration.json: `artifacts/lr_ace_flagship_suite_v1/cases/h3plus_lr_ace_adaptive/calibration.json`
- calibration_report.md: `artifacts/lr_ace_flagship_suite_v1/cases/h3plus_lr_ace_adaptive/calibration_report.md`
- runtime_submission.json: `artifacts/lr_ace_flagship_suite_v1/cases/h3plus_lr_ace_adaptive/runtime_submission.json`
- qcschema.json: `None`
- result.h5: `None`

## Log Summary

- Loading config from configs/lr_ace/h3plus_adaptive.yaml
- Resolved molecular input: kind=inline_geometry, format=inline, atoms=3, sha256=0b4d09ceda09
- Building electronic structure problem
- Applying mapping: parity_two_qubit_reduction
- Z2 tapering skipped for LR-ACE in auto mode because its trust-first provenance currently targets untapered parity-reduced workloads.
- Constructed compressed mapped Hamiltonian via modified_cholesky
- Computed compression audit: modified_cholesky
- Prepared measurement plan: groups=7, cost=70000
- Preparing backend: statevector
- Running solver: lr_ace
- Computing exact spectrum for 1 states
- Writing exact baseline artifact to artifacts/lr_ace_flagship_suite_v1/cases/h3plus_lr_ace_adaptive/exact_result.json
- Computed compressed-vs-uncompressed execution comparison
- Computed empirical calibration: wall_time=0.399s, measured_cost=None
- Writing JSON result to artifacts/lr_ace_flagship_suite_v1/cases/h3plus_lr_ace_adaptive/result.json
- Writing Markdown report to artifacts/lr_ace_flagship_suite_v1/cases/h3plus_lr_ace_adaptive/report.md
- Run completed
