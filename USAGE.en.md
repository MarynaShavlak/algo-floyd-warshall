# Quick start

[🇺🇦 Українська](USAGE.md)  ·  **🇬🇧 English**

> Part of the documentation for the [“Floyd–Warshall Algorithm: a step-by-step walkthrough”](README.en.md) project. This page covers the commands for installation, running the examples and the tests. For the repository structure see [PROJECT_STRUCTURE.en.md](PROJECT_STRUCTURE.en.md).

> **Requires Python ≥ 3.8.** The code uses `from __future__ import annotations`, so it works on 3.8+ (developed and tested on 3.12).

```bash
# 1. Dependencies
pip install -r requirements.txt
# or install the package in development mode:
pip install -e .
# (optional) MP4 videos of the animations without root — adds ffmpeg from imageio-ffmpeg:
pip install -e ".[video]"

# 2. Reproduce all figures and text output in English (→ docs/images/en/) — pass the `en` argument
python examples/00_airport_analogy.py en      # airport analogy
python examples/01_graph_abcdef.py en          # graph A–F
python examples/02_negative_cycle.py en        # negative cycle
python examples/03_negative_edges_pqrs.py en   # negative edges
python examples/04_animations.py en            # GIF+MP4 animations (evolution, path, hubs)

# 3. Without the argument the same media are produced in Ukrainian (→ docs/images/)
python examples/01_graph_abcdef.py
```

The five scripts together generate **24 static figures** (`.png`), **8 GIF animations** (`.gif`), and **8 MP4 videos** (`.mp4`); without an argument they go to [`docs/images/`](docs/images) (Ukrainian), and with `en` the English versions go to [`docs/images/en/`](docs/images/en). They run in a few seconds. **MP4** is encoded only when `ffmpeg` is available (system-wide or from `imageio-ffmpeg`); without it only the GIFs are built — the build never fails.

Check the algorithm's correctness (results are cross-checked against the reference `networkx` implementation):

```bash
python tests/test_core.py     # core correctness (no extra dependencies)
python tests/test_smoke.py    # smoke: rendering and GIF assembly don't crash (matplotlib, pillow)
# or both via pytest (pip install -e ".[dev]"):
pytest
```

`test_core.py` covers agreement with `networkx` on positive and negative weights, support for zero-weight edges, negative-cycle detection, path reconstruction through `nxt`, and the robustness of `reconstruct_path` against a negative cycle (no infinite loop). The smoke tests in `test_smoke.py` check that every drawing function and the GIF assembly run without errors, and that `report_distances` correctly handles a pair with no path.

Minimal use as a library:

```python
from floyd_warshall import floyd_warshall, reconstruct_path, has_negative_cycle, INF

adj = [
    [0,   3,   INF],
    [INF, 0,   1  ],
    [INF, INF, 0  ],
]
dist = floyd_warshall(adj)        # the matrix of shortest distances
```
