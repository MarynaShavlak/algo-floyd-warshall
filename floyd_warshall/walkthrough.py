# -*- coding: utf-8 -*-
"""Покрокова візуалізація «код ↔ візуалізація» для алгоритму Флойда–Воршала.

Кожен крок — це рядок із двох панелей: **ліворуч фрагмент коду з підсвіченими
активними рядками**, **праворуч стан матриці D** саме на цьому кроці. Підхід
(журнал кроків → кодова панель → панель стану → композитор) описано в
``step-by-step-panels-playbook.md``; цей модуль — його перенесення на Флойда–Воршала.

Три незалежні блоки + композитор:

* **журнал** (:func:`build_overview_steps`, :func:`build_cell_steps`) — проганяє
  алгоритм і складає список **незмінних знімків**; знає алгоритм, нічого не малює;
* **кодова панель** (:func:`draw_code_panel`) — малює :data:`CODE` і підсвічує
  рядки за мапою ``{індекс: колір}`` зі знімка; нічого не знає про алгоритм;
* **панель стану** — повторно використовуємо :func:`visualization.draw_matrix`;
* **композитор** (:func:`render_code_step`, :func:`draw_code_walkthrough_grid`) —
  складає панелі в одну фігуру / у високу сітку.

Два рівні деталізації (обидва будуються з одного журналу):

* **оглядовий** — один крок на проміжну вершину ``k`` (підсвічено цикли,
  праворуч матриця після ``k``); :func:`build_overview_steps`;
* **по клітинці** — для одного обраного ``k`` крок = одна пара ``(i, j)``; колір
  коду показує, **яка гілка** ``if`` спрацювала; :func:`build_cell_steps`.

Двомовність: увесь видимий текст через :func:`floyd_warshall.i18n.t`; кольори —
зі :mod:`floyd_warshall.style`.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Dict, List, Optional, Sequence, Set, Tuple

import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle

from .core import INF, floyd_warshall_steps
from .i18n import t
from .style import (
    HL_ACTIVE,
    HL_ADD,
    HL_SKIP,
    GREEN_TXT,
    MUTED_TXT,
    TEXT_DARK,
    TEXT_FORMULA,
)
from .visualization import draw_matrix, format_value

__all__ = [
    "CODE",
    "build_overview_steps",
    "build_cell_steps",
    "pick_illustrative",
    "best_focus_k",
    "draw_code_panel",
    "render_code_step",
    "draw_code_walkthrough_grid",
    "code_legend_handles",
]


# ---------------------------------------------------------------------------
# «Код як дані»: один елемент списку = один рядок коду. Індекси СТАБІЛЬНІ — саме
# на них посилається мапа підсвічування `hl`. Дослівно повторює серце
# `core.floyd_warshall_steps` (зайве для навчання — як коментар-псевдокод).
# ---------------------------------------------------------------------------
CODE: List[str] = [
    "dist = adjacency_to_inf(adj)",              # 0  init: прямі ребра, ∞ де немає
    "nxt  = next_hops(dist)",                    # 1  init: перша вершина шляху
    "",                                          # 2
    "for k in range(n):",                        # 3  ← оглядовий крок
    "    for i in range(n):",                    # 4
    "        for j in range(n):",                # 5
    "            via_k = dist[i][k] + dist[k][j]",   # 6  ← обчислення
    "            if via_k < dist[i][j]:",        # 7  ← перевірка (гілка)
    "                dist[i][j] = via_k",        # 8  ← гілка «оновити»
    "                nxt[i][j] = nxt[i][k]",     # 9  ← гілка «оновити»
    "            # else: лишаємо старе значення",   # 10 ← гілка «без змін»
]

# Семантичні набори рядків для `hl` (значення — кольори зі style.py):
_HL_INIT = {0: HL_ACTIVE, 1: HL_ACTIVE}                       # ініціалізація
_HL_LOOPS = {3: HL_ACTIVE, 4: HL_ACTIVE, 5: HL_ACTIVE}        # «крутяться» всі цикли
_HL_TEST = {6: HL_ACTIVE, 7: HL_ACTIVE}                       # обчислили via_k і перевіряємо
_HL_IMPROVE = {6: HL_ACTIVE, 7: HL_ACTIVE, 8: HL_ADD, 9: HL_ADD}  # умова істинна → оновлюємо
_HL_NOCHANGE = {6: HL_ACTIVE, 7: HL_ACTIVE, 10: HL_SKIP}      # умова хибна → без змін


# ---------------------------------------------------------------------------
# Дрібні допоміжні
# ---------------------------------------------------------------------------
def _pair(a: float, b: float) -> str:
    """``a+b`` для формули; від'ємний доданок беремо в дужки (``4+(-2)``)."""
    sb = "(" + format_value(b) + ")" if (b != INF and b < 0) else format_value(b)
    return format_value(a) + "+" + sb


def best_focus_k(adj: List[List[float]]) -> int:
    """Індекс проміжної вершини ``k``, що покращує НАЙБІЛЬШЕ відстаней.

    Зручний автодобір «найцікавішого» кроку для детального розбору по клітинках.
    """
    _, _, snaps = floyd_warshall_steps(adj)
    return max(range(len(adj)), key=lambda k: len(snaps[k + 1]["changed"]))


# ---------------------------------------------------------------------------
# Блок 1 — журнал кроків (знімки НЕЗМІННІ: копіюємо мутабельне)
# ---------------------------------------------------------------------------
def build_overview_steps(adj: List[List[float]], labels: Sequence[str]) -> List[Dict]:
    """Оглядовий журнал: один крок на проміжну вершину ``k``.

    Знімки беремо з :func:`core.floyd_warshall_steps` (вони вже є копіями).
    """
    _, _, snaps = floyd_warshall_steps(adj)
    steps: List[Dict] = [{
        "kind": "init",
        "hl": dict(_HL_INIT),
        "matrix": snaps[0]["matrix"],
        "pivot": None, "changed": set(), "current": None,
        "title": t("Початок"),
        "caption": t("Ініціалізація: D = прямі ребра (∞ де немає), nxt — перша вершина шляху"),
    }]
    for snap in snaps[1:]:
        k = snap["k"]
        kn = labels[k]
        n_imp = len(snap["changed"])
        caption = (t("Відкрили {k}: внутрішні цикли покращили {n} відстаней").format(k=kn, n=n_imp)
                   if n_imp else t("Відкрили {k}: коротших шляхів не знайшлося").format(k=kn))
        steps.append({
            "kind": "k",
            "hl": dict(_HL_LOOPS),
            "matrix": snap["matrix"],
            "pivot": k, "changed": snap["changed"], "current": None,
            "title": t("Після відкриття {k}").format(k=kn),
            "caption": caption,
        })
    return steps


def build_cell_steps(adj: List[List[float]], focus_k: int, labels: Sequence[str]) -> List[Dict]:
    """Детальний журнал для одного ``k``: крок = одна пара ``(i, j)``.

    Відтворюємо подвійний цикл руками зі стану «до кроку ``k``», після кожної
    пари кладемо знімок-**копію** з мапою ``hl``, що кодує спрацьовану гілку.
    Наприкінці звіряємося з офіційним знімком алгоритму (``assert``).
    """
    n = len(labels)
    _, _, snaps = floyd_warshall_steps(adj)
    snap = snaps[focus_k + 1]            # знімок «після відкриття focus_k»
    work = deepcopy(snap["prev"])        # стан ДО кроку focus_k
    kn = labels[focus_k]

    steps: List[Dict] = [{
        "kind": "k",
        "hl": dict(_HL_LOOPS),
        "matrix": deepcopy(work),
        "pivot": focus_k, "changed": set(), "current": None,
        "title": t("k = {k}: стан до кроку").format(k=kn),
        "caption": t("Відкриваємо {k}; два внутрішні цикли перебиратимуть усі пари (i, j)").format(k=kn),
    }]

    changed: Set[Tuple[int, int]] = set()
    for i in range(n):
        for j in range(n):
            structural = (i == focus_k or j == focus_k or i == j)
            a, b = labels[i], labels[j]
            old = work[i][j]
            dik, dkj = work[i][focus_k], work[focus_k][j]
            via = dik + dkj
            # реальна умова коду — перевіряємо ВСІ клітинки (у від'ємному циклі
            # покращитися може навіть рядок/стовпець k, коли D[k][k] < 0)
            improved = via < old
            if improved:
                work[i][j] = via
                changed.add((i, j))

            if improved:
                kind, hl = "improve", dict(_HL_IMPROVE)
                caption = t("({a},{b}): D = min({old}, {expr}) = {new}  ✔ оновлено").format(
                    a=a, b=b, old=format_value(old), expr=_pair(dik, dkj), new=format_value(via))
            elif structural:
                kind, hl = "skip", dict(_HL_NOCHANGE)
                caption = t("({a},{b}): рядок/стовпець {k} або діагональ — покращити не може").format(
                    a=a, b=b, k=kn)
            else:
                kind, hl = "nochange", dict(_HL_NOCHANGE)
                caption = t("({a},{b}): D = min({old}, {expr}) = {old}  — без змін").format(
                    a=a, b=b, old=format_value(old), expr=_pair(dik, dkj))

            steps.append({
                "kind": kind, "hl": hl,
                "matrix": deepcopy(work),
                "pivot": focus_k, "changed": set(changed), "current": (i, j),
                "title": t("k = {k}: перебір пар (i, j)").format(k=kn),
                "caption": caption,
            })

    # безпека: ручний прохід має давати рівно те саме, що й алгоритм
    assert work == snap["matrix"] and changed == snap["changed"], "скан не збігся зі знімком"

    steps.append({
        "kind": "final",
        "hl": {},
        "matrix": deepcopy(work),
        "pivot": focus_k, "changed": set(changed), "current": None,
        "title": t("k = {k}: підсумок кроку").format(k=kn),
        "caption": t("Готово: {k} покращила {n} відстаней").format(k=kn, n=len(changed)),
    })
    return steps


def pick_illustrative(steps: List[Dict]) -> List[Dict]:
    """Кураторський зріз журналу по клітинках для СТАТИЧНОЇ сітки.

    Лишає контекст-крок ``k``, по одному показовому прикладу «пропуск» і «без
    змін», УСІ покращення та підсумок — щоб сітка була читомою (а не на n² рядків).
    Повний журнал (усі пари) лишаємо для анімації.
    """
    out: List[Dict] = []
    seen = {"skip": 0, "nochange": 0}
    for s in steps:
        kind = s["kind"]
        if kind in ("init", "k", "improve", "final"):
            out.append(s)
        elif kind in ("skip", "nochange") and seen[kind] < 1:
            out.append(s)
            seen[kind] += 1
    return out


# ---------------------------------------------------------------------------
# Блок 2 — кодова панель (ліворуч)
# ---------------------------------------------------------------------------
def draw_code_panel(ax, highlights: Dict[int, str], code: Sequence[str] = CODE,
                    *, fontsize: float = 10.5) -> None:
    """Малює ``code`` на осі ``ax`` і підсвічує рядки за мапою ``highlights``.

    :param highlights: ``{індекс_рядка: колір_заливки}`` зі знімка журналу.
    Рендер **чистий**: та сама мапа → та сама картинка, без знання про алгоритм.
    Кожен рядок проганяється через :func:`t` (коментар перекладеться, чистий код —
    лишиться незмінним обома мовами).
    """
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    nlines = len(code)
    line_h = 1.0 / nlines
    for i, line in enumerate(code):
        y = 1.0 - (i + 0.5) * line_h
        if i in highlights:
            ax.add_patch(Rectangle((0, y - line_h * 0.46), 1, line_h * 0.92,
                                   facecolor=highlights[i], edgecolor="none", zorder=0))
        ax.text(0.02, y, t(line), family="monospace", fontsize=fontsize,
                va="center", ha="left", color=TEXT_DARK, zorder=2)


def code_legend_handles() -> List[Patch]:
    """Хендли легенди підсвічування коду (для ``fig.legend``)."""
    return [
        Patch(facecolor=HL_ACTIVE, edgecolor="none", label=t("активний рядок")),
        Patch(facecolor=HL_ADD, edgecolor="none", label=t("оновлення (D покращилося)")),
        Patch(facecolor=HL_SKIP, edgecolor="none", label=t("без змін")),
    ]


def _caption_color(kind: str) -> str:
    """Колір підпису-вердикту за типом кроку."""
    if kind == "improve":
        return GREEN_TXT
    if kind == "skip":
        return MUTED_TXT
    return TEXT_FORMULA


# ---------------------------------------------------------------------------
# Композитор — одна фігура на крок (анімація) + повна сітка (статика)
# ---------------------------------------------------------------------------
def render_code_step(step: Dict, labels: Sequence[str], *,
                     figsize: Tuple[float, float] = (10.5, 3.9),
                     code: Sequence[str] = CODE):
    """Один крок → одна фігура ``[код | матриця]`` (кадр для анімації).

    :returns: об'єкт ``Figure``.
    """
    fig, (axc, axr) = plt.subplots(1, 2, figsize=figsize,
                                   gridspec_kw={"width_ratios": [1.25, 1]})
    draw_code_panel(axc, step["hl"], code)
    draw_matrix(axr, step["matrix"], labels, step["title"],
                pivot=step["pivot"], changed=step["changed"], current=step.get("current"))
    if step.get("caption"):
        fig.text(0.5, 0.025, step["caption"], ha="center", va="bottom",
                 fontsize=10, family="monospace", color=_caption_color(step["kind"]))
    fig.subplots_adjust(left=0.03, right=0.97, top=0.95, bottom=0.12, wspace=0.08)
    return fig


def draw_code_walkthrough_grid(steps: List[Dict], labels: Sequence[str], suptitle: str,
                               *, code: Sequence[str] = CODE,
                               row_h: float = 3.55, width: float = 11.0,
                               legend: bool = True):
    """Усі ``steps`` у ОДНІЙ високій сітці: рядок = ``[код | матриця]``.

    :param steps: журнал (повний або кураторський зріз :func:`pick_illustrative`).
    :returns: об'єкт ``Figure``.
    """
    nrow = len(steps)
    fig, axes = plt.subplots(nrow, 2, figsize=(width, row_h * nrow),
                             gridspec_kw={"width_ratios": [1.25, 1]})
    if nrow == 1:
        axes = [axes]
    for r, step in enumerate(steps):
        axc, axr = axes[r]
        draw_code_panel(axc, step["hl"], code)
        draw_matrix(axr, step["matrix"], labels, step["title"],
                    pivot=step["pivot"], changed=step["changed"], current=step.get("current"))
        if step.get("caption"):
            axr.text(0.5, -0.06, step["caption"], transform=axr.transAxes,
                     ha="center", va="top", fontsize=9, family="monospace",
                     color=_caption_color(step["kind"]), clip_on=False)

    fig.suptitle(suptitle, fontsize=14, fontweight="bold")
    bottom = 0.04 if legend else 0.01
    if legend:
        fig.legend(handles=code_legend_handles(), loc="lower center", ncol=3,
                   frameon=False, fontsize=10, bbox_to_anchor=(0.5, 0.002))
    fig.tight_layout(rect=(0, bottom, 1, 0.985), h_pad=5.5)
    return fig
