"""Build a Large Print Sudoku book.

Generates 60 unique-solution puzzles across three difficulty tiers
(20 Medium, 20 Hard, 20 Extreme) and writes:

  - sudoku_book_full.md   : the complete book (puzzle pages + Answers chapter)
  - BOOK-LAYOUT-GUIDE.md   : a structured layout template showing exactly how a
                             single puzzle page and an Answers (4-up) page look.

Difficulty is controlled by the number of given clues, with each puzzle proven
to have exactly ONE solution (verified with a counting solver). Empty cells in
the starting grids are rendered as spaces, inside fenced code blocks so the
alignment is preserved for copy/paste into a publishing layout.

Dependency-free. Run:  python3 generate_book.py
"""

import os
import random
import time

import sudoku_gen as sg

N = 9

# --------------------------------------------------------------------------
# Difficulty tiers: (label, target number of given clues)
# Fewer givens => harder. Every puzzle is still proven uniquely solvable.
# --------------------------------------------------------------------------
# (label, target_givens, ceiling_givens, symmetric, quantity)
# target = aim for this clue count; ceiling = reject/retry if above this.
# Symmetric removal looks nicer but can't reach low counts, so the harder
# tiers remove cells asymmetrically to achieve genuinely fewer clues.
TIERS = [
    ("Medium", 32, 34, True, 20),
    ("Hard", 27, 29, False, 20),
    ("Extreme", 24, 26, False, 20),
]


# --------------------------------------------------------------------------
# Calm titles (no demographic wording anywhere).
# --------------------------------------------------------------------------
_TIMES = [
    "Morning", "Afternoon", "Evening", "Twilight", "Sunrise",
    "Sunset", "Midday", "Dawn", "Dusk", "Lakeside",
]
_MOODS = [
    "Relaxation", "Calm", "Serenity", "Reflection", "Stillness",
    "Repose", "Quiet Hour", "Easy Breeze", "Comfort", "Harmony",
    "Tranquility", "Leisure",
]


def build_titles(count):
    titles = []
    for mood in _MOODS:
        for tm in _TIMES:
            titles.append("{} {}".format(tm, mood))
    # Deterministic, unique, plenty (120) -> slice what we need.
    return titles[:count]


# --------------------------------------------------------------------------
# Generation with multi-pass symmetric removal to hit lower clue counts.
# --------------------------------------------------------------------------
def make_puzzle(target_givens, seed, symmetric=True):
    """Single-pass clue removal. Symmetric keeps rotational pairs (prettier);
    asymmetric removes one cell at a time and reaches lower clue counts."""
    random.seed(seed)
    solution = [[0] * N for _ in range(N)]
    sg._fill_full(solution)
    puzzle = [row[:] for row in solution]

    coords = [(r, c) for r in range(N) for c in range(N)]
    random.shuffle(coords)
    givens = N * N
    for (r, c) in coords:
        if givens <= target_givens:
            break
        if puzzle[r][c] == 0:
            continue
        backup = [(r, c, puzzle[r][c])]
        puzzle[r][c] = 0
        if symmetric:
            r2, c2 = N - 1 - r, N - 1 - c
            if (r2, c2) != (r, c) and puzzle[r2][c2] != 0:
                backup.append((r2, c2, puzzle[r2][c2]))
                puzzle[r2][c2] = 0
        test = [row[:] for row in puzzle]
        if sg._count_solutions(test, limit=2) != 1:
            for (rr, cc, v) in backup:
                puzzle[rr][cc] = v
        else:
            givens -= len(backup)
    return puzzle, solution, givens


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------
def puzzle_grid_spaces(grid):
    """Starting grid: blanks shown as spaces (per spec)."""
    sep = "+-------+-------+-------+"
    lines = [sep]
    for r in range(N):
        cells = [(" " if grid[r][c] == 0 else str(grid[r][c])) for c in range(N)]
        lines.append("| {} {} {} | {} {} {} | {} {} {} |".format(*cells))
        if r % 3 == 2:
            lines.append(sep)
    return "\n".join(lines)


def mini_lines(grid):
    """Compact full grid as a list of 11 lines for answer keys."""
    sep = "------+-------+------"
    out = []
    for r in range(N):
        row = "{} {} {} | {} {} {} | {} {} {}".format(*grid[r])
        out.append(row)
        if r % 3 == 2 and r != N - 1:
            out.append(sep)
    return out


def four_up_block(items):
    """items: list of up to 4 (number, grid). Render as 2x2 mini grids."""
    lines = []
    rows = [items[0:2], items[2:4]]
    for pair in rows:
        if not pair:
            continue
        # header line with answer numbers
        headers = []
        bodies = []
        for (num, grid) in pair:
            headers.append("Answer {}".format(num).ljust(21))
            bodies.append(mini_lines(grid))
        lines.append("    ".join(headers).rstrip())
        for i in range(len(bodies[0])):
            row_cells = [b[i].ljust(21) for b in bodies]
            lines.append("    ".join(row_cells).rstrip())
        lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Book assembly
# --------------------------------------------------------------------------
def main():
    start = time.time()
    out_dir = os.path.dirname(os.path.abspath(__file__))

    all_titles = build_titles(sum(t[4] for t in TIERS))
    puzzles = []  # (number, title, tier, givens, puzzle, solution)
    seen = set()
    num = 0
    seed = 5000
    for (label, target, ceiling, symmetric, qty) in TIERS:
        made = 0
        while made < qty:
            # Try a few seeds; keep the first under the ceiling, else the best.
            best = None  # (givens, puzzle, solution)
            for _attempt in range(5):
                seed += 1
                puzzle, solution, givens = make_puzzle(target, seed, symmetric)
                sig = tuple(tuple(r) for r in puzzle)
                if sig in seen:
                    continue
                ok, _msg = sg.verify(puzzle, solution)
                if not ok:
                    continue
                if best is None or givens < best[0]:
                    best = (givens, puzzle, solution, sig)
                if givens <= ceiling:
                    break
            if best is None:
                continue
            givens, puzzle, solution, sig = best
            seen.add(sig)
            num += 1
            made += 1
            puzzles.append((num, all_titles[num - 1], label, givens, puzzle, solution))
        print("[{}] generated {} puzzles (target {} / ceiling {})".format(
            label, qty, target, ceiling))

    # ---- Full book markdown -------------------------------------------------
    book = []
    book.append("# Large Print Sudoku\n")
    book.append("## A Collection of 60 Puzzles\n")
    book.append("Medium &middot; Hard &middot; Extreme\n")
    book.append("\n---\n")
    book.append("> Every puzzle in this book has exactly **one** unique solution. "
                "Solutions are collected in the **Answers** chapter at the back, "
                "numbered to match each puzzle.\n")
    book.append("\n---\n")

    current_tier = None
    for (n, title, tier, givens, puzzle, solution) in puzzles:
        if tier != current_tier:
            current_tier = tier
            book.append("\n# {} Puzzles\n".format(tier))
        book.append("\n## Puzzle {}: {}\n".format(n, title))
        book.append("**Difficulty:** {}  \n**Clues:** {}  \n**Answer:** see Answer {} in the Answers chapter\n"
                    .format(tier, givens, n))
        book.append("\n```text")
        book.append(puzzle_grid_spaces(puzzle))
        book.append("```\n")
        book.append("\n_Notes: _______________________________________________________________\n")
        book.append("\n<!-- page break -->\n")

    # ---- Answers chapter (4 mini-grids per page) ---------------------------
    book.append("\n\n# Answers\n")
    book.append("\nEach answer number matches its puzzle number.\n")
    page_items = []
    page_no = 1
    for (n, title, tier, givens, puzzle, solution) in puzzles:
        page_items.append((n, solution))
        if len(page_items) == 4:
            book.append("\n### Answers {}-{}\n".format(page_items[0][0], page_items[-1][0]))
            book.append("```text")
            book.append(four_up_block(page_items))
            book.append("```\n")
            book.append("\n<!-- page break -->\n")
            page_items = []
            page_no += 1
    if page_items:
        book.append("\n### Answers {}-{}\n".format(page_items[0][0], page_items[-1][0]))
        book.append("```text")
        book.append(four_up_block(page_items))
        book.append("```\n")

    book_md = "\n".join(book)
    book_path = os.path.join(out_dir, "sudoku_book_full.md")
    with open(book_path, "w", encoding="utf-8") as f:
        f.write(book_md)

    # ---- Layout guide (uses the real Puzzle 1) -----------------------------
    p1 = puzzles[0]
    guide = build_layout_guide(p1, puzzles[:4])
    guide_path = os.path.join(out_dir, "BOOK-LAYOUT-GUIDE.md")
    with open(guide_path, "w", encoding="utf-8") as f:
        f.write(guide)

    elapsed = time.time() - start
    print("\nWrote: {}".format(book_path))
    print("Wrote: {}".format(guide_path))
    print("Total puzzles: {}  |  generation time: {:.1f}s".format(len(puzzles), elapsed))
    # Clue spread per tier
    for (label, _t, _c, _sym, _q) in TIERS:
        gv = [g for (_n, _ti, t, g, _p, _s) in puzzles if t == label]
        print("  {:<8} clues min/avg/max: {}/{:.1f}/{}".format(
            label, min(gv), sum(gv) / len(gv), max(gv)))


def build_layout_guide(puzzle1, first_four):
    n, title, tier, givens, puzzle, solution = puzzle1
    grid_txt = puzzle_grid_spaces(puzzle)
    four = four_up_block([(x[0], x[5]) for x in first_four])

    return GUIDE_TEMPLATE.format(
        title=title,
        plevel=tier,
        pnum=n,
        pageno=12,
        givens=givens,
        grid=grid_txt,
        four_up=four,
    )


GUIDE_TEMPLATE = """# Large Print Sudoku - Book Layout Guide

This guide is a print-ready template. It shows the exact structure of a single
puzzle page and of an Answers (4-up) page, with margin and type guidance for
both common large-print trim sizes.

---

## 1. Trim sizes, margins & type

High contrast and generous whitespace are the priority. Pure black ink on a
warm white (cream) page reduces glare. Use a clean serif or humanist sans for
headings and a fixed-width face for the grid so columns stay aligned.

| Setting            | 6 x 9 in                | 8.5 x 11 in             |
|--------------------|-------------------------|-------------------------|
| Outside margin     | 0.5 in                  | 0.75 in                 |
| Inside (gutter)    | 0.75 in                 | 1.0 in                  |
| Top margin         | 0.75 in                 | 1.0 in                  |
| Bottom margin      | 0.75 in                 | 1.0 in                  |
| Title type size    | 22-26 pt bold           | 26-30 pt bold           |
| Difficulty label   | 14-16 pt                | 16-18 pt                |
| Grid cell digit    | 28-34 pt                | 36-44 pt                |
| One puzzle per page | yes                    | yes                     |
| Grid placement     | centered, upper-middle  | centered, upper-middle  |

Contrast & spacing rules:
- One puzzle per page. Never crowd two puzzles onto a single page.
- Cell size at least 0.45 in (6x9) / 0.6 in (8.5x11) so digits stay bold.
- Thick rules (2-3 pt) on the 3x3 box borders; thin rules (0.5-1 pt) inside.
- Leave a clear band of whitespace (>= 0.4 in) above and below the grid.

---

## 2. Single puzzle page (template)

```
+------------------------------------------------------------+  <- trim edge
|                  [ top margin / whitespace ]               |
|                                                            |
|   Puzzle {pnum} - {title}                                  |  <- Title (top-left or centered)
|   Difficulty: {plevel}        Clues: {givens}                       |  <- Difficulty + clue count
|                                                            |
|                                                            |
|              +-------+-------+-------+                      |
|              |  the 9 x 9 grid, centered  |                |
|              +-------+-------+-------+                      |
|                                                            |
|                                                            |
|   Notes: _________________________________________        |  <- optional notes line
|                                                            |
|                  [ bottom margin / whitespace ]            |
|                          -  {pageno}  -                         |  <- footer page number, centered
+------------------------------------------------------------+
```

### 2a. Title & difficulty block
- Place the **Puzzle number + Title** at the top (left-aligned for 6x9,
  centered for 8.5x11 both read well).
- Put **Difficulty** directly beneath it. Optionally show the clue count.
- Keep one blank line between this block and the grid.

### 2b. Optimized text grid (blanks are spaces, leaves room for margins)

The grid below is only 25 characters wide, so it floats comfortably inside the
margins on either trim size. Givens are printed; empty cells are spaces.

```text
{grid}
```

### 2c. Footer
- A single light **Notes** line (optional) sits below the grid.
- The **page number** is centered in the bottom margin, e.g. `-  12  -`.
- Running headers are optional; if used, keep them small (10-11 pt).

---

## 3. Answers page (4 mini-grids per page)

Answers live in a chapter at the back. Pack **four** solved grids per page in a
2 x 2 arrangement to save space while keeping them readable. Each answer is
labeled with the number that matches its puzzle.

```
+------------------------------------------------------------+
|   Answers 1 - 4                                            |  <- section header
|                                                            |
|   Answer 1                 Answer 2                        |
|   [ mini grid ]            [ mini grid ]                    |
|                                                            |
|   Answer 3                 Answer 4                        |
|   [ mini grid ]            [ mini grid ]                    |
|                                                            |
|                          -  101  -                          |
+------------------------------------------------------------+
```

Rendered example (real solutions for puzzles 1-4):

```text
{four_up}
```

Answer-page rules:
- 4 grids per page (2 columns x 2 rows). Digit size 12-16 pt is plenty here.
- Always label each grid `Answer N` so it maps to `Puzzle N`.
- Add the section header `Answers X - Y` at the top of each page.

---

## 4. Front/back matter checklist
- Title page, then a short "How to Solve" page (1 page).
- Puzzles grouped by difficulty: Medium, then Hard, then Extreme.
- Answers chapter at the very back, 4-up pages, numbered to match.
- Consistent footer page numbers throughout.
"""


if __name__ == "__main__":
    main()
