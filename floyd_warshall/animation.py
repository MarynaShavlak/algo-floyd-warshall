"""Складання GIF-анімацій із кадрів matplotlib.

Кадри малюють ті самі функції зі :mod:`floyd_warshall.visualization`
(``draw_matrix``, ``draw_graph``, ``draw_airport_progressive_panel`` тощо) —
цей модуль лише «зшиває» готові фігури в один зациклений GIF через Pillow.

Чому окремий модуль: :mod:`floyd_warshall.core` лишається чистим алгоритмом,
:mod:`floyd_warshall.visualization` відповідає за статичні рисунки, а збірка
анімацій (єдине місце, що залежить від Pillow) винесена сюди, щоб не змішувати
відповідальності.

Ключова деталь коректного GIF — **усі кадри мусять мати однаковий розмір у
пікселях**. Тому при рендері кадрів навмисно НЕ використовуємо
``bbox_inches="tight"`` (він обрізає по-різному), а покладаємось на фіксований
``figsize × dpi``. Палітра будується одразу з усіх кадрів, щоб акценти, які
з'являються лише на пізніх кадрах (зелені оновлення, червоний шлях), не
загубилися.
"""

from __future__ import annotations

import io
from typing import List, Sequence, Union

import matplotlib.pyplot as plt
from PIL import Image

from .style import GIF_DPI

__all__ = ["save_gif"]


def _figure_to_image(fig: "plt.Figure", dpi: int) -> Image.Image:
    """Рендерить фігуру matplotlib у растрове зображення (RGB) та закриває її.

    ``bbox_inches`` не задаємо навмисно: розмір кадру має бути сталим
    (``figsize × dpi``), інакше GIF «стрибатиме» між кадрами.
    """
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert("RGB")


def _shared_palette(frames: Sequence[Image.Image], colors: int) -> Image.Image:
    """Будує спільну палітру з УСІХ кадрів.

    Зелені (оновлені клітинки) та червоні (підсвічений шлях) пікселі з'являються
    лише на частині кадрів; якщо взяти палітру з одного кадру, ці кольори можуть
    «злитися» в сірий. Тому складаємо кадри в одне високе полотно й квантуємо
    його разом.
    """
    width = max(f.width for f in frames)
    canvas = Image.new("RGB", (width, sum(f.height for f in frames)), "white")
    y = 0
    for f in frames:
        canvas.paste(f, (0, y))
        y += f.height
    return canvas.quantize(colors=colors, method=Image.Quantize.MEDIANCUT)


def save_gif(
    figures: List["plt.Figure"],
    path: str,
    durations: Union[int, Sequence[int]],
    *,
    dpi: int = GIF_DPI,
    colors: int = 128,
    loop: int = 0,
) -> None:
    """Зшиває список фігур matplotlib у зациклений GIF і зберігає у ``path``.

    Усі передані фігури будуть **закриті** (``plt.close``) у процесі рендера.

    :param figures: кадри анімації — кожен окрема :class:`matplotlib.figure.Figure`.
    :param path: куди зберегти ``.gif``.
    :param durations: тривалість кадру(ів) у мілісекундах — одне число (однаково
        для всіх) або послідовність по одному значенню на кадр.
    :param dpi: роздільність рендера (за замовчуванням нижча за статичні рисунки).
    :param colors: розмір спільної палітри GIF.
    :param loop: кількість повторів; ``0`` — нескінченний цикл.
    """
    if not figures:
        raise ValueError("save_gif: немає жодного кадру для анімації.")

    frames = [_figure_to_image(fig, dpi) for fig in figures]
    size = frames[0].size
    frames = [f if f.size == size else f.resize(size) for f in frames]

    palette = _shared_palette(frames, colors)
    paletted = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]

    paletted[0].save(
        path,
        save_all=True,
        append_images=paletted[1:],
        duration=list(durations) if not isinstance(durations, int) else durations,
        loop=loop,
        optimize=True,
        disposal=2,  # кожен кадр повністю замінює попередній (без «привидів»)
    )
