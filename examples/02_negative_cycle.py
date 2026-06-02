"""Приклад 2 — від'ємний цикл ``X → Y → Z → X`` (усі ребра = −1).

Демонструє, чому Флойд–Воршал **не може** обробити граф із від'ємним циклом:
вага шляху падає необмежено (``−3, −6, −9, … → −∞``), тож найкоротшого шляху
не існує. Ознака проблеми — від'ємні значення на діагоналі матриці.

Зберігає два рисунки в ``docs/images/``: сам цикл і графік розбіжності ваги.

Запуск:  ``python examples/02_negative_cycle.py``
"""

import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from floyd_warshall.core import floyd_warshall_steps, has_negative_cycle  # noqa: E402
from floyd_warshall.visualization import configure_style, draw_graph, _fmt  # noqa: E402

IMG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs", "images"))
os.makedirs(IMG_DIR, exist_ok=True)


def save(fig, name: str) -> None:
    fig.savefig(os.path.join(IMG_DIR, name), bbox_inches="tight", dpi=110)


# --- дані прикладу: цикл X → Y → Z → X, кожне ребро = −1 (сума = −3) ----------
LABELS = ["X", "Y", "Z"]
graph_cycle = [
    [0, -1, 0],   # X → Y (-1)
    [0, 0, -1],   # Y → Z (-1)
    [-1, 0, 0],   # Z → X (-1)
]
pos_cycle = {0: (1.5, 2.2), 1: (2.7, 0.4), 2: (0.3, 0.4)}  # X угорі, Y і Z знизу


def main() -> None:
    configure_style()

    # 1) увесь цикл підсвічуємо червоним (highlight_path = X → Y → Z → X)
    save(draw_graph(graph_cycle, pos_cycle, LABELS, highlight_path=[0, 1, 2, 0],
                    title="Повністю від'ємний цикл X → Y → Z → X (сума ваг = −3)", curved=True),
         "negcycle_graph_xyz.png")

    # 2) наочно: вага шляху падає необмежено з кожним обходом циклу
    cycle_weight = -3
    loops = list(range(0, 11))
    weights = [cycle_weight * k for k in loops]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(loops, weights, "o-", color="#D32F2F", linewidth=2)
    ax.axhline(0, color="#999", linewidth=0.8)
    ax.set_xlabel("Кількість обходів циклу  k")
    ax.set_ylabel("Накопичена вага шляху")
    ax.set_title("Вага шляху з k обходами циклу X → Y → Z → X  (вага циклу = −3)")
    ax.annotate("→ −∞\n(мінімуму не існує)", xy=(10, weights[-1]), xytext=(5.2, weights[-1] + 7),
                fontsize=11, color="#D32F2F", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color="#D32F2F", lw=1.6))
    ax.grid(alpha=0.3)
    fig.tight_layout()
    save(fig, "negcycle_weight_divergence.png")

    # 3) що видає сам алгоритм: дивимось на діагональ
    dist_c, _, _ = floyd_warshall_steps(graph_cycle)
    print("Діагональ матриці D після Флойда–Воршала (вершини X, Y, Z):",
          [_fmt(dist_c[i][i]) for i in range(len(LABELS))])
    print("Є вершина з D[i][i] < 0  →  виявлено від'ємний цикл:", has_negative_cycle(dist_c))
    print("\nЧисла поза діагоналлю алгоритм теж повертає скінченними, але вони НЕ є")
    print("справжніми найкоротшими відстанями — насправді для цих пар відповідь −∞.")

    print(f"\nРисунки збережено у: {IMG_DIR}")


if __name__ == "__main__":
    main()
