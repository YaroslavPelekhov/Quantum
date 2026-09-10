"""Export logical measured circuits and a plan, with NO cloud submission code."""
import json
import random
from pathlib import Path
from qiskit import qpy, qasm3
from run_readiness import inputs, digest, bks_indicator, EXPERIMENT, HERE
from qiskit.quantum_info import Statevector


def main():
    rows, _ = inputs()
    out = HERE/'hardware'
    out.mkdir(exist_ok=True)
    cases=['karate','chesapeake','football']
    methods=['published_lr','prior_matched_random']
    circuits=[]
    for case in cases:
        for method in methods:
            row=rows[case,method,'sorted']
            source=EXPERIMENT/row['circuit_file']
            if digest(source)!=row['circuit_sha256']:
                raise ValueError('Source circuit changed')
            with source.open('rb') as stream:
                circuit,=qpy.load(stream)
            exact=float(Statevector.from_instruction(circuit).probabilities() @ bks_indicator(row['scorer']))
            if abs(exact-row['exact_metrics']['bks_rate'])>1e-9:
                raise ValueError('Logical circuit preflight failed')
            circuit.measure_all()
            name=f'{case}__{method}'
            qpy_path=out/(name+'.qpy')
            with qpy_path.open('wb') as stream:
                qpy.dump(circuit,stream)
            (out/(name+'.qasm')).write_text(qasm3.dumps(circuit),encoding='utf-8')
            circuits.append(dict(case=case,method=method,qubits=circuit.num_qubits,
                file=qpy_path.name,sha256=digest(qpy_path),scorer=row['scorer'],
                exact_bks=row['exact_metrics']['bks_rate'],source_sha256=row['circuit_sha256'],
                bit_convention='Integer bit i is logical qubit i, classical register meas; transpile WITH measurements'))
    rng=random.Random(20260909)
    tasks=[]
    for block in range(4):
        order=cases.copy()
        rng.shuffle(order)
        for case in order:
            arms=methods.copy()
            rng.shuffle(arms)
            for method in arms:
                tasks.append(dict(block=block,case=case,method=method,shots=2500,
                    circuit=f'{case}__{method}.qpy'))
    payload=dict(status='prepared_not_submitted',provider='Amazon Braket',backend=None,
        local_exact_preflight_passed=True,
        approved_max_cost=None,submission_enabled=False,shots_total=60000,
        circuits=circuits,planned_tasks=tasks,
        warning='Logical circuits only; requires device ISA transpilation, calibration, budget approval and a new frozen manifest')
    (out/'manifest.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8')
    print('Prepared six logical measured circuits, 24 planned executions, 60000 shots; no cloud calls.')


if __name__=='__main__':
    main()
