"""Приклад 3 — граф ``P, Q, R, S`` із від'ємним ребром ``Q → R = −2``.

Показує, що Флойд–Воршал **коректно** працює з від'ємними вагами (якщо немає
від'ємного циклу), на відміну від Дейкстри. Ключовий момент: пряме ребро
``P → S = 10`` програє довшому шляху ``P → Q → R → S`` завдовжки 5, бо той
використовує від'ємне ребро.

Зберігає всі рисунки розділу в ``docs/images/``.

Запуск:  ``python examples/03_negative_edges_pqrs.py``
"""

# _common ПЕРШИМ: налаштовує Agg і sys.path до імпорту matplotlib.pyplot
from _common import print_saved_location, report_distances, save_figure
from _graphs import PQRS

from floyd_warshall.core import (  # noqa: E402
    floyd_warshall_steps,
    has_negative_cycle,
    reconstruct_path,
)
from floyd_warshall.i18n import t  # noqa: E402
from floyd_warshall.visualization import (  # noqa: E402
    configure_style,
    draw_evolution,
    draw_graph,
    draw_matrix_standalone,
    show_step,
)

# --- дані прикладу: граф P–Q–R–S (єдине джерело — examples/_graphs.py) -------
EXAMPLE = PQRS


def main() -> None:
    configure_style()
    labels, graph_neg, pos_neg = EXAMPLE.labels, EXAMPLE.adjacency, EXAMPLE.positions

    final_dist, nxt, snapshots = floyd_warshall_steps(graph_neg)

    # 1) граф із від'ємним ребром
    save_figure(draw_graph(graph_neg, pos_neg, labels,
                           title=t("Граф із від'ємним ребром (Q → R = −2)"), curved=True),
                "graph_pqrs.png")

    # 2) початкова матриця
    save_figure(draw_matrix_standalone(snapshots[0]["matrix"], labels, title=t("Початкова матриця D")),
                "matrix_initial_pqrs.png")

    # 3) детальний кадр після кожної проміжної вершини k = P..S
    for snap in snapshots[1:]:
        fig = show_step(snap, labels)
        save_figure(fig, f"step_pqrs_k_{labels[snap['k']]}.png")

    # 4) зведена сітка еволюції
    save_figure(draw_evolution(snapshots, labels,
                               t("Еволюція матриці відстаней D (відкриваємо вершини P → S)"), ncols=3),
                "evolution_pqrs.png")

    # 5) підсумкова матриця + відновлення шляхів (текст): P→R, P→S, Q→S
    report_distances(final_dist, nxt, labels, [(0, 2), (0, 3), (1, 3)])

    # 6) підсвічений найкоротший шлях P → S (іде через від'ємне ребро)
    path_p_s = reconstruct_path(nxt, 0, 3)
    title = t("Найкоротший шлях P → S: {path}  (довжина 5)").format(
        path=" → ".join(labels[w] for w in path_p_s))
    save_figure(draw_graph(graph_neg, pos_neg, labels, highlight_path=path_p_s, title=title, curved=True),
                "path_pqrs_P_to_S.png")

    # 7) підсумкова матриця (окремо) + перевірка від'ємного циклу
    save_figure(draw_matrix_standalone(final_dist, labels, title=t("Підсумкова матриця найкоротших відстаней")),
                "matrix_final_pqrs.png")
    assert not has_negative_cycle(final_dist), "Виявлено від'ємний цикл!"
    print(t("\nВід'ємних циклів немає, матрицю обчислено коректно ✔"))

    print_saved_location()


if __name__ == "__main__":
    main()
