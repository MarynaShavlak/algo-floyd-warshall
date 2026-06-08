# Швидкий старт

**🇺🇦 Українська**  ·  [🇬🇧 English](USAGE.en.md)

> Частина документації проєкту [«Алгоритм Флойда–Воршала: покроковий розбір»](README.md). Тут — команди встановлення, запуску прикладів і тестів. Структуру репозиторію див. у [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md).

> **Потрібен Python ≥ 3.8.** Код використовує `from __future__ import annotations`, тож працює на 3.8+ (розробляється й тестується на 3.12).

```bash
# 1. Залежності
pip install -r requirements.txt
# або встановити пакет у режимі розробки:
pip install -e .
# (опційно) MP4-відео анімацій без root — додає ffmpeg із пакета imageio-ffmpeg:
pip install -e ".[video]"

# 2. Відтворити всі рисунки й текстові виводи (українською → docs/images/)
python examples/00_airport_analogy.py      # аналогія з аеропортами
python examples/01_graph_abcdef.py         # граф A–F
python examples/02_negative_cycle.py       # від'ємний цикл
python examples/03_negative_edges_pqrs.py  # від'ємні ребра
python examples/04_animations.py           # анімації GIF+MP4 (еволюція, шлях, хаби)

# 3. Те саме англійською (→ docs/images/en/) — додайте аргумент `en`:
python examples/00_airport_analogy.py en
python examples/01_graph_abcdef.py en
python examples/04_animations.py en
```

П'ять скриптів разом генерують **24 статичні рисунки** (`.png`), **8 GIF-анімацій** (`.gif`) і **8 MP4-відео** (`.mp4`) у [`docs/images/`](docs/images) та друкують текстові виводи в консоль; з аргументом `en` ті самі медіа англійською потрапляють у [`docs/images/en/`](docs/images/en). Виконуються за кілька секунд. **MP4** кодуються лише за наявності `ffmpeg` (системного або з `imageio-ffmpeg`); без нього збираються самі GIF — збірка не падає.

Перевірити коректність алгоритму (результати звірено з еталонною реалізацією `networkx`):

```bash
python tests/test_core.py     # коректність ядра (без додаткових залежностей)
python tests/test_smoke.py    # smoke: рендер і збірка GIF не падають (matplotlib, pillow)
# або обидва через pytest (pip install -e ".[dev]"):
pytest
```

Тести `test_core.py` покривають збіг з `networkx` на додатних і від'ємних вагах, підтримку ребер нульової ваги, виявлення від'ємного циклу, відновлення шляху через `nxt` та стійкість `reconstruct_path` до від'ємного циклу (без зациклення). Smoke-тести `test_smoke.py` перевіряють, що всі функції малювання та збірка GIF виконуються без помилок, а `report_distances` коректно обробляє пару без шляху.

Мінімальне використання як бібліотеки:

```python
from floyd_warshall import floyd_warshall, reconstruct_path, has_negative_cycle, INF

adj = [
    [0,   3,   INF],
    [INF, 0,   1  ],
    [INF, INF, 0  ],
]
dist = floyd_warshall(adj)        # матриця найкоротших відстаней
```
