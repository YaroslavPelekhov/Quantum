# Зачем проекту узел 8×H200

Полный узел не нужен для первого прототипа. Рациональный режим:

- 1 GPU: разработка, unit tests, малые state-vector simulations;
- 2–4 GPU: параллельная оценка популяции и noisy sweeps;
- 8 GPU: scaling experiment, batched candidate evaluation, multi-GPU circuit simulation и крупные held-out sweeps.

Лучшее использование 8 GPU — независимые evaluation workers, а не распределение каждого маленького circuit на весь узел.

План измерения:
1. throughput candidates/hour на 1/2/4/8 GPU;
2. strong- и weak-scaling;
3. VRAM и communication overhead;
4. cost per promoted operator;
5. simulator-to-QPU transfer для финального shortlist.
