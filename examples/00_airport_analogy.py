"""Приклад 0 — ілюстрації до аналогії з аеропортами (розділ «Інтуїція» README).

Генерує три рисунки, що пояснюють ідею алгоритму «на пальцях», ще до матриць:

1. ``airport_relaxation.png``    — прямий рейс проти пересадки (суть релаксації);
2. ``airport_progressive.png``   — як відкриття хабів по черзі вкорочує маршрут;
3. ``airport_map_abcdef.png``    — граф ``A–F`` як карта аеропортів.

Запуск:  ``python examples/00_airport_analogy.py``
"""

# _common ПЕРШИМ: налаштовує Agg і sys.path до імпорту matplotlib.pyplot
from _common import GraphExample, print_saved_location, save_figure

from floyd_warshall.visualization import (  # noqa: E402
    configure_style,
    draw_airport_progressive,
    draw_airport_relaxation,
    draw_graph,
)

# Той самий граф A–F, що й у прикладі 1 (тут — як «карта аеропортів»).
ABCDEF = GraphExample(
    labels=["A", "B", "C", "D", "E", "F"],
    adjacency=[
        [0, 3, 0, 0, 0, 0],   # A → B (3)
        [0, 0, 1, 0, 0, 0],   # B → C (1)
        [0, 0, 0, 7, 0, 2],   # C → D (7), C → F (2)
        [0, 0, 0, 0, 0, 0],   # D — стік
        [0, 0, 0, 2, 0, 3],   # E → D (2), E → F (3)
        [0, 0, 0, 0, 0, 0],   # F — стік
    ],
    positions={0: (3.4, 2.6), 1: (3.0, 1.7), 2: (2.0, 1.7),
               3: (2.1, 0.0), 4: (0.9, 1.7), 5: (0.4, 2.7)},
)


def main() -> None:
    configure_style()

    # 1) прямий рейс vs пересадка через хаб k
    save_figure(draw_airport_relaxation(), "airport_relaxation.png")

    # 2) хаби відкриваються по черзі
    save_figure(draw_airport_progressive(), "airport_progressive.png")

    # 3) граф A–F як карта аеропортів
    save_figure(
        draw_graph(ABCDEF.adjacency, ABCDEF.positions, ABCDEF.labels,
                   title="Карта аеропортів: вершини = аеропорти, ребра = прямі рейси (тривалість)",
                   figsize=(7, 5)),
        "airport_map_abcdef.png",
    )

    print("Збережено 3 рисунки аналогії з аеропортами.")
    print_saved_location()


if __name__ == "__main__":
    main()
