"""Реалізації алгоритму Флойда–Воршала (all-pairs shortest paths).

Модуль містить три рівні реалізації — від навчально-інструментованої до
короткої «бойової»:

* :func:`floyd_warshall_steps` — інструментована версія, що повертає не лише
  фінальну матрицю, а й матрицю наступних вершин ``nxt`` (для відновлення
  самих шляхів) та «знімки» матриці після відкриття кожної проміжної вершини.
  Саме її використовують навчальні візуалізації.
* :func:`floyd_warshall` — компактна реалізація без службових структур.
* :func:`reconstruct_path` / :func:`has_negative_cycle` — допоміжні утиліти.

Дві перші функції відрізняються **угодою про відсутнє ребро**:

* ``floyd_warshall_steps`` працює з матрицею суміжності, де ``0`` означає
  «немає ребра» (так задано вихідний приклад).
* ``floyd_warshall`` очікує матрицю, де відсутнє ребро задано як ``INF``, а на
  діагоналі стоять нулі. Ця угода надійніша: вона коректно підтримує й ребра
  *нульової* ваги, які за угодою ``0 == немає ребра`` відрізнити неможливо.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Dict, List, Optional, Set, Tuple

#: «Нескінченність» — позначає відсутність шляху між двома вершинами.
INF: float = float("inf")

Matrix = List[List[float]]
Snapshot = Dict[str, object]


def adjacency_to_inf(adj: Matrix) -> Matrix:
    """Переводить матрицю суміжності з угоди ``0 == немає ребра`` в угоду з ``INF``.

    Повертає нову матрицю відстаней: нулі на діагоналі, ваги наявних ребер, а
    відсутні ребра — :data:`INF`. Це спільна ініціалізація для покрокової
    версії алгоритму (і зручний місток між двома угодами про вхід).
    """
    n = len(adj)
    dist: Matrix = [[INF] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                dist[i][j] = 0
            elif adj[i][j] != 0:
                dist[i][j] = adj[i][j]
    return dist


def floyd_warshall_steps(adj: Matrix) -> Tuple[Matrix, List[List[Optional[int]]], List[Snapshot]]:
    """Інструментована версія Флойда–Воршала для покрокового розбору.

    Угода про вхід: ``adj[i][j]`` — вага ребра ``i -> j``; значення ``0``
    означає «ребра немає» (звичайна матриця суміжності).

    :returns: кортеж ``(dist, nxt, snapshots)``, де

        * ``dist`` — підсумкова матриця найкоротших відстаней між усіма парами;
        * ``nxt`` — матриця наступних вершин: ``nxt[i][j]`` — перша вершина
          після ``i`` на найкоротшому шляху ``i -> j`` (``None``, якщо шляху
          немає). Використовується :func:`reconstruct_path`;
        * ``snapshots`` — список знімків матриці: перший (``k=None``) — стан
          до відкриття будь-яких вершин, далі по одному після відкриття кожної
          проміжної вершини ``k``. Кожен знімок — словник з ключами
          ``k`` (індекс проміжної вершини або ``None``), ``matrix`` (копія
          матриці), ``prev`` (матриця до цього кроку) та ``changed`` (множина
          клітинок ``(i, j)``, що покращилися на кроці).

    Складність: :math:`O(n^3)` часу та :math:`O(n^2)` пам'яті
    (плюс ще :math:`O(n^2)` на ``nxt`` та на знімки).
    """
    n = len(adj)
    dist: Matrix = adjacency_to_inf(adj)
    # ``nxt[i][j] = j`` для кожної відомої (скінченної) відстані, інакше ``None``.
    nxt: List[List[Optional[int]]] = [
        [j if dist[i][j] != INF else None for j in range(n)] for i in range(n)
    ]

    # знімок початкового стану (жодної проміжної вершини ще не відкрито)
    snapshots: List[Snapshot] = [
        {"k": None, "matrix": deepcopy(dist), "prev": None, "changed": set()}
    ]

    # --- основні ітерації: «відкриваємо» вершини 0, 1, 2, ... по черзі ---
    for k in range(n):
        prev = deepcopy(dist)  # копія лише задля підсвічування змін
        changed: Set[Tuple[int, int]] = set()
        for i in range(n):
            for j in range(n):
                via_k = dist[i][k] + dist[k][j]
                if via_k < dist[i][j]:
                    dist[i][j] = via_k
                    nxt[i][j] = nxt[i][k]  # шлях i -> j тепер іде через k
                    changed.add((i, j))     # релаксація лише зменшує — зміна = покращення
        snapshots.append(
            {"k": k, "matrix": deepcopy(dist), "prev": prev, "changed": changed}
        )

    return dist, nxt, snapshots


def floyd_warshall(adj: Matrix) -> Matrix:
    """Компактна реалізація Флойда–Воршала (без службових структур).

    Угода про вхід: ``adj[i][j]`` — вага ребра або :data:`INF`, якщо ребра
    немає; на діагоналі — нулі. На відміну від :func:`floyd_warshall_steps`,
    ця угода коректно підтримує ребра нульової ваги.

    :returns: матриця найкоротших відстаней між усіма парами вершин.
    """
    n = len(adj)
    dist: Matrix = [row[:] for row in adj]
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
    return dist


def reconstruct_path(nxt: List[List[Optional[int]]], u: int, v: int) -> Optional[List[int]]:
    """Відновлює список вершин найкоротшого шляху ``u -> v`` за матрицею ``nxt``.

    :param nxt: матриця наступних вершин, повернена :func:`floyd_warshall_steps`.
    :returns: список індексів вершин від ``u`` до ``v`` включно, або ``None``,
        якщо шляху не існує.
    """
    if nxt[u][v] is None:
        return None
    path = [u]
    while u != v:
        u = nxt[u][v]  # type: ignore[assignment]
        path.append(u)
    return path


def has_negative_cycle(dist: Matrix) -> bool:
    """Чи є у графі досяжний цикл від'ємної ваги.

    Зручний критерій: після Флойда–Воршала від'ємний цикл існує тоді й лише
    тоді, коли на діагоналі знайдеться від'ємне значення (``dist[i][i] < 0``):
    вершина ``i`` «повертається в себе» з від'ємною вагою.
    """
    return any(dist[i][i] < 0 for i in range(len(dist)))
