"""Приклад 5 — покрокова візуалізація «код ↔ матриця».

Кожен крок = рядок із двох панелей: ліворуч код алгоритму з **підсвіченими
активними рядками** (колір показує, яка гілка ``if`` спрацювала), праворуч —
**стан матриці D** саме на цьому кроці. Логіку див. у
``floyd_warshall/walkthrough.py`` та ``step-by-step-panels-playbook.md``.

Для кожного навчального графа (A–F, P–S, X–Y–Z) генеруємо два рівні:

* **огляд** (``code_steps_*.png``) — один крок на проміжну вершину ``k``;
* **по клітинках** для найпоказовішого ``k`` — статична кураторська сітка
  (``code_walk_*_k_*.png``) і повна анімація скану пар ``(i, j)``
  (``code_walk_*_k_*.gif`` + ``.mp4``).

Запуск:  ``python examples/05_code_walkthrough.py``      (українською → docs/images/)
         ``python examples/05_code_walkthrough.py en``   (англійською → docs/images/en/)
"""

# _common ПЕРШИМ: налаштовує Agg, sys.path і мову до імпорту matplotlib.pyplot
from _common import GraphExample, print_saved_location, save_anim, save_figure
from _graphs import ABCDEF, PQRS, XYZ

import matplotlib.pyplot as plt  # noqa: E402

from floyd_warshall.i18n import t  # noqa: E402
from floyd_warshall.visualization import configure_style  # noqa: E402
from floyd_warshall.walkthrough import (  # noqa: E402
    best_focus_k,
    build_cell_steps,
    build_overview_steps,
    draw_code_walkthrough_grid,
    pick_illustrative,
    render_code_step,
)

# Тривалість кадру анімації за типом кроку (мс): покращення «тримаємо» довше,
# структурні пропуски — швидко прогортуємо.
_DUR = {"k": 1500, "skip": 240, "nochange": 480, "improve": 1700, "final": 2800}


def make_overview(example: GraphExample, name: str) -> None:
    """Статична сітка огляду: рядок = [код | матриця D] на кожну вершину ``k``."""
    labels = example.labels
    steps = build_overview_steps(example.adjacency, labels)
    fig = draw_code_walkthrough_grid(
        steps, labels, t("Код ↔ матриця D: огляд по проміжних вершинах k"))
    save_figure(fig, name + ".png")
    plt.close(fig)
    print(t("  {name}: огляд, {n} кроків").format(name=name, n=len(steps)))


def make_cell(example: GraphExample, name: str, focus_k=None,
              *, figsize=(10.5, 3.9)) -> None:
    """Детальний розбір одного ``k`` по клітинках: статична сітка + анімація."""
    labels = example.labels
    k = best_focus_k(example.adjacency) if focus_k is None else focus_k
    kn = labels[k]
    steps = build_cell_steps(example.adjacency, k, labels)

    # 1) статична кураторська сітка (читома: контекст + пропуск + без змін + усі покращення + підсумок)
    grid = draw_code_walkthrough_grid(
        pick_illustrative(steps), labels,
        t("Код ↔ матриця D по клітинках (i, j) для k = {k}").format(k=kn))
    save_figure(grid, "{name}_k_{k}.png".format(name=name, k=kn))
    plt.close(grid)

    # 2) повна анімація скану всіх пар (i, j)
    figures = [render_code_step(s, labels, figsize=figsize) for s in steps]
    durations = [_DUR.get(s["kind"], 600) for s in steps]
    save_anim(figures, "{name}_k_{k}".format(name=name, k=kn), durations)
    print(t("  {name}: по клітинках, {n} кадрів (k = {k})").format(
        name=name, n=len(figures), k=kn))


def main() -> None:
    configure_style()
    print(t("Генерую покрокові панелі «код ↔ матриця»…"))

    # імена — БЕЗ розширення (save_figure додає .png; save_anim — .gif/.mp4)
    # огляд по k — для всіх трьох графів
    make_overview(ABCDEF, "code_steps_abcdef")
    make_overview(PQRS, "code_steps_pqrs")
    make_overview(XYZ, "code_steps_xyz")

    # детально по клітинках — найпоказовіший k кожного графа добираємо автоматично
    make_cell(ABCDEF, "code_walk_abcdef")
    make_cell(PQRS, "code_walk_pqrs")
    make_cell(XYZ, "code_walk_xyz")

    print_saved_location()


if __name__ == "__main__":
    main()
