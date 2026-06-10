# Large Print Sudoku - Book Layout Guide

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
|   Puzzle 1 - Morning Relaxation                                  |  <- Title (top-left or centered)
|   Difficulty: Medium        Clues: 31                       |  <- Difficulty + clue count
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
|                          -  12  -                         |  <- footer page number, centered
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
+-------+-------+-------+
|   3   |   1   |       |
| 5     |       | 2 8   |
| 4     | 2 9 8 |     5 |
+-------+-------+-------+
|       | 4     | 9     |
|   1 7 | 9 5 3 | 6 4   |
|     3 |     2 |       |
+-------+-------+-------+
| 3     | 1 6 4 |     7 |
|   2 4 |       |     6 |
|       |   2   |   5   |
+-------+-------+-------+
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
Answer 1                 Answer 2
2 3 8 | 5 1 7 | 4 6 9    3 8 4 | 7 1 9 | 6 5 2
5 7 9 | 3 4 6 | 2 8 1    5 1 7 | 2 6 3 | 9 4 8
4 6 1 | 2 9 8 | 7 3 5    9 6 2 | 4 5 8 | 1 3 7
------+-------+------    ------+-------+------
6 5 2 | 4 8 1 | 9 7 3    2 3 9 | 5 4 7 | 8 1 6
8 1 7 | 9 5 3 | 6 4 2    6 5 8 | 1 9 2 | 4 7 3
9 4 3 | 6 7 2 | 5 1 8    7 4 1 | 3 8 6 | 2 9 5
------+-------+------    ------+-------+------
3 9 5 | 1 6 4 | 8 2 7    4 9 6 | 8 3 5 | 7 2 1
7 2 4 | 8 3 5 | 1 9 6    1 2 3 | 6 7 4 | 5 8 9
1 8 6 | 7 2 9 | 3 5 4    8 7 5 | 9 2 1 | 3 6 4

Answer 3                 Answer 4
1 5 7 | 4 2 6 | 8 3 9    1 5 9 | 8 7 6 | 2 3 4
6 9 3 | 8 7 1 | 2 5 4    2 6 3 | 1 4 5 | 8 7 9
8 2 4 | 9 5 3 | 7 1 6    4 7 8 | 9 3 2 | 6 1 5
------+-------+------    ------+-------+------
7 6 2 | 5 3 4 | 1 9 8    5 4 6 | 2 9 3 | 7 8 1
5 1 9 | 6 8 7 | 4 2 3    8 1 7 | 6 5 4 | 3 9 2
3 4 8 | 1 9 2 | 6 7 5    9 3 2 | 7 8 1 | 5 4 6
------+-------+------    ------+-------+------
4 3 6 | 7 1 5 | 9 8 2    6 2 4 | 3 1 7 | 9 5 8
9 7 5 | 2 4 8 | 3 6 1    7 9 1 | 5 6 8 | 4 2 3
2 8 1 | 3 6 9 | 5 4 7    3 8 5 | 4 2 9 | 1 6 7

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
