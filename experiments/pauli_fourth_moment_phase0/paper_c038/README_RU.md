# Самостоятельная статья C038+C042

Эта папка содержит сфокусированную рукопись только об all-line-graph теореме.
Старые C031/SCF-конструкции намеренно не включены: они сохранены в полной
исторической рукописи `../paper`.

Главный результат:

`beta(L(R),w) = alpha(L(R),w) = nu(R,w)`

для любого конечного простого графа `R` и любых неотрицательных весов.

Центральный механизм теперь проверен отдельным C039-циклом: 6 225 взвешенных
случаев сравнивают degree-only, clique+odd-cycle и полный blossom baseline;
контролируемые семейства разделяют локальные odd-cycle и общие odd-set
ограничения; точный Householder-контрпример показывает необходимость
skew-symmetry. Итоговые таблицы и графики встроены в статью.

C040--C041 масштабируют проверку до случайных корней порядка 40,
контролируемых семейств порядка 132 и weak-coupling конструкций порядка 80.
Добавлены пять уровней baseline, четыре режима весов, density stress,
три графика, десять таблиц/графиков с хешами и независимые verifiers.

C042 добавляет доказанный мост за пределы line graphs: rank-perfect SCF
графы hbar-perfect, поэтому SCF semi-line класс покрыт целиком. Включён
строгий девятивершинный свидетель вне line и h-perfect классов, исчерпывающий
order-nine boundary audit и 60 больших stress-графов. Гипотеза про все SCF
quasi-line графы оставлена гипотезой, а не перенесена в теорему.

Перед публичной подачей автор самостоятельно заполняет имя, аффилиацию,
контакт, funding/conflict statements и точное раскрытие AI-помощи. Текущая
версия анонимна и не проходила внешнее рецензирование.

Проверка содержания:

```text
python experiments/pauli_fourth_moment_phase0/paper_c038/check_paper.py
python -S experiments/pauli_fourth_moment_phase0/verify_c039_central_ablations.py
python -m unittest discover -s experiments/pauli_fourth_moment_phase0 -p test_c039_central_ablations.py -v
python -S experiments/pauli_fourth_moment_phase0/verify_c040_scaled_ablations.py
python -S experiments/pauli_fourth_moment_phase0/verify_c041_density_coupling_stress.py
```

Воспроизводимая сборка без зависимости от Perl/latexmk:

```text
python experiments/pauli_fourth_moment_phase0/paper_c038/build.py
```

Скрипт выполняет два прохода `pdflatex`, отклоняет переполнения и неразрешённые
ссылки, запускает проверку содержания и записывает итоговый PDF в
`output/pdf/c038_line_graph_pauli_matching_theorem.pdf`.
