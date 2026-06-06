"""
A small, dependency-free PDF generator.

PDF is a text-based container format, so we can write valid PDFs by hand using
only the Python standard library. We use the built-in (non-embedded) standard
fonts Helvetica and Helvetica-Bold, which every PDF reader ships with, so no
font files are required.

Supported block types (see render_blocks):
    title_page, disclaimer, h1, h2, para, bullet, number, spacer, pagebreak,
    table, callout
"""

# --- Standard Helvetica glyph widths (units per 1000 em) ---------------------
_HELV = {
    ' ': 278, '!': 278, '"': 355, '#': 556, '$': 556, '%': 889, '&': 667,
    "'": 191, '(': 333, ')': 333, '*': 389, '+': 584, ',': 278, '-': 333,
    '.': 278, '/': 278, '0': 556, '1': 556, '2': 556, '3': 556, '4': 556,
    '5': 556, '6': 556, '7': 556, '8': 556, '9': 556, ':': 278, ';': 278,
    '<': 584, '=': 584, '>': 584, '?': 556, '@': 1015, 'A': 667, 'B': 667,
    'C': 722, 'D': 722, 'E': 667, 'F': 611, 'G': 778, 'H': 722, 'I': 278,
    'J': 500, 'K': 667, 'L': 556, 'M': 833, 'N': 722, 'O': 778, 'P': 667,
    'Q': 778, 'R': 722, 'S': 667, 'T': 611, 'U': 722, 'V': 667, 'W': 944,
    'X': 667, 'Y': 667, 'Z': 611, '[': 278, '\\': 278, ']': 278, '^': 469,
    '_': 556, '`': 333, 'a': 556, 'b': 556, 'c': 500, 'd': 556, 'e': 556,
    'f': 278, 'g': 556, 'h': 556, 'i': 222, 'j': 222, 'k': 500, 'l': 222,
    'm': 833, 'n': 556, 'o': 556, 'p': 556, 'q': 556, 'r': 333, 's': 500,
    't': 278, 'u': 556, 'v': 500, 'w': 722, 'x': 500, 'y': 500, 'z': 500,
    '{': 334, '|': 260, '}': 334, '~': 584,
}
_HELV_BOLD = {
    ' ': 278, '!': 333, '"': 474, '#': 556, '$': 556, '%': 889, '&': 722,
    "'": 238, '(': 333, ')': 333, '*': 389, '+': 584, ',': 278, '-': 333,
    '.': 278, '/': 278, '0': 556, '1': 556, '2': 556, '3': 556, '4': 556,
    '5': 556, '6': 556, '7': 556, '8': 556, '9': 556, ':': 333, ';': 333,
    '<': 584, '=': 584, '>': 584, '?': 611, '@': 975, 'A': 722, 'B': 722,
    'C': 722, 'D': 722, 'E': 667, 'F': 611, 'G': 778, 'H': 722, 'I': 278,
    'J': 556, 'K': 722, 'L': 611, 'M': 833, 'N': 722, 'O': 778, 'P': 667,
    'Q': 778, 'R': 722, 'S': 667, 'T': 611, 'U': 722, 'V': 667, 'W': 944,
    'X': 667, 'Y': 667, 'Z': 611, '[': 333, '\\': 278, ']': 333, '^': 584,
    '_': 556, '`': 333, 'a': 556, 'b': 611, 'c': 556, 'd': 611, 'e': 556,
    'f': 333, 'g': 611, 'h': 611, 'i': 278, 'j': 278, 'k': 556, 'l': 278,
    'm': 889, 'n': 611, 'o': 611, 'p': 611, 'q': 611, 'r': 389, 's': 556,
    't': 333, 'u': 611, 'v': 556, 'w': 778, 'x': 556, 'y': 556, 'z': 500,
    '{': 389, '|': 280, '}': 389, '~': 584,
}


def _sanitize(text):
    """Map common unicode punctuation to ASCII so it renders with WinAnsi."""
    repl = {
        '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"',
        '\u2013': '-', '\u2014': '--', '\u2026': '...', '\u00a0': ' ',
        '\u2022': '-', '\u2192': '->', '\u00bd': '1/2', '\u00b0': ' deg',
        '\u00e9': 'e', '\u2032': "'", '\u2033': '"',
    }
    for k, v in repl.items():
        text = text.replace(k, v)
    # Drop anything still outside printable ASCII.
    return ''.join(c if 32 <= ord(c) < 127 else '?' for c in text)


def text_width(text, size, bold=False):
    table = _HELV_BOLD if bold else _HELV
    total = 0
    for ch in text:
        total += table.get(ch, 556)
    return total / 1000.0 * size


def wrap(text, size, max_width, bold=False):
    """Word-wrap a string to fit max_width points. Returns list of lines."""
    text = _sanitize(text)
    words = text.split()
    if not words:
        return ['']
    lines = []
    cur = words[0]
    for w in words[1:]:
        trial = cur + ' ' + w
        if text_width(trial, size, bold) <= max_width:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def _esc(text):
    return _sanitize(text).replace('\\', r'\\').replace('(', r'\(').replace(')', r'\)')


class PDF:
    def __init__(self, page_w=612, page_h=792, margin=72):
        self.page_w = page_w
        self.page_h = page_h
        self.margin = margin
        self.left = margin
        self.right = page_w - margin
        self.top = page_h - margin
        self.bottom = margin
        self.text_width_max = self.right - self.left
        self.pages = []        # each page is a list of content-stream fragments
        self._ops = None       # current page op buffer
        self.y = None
        self.show_page_numbers = True

    # -- page management ------------------------------------------------------
    def new_page(self):
        self._ops = []
        self.pages.append(self._ops)
        self.y = self.top

    def _ensure_space(self, needed):
        if self.y - needed < self.bottom:
            self.new_page()

    # -- low level drawing ----------------------------------------------------
    def _font(self, bold):
        return '/F2' if bold else '/F1'

    def draw_text(self, x, y, text, size, bold=False, color=(0, 0, 0)):
        r, g, b = color
        self._ops.append(
            "%.3f %.3f %.3f rg BT %s %.2f Tf 1 0 0 1 %.2f %.2f Tm (%s) Tj ET 0 g"
            % (r, g, b, self._font(bold), size, x, y, _esc(text))
        )

    def draw_text_centered(self, y, text, size, bold=False, color=(0, 0, 0)):
        w = text_width(_sanitize(text), size, bold)
        x = (self.page_w - w) / 2.0
        self.draw_text(x, y, text, size, bold, color=color)

    def draw_line(self, x1, y1, x2, y2, width=1.0, gray=0.0):
        self._ops.append(
            "%.2f G %.2f w %.2f %.2f m %.2f %.2f l S"
            % (gray, width, x1, y1, x2, y2)
        )

    def fill_rect(self, x, y, w, h, gray=0.9):
        self._ops.append("%.3f g %.2f %.2f %.2f %.2f re f 0 g" % (gray, x, y, w, h))

    def stroke_rect(self, x, y, w, h, width=1.0, gray=0.0):
        self._ops.append(
            "%.2f G %.2f w %.2f %.2f %.2f %.2f re S" % (gray, width, x, y, w, h)
        )

    # -- colored vector primitives (used for the cartoon covers) -------------
    def rect_rgb(self, x, y, w, h, fill):
        r, g, b = fill
        self._ops.append("%.3f %.3f %.3f rg %.2f %.2f %.2f %.2f re f 0 g"
                         % (r, g, b, x, y, w, h))

    def _ellipse_path(self, cx, cy, rx, ry):
        k = 0.5523
        return (
            "%.2f %.2f m "
            "%.2f %.2f %.2f %.2f %.2f %.2f c "
            "%.2f %.2f %.2f %.2f %.2f %.2f c "
            "%.2f %.2f %.2f %.2f %.2f %.2f c "
            "%.2f %.2f %.2f %.2f %.2f %.2f c h"
            % (
                cx + rx, cy,
                cx + rx, cy + ry * k, cx + rx * k, cy + ry, cx, cy + ry,
                cx - rx * k, cy + ry, cx - rx, cy + ry * k, cx - rx, cy,
                cx - rx, cy - ry * k, cx - rx * k, cy - ry, cx, cy - ry,
                cx + rx * k, cy - ry, cx + rx, cy - ry * k, cx + rx, cy,
            )
        )

    def ellipse(self, cx, cy, rx, ry, fill=None, stroke=None, lw=1.0):
        path = self._ellipse_path(cx, cy, rx, ry)
        if fill is not None:
            r, g, b = fill
            self._ops.append("%.3f %.3f %.3f rg" % (r, g, b))
        if stroke is not None:
            r, g, b = stroke
            self._ops.append("%.3f %.3f %.3f RG %.2f w" % (r, g, b, lw))
        op = "B" if (fill is not None and stroke is not None) else (
            "f" if fill is not None else "S")
        self._ops.append(path + " " + op + " 0 g 0 G")

    def circle(self, cx, cy, r, fill=None, stroke=None, lw=1.0):
        self.ellipse(cx, cy, r, r, fill=fill, stroke=stroke, lw=lw)

    def polygon(self, pts, fill=None, stroke=None, lw=1.0):
        cmds = "%.2f %.2f m " % (pts[0][0], pts[0][1])
        cmds += " ".join("%.2f %.2f l" % (x, y) for x, y in pts[1:])
        cmds += " h"
        if fill is not None:
            r, g, b = fill
            self._ops.append("%.3f %.3f %.3f rg" % (r, g, b))
        if stroke is not None:
            r, g, b = stroke
            self._ops.append("%.3f %.3f %.3f RG %.2f w" % (r, g, b, lw))
        op = "B" if (fill is not None and stroke is not None) else (
            "f" if fill is not None else "S")
        self._ops.append(cmds + " " + op + " 0 g 0 G")

    def thick_line(self, x1, y1, x2, y2, width, color, cap=1):
        """A round-capped colored line - used as a 'capsule' for limbs/torso."""
        r, g, b = color
        self._ops.append(
            "%d J %.3f %.3f %.3f RG %.2f w %.2f %.2f m %.2f %.2f l S 0 G 0 J"
            % (cap, r, g, b, width, x1, y1, x2, y2))

    def polyline(self, pts, width, color, cap=1):
        r, g, b = color
        seg = "%.2f %.2f m " % (pts[0][0], pts[0][1])
        seg += " ".join("%.2f %.2f l" % (x, y) for x, y in pts[1:])
        self._ops.append("%d J %.3f %.3f %.3f RG %.2f w %s S 0 G 0 J"
                         % (cap, r, g, b, width, seg))

    # -- a simple flat cartoon person ----------------------------------------
    def person(self, cx, base, f=1.0, shirt=(0.30, 0.45, 0.75),
               pants=(0.25, 0.27, 0.32), skin=(0.98, 0.80, 0.66),
               hair=(0.55, 0.55, 0.58), pose='stand'):
        hip = base + 52 * f
        shoulder = hip + 60 * f
        head_cy = shoulder + 22 * f
        hr = 16 * f
        tw = 30 * f
        # legs
        self.thick_line(cx - 8 * f, hip, cx - 8 * f, base, 12 * f, pants)
        self.thick_line(cx + 8 * f, hip, cx + 8 * f, base, 12 * f, pants)
        # torso (capsule)
        self.thick_line(cx, hip, cx, shoulder, tw, shirt)
        # arms by pose
        sh_l = (cx - tw / 2 + 2 * f, shoulder - 4 * f)
        sh_r = (cx + tw / 2 - 2 * f, shoulder - 4 * f)
        if pose == 'arms_up':
            hand_l = (cx - tw / 2 - 14 * f, shoulder + 46 * f)
            hand_r = (cx + tw / 2 + 14 * f, shoulder + 46 * f)
        elif pose == 'wave':
            hand_l = (cx - tw / 2 - 20 * f, hip + 22 * f)
            hand_r = (cx + tw / 2 + 16 * f, shoulder + 40 * f)
        else:  # stand
            hand_l = (cx - tw / 2 - 12 * f, hip + 18 * f)
            hand_r = (cx + tw / 2 + 12 * f, hip + 18 * f)
        self.thick_line(sh_l[0], sh_l[1], hand_l[0], hand_l[1], 10 * f, shirt)
        self.thick_line(sh_r[0], sh_r[1], hand_r[0], hand_r[1], 10 * f, shirt)
        self.circle(hand_l[0], hand_l[1], 5 * f, fill=skin)
        self.circle(hand_r[0], hand_r[1], 5 * f, fill=skin)
        # head + hair + face
        self.circle(cx, head_cy, hr, fill=skin)
        self.ellipse(cx, head_cy + hr * 0.45, hr * 1.08, hr * 0.78, fill=hair)
        self.circle(cx - hr * 0.4, head_cy + 1 * f, 2.0 * f, fill=(0.2, 0.2, 0.2))
        self.circle(cx + hr * 0.4, head_cy + 1 * f, 2.0 * f, fill=(0.2, 0.2, 0.2))
        return {"head_cy": head_cy, "hr": hr, "hand_r": hand_r, "hand_l": hand_l,
                "shoulder": shoulder, "hip": hip}

    # -- cover page -----------------------------------------------------------
    def cover(self, title, subtitle, series, audience, scene, palette):
        self.new_page()
        W, H = self.page_w, self.page_h
        pal = palette
        # background
        self.rect_rgb(0, 0, W, H, pal['bg'])
        # top accent bar
        self.rect_rgb(0, H - 30, W, 30, pal['accent'])
        # decorative sun/emblem behind the scene
        self.circle(W / 2.0, 432, 128, fill=pal['circle'])
        # bottom band acts as the ground the characters stand on
        self.rect_rgb(0, 0, W, 158, pal['accent'])
        self.rect_rgb(0, 152, W, 8, pal['ground'])
        # the cartoon scene
        SCENES[scene](self, pal)
        # title
        ty = 712
        for line in wrap(title, 30, W - 96, bold=True):
            self.draw_text_centered(ty, line, 30, bold=True, color=pal['title'])
            ty -= 36
        # subtitle
        ty -= 6
        for line in wrap(subtitle, 13.5, W - 150, bold=False):
            self.draw_text_centered(ty, line, 13.5, bold=False, color=pal['sub'])
            ty -= 19
        # series + audience on the bottom band (white)
        white = (1, 1, 1)
        self.draw_text_centered(112, series, 13, bold=True, color=white)
        ay = 90
        for line in wrap(audience, 10.5, W - 130):
            self.draw_text_centered(ay, line, 10.5, color=white)
            ay -= 15

    # -- high level paragraph helpers ----------------------------------------
    def paragraph(self, text, size=14.5, bold=False, leading=None, gap_after=11,
                  indent=0, color_gray=0.0):
        if leading is None:
            leading = size * 1.6
        max_w = self.text_width_max - indent
        for line in wrap(text, size, max_w, bold):
            self._ensure_space(leading)
            if color_gray:
                self._ops.append("%.3f g" % color_gray)
            self.draw_text(self.left + indent, self.y - size, line, size, bold)
            if color_gray:
                self._ops.append("0 g")
            self.y -= leading
        self.y -= gap_after

    def bullet(self, text, size=14.5, leading=None, gap_after=7, marker='-'):
        if leading is None:
            leading = size * 1.55
        bullet_indent = 24
        max_w = self.text_width_max - bullet_indent
        lines = wrap(text, size, max_w)
        for i, line in enumerate(lines):
            self._ensure_space(leading)
            if i == 0:
                self.draw_text(self.left, self.y - size, marker, size, bold=True)
            self.draw_text(self.left + bullet_indent, self.y - size, line, size)
            self.y -= leading
        self.y -= gap_after

    def heading(self, text, level=1, gap_before=16, gap_after=10):
        size = 22 if level == 1 else 16.5
        bold = True
        if level == 1:
            # Start each chapter on a fresh page (unless the page is empty).
            if self.y is None or self.y < self.top - 1:
                self.new_page()
            self.y -= 6
        else:
            self._ensure_space(size * 1.6 + gap_before)
            self.y -= gap_before
        for line in wrap(text, size, self.text_width_max, bold):
            self._ensure_space(size * 1.4)
            self.draw_text(self.left, self.y - size, line, size, bold)
            self.y -= size * 1.34
        if level == 1:
            # underline rule
            self._ensure_space(6)
            self.draw_line(self.left, self.y + 2, self.right, self.y + 2,
                           width=1.4, gray=0.4)
        self.y -= gap_after

    def spacer(self, h=10):
        self.y -= h

    def callout(self, title, text, size=13):
        """A shaded box with a bold title and body text."""
        # Pre-compute height.
        title_lines = wrap(title, size + 1, self.text_width_max - 24, bold=True)
        body_lines = wrap(text, size, self.text_width_max - 24)
        line_h = size * 1.42
        box_h = 16 + len(title_lines) * (size + 1) * 1.3 + len(body_lines) * line_h + 12
        self._ensure_space(box_h + 8)
        top_y = self.y
        self.fill_rect(self.left, top_y - box_h, self.text_width_max, box_h, gray=0.93)
        self.draw_line(self.left, top_y, self.left, top_y - box_h, width=3, gray=0.4)
        cy = top_y - 14
        for ln in title_lines:
            self.draw_text(self.left + 14, cy - (size + 1), ln, size + 1, bold=True)
            cy -= (size + 1) * 1.3
        for ln in body_lines:
            self.draw_text(self.left + 14, cy - size, ln, size)
            cy -= line_h
        self.y = top_y - box_h - 12

    # -- tables ---------------------------------------------------------------
    def table(self, headers, rows, col_widths=None, size=11, gap_after=14):
        n = len(headers)
        avail = self.text_width_max
        if col_widths is None:
            col_widths = [avail / n] * n
        else:
            scale = avail / float(sum(col_widths))
            col_widths = [w * scale for w in col_widths]
        pad = 5
        line_h = size * 1.32

        def row_height(cells, bold=False):
            maxlines = 1
            for i, c in enumerate(cells):
                lines = wrap(str(c), size, col_widths[i] - 2 * pad, bold)
                maxlines = max(maxlines, len(lines))
            return maxlines * line_h + 2 * pad

        def draw_row(cells, y_top, bold=False, shade=None):
            h = row_height(cells, bold)
            if shade is not None:
                self.fill_rect(self.left, y_top - h, avail, h, gray=shade)
            x = self.left
            for i, c in enumerate(cells):
                lines = wrap(str(c), size, col_widths[i] - 2 * pad, bold)
                ty = y_top - pad - size
                for ln in lines:
                    self.draw_text(x + pad, ty, ln, size, bold)
                    ty -= line_h
                x += col_widths[i]
            # grid lines
            self.stroke_rect(self.left, y_top - h, avail, h, width=0.6, gray=0.55)
            x = self.left
            for i in range(n - 1):
                x += col_widths[i]
                self.draw_line(x, y_top, x, y_top - h, width=0.6, gray=0.55)
            return h

        # header
        hh = row_height(headers, bold=True)
        self._ensure_space(hh + line_h)
        self.y -= draw_row(headers, self.y, bold=True, shade=0.82)
        for ridx, r in enumerate(rows):
            h = row_height(r)
            if self.y - h < self.bottom:
                self.new_page()
                self.y -= draw_row(headers, self.y, bold=True, shade=0.82)
            shade = 0.96 if ridx % 2 == 0 else None
            self.y -= draw_row(r, self.y, shade=shade)
        self.y -= gap_after

    # -- specialty pages ------------------------------------------------------
    def title_page(self, title, subtitle, series, audience):
        self.new_page()
        # top rule
        self.draw_line(self.left, self.top - 6, self.right, self.top - 6,
                       width=2, gray=0.3)
        y = self.page_h * 0.62
        for line in wrap(title, 30, self.text_width_max - 20, bold=True):
            self.draw_text_centered(y, line, 30, bold=True)
            y -= 36
        y -= 14
        for line in wrap(subtitle, 15, self.text_width_max - 40, bold=False):
            self.draw_text_centered(y, line, 15, bold=False)
            y -= 21
        # lower block
        self.draw_line(self.left, self.bottom + 96, self.right, self.bottom + 96,
                       width=1, gray=0.5)
        self.draw_text_centered(self.bottom + 70, series, 12, bold=True)
        for i, line in enumerate(wrap(audience, 11, self.text_width_max - 60)):
            self.draw_text_centered(self.bottom + 50 - i * 15, line, 11)

    def disclaimer_page(self, category):
        """A full-page, bold disclaimer. Starts as page 2 of the book."""
        self.new_page()
        text = (
            "The information provided in this manual is intended for general "
            "educational and informational purposes only. The author is not a "
            "licensed medical professional, financial advisor, or legal "
            "attorney. Content regarding " + category + " should not be taken "
            "as professional advice. Readers should consult with appropriate "
            "professionals before executing any physical exercises or "
            "financial/legal changes outlined herein. The author and publisher "
            "assume no liability or responsibility for any actions taken, "
            "injuries sustained, or technical damages incurred resulting "
            "directly or indirectly from the use of this material."
        )
        size = 16
        leading = size * 1.6
        lines = wrap(text, size, self.text_width_max, bold=True)
        block_h = len(lines) * leading
        # vertically center the block on the page
        start_y = (self.page_h + block_h) / 2.0
        # header word
        self.draw_text_centered(self.top - 10, "DISCLAIMER", 13, bold=True)
        self.draw_line(self.left, self.top - 18, self.right, self.top - 18,
                       width=1, gray=0.5)
        y = min(start_y, self.top - 50)
        for line in lines:
            self.draw_text_centered(y - size, line, size, bold=True)
            y -= leading

    def notes_pages(self, title, count=2):
        """Render ruled note-taking pages, useful as a workbook companion."""
        for p in range(count):
            self.new_page()
            self.heading(title if count == 1 else "%s (%d of %d)"
                         % (title, p + 1, count), level=1)
            # draw evenly spaced ruled lines down the page
            y = self.y - 14
            while y > self.bottom + 4:
                self.draw_line(self.left, y, self.right, y, width=0.6, gray=0.7)
                y -= 30

    # -- render driver --------------------------------------------------------
    def render_blocks(self, blocks):
        for b in blocks:
            t = b['type']
            if t == 'title_page':
                self.title_page(b['title'], b.get('subtitle', ''),
                                b.get('series', ''), b.get('audience', ''))
            elif t == 'cover':
                self.cover(b['title'], b.get('subtitle', ''), b.get('series', ''),
                           b.get('audience', ''), b['scene'],
                           PALETTES[b.get('palette', b['scene'])])
            elif t == 'disclaimer':
                self.disclaimer_page(b['category'])
            elif t == 'newpage_content_start':
                self.new_page()
            elif t == 'pagebreak':
                self.new_page()
            elif t == 'h1':
                self.heading(b['text'], level=1)
            elif t == 'h2':
                self.heading(b['text'], level=2)
            elif t == 'para':
                self.paragraph(b['text'], size=b.get('size', 14.5),
                               bold=b.get('bold', False))
            elif t == 'bullet':
                self.bullet(b['text'])
            elif t == 'number':
                self.bullet(b['text'], marker=b.get('marker', '-'))
            elif t == 'spacer':
                self.spacer(b.get('h', 10))
            elif t == 'callout':
                self.callout(b['title'], b['text'])
            elif t == 'notes_pages':
                self.notes_pages(b.get('title', 'My Notes'), b.get('count', 2))
            elif t == 'table':
                self.table(b['headers'], b['rows'], b.get('col_widths'),
                           size=b.get('size', 10))
            else:
                raise ValueError("unknown block type: %s" % t)

    # -- page number footer ---------------------------------------------------
    def _add_footers(self):
        for i, ops in enumerate(self.pages):
            num = i + 1
            if num == 1:
                continue  # no footer on title page
            label = str(num)
            w = text_width(label, 9)
            x = (self.page_w - w) / 2.0
            ops.append("BT /F1 9 Tf 1 0 0 1 %.2f %.2f Tm (%s) Tj ET"
                       % (x, self.bottom - 24, label))

    # -- serialize ------------------------------------------------------------
    def save(self, path):
        if self.show_page_numbers:
            self._add_footers()
        objects = []  # list of (id, bytes)

        # Object ids:
        # 1 = catalog, 2 = pages, 3 = font helv, 4 = font helv-bold,
        # then per page: page dict + content stream
        n_pages = len(self.pages)
        page_obj_ids = []
        content_obj_ids = []
        next_id = 5
        for _ in range(n_pages):
            page_obj_ids.append(next_id); next_id += 1
            content_obj_ids.append(next_id); next_id += 1

        kids = " ".join("%d 0 R" % pid for pid in page_obj_ids)
        catalog = b"<< /Type /Catalog /Pages 2 0 R >>"
        pages = ("<< /Type /Pages /Count %d /Kids [%s] >>"
                 % (n_pages, kids)).encode('latin-1')
        font1 = (b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica "
                 b"/Encoding /WinAnsiEncoding >>")
        font2 = (b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold "
                 b"/Encoding /WinAnsiEncoding >>")

        objects.append((1, catalog))
        objects.append((2, pages))
        objects.append((3, font1))
        objects.append((4, font2))

        for idx in range(n_pages):
            stream_data = ("\n".join(self.pages[idx])).encode('latin-1')
            content_dict = ("<< /Length %d >>" % len(stream_data)).encode('latin-1')
            content_obj = content_dict + b"\nstream\n" + stream_data + b"\nendstream"
            page_dict = (
                "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %d %d] "
                "/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> "
                "/Contents %d 0 R >>"
                % (self.page_w, self.page_h, content_obj_ids[idx])
            ).encode('latin-1')
            objects.append((page_obj_ids[idx], page_dict))
            objects.append((content_obj_ids[idx], content_obj))

        objects.sort(key=lambda o: o[0])
        max_id = objects[-1][0]

        out = bytearray()
        out += b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
        offsets = {}
        for oid, body in objects:
            offsets[oid] = len(out)
            out += ("%d 0 obj\n" % oid).encode('latin-1')
            out += body
            out += b"\nendobj\n"

        xref_pos = len(out)
        count = max_id + 1
        out += ("xref\n0 %d\n" % count).encode('latin-1')
        out += b"0000000000 65535 f \n"
        for oid in range(1, count):
            if oid in offsets:
                out += ("%010d 00000 n \n" % offsets[oid]).encode('latin-1')
            else:
                out += b"0000000000 65535 f \n"
        out += ("trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"
                % (count, xref_pos)).encode('latin-1')

        with open(path, 'wb') as f:
            f.write(out)
        return len(out)



# ============================================================================
# Cover palettes and cartoon scenes
# ============================================================================

PALETTES = {
    'cyber': {
        'bg': (0.87, 0.93, 0.98), 'accent': (0.13, 0.24, 0.42),
        'circle': (0.78, 0.88, 0.96), 'ground': (0.10, 0.19, 0.34),
        'title': (0.11, 0.20, 0.36), 'sub': (0.27, 0.36, 0.50),
    },
    'herbs': {
        'bg': (0.89, 0.95, 0.85), 'accent': (0.24, 0.46, 0.27),
        'circle': (0.80, 0.90, 0.74), 'ground': (0.18, 0.36, 0.20),
        'title': (0.18, 0.38, 0.22), 'sub': (0.30, 0.44, 0.30),
    },
    'cooking': {
        'bg': (0.99, 0.93, 0.81), 'accent': (0.80, 0.42, 0.22),
        'circle': (0.99, 0.86, 0.66), 'ground': (0.62, 0.31, 0.15),
        'title': (0.66, 0.33, 0.15), 'sub': (0.52, 0.34, 0.22),
    },
    'finance': {
        'bg': (0.86, 0.93, 0.95), 'accent': (0.16, 0.42, 0.50),
        'circle': (0.76, 0.89, 0.92), 'ground': (0.10, 0.30, 0.36),
        'title': (0.11, 0.33, 0.39), 'sub': (0.25, 0.42, 0.47),
    },
    'exercise': {
        'bg': (0.93, 0.88, 0.96), 'accent': (0.45, 0.34, 0.62),
        'circle': (0.87, 0.80, 0.93), 'ground': (0.33, 0.24, 0.48),
        'title': (0.36, 0.26, 0.52), 'sub': (0.45, 0.38, 0.56),
    },
}


def _scene_cyber(pdf, pal):
    # A person at a laptop, guarded by a large shield with a checkmark.
    pdf.person(232, 168, f=1.25, shirt=(0.20, 0.35, 0.62),
               pants=(0.22, 0.24, 0.30), hair=(0.5, 0.5, 0.55), pose='stand')
    # laptop on a little stand in front of the person
    pdf.rect_rgb(196, 150, 74, 10, (0.30, 0.32, 0.38))      # base
    pdf.polygon([(204, 160), (262, 160), (256, 196), (210, 196)],
                fill=(0.85, 0.90, 0.96), stroke=(0.30, 0.32, 0.38), lw=2)
    # shield
    sx, sy = 408, 326
    pdf.polygon([(sx - 46, sy + 54), (sx + 46, sy + 54), (sx + 46, sy - 14),
                 (sx, sy - 58), (sx - 46, sy - 14)],
                fill=(0.20, 0.52, 0.80), stroke=(1, 1, 1), lw=4)
    pdf.polyline([(sx - 20, sy + 14), (sx - 4, sy - 4), (sx + 24, sy + 34)],
                 width=8, color=(1, 1, 1))


def _scene_herbs(pdf, pal):
    # A gardener tending a row of potted herbs.
    info = pdf.person(196, 168, f=1.2, shirt=(0.32, 0.55, 0.33),
                      pants=(0.40, 0.30, 0.22), hair=(0.62, 0.62, 0.6),
                      pose='wave')
    # watering can in the raised hand
    hx, hy = info['hand_r']
    pdf.rect_rgb(hx - 6, hy - 8, 26, 18, (0.55, 0.60, 0.66))
    pdf.polyline([(hx + 20, hy + 6), (hx + 34, hy + 14)], width=4,
                 color=(0.55, 0.60, 0.66))
    # three terracotta pots with green herbs on the ground band
    for px in (336, 398, 460):
        pdf.polygon([(px - 22, 184), (px + 22, 184), (px + 15, 152),
                     (px - 15, 152)], fill=(0.78, 0.43, 0.28))
        pdf.rect_rgb(px - 24, 182, 48, 7, (0.68, 0.36, 0.23))   # rim
        # foliage
        pdf.circle(px, 200, 14, fill=(0.30, 0.58, 0.32))
        pdf.circle(px - 12, 194, 10, fill=(0.36, 0.64, 0.36))
        pdf.circle(px + 12, 194, 10, fill=(0.26, 0.52, 0.28))
        pdf.thick_line(px, 184, px, 198, 3, (0.30, 0.45, 0.25))


def _scene_cooking(pdf, pal):
    # Two friendly cooks beside a steaming pot (cooking for two, or one).
    pdf.person(180, 168, f=1.12, shirt=(0.85, 0.48, 0.28),
               pants=(0.40, 0.30, 0.26), hair=(0.6, 0.6, 0.6), pose='stand')
    pdf.person(286, 168, f=1.12, shirt=(0.55, 0.62, 0.40),
               pants=(0.30, 0.32, 0.38), hair=(0.55, 0.5, 0.5), pose='stand')
    # cooking pot on the right
    px, py = 432, 168
    pdf.ellipse(px, py + 38, 42, 12, fill=(0.40, 0.42, 0.48))      # rim top
    pdf.rect_rgb(px - 42, py - 6, 84, 44, (0.34, 0.36, 0.42))      # body
    pdf.ellipse(px, py - 6, 42, 11, fill=(0.28, 0.30, 0.36))       # bottom curve
    pdf.thick_line(px - 54, py + 30, px - 44, py + 30, 7, (0.34, 0.36, 0.42))
    pdf.thick_line(px + 44, py + 30, px + 54, py + 30, 7, (0.34, 0.36, 0.42))
    # steam
    for dx in (-14, 0, 14):
        pdf.polyline([(px + dx, py + 50), (px + dx + 8, py + 64),
                      (px + dx - 6, py + 78), (px + dx + 6, py + 92)],
                     width=4, color=(0.95, 0.95, 0.95))


def _scene_finance(pdf, pal):
    # A person beside a growing stack of coins and a savings jar.
    pdf.person(214, 168, f=1.22, shirt=(0.20, 0.46, 0.54),
               pants=(0.25, 0.27, 0.33), hair=(0.55, 0.55, 0.58), pose='stand')
    # coin stack
    cx = 404
    for i, cy in enumerate((168, 184, 200, 216)):
        w = 38 - i * 2
        pdf.ellipse(cx, cy, w, 11, fill=(0.93, 0.76, 0.30),
                    stroke=(0.75, 0.58, 0.18), lw=1.5)
        pdf.draw_text_centered(cy - 5, "$", 13, bold=True,
                               color=(0.6, 0.45, 0.10))
    # savings jar to the right
    jx = 478
    pdf.rect_rgb(jx - 26, 152, 52, 60, (0.80, 0.90, 0.93))
    pdf.rect_rgb(jx - 26, 206, 52, 8, (0.55, 0.62, 0.66))     # lid
    pdf.ellipse(jx, 176, 12, 12, fill=(0.93, 0.76, 0.30))     # a coin inside
    pdf.draw_text_centered(171, "$", 12, bold=True, color=(0.6, 0.45, 0.10))


def _scene_exercise(pdf, pal):
    # A person stretching upward, with a small heart for healthy living.
    pdf.person(300, 168, f=1.28, shirt=(0.46, 0.35, 0.64),
               pants=(0.30, 0.32, 0.40), hair=(0.6, 0.6, 0.62), pose='arms_up')
    # a calm second figure seated nearby on the ground (suggested with a dot)
    pdf.circle(196, 252, 11, fill=(0.98, 0.80, 0.66))        # head
    pdf.thick_line(196, 220, 196, 244, 22, (0.55, 0.50, 0.70))  # seated body
    pdf.thick_line(196, 222, 222, 214, 9, (0.55, 0.50, 0.70))   # leg
    # heart above the stretcher
    hx, hy = 300, 360
    pdf.circle(hx - 9, hy + 4, 9, fill=(0.85, 0.32, 0.42))
    pdf.circle(hx + 9, hy + 4, 9, fill=(0.85, 0.32, 0.42))
    pdf.polygon([(hx - 17, hy + 6), (hx + 17, hy + 6), (hx, hy - 16)],
                fill=(0.85, 0.32, 0.42))


SCENES = {
    'cyber': _scene_cyber,
    'herbs': _scene_herbs,
    'cooking': _scene_cooking,
    'finance': _scene_finance,
    'exercise': _scene_exercise,
}
