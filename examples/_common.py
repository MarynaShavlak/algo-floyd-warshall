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

from floyd_warshall.animation import save_animation as _save_animation  # noqa: E402
from floyd_warshall.core import reconstruct_path  # noqa: E402
from floyd_warshall.i18n import set_lang, t  # noqa: E402
from floyd_warshall.style import FIGURE_DPI  # noqa: E402
from floyd_warshall.visualization import print_distance_matrix  # noqa: E402

# --- вибір мови підписів із аргументів CLI ---------------------------------
# Передайте "en" аргументом (``python examples/01_graph_abcdef.py en``), щоб
# малювати англійською. Імпортуйте _common ПЕРШИМ: тут одразу перемикається мова
# t() і маршрут теки виводу, тож усі подальші виклики малювання знають мову.
LANG: str = "en" if "en" in sys.argv[1:] else "uk"
set_lang(LANG)

#: Тека, куди приклади зберігають усі рисунки (англійською → у підтеку ``en/``).
IMG_DIR = (
    os.path.join(_ROOT, "docs", "images", "en") if LANG == "en"
    else os.path.join(_ROOT, "docs", "images")
)
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


def save_anim(figures, basename: str, durations, **kwargs):
    """Зберігає анімацію у :data:`IMG_DIR`: GIF завжди + MP4 за наявності ffmpeg.

    :param figures: список фігур-кадрів (будуть закриті під час рендера).
    :param basename: ім'я файлу БЕЗ розширення — ``.gif`` і ``.mp4`` додаються самі.
    :param durations: тривалість кадру(ів) у мс (число або послідовність).
    :returns: шлях до MP4, якщо його записано, інакше ``None`` (GIF є завжди).
    """
    gif = os.path.join(IMG_DIR, basename + ".gif")
    mp4 = os.path.join(IMG_DIR, basename + ".mp4")
    return _save_animation(figures, gif, durations, mp4_path=mp4, **kwargs)


def report_distances(
    final_dist: List[List[float]],
    nxt: List[List[object]],
    labels: Sequence[str],
    pairs: Iterable[Tuple[int, int]],
) -> None:
    """Друкує підсумкову матрицю відстаней і найкоротші шляхи для заданих пар.

    :param pairs: ітерабельне з пар ``(u, v)`` — для яких відновити й надрукувати шлях.
    """
    print(t("\nФінальна матриця найкоротших відстаней (рядок = звідки, стовпець = куди):"))
    print_distance_matrix(final_dist, labels)
    print()
    for u, v in pairs:
        path = reconstruct_path(nxt, u, v)
        if path is None:
            print(t("Найкоротший шлях {a} → {b}:  шляху не існує").format(a=labels[u], b=labels[v]))
            continue
        joined = " → ".join(labels[w] for w in path)
        print(t("Найкоротший шлях {a} → {b}:  {path}   (довжина = {n:g})").format(
            a=labels[u], b=labels[v], path=joined, n=final_dist[u][v]))


def print_saved_location() -> None:
    """Друкує підсумкове повідомлення про теку зі збереженими рисунками."""
    print(t("\nРисунки збережено у: {path}").format(path=IMG_DIR))
