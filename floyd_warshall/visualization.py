"""Візуалізації для навчального розбору алгоритму Флойда–Воршала.

Усі функції малювання параметризовані списком міток вершин ``labels``, тож
одні й ті самі функції працюють і для звичайних, і для від'ємних ваг — для
будь-якого прикладу:

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

import math
from typing import Dict, List, Optional, Sequence, Set, Tuple

import matplotlib.pyplot as plt
import networkx as nx

from .core import INF
from .i18n import t
from .style import (
    FIGURE_DPI,
    configure_style,
    BLUE_FILL,
    BLUE_EDGE,
    GREEN_FILL,
    GREEN_TXT,
    GRID_EDGE,
    PIVOT_EDGE,
    SCAN_EDGE,
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
    "draw_airport_relaxation",
    "draw_airport_progressive",
    "draw_airport_progressive_panel",
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
    title: Optional[str] = None,
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

    ax.set_title(t("Орієнтований зважений граф") if title is None else title)
    ax.axis("off")
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Аналогія з аеропортами (ілюстрації для розділу «Інтуїція»)
# ---------------------------------------------------------------------------
def _airport_node(ax, xy: Tuple[float, float], label: str,
                  *, color: str = NODE_COLOR, r: float = 0.32, fontsize: int = 15) -> None:
    """Малює один «аеропорт» — кружок із підписом."""
    ax.add_patch(plt.Circle(xy, r, facecolor=color, edgecolor="white", linewidth=2, zorder=3))
    ax.text(xy[0], xy[1], label, ha="center", va="center", color="white",
            fontweight="bold", fontsize=fontsize, zorder=4)


def _arrow(ax, src: Tuple[float, float], dst: Tuple[float, float],
           *, color: str, lw: float, dashed: bool = False, r: float = 0.32) -> None:
    """Стрілка-«рейс» між двома аеропортами, з відступом ``r`` від кружків."""
    dx, dy = dst[0] - src[0], dst[1] - src[1]
    dist = math.hypot(dx, dy) or 1.0
    ux, uy = dx / dist, dy / dist
    a = (src[0] + ux * r, src[1] + uy * r)
    b = (dst[0] - ux * r, dst[1] - uy * r)
    ax.annotate("", xy=b, xytext=a, zorder=2,
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw,
                                linestyle="--" if dashed else "-"))


def draw_airport_relaxation(direct: float = 10, leg1: float = 4, leg2: float = 3,
                            i_label: str = "i", k_label: str = "k", j_label: str = "j",
                            figsize: Tuple[float, float] = (7.5, 5.2)):
    """Схема «прямий рейс проти пересадки»: суть релаксації мовою аеропортів.

    Прямий рейс ``i → j`` (пунктир) проти пересадки ``i → k → j``. Виграшний
    варіант підсвічено зеленим, унизу — формула ``D[i][j] = min(пряме, через k)``.

    :returns: об'єкт ``Figure``.
    """
    via = leg1 + leg2
    pos_i, pos_j, pos_k = (0.0, 0.0), (5.0, 0.0), (2.5, 2.6)
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_xlim(-1.2, 6.2)
    ax.set_ylim(-2.4, 3.5)
    ax.set_aspect("equal")
    ax.axis("off")

    transfer_wins = via < direct
    transfer_color = GREEN_TXT if transfer_wins else NEUTRAL_GRAY
    direct_color = NEUTRAL_GRAY if transfer_wins else GREEN_TXT

    _arrow(ax, pos_i, pos_k, color=transfer_color, lw=3.2)
    _arrow(ax, pos_k, pos_j, color=transfer_color, lw=3.2)
    _arrow(ax, pos_i, pos_j, color=direct_color, lw=2.2, dashed=True)

    _airport_node(ax, pos_i, i_label)
    _airport_node(ax, pos_j, j_label)
    _airport_node(ax, pos_k, k_label, color=BLUE_EDGE)

    def _leg(p, q, text, color):
        ax.text((p[0] + q[0]) / 2, (p[1] + q[1]) / 2, text, ha="center", va="center",
                fontsize=12, color=color, fontweight="bold", zorder=5,
                bbox=dict(boxstyle="round,pad=0.18", fc="white", ec=color, alpha=0.95))

    _leg(pos_i, pos_k, t("{leg:g} год").format(leg=leg1), transfer_color)
    _leg(pos_k, pos_j, t("{leg:g} год").format(leg=leg2), transfer_color)
    ax.text(2.5, -0.6, t("прямий рейс: {direct:g} год").format(direct=direct), ha="center", va="center",
            fontsize=12, color=direct_color, fontweight="bold", zorder=5,
            bbox=dict(boxstyle="round,pad=0.18", fc="white", ec=direct_color, alpha=0.95))

    # суто формульний рядок (без слів) — однаковий обома мовами, тож без t()
    ax.text(2.5, -1.5, f"D[{i_label}][{j_label}] = min( {direct:g} ,  {leg1:g}+{leg2:g} ) = {min(direct, via):g}",
            ha="center", va="center", fontsize=14, family="monospace",
            color=TEXT_RESULT, fontweight="bold")
    note = (t("пересадка через {k} коротша за прямий рейс").format(k=k_label)
            if transfer_wins else t("прямий рейс коротший за пересадку через {k}").format(k=k_label))
    ax.text(2.5, -2.05, note, ha="center", va="center", fontsize=11,
            color=GREEN_TXT if transfer_wins else HEADER_TXT, style="italic")

    ax.set_title(t("Аналогія: прямий рейс проти пересадки через хаб {k}").format(k=k_label), fontsize=14, pad=10)
    fig.tight_layout()
    return fig


# Дані прогресії хабів — спільні для статичної версії (:func:`draw_airport_progressive`)
# та для GIF-анімації (:func:`draw_airport_progressive_panel`), щоб не дублювати їх.
_PROG_POS: Dict[str, Tuple[float, float]] = {
    "i": (0.0, 0.0), "B": (1.4, 1.5), "C": (3.1, 1.5), "j": (4.5, 0.0),
}
_PROG_EDGES = [("i", "B", "3"), ("B", "C", "1"), ("C", "j", "2"), ("B", "j", "9")]
_PROG_PANELS = [
    ("—", [], "i → j: прямого рейсу немає  →  ∞"),
    ("B", ["i", "B", "j"], "i → B → j = 3 + 9 = 12"),
    ("B, C", ["i", "B", "C", "j"], "i → B → C → j = 3 + 1 + 2 = 6"),
]


def _progressive_panel(ax, pos, edges, allowed: str, path: List[str], caption: str) -> None:
    """Одна панель прогресії: граф аеропортів із підсвіченим поточним маршрутом."""
    ax.set_xlim(-0.8, 5.3)
    ax.set_ylim(-1.7, 2.5)
    ax.set_aspect("equal")
    ax.axis("off")
    path_edges = {(path[t], path[t + 1]) for t in range(len(path) - 1)}
    for u, v, w in edges:
        active = (u, v) in path_edges
        _arrow(ax, pos[u], pos[v], color=PATH_COLOR if active else NEUTRAL_GRAY,
               lw=3.2 if active else 1.4, r=0.28)
        ax.text((pos[u][0] + pos[v][0]) / 2, (pos[u][1] + pos[v][1]) / 2, w,
                ha="center", va="center", fontsize=11, zorder=5,
                color=PATH_COLOR if active else MUTED_TXT,
                bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.9))
    for name, xy in pos.items():
        _airport_node(ax, xy, name, color=PATH_COLOR if name in path else NODE_COLOR,
                      r=0.28, fontsize=13)
    ax.set_title(t("Дозволено пересадки: {allowed}").format(allowed=allowed),
                 fontsize=12, color=HEADER_TXT, pad=6)
    ax.text(2.25, -1.45, t(caption), ha="center", va="center", fontsize=11,
            color=HEADER_TXT, fontweight="bold")


def draw_airport_progressive(figsize: Tuple[float, float] = (13.5, 4.6)):
    """Три панелі: як дозвіл пересадок через нові хаби поступово вкорочує ``i → j``.

    :returns: об'єкт ``Figure``.
    """
    fig, axes = plt.subplots(1, 3, figsize=figsize)
    for ax, (allowed, path, caption) in zip(axes, _PROG_PANELS):
        _progressive_panel(ax, _PROG_POS, _PROG_EDGES, allowed, path, caption)
    fig.suptitle(t("Відкриваємо аеропорти-хаби по черзі — маршрут i → j коротшає"), fontsize=14)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    return fig


def draw_airport_progressive_panel(
    index: int,
    figsize: Tuple[float, float] = (5.2, 4.7),
):
    """Одна панель прогресії хабів як окрема фігура — кадр для GIF-анімації.

    Та сама ідея, що й у :func:`draw_airport_progressive`, але по одному стану на
    фігуру (щоб зібрати з них анімацію в :func:`floyd_warshall.animation.save_gif`).

    :param index: 0, 1 або 2 — скільки хабів уже «відкрито» (нічого / B / B, C).
    :returns: об'єкт ``Figure``.
    """
    allowed, path, caption = _PROG_PANELS[index]
    fig, ax = plt.subplots(figsize=figsize)
    _progressive_panel(ax, _PROG_POS, _PROG_EDGES, allowed, path, caption)
    fig.suptitle(t("Відкриваємо хаби по черзі — маршрут i → j коротшає"), fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
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
    current: Optional[Tuple[int, int]] = None,
) -> None:
    """Малює матрицю відстаней як таблицю на заданій осі ``ax``.

    :param pivot: індекс поточної проміжної вершини ``k`` (підсвічуємо рядок
        і стовпець). ``None`` — без підсвічування (початковий знімок).
    :param changed: множина клітинок ``(i, j)``, що змінилися (зелені).
    :param prev: попередня матриця — щоб показати старе значення в дужках.
    :param current: клітинка ``(i, j)``, яку зараз перевіряє скан двох внутрішніх
        циклів — обводимо помаранчевим (для покрокової анімації кроку).
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

    if current is not None:
        ci, cj = current
        ax.add_patch(plt.Rectangle((cj + 1, ci + 1), 1, 1, fill=False,
                                   edgecolor=SCAN_EDGE, linewidth=3, zorder=5))


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

    ax.set_title(title if title is not None else t("Матриця D"), fontsize=15, pad=12)
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
    cell_w: float = 3.4,
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

    cell_h, header_w, header_h = 2.55, 1.05, 1.0
    left_pad, top_pad, bot_pad = 2.7, 1.15, 0.5
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
                dy = 0.34
                y_start = row_yc(i) - dy * (len(lines) - 1) / 2
                # NB: не називаємо лічильник `t` — це затінило б імпортовану t() (i18n)
                for li, (txt, col, w) in enumerate(lines):
                    ax.text(x0 + 0.16, y_start + li * dy, txt, ha="left", va="center",
                            fontsize=16.8 if w == "bold" else 15.4, family="monospace", color=col, fontweight=w)
            else:
                v = matrix[i][j]
                ax.text(cell_xc(j), row_yc(i), format_value(v), ha="center", va="center",
                        fontsize=26, color=MUTED_TXT if v == INF else "black")

    # рамка навколо рядка k та стовпця k
    ax.add_patch(plt.Rectangle((xs[0], row_top(k)), total_w - xs[0], cell_h, fill=False, edgecolor=BLUE_EDGE, linewidth=2.5))
    ax.add_patch(plt.Rectangle((xs[k], row_top(0)), cell_w, n * cell_h, fill=False, edgecolor=BLUE_EDGE, linewidth=2.5))

    ax.text(total_w / 2, total_h - bot_pad * 0.4,
            t("у кожній клітинці — повна формула:  D[i][j] = min( поточне , шлях через k ) = min( числа ) = результат (жирним)"),
            ha="center", va="center", fontsize=8.2, color=MUTED_TXT, style="italic")

    kn = labels[k]
    ax.annotate(t("Стовпець {k} містить\nD[i][{k}]  (відстань до {k})").format(k=kn),
                xy=(cell_xc(k), row_top(0)), xytext=(cell_xc(k), top_pad * 0.30),
                ha="center", va="center", fontsize=10, color=BLUE_EDGE, fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color=BLUE_EDGE, lw=1.8))
    ax.annotate(t("рядок {k} містить\nD[{k}][j]\n(відстань від {k})").format(k=kn),
                xy=(left_pad, row_yc(k)), xytext=(left_pad * 0.46, row_yc(k)),
                ha="center", va="center", fontsize=10, color=BLUE_EDGE, fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color=BLUE_EDGE, lw=1.8))

    ax.set_title(title if title is not None else t("Матриця D після відкриття вершини {k}").format(k=kn),
                 fontsize=14, pad=12)
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

    titles = [t("Початок")] + [t("Після {k}").format(k=labels[s["k"]]) for s in snapshots[1:]]
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
    out = [bar, t("Крок: проміжна вершина k = {k}").format(k=labels[k]), bar]

    if not changed:
        out.append(t("Жодна відстань не покращилася на цьому кроці."))
        no_in = all(prev[i][k] == INF for i in range(n) if i != k)
        no_out = all(prev[k][j] == INF for j in range(n) if j != k)
        if no_in:
            out.append(t("  Причина: у вершину {k} не входить жодне ребро (D[i][{k}] = ∞).").format(k=labels[k]))
        elif no_out:
            out.append(t("  Причина: з вершини {k} не виходить жодне ребро (D[{k}][j] = ∞).").format(k=labels[k]))
        else:
            out.append(t("  Через {k} не знайшлося коротших шляхів.").format(k=labels[k]))
    else:
        out.append(t("Покращено відстаней: {n}").format(n=len(changed)))
        for (i, j) in sorted(changed):
            va, vb = prev[i][k], prev[k][j]   # числові опорні значення для _sum_expr
            new = snap["matrix"][i][j]
            old = prev[i][j]
            out.append(
                t("  D[{a}][{b}]: {old} → {new}   (бо D[{a}][{k}] + D[{k}][{b}] = {expr} = {new})").format(
                    a=labels[i], b=labels[j], k=labels[k],
                    old=format_value(old), new=format_value(new), expr=_sum_expr(va, vb),
                )
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
        title=t("Матриця D після відкриття вершини {k}").format(k=labels[snap["k"]]),
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
