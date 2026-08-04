# Как применить каждую работу к quantum × evolutionary computing

## 1. AlphaEvolve_TSP — прямое ядро проекта

### Что уже есть
- эволюция полного исполняемого solver-кода;
- внешний evaluator с таймаутами, проверкой корректности и точным oracle на малых задачах;
- multi-objective постановка через quality/runtime и UB/LB;
- архив кандидатов и LLM-generated code modifications.

### Перенос
Заменить `solve_tsp(coords)` на интерфейс вроде:

```python
def build_quantum_policy(instance, hardware, budget):
    return {
        "encoding": ...,
        "preprocess": ...,
        "mixer": ...,
        "depth": ...,
        "parameter_schedule": ...,
        "transpilation": ...,
        "classical_repair": ...,
    }
```

Evaluator должен запускать политику на train QOBLIB instances сначала через noiseless simulator, затем noise model, и возвращать quality gap, feasibility, two-qubit gates, depth, shots и runtime. Лучшие кандидаты проверяются через Metriq-Gym на QPU.

### Самые полезные файлы
- `code/AlphaEvolve_TSP/evaluator.py` — шаблон внешнего исполняемого evaluator;
- `code/AlphaEvolve_TSP/config.yaml` — структура задания LLM и жёсткого output contract.

## 2. RG-HLI / Long_Horizon_Research — главная методологическая новизна

### Что уже есть
- единый typed hypothesis state;
- residual classes вместо свободного textual feedback;
- executable operators;
- complexity-aware held-out promotion;
- замороженный язык на финальной оценке.

### Перенос
Определить quantum residual taxonomy:

- `infeasible_sample`;
- `encoding_violation`;
- `mixer_breaks_constraint`;
- `depth_budget_exceeded`;
- `transpilation_blowup`;
- `shot_instability`;
- `simulator_hardware_gap`;
- `size_transfer_failure`.

Повторяющийся residual индуцирует оператор: warm-start rule, graph decomposition, constraint-preserving mixer, parameter interpolation, qubit routing rule или post-processing repair. Оператор принимается только при улучшении на disjoint QOBLIB instances после штрафа за сложность.

### Самые полезные файлы
- `operator_genome.py` — представление операторов;
- `self_induced_language.py` — рост языка;
- `universal_hypothesis_kernel.py` — общий typed kernel;
- `run_language_growth_experiment.py` — экспериментальный протокол.

## 3. TherapyBench / RAVR-S — verifier и proof objects

### Что переносится
Не клиническое содержание, а инженерная схема:

- набор типизированных обязательных predicates;
- machine-readable proof object;
- state-sensitive candidate selection;
- repair, conditioned on the exact violated predicate;
- trajectory-level evaluation.

### Quantum-версия
Proof object для каждого solver run может содержать:

```json
{
  "feasible": true,
  "encoding_valid": true,
  "hardware_compatible": true,
  "budget": {"depth": 82, "two_qubit_gates": 194, "shots": 2048},
  "violations": [],
  "objective": 0.91,
  "confidence": 0.87
}
```

State-sensitive selection становится hardware-state-sensitive selection: учитывать calibration snapshot, queue/budget, connectivity, observed noise and remaining evaluation budget.

## 4. FlowDraft — дешёвое предложение кандидатов и HPC

### Что переносится
- learned draft head / candidate generation;
- verifier-aligned selection;
- residual flow and candidate support;
- строгий benchmark protocol;
- training/evaluation на одном 8×H200 node как образец HPC-пайплайна.

### Quantum-версия
Можно обучить surrogate/draft model предлагать:
- promising QAOA schedules;
- mixer families;
- subproblem decompositions;
- top-k circuit edits.

Дорогой simulator/QPU становится verifier, а learned draft stage сокращает число полноценных circuit evaluations.

## 5. SMILES — surrogate evaluator

### Что переносится
Проект извлекает внутренние представления и обучает дешёвый probe для ранней классификации. В quantum search это можно использовать как surrogate ranker, предсказывающий, какие программы:
- вероятно не пройдут feasibility;
- дадут transpilation blow-up;
- будут unstable under shots/noise;
- заслуживают дорогого noisy/QPU evaluation.

Probe нельзя использовать как финальный источник истины: он только фильтрует кандидатов, после чего решения проходят executable verification.

## 6. Holosophos — orchestration layer

Роли можно заменить на:
- **Proposer:** генерирует solver/circuit edits;
- **Verifier:** запускает симуляторы и QOBLIB checker;
- **Hardware critic:** оценивает connectivity, depth и calibration sensitivity;
- **Evolution manager:** ведёт population/archive;
- **Reproducibility agent:** формирует Metriq-Gym jobs и experiment manifests.

## Рекомендуемый первый эксперимент

**MIS on QOBLIB, QAOA/hybrid policies, 12–24 quantum variables.**

1. Small exact/noiseless stage на локальной GPU.
2. Noisy stage для top 10% кандидатов.
3. Held-out split по graph family и size.
4. Сравнение с fixed QAOA, warm-start QAOA, XY-mixer baseline, random evolution и LLM-only repair.
5. Финальная проверка 5–10 policies через Metriq-Gym/QPU.

Главный paper claim должен быть о переносе и верифицированном росте solver language, а не просто о подборе QAOA-углов.
