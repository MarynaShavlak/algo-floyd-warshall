"""Візуалізації для навчального розбору алгоритму Флойда–Воршала.

Модуль збирає в одному місці всі функції малювання, що в оригінальному
ноутбуці існували у двох майже однакових копіях (звичайна та «для від'ємних
ваг»). Тут вони об'єднані й параметризовані списком міток вершин ``labels``,
тож працюють для будь-якого прикладу:

* :func:`draw_graph` — орієнтований зважений граф (із можливістю підсвітити шлях);
* :func:`draw_matrix` — компактна матриця відстаней на заданій осі;
* :func:`draw_matrix_standalone` — те саме, але створює власну фігуру;
* :func:`draw_floyd_step` — «детальний кадр»: у кожній клітинці, що може
  оновитися, повна формула ``min(...)`` записана вертикально;
* :func:`draw_evolution` — зведена сітка знімків матриці після кожного кроку;
* :func:`show_step` / :func:`step_summary` — текстовий підсумок кроку + кадр.

Кольорова схема (єдина для всіх візуалізацій):

* 🟦 синій (``#E3F2FD`` / ``#1976D2``) — поточна проміжна вершина ``k``
  (її рядок і стовпець — «опорні» значення ``D[i][k]`` та ``D[k][j]``);
* 🟩 зелений (``#C8E6C9`` / ``#2E7D32``) — клітинка, що покращилася на кроці;
* 🔴 червоний (``#D32F2F``) — підсвічений найкоротший шлях на графі.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Set, Tuple

import matplotlib.pyplot as plt
import networkx as nx

from .core import INF
from .style import (
    FIGURE_DPI,
    configure_style,
    BLUE_FILL,
    BLUE_EDGE,
    GREEN_FILL,
    GREEN_TXT,
    GRID_EDGE,
    PIVOT_EDGE,
    PATH_COLOR,
    NODE_COLOR,
    NEUTRAL_GRAY,
    DIAG_FILL,
    HEADER_TXT,
    SUBLABEL_TXT,
    MUTED_TXT,
    INF_TXT_COMPACT,
    TEXT_DARK,
    TEXT_FORMULA,
    TEXT_RESULT,
)

# :func:`configure_style` лишається доступною з цього модуля задля сумісності
# (приклади імпортують її саме звідси), але визначена в :mod:`floyd_warshall.style`.

__all__ = [
    "configure_style",
    "format_value",
    "build_graph",
    "draw_graph",
    "draw_matrix",
    "draw_matrix_standalone",
    "draw_floyd_step",
    "draw_evolution",
    "step_summary",
    "show_step",
    "print_distance_matrix",
]


# ---------------------------------------------------------------------------
# Допоміжні форматувальники
# ---------------------------------------------------------------------------
def format_value(v: float) -> str:
    """Форматує значення матриці; нескінченність -> символ ∞."""
    return "∞" if v == INF else f"{v:g}"


def _sum_expr(a: float, b: float) -> str:
    """Гарний запис суми двох доданків: від'ємний доданок беремо в дужки.

    Напр. ``4 + (-2)`` друкується як ``4+(-2)``, а ``3 + 1`` — як ``3+1``.
    """
    sa = format_value(a)
    sb = f"({format_value(b)})" if (b != INF and b < 0) else format_value(b)
    return f"{sa}+{sb}"


# ---------------------------------------------------------------------------
# Граф
# ---------------------------------------------------------------------------
def build_graph(adj: List[List[float]]) -> "nx.DiGraph":
    """Будує орієнтований граф ``networkx`` із матриці суміжності (``0 == немає ребра``)."""
    G = nx.DiGraph()
    G.add_nodes_from(range(len(adj)))
    for i in range(len(adj)):
        for j in range(len(adj)):
            if i != j and adj[i][j] != 0:
                G.add_edge(i, j, weight=adj[i][j])
    return G


def draw_graph(
    adj: List[List[float]],
    pos: Dict[int, Tuple[float, float]],
    labels: Sequence[str],
    highlight_path: Optional[Sequence[int]] = None,
    title: str = "Орієнтований зважений граф",
    curved: bool = False,
    figsize: Tuple[float, float] = (7, 4.5),
):
    """Малює орієнтований зважений граф.

    :param pos: координати вершин ``{індекс: (x, y)}``.
    :param labels: підписи вершин (за індексами).
    :param highlight_path: список вершин шляху, який треба підсвітити червоним.
    :param curved: вигнуті ребра (``arc3``) — зручно, коли є зустрічні ребра
        (наприклад, у циклі), щоб вони не накладалися.
    :returns: об'єкт ``Figure``.
    """
    G = build_graph(adj)
    fig, ax = plt.subplots(figsize=figsize)

    path_edges: Set[Tuple[int, int]] = set()
    if highlight_path and len(highlight_path) > 1:
        path_edges = {
            (highlight_path[t], highlight_path[t + 1])
            for t in range(len(highlight_path) - 1)
        }

    edge_colors = [PATH_COLOR if (u, v) in path_edges else NEUTRAL_GRAY for u, v in G.edges()]
    widths = [3.0 if (u, v) in path_edges else 1.6 for u, v in G.edges()]
    node_colors = [
        PATH_COLOR if (highlight_path and node in highlight_path) else NODE_COLOR
        for node in G.nodes()
    ]

    edge_kwargs = dict(
        edge_color=edge_colors, width=widths,
        arrowsize=20, arrowstyle="-|>", node_size=750, ax=ax,
    )
    if curved:
        edge_kwargs["connectionstyle"] = "arc3,rad=0.12"

    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=750, ax=ax)
    nx.draw_networkx_labels(
        G, pos, labels={i: labels[i] for i in G.nodes()},
        font_color="white", font_weight="bold", ax=ax,
    )
    nx.draw_networkx_edges(G, pos, **edge_kwargs)
    edge_labels = nx.get_edge_attributes(G, "weight")
    nx.draw_networkx_edge_labels(
        G, pos, edge_labels=edge_labels, font_size=11, label_pos=0.5, ax=ax,
        bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85),
    )

    ax.set_title(title)
    ax.axis("off")
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Компактна матриця
# ---------------------------------------------------------------------------
def draw_matrix(
    ax,
    matrix: List[List[float]],
    labels: Sequence[str],
    title: str,
    pivot: Optional[int] = None,
    changed: Optional[Set[Tuple[int, int]]] = None,
    prev: Optional[List[List[float]]] = None,
) -> None:
    """Малює матрицю відстаней як таблицю на заданій осі ``ax``.

    :param pivot: індекс поточної проміжної вершини ``k`` (підсвічуємо рядок
        і стовпець). ``None`` — без підсвічування (початковий знімок).
    :param changed: множина клітинок ``(i, j)``, що змінилися (зелені).
    :param prev: попередня матриця — щоб показати старе значення в дужках.
    """
    n = len(matrix)
    changed = changed or set()
    ax.set_xlim(-0.2, n + 1.2)
    ax.set_ylim(-0.2, n + 1.2)
    ax.set_aspect("equal")
    ax.invert_yaxis()
    ax.axis("off")
    ax.set_title(title, fontsize=12, pad=8)

    ax.text(0.5, 0.5, "i→j", ha="center", va="center", fontsize=8.5, color=SUBLABEL_TXT)
    for j in range(n):
        ax.text(j + 1.5, 0.5, labels[j], ha="center", va="center", fontweight="bold", color=HEADER_TXT)
    for i in range(n):
        ax.text(0.5, i + 1.5, labels[i], ha="center", va="center", fontweight="bold", color=HEADER_TXT)

    for i in range(n):
        for j in range(n):
            face = "white"
            if i == j:
                face = DIAG_FILL
            if pivot is not None and (i == pivot or j == pivot):
                face = BLUE_FILL
            if (i, j) in changed:
                face = GREEN_FILL
            ax.add_patch(plt.Rectangle((j + 1, i + 1), 1, 1, facecolor=face, edgecolor=GRID_EDGE, linewidth=1))
            val = matrix[i][j]
            txt = format_value(val)
            if (i, j) in changed:
                ax.text(j + 1.5, i + 1.42, txt, ha="center", va="center",
                        fontsize=12, fontweight="bold", color=GREEN_TXT)
                if prev is not None:
                    ax.text(j + 1.5, i + 1.78, "(" + format_value(prev[i][j]) + ")", ha="center", va="center",
                            fontsize=6.5, color=NEUTRAL_GRAY)
            else:
                color = INF_TXT_COMPACT if val == INF else TEXT_DARK
                ax.text(j + 1.5, i + 1.5, txt, ha="center", va="center", fontsize=12, color=color)

    if pivot is not None:
        ax.add_patch(plt.Rectangle((pivot + 1, 1), 1, n, fill=False, edgecolor=PIVOT_EDGE, linewidth=2))
        ax.add_patch(plt.Rectangle((1, pivot + 1), n, 1, fill=False, edgecolor=PIVOT_EDGE, linewidth=2))


def draw_matrix_standalone(
    matrix: List[List[float]],
    labels: Sequence[str],
    title: Optional[str] = None,
    cell: float = 1.15,
):
    """Проста матриця ``D`` у власній фігурі (без підсвічувань).

    Зручно для початкової та підсумкової матриць.
    :returns: об'єкт ``Figure``.
    """
    n = len(labels)
    hw = 1.05
    total = hw + n * cell
    fig, ax = plt.subplots(figsize=(total * 0.95, total * 0.95))
    ax.set_xlim(0, total)
    ax.set_ylim(0, total)
    ax.invert_yaxis()
    ax.axis("off")

    def cxc(j: int) -> float:
        return hw + j * cell + cell / 2

    def ryc(i: int) -> float:
        return hw + i * cell + cell / 2

    for j in range(n):
        ax.text(cxc(j), hw / 2, labels[j], ha="center", va="center", fontsize=15, fontweight="bold")
    ax.text(hw / 2, hw / 2, "i→j", ha="center", va="center", fontsize=9, color=MUTED_TXT)
    for i in range(n):
        ax.text(hw / 2, ryc(i), labels[i], ha="center", va="center", fontsize=15, fontweight="bold")

    for i in range(n):
        for j in range(n):
            ax.add_patch(plt.Rectangle((hw + j * cell, hw + i * cell), cell, cell,
                         facecolor="white", edgecolor=GRID_EDGE, linewidth=1))
            v = matrix[i][j]
            ax.text(cxc(j), ryc(i), format_value(v), ha="center", va="center",
                    fontsize=14, color=MUTED_TXT if v == INF else "black")

    ax.set_title(title or "Матриця D", fontsize=15, pad=12)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Детальний кадр кроку (повна формула в кожній клітинці)
# ---------------------------------------------------------------------------
def draw_floyd_step(
    matrix: List[List[float]],
    k: int,
    labels: Sequence[str],
    prev: Optional[List[List[float]]] = None,
    changed: Optional[Set[Tuple[int, int]]] = None,
    title: Optional[str] = None,
    cell_w: float = 2.7,
):
    """Детальний кадр кроку Флойда–Воршала.

    У КОЖНІЙ клітинці, що може оновитися (``i != k`` і ``i != j``), повна
    формула записана вертикально::

        D[i][j] = min(
          D[i][j],
          D[i][k]+D[k][j]
        ) = min( <до>, <шлях через k> ) = <результат>

    Результат (після кроку) — жирним, зеленим, якщо покращився. Опорний рядок
    і стовпець ``k`` підсвічуються й підписуються стрілками.

    :returns: об'єкт ``Figure``.
    """
    if changed is None:
        changed = set()
    if prev is None:
        prev = matrix
    n = len(labels)

    cell_h, header_w, header_h = 2.12, 1.05, 1.0
    left_pad, top_pad, bot_pad = 4.3, 1.9, 0.6
    xs = [left_pad + header_w + j * cell_w for j in range(n)]
    total_w = left_pad + header_w + n * cell_w
    total_h = top_pad + header_h + n * cell_h + bot_pad

    fig, ax = plt.subplots(figsize=(total_w * 0.82, total_h * 0.82))
    ax.set_xlim(0, total_w)
    ax.set_ylim(0, total_h)
    ax.invert_yaxis()
    ax.axis("off")

    def cell_xc(j: int) -> float:
        return xs[j] + cell_w / 2

    def row_top(i: int) -> float:
        return top_pad + header_h + i * cell_h

    def row_yc(i: int) -> float:
        return row_top(i) + cell_h / 2

    col_hdr_yc = top_pad + header_h / 2

    # заголовки рядків/стовпців
    for j in range(n):
        ax.text(cell_xc(j), col_hdr_yc, labels[j], ha="center", va="center",
                fontsize=15, fontweight="bold", color=HEADER_TXT)
    ax.text(left_pad + header_w / 2, col_hdr_yc, "i→j", ha="center", va="center", fontsize=9, color=MUTED_TXT)
    for i in range(n):
        ax.text(left_pad + header_w / 2, row_yc(i), labels[i], ha="center", va="center",
                fontsize=15, fontweight="bold", color=HEADER_TXT)

    # клітинки
    for i in range(n):
        for j in range(n):
            x0, y0 = xs[j], row_top(i)
            updatable = (i != k and i != j)
            if (i, j) in changed:
                face = GREEN_FILL
            elif i == k or j == k:
                face = BLUE_FILL
            elif i == j:
                face = DIAG_FILL
            else:
                face = "white"
            ax.add_patch(plt.Rectangle((x0, y0), cell_w, cell_h, facecolor=face, edgecolor=GRID_EDGE, linewidth=1))

            if updatable:
                a, b, c = labels[i], labels[j], labels[k]
                dik, dkj = matrix[i][k], matrix[k][j]  # рядок/стовпець k під час свого кроку незмінні
                old, res = prev[i][j], matrix[i][j]
                improved = (i, j) in changed
                lines = [
                    (f"D[{a}][{b}] = min(", HEADER_TXT, "normal"),
                    (f"  D[{a}][{b}],", SUBLABEL_TXT, "normal"),
                    (f"  D[{a}][{c}]+D[{c}][{b}]", SUBLABEL_TXT, "normal"),
                    (") = min(", HEADER_TXT, "normal"),
                    (f"  {format_value(old)},", TEXT_FORMULA, "normal"),
                    (f"  {_sum_expr(dik, dkj)}", TEXT_FORMULA, "normal"),
                    (f") = {format_value(res)}", GREEN_TXT if improved else TEXT_RESULT, "bold"),
                ]
                dy = 0.27
                y_start = row_yc(i) - dy * (len(lines) - 1) / 2
                for t, (txt, col, w) in enumerate(lines):
                    ax.text(x0 + 0.13, y_start + t * dy, txt, ha="left", va="center",
                            fontsize=8.4 if w == "bold" else 7.7, family="monospace", color=col, fontweight=w)
            else:
                v = matrix[i][j]
                ax.text(cell_xc(j), row_yc(i), format_value(v), ha="center", va="center",
                        fontsize=14, color=MUTED_TXT if v == INF else "black")

    # рамка навколо рядка k та стовпця k
    ax.add_patch(plt.Rectangle((xs[0], row_top(k)), total_w - xs[0], cell_h, fill=False, edgecolor=BLUE_EDGE, linewidth=2.5))
    ax.add_patch(plt.Rectangle((xs[k], row_top(0)), cell_w, n * cell_h, fill=False, edgecolor=BLUE_EDGE, linewidth=2.5))

    ax.text(total_w / 2, total_h - bot_pad * 0.4,
            "у кожній клітинці — повна формула:  D[i][j] = min( поточне , шлях через k ) = min( числа ) = результат (жирним)",
            ha="center", va="center", fontsize=8.2, color=MUTED_TXT, style="italic")

    kn = labels[k]
    ax.annotate(f"Стовпець {kn} містить\nD[i][{kn}]  (відстань до {kn})",
                xy=(cell_xc(k), row_top(0)), xytext=(cell_xc(k), top_pad * 0.30),
                ha="center", va="center", fontsize=10, color=BLUE_EDGE, fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color=BLUE_EDGE, lw=1.8))
    ax.annotate(f"рядок {kn} містить\nD[{kn}][j]\n(відстань від {kn})",
                xy=(left_pad, row_yc(k)), xytext=(left_pad * 0.46, row_yc(k)),
                ha="center", va="center", fontsize=10, color=BLUE_EDGE, fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color=BLUE_EDGE, lw=1.8))

    ax.set_title(title or f"Матриця D після відкриття вершини {kn}", fontsize=14, pad=12)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Зведена сітка знімків
# ---------------------------------------------------------------------------
def draw_evolution(
    snapshots: List[Dict[str, object]],
    labels: Sequence[str],
    suptitle: str,
    ncols: int = 4,
):
    """Зведена сітка: матриця ``D`` після кожної проміжної вершини.

    :param snapshots: список знімків, повернений :func:`core.floyd_warshall_steps`.
    :returns: об'єкт ``Figure``.
    """
    count = len(snapshots)
    nrows = (count + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(ncols * 3.3, nrows * 3.3))
    axes = axes.flatten() if hasattr(axes, "flatten") else [axes]

    titles = ["Початок"] + [f"Після {labels[s['k']]}" for s in snapshots[1:]]
    for idx, snap in enumerate(snapshots):
        draw_matrix(axes[idx], snap["matrix"], labels, titles[idx],
                    pivot=snap["k"], changed=snap["changed"], prev=snap["prev"])
    for extra in range(count, len(axes)):
        axes[extra].axis("off")

    fig.suptitle(suptitle, fontsize=14)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Текстовий підсумок кроку + кадр
# ---------------------------------------------------------------------------
def step_summary(snap: Dict[str, object], labels: Sequence[str]) -> str:
    """Повертає текстовий підсумок одного кроку (що покращилося і чому).

    Якщо змін немає — пояснює причину (вершина-джерело або вершина-стік).
    """
    k = snap["k"]
    changed = snap["changed"]
    prev = snap["prev"]
    n = len(prev)
    bar = "=" * 60
    out = [bar, f"Крок: проміжна вершина k = {labels[k]}", bar]

    if not changed:
        out.append("Жодна відстань не покращилася на цьому кроці.")
        no_in = all(prev[i][k] == INF for i in range(n) if i != k)
        no_out = all(prev[k][j] == INF for j in range(n) if j != k)
        if no_in:
            out.append(f"  Причина: у вершину {labels[k]} не входить жодне ребро (D[i][{labels[k]}] = ∞).")
        elif no_out:
            out.append(f"  Причина: з вершини {labels[k]} не виходить жодне ребро (D[{labels[k]}][j] = ∞).")
        else:
            out.append(f"  Через {labels[k]} не знайшлося коротших шляхів.")
    else:
        out.append(f"Покращено відстаней: {len(changed)}")
        for (i, j) in sorted(changed):
            a, b = prev[i][k], prev[k][j]
            new = snap["matrix"][i][j]
            old = prev[i][j]
            out.append(
                f"  D[{labels[i]}][{labels[j]}]: {format_value(old)} → {format_value(new)}   "
                f"(бо D[{labels[i]}][{labels[k]}] + D[{labels[k]}][{labels[j]}] = {_sum_expr(a, b)} = {format_value(new)})"
            )
    return "\n".join(out)


def show_step(snap: Dict[str, object], labels: Sequence[str], save_path: Optional[str] = None):
    """Друкує текстовий підсумок кроку та малює детальний кадр.

    :param save_path: якщо задано — зберігає кадр у файл.
    :returns: об'єкт ``Figure``.
    """
    print(step_summary(snap, labels))
    fig = draw_floyd_step(
        snap["matrix"], snap["k"], labels, prev=snap["prev"], changed=snap["changed"],
        title=f"Матриця D після відкриття вершини {labels[snap['k']]}",
    )
    if save_path:
        fig.savefig(save_path, bbox_inches="tight", dpi=FIGURE_DPI)
    return fig


def print_distance_matrix(dist: List[List[float]], labels: Sequence[str]) -> None:
    """Друкує матрицю найкоротших відстаней у вигляді вирівняної таблиці."""
    n = len(labels)
    print("       " + "  ".join("{:>3}".format(labels[j]) for j in range(n)))
    for i in range(n):
        print("   {} | ".format(labels[i]) + "  ".join("{:>3}".format(format_value(dist[i][j])) for j in range(n)))
