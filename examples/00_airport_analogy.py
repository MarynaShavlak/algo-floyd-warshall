"""Приклад 0 — ілюстрації до аналогії з аеропортами (розділ «Інтуїція» README).

Генерує три рисунки, що пояснюють ідею алгоритму «на пальцях», ще до матриць:

1. ``airport_relaxation.png``    — прямий рейс проти пересадки (суть релаксації);
2. ``airport_progressive.png``   — як відкриття хабів по черзі вкорочує маршрут;
3. ``airport_map_abcdef.png``    — граф ``A–F`` як карта аеропортів.

Запуск:  ``python examples/00_airport_analogy.py``
"""

# _common ПЕРШИМ: налаштовує Agg і sys.path до імпорту matplotlib.pyplot
from _common import print_saved_location, save_figure
from _graphs import ABCDEF

from floyd_warshall.visualization import (  # noqa: E402
    configure_style,
    draw_airport_progressive,
    draw_airport_relaxation,
    draw_graph,
)

# Граф A–F тут виступає як «карта аеропортів» (дані — в examples/_graphs.py).


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
