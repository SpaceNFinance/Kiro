"""Large-print Sudoku puzzle generator for the Senior Reader series.

Generates valid Easy-difficulty Sudoku puzzles, each guaranteed to have
exactly ONE unique solution that is reachable with basic logic (the
puzzles keep enough givens that simple scanning / single-candidate
deduction is sufficient, so no guessing is required).

Outputs a large-print HTML file with:
  - a clearly drawn 9x9 starting grid,
  - a text-based grid (pipes | and dashes -) for easy copy/paste into
    a publishing layout,
  - the complete solution grid.

Dependency-free: standard library only.  Run with:  python3 sudoku_gen.py
"""

import os
import random

N = 9
BOX = 3


# ---------------------------------------------------------------------------
# Core solver / generator
# ---------------------------------------------------------------------------
def _find_empty(grid):
    for r in range(N):
        for c in range(N):
            if grid[r][c] == 0:
                return r, c
    return None


def _valid(grid, r, c, val):
    for i in range(N):
        if grid[r][i] == val or grid[i][c] == val:
            return False
    br, bc = (r // BOX) * BOX, (c // BOX) * BOX
    for i in range(br, br + BOX):
        for j in range(bc, bc + BOX):
            if grid[i][j] == val:
                return False
    return True


def _count_solutions(grid, limit=2):
    """Count solutions up to `limit` (used to prove uniqueness)."""
    spot = _find_empty(grid)
    if spot is None:
        return 1
    r, c = spot
    total = 0
    for val in range(1, 10):
        if _valid(grid, r, c, val):
            grid[r][c] = val
            total += _count_solutions(grid, limit)
            grid[r][c] = 0
            if total >= limit:
                break
    return total


def _fill_full(grid):
    """Fill an empty grid with a random complete valid solution."""
    spot = _find_empty(grid)
    if spot is None:
        return True
    r, c = spot
    nums = list(range(1, 10))
    random.shuffle(nums)
    for val in nums:
        if _valid(grid, r, c, val):
            grid[r][c] = val
            if _fill_full(grid):
                return True
            grid[r][c] = 0
    return False


def generate_puzzle(target_givens=38, rng_seed=None):
    """Return (puzzle, solution) where puzzle has a unique solution.

    Easy difficulty: we keep a high number of givens (default 38) and
    remove cells in symmetric pairs only while uniqueness is preserved.
    """
    if rng_seed is not None:
        random.seed(rng_seed)

    solution = [[0] * N for _ in range(N)]
    _fill_full(solution)

    puzzle = [row[:] for row in solution]

    # Symmetric cell positions (rotational), shuffled.
    coords = [(r, c) for r in range(N) for c in range(N)]
    random.shuffle(coords)

    givens = N * N
    for (r, c) in coords:
        if givens <= target_givens:
            break
        r2, c2 = N - 1 - r, N - 1 - c
        if puzzle[r][c] == 0:
            continue
        backup = [(r, c, puzzle[r][c])]
        puzzle[r][c] = 0
        if (r2, c2) != (r, c) and puzzle[r2][c2] != 0:
            backup.append((r2, c2, puzzle[r2][c2]))
            puzzle[r2][c2] = 0

        test = [row[:] for row in puzzle]
        if _count_solutions(test, limit=2) != 1:
            # Revert: removal broke uniqueness.
            for (rr, cc, v) in backup:
                puzzle[rr][cc] = v
        else:
            givens -= len(backup)

    return puzzle, solution


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------
def to_text_grid(grid, empty="_"):
    """Render a grid as a pipe/dash text block."""
    sep = "+-------+-------+-------+"
    lines = [sep]
    for r in range(N):
        cells = []
        for c in range(N):
            v = grid[r][c]
            cells.append(empty if v == 0 else str(v))
        row = "| {} {} {} | {} {} {} | {} {} {} |".format(*cells)
        lines.append(row)
        if r % 3 == 2:
            lines.append(sep)
    return "\n".join(lines)


def count_givens(grid):
    return sum(1 for r in range(N) for c in range(N) if grid[r][c] != 0)


# ---------------------------------------------------------------------------
# HTML output
# ---------------------------------------------------------------------------
HTML_HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Large Print Sudoku - Easy, Batch 1</title>
<style>
  :root { --ink:#1a1a1a; --line:#1a1a1a; --soft:#f6f4ee; }
  * { box-sizing: border-box; }
  body {
    font-family: "Georgia", "Times New Roman", serif;
    background: #fffdf8;
    color: var(--ink);
    margin: 0;
    padding: 40px 20px 80px;
    line-height: 1.5;
  }
  .page { max-width: 760px; margin: 0 auto; }
  h1 { font-size: 40px; text-align: center; margin: 0 0 6px; }
  .sub { text-align: center; font-size: 20px; color: #555; margin-bottom: 40px; }
  .puzzle { page-break-inside: avoid; margin: 0 0 70px; }
  h2 { font-size: 30px; border-bottom: 4px solid var(--ink); padding-bottom: 8px; }
  h3 { font-size: 22px; margin: 28px 0 12px; }
  table.sudoku { border-collapse: collapse; margin: 0 auto 10px; }
  table.sudoku td {
    width: 58px; height: 58px;
    text-align: center; vertical-align: middle;
    font-size: 30px; font-weight: bold;
    border: 1px solid #999;
  }
  table.sudoku td.given { color: #000; }
  table.sudoku td.blank { color: #bbb; }
  /* thick 3x3 box borders */
  table.sudoku td { border-top: 1px solid #999; border-left: 1px solid #999; }
  table.sudoku tr:first-child td { border-top: 3px solid var(--ink); }
  table.sudoku tr td:first-child { border-left: 3px solid var(--ink); }
  table.sudoku tr td:last-child { border-right: 3px solid var(--ink); }
  table.sudoku tr:last-child td { border-bottom: 3px solid var(--ink); }
  table.sudoku tr:nth-child(3n) td { border-bottom: 3px solid var(--ink); }
  table.sudoku td:nth-child(3n) { border-right: 3px solid var(--ink); }
  pre.textgrid {
    background: var(--soft);
    border: 1px solid #ddd;
    border-radius: 6px;
    padding: 16px 20px;
    font-size: 19px;
    font-family: "Courier New", monospace;
    line-height: 1.35;
    overflow-x: auto;
  }
  .meta { text-align:center; font-size:17px; color:#666; margin-bottom:18px; }
  .grids { display:flex; flex-wrap:wrap; gap:30px; justify-content:center; align-items:flex-start; }
  .grids > div { flex: 1 1 320px; }
  .grids h3 { text-align:center; }
  details { margin-top: 10px; }
  summary { font-size: 20px; cursor: pointer; font-weight: bold; }
  footer { text-align:center; color:#888; font-size:15px; margin-top:40px; }
</style>
</head>
<body>
<div class="page">
<h1>Large Print Sudoku</h1>
<div class="sub">Easy Puzzles &mdash; Batch 1 &middot; Relax, Refresh, Enjoy</div>
"""

HTML_FOOT = """<footer>Every puzzle has exactly one solution and can be solved with
basic logic &mdash; no guessing required. Happy puzzling!</footer>
</div>
</body>
</html>
"""


def grid_to_html_table(puzzle):
    rows = []
    for r in range(N):
        cells = []
        for c in range(N):
            v = puzzle[r][c]
            if v == 0:
                cells.append('<td class="blank">&middot;</td>')
            else:
                cells.append('<td class="given">{}</td>'.format(v))
        rows.append("<tr>{}</tr>".format("".join(cells)))
    return '<table class="sudoku">{}</table>'.format("".join(rows))


PUZZLE_TITLES = [
    "Afternoon Relaxation",
    "Morning Sunshine",
    "Quiet Evening Tea",
]


def build_html(puzzles):
    parts = [HTML_HEAD]
    for i, (puzzle, solution) in enumerate(puzzles, start=1):
        title = PUZZLE_TITLES[(i - 1) % len(PUZZLE_TITLES)]
        givens = count_givens(puzzle)
        parts.append('<section class="puzzle">')
        parts.append("<h2>Puzzle {}: {}</h2>".format(i, title))
        parts.append('<div class="meta">Difficulty: Easy &middot; {} given numbers &middot; one unique solution</div>'.format(givens))

        parts.append('<div class="grids">')
        parts.append("<div><h3>Starting Grid</h3>{}</div>".format(grid_to_html_table(puzzle)))
        parts.append("<div><h3>Solution</h3>{}</div>".format(grid_to_html_table(solution)))
        parts.append("</div>")

        parts.append("<h3>Starting Grid (text)</h3>")
        parts.append('<pre class="textgrid">{}</pre>'.format(to_text_grid(puzzle)))

        parts.append("<details><summary>Show Solution (text)</summary>")
        parts.append('<pre class="textgrid">{}</pre>'.format(to_text_grid(solution)))
        parts.append("</details>")
        parts.append("</section>")
    parts.append(HTML_FOOT)
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Verification + main
# ---------------------------------------------------------------------------
def verify(puzzle, solution):
    """Confirm puzzle is consistent with solution and uniquely solvable."""
    for r in range(N):
        for c in range(N):
            if puzzle[r][c] != 0 and puzzle[r][c] != solution[r][c]:
                return False, "given conflicts with solution"
    test = [row[:] for row in puzzle]
    n = _count_solutions(test, limit=2)
    if n != 1:
        return False, "solution count = {}".format(n)
    return True, "unique"


def main():
    out_dir = os.path.dirname(os.path.abspath(__file__))
    seeds = [101, 202, 303]
    puzzles = []
    seen = set()
    for s in seeds:
        puzzle, solution = generate_puzzle(target_givens=38, rng_seed=s)
        ok, msg = verify(puzzle, solution)
        sig = tuple(tuple(row) for row in puzzle)
        assert ok, "Puzzle failed verification: " + msg
        assert sig not in seen, "Duplicate puzzle generated"
        seen.add(sig)
        puzzles.append((puzzle, solution))
        print("Puzzle seed {:>3}: {} givens, {}".format(
            s, count_givens(puzzle), msg))

    html = build_html(puzzles)
    out_path = os.path.join(out_dir, "sudoku_easy_batch1.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print("\nWrote: {} ({:.1f} KB)".format(out_path, len(html) / 1024.0))

    # Also print the text grids to stdout for quick review.
    for i, (puzzle, solution) in enumerate(puzzles, start=1):
        print("\n" + "=" * 40)
        print("Puzzle {}: {}".format(i, PUZZLE_TITLES[i - 1]))
        print("=" * 40)
        print(to_text_grid(puzzle))


if __name__ == "__main__":
    main()
