# Senior Reader Book Series

Five short, illustrated PDF manuals written for readers over 50, each in large,
easy-to-read type with a stylized flat-cartoon cover. Every book opens with a
cover (page 1), a full-page disclaimer (page 2), and 20-30 pages of content.

| # | Book | Topic | Disclaimer category |
|---|------|-------|---------------------|
| 1 | Defending Your Digital Perimeter | Anti-scam & privacy tactics | Tech |
| 2 | The Everyday Culinary Herb Garden | Low-maintenance herb gardening | Health |
| 3 | Precision Cooking for Two (or One) | Cooking at a smaller scale | Health |
| 4 | Smart Money in Retirement | Everyday budgeting & fraud safety | Finance |
| 5 | Staying Strong and Steady | Gentle balance & mobility exercises | Health |

## Files

- `output/*.pdf` - the five finished books.
- `pdfgen.py` - a dependency-free, pure-Python PDF generator (standard fonts,
  vector cartoon covers; no third-party libraries required).
- `book1.py` ... `book5.py` - the content of each book as structured blocks.
- `build.py` - renders all five books into `output/`.

## Building

```bash
python3 build.py
```

No external dependencies are needed; the generator uses only the Python
standard library.

## Disclaimer

The information in these manuals is for general educational purposes only and is
not professional medical, financial, or legal advice. Readers should consult
appropriate licensed professionals before acting on the content.
