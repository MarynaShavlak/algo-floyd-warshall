"""Тести коректності алгоритму Флойда–Воршала.

Покривають три речі, про які йдеться в README:

* збіг результату з еталонною реалізацією ``networkx`` (додатні й від'ємні ваги);
* коректну підтримку ребра **нульової ваги** (саме той кейс, через який угода
  ``INF`` надійніша за ``0 == немає ребра``);
* виявлення від'ємного циклу та відновлення самого шляху через матрицю ``nxt``.

Запуск::

    pytest                       # якщо встановлено pytest
    python tests/test_core.py    # без pytest (вбудований раннер)
"""

from __future__ import annotations

import os
import sys

import networkx as nx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from floyd_warshall import (  # noqa: E402
    INF,
    adjacency_to_inf,
    floyd_warshall,
    floyd_warshall_steps,
    has_negative_cycle,
    reconstruct_path,
)

# --- Граф A–F (додатні ваги), вершини 0..5 --------------------------------
ABCDEF_EDGES = [(0, 1, 3), (1, 2, 1), (2, 3, 7), (2, 5, 2), (4, 3, 2), (4, 5, 3)]
# --- Граф P, Q, R, S із від'ємним ребром Q→R, вершини 0..3 ----------------
PQRS_EDGES = [(0, 1, 4), (1, 2, -2), (2, 3, 3), (0, 3, 10)]


def _edges_to_inf_matrix(n, edges):
    """Список ребер -> матриця відстаней в угоді INF (0 на діагоналі)."""
    dist = [[0 if i == j else INF for j in range(n)] for i in range(n)]
    for u, v, w in edges:
        dist[u][v] = w
    return dist


def _networkx_reference(n, edges):
    """Еталонна матриця all-pairs відстаней від networkx (та сама угода INF)."""
    g = nx.DiGraph()
    g.add_nodes_from(range(n))
    g.add_weighted_edges_from(edges)
    nx_dist = dict(nx.floyd_warshall(g))
    return [[nx_dist[i].get(j, INF) for j in range(n)] for i in range(n)]


def test_matches_networkx_positive_weights():
    n = 6
    got = floyd_warshall(_edges_to_inf_matrix(n, ABCDEF_EDGES))
    assert got == _networkx_reference(n, ABCDEF_EDGES)


def test_matches_networkx_negative_edges():
    n = 4
    got = floyd_warshall(_edges_to_inf_matrix(n, PQRS_EDGES))
    assert got == _networkx_reference(n, PQRS_EDGES)
    # пряме ребро P→S=10 програє шляху P→Q→R→S=5 (ефект від'ємного ребра)
    assert got[0][3] == 5


def test_zero_weight_edge_supported():
    """Ребро ваги 0 має зберігатися, а не трактуватись як «немає ребра»."""
    # 0 →(0)→ 1 →(5)→ 2 ; перевіряємо, що нульове ребро не «загубилось»
    adj = [
        [0, 0, INF],
        [INF, 0, 5],
        [INF, INF, 0],
    ]
    dist = floyd_warshall(adj)
    assert dist[0][1] == 0  # пряме ребро нульової ваги
    assert dist[0][2] == 5  # 0 → 1 → 2 = 0 + 5


def test_known_distances_abcdef():
    dist, nxt, snapshots = floyd_warshall_steps(
        [
            [0, 3, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0],
            [0, 0, 0, 7, 0, 2],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 2, 0, 3],
            [0, 0, 0, 0, 0, 0],
        ]
    )
    assert dist[0][3] == 11  # A → D
    assert dist[0][5] == 6   # A → F
    assert dist[0][2] == 4   # A → C
    assert dist[3][0] == INF  # D — стік, з нього шляху в A немає


def test_reconstruct_path_abcdef():
    _, nxt, _ = floyd_warshall_steps(
        [
            [0, 3, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0],
            [0, 0, 0, 7, 0, 2],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 2, 0, 3],
            [0, 0, 0, 0, 0, 0],
        ]
    )
    assert reconstruct_path(nxt, 0, 3) == [0, 1, 2, 3]  # A → B → C → D
    assert reconstruct_path(nxt, 0, 0) == [0]            # тривіальний шлях у себе
    assert reconstruct_path(nxt, 3, 0) is None           # шляху не існує


def test_snapshots_count_equals_n_plus_one():
    adj = [[0, 3, 0], [0, 0, 1], [0, 0, 0]]
    _, _, snapshots = floyd_warshall_steps(adj)
    # один початковий знімок (k=None) + по одному після кожної з n вершин
    assert len(snapshots) == len(adj) + 1
    assert snapshots[0]["k"] is None


def test_negative_cycle_detected():
    # цикл 0 → 1 → 2 → 0 вагою 1 + (-1) + (-1) = -1 < 0
    neg = [
        [0, 1, 0],
        [0, 0, -1],
        [-1, 0, 0],
    ]
    dist, _, _ = floyd_warshall_steps(neg)
    assert has_negative_cycle(dist) is True


def test_no_negative_cycle_on_normal_graph():
    dist = floyd_warshall(_edges_to_inf_matrix(4, PQRS_EDGES))
    assert has_negative_cycle(dist) is False


def test_adjacency_to_inf_conversion():
    adj = [[0, 3, 0], [0, 0, 1], [0, 0, 0]]
    dist = adjacency_to_inf(adj)
    assert dist[0][0] == 0      # діагональ
    assert dist[0][1] == 3      # наявне ребро
    assert dist[0][2] == INF    # відсутнє ребро


def _run_without_pytest():
    """Мінімальний раннер на випадок, якщо pytest не встановлено."""
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failures = 0
    for test in tests:
        try:
            test()
            print(f"PASS  {test.__name__}")
        except AssertionError as exc:
            failures += 1
            print(f"FAIL  {test.__name__}: {exc}")
    print(f"\n{len(tests) - failures}/{len(tests)} тестів пройдено")
    return failures


if __name__ == "__main__":
    sys.exit(1 if _run_without_pytest() else 0)
