# Плейбук: i18n підписів + генерація відео/анімацій для проєктів-візуалізацій

> Перенесена «з коробки» інструкція, витягнута з проєкту **algo-krustal-mst**.
> Описує два повторно використовувані прийоми:
> 1. **Легка двомовність (i18n)** підписів на схемах matplotlib + двомовний README.
> 2. **Генерація анімацій** із кадрів → збереження у **GIF (завжди) + MP4 (за наявності ffmpeg)**.
>
> Підходить для будь-якого проєкту, що генерує статичні схеми / анімації через
> `matplotlib` (+ за потреби `networkx`) і публікує їх у README. Усе тут — без важких
> інструментів (без `gettext`/`.po`, без зовнішніх відеоредакторів, без `sudo`).

---

## 0. Ментальна модель (архітектура за 1 хвилину)

Сім принципів, на яких тримаються обидва прийоми. Скопіюйте саме їх — решта деталей похідні.

1. **Один пакет візуалізацій із пласким публічним API.** Внутрішньо поділений на підпапки
   за роллю (`core/`, `figures/`, `steps/`, `proofs/`, `anim/`), але назовні — один плаский
   простір імен: `from mypkg.viz import draw_graph, build_x_animation, ...`. Підпапки —
   деталь реалізації, споживач про них не знає.
2. **Один модуль палітри — єдине джерело правди для кольорів** (`viz/core/palette.py`).
   Жодних хардкод-кольорів у фігурах. Зміна стилю = правка одного файлу.
3. **Кожна статична схема — це функція, що повертає `fig`** (об'єкт `matplotlib.figure.Figure`).
   Функція *не зберігає* файл і *не закриває* фігуру — це робить оркестратор.
4. **Кожна анімація — це функція, що повертає `(fig, anim)`** (готовий `FuncAnimation`).
   Так само: не зберігає, не закриває.
5. **Увесь текст, видимий людині, обгорнутий у `t(...)`** — заголовки, легенди, підписи,
   анотації. Без винятків (навіть однолітерні префікси).
6. **Один скрипт-оркестратор** (`scripts/generate_images.py`): обирає мову з аргументів →
   `set_lang()` → визначає теку виводу → викликає кожен білдер → `save()` / `save_anim()`.
7. **Два файли README** (мова за замовчуванням + переклад) з рядком-перемикачем зверху;
   переклад посилається на `images/en/...`.

### Розкладка тек (цільова)

```
.
├── README.md                     # основна мова (тут: UA) — посилається на images/*
├── README.en.md                  # переклад (EN) — посилається на images/en/*
├── images/                       # згенеровані схеми мовою за замовчуванням (uk)
│   ├── *.png  *.gif  *.mp4
│   └── en/                       # ті самі схеми, але англійською
│       └── *.png  *.gif  *.mp4
├── scripts/
│   └── generate_images.py        # ЄДИНА точка входу регенерації всіх медіа
├── src/mypkg/
│   ├── ...                        # сам алгоритм / логіка (без візуалізацій)
│   └── viz/
│       ├── __init__.py            # плаский публічний API (re-export усього)
│       ├── core/
│       │   ├── i18n.py            # ❶ серце двомовності: t(), set_lang(), _EN
│       │   └── palette.py         # єдина палітра кольорів
│       ├── figures/               # окремі статичні схеми (кожна → fig)
│       ├── steps/                 # покрокові розбори + збірка в сітку
│       ├── proofs/                # схеми-доведення
│       └── anim/                  # ❷ анімації (кожна → (fig, anim))
├── pyproject.toml                 # extras: [video] = imageio-ffmpeg
└── requirements.txt
```

---

## ❶ Інтернаціоналізація (i18n)

### 1.1 Головна ідея: «вихідний рядок — це і є ключ»

Замість `gettext`/`.po`-файлів та цифрових/символьних ключів використовується
**сам український рядок як ключ** у словнику перекладів. Наслідки:

- **Мова за замовчуванням лишається байт-у-байт незмінною.** Коли `LANG == "uk"`,
  функція `t(s)` повертає `s` *без жодного пошуку*. Тобто UA-вивід ідентичний тому,
  що був би й без i18n узагалі — нульовий ризик регресій під час впровадження.
- **Відсутній переклад «деградує» безпечно** до вихідного рядка (`_EN.get(s, s)`):
  забули перекласти — отримаєте український підпис, а не `KeyError` чи `"???"`.
- **Ключі самодокументовані.** Дивлячись на словник, одразу видно повний текст обома мовами.
- **Нуль інфраструктури.** Один Python-файл, жодних білд-кроків, жодних залежностей.

Платою є: ключі довгі; якщо змінити вихідний рядок у фігурі — треба синхронно змінити
ключ у словнику (інакше переклад «відклеїться» і тихо впаде назад на UA). Для проєкту
з десятками підписів це прийнятно; для тисяч — беріть `gettext`.

### 1.2 Модуль `viz/core/i18n.py` (шаблон для копіювання)

```python
# -*- coding: utf-8 -*-
"""Двомовні підписи для схем (uk за замовчуванням / en).

t(s) повертає s для мови за замовчуванням або переклад для іншої.
Ключ — сам вихідний (український) рядок, тож UA-вивід лишається байт-у-байт
незмінним: коли LANG == "uk", функція повертає аргумент без змін.

Оркестратор перемикає мову через set_lang("en") і кладе схеми в images/en/.
Рядки з {плейсхолдерами} використовуються як t(шаблон).format(...).
"""
from __future__ import annotations

LANG = "uk"  # мова за замовчуванням (= вихідна мова рядків-ключів)


def set_lang(lang: str) -> None:
    """Встановити мову підписів: "uk" (типово) або "en"."""
    global LANG
    assert lang in ("uk", "en"), lang
    LANG = lang


#: Вихідний (uk) рядок -> переклад (en). Лише те, що реально потрапляє у схеми.
_EN = {
    "Вихідний зважений граф": "Input weighted graph",
    "Мінімальне остовне дерево (вага {total})": "Minimum spanning tree (weight {total})",
    "корінь": "root",
    "р": "r",  # навіть однолітерний префікс рангу (рN -> rN) йде через словник
    # ... один рядок на кожен видимий людині підпис ...
}


def t(s: str) -> str:
    """Повернути підпис мовою LANG (ключ — вихідний рядок)."""
    if LANG == "uk":
        return s            # мова за замовчуванням: жодного пошуку, байт-у-байт
    return _EN.get(s, s)    # відсутній ключ -> безпечно повертаємо вихідний рядок
```

> 💡 Щоб додати третю мову — додайте `_DE = {...}` і розгалуження в `t()`
> (або словник словників `{"en": _EN, "de": _DE}` і `TABLES.get(LANG, {}).get(s, s)`).

### 1.3 Правила вживання `t()` у коді фігур

```python
from ..core.i18n import t

# 1) Звичайний підпис — просто обгортаємо літерал:
ax.set_title(t("Вихідний зважений граф"))

# 2) Підпис із підстановкою — обгортаємо ШАБЛОН, потім .format():
ax.set_title(t("Мінімальне остовне дерево (вага {total})").format(total=total))
#            ^ перекладається шаблон цілком (з {total}), а не зібраний рядок

# 3) Легенда — кожен label через t():
handles = [Patch(facecolor=C_NODE, label=t("корінь (сам собі батько)")),
           Patch(facecolor=C_MST,  label=t("знайдений корінь"))]

# 4) Навіть дрібні/складені підписи:
ax.annotate(f"{t('корінь')}, {t('ранг')} {rank[n]}", ...)
ax.set_title(f"{t('Крок')} {i + 1}/{len(STATES)}:  {t(st['desc'])}")
```

**Залізні правила:**
- Обгортайте **шаблон**, а не результат: `t("...{x}...").format(x=v)`, ніколи `t(f"...{v}...")`
  (інакше ключ щоразу інакший — переклад не знайдеться).
- Ключ у словнику має збігатися **символ-у-символ**, включно з пробілами, переносами `\n`,
  типом тире (`–` en-dash ≠ `-` дефіс) та стрілками (`→`, `->`). Це найчастіше джерело
  «чомусь не перекладається».
- Текст-дані (наприклад, поле `desc` у кадрах анімації) теж проганяйте через `t()` у місці
  виводу: `t(st["desc"])`. Тоді у словнику ключем буде цілий рядок опису.

### 1.4 Перемикання мови + маршрутизація виводу

Вся «магія» — три рядки в оркестраторі (повний скрипт див. §3):

```python
from mypkg.viz.core.i18n import set_lang
LANG = "en" if "en" in sys.argv[1:] else "uk"     # мова з аргументів CLI
set_lang(LANG)                                     # глобально перемикає t()
IMAGES = os.path.join(ROOT, "images", "en") if LANG == "en" else os.path.join(ROOT, "images")
```

Запуск:
```bash
python scripts/generate_images.py        # uk -> images/
python scripts/generate_images.py en     # en -> images/en/
```

Той самий код фігур, той самий білдер — змінюється лише глобальний `LANG`, і всі `t()`
всередині повертають переклад. Жодна функція-фігура не знає про мову.

### 1.5 Чек-лист впровадження i18n у новому проєкті

- [ ] Створити `viz/core/i18n.py` за шаблоном (§1.2) з порожнім `_EN = {}`.
- [ ] Прогнати по всіх модулях фігур: обгорнути **кожен** видимий літерал у `t(...)`
      (заголовки, легенди, анотації, осі). Шаблони — через `t(...).format(...)`.
- [ ] Наповнити `_EN` перекладами (ключ = точний вихідний рядок).
- [ ] В оркестраторі додати читання мови з argv + `set_lang()` + розгалуження теки виводу.
- [ ] Перевірити: запуск без аргументу дає **байт-у-байт** ті самі файли, що й до правок
      (git diff на `images/*.png` має бути порожнім, якщо нічого не змінювали).
- [ ] Запустити з `en` → переконатися, що `images/en/` заповнюється перекладеними схемами.

---

## ❷ Генерація відео / анімацій

### 2.1 Головна ідея: декларативні кадри + `FuncAnimation`

Анімація описується як **список кадрів-станів** (звичайні `dict` з даними) і **чиста
функція рендера** `draw(ax, i)`, що очищає вісь і перемальовує її зі стану `frames[i]`.
Жодного мутабельного стану між кадрами — кадр `i` повністю визначається `frames[i]`.
Це робить анімації передбачуваними, придатними до діффу та легко редагованими
(додати крок = вставити один `dict`).

### 2.2 Скелет білдера анімації (шаблон для копіювання)

```python
# -*- coding: utf-8 -*-
"""Анімація <щось>. build_x_animation() повертає (fig, anim) —
готовий FuncAnimation для збереження у GIF (Pillow) чи MP4 (ffmpeg)."""
from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.animation import FuncAnimation
from ..core.i18n import t
from ..core.palette import C_NODE, C_NODE_EDGE, C_MST   # кольори — лише з палітри

# 1) Кожен кадр — звичайні дані (декларативно). desc піде через t() при рендері.
FRAMES = [
    dict(desc="Старт: ...", state={...}),
    dict(desc="Крок 1: ...", state={...}, highlight=(...)),
    # ... додати крок = додати dict ...
]


# 2) Чистий рендер кадру i на вісь: очистити -> намалювати зі FRAMES[i].
def _draw(ax, i):
    ax.clear()
    fr = FRAMES[i]
    # ... малюємо за fr["state"]; усі кольори з палітри ...
    ax.set_title(f"{t('Крок')} {i + 1}/{len(FRAMES)}:  {t(fr['desc'])}", fontsize=11)
    ax.set_axis_off()
    handles = [Patch(facecolor=C_NODE, edgecolor=C_NODE_EDGE, label=t("звичайний вузол")),
               Patch(facecolor=C_MST,  edgecolor=C_NODE_EDGE, label=t("результат"))]
    ax.legend(handles=handles, loc="upper left", fontsize=8.5, frameon=False)


# 3) Білдер повертає (fig, anim). НЕ зберігає файл, НЕ закриває фігуру.
def build_x_animation():
    fig, ax = plt.subplots(figsize=(7.6, 5.2))
    fig.subplots_adjust(top=0.86, bottom=0.04)
    anim = FuncAnimation(fig, lambda i: _draw(ax, i), frames=len(FRAMES), interval=2000)
    return fig, anim          # interval (мс) — для інтерактивного перегляду; для файлу
                              # реальну швидкість задає fps під час save (див. §2.3)
```

Реальні приклади в репозиторії: `viz/anim/dsu_anim.py` (об'єднання за рангом + стиснення
шляху на 5 вузлах), `viz/anim/bfs_anim.py` (два BFS-обходи: «шлях знайдено» / «недосяжно»).
Зверніть увагу, як стан кадру тримає не лише дані для малювання, а й семантичні маркери
(`new`, `climb`, `comp`, `found`, `cur`, `queue`, `done`), за якими рендер обирає колір
із палітри.

### 2.3 Збереження: GIF завжди + MP4 за можливості — хелпер `save_anim`

```python
def save_anim(fig, anim, basename, fps=0.5):
    """Зберегти анімацію як GIF (Pillow, завжди) і MP4 (ffmpeg, якщо є).

    fps=0.5  ->  0.5 кадру/с  ->  ~2 секунди на кадр (зручно для навчальних схем).
    """
    gif = os.path.join(IMAGES, basename + ".gif")
    anim.save(gif, writer="pillow", fps=fps, dpi=110)      # Pillow є завжди (через matplotlib)
    print("  ->", gif)
    try:
        mp4 = os.path.join(IMAGES, basename + ".mp4")
        anim.save(mp4, writer="ffmpeg", fps=fps, dpi=130)  # MP4 — лише якщо є ffmpeg
        print("  ->", mp4)
    except Exception as exc:                               # ffmpeg немає -> GIF усе одно є
        print(f"  ({basename}.mp4 пропущено — встанови ffmpeg для відео):", exc)
    plt.close(fig)                                         # закриваємо саме тут, не в білдері
```

Чому два формати:
- **GIF** (writer `pillow`) — працює **скрізь без додаткових залежностей** (Pillow тягнеться
  разом із matplotlib), рендериться інлайн у будь-якому README/GitHub. Це «гарантований» формат.
- **MP4** (writer `ffmpeg`) — менший за розміром і дає **плеєр із контролами** на GitHub,
  але потребує `ffmpeg`. Тому загорнутий у `try/except`: немає ffmpeg → MP4 тихо пропускається,
  GIF лишається. Білд ніколи не падає через відсутність ffmpeg.

### 2.4 ffmpeg без `sudo` (через `imageio-ffmpeg`) + headless-рендер

Щоб MP4 збиралися **без системного ffmpeg і без root**, на старті оркестратора підхоплюємо
бінарник, що приходить із pip-пакетом `imageio-ffmpeg`:

```python
import matplotlib
matplotlib.use("Agg")        # headless: рендеримо у файли, без вікон (для CI/серверів)
import matplotlib.pyplot as plt

# MP4 потребує ffmpeg. Пріоритет — системний; інакше беремо бінарник із pip-пакета
# imageio-ffmpeg (без apt/sudo). Немає ні того, ні іншого -> MP4 пропускаються, GIF будуть.
try:
    from matplotlib.animation import FFMpegWriter
    if not FFMpegWriter.isAvailable():
        import imageio_ffmpeg
        plt.rcParams["animation.ffmpeg_path"] = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    pass
```

Встановлення відео-залежності (опційно, без root):
```bash
pip install imageio-ffmpeg        # або: pip install -e ".[video]"  (див. §5)
```
Альтернатива — системний ffmpeg: `apt install ffmpeg` / `brew install ffmpeg` /
`conda install -c conda-forge ffmpeg`. Скрипт сам підхопить будь-який доступний.

### 2.5 Семантика часу (fps vs interval)

- `FuncAnimation(..., interval=2000)` — затримка між кадрами **в інтерактивному перегляді** (мс).
- `anim.save(..., fps=0.5)` — реальна швидкість **у збереженому файлі**: `fps=0.5` = пів кадру
  за секунду = **~2 с на кадр**. Для навчальних анімацій повільно — добре (встигаєш прочитати).
  Для динамічних — підніміть fps (5–15).
- `dpi` під час `save` керує роздільністю: у прикладі GIF=110, MP4=130 (MP4 дешевший за байт,
  тож можна різкіше).

### 2.6 Чек-лист впровадження анімацій

- [ ] Створити `viz/anim/<name>.py` за скелетом (§2.2): `FRAMES` + `_draw(ax, i)` + `build_*()`.
- [ ] Кожен підпис у рендері — через `t()` (заголовок, легенда, анотації, поле `desc`).
- [ ] Кольори — лише з `palette.py`.
- [ ] Білдер повертає `(fig, anim)`, **не** зберігає й **не** закриває фігуру.
- [ ] Реекспортувати білдер у `viz/__init__.py`.
- [ ] В оркестраторі додати `matplotlib.use("Agg")` + bootstrap ffmpeg (§2.4) + виклик `save_anim`.
- [ ] Перевірити: без ffmpeg збираються GIF (і друкується рядок «mp4 пропущено»); з ffmpeg — обидва.

---

## 3. Скрипт-оркестратор (повний шаблон `scripts/generate_images.py`)

```python
# -*- coding: utf-8 -*-
"""Регенерує всі зображення для README у теку images/ (або images/en/).

Запуск:  python scripts/generate_images.py [en]
Працює без встановлення пакета — додає src/ у шлях самостійно.
"""
from __future__ import annotations

import os
import sys

import matplotlib
matplotlib.use("Agg")            # без вікон, лише запис у файли
import matplotlib.pyplot as plt

# дозволяємо імпорт пакета з src/ без встановлення
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
plt.rcParams["font.family"] = "DejaVu Sans"   # шрифт із гліфами і uk, і en

# Bootstrap ffmpeg для MP4 без sudo (див. §2.4)
try:
    from matplotlib.animation import FFMpegWriter
    if not FFMpegWriter.isAvailable():
        import imageio_ffmpeg
        plt.rcParams["animation.ffmpeg_path"] = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    pass

# Плаский публічний API пакета візуалізацій
from mypkg.viz import (
    my_figure, another_figure,
    build_x_animation, build_y_animation,
)
from mypkg.viz.core.i18n import set_lang, t

# --- вибір мови + маршрут теки виводу ---
LANG = "en" if "en" in sys.argv[1:] else "uk"
set_lang(LANG)
IMAGES = os.path.join(ROOT, "images", "en") if LANG == "en" else os.path.join(ROOT, "images")
os.makedirs(IMAGES, exist_ok=True)


def save(fig, name, dpi=110):
    path = os.path.join(IMAGES, name)
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print("  ->", os.path.relpath(path, ROOT))


def save_anim(fig, anim, basename, fps=0.5):
    """GIF (Pillow, завжди) + MP4 (ffmpeg, якщо є). Див. §2.3."""
    gif = os.path.join(IMAGES, basename + ".gif")
    anim.save(gif, writer="pillow", fps=fps, dpi=110)
    print("  ->", os.path.relpath(gif, ROOT))
    try:
        mp4 = os.path.join(IMAGES, basename + ".mp4")
        anim.save(mp4, writer="ffmpeg", fps=fps, dpi=130)
        print("  ->", os.path.relpath(mp4, ROOT))
    except Exception as exc:
        print(f"  ({basename}.mp4 пропущено — встанови ffmpeg):", exc)
    plt.close(fig)


def main():
    print(f"Генерація зображень ({LANG}):")

    # --- статичні схеми: save(builder(), "name.png") ---
    save(my_figure(), "my_figure.png")
    # підпис із підстановкою формується всередині фігури через t(...).format(...),
    # або тут — якщо потрібен внутрішній текст:
    save(another_figure(), "another.png")

    # --- анімації: GIF + (опційно) MP4 ---
    for builder, name in [
        (build_x_animation, "x_anim"),
        (build_y_animation, "y_anim"),
    ]:
        fig, anim = builder()
        save_anim(fig, anim, name)

    print("Готово.")


if __name__ == "__main__":
    main()
```

**Дворазовий запуск регенерує обидві мови:**
```bash
python scripts/generate_images.py        # -> images/      (uk)
python scripts/generate_images.py en     # -> images/en/   (en)
```

---

## 4. Двомовний README (споживацька сторона)

### 4.1 Рядок-перемикач мови (зверху обох файлів)

`README.md` (мова за замовчуванням, UA):
```markdown
# 🌳 Заголовок проєкту

**🇺🇦 Українська**  ·  [🇬🇧 English](README.en.md)
```

`README.en.md` (переклад, EN) — дзеркально, активна позначена жирним:
```markdown
# 🌳 Project Title

[🇺🇦 Українська](README.md)  ·  **🇬🇧 English**
```

### 4.2 Вбудовування медіа

- **Статичні схеми та анімації** вставляються звичайним markdown-синтаксисом зображення —
  GIF теж так (GitHub програє його інлайн):
  ```markdown
  ![Вихідний зважений граф](images/graph.png)
  ![Як будується структура зсередини](images/dsu_build.gif)
  ```
- **EN-версія посилається на `images/en/...`** — ті самі імена файлів, інша тека:
  ```markdown
  ![Input weighted graph](images/en/graph.png)
  ![How the structure is built](images/en/dsu_build.gif)
  ```
- **MP4 кладеться поряд** (те саме базове ім'я, `.mp4`) як важчий, але якісніший формат
  для завантаження/перегляду з контролами. Інлайн у README достатньо GIF — він
  гарантовано рендериться без `<video>`-тегів.

> Підказка щодо синхронності: тримайте **однакові імена файлів** у `images/` та `images/en/`.
> Тоді переклад README — це механічна заміна шляху `images/` → `images/en/` і самого тексту.

---

## 5. Залежності та конфіг проєкту

`requirements.txt` (мінімум):
```
networkx>=3.2        # лише якщо малюєте графи; інакше не потрібен
matplotlib>=3.7
```

`pyproject.toml` — винесіть ffmpeg в опційний extra, щоб базова установка лишалась легкою:
```toml
[project]
dependencies = [
    "networkx>=3.2",
    "matplotlib>=3.7",
]

[project.optional-dependencies]
# Рендер анімацій у .mp4 без системного ffmpeg.
video = ["imageio-ffmpeg>=0.4"]

[tool.setuptools]
package-dir = { "" = "src" }

[tool.setuptools.packages.find]
where = ["src"]
```

Установка:
```bash
pip install -e .            # базово: PNG + GIF
pip install -e ".[video]"  # + MP4 без sudo (тягне imageio-ffmpeg)
```

---

## 6. Покрокова міграція в НОВИЙ проєкт (швидкий рецепт)

1. **Скопіюйте каркас пакета:** `src/<pkg>/viz/{__init__.py, core/palette.py, core/i18n.py}`.
   Палітру підженіть під свій стиль; `i18n.py` візьміть із §1.2 з порожнім `_EN`.
2. **Винесіть кольори** всіх наявних схем у `palette.py` (жодних хардкодів у фігурах).
3. **Зробіть кожну схему функцією, що повертає `fig`**; кожну анімацію — функцією, що
   повертає `(fig, anim)` (скелет §2.2). Реекспортуйте все плоско з `viz/__init__.py`.
4. **Обгорніть увесь видимий текст у `t(...)`** (правила §1.3). Спочатку — лишаючи `_EN`
   порожнім: вивід має лишитися ідентичним (перевірка байт-у-байт).
5. **Напишіть `scripts/generate_images.py`** за §3 (Agg + bootstrap ffmpeg + `save`/`save_anim`
   + вибір мови з argv + маршрут теки).
6. **Наповніть `_EN`** перекладами. Запустіть `... generate_images.py en` → отримайте `images/en/`.
7. **Створіть `README.en.md`**, додайте рядок-перемикач (§4.1) в обидва README, переведіть
   шляхи на `images/en/` у перекладі.
8. **Додайте extra `[video]`** у `pyproject.toml` (§5). Готово.

---

## 7. Граблі та засвоєні уроки

- **Тире та стрілки.** En-dash `–`, дефіс `-`, мінус `−` — різні символи. Так само `→` vs `->`.
  Ключ у `_EN` мусить збігатися рівно з рядком у коді, інакше переклад тихо впаде на UA.
  Найшвидший спосіб упіймати — генерувати `en` і шукати в результаті український текст.
- **Шаблон, а не результат.** `t("...{x}...").format(x=v)`, ніколи `t(f"...{v}...")`.
- **`matplotlib.use("Agg")` — до `import matplotlib.pyplot`.** Інакше на сервері/у CI впаде
  через відсутність дисплея.
- **Шрифт із потрібними гліфами.** `plt.rcParams["font.family"] = "DejaVu Sans"` — він має
  і латиницю, і кирилицю, і типографські тире/стрілки. Інакше — «прямокутники» в підписах.
- **Білдер не зберігає й не закриває.** Збереження та `plt.close(fig)` — лише в `save`/`save_anim`.
  Закриєте фігуру в білдері — `anim.save` впаде.
- **GIF — обов'язковий, MP4 — бонус.** Ніколи не робіть білд залежним від ffmpeg: лише
  `try/except` навколо MP4. GIF (Pillow) є завжди.
- **`fps` керує часом у файлі, `interval` — лише в інтерактиві.** Для навчальних схем `fps=0.5`.
- **Однакові імена файлів у `images/` та `images/en/`** — переклад README стає механічним.
- **Тримайте `LANG` глобальним і єдиним.** Жодна функція-фігура не приймає мову параметром —
  лише читає глобальний стан через `t()`. Це те, що робить перемикання однорядковим.

---

*Джерело прийомів: проєкт `algo-krustal-mst` (двомовний навчальний розбір алгоритму Краскала).
Релевантні файли-приклади: `src/kruskal_mst/viz/core/i18n.py`, `.../viz/anim/*.py`,
`.../viz/core/palette.py`, `scripts/generate_images.py`.*
