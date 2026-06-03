"""Smoke-тести: візуалізація та збірка GIF виконуються без помилок.

На відміну від ``test_core.py`` (який перевіряє ЧИСЛА), ці тести не звіряють
«правильність картинки» — лише що кожна функція малювання повертає фігуру й не
кидає винятків, що ``save_gif`` збирає валідний GIF, і що допоміжні утиліти
коректно обробляють крайові випадки (пара без шляху).

Потребують ``matplotlib``, ``networkx`` і ``pillow``.

Запуск::

    pytest
    python tests/test_smoke.py    # вбудований раннер, без pytest
"""

from __future__ import annotations

import io
import os
import sys
import tempfile
from contextlib import redirect_stdout

import matplotlib

matplotlib.use("Agg")  # без графічного дисплея — ДО імпорту pyplot

import matplotlib.pyplot as plt  # noqa: E402

# корінь репозиторію та examples/ у sys.path
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (_ROOT, os.path.join(_ROOT, "examples")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from floyd_warshall.animation import save_gif  # noqa: E402
from floyd_warshall.core import floyd_warshall_steps  # noqa: E402
from floyd_warshall.visualization import (  # noqa: E402
    configure_style,
    draw_airport_progressive,
    draw_airport_progressive_panel,
    draw_airport_relaxation,
    draw_evolution,
    draw_floyd_step,
    draw_graph,
    draw_matrix,
    draw_matrix_standalone,
)
from _common import report_distances  # noqa: E402

# Маленький граф (A, B, C): A→B(3), B→C(1) — достатній для перевірки рендера.
_ADJ = [[0, 3, 0], [0, 0, 1], [0, 0, 0]]
_LABELS = ["A", "B", "C"]
_POS = {0: (0.0, 1.0), 1: (1.0, 1.0), 2: (2.0, 0.0)}


def test_draw_functions_return_figures():
    """Кожна функція малювання відпрацьовує без винятків і дає фігуру."""
    configure_style()
    _, _, snaps = floyd_warshall_steps(_ADJ)

    fig = draw_graph(_ADJ, _POS, _LABELS, title="t", highlight_path=[0, 1, 2])
    assert fig is not None
    plt.close(fig)

    # draw_matrix малює на переданій осі; перевіряємо всі підсвічування разом
    f, ax = plt.subplots()
    draw_matrix(ax, snaps[-1]["matrix"], _LABELS, "t",
                pivot=1, changed={(0, 2)}, prev=snaps[-1]["prev"], current=(0, 2))
    plt.close(f)

    for fig in (
        draw_matrix_standalone(snaps[-1]["matrix"], _LABELS, "t"),
        draw_floyd_step(snaps[2]["matrix"], 1, _LABELS,
                        prev=snaps[2]["prev"], changed=snaps[2]["changed"]),
        draw_evolution(snaps, _LABELS, "t", ncols=4),
        draw_airport_relaxation(),
        draw_airport_progressive(),
        draw_airport_progressive_panel(2),
    ):
        assert fig is not None
        plt.close(fig)


def test_save_gif_creates_valid_gif():
    """save_gif збирає багатокадровий GIF із кількох фігур."""
    from PIL import Image

    frames = []
    for i in range(3):
        fig, ax = plt.subplots(figsize=(2, 2))
        ax.plot([0, 1], [0, i + 1])   # кадри РІЗНІ, інакше GIF злив би їх в один
        ax.set_title(str(i))
        frames.append(fig)

    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "smoke.gif")
        save_gif(frames, out, [200, 200, 200])
        assert os.path.exists(out)
        with Image.open(out) as im:
            assert im.n_frames == 3
            assert im.info.get("loop") == 0


def test_save_gif_rejects_empty():
    """Порожній список кадрів має давати зрозумілий ValueError, а не падати глибше."""
    with tempfile.TemporaryDirectory() as d:
        raised = False
        try:
            save_gif([], os.path.join(d, "x.gif"), 100)
        except ValueError:
            raised = True
        assert raised, "save_gif мав кинути ValueError на порожньому списку"


def test_report_distances_handles_missing_path():
    """#2: пара без шляху (C → A) не повинна валити report_distances."""
    final, nxt, _ = floyd_warshall_steps(_ADJ)
    buf = io.StringIO()
    with redirect_stdout(buf):
        report_distances(final, nxt, _LABELS, [(2, 0)])  # C → A: шляху немає
    assert "не існує" in buf.getvalue()  # надрукувало пояснення, а не впало


def _run_without_pytest():
    """Мінімальний раннер; на відміну від ядра, ловить БУДЬ-ЯКИЙ виняток."""
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failures = 0
    for test in tests:
        try:
            test()
            print(f"PASS  {test.__name__}")
        except Exception as exc:  # noqa: BLE001 — smoke: будь-яка помилка = провал
            failures += 1
            print(f"FAIL  {test.__name__}: {type(exc).__name__}: {exc}")
    print(f"\n{len(tests) - failures}/{len(tests)} smoke-тестів пройдено")
    return failures


if __name__ == "__main__":
    sys.exit(1 if _run_without_pytest() else 0)
