# Quantum × Evolutionary Computing — рабочий архив Ярослава Пелехова

Это не список ссылок: в папке `code/` лежат **реальные исходные файлы из публичных репозиториев**, а в `papers/` — исходный PDF статьи AAMAS 2026 про OpenEvolve и TSP.

## Что открыть первым

1. `papers/AAMAS_2026_Program_Evolution_TSP.pdf`
2. `code/AlphaEvolve_TSP/evaluator.py` и `config.yaml`
3. `code/Long_Horizon_Research/mars/induction/operator_genome.py`
4. `code/Long_Horizon_Research/mars/induction/self_induced_language.py`
5. `code/Long_Horizon_Research/mars/runners/run_language_growth_experiment.py`
6. `explanations/QUANTUM_APPLICATION_MAP_RU.md`
7. `code/quantum_adapter_template/example_run.py`

## Основная исследовательская линия

Переносится единый цикл:

`LLM/program proposer → executable candidate → verifier → typed residual → held-out promotion → reusable solver policy`.

В квантовой оптимизации кандидат — не только набор QAOA-углов, а исполняемая политика, выбирающая encoding, preprocessing, mixer, depth, initialization, transpilation и repair под instance, hardware и бюджет.

## Что является оригинальными файлами

Папки `AlphaEvolve_TSP`, `Long_Horizon_Research`, `FlowDraft`, `SMILES`, `TherapyBench` и `holosophos-multi-llm` содержат снимки файлов, скачанные из публичных GitHub-репозиториев пользователя 2 августа 2026 года. `quantum_adapter_template` — отдельный адаптационный каркас, созданный для переноса этих механизмов на QOBLIB/Metriq-Gym; он не выдаётся за исходный проект.
