"""Приклад 1 — основний граф ``A–F`` (орієнтований, лише додатні ваги).

Відтворює весь покроковий розбір із README: базовий граф, початкову матрицю,
детальний кадр після кожної проміжної вершини ``k = A … F``, зведену сітку
еволюції та підсвічений найкоротший шлях ``A → D``. Усі рисунки зберігаються
в ``docs/images/``.

Запуск:  ``python examples/01_graph_abcdef.py``
"""

import os
import sys

import matplotlib

matplotlib.use("Agg")  # зберігаємо у файли без графічного дисплея

# дозволяємо запуск без встановлення пакета (`pip install -e .`)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from floyd_warshall.core import floyd_warshall_steps, reconstruct_path
import matplotlib.pyplot as plt  # noqa: E402

from floyd_warshall.visualization import (
    configure_style,
    draw_evolution,
    draw_graph,
    draw_matrix,
    print_distance_matrix,
    show_step,
)

IMG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs", "images"))
os.makedirs(IMG_DIR, exist_ok=True)


def save(fig, name: str) -> None:
    fig.savefig(os.path.join(IMG_DIR, name), bbox_inches="tight", dpi=110)


# --- дані прикладу -----------------------------------------------------------
LABELS = ["A", "B", "C", "D", "E", "F"]  # вершини (внутрішньо — індекси 0..5)

# Матриця суміжності (0 = немає ребра). Рядок/стовпець 0..5 = вершини A..F.
graph = [
    [0, 3, 0, 0, 0, 0],   # A → B (3)
    [0, 0, 1, 0, 0, 0],   # B → C (1)
    [0, 0, 0, 7, 0, 2],   # C → D (7), C → F (2)
    [0, 0, 0, 0, 0, 0],   # D — стік
    [0, 0, 0, 2, 0, 3],   # E → D (2), E → F (3)
    [0, 0, 0, 0, 0, 0],   # F — стік
]

# координати вершин для гарного малюнка
pos = {
    0: (3.4, 2.6),   # A
    1: (3.0, 1.7),   # B
    2: (2.0, 1.7),   # C
    3: (2.1, 0.0),   # D
    4: (0.9, 1.7),   # E
    5: (0.4, 2.7),   # F
}


def main() -> None:
    configure_style()

    # 1) сам граф
    save(draw_graph(graph, pos, LABELS, title="Орієнтований зважений граф", figsize=(7, 5)),
         "graph_abcdef.png")

    # 2) алгоритм зі знімками + матриця наступних вершин
    final_dist, nxt, snapshots = floyd_warshall_steps(graph)
    print("Готово: зібрано", len(snapshots), "знімків (початковий + по одному на кожну вершину).")

    # 3) початкова матриця (компактний стиль на власній фігурі)
    fig, ax = plt.subplots(figsize=(5.2, 5.2))
    draw_matrix(ax, snapshots[0]["matrix"], LABELS, "Початкова матриця D  (жодної проміжної вершини)")
    fig.tight_layout()
    save(fig, "matrix_initial_abcdef.png")

    # 4) детальний кадр після кожної проміжної вершини k = A..F
    for snap in snapshots[1:]:
        fig = show_step(snap, LABELS)
        save(fig, f"step_abcdef_k_{LABELS[snap['k']]}.png")

    # 5) зведена сітка еволюції
    save(draw_evolution(snapshots, LABELS,
                        "Еволюція матриці відстаней D (відкриваємо вершини A → F)", ncols=4),
         "evolution_abcdef.png")

    # 6) підсумкова матриця + відновлення шляхів (текст)
    print("\nФінальна матриця найкоротших відстаней (рядок = звідки, стовпець = куди):")
    print_distance_matrix(final_dist, LABELS)
    print()
    for target in (3, 5, 2):  # A→D, A→F, A→C
        path = reconstruct_path(nxt, 0, target)
        joined = " → ".join(LABELS[v] for v in path)
        dist = final_dist[0][target]
        print(f"Найкоротший шлях A → {LABELS[target]}:  {joined}   (довжина = {dist:g})")

    # 7) підсвічений найкоротший шлях A → D на графі
    path_a_d = reconstruct_path(nxt, 0, 3)
    title = "Найкоротший шлях A → D: " + " → ".join(LABELS[v] for v in path_a_d) + "  (довжина 11)"
    save(draw_graph(graph, pos, LABELS, highlight_path=path_a_d, title=title, figsize=(7, 5)),
         "path_abcdef_A_to_D.png")

    print(f"\nРисунки збережено у: {IMG_DIR}")


if __name__ == "__main__":
    main()
