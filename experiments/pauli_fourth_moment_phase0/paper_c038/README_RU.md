# Самостоятельная статья C038+C043

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

C042 добавил мост за пределы line graphs: rank-perfect SCF графы
hbar-perfect. C043 закрывает оставшуюся границу аналитически: каждый SCF
quasi-line граф rank-perfect и поэтому hbar-perfect. Доказательство исключает
все nonrank clique-circulants; 4308 deletion-контролей, 6162 циркулянтных
параметра, полный перебор 18 149 клик малых циркулянтов, опубликованный
nonrank positive control и 250 exact-CFI stress
графов проходят независимую проверку.

C044 заменил краткий three-arc sketch полностью автономным sumset-доказательством
оценки для нелокальных клик. Дополнительно проверены все 38 772 удаления,
1 027 351 алгебраическая строка, 4 194 302 deficit-подмножества и
3 803 174 циркулянтные клики до порядка 30.

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
python -S experiments/pauli_fourth_moment_phase0/verify_c043_quasiline_scf_theorem.py
```

Воспроизводимая сборка без зависимости от Perl/latexmk:

```text
python experiments/pauli_fourth_moment_phase0/paper_c038/build.py
```

Скрипт выполняет два прохода `pdflatex`, отклоняет переполнения и неразрешённые
ссылки, запускает проверку содержания и записывает итоговый PDF в
`output/pdf/c038_line_graph_pauli_matching_theorem.pdf`.
