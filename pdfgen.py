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

    # -- improved cartoon person ----------------------------------------------
    def person(self, cx, base, f=1.0, shirt=(0.85, 0.38, 0.26),
               pants=(0.30, 0.34, 0.50), skin=(0.97, 0.78, 0.62),
               hair=(0.42, 0.28, 0.18), shoe=(0.22, 0.18, 0.14),
               pose='stand', gender='m'):
        """
        A warmer, rounder cartoon person.
        pose: 'stand' | 'wave' | 'arms_up' | 'sit' | 'lean'
        gender: 'm' | 'f'  (affects hair silhouette only)
        """
        # proportions
        leg_h   = 62 * f
        torso_h = 58 * f
        neck_h  = 10 * f
        hr      = 18 * f          # head radius
        tw      = 32 * f          # torso half-width (used as line width)
        leg_w   = 13 * f
        arm_w   = 11 * f

        foot_y  = base
        hip_y   = foot_y + leg_h
        shldr_y = hip_y  + torso_h
        neck_y  = shldr_y + neck_h
        head_cy = neck_y  + hr

        # ── shadow ellipse under feet ──────────────────────────────────────
        self.ellipse(cx, foot_y + 4, 22 * f, 6 * f,
                     fill=(0.0, 0.0, 0.0, 0.0) if False else None)
        # (skip: shadow looks odd without transparency support)

        # ── legs ──────────────────────────────────────────────────────────
        if pose == 'sit':
            # left leg horizontal, right leg tucked
            self.thick_line(cx - 10*f, hip_y, cx - 38*f, hip_y - 10*f,
                            leg_w, pants)
            self.thick_line(cx + 10*f, hip_y, cx + 36*f, hip_y - 8*f,
                            leg_w, pants)
            # shoes at end of each leg
            self.ellipse(cx - 44*f, hip_y - 10*f, 10*f, 6*f, fill=shoe)
            self.ellipse(cx + 42*f, hip_y - 8*f,  10*f, 6*f, fill=shoe)
        else:
            self.thick_line(cx - 9*f, hip_y, cx - 9*f, foot_y + 6*f,
                            leg_w, pants)
            self.thick_line(cx + 9*f, hip_y, cx + 9*f, foot_y + 6*f,
                            leg_w, pants)
            # rounded shoe bumps
            self.ellipse(cx - 9*f,  foot_y + 5*f, 12*f, 7*f, fill=shoe)
            self.ellipse(cx + 9*f,  foot_y + 5*f, 12*f, 7*f, fill=shoe)

        # ── torso (wide rounded capsule) ───────────────────────────────────
        self.thick_line(cx, hip_y, cx, shldr_y, tw * 2.0, shirt)

        # ── shirt collar V ────────────────────────────────────────────────
        collar = (
            min(shirt[0] + 0.12, 1.0),
            min(shirt[1] + 0.12, 1.0),
            min(shirt[2] + 0.12, 1.0),
        )
        self.polygon(
            [(cx - 7*f, shldr_y - 4*f),
             (cx,       shldr_y - 16*f),
             (cx + 7*f, shldr_y - 4*f)],
            fill=collar
        )

        # ── arms ──────────────────────────────────────────────────────────
        sh_l = (cx - tw + 2*f, shldr_y - 8*f)
        sh_r = (cx + tw - 2*f, shldr_y - 8*f)

        if pose == 'arms_up':
            hand_l = (cx - tw - 16*f, shldr_y + 48*f)
            hand_r = (cx + tw + 16*f, shldr_y + 48*f)
        elif pose == 'wave':
            hand_l = (cx - tw - 18*f, hip_y + 20*f)
            hand_r = (cx + tw + 18*f, shldr_y + 42*f)
        elif pose == 'lean':
            hand_l = (cx - tw - 22*f, hip_y + 8*f)
            hand_r = (cx + tw + 10*f, hip_y + 34*f)
        elif pose == 'sit':
            hand_l = (cx - 28*f, hip_y + 16*f)
            hand_r = (cx + 28*f, hip_y + 16*f)
        else:  # stand
            hand_l = (cx - tw - 14*f, hip_y + 16*f)
            hand_r = (cx + tw + 14*f, hip_y + 16*f)

        self.thick_line(sh_l[0], sh_l[1], hand_l[0], hand_l[1], arm_w, shirt)
        self.thick_line(sh_r[0], sh_r[1], hand_r[0], hand_r[1], arm_w, shirt)

        # ── hands (palm + 3 finger nubs) ──────────────────────────────────
        for hx, hy in (hand_l, hand_r):
            self.circle(hx, hy, 6*f, fill=skin)
            # three small finger bumps along the top
            for di in (-1, 0, 1):
                fx = hx + di * 4*f
                fy = hy + 5*f
                self.circle(fx, fy, 2.8*f, fill=skin)

        # ── neck ──────────────────────────────────────────────────────────
        self.thick_line(cx, neck_y - 4*f, cx, shldr_y, 12*f, skin)

        # ── head (slightly oval, warm skin) ───────────────────────────────
        self.ellipse(cx, head_cy, hr, hr * 1.05, fill=skin)

        # ── ears ──────────────────────────────────────────────────────────
        self.ellipse(cx - hr + 2*f, head_cy - 2*f, 5*f, 7*f, fill=skin)
        self.ellipse(cx + hr - 2*f, head_cy - 2*f, 5*f, 7*f, fill=skin)

        # ── hair ──────────────────────────────────────────────────────────
        if gender == 'f':
            # longer flowing hair (two side lobes + top cap)
            self.ellipse(cx - hr * 0.7, head_cy - hr * 0.5,
                         hr * 0.7, hr * 1.3, fill=hair)
            self.ellipse(cx + hr * 0.7, head_cy - hr * 0.5,
                         hr * 0.7, hr * 1.3, fill=hair)
            self.ellipse(cx, head_cy + hr * 0.55, hr * 1.10, hr * 0.72, fill=hair)
        else:
            # short neat hair: top cap + slight side taper
            self.ellipse(cx, head_cy + hr * 0.55, hr * 1.06, hr * 0.68, fill=hair)
            self.ellipse(cx - hr * 0.55, head_cy + hr * 0.1,
                         hr * 0.5, hr * 0.62, fill=hair)
            self.ellipse(cx + hr * 0.55, head_cy + hr * 0.1,
                         hr * 0.5, hr * 0.62, fill=hair)

        # ── eyes (white sclera + dark iris + small highlight) ─────────────
        for ex, sign in ((cx - hr * 0.38, -1), (cx + hr * 0.38, 1)):
            ey = head_cy + 3*f
            self.ellipse(ex, ey, 4.5*f, 4.0*f, fill=(1, 1, 1))
            self.circle(ex, ey, 2.8*f, fill=(0.18, 0.12, 0.08))
            self.circle(ex + 1.2*f, ey + 1.2*f, 1.0*f, fill=(1, 1, 1))

        # ── eyebrows ──────────────────────────────────────────────────────
        brow = (max(hair[0]-0.05,0), max(hair[1]-0.05,0), max(hair[2]-0.05,0))
        for ex in (cx - hr*0.38, cx + hr*0.38):
            self.thick_line(ex - 4*f, head_cy + 9*f,
                            ex + 4*f, head_cy + 10*f, 2*f, brow)

        # ── nose (small dot/bump) ─────────────────────────────────────────
        nose_c = (skin[0]*0.88, skin[1]*0.75, skin[2]*0.70)
        self.ellipse(cx, head_cy - 1*f, 2.5*f, 3*f, fill=nose_c)

        # ── smile ─────────────────────────────────────────────────────────
        # drawn as two overlapping ellipses (light arc trick)
        smile_c = (0.72, 0.32, 0.24)
        self.ellipse(cx, head_cy - 8*f, 7*f, 4.5*f, fill=smile_c)
        self.ellipse(cx, head_cy - 6.5*f, 6*f, 3.5*f, fill=skin)

        # ── cheek blush ───────────────────────────────────────────────────
        blush = (1.0, 0.72, 0.68)
        self.ellipse(cx - hr*0.62, head_cy - 3*f, 5*f, 3.5*f, fill=blush)
        self.ellipse(cx + hr*0.62, head_cy - 3*f, 5*f, 3.5*f, fill=blush)

        return {
            "head_cy": head_cy, "hr": hr,
            "hand_r": hand_r, "hand_l": hand_l,
            "shoulder": shldr_y, "hip": hip_y,
            "foot_y": foot_y,
        }

    # -- cover page -----------------------------------------------------------
    def cover(self, title, subtitle, series, audience, scene, palette):
        self.new_page()
        W, H = self.page_w, self.page_h
        p = palette

        # ── sky background: two-tone gradient (stacked bands) ─────────────
        sky_top = p['sky_top']
        sky_bot = p['sky_mid']
        # approximate a gradient with 6 horizontal bands
        for i in range(6):
            t = i / 5.0
            band_col = tuple(sky_top[c] + (sky_bot[c] - sky_top[c]) * t
                             for c in range(3))
            bh = (H - 180) / 6.0
            self.rect_rgb(0, 180 + (5 - i) * bh, W, bh + 1, band_col)

        # ── ground / floor (two-tone) ─────────────────────────────────────
        self.rect_rgb(0, 0,   W, 180, p['ground_dark'])
        self.rect_rgb(0, 152, W,  40, p['ground_light'])

        # ── horizon glow ellipse ──────────────────────────────────────────
        self.ellipse(W / 2.0, 192, 210, 56, fill=p['glow'])

        # ── fluffy clouds (3 overlapping circles each) ────────────────────
        for cx_c, cy_c in ((130, 630), (390, 680), (530, 610)):
            for dx, s in ((-22, 20), (0, 26), (22, 20)):
                self.circle(cx_c + dx, cy_c, s, fill=p['cloud'])

        # ── large warm sun / moon disc ────────────────────────────────────
        self.circle(W - 106, H - 128, 62, fill=p['sun'])
        self.circle(W - 106, H - 128, 54, fill=p['sun_inner'])

        # ── scene-specific illustration ───────────────────────────────────
        SCENES[scene](self, p)

        # ── title card (rounded-rect feel via two stacked rects) ──────────
        card_y = H - 72
        card_h = 132
        self.rect_rgb(0, card_y - card_h, W, card_h + 2, p['card_bg'])
        # top border line of card
        self.thick_line(0, card_y, W, card_y, 4, p['card_border'])

        # ── series badge (small pill at top of card) ──────────────────────
        bw, bh = 220, 20
        bx = (W - bw) / 2.0
        by = card_y - 10
        self.rect_rgb(bx, by, bw, bh, p['badge_bg'])
        self.draw_text_centered(by + 5, series, 10, bold=True,
                                color=p['badge_text'])

        # ── title text ────────────────────────────────────────────────────
        ty = card_y - 38
        for line in wrap(title, 27, W - 80, bold=True):
            self.draw_text_centered(ty, line, 27, bold=True, color=p['title'])
            ty -= 32

        # ── subtitle ──────────────────────────────────────────────────────
        ty -= 4
        for line in wrap(subtitle, 12, W - 120):
            self.draw_text_centered(ty, line, 12, color=p['sub'])
            ty -= 17

        # ── footer strip ──────────────────────────────────────────────────
        self.rect_rgb(0, 0, W, 36, p['footer_bg'])
        self.draw_text_centered(13, audience, 9.5, color=p['footer_text'])

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
# Cover palettes and cartoon scenes  (v2 — warmer, richer)
# ============================================================================

# Each palette has:
#   sky_top / sky_mid  – sky gradient bands (top → horizon)
#   ground_dark / ground_light – ground strip
#   glow               – warm horizon ellipse
#   cloud              – cloud puffs
#   sun / sun_inner    – sun disc colours
#   card_bg            – title card background
#   card_border        – top rule of title card
#   badge_bg / badge_text – series pill
#   title / sub        – title & subtitle text
#   footer_bg / footer_text – bottom strip

PALETTES = {
    # Book 1 – cyber: twilight blues → warm amber glow
    'cyber': {
        'sky_top':      (0.16, 0.22, 0.44),
        'sky_mid':      (0.52, 0.62, 0.82),
        'ground_dark':  (0.12, 0.17, 0.32),
        'ground_light': (0.22, 0.30, 0.50),
        'glow':         (0.94, 0.74, 0.44),
        'cloud':        (0.68, 0.74, 0.90),
        'sun':          (0.98, 0.84, 0.46),
        'sun_inner':    (0.99, 0.92, 0.66),
        'card_bg':      (0.97, 0.96, 0.92),
        'card_border':  (0.22, 0.34, 0.62),
        'badge_bg':     (0.22, 0.34, 0.62),
        'badge_text':   (1.0, 1.0, 1.0),
        'title':        (0.14, 0.22, 0.44),
        'sub':          (0.34, 0.40, 0.56),
        'footer_bg':    (0.22, 0.34, 0.62),
        'footer_text':  (0.90, 0.94, 1.0),
    },
    # Book 2 – herbs: warm golden morning, lush greens
    'herbs': {
        'sky_top':      (0.52, 0.74, 0.90),
        'sky_mid':      (0.94, 0.84, 0.62),
        'ground_dark':  (0.28, 0.48, 0.24),
        'ground_light': (0.46, 0.66, 0.34),
        'glow':         (0.99, 0.94, 0.68),
        'cloud':        (0.99, 0.98, 0.92),
        'sun':          (0.99, 0.84, 0.30),
        'sun_inner':    (0.99, 0.96, 0.72),
        'card_bg':      (0.98, 0.96, 0.88),
        'card_border':  (0.30, 0.52, 0.24),
        'badge_bg':     (0.30, 0.52, 0.24),
        'badge_text':   (1.0, 1.0, 1.0),
        'title':        (0.22, 0.40, 0.18),
        'sub':          (0.36, 0.50, 0.28),
        'footer_bg':    (0.30, 0.52, 0.24),
        'footer_text':  (0.92, 0.98, 0.86),
    },
    # Book 3 – cooking: warm terracotta kitchen noon
    'cooking': {
        'sky_top':      (0.96, 0.86, 0.68),
        'sky_mid':      (0.99, 0.94, 0.80),
        'ground_dark':  (0.54, 0.28, 0.14),
        'ground_light': (0.76, 0.46, 0.24),
        'glow':         (1.00, 0.90, 0.60),
        'cloud':        (1.00, 0.96, 0.88),
        'sun':          (0.98, 0.72, 0.26),
        'sun_inner':    (1.00, 0.90, 0.54),
        'card_bg':      (0.99, 0.96, 0.88),
        'card_border':  (0.76, 0.36, 0.16),
        'badge_bg':     (0.76, 0.36, 0.16),
        'badge_text':   (1.0, 1.0, 1.0),
        'title':        (0.56, 0.24, 0.10),
        'sub':          (0.60, 0.38, 0.22),
        'footer_bg':    (0.76, 0.36, 0.16),
        'footer_text':  (1.00, 0.94, 0.84),
    },
    # Book 4 – finance: calm teal sea morning
    'finance': {
        'sky_top':      (0.46, 0.70, 0.82),
        'sky_mid':      (0.80, 0.92, 0.96),
        'ground_dark':  (0.14, 0.36, 0.44),
        'ground_light': (0.26, 0.54, 0.62),
        'glow':         (0.96, 0.88, 0.60),
        'cloud':        (0.96, 0.99, 1.00),
        'sun':          (0.98, 0.88, 0.42),
        'sun_inner':    (0.99, 0.96, 0.72),
        'card_bg':      (0.96, 0.98, 0.96),
        'card_border':  (0.16, 0.44, 0.54),
        'badge_bg':     (0.16, 0.44, 0.54),
        'badge_text':   (1.0, 1.0, 1.0),
        'title':        (0.10, 0.30, 0.40),
        'sub':          (0.26, 0.44, 0.52),
        'footer_bg':    (0.16, 0.44, 0.54),
        'footer_text':  (0.88, 0.96, 0.98),
    },
    # Book 5 – exercise: lavender sunrise, energetic
    'exercise': {
        'sky_top':      (0.56, 0.42, 0.74),
        'sky_mid':      (0.88, 0.80, 0.96),
        'ground_dark':  (0.34, 0.26, 0.50),
        'ground_light': (0.56, 0.46, 0.72),
        'glow':         (0.99, 0.88, 0.66),
        'cloud':        (0.96, 0.94, 0.99),
        'sun':          (0.99, 0.82, 0.40),
        'sun_inner':    (1.00, 0.94, 0.70),
        'card_bg':      (0.98, 0.96, 0.99),
        'card_border':  (0.50, 0.36, 0.72),
        'badge_bg':     (0.50, 0.36, 0.72),
        'badge_text':   (1.0, 1.0, 1.0),
        'title':        (0.34, 0.22, 0.54),
        'sub':          (0.50, 0.40, 0.62),
        'footer_bg':    (0.50, 0.36, 0.72),
        'footer_text':  (0.94, 0.90, 1.00),
    },
}

# ── shared drawing helpers ────────────────────────────────────────────────────

def _cloud(pdf, cx, cy, s=1.0, col=(0.99, 0.98, 0.92)):
    """Draw one puffy cloud at (cx,cy) with scale s."""
    for dx, r in ((-26*s, 18*s), (-8*s, 24*s), (12*s, 20*s), (28*s, 16*s)):
        pdf.circle(cx + dx, cy, r, fill=col)

def _bush(pdf, cx, cy, col=(0.36, 0.58, 0.28), dark=None):
    """Three overlapping circles making a leafy bush."""
    dark = dark or (col[0]*0.82, col[1]*0.82, col[2]*0.82)
    pdf.circle(cx - 16, cy, 14, fill=dark)
    pdf.circle(cx + 16, cy, 14, fill=dark)
    pdf.circle(cx,      cy + 10, 18, fill=col)

def _window(pdf, x, y, w=44, h=36, frame=(0.70, 0.55, 0.38),
            glass=(0.72, 0.88, 0.96)):
    """A simple house window with cross mullion."""
    pdf.rect_rgb(x, y, w, h, glass)
    pdf.rect_rgb(x, y, w, h, frame)           # outer frame (draw twice for effect)
    # cross
    pdf.thick_line(x + w/2, y, x + w/2, y + h, 3, frame)
    pdf.thick_line(x, y + h/2, x + w, y + h/2, 3, frame)

def _pot(pdf, cx, base, col=(0.74, 0.38, 0.22), herb_col=(0.34, 0.62, 0.28)):
    """A terracotta pot with lush foliage."""
    # rim
    pdf.rect_rgb(cx - 20, base + 38, 40, 7, (col[0]*0.88, col[1]*0.82, col[2]*0.78))
    # body (trapezoid)
    pdf.polygon(
        [(cx-18, base+38),(cx+18, base+38),(cx+12, base),(cx-12, base)],
        fill=col
    )
    # three foliage circles
    dark_h = (herb_col[0]*0.80, herb_col[1]*0.80, herb_col[2]*0.80)
    pdf.circle(cx,      base + 58, 15, fill=dark_h)
    pdf.circle(cx - 12, base + 52, 11, fill=herb_col)
    pdf.circle(cx + 12, base + 52, 11, fill=herb_col)
    pdf.circle(cx,      base + 66, 12, fill=herb_col)

# ── scene 1: cyber / anti-scam ───────────────────────────────────────────────

def _scene_cyber(pdf, p):
    """
    An older man seated at a laptop. A large glowing shield floats on the
    right with a warm gold lock on it. Warm lamplight fills the scene.
    """
    skin  = (0.97, 0.78, 0.62)
    hair  = (0.72, 0.68, 0.64)   # silver-white hair
    shirt = (0.28, 0.44, 0.72)
    pants = (0.24, 0.26, 0.42)
    shoe  = (0.18, 0.16, 0.14)

    # ── desk ─────────────────────────────────────────────────────────────
    pdf.rect_rgb(100, 184, 260, 14, (0.60, 0.40, 0.22))  # desk top
    pdf.rect_rgb(112, 152, 16, 32,  (0.50, 0.32, 0.16))  # left leg
    pdf.rect_rgb(332, 152, 16, 32,  (0.50, 0.32, 0.16))  # right leg

    # ── laptop on desk ───────────────────────────────────────────────────
    # screen
    pdf.polygon([(168, 198),(284, 198),(278, 260),(174, 260)],
                fill=(0.18, 0.20, 0.28), stroke=(0.38, 0.40, 0.50), lw=2)
    pdf.polygon([(172, 202),(280, 202),(274, 256),(178, 256)],
                fill=(0.22, 0.58, 0.82))  # screen glow
    # display content: a little padlock icon on screen
    lx, ly = 226, 228
    pdf.rect_rgb(lx-8, ly-6, 16, 14, (0.95, 0.88, 0.40))
    pdf.ellipse(lx, ly+10, 7, 7, fill=None, stroke=(0.95, 0.88, 0.40), lw=3)
    # base of laptop
    pdf.rect_rgb(168, 194, 116, 6, (0.32, 0.34, 0.40))
    pdf.rect_rgb(160, 192, 130, 5, (0.40, 0.42, 0.50))

    # ── seated person ────────────────────────────────────────────────────
    info = pdf.person(196, 152, f=1.0, shirt=shirt, pants=pants, skin=skin,
                      hair=hair, shoe=shoe, pose='sit', gender='m')

    # ── chair ────────────────────────────────────────────────────────────
    pdf.rect_rgb(154, 152, 84, 8,  (0.52, 0.36, 0.20))   # seat
    pdf.rect_rgb(228, 152, 10, 44, (0.52, 0.36, 0.20))   # right leg
    pdf.rect_rgb(154, 152, 10, 44, (0.52, 0.36, 0.20))   # left leg

    # ── shield (right side) ──────────────────────────────────────────────
    sx, sy = 430, 306
    # outer shield glow
    pdf.polygon(
        [(sx-52,sy+62),(sx+52,sy+62),(sx+52,sy-10),(sx,sy-66),(sx-52,sy-10)],
        fill=(0.98, 0.84, 0.44)
    )
    # inner shield
    pdf.polygon(
        [(sx-42,sy+50),(sx+42,sy+50),(sx+42,sy-4),(sx,sy-54),(sx-42,sy-4)],
        fill=(0.22, 0.38, 0.72)
    )
    # checkmark on shield
    pdf.polyline(
        [(sx-22, sy+18),(sx-4, sy-4),(sx+26, sy+32)],
        width=9, color=(0.98, 0.96, 0.88)
    )

    # ── warm desk lamp ───────────────────────────────────────────────────
    pdf.thick_line(330, 198, 330, 240, 5, (0.70, 0.54, 0.30))
    pdf.thick_line(330, 240, 348, 254, 5, (0.70, 0.54, 0.30))
    pdf.circle(350, 258, 10, fill=(0.98, 0.90, 0.50))  # lamp shade
    # lamp glow halo
    pdf.ellipse(350, 252, 22, 12, fill=(0.99, 0.96, 0.78))
    pdf.circle(350, 258, 10, fill=(0.98, 0.90, 0.50))

    # ── small bush on ground ─────────────────────────────────────────────
    _bush(pdf, 66, 190, col=(0.32, 0.52, 0.28))


# ── scene 2: herb garden ─────────────────────────────────────────────────────

def _scene_herbs(pdf, p):
    """
    A cheerful woman watering a row of potted herbs on a sunny terrace.
    """
    skin  = (0.98, 0.80, 0.62)
    hair  = (0.54, 0.36, 0.18)   # warm auburn
    shirt = (0.30, 0.60, 0.40)   # garden green
    pants = (0.46, 0.34, 0.22)   # earthy brown
    shoe  = (0.30, 0.20, 0.14)

    # ── stone terrace wall ────────────────────────────────────────────────
    pdf.rect_rgb(0, 172, 612, 14, (0.76, 0.68, 0.58))
    # stone texture: horizontal lines
    for tx in range(60, 560, 80):
        pdf.thick_line(tx, 172, tx + 66, 172, 2, (0.64, 0.56, 0.46))

    # ── gardener ─────────────────────────────────────────────────────────
    info = pdf.person(168, 186, f=1.08, shirt=shirt, pants=pants, skin=skin,
                      hair=hair, shoe=shoe, pose='wave', gender='f')

    # ── watering can ─────────────────────────────────────────────────────
    hx, hy = info['hand_r']
    # can body
    pdf.ellipse(hx + 12, hy + 6, 18, 12, fill=(0.46, 0.56, 0.66))
    # spout
    pdf.polyline([(hx + 28, hy + 10), (hx + 52, hy - 2),
                  (hx + 64, hy + 4)], width=5, color=(0.38, 0.48, 0.58))
    # handle arc (two lines)
    pdf.thick_line(hx + 14, hy + 16, hx + 8, hy + 24, 4, (0.38, 0.48, 0.58))
    pdf.thick_line(hx + 8, hy + 24, hx + 16, hy + 30, 4, (0.38, 0.48, 0.58))
    # water drops
    for di, wdx in enumerate((-2, 0, 2)):
        pdf.circle(hx + 66 + wdx, hy + 4 - di * 8, 2.5,
                   fill=(0.60, 0.78, 0.92))

    # ── four potted herbs ─────────────────────────────────────────────────
    herbs = [
        (300, 186, (0.74, 0.38, 0.22), (0.34, 0.64, 0.28)),  # basil
        (358, 186, (0.78, 0.42, 0.24), (0.28, 0.54, 0.24)),  # rosemary
        (416, 186, (0.72, 0.36, 0.20), (0.42, 0.68, 0.30)),  # thyme
        (474, 186, (0.76, 0.40, 0.22), (0.36, 0.60, 0.26)),  # mint
    ]
    herb_names = ['Basil', 'Rosemary', 'Thyme', 'Mint']
    for (px, py, pc, hc), name in zip(herbs, herb_names):
        _pot(pdf, px, py, col=pc, herb_col=hc)
        pdf.draw_text_centered(py - 6, name, 7.5,
                               color=(0.34, 0.26, 0.14))

    # ── small garden butterfly ────────────────────────────────────────────
    bx, by = 520, 370
    pdf.ellipse(bx - 12, by + 6,  11, 7, fill=(0.92, 0.60, 0.22))
    pdf.ellipse(bx + 12, by + 6,  11, 7, fill=(0.92, 0.60, 0.22))
    pdf.ellipse(bx - 8,  by - 4,   8, 5, fill=(0.98, 0.80, 0.36))
    pdf.ellipse(bx + 8,  by - 4,   8, 5, fill=(0.98, 0.80, 0.36))
    pdf.thick_line(bx, by - 8, bx, by + 14, 2, (0.28, 0.22, 0.14))

    # ── sunshine rays around the sun ──────────────────────────────────────
    for angle_i in range(8):
        import math
        a = angle_i * math.pi / 4
        rx1, ry1 = 506 + 66*math.cos(a), 664 + 66*math.sin(a)
        rx2, ry2 = 506 + 82*math.cos(a), 664 + 82*math.sin(a)
        pdf.thick_line(rx1, ry1, rx2, ry2, 3, (0.98, 0.86, 0.42))


# ── scene 3: cooking for two ──────────────────────────────────────────────────

def _scene_cooking(pdf, p):
    """
    A cosy kitchen counter. Two friends cooking together with a steaming pot,
    vegetables, and a warm tiled backdrop.
    """
    skin1  = (0.96, 0.76, 0.58)   # person 1
    hair1  = (0.28, 0.20, 0.14)
    shirt1 = (0.80, 0.38, 0.22)   # warm red apron
    pants1 = (0.38, 0.32, 0.52)
    shoe1  = (0.20, 0.16, 0.12)

    skin2  = (0.82, 0.62, 0.46)   # person 2, darker tone
    hair2  = (0.16, 0.12, 0.10)
    shirt2 = (0.38, 0.58, 0.40)
    pants2 = (0.28, 0.30, 0.44)
    shoe2  = (0.18, 0.16, 0.12)

    # ── kitchen tile wall ─────────────────────────────────────────────────
    pdf.rect_rgb(0, 298, 612, 100, (0.96, 0.92, 0.86))
    for tx in range(0, 612, 40):
        for ty in range(298, 398, 32):
            pdf.thick_line(tx, ty, tx + 40, ty, 1, (0.84, 0.80, 0.74))
    for tx in range(0, 612, 40):
        pdf.thick_line(tx, 298, tx, 398, 1, (0.84, 0.80, 0.74))

    # ── kitchen counter ───────────────────────────────────────────────────
    pdf.rect_rgb(0, 196, 612, 18, (0.84, 0.70, 0.52))   # counter top
    pdf.rect_rgb(0, 152, 612, 44, (0.62, 0.46, 0.32))   # counter body

    # ── cutting board with veg ────────────────────────────────────────────
    pdf.rect_rgb(96, 196, 88, 12, (0.82, 0.64, 0.42))   # cutting board
    # three vegetable circles (tomato, courgette, carrot)
    for vx, vc in ((110, (0.88, 0.30, 0.24)), (128, (0.42, 0.68, 0.32)),
                   (146, (0.92, 0.56, 0.22))):
        pdf.circle(vx, 204, 7, fill=vc)

    # ── people ────────────────────────────────────────────────────────────
    pdf.person(174, 214, f=1.02, shirt=shirt1, pants=pants1, skin=skin1,
               hair=hair1, shoe=shoe1, pose='stand', gender='f')
    pdf.person(312, 214, f=1.02, shirt=shirt2, pants=pants2, skin=skin2,
               hair=hair2, shoe=shoe2, pose='wave', gender='m')

    # ── large cooking pot ─────────────────────────────────────────────────
    px, py = 456, 196
    # pot body
    pdf.ellipse(px, py + 42, 46, 14, fill=(0.38, 0.40, 0.48))  # top rim
    pdf.rect_rgb(px - 46, py, 92, 44, (0.32, 0.34, 0.42))
    pdf.ellipse(px, py, 46, 12, fill=(0.26, 0.28, 0.36))        # base curve
    # handles
    pdf.thick_line(px - 58, py + 32, px - 47, py + 32, 8, (0.32, 0.34, 0.42))
    pdf.thick_line(px + 47, py + 32, px + 58, py + 32, 8, (0.32, 0.34, 0.42))
    # lid
    pdf.ellipse(px, py + 46, 46, 14, fill=(0.46, 0.48, 0.56))
    pdf.circle(px, py + 60, 6, fill=(0.58, 0.60, 0.68))         # lid knob
    # steam wisps (wavy S curves approximated by polylines)
    for dx in (-18, 0, 18):
        pdf.polyline(
            [(px+dx, py+66), (px+dx+8, py+82), (px+dx-6, py+98), (px+dx+6, py+114)],
            width=4, color=(0.96, 0.94, 0.90)
        )

    # ── window behind ─────────────────────────────────────────────────────
    _window(pdf, 520, 328, w=58, h=46)
    # view through window: little sun
    pdf.circle(549, 368, 9, fill=(0.99, 0.88, 0.40))

    # ── recipe card on counter ────────────────────────────────────────────
    pdf.rect_rgb(380, 198, 52, 10, (0.98, 0.96, 0.88))
    pdf.thick_line(386, 202, 426, 202, 1, (0.76, 0.72, 0.66))
    pdf.thick_line(386, 205, 426, 205, 1, (0.76, 0.72, 0.66))


# ── scene 4: smart money ──────────────────────────────────────────────────────

def _scene_finance(pdf, p):
    """
    A relaxed older woman at a desk with a laptop, a piggy bank and rising
    coin stacks. Morning light through a window.
    """
    skin  = (0.96, 0.76, 0.58)
    hair  = (0.74, 0.70, 0.66)   # silver
    shirt = (0.28, 0.52, 0.58)
    pants = (0.22, 0.26, 0.44)
    shoe  = (0.18, 0.16, 0.14)

    # ── desk surface ──────────────────────────────────────────────────────
    pdf.rect_rgb(62, 192, 380, 14, (0.62, 0.44, 0.26))
    pdf.rect_rgb(74,  152, 14, 40, (0.50, 0.34, 0.18))
    pdf.rect_rgb(414, 152, 14, 40, (0.50, 0.34, 0.18))

    # ── laptop (open) ─────────────────────────────────────────────────────
    pdf.polygon([(102,206),(214,206),(208,256),(108,256)],
                fill=(0.18, 0.20, 0.28), stroke=(0.38, 0.40, 0.50), lw=2)
    pdf.polygon([(106,210),(210,210),(204,252),(112,252)],
                fill=(0.22, 0.60, 0.78))
    # dollar sign on screen
    pdf.draw_text_centered(232, "$", 18, bold=True, color=(0.98, 0.92, 0.40))
    # base
    pdf.rect_rgb(102, 202, 112, 6, (0.30, 0.32, 0.40))
    pdf.rect_rgb(94,  200, 128, 5, (0.40, 0.42, 0.50))

    # ── seated person ─────────────────────────────────────────────────────
    info = pdf.person(174, 152, f=0.98, shirt=shirt, pants=pants, skin=skin,
                      hair=hair, shoe=shoe, pose='sit', gender='f')

    # ── chair ─────────────────────────────────────────────────────────────
    pdf.rect_rgb(132, 152, 84, 8,  (0.50, 0.34, 0.18))
    pdf.rect_rgb(208, 152, 10, 44, (0.50, 0.34, 0.18))
    pdf.rect_rgb(132, 152, 10, 44, (0.50, 0.34, 0.18))

    # ── piggy bank ────────────────────────────────────────────────────────
    pbx, pby = 370, 228
    # body
    pdf.ellipse(pbx, pby, 34, 26, fill=(0.96, 0.72, 0.74))
    # snout
    pdf.ellipse(pbx + 32, pby - 4, 10, 8, fill=(0.92, 0.64, 0.68))
    pdf.circle(pbx + 30, pby - 5, 2.5, fill=(0.74, 0.46, 0.52))
    pdf.circle(pbx + 35, pby - 5, 2.5, fill=(0.74, 0.46, 0.52))
    # eye
    pdf.circle(pbx + 16, pby + 10, 3, fill=(0.22, 0.16, 0.14))
    pdf.circle(pbx + 17, pby + 11, 1, fill=(1, 1, 1))
    # coin slot on top
    pdf.thick_line(pbx - 6, pby + 24, pbx + 6, pby + 24, 3, (0.74, 0.52, 0.56))
    # legs
    for legx in (pbx - 20, pbx - 6, pbx + 8, pbx + 22):
        pdf.thick_line(legx, pby - 22, legx, pby - 14, 5, (0.92, 0.68, 0.70))
    # ear
    pdf.ellipse(pbx - 24, pby + 18, 8, 10, fill=(0.96, 0.72, 0.74))
    # tail curl
    pdf.polyline([(pbx-32, pby-2),(pbx-38, pby+6),(pbx-34, pby+12)],
                 width=3, color=(0.88, 0.62, 0.66))

    # ── three rising coin stacks ───────────────────────────────────────────
    gold = (0.94, 0.76, 0.28)
    gold_d = (0.78, 0.58, 0.16)
    for i, (scx, n_coins) in enumerate(((448, 2), (486, 4), (524, 6))):
        for ci in range(n_coins):
            cy = 192 + ci * 9
            pdf.ellipse(scx, cy, 14, 5, fill=gold, stroke=gold_d, lw=1)

    # ── window with morning sun ────────────────────────────────────────────
    _window(pdf, 488, 328, w=60, h=48)
    pdf.circle(518, 370, 10, fill=(0.99, 0.88, 0.40))

    # ── small plant on desk ────────────────────────────────────────────────
    _pot(pdf, 434, 192, col=(0.72, 0.38, 0.22),
         herb_col=(0.36, 0.62, 0.28))


# ── scene 5: exercise / staying strong ───────────────────────────────────────

def _scene_exercise(pdf, p):
    """
    Two people: one standing doing arm raises, one seated stretching.
    A warm sunrise park setting with a tree, path, and a heart badge.
    """
    skin1  = (0.97, 0.78, 0.60)
    hair1  = (0.68, 0.64, 0.60)   # silver
    shirt1 = (0.44, 0.34, 0.68)
    pants1 = (0.26, 0.28, 0.44)
    shoe1  = (0.20, 0.18, 0.14)

    skin2  = (0.90, 0.70, 0.54)
    hair2  = (0.18, 0.14, 0.12)
    shirt2 = (0.28, 0.56, 0.52)
    pants2 = (0.30, 0.32, 0.48)
    shoe2  = (0.20, 0.18, 0.14)

    # ── park path ─────────────────────────────────────────────────────────
    pdf.polygon(
        [(200, 152),(380, 152),(460, 192),(120, 192)],
        fill=(0.82, 0.76, 0.64)
    )
    # path edging
    pdf.thick_line(200, 152, 120, 192, 2, (0.68, 0.62, 0.50))
    pdf.thick_line(380, 152, 460, 192, 2, (0.68, 0.62, 0.50))

    # ── tree (left) ───────────────────────────────────────────────────────
    # trunk
    pdf.rect_rgb(76, 152, 22, 100, (0.54, 0.36, 0.20))
    # canopy: three overlapping circles
    pdf.circle(87, 278, 34, fill=(0.28, 0.52, 0.26))
    pdf.circle(68, 266, 28, fill=(0.32, 0.58, 0.28))
    pdf.circle(106,266, 28, fill=(0.32, 0.58, 0.28))
    pdf.circle(87, 294, 24, fill=(0.36, 0.62, 0.30))

    # ── standing person (arms up) ─────────────────────────────────────────
    pdf.person(280, 192, f=1.14, shirt=shirt1, pants=pants1, skin=skin1,
               hair=hair1, shoe=shoe1, pose='arms_up', gender='f')

    # ── seated person (stretch) on a park bench ────────────────────────────
    # bench
    pdf.rect_rgb(394, 192, 110, 10, (0.62, 0.44, 0.26))
    pdf.rect_rgb(398, 152, 10, 40,  (0.52, 0.36, 0.18))
    pdf.rect_rgb(490, 152, 10, 40,  (0.52, 0.36, 0.18))
    pdf.rect_rgb(394, 226, 110, 6,  (0.62, 0.44, 0.26))   # back rest

    info2 = pdf.person(446, 202, f=0.92, shirt=shirt2, pants=pants2, skin=skin2,
                       hair=hair2, shoe=shoe2, pose='sit', gender='m')

    # ── warm heart badge floating up ─────────────────────────────────────
    hx, hy = 280, 378
    # glow
    pdf.circle(hx, hy, 24, fill=(1.00, 0.88, 0.88))
    # heart shape: two circles + triangle
    pdf.circle(hx - 10, hy + 6, 11, fill=(0.88, 0.28, 0.38))
    pdf.circle(hx + 10, hy + 6, 11, fill=(0.88, 0.28, 0.38))
    pdf.polygon(
        [(hx - 20, hy + 8),(hx + 20, hy + 8),(hx, hy - 16)],
        fill=(0.88, 0.28, 0.38)
    )

    # ── small flowers on the ground ────────────────────────────────────────
    for fx, fy in ((158, 194),(180, 196),(530, 194),(552, 196)):
        pdf.circle(fx, fy, 5, fill=(0.98, 0.86, 0.30))
        for da in range(6):
            import math
            a = da * math.pi / 3
            pdf.circle(fx + 7*math.cos(a), fy + 7*math.sin(a), 3.5,
                       fill=(1.00, 0.94, 0.62))


SCENES = {
    'cyber':    _scene_cyber,
    'herbs':    _scene_herbs,
    'cooking':  _scene_cooking,
    'finance':  _scene_finance,
    'exercise': _scene_exercise,
}
