"""Render all five books to PDF files and report page counts."""
import os
from pdfgen import PDF
import book1, book2, book3, book4, book5

BOOKS = [book1, book2, book3, book4, book5]
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(OUT_DIR, exist_ok=True)


def main():
    print("Generating %d books...\n" % len(BOOKS))
    for mod in BOOKS:
        pdf = PDF()
        pdf.render_blocks(mod.blocks)
        path = os.path.join(OUT_DIR, mod.FILENAME)
        size = pdf.save(path)
        pages = len(pdf.pages)
        status = "OK" if 20 <= pages <= 30 else "CHECK PAGE COUNT"
        print("  %-44s  %2d pages  %6.1f KB  [%s]"
              % (mod.FILENAME, pages, size / 1024.0, status))
    print("\nAll files written to: %s" % OUT_DIR)


if __name__ == "__main__":
    main()
