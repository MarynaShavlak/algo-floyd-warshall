# -*- coding: utf-8 -*-
"""Двомовні підписи для візуалізацій (uk за замовчуванням / en).

Замість важкої інфраструктури ``gettext``/``.po`` тут застосовано прийом
**«вихідний рядок — це і є ключ»**: ключем у словнику перекладів виступає сам
український рядок. Наслідки:

* **Мова за замовчуванням лишається байт-у-байт незмінною.** Коли ``LANG == "uk"``,
  :func:`t` повертає аргумент *без жодного пошуку* — український вивід (і всі
  раніше згенеровані рисунки) ідентичні тим, що були б і без i18n узагалі.
* **Відсутній переклад «деградує» безпечно** до вихідного рядка (``_EN.get(s, s)``):
  забули перекласти — отримаєте український підпис, а не ``KeyError`` чи ``"???"``.
* **Нуль інфраструктури** — один Python-файл, жодних білд-кроків.

Оркестратор (скрипти ``examples/``) перемикає мову через :func:`set_lang`
(``"en"`` із аргументів CLI) і кладе рисунки в ``docs/images/en/``. Той самий код
малювання, той самий білдер — змінюється лише глобальний ``LANG``, і всі виклики
:func:`t` всередині повертають переклад. Жодна функція-фігура не знає про мову.

Правила вживання у коді фігур:

* обгортайте **шаблон**, а не результат: ``t("…{x}…").format(x=v)``, ніколи
  ``t(f"…{v}…")`` — інакше ключ щоразу інакший і переклад не знайдеться;
* ключ у :data:`_EN` має збігатися з рядком у коді **символ-у-символ**, включно з
  пробілами, переносами ``\\n``, тире (``–`` en-dash ≠ ``-`` дефіс), стрілками
  (``→``) та символом ``∞``;
* суто формульні/символьні рядки (без жодного українського слова — напр.
  ``"i → B → j = 3 + 9 = 12"``) у словник НЕ заносимо: :func:`t` поверне їх
  незмінними, а виглядають вони однаково обома мовами.
"""

from __future__ import annotations

import re
from typing import Dict, Set

#: Мова за замовчуванням (= вихідна мова рядків-ключів у коді).
LANG = "uk"

#: Будь-яка кирилична літера — ознака «це український рядок, а не формула/символи».
_CYRILLIC = re.compile(r"[Ѐ-ӿ]")

#: Аудит повноти перекладу: рядки з кирилицею, які в режимі ``en`` НЕ знайшлися в
#: :data:`_EN` (тобто лишилися б українськими). Наповнюється на льоту в :func:`t`;
#: має бути порожнім після повного прогону ``en`` — це й перевіряють тести/збірка.
missing_translations: Set[str] = set()


def set_lang(lang: str) -> None:
    """Встановити мову підписів: ``"uk"`` (типово) або ``"en"``."""
    global LANG
    assert lang in ("uk", "en"), lang
    LANG = lang


def get_lang() -> str:
    """Повернути поточну мову підписів (``"uk"`` або ``"en"``)."""
    return LANG


def t(s: str) -> str:
    """Повернути підпис мовою :data:`LANG` (ключ — вихідний український рядок).

    Для ``LANG == "uk"`` повертає ``s`` без змін (нульовий ризик регресій); для
    ``"en"`` — переклад із :data:`_EN`, а якщо його немає — безпечно сам ``s``.
    Якщо в режимі ``en`` рядок містить кирилицю, але перекладу немає, він
    запам'ятовується в :data:`missing_translations` (мовчазний аудит — не падаємо,
    лише фіксуємо «забутий» ключ).
    """
    if LANG == "uk":
        return s                # мова за замовчуванням: жодного пошуку, байт-у-байт
    out = _EN.get(s)
    if out is None:
        if _CYRILLIC.search(s):
            missing_translations.add(s)   # забутий/неточний ключ — фіксуємо для аудиту
        return s                # відсутній ключ -> безпечно повертаємо вихідний рядок
    return out


# ---------------------------------------------------------------------------
# Словник перекладів (uk -> en).
#
# Згруповано за місцем появи. Шаблони з {плейсхолдерами} перекладені цілком — у
# коді їх викликають як t(шаблон).format(...). НЕ перейменовуйте плейсхолдери:
# їхні імена мусять збігатися з тими, що у виклику .format().
# ---------------------------------------------------------------------------
_EN: Dict[str, str] = {
    # --- visualization.draw_graph (типовий заголовок графа) -------------------
    "Орієнтований зважений граф": "Directed weighted graph",

    # --- visualization: аналогія з аеропортами --------------------------------
    "{leg:g} год": "{leg:g} h",
    "прямий рейс: {direct:g} год": "direct flight: {direct:g} h",
    "пересадка через {k} коротша за прямий рейс":
        "a transfer via {k} is shorter than the direct flight",
    "прямий рейс коротший за пересадку через {k}":
        "the direct flight is shorter than a transfer via {k}",
    "Аналогія: прямий рейс проти пересадки через хаб {k}":
        "Analogy: direct flight vs. a transfer through hub {k}",
    "Дозволено пересадки: {allowed}": "Transfers allowed: {allowed}",
    "Відкриваємо аеропорти-хаби по черзі — маршрут i → j коротшає":
        "Opening hub airports one by one — route i → j keeps shrinking",
    "Відкриваємо хаби по черзі — маршрут i → j коротшає":
        "Opening hubs one by one — route i → j keeps shrinking",
    # підпис панелі прогресії (поле caption у _PROG_PANELS), що містить слова:
    "i → j: прямого рейсу немає  →  ∞": "i → j: no direct flight  →  ∞",

    # --- visualization: компактна матриця -------------------------------------
    "Матриця D": "Matrix D",

    # --- visualization.draw_floyd_step ----------------------------------------
    "у кожній клітинці — повна формула:  D[i][j] = min( поточне , шлях через k ) = min( числа ) = результат (жирним)":
        "each cell holds the full formula:  D[i][j] = min( current , path via k ) = min( numbers ) = result (bold)",
    "Стовпець {k} містить\nD[i][{k}]  (відстань до {k})":
        "Column {k} holds\nD[i][{k}]  (distance to {k})",
    "рядок {k} містить\nD[{k}][j]\n(відстань від {k})":
        "row {k} holds\nD[{k}][j]\n(distance from {k})",
    "Матриця D після відкриття вершини {k}":
        "Matrix D after opening vertex {k}",

    # --- visualization.draw_evolution -----------------------------------------
    "Початок": "Start",
    "Після {k}": "After {k}",

    # --- visualization.step_summary (текстовий підсумок кроку) -----------------
    "Крок: проміжна вершина k = {k}": "Step: intermediate vertex k = {k}",
    "Жодна відстань не покращилася на цьому кроці.":
        "No distance improved on this step.",
    "  Причина: у вершину {k} не входить жодне ребро (D[i][{k}] = ∞).":
        "  Reason: vertex {k} has no incoming edges (D[i][{k}] = ∞).",
    "  Причина: з вершини {k} не виходить жодне ребро (D[{k}][j] = ∞).":
        "  Reason: vertex {k} has no outgoing edges (D[{k}][j] = ∞).",
    "  Через {k} не знайшлося коротших шляхів.":
        "  No shorter paths were found through {k}.",
    "Покращено відстаней: {n}": "Distances improved: {n}",
    "  D[{a}][{b}]: {old} → {new}   (бо D[{a}][{k}] + D[{k}][{b}] = {expr} = {new})":
        "  D[{a}][{b}]: {old} → {new}   (since D[{a}][{k}] + D[{k}][{b}] = {expr} = {new})",

    # --- _common.report_distances (підсумкова матриця + шляхи) -----------------
    "\nФінальна матриця найкоротших відстаней (рядок = звідки, стовпець = куди):":
        "\nFinal matrix of shortest distances (row = from, column = to):",
    "Найкоротший шлях {a} → {b}:  шляху не існує":
        "Shortest path {a} → {b}:  no path exists",
    "Найкоротший шлях {a} → {b}:  {path}   (довжина = {n:g})":
        "Shortest path {a} → {b}:  {path}   (length = {n:g})",
    "\nРисунки збережено у: {path}": "\nFigures saved to: {path}",

    # --- examples/00_airport_analogy ------------------------------------------
    "Карта аеропортів: вершини = аеропорти, ребра = прямі рейси (тривалість)":
        "Airport map: vertices = airports, edges = direct flights (duration)",
    "Збережено 3 рисунки аналогії з аеропортами.":
        "Saved 3 airport-analogy figures.",

    # --- examples/01_graph_abcdef ---------------------------------------------
    "Готово: зібрано {n} знімків (початковий + по одному на кожну вершину).":
        "Done: collected {n} snapshots (the initial one + one per vertex).",
    "Початкова матриця D  (жодної проміжної вершини)":
        "Initial matrix D  (no intermediate vertices)",
    "Еволюція матриці відстаней D (відкриваємо вершини A → F)":
        "Evolution of the distance matrix D (opening vertices A → F)",
    "Найкоротший шлях A → D: {path}  (довжина 11)":
        "Shortest path A → D: {path}  (length 11)",

    # --- examples/02_negative_cycle -------------------------------------------
    "Повністю від'ємний цикл X → Y → Z → X (сума ваг = −3)":
        "Fully negative cycle X → Y → Z → X (total weight = −3)",
    "Кількість обходів циклу  k": "Number of cycle traversals  k",
    "Накопичена вага шляху": "Accumulated path weight",
    "Вага шляху з k обходами циклу X → Y → Z → X  (вага циклу = −3)":
        "Path weight with k traversals of cycle X → Y → Z → X  (cycle weight = −3)",
    "→ −∞\n(мінімуму не існує)": "→ −∞\n(no minimum exists)",
    "Діагональ матриці D після Флойда–Воршала (вершини X, Y, Z):":
        "Diagonal of matrix D after Floyd–Warshall (vertices X, Y, Z):",
    "Є вершина з D[i][i] < 0  →  виявлено від'ємний цикл: {flag}":
        "There is a vertex with D[i][i] < 0  →  negative cycle detected: {flag}",
    "\nЧисла поза діагоналлю алгоритм теж повертає скінченними, але вони НЕ є":
        "\nThe off-diagonal numbers are returned finite too, but they are NOT",
    "справжніми найкоротшими відстанями — насправді для цих пар відповідь −∞.":
        "the true shortest distances — for those pairs the real answer is −∞.",

    # --- examples/03_negative_edges_pqrs --------------------------------------
    "Граф із від'ємним ребром (Q → R = −2)":
        "Graph with a negative edge (Q → R = −2)",
    "Початкова матриця D": "Initial matrix D",
    "Еволюція матриці відстаней D (відкриваємо вершини P → S)":
        "Evolution of the distance matrix D (opening vertices P → S)",
    "Найкоротший шлях P → S: {path}  (довжина 5)":
        "Shortest path P → S: {path}  (length 5)",
    "Підсумкова матриця найкоротших відстаней":
        "Final matrix of shortest distances",
    "\nВід'ємних циклів немає, матрицю обчислено коректно ✔":
        "\nNo negative cycles — the matrix was computed correctly ✔",

    # --- examples/04_animations -----------------------------------------------
    "Після відкриття {k}": "After opening {k}",
    "Відновлення шляху {a} → {b} за nxt:  {arrow}":
        "Reconstructing path {a} → {b} from nxt:  {arrow}",
    "Крок k = {k}: два внутрішні цикли перебирають усі пари (i, j)":
        "Step k = {k}: two inner loops sweep every pair (i, j)",
    "(i, j) = ({a}, {b}):  рядок/стовпець {k} або діагональ — пропускаємо":
        "(i, j) = ({a}, {b}):  row/column {k} or the diagonal — skipped",
    "   ✔ покращено": "   ✔ improved",
    "   без змін": "   no change",
    "Обхід від'ємного циклу {a} → {b} → {c} → {a} (кожне ребро −1)":
        "Walking the negative cycle {a} → {b} → {c} → {a} (each edge −1)",
    "на старті у {a}\nнакопичена вага: 0":
        "starting at {a}\naccumulated weight: 0",
    "крок {s}:  {u} → {v}\nнакопичена вага: {acc}\nповних обходів: {done}":
        "step {s}:  {u} → {v}\naccumulated weight: {acc}\nfull loops: {done}",
    "обходити можна вічно:\n−3, −6, −9, …  →  −∞":
        "you can loop forever:\n−3, −6, −9, …  →  −∞",
    "Генерую GIF-анімації (Tier 1–2)…": "Generating animations (Tier 1–2)…",
    "  {name}: {n} кадрів": "  {name}: {n} frames",
    "  {name}: {n} кадрів ({arrow})": "  {name}: {n} frames ({arrow})",
    "  {name}: {n} кадрів (покращень: {imp})":
        "  {name}: {n} frames (improvements: {imp})",

    # --- animation.save_animation (діагностика MP4, рідкісні шляхи) ------------
    "  ({name} пропущено — ffmpeg недоступний; pip install imageio-ffmpeg для відео)":
        "  ({name} skipped — ffmpeg unavailable; pip install imageio-ffmpeg for video)",
    "  ({name} пропущено: {err})": "  ({name} skipped: {err})",
}
