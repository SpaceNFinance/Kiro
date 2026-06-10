"""Render the full 60-puzzle book to a single print-ready HTML file.

Parses sudoku_book_full.md (already generated) so it runs instantly --
no puzzle regeneration. Produces sudoku_book_full.html with:
  - one puzzle per page (drawn grid, large print),
  - an Answers chapter packed 4 mini-grids per page,
  - print CSS so "Print to PDF" gives a clean book at the chosen trim size.

Run:  python3 book_to_html.py
"""
import re

import verify_book as vb  # reuse the markdown parsers

N = 9


INTRO_HTML = """
<p>Welcome. Whatever brought you to this book &mdash; a love of numbers, a
quiet morning with a cup of tea, or simply the wish to keep the mind busy and
bright &mdash; you are in good company. Sudoku has charmed millions of people
around the world, and it is about to become a friendly part of your day.</p>

<p>The puzzle has a longer and more surprising story than most people imagine.
Its roots reach back to the 1700s and the Swiss mathematician Leonhard Euler,
who studied &ldquo;Latin squares&rdquo; &mdash; grids in which each symbol
appears exactly once in every row and column. The modern game took shape much
later. In 1979, an American puzzle designer named Howard Garns created a
number puzzle for Dell magazines and called it &ldquo;Number Place.&rdquo; It
found its true home in Japan, where the publisher Nikoli introduced it in 1984
and gave it the name we use today: Sudoku, drawn from a phrase meaning
&ldquo;the digits must stay single.&rdquo; Two decades later, a New Zealander
named Wayne Gould wrote a computer program to generate puzzles and offered them
to newspapers everywhere. By 2005, Sudoku had become a beloved daily ritual on
nearly every continent.</p>

<p>Its lasting popularity is no accident. Beyond the simple pleasure of solving,
Sudoku invites the mind to do wonderful work. Each grid calls on logic,
concentration, and working memory &mdash; the skill of holding several
possibilities in mind at once. Hunting for the next number sharpens pattern
recognition and rewards patience, and finishing a grid brings a warm sense of
accomplishment. Those who study the mind often point to the value of regular,
enjoyable mental activity, and a puzzle that is both calming and gently
challenging makes an ideal companion for that healthy habit. Think of every
session as a pleasant walk for your memory and focus.</p>

<p>A few gentle words before you begin. There is no clock here and no need to
rush. Every puzzle in this book has exactly one solution, and each one can be
reached through careful, step-by-step reasoning &mdash; never guesswork. A
pencil and a soft eraser are your best friends; mistakes are simply part of the
journey. Start with the Medium puzzles to warm up, then move to Hard and
Extreme as your confidence grows. When you would like to check your work, the
answers wait at the back of the book, each one numbered to match its puzzle.</p>

<p class="signoff">Settle in, take a deep breath, and enjoy. Happy puzzling!</p>
"""


# Five short, encouraging notes shown in italic above each puzzle (rotating).
TIPS = [
    "A few quiet minutes with a puzzle each day keep the mind curious and bright.",
    "Every number you place is a small victory \u2014 enjoy each one.",
    "There is no clock here. Take your time, and let the answer come to you.",
    "A sharp mind is built one happy habit at a time.",
    "Mistakes are part of the fun \u2014 erase, smile, and try again.",
]


def parse_meta(text):
    """Return {num: (title, difficulty, clues)}."""
    meta = {}
    for m in re.finditer(
        r"## Puzzle (\d+): (.+?)\n\*\*Difficulty:\*\* (\w+).*?\n\*\*Clues:\*\* (\d+)",
        text, re.S,
    ):
        num = int(m.group(1))
        meta[num] = (m.group(2).strip(), m.group(3).strip(), int(m.group(4)))
    return meta


def big_table(grid):
    rows = []
    for r in range(N):
        cells = []
        for c in range(N):
            v = grid[r][c]
            if v == 0:
                cells.append('<td class="blank">&nbsp;</td>')
            else:
                cells.append("<td>{}</td>".format(v))
        rows.append("<tr>{}</tr>".format("".join(cells)))
    return '<table class="sudoku big">{}</table>'.format("".join(rows))


def mini_table(grid):
    rows = []
    for r in range(N):
        cells = ["<td>{}</td>".format(grid[r][c]) for c in range(N)]
        rows.append("<tr>{}</tr>".format("".join(cells)))
    return '<table class="sudoku mini">{}</table>'.format("".join(rows))


CSS = """
:root { --ink:#000; --paper:#fffdf7; }
* { box-sizing: border-box; }
body { font-family: Georgia, "Times New Roman", serif; color: var(--ink);
       background: var(--paper); margin: 0; }
.book-title { text-align:center; padding:120px 40px 60px; }
.book-title h1 { font-size:52px; margin:0 0 16px; }
.book-title p { font-size:22px; color:#444; }
.tier-divider { page-break-before: always; text-align:center; padding-top:200px; }
.tier-divider h2 { font-size:46px; border:none; }

.page { page-break-after: always; page-break-inside: avoid; break-inside: avoid;
        padding:36px 48px; display:flex; flex-direction:column; }
.puzzle-head h2 { font-size:34px; margin:0 0 4px; }
.puzzle-head .diff { font-size:20px; color:#333; margin:0 0 6px; }
.tip { font-style:italic; font-size:19px; color:#3a3a3a; text-align:center;
       margin:6px 0 18px; line-height:1.4; }
.grid-wrap { display:flex; align-items:center; justify-content:center;
             margin:8px 0 14px; }
.notes { font-size:17px; color:#555; margin-top:14px; }
.foot { text-align:center; font-size:15px; color:#777; margin-top:14px; }

/* Introduction page */
.intro { page-break-after: always; padding:64px 72px; }
.intro h2 { font-size:42px; text-align:center; margin:0 0 30px; }
.intro p { font-size:19.5px; line-height:1.7; margin:0 0 15px; text-align:justify; }
.intro .signoff { text-align:center; font-style:italic; color:#444; margin-top:22px; }

table.sudoku { border-collapse:collapse; }
table.sudoku td { text-align:center; vertical-align:middle; font-weight:bold;
                  border:1px solid #888; }
table.sudoku.big td { width:62px; height:62px; font-size:34px; }
table.sudoku.big td.blank { color:#fff; }
table.sudoku.big tr:first-child td { border-top:3px solid var(--ink); }
table.sudoku.big tr td:first-child { border-left:3px solid var(--ink); }
table.sudoku.big tr td:last-child { border-right:3px solid var(--ink); }
table.sudoku.big tr:last-child td { border-bottom:3px solid var(--ink); }
table.sudoku.big tr:nth-child(3n) td { border-bottom:3px solid var(--ink); }
table.sudoku.big td:nth-child(3n) { border-right:3px solid var(--ink); }

table.sudoku.mini td { width:24px; height:24px; font-size:14px; }
table.sudoku.mini tr:first-child td { border-top:2.5px solid var(--ink); }
table.sudoku.mini tr td:first-child { border-left:2.5px solid var(--ink); }
table.sudoku.mini tr td:last-child { border-right:2.5px solid var(--ink); }
table.sudoku.mini tr:last-child td { border-bottom:2.5px solid var(--ink); }
table.sudoku.mini tr:nth-child(3n) td { border-bottom:2.5px solid var(--ink); }
table.sudoku.mini td:nth-child(3n) { border-right:2.5px solid var(--ink); }

.ans-page { page-break-after: always; padding:40px 48px; }
.ans-page h3 { font-size:26px; margin:0 0 20px; }
.ans-grid { display:grid; grid-template-columns:1fr 1fr; gap:34px 24px;
            justify-items:center; }
.ans-cell { text-align:center; break-inside: avoid; page-break-inside: avoid; }
.ans-cell .lbl { font-size:18px; font-weight:bold; margin-bottom:8px; }
@page { size: 8.5in 11in; margin: 0.6in; }
"""


def main():
    with open("sudoku_book_full.md", encoding="utf-8") as f:
        text = f.read()

    puzzles = vb.parse_puzzles(text)       # {num: grid}
    answers = vb.parse_answers(text)       # {num: grid}
    meta = parse_meta(text)

    nums = sorted(puzzles)
    parts = ["<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'>",
             "<meta name='viewport' content='width=device-width, initial-scale=1'>",
             "<title>Large Print Sudoku - 60 Puzzles</title>",
             "<style>{}</style></head><body>".format(CSS)]

    # Title page
    parts.append("<div class='book-title'><h1>Large Print Sudoku</h1>"
                 "<p>60 Puzzles &middot; Medium &middot; Hard &middot; Extreme</p>"
                 "<p>Every puzzle has exactly one solution. "
                 "Answers are in the back, numbered to match.</p></div>")

    # Introduction page
    parts.append("<div class='intro'><h2>Welcome to Your Puzzle Book</h2>{}</div>"
                 .format(INTRO_HTML))

    # Puzzle pages, grouped by tier with a divider
    last_tier = None
    for num in nums:
        title, diff, clues = meta[num]
        if diff != last_tier:
            last_tier = diff
            parts.append("<div class='tier-divider'><h2>{} Puzzles</h2></div>".format(diff))
        parts.append("<div class='page'>")
        parts.append("<div class='puzzle-head'><h2>Puzzle {}: {}</h2>"
                     "<p class='diff'>Difficulty: {} &nbsp;&middot;&nbsp; Clues: {}</p></div>"
                     .format(num, title, diff, clues))
        parts.append("<p class='tip'><em>{}</em></p>".format(TIPS[(num - 1) % len(TIPS)]))
        parts.append("<div class='grid-wrap'>{}</div>".format(big_table(puzzles[num])))
        parts.append("<div class='notes'>Notes: "
                     "________________________________________________</div>")
        parts.append("<div class='foot'>&middot; {} &middot;</div>".format(num))
        parts.append("</div>")

    # Answers chapter, 4 per page
    parts.append("<div class='tier-divider'><h2>Answers</h2></div>")
    for i in range(0, len(nums), 4):
        chunk = nums[i:i + 4]
        parts.append("<div class='ans-page'>")
        parts.append("<h3>Answers {} - {}</h3>".format(chunk[0], chunk[-1]))
        parts.append("<div class='ans-grid'>")
        for num in chunk:
            grid = answers.get(num)
            cell = mini_table(grid) if grid else "<em>missing</em>"
            parts.append("<div class='ans-cell'><div class='lbl'>Answer {}</div>{}</div>"
                         .format(num, cell))
        parts.append("</div></div>")

    parts.append("</body></html>")
    html = "\n".join(parts)

    with open("sudoku_book_full.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Wrote sudoku_book_full.html  ({} puzzles, {} answers, {:.1f} KB)"
          .format(len(puzzles), len(answers), len(html) / 1024.0))


if __name__ == "__main__":
    main()
