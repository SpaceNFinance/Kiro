"""Independent verifier: parse sudoku_book_full.md and confirm that
  1. every starting grid has exactly ONE solution, and
  2. that solution equals the printed Answer N (mapping is correct).

Run:  python3 verify_book.py
"""
import re
import sys

import sudoku_gen as sg


def parse_puzzle_rows(block_lines):
    grid = []
    for ln in block_lines:
        if not ln.startswith("|"):
            continue
        groups = [g for g in ln.split("|")[1:-1]]
        row = []
        for g in groups:
            for idx in (1, 3, 5):
                ch = g[idx] if idx < len(g) else " "
                row.append(0 if ch == " " else int(ch))
        grid.append(row)
    return grid


def parse_puzzles(text):
    puzzles = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = re.match(r"## Puzzle (\d+):", lines[i])
        if m:
            num = int(m.group(1))
            # find the ```text block
            while i < len(lines) and not lines[i].startswith("```text"):
                i += 1
            block = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                block.append(lines[i])
                i += 1
            puzzles[num] = parse_puzzle_rows(block)
        i += 1
    return puzzles


def parse_answers(text):
    """Parse the 4-up answer blocks into {num: 9x9 grid}."""
    answers = {}
    # isolate the Answers chapter
    chap = text.split("\n# Answers\n", 1)[1]
    blocks = re.findall(r"```text\n(.*?)```", chap, re.S)
    for blk in blocks:
        lines = blk.splitlines()
        # find header lines containing "Answer N"
        # columns: left grid occupies cols [0:21], right grid cols [25:]
        # rows come in groups: header, then 11 grid lines (9 data + 2 sep)
        r = 0
        while r < len(lines):
            hdr = lines[r]
            nums = re.findall(r"Answer (\d+)", hdr)
            if nums:
                grid_lines = lines[r + 1:r + 12]
                cols = {0: int(nums[0])}
                if len(nums) > 1:
                    cols[25] = int(nums[1])
                for off, num in cols.items():
                    g = []
                    for gl in grid_lines:
                        seg = gl[off:off + 21]
                        digits = [int(c) for c in seg if c.isdigit()]
                        if len(digits) == 9:
                            g.append(digits)
                    if len(g) == 9:
                        answers[num] = g
                r += 12
            else:
                r += 1
    return answers


def solve_unique(grid):
    test = [row[:] for row in grid]
    count = sg._count_solutions(test, limit=2)
    # produce the (single) solution
    sol = [row[:] for row in grid]
    _fill_one(sol)
    return count, sol


def _fill_one(grid):
    spot = sg._find_empty(grid)
    if spot is None:
        return True
    r, c = spot
    for v in range(1, 10):
        if sg._valid(grid, r, c, v):
            grid[r][c] = v
            if _fill_one(grid):
                return True
            grid[r][c] = 0
    return False


def main():
    with open("sudoku_book_full.md", encoding="utf-8") as f:
        text = f.read()
    puzzles = parse_puzzles(text)
    answers = parse_answers(text)

    print("Parsed {} puzzles, {} answers".format(len(puzzles), len(answers)))
    problems = 0
    for num in sorted(puzzles):
        grid = puzzles[num]
        count, sol = solve_unique(grid)
        if count != 1:
            print("  Puzzle {}: NOT UNIQUE (solutions>={})".format(num, count))
            problems += 1
            continue
        ans = answers.get(num)
        if ans is None:
            print("  Puzzle {}: missing Answer".format(num))
            problems += 1
        elif ans != sol:
            print("  Puzzle {}: Answer does NOT match unique solution".format(num))
            problems += 1
    if problems == 0:
        print("ALL {} PUZZLES OK: unique solution + correct mapped answer.".format(len(puzzles)))
        return 0
    print("FAILURES: {}".format(problems))
    return 1


if __name__ == "__main__":
    sys.exit(main())
