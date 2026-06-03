"""Приклад 2 — від'ємний цикл ``X → Y → Z → X`` (усі ребра = −1).

Демонструє, чому Флойд–Воршал **не може** обробити граф із від'ємним циклом:
вага шляху падає необмежено (``−3, −6, −9, … → −∞``), тож найкоротшого шляху
не існує. Ознака проблеми — від'ємні значення на діагоналі матриці.

Зберігає два рисунки в ``docs/images/``: сам цикл і графік розбіжності ваги.

Запуск:  ``python examples/02_negative_cycle.py``
"""

# _common ПЕРШИМ: налаштовує Agg і sys.path до імпорту matplotlib.pyplot
from _common import print_saved_location, save_figure
from _graphs import XYZ

import matplotlib.pyplot as plt  # noqa: E402

from floyd_warshall.core import floyd_warshall_steps, has_negative_cycle  # noqa: E402
from floyd_warshall.style import AXIS_LINE, PATH_COLOR  # noqa: E402
from floyd_warshall.visualization import configure_style, draw_graph, format_value  # noqa: E402

# --- дані прикладу: цикл X → Y → Z → X (єдине джерело — examples/_graphs.py) --
EXAMPLE = XYZ


def main() -> None:
    configure_style()
    labels, graph_cycle, pos_cycle = EXAMPLE.labels, EXAMPLE.adjacency, EXAMPLE.positions

    # 1) увесь цикл підсвічуємо червоним (highlight_path = X → Y → Z → X)
    save_figure(draw_graph(graph_cycle, pos_cycle, labels, highlight_path=[0, 1, 2, 0],
                           title="Повністю від'ємний цикл X → Y → Z → X (сума ваг = −3)", curved=True),
                "negcycle_graph_xyz.png")

    # 2) наочно: вага шляху падає необмежено з кожним обходом циклу
    cycle_weight = -3
    loops = list(range(0, 11))
    weights = [cycle_weight * k for k in loops]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(loops, weights, "o-", color=PATH_COLOR, linewidth=2)
    ax.axhline(0, color=AXIS_LINE, linewidth=0.8)
    ax.set_xlabel("Кількість обходів циклу  k")
    ax.set_ylabel("Накопичена вага шляху")
    ax.set_title("Вага шляху з k обходами циклу X → Y → Z → X  (вага циклу = −3)")
    ax.annotate("→ −∞\n(мінімуму не існує)", xy=(10, weights[-1]), xytext=(5.2, weights[-1] + 7),
                fontsize=11, color=PATH_COLOR, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=PATH_COLOR, lw=1.6))
    ax.grid(alpha=0.3)
    fig.tight_layout()
    save_figure(fig, "negcycle_weight_divergence.png")

    # 3) що видає сам алгоритм: дивимось на діагональ
    dist_c, _, _ = floyd_warshall_steps(graph_cycle)
    print("Діагональ матриці D після Флойда–Воршала (вершини X, Y, Z):",
          [format_value(dist_c[i][i]) for i in range(len(labels))])
    print("Є вершина з D[i][i] < 0  →  виявлено від'ємний цикл:", has_negative_cycle(dist_c))
    print("\nЧисла поза діагоналлю алгоритм теж повертає скінченними, але вони НЕ є")
    print("справжніми найкоротшими відстанями — насправді для цих пар відповідь −∞.")

    print_saved_location()


if __name__ == "__main__":
    main()
