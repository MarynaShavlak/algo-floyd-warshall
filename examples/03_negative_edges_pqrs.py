"""Приклад 3 — граф ``P, Q, R, S`` із від'ємним ребром ``Q → R = −2``.

Показує, що Флойд–Воршал **коректно** працює з від'ємними вагами (якщо немає
від'ємного циклу), на відміну від Дейкстри. Ключовий момент: пряме ребро
``P → S = 10`` програє довшому шляху ``P → Q → R → S`` завдовжки 5, бо той
використовує від'ємне ребро.

Зберігає всі рисунки розділу в ``docs/images/``.

Запуск:  ``python examples/03_negative_edges_pqrs.py``
"""

import os
import sys

import matplotlib

matplotlib.use("Agg")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from floyd_warshall.core import (  # noqa: E402
    floyd_warshall_steps,
    has_negative_cycle,
    reconstruct_path,
)
from floyd_warshall.visualization import (  # noqa: E402
    configure_style,
    draw_evolution,
    draw_graph,
    draw_matrix_standalone,
    print_distance_matrix,
    show_step,
)

IMG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs", "images"))
os.makedirs(IMG_DIR, exist_ok=True)


def save(fig, name: str) -> None:
    fig.savefig(os.path.join(IMG_DIR, name), bbox_inches="tight", dpi=110)


# --- дані прикладу -----------------------------------------------------------
LABELS = ["P", "Q", "R", "S"]
graph_neg = [
    [0, 4, 0, 10],   # P → Q (4),  P → S (10)
    [0, 0, -2, 0],   # Q → R (-2)   ← від'ємне ребро
    [0, 0, 0, 3],    # R → S (3)
    [0, 0, 0, 0],    # S — без вихідних ребер
]
pos_neg = {0: (0.3, 1.0), 1: (1.5, 1.9), 2: (2.9, 1.9), 3: (4.1, 1.0)}  # P, Q, R, S


def main() -> None:
    configure_style()

    final_dist, nxt, snapshots = floyd_warshall_steps(graph_neg)

    # 1) граф із від'ємним ребром
    save(draw_graph(graph_neg, pos_neg, LABELS, title="Граф із від'ємним ребром (Q → R = −2)", curved=True),
         "graph_pqrs.png")

    # 2) початкова матриця
    save(draw_matrix_standalone(snapshots[0]["matrix"], LABELS, title="Початкова матриця D"),
         "matrix_initial_pqrs.png")

    # 3) детальний кадр після кожної проміжної вершини k = P..S
    for snap in snapshots[1:]:
        fig = show_step(snap, LABELS)
        save(fig, f"step_pqrs_k_{LABELS[snap['k']]}.png")

    # 4) зведена сітка еволюції
    save(draw_evolution(snapshots, LABELS,
                        "Еволюція матриці відстаней D (відкриваємо вершини P → S)", ncols=3),
         "evolution_pqrs.png")

    # 5) підсумкова матриця + відновлення шляхів (текст)
    print("\nФінальна матриця найкоротших відстаней (рядок = звідки, стовпець = куди):")
    print_distance_matrix(final_dist, LABELS)
    print()
    for (u, v) in [(0, 2), (0, 3), (1, 3)]:  # P→R, P→S, Q→S
        path = reconstruct_path(nxt, u, v)
        joined = " → ".join(LABELS[w] for w in path)
        print(f"Найкоротший шлях {LABELS[u]} → {LABELS[v]}:  {joined}   (довжина = {final_dist[u][v]:g})")

    # 6) підсвічений найкоротший шлях P → S (іде через від'ємне ребро)
    path_p_s = reconstruct_path(nxt, 0, 3)
    title = "Найкоротший шлях P → S: " + " → ".join(LABELS[w] for w in path_p_s) + "  (довжина 5)"
    save(draw_graph(graph_neg, pos_neg, LABELS, highlight_path=path_p_s, title=title, curved=True),
         "path_pqrs_P_to_S.png")

    # 7) підсумкова матриця (окремо) + перевірка від'ємного циклу
    save(draw_matrix_standalone(final_dist, LABELS, title="Підсумкова матриця найкоротших відстаней"),
         "matrix_final_pqrs.png")
    assert not has_negative_cycle(final_dist), "Виявлено від'ємний цикл!"
    print("\nВід'ємних циклів немає, матрицю обчислено коректно \u2714")

    print(f"\nРисунки збережено у: {IMG_DIR}")


if __name__ == "__main__":
    main()
