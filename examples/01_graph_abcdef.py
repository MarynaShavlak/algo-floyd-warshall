"""Приклад 1 — основний граф ``A–F`` (орієнтований, лише додатні ваги).

Відтворює весь покроковий розбір із README: базовий граф, початкову матрицю,
детальний кадр після кожної проміжної вершини ``k = A … F``, зведену сітку
еволюції та підсвічений найкоротший шлях ``A → D``. Усі рисунки зберігаються
в ``docs/images/``.

Запуск:  ``python examples/01_graph_abcdef.py``
"""

# _common ПЕРШИМ: налаштовує Agg і sys.path до імпорту matplotlib.pyplot
from _common import print_saved_location, report_distances, save_figure
from _graphs import ABCDEF

import matplotlib.pyplot as plt  # noqa: E402

from floyd_warshall.core import floyd_warshall_steps, reconstruct_path  # noqa: E402
from floyd_warshall.visualization import (  # noqa: E402
    configure_style,
    draw_evolution,
    draw_graph,
    draw_matrix,
    show_step,
)

# --- дані прикладу: граф A–F (єдине джерело — examples/_graphs.py) -----------
EXAMPLE = ABCDEF


def main() -> None:
    configure_style()
    labels, graph, pos = EXAMPLE.labels, EXAMPLE.adjacency, EXAMPLE.positions

    # 1) сам граф
    save_figure(draw_graph(graph, pos, labels, title="Орієнтований зважений граф", figsize=(7, 5)),
                "graph_abcdef.png")

    # 2) алгоритм зі знімками + матриця наступних вершин
    final_dist, nxt, snapshots = floyd_warshall_steps(graph)
    print("Готово: зібрано", len(snapshots), "знімків (початковий + по одному на кожну вершину).")

    # 3) початкова матриця (компактний стиль на власній фігурі)
    fig, ax = plt.subplots(figsize=(5.2, 5.2))
    draw_matrix(ax, snapshots[0]["matrix"], labels, "Початкова матриця D  (жодної проміжної вершини)")
    fig.tight_layout()
    save_figure(fig, "matrix_initial_abcdef.png")

    # 4) детальний кадр після кожної проміжної вершини k = A..F
    for snap in snapshots[1:]:
        fig = show_step(snap, labels)
        save_figure(fig, f"step_abcdef_k_{labels[snap['k']]}.png")

    # 5) зведена сітка еволюції
    save_figure(draw_evolution(snapshots, labels,
                               "Еволюція матриці відстаней D (відкриваємо вершини A → F)", ncols=4),
                "evolution_abcdef.png")

    # 6) підсумкова матриця + відновлення шляхів (текст): A→D, A→F, A→C
    report_distances(final_dist, nxt, labels, [(0, 3), (0, 5), (0, 2)])

    # 7) підсвічений найкоротший шлях A → D на графі
    path_a_d = reconstruct_path(nxt, 0, 3)
    title = "Найкоротший шлях A → D: " + " → ".join(labels[v] for v in path_a_d) + "  (довжина 11)"
    save_figure(draw_graph(graph, pos, labels, highlight_path=path_a_d, title=title, figsize=(7, 5)),
                "path_abcdef_A_to_D.png")

    print_saved_location()


if __name__ == "__main__":
    main()
