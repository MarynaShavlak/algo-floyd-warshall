"""Спільні утиліти для прикладів (``examples/``).

Раніше кожен приклад повторював той самий boilerplate: перемикання matplotlib
на ``Agg``, додавання кореня репозиторію в ``sys.path``, обчислення шляху до
``docs/images`` та однаковісінькі функції збереження фігур і друку шляхів.
Тут це зведено в одне місце.

Імпортуйте цей модуль ПЕРШИМ у прикладі — він налаштовує ``Agg`` до того, як
буде імпортовано ``matplotlib.pyplot``.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Sequence, Tuple

import matplotlib

matplotlib.use("Agg")  # зберігаємо у файли без графічного дисплея

# корінь репозиторію в sys.path — дозволяє запуск без `pip install -e .`
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from floyd_warshall.core import reconstruct_path  # noqa: E402
from floyd_warshall.style import FIGURE_DPI  # noqa: E402
from floyd_warshall.visualization import print_distance_matrix  # noqa: E402

#: Тека, куди приклади зберігають усі рисунки.
IMG_DIR = os.path.join(_ROOT, "docs", "images")
os.makedirs(IMG_DIR, exist_ok=True)


@dataclass(frozen=True)
class GraphExample:
    """Дані одного прикладу: підписи вершин, матриця суміжності та координати.

    :param labels: підписи вершин (за індексами ``0..n-1``).
    :param adjacency: матриця суміжності (``0 == немає ребра``).
    :param positions: координати вершин ``{індекс: (x, y)}`` для малювання графа.
    """

    labels: Sequence[str]
    adjacency: List[List[float]]
    positions: Dict[int, Tuple[float, float]] = field(default_factory=dict)


def save_figure(fig, name: str) -> None:
    """Зберігає фігуру у :data:`IMG_DIR` під іменем ``name``."""
    fig.savefig(os.path.join(IMG_DIR, name), bbox_inches="tight", dpi=FIGURE_DPI)


def report_distances(
    final_dist: List[List[float]],
    nxt: List[List[object]],
    labels: Sequence[str],
    pairs: Iterable[Tuple[int, int]],
) -> None:
    """Друкує підсумкову матрицю відстаней і найкоротші шляхи для заданих пар.

    :param pairs: ітерабельне з пар ``(u, v)`` — для яких відновити й надрукувати шлях.
    """
    print("\nФінальна матриця найкоротших відстаней (рядок = звідки, стовпець = куди):")
    print_distance_matrix(final_dist, labels)
    print()
    for u, v in pairs:
        path = reconstruct_path(nxt, u, v)
        if path is None:
            print(f"Найкоротший шлях {labels[u]} → {labels[v]}:  шляху не існує")
            continue
        joined = " → ".join(labels[w] for w in path)
        print(f"Найкоротший шлях {labels[u]} → {labels[v]}:  {joined}   (довжина = {final_dist[u][v]:g})")


def print_saved_location() -> None:
    """Друкує підсумкове повідомлення про теку зі збереженими рисунками."""
    print(f"\nРисунки збережено у: {IMG_DIR}")
