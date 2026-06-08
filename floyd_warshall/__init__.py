"""Навчальна реалізація та візуалізація алгоритму Флойда–Воршала.

Пакет розділено на два модулі:

* :mod:`floyd_warshall.core` — сам алгоритм (``floyd_warshall``,
  ``floyd_warshall_steps``), відновлення шляху та виявлення від'ємних циклів;
* :mod:`floyd_warshall.visualization` — функції малювання графів, матриць та
  покрокових кадрів (потребують ``matplotlib`` і ``networkx``);
* :mod:`floyd_warshall.walkthrough` — покрокова візуалізація «код ↔ матриця» з
  підсвічуванням активних рядків коду (потребує ``matplotlib``).

``core`` та ``i18n`` лишаються без важких залежностей, тож ``import floyd_warshall``
не тягне ``matplotlib``; модулі малювання імпортують явно (``from
floyd_warshall.visualization import …`` / ``… .walkthrough import …``).

Приклад::

    from floyd_warshall import floyd_warshall, INF

    adj = [
        [0,   3,   INF],
        [INF, 0,   1  ],
        [INF, INF, 0  ],
    ]
    dist = floyd_warshall(adj)
"""

from .core import (
    INF,
    adjacency_to_inf,
    floyd_warshall,
    floyd_warshall_steps,
    has_negative_cycle,
    reconstruct_path,
)
from .i18n import get_lang, set_lang, t

__all__ = [
    "INF",
    "adjacency_to_inf",
    "floyd_warshall",
    "floyd_warshall_steps",
    "reconstruct_path",
    "has_negative_cycle",
    # двомовні підписи (uk/en) — без важких залежностей, тож безпечно тут
    "t",
    "set_lang",
    "get_lang",
]

# Єдине джерело правди для версії пакета: pyproject.toml читає його звідси через
# [tool.setuptools.dynamic] version = { attr = "floyd_warshall.__version__" }.
__version__ = "1.0.0"
