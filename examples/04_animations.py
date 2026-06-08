"""Приклад 4 — GIF-анімації (Tier 1–2) для README.

Показує АЛГОРИТМ У РУСІ там, де статичний кадр поступається. Статичні рисунки
(``.png``) генерують приклади 00–03; тут — лише анімації.

Tier 1 (інтуїція та результат):

1. ``evolution_abcdef.gif`` / ``evolution_pqrs.gif`` — матриця ``D`` «дозріває»
   крок за кроком, поки по черзі відкриваємо проміжні вершини (зелене
   «спалахує» рівно на тому кроці, де відстань покращилася);
2. ``path_abcdef_A_to_D.gif`` / ``path_pqrs_P_to_S.gif`` — маршрут розгортається
   ребро за ребром за матрицею ``nxt`` (саме так працює ``reconstruct_path``);
3. ``airport_progressive.gif`` — відкриваємо хаби по черзі, і маршрут ``i → j``
   коротшає (``∞ → 12 → 6``).

Tier 2 (механіка циклів і від'ємний цикл):

4. ``sweep_abcdef_k_C.gif`` — два внутрішні цикли перебирають усі пари
   ``(i, j)`` за фіксованого ``k = C`` (помаранчева рамка — поточна клітинка);
5. ``negcycle_walk_xyz.gif`` — обхід від'ємного циклу ``X → Y → Z → X`` з
   накопиченням ваги (``0, −1, −2, … нескінченно``);
6. ``negcycle_weight_divergence.gif`` — графік ваги ``−3, −6, −9, … → −∞``,
   точка за точкою.

Запуск:  ``python examples/04_animations.py``
"""

# _common ПЕРШИМ: налаштовує Agg і sys.path до імпорту matplotlib.pyplot
from copy import deepcopy

from _common import GraphExample, print_saved_location, save_anim
from _graphs import ABCDEF, PQRS, XYZ

import matplotlib.pyplot as plt  # noqa: E402

from floyd_warshall.core import floyd_warshall_steps, reconstruct_path  # noqa: E402
from floyd_warshall.i18n import t  # noqa: E402
from floyd_warshall.style import AXIS_LINE, GREEN_TXT, PATH_COLOR  # noqa: E402
from floyd_warshall.visualization import (  # noqa: E402
    configure_style,
    draw_airport_progressive_panel,
    draw_graph,
    draw_matrix,
    format_value,
)

# Графи ABCDEF / PQRS / XYZ беремо з examples/_graphs.py (єдине джерело правди).
# Збереження кадрів робить save_anim із _common: GIF завжди + MP4 за наявності
# ffmpeg, у теку поточної мови (docs/images або docs/images/en). Параметр name —
# базове ім'я файлу БЕЗ розширення.


def animate_evolution(example: GraphExample, figsize, name: str) -> None:
    """GIF: матриця ``D`` після кожної відкритої вершини ``k``.

    Цікаві кроки (де щось покращилося) тримаємо на екрані довше, «порожні» —
    коротше, фінальний кадр — із додатковою затримкою перед зацикленням.
    """
    labels = example.labels
    _, _, snapshots = floyd_warshall_steps(example.adjacency)
    figures, durations = [], []
    for snap in snapshots:
        title = (t("Початок") if snap["k"] is None
                 else t("Після відкриття {k}").format(k=labels[snap["k"]]))
        fig, ax = plt.subplots(figsize=figsize)
        draw_matrix(ax, snap["matrix"], labels, title,
                    pivot=snap["k"], changed=snap["changed"], prev=snap["prev"])
        fig.tight_layout()
        figures.append(fig)
        if snap["k"] is None:
            durations.append(1400)
        elif snap["changed"]:
            durations.append(2200)
        else:
            durations.append(900)
    durations[-1] += 1200
    save_anim(figures, name, durations)
    print(t("  {name}: {n} кадрів").format(name=name, n=len(figures)))


def animate_path(example: GraphExample, src: int, dst: int, name: str,
                 *, curved: bool = False, figsize=(7, 5)) -> None:
    """GIF/MP4: маршрут ``src → dst`` розгортається ребро за ребром за матрицею ``nxt``."""
    labels = example.labels
    _, nxt, _ = floyd_warshall_steps(example.adjacency)
    path = reconstruct_path(nxt, src, dst)
    arrow = " → ".join(labels[v] for v in path)
    title = t("Відновлення шляху {a} → {b} за nxt:  {arrow}").format(
        a=labels[src], b=labels[dst], arrow=arrow)

    figures, durations = [], []
    # вступний кадр — увесь граф без підсвітки (контекст)
    figures.append(draw_graph(example.adjacency, example.positions, labels,
                              title=title, curved=curved, figsize=figsize))
    durations.append(1100)
    # далі по одному ребру за раз: [src], [src, …], … увесь шлях
    # (лічильник навмисно `ti`, а не `t` — щоб не затінити імпортовану t() з i18n)
    for ti in range(1, len(path) + 1):
        figures.append(draw_graph(example.adjacency, example.positions, labels,
                                  highlight_path=path[:ti], title=title,
                                  curved=curved, figsize=figsize))
        durations.append(2400 if ti == len(path) else 900)
    save_anim(figures, name, durations)
    print(t("  {name}: {n} кадрів ({arrow})").format(name=name, n=len(figures), arrow=arrow))


def animate_airport_progressive(name: str) -> None:
    """GIF/MP4: відкриваємо хаби по черзі — маршрут ``i → j`` коротшає (``∞ → 12 → 6``)."""
    figures = [draw_airport_progressive_panel(i) for i in range(3)]
    durations = [1500, 1800, 2600]
    save_anim(figures, name, durations)
    print(t("  {name}: {n} кадрів").format(name=name, n=len(figures)))


def animate_kstep_sweep(example: GraphExample, k: int, name: str,
                        figsize=(5.9, 6.7)) -> None:
    """GIF: два внутрішні цикли перебирають усі пари ``(i, j)`` за фіксованого ``k``.

    Відтворюємо подвійний цикл руками, починаючи зі стану «до кроку ``k``», і
    зберігаємо кадр на кожну пару: помаранчева рамка — поточна ``(i, j)``, синій
    хрест — опорні рядок/стовпець ``k``, зелене — клітинки, уже покращені на
    цьому кроці. Наприкінці звіряємося з офіційним знімком алгоритму.
    """
    labels = example.labels
    n = len(labels)
    _, _, snapshots = floyd_warshall_steps(example.adjacency)
    snap = snapshots[k + 1]                 # знімок «після відкриття k»
    work = deepcopy(snap["prev"])           # стан ДО кроку k
    kn = labels[k]
    title = t("Крок k = {k}: два внутрішні цикли перебирають усі пари (i, j)").format(k=kn)

    changed, figures, durations = set(), [], []
    for i in range(n):
        for j in range(n):
            skip = (i == k or j == k or i == j)
            old, via = work[i][j], work[i][k] + work[k][j]
            improved = (not skip) and (via < old)
            if improved:
                work[i][j] = via
                changed.add((i, j))

            a, b = labels[i], labels[j]
            if skip:
                caption = t("(i, j) = ({a}, {b}):  рядок/стовпець {k} або діагональ — пропускаємо").format(
                    a=a, b=b, k=kn)
            else:
                tail = t("   ✔ покращено") if improved else t("   без змін")
                caption = t("(i, j) = ({a}, {b}):  D[{a}][{b}] = min({old}, {dik}+{dkj}) = {res}{tail}").format(
                    a=a, b=b, old=format_value(old), dik=format_value(work[i][k]),
                    dkj=format_value(work[k][j]), res=format_value(work[i][j]), tail=tail)

            fig, ax = plt.subplots(figsize=figsize)
            draw_matrix(ax, work, labels, title, pivot=k, changed=set(changed), current=(i, j))
            fig.text(0.5, 0.045, caption, ha="center", va="center", fontsize=11,
                     family="monospace", color=GREEN_TXT if improved else "#3c4043")
            fig.subplots_adjust(left=0.04, right=0.96, top=0.93, bottom=0.10)
            figures.append(fig)
            durations.append(1200 if improved else (190 if skip else 360))

    # безпека: ручний прохід має давати той самий результат, що й алгоритм
    assert work == snap["matrix"] and changed == snap["changed"], "скан не збігся зі знімком"
    durations[-1] += 1400
    save_anim(figures, name, durations)
    print(t("  {name}: {n} кадрів (покращень: {imp})").format(name=name, n=len(figures), imp=len(changed)))


def _walk_box(fig, text: str) -> None:
    """Підпис у фіксованому куті осі (накопичена вага під час обходу циклу)."""
    ax = fig.axes[0]
    ax.text(0.02, 0.98, text, transform=ax.transAxes, ha="left", va="top",
            fontsize=11, color=PATH_COLOR, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=PATH_COLOR, alpha=0.92))


def animate_negcycle_walk(example: GraphExample, name: str, loops: int = 3,
                          figsize=(6.4, 4.9)) -> None:
    """GIF/MP4: обхід від'ємного циклу з накопиченням ваги (``0, −1, −2, … → −∞``)."""
    labels = example.labels
    adj, pos = example.adjacency, example.positions
    cycle = [0, 1, 2]                       # X → Y → Z → (X)
    edge_w = -1
    title = t("Обхід від'ємного циклу {a} → {b} → {c} → {a} (кожне ребро −1)").format(
        a=labels[0], b=labels[1], c=labels[2])

    figures, durations = [], []
    # старт
    fig = draw_graph(adj, pos, labels, highlight_path=[0], title=title, curved=True, figsize=figsize)
    _walk_box(fig, t("на старті у {a}\nнакопичена вага: 0").format(a=labels[0]))
    figures.append(fig)
    durations.append(1200)

    acc = 0
    for s in range(loops * 3):
        u, v = cycle[s % 3], cycle[(s + 1) % 3]
        acc += edge_w
        done = (s + 1) // 3
        fig = draw_graph(adj, pos, labels, highlight_path=[u, v], title=title, curved=True, figsize=figsize)
        _walk_box(fig, t("крок {s}:  {u} → {v}\nнакопичена вага: {acc}\nповних обходів: {done}").format(
            s=s + 1, u=labels[u], v=labels[v], acc=acc, done=done))
        figures.append(fig)
        durations.append(1000 if (s + 1) % 3 == 0 else 700)

    # фінальний кадр — увесь цикл і висновок
    fig = draw_graph(adj, pos, labels, highlight_path=[0, 1, 2, 0], title=title, curved=True, figsize=figsize)
    _walk_box(fig, t("обходити можна вічно:\n−3, −6, −9, …  →  −∞"))
    figures.append(fig)
    durations.append(2800)

    save_anim(figures, name, durations)
    print(t("  {name}: {n} кадрів").format(name=name, n=len(figures)))


def animate_negcycle_divergence(name: str, cycle_weight: int = -3,
                                max_loops: int = 10, figsize=(7, 4.2)) -> None:
    """GIF/MP4: графік накопиченої ваги ``−3, −6, … → −∞``, точка за точкою."""
    loops = list(range(0, max_loops + 1))
    weights = [cycle_weight * k for k in loops]
    y_lo = cycle_weight * max_loops - 2

    figures, durations = [], []
    # лічильник навмисно `ti`, а не `t` — щоб не затінити імпортовану t() з i18n
    for ti in range(len(loops)):
        fig, ax = plt.subplots(figsize=figsize)
        ax.set_xlim(-0.3, max_loops + 0.3)
        ax.set_ylim(y_lo, 3)
        ax.axhline(0, color=AXIS_LINE, linewidth=0.8)
        ax.plot(loops[:ti + 1], weights[:ti + 1], "o-", color=PATH_COLOR, linewidth=2)
        ax.plot([loops[ti]], [weights[ti]], "o", color=PATH_COLOR, markersize=11)
        ax.text(loops[ti] + 0.15, weights[ti], f"{weights[ti]}", color=PATH_COLOR,
                fontsize=10, fontweight="bold", va="center")
        ax.set_xlabel(t("Кількість обходів циклу  k"))
        ax.set_ylabel(t("Накопичена вага шляху"))
        ax.set_title(t("Вага шляху з k обходами циклу X → Y → Z → X  (вага циклу = −3)"))
        ax.grid(alpha=0.3)
        if ti == len(loops) - 1:
            ax.annotate(t("→ −∞\n(мінімуму не існує)"), xy=(max_loops, weights[-1]),
                        xytext=(max_loops * 0.52, weights[-1] + 7),
                        fontsize=11, color=PATH_COLOR, fontweight="bold",
                        arrowprops=dict(arrowstyle="->", color=PATH_COLOR, lw=1.6))
        fig.tight_layout()
        figures.append(fig)
        durations.append(520)
    durations[0] = 1000
    durations[-1] = 2800
    save_anim(figures, name, durations)
    print(t("  {name}: {n} кадрів").format(name=name, n=len(figures)))


def main() -> None:
    configure_style()
    print(t("Генерую GIF-анімації (Tier 1–2)…"))

    # імена — БЕЗ розширення: save_anim сам додасть .gif (+ .mp4 за наявності ffmpeg)
    # 1) еволюція матриці D
    animate_evolution(ABCDEF, (5.7, 6.0), "evolution_abcdef")
    animate_evolution(PQRS, (4.7, 5.0), "evolution_pqrs")

    # 2) розгортання найкоротшого шляху за nxt
    animate_path(ABCDEF, 0, 3, "path_abcdef_A_to_D", figsize=(7, 5))
    animate_path(PQRS, 0, 3, "path_pqrs_P_to_S", curved=True, figsize=(7, 4.5))

    # 3) прогресія хабів (аналогія з аеропортами)
    animate_airport_progressive("airport_progressive")

    # 4) скан пар (i, j) двома внутрішніми циклами для k = C
    animate_kstep_sweep(ABCDEF, 2, "sweep_abcdef_k_C")

    # 5) від'ємний цикл: обхід із накопиченням ваги + графік розбіжності
    animate_negcycle_walk(XYZ, "negcycle_walk_xyz")
    animate_negcycle_divergence("negcycle_weight_divergence")

    print_saved_location()


if __name__ == "__main__":
    main()
