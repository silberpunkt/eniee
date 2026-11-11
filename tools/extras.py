# extras.py -- the characters OCR-B never had, made for Eniee Monad by program, so that a YOWL deck (box drawings,
# shade blocks, the blank Braille cell for indenting, the colorburst marks under the periods) never borrows a glyph
# of another width from another font. Called by build.py for the monospaced cut.
#   box drawing U+2500-257F   drawn from the Unicode names themselves: each name says which arms, light, heavy or
#                             double, dashed or arced; one stroke weight for light, one for heavy
#   block elements U+2580-259F  the whole line box, gap included, so blocks and verticals meet line to line
#   Braille U+2800-28FF        eight square dots, Eniee's own square period
#   combining marks           zero width, drawn over or under the cell before them, made from Eniee's own accents
import math, unicodedata
import pathops

K = 0.5523   # a quarter circle as one cubic
SEAM = 5     # arms run this far past the cell's edge, so neighbouring cells overlap and no hairline shows between them

def rect(p, x0, y0, x1, y1):
    x0, x1 = min(x0, x1), max(x0, x1); y0, y1 = min(y0, y1), max(y0, y1)
    pen = p.getPen(); pen.moveTo((x0, y0)); pen.lineTo((x1, y0)); pen.lineTo((x1, y1)); pen.lineTo((x0, y1)); pen.closePath()

def poly(p, pts):
    pen = p.getPen(); pen.moveTo(pts[0])
    for q in pts[1:]: pen.lineTo(q)
    pen.closePath()

def union(p):
    out = pathops.Path(); pathops.union([p], out.getPen()); return out

class Box:
    def __init__(s, W, top, bot, cy, light, heavy):
        s.W, s.top, s.bot, s.cy, s.cx = W, top, bot, cy, W / 2
        s.t = {1: light, 2: heavy}; s.td = round(light * 0.62); s.o = round(light * 0.62 + light * 0.7)

    def arms(s, name):
        """{dir: weight} from a Unicode box-drawing name; weight 1 light, 2 heavy, 3 double."""
        words = name.replace('BOX DRAWINGS ', '').split()
        wmap = {'LIGHT': 1, 'SINGLE': 1, 'HEAVY': 2, 'DOUBLE': 3}
        dmap = {'UP': ['u'], 'DOWN': ['d'], 'LEFT': ['l'], 'RIGHT': ['r'], 'VERTICAL': ['u', 'd'], 'HORIZONTAL': ['l', 'r']}
        groups, cur = [], []
        for w in words:
            if w == 'AND': groups.append(cur); cur = []
            else: cur.append(w)
        groups.append(cur)
        arms, last = {}, 1
        for g in groups:
            wt = next((wmap[w] for w in g if w in wmap), None)
            if wt is None: wt = last
            last = wt
            for w in g:
                for d in dmap.get(w, []): arms[d] = wt
        return arms

    def glyph(s, cp):
        name = unicodedata.name(chr(cp)); p = pathops.Path(); W, top, bot, cy, cx = s.W, s.top, s.bot, s.cy, s.cx
        if 'DASH' in name:
            n = 2 if 'DOUBLE DASH' in name else 3 if 'TRIPLE' in name else 4
            t = s.t[2 if 'HEAVY' in name else 1]
            if 'HORIZONTAL' in name:
                L = W / n
                for k in range(n): rect(p, k * L + L * 0.18, cy - t / 2, (k + 1) * L - L * 0.18, cy + t / 2)
            else:
                L = (top - bot) / n
                for k in range(n): rect(p, cx - t / 2, bot + k * L + L * 0.18, cx + t / 2, bot + (k + 1) * L - L * 0.18)
            return union(p)
        if 'ARC' in name:
            t = s.t[1]; r = W / 2
            # the arc's two arms, as the name says; the turn is a quarter circle of radius half a cell
            a = s.arms(name.replace('ARC ', ''))
            sx = 1 if 'r' in a else -1; sy = 1 if 'u' in a else -1   # toward the arms
            ox, oy = cx + sx * r, cy + sy * r                          # the arc's centre
            pen = p.getPen()
            def arcpts(rad):   # from the horizontal arm's end round to the vertical arm's end
                p0 = (ox, oy - sy * rad); p3 = (ox - sx * rad, oy)
                return p0, (ox - sx * rad * K, oy - sy * rad), (ox - sx * rad, oy - sy * rad * K), p3
            R1, R0 = r + t / 2, r - t / 2
            a0, a1, a2, a3 = arcpts(R1); b0, b1, b2, b3 = arcpts(R0)
            pen.moveTo(a0); pen.curveTo(a1, a2, a3); pen.lineTo(b3); pen.curveTo(b2, b1, b0); pen.closePath()
            ex = (W if sx > 0 else 0) + sx * SEAM; ey = (top if sy > 0 else bot) + sy * SEAM
            rect(p, ox, cy - t / 2, ex, cy + t / 2); rect(p, cx - t / 2, oy, cx + t / 2, ey)
            return union(p)
        if 'DIAGONAL' in name:
            t = s.t[1]
            def diag(x0, y0, x1, y1):
                dx, dy = x1 - x0, y1 - y0; L = math.hypot(dx, dy); nx, ny = -dy / L * t / 2, dx / L * t / 2
                poly(p, [(x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)])
            if 'UPPER RIGHT TO LOWER LEFT' in name or 'CROSS' in name: diag(0, bot, W, top)
            if 'UPPER LEFT TO LOWER RIGHT' in name or 'CROSS' in name: diag(0, top, W, bot)
            return union(p)
        a = s.arms(name); o, td = s.o, s.td
        perp = {'u': ('l', 'r'), 'd': ('l', 'r'), 'l': ('d', 'u'), 'r': ('d', 'u')}
        opp = {'u': 'd', 'd': 'u', 'l': 'r', 'r': 'l'}
        for d, wt in a.items():
            vert = d in 'ud'; sgn = 1 if d in 'ur' else -1; c0 = cy if vert else cx; E = ((top if d == 'u' else bot) if vert else (W if d == 'r' else 0)) + sgn * SEAM
            pa = [a.get(q) for q in perp[d]]
            if wt in (1, 2):
                t = s.t[wt]
                if 3 in pa:   # a single line meeting a double pair: to the near line if the pair runs through, else to the far one
                    through = all(q == 3 for q in pa)
                    reach = c0 + sgn * (o - td / 2) if through else c0 - sgn * (o + td / 2)
                else:
                    reach = c0 - sgn * max([s.t[q] / 2 for q in pa if q in (1, 2)] + [0])
                if vert: rect(p, cx - t / 2, reach, cx + t / 2, E)
                else: rect(p, reach, cy - t / 2, E, cy + t / 2)
            else:   # a double arm: two lines, each told where to stop by its neighbours
                for side, q in zip((-1, 1), pa):
                    other = pa[1] if side == -1 else pa[0]
                    if q == 3: st = c0 + sgn * o                       # an inner corner
                    elif q in (1, 2): st = c0 - sgn * s.t[q] / 2         # meets a single line on that side
                    elif a.get(opp[d]) == 3: st = c0                    # runs straight on
                    elif other == 3: st = c0 - sgn * o                  # an outer corner
                    elif other in (1, 2): st = c0 - sgn * s.t[other] / 2
                    else: st = c0
                    off = side * o
                    if vert: rect(p, cx + off - td / 2, st, cx + off + td / 2, E)
                    else: rect(p, st, cy + off - td / 2, E, cy + off + td / 2)
        return union(p)

def blocks(cp, W, top, bot):
    name = unicodedata.name(chr(cp)); p = pathops.Path(); H = top - bot
    fr = {'ONE': 1, 'TWO': 2, 'THREE': 3, 'FOUR': 4, 'FIVE': 5, 'SIX': 6, 'SEVEN': 7}
    if name == 'FULL BLOCK': rect(p, 0, bot, W, top)
    elif name.endswith('HALF BLOCK'):
        if 'UPPER' in name: rect(p, 0, bot + H / 2, W, top)
        elif 'LOWER' in name: rect(p, 0, bot, W, bot + H / 2)
        elif 'LEFT' in name: rect(p, 0, bot, W / 2, top)
        else: rect(p, W / 2, bot, W, top)
    elif 'EIGHTH' in name:
        n = fr[name.split()[1]]
        if name.startswith('LOWER'): rect(p, 0, bot, W, bot + H * n / 8)
        elif name.startswith('UPPER'): rect(p, 0, top - H * n / 8, W, top)
        elif name.startswith('LEFT'): rect(p, 0, bot, W * n / 8, top)
        else: rect(p, W - W * n / 8, bot, W, top)
    elif name.endswith('SHADE'):   # a dither of small squares: a quarter, a half, three quarters
        cols, rows = 4, 8; cw, ch = W / cols, H / rows
        on = {'LIGHT': lambda i, j: i % 2 == 0 and j % 2 == 0, 'MEDIUM': lambda i, j: (i + j) % 2 == 0, 'DARK': lambda i, j: not (i % 2 == 1 and j % 2 == 1)}[name.split()[0]]
        for i in range(cols):
            for j in range(rows):
                if on(i, j): rect(p, i * cw, bot + j * ch, (i + 1) * cw, bot + (j + 1) * ch)
    elif name.startswith('QUADRANT'):
        q = {'UPPER LEFT': (0, 1), 'UPPER RIGHT': (1, 1), 'LOWER LEFT': (0, 0), 'LOWER RIGHT': (1, 0)}
        for k, (i, j) in q.items():
            if k in name.replace('QUADRANT ', ''): rect(p, i * W / 2, bot + j * H / 2, (i + 1) * W / 2, bot + (j + 1) * H / 2)
    return union(p)

def braille(cp, W, asc, desc, dot):
    bits = cp - 0x2800; p = pathops.Path()
    pos = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (0, 3), (1, 3)]   # dots 1-8: column, row from the top
    ys = [asc - 120 - k * (asc - desc - 240) / 3 for k in range(4)]; xs = [W * 0.32, W * 0.68]
    for b in range(8):
        if bits >> b & 1:
            c, r = pos[b]; rect(p, xs[c] - dot / 2, ys[r] - dot / 2, xs[c] + dot / 2, ys[r] + dot / 2)
    return union(p) if bits else p

def contours_path(cs, fx):
    """Eniee's own traced contours, moved by fx((x, y)) -> (x, y), as one path."""
    p = pathops.Path(); pen = p.getPen()
    for seg in cs:
        for s in seg:
            if s[0] == 'M': pen.moveTo(fx(s[1]))
            elif s[0] == 'L': pen.lineTo(fx(s[1]))
            else: pen.curveTo(fx(s[1]), fx(s[2]), fx(s[3]))
        pen.closePath()
    return p

def marks(O, W, xh, desc):
    """Combining marks, zero width, centred on the cell before them (x from -W to 0)."""
    def bb(cs):
        xs = [pt[0] for seg in cs for s in seg for pt in s[1:]]; ys = [pt[1] for seg in cs for s in seg for pt in s[1:]]
        return min(xs), min(ys), max(xs), max(ys)
    # The hats and shoes keep the nib's own weight: each of Eniee's accents is used near its own size (OCR-B drew
    # them as letters' companions, not miniatures), so their strokes are no thinner than about six tenths of the
    # nib, between the humble period and the full knifeblade accent. (User1, 8 xi: "our bit does not bite that small")
    def fit(code, below, sc, mirror=False):
        cs = O[str(code)]['contours']; x0, y0, x1, y1 = bb(cs)
        if mirror: cs = [[[s[0]] + [(-pt[0], pt[1]) for pt in s[1:]] for s in seg] for seg in cs]; x0, x1 = -x1, -x0
        tx = -W / 2 - (x0 + x1) / 2 * sc
        ty = ((20 if code == 24 else -45) - y1 * sc) if below else (xh + 45 - y0 * sc)   # the cedilla touches its letter
        return union(contours_path(cs, lambda q: (q[0] * sc + tx, q[1] * sc + ty)))
    def drawn(fn):
        p = pathops.Path(); fn(p); return union(p)
    t = 70; c = -W / 2; y = -130   # strokes for the few marks Eniee has no letter for
    tack_up = lambda p: (rect(p, c - 90, y - 70, c + 90, y - 70 + t), rect(p, c - t / 2, y - 70, c + t / 2, y + 70))
    tack_dn = lambda p: (rect(p, c - 90, y + 70 - t, c + 90, y + 70), rect(p, c - t / 2, y - 70, c + t / 2, y + 70))
    def halfring(p):
        R1, R0 = 85, 85 - t; pen = p.getPen()
        pen.moveTo((c, y + R1)); pen.curveTo((c - R1 * K, y + R1), (c - R1, y + R1 * K), (c - R1, y)); pen.curveTo((c - R1, y - R1 * K), (c - R1 * K, y - R1), (c, y - R1))
        pen.lineTo((c, y - R0)); pen.curveTo((c - R0 * K, y - R0), (c - R0, y - R0 * K), (c - R0, y)); pen.curveTo((c - R0, y + R0 * K), (c - R0 * K, y + R0), (c, y + R0)); pen.closePath()
    vbar = lambda p: rect(p, c - t / 2, y - 80, c + t / 2, y + 80)
    above = {0x300: 18, 0x301: 19, 0x302: 94, 0x303: 126, 0x304: 22, 0x306: 21, 0x307: 46, 0x308: 127, 0x30A: 23, 0x30C: 20}
    below = {0x316: 18, 0x317: 19, 0x323: 46, 0x324: 127, 0x325: 23, 0x326: 44, 0x327: 24, 0x32C: 20, 0x32D: 94, 0x32E: 21,
             0x330: 126, 0x331: 22, 0x332: 95, 0x31F: 43, 0x320: 45}
    out = {}
    SA = {18: .85, 19: .85, 20: .6, 21: .6, 22: .65, 23: .9, 127: .9, 94: .6, 126: .6, 46: .9}
    SB = {18: .75, 19: .75, 46: .9, 127: .9, 23: .8, 44: .6, 24: .65, 20: .5, 94: .5, 21: .5, 126: .5, 22: .6, 95: .6, 43: .5, 45: .5}
    for cp, code in above.items(): out[cp] = fit(code, False, SA[code])
    for cp, code in below.items(): out[cp] = fit(code, True, SB[code])
    # OCR-B's own grave is so short that at text sizes it reads as a dot (a grave a would pass for a dotted one); the
    # grave is the acute turned left for right instead, as the quotes are a turned pair
    out[0x300] = fit(19, False, SA[19], mirror=True); out[0x316] = fit(19, True, SB[19], mirror=True)
    out[0x31C] = drawn(halfring); out[0x31D] = drawn(tack_up); out[0x31E] = drawn(tack_dn); out[0x329] = drawn(vbar)
    return out

def composed(base_by_cp, mk, W, xh, have):
    """Accented Latin letters built from Eniee's own letters and its own marks: the letter, and the mark over its cell's
    centre, raised over a capital or an ascender. i and j take their dotless forms first."""
    out = []
    dotless = {0x69: 0x131, 0x6A: 0x237}
    for cp in list(range(0xC0, 0x250)) + list(range(0x1E00, 0x1F00)):
        if cp in have: continue
        dec = unicodedata.decomposition(chr(cp)).split()
        if len(dec) != 2 or dec[0].startswith('<'): continue
        b, m = int(dec[0], 16), int(dec[1], 16); b = dotless.get(b, b) if m < 0x316 else b
        if b not in base_by_cp or m not in mk: continue
        cs = base_by_cp[b]; ys = [pt[1] for seg in cs for s in seg for pt in s[1:]]
        p = union(contours_path(cs, lambda q: (q[0], q[1])))   # the letter, made whole on its own first
        tall = m < 0x316 and max(ys) > xh + 40
        if tall:   # over a capital or an ascender: the hat a little smaller (0.85) and a little closer
            k, yb = 0.85, xh + 45; lift = max(ys) - xh - 10
            mp = pathops.Path(); mk[m].draw(_Scale(mp.getPen(), k, k, k * W / 2 + W / 2, yb * (1 - k) + lift))
        else:
            mp = pathops.Path(); mk[m].draw(_Shift(mp.getPen(), W, 0))
        # letter and mark joined as two shapes, so where they overlap (a cedilla on its c) the ink adds, not cancels
        both = pathops.Path(); pathops.union([p, union(mp)], both.getPen())
        out.append(('uni%04X' % cp, cp, W, both))
    return out

class _Shift:
    """A pen that moves what is drawn through it by (dx, dy)."""
    def __init__(s, pen, dx, dy): s.p, s.dx, s.dy = pen, dx, dy
    def _m(s, q): return (q[0] + s.dx, q[1] + s.dy)
    def moveTo(s, q): s.p.moveTo(s._m(q))
    def lineTo(s, q): s.p.lineTo(s._m(q))
    def curveTo(s, *qs): s.p.curveTo(*[s._m(q) for q in qs])
    def qCurveTo(s, *qs): s.p.qCurveTo(*[s._m(q) if q is not None else None for q in qs])
    def closePath(s): s.p.closePath()
    def endPath(s): s.p.endPath()

class _Scale(_Shift):
    """A pen that scales (sx, sy) and then moves (dx, dy)."""
    def __init__(s, pen, sx, sy, dx, dy): s.p, s.sx, s.sy, s.dx, s.dy = pen, sx, sy, dx, dy
    def _m(s, q): return (q[0] * s.sx + s.dx, q[1] * s.sy + s.dy)

def dejavu(path, have, W):
    """The safety net: every character DejaVu Sans Mono has and Eniee Monad does not, scaled to Monad's cell (its em to
    Monad's em, its cell to Monad's cell). Combining marks are set to zero width over the cell before them.
    Bitstream Vera licence; DejaVu's own changes are in the public domain (see LICENSE-DejaVu.txt)."""
    from fontTools.ttLib import TTFont
    from fontTools.pens.boundsPen import BoundsPen
    f = TTFont(path); gs = f.getGlyphSet(); upm = f['head'].unitsPerEm; cm = f.getBestCmap()
    sy = 1000 / upm; sx = W / f['hmtx'][cm[0x41]][0]
    out = []
    for cp, gn in sorted(cm.items()):
        if cp in have or cp < 0x20 or 0xD800 <= cp < 0xF900 or unicodedata.category(chr(cp)) in ('Cc', 'Cf', 'Zl', 'Zp'): continue
        p = pathops.Path()
        from fontTools.pens.recordingPen import DecomposingRecordingPen
        rec = DecomposingRecordingPen(gs); gs[gn].draw(rec)   # composites are drawn out whole
        try:
            if unicodedata.category(chr(cp)) in ('Mn', 'Me'):
                bp = BoundsPen(gs); gs[gn].draw(bp)
                if not bp.bounds: continue
                cx = (bp.bounds[0] + bp.bounds[2]) / 2 * sx
                rec.replay(_Scale(p.getPen(), sx, sy, -W / 2 - cx, 0)); adv = 0
            else:
                rec.replay(_Scale(p.getPen(), sx, sy, 0, 0)); adv = W
            out.append(('dv%04X' % cp if cp <= 0xFFFF else 'dv%06X' % cp, cp, adv, union(p)))
        except Exception:
            continue
    return out

def circle(pen, cx, cy, r, ccw=True):
    k = r * K; pts = [(cx + r, cy), (cx, cy + r), (cx - r, cy), (cx, cy - r)]
    if not ccw: pts = pts[::-1]
    pen.moveTo(pts[0])
    for i in range(4):
        a, b = pts[i], pts[(i + 1) % 4]
        # control points along each end's tangent
        ta = (-(a[1] - cy), a[0] - cx) if ccw else ((a[1] - cy), -(a[0] - cx)); tb = (-(b[1] - cy), b[0] - cx) if ccw else ((b[1] - cy), -(b[0] - cx))
        pen.curveTo((a[0] + ta[0] / r * k, a[1] + ta[1] / r * k), (b[0] - tb[0] / r * k, b[1] - tb[1] / r * k), b)
    pen.closePath()

def symbols(W, xh, stem):
    """The two Dellschau needed that DejaVu Sans Mono does not have: the neuter sign (CAAD's descending man) and a
    medium black circle."""
    t = round(stem * 0.85); out = []
    p = pathops.Path(); pen = p.getPen(); r = W * 0.33; cy = xh + 70
    circle(pen, W / 2, cy, r); circle(pen, W / 2, cy, r - t, ccw=False)
    rect(p, W / 2 - t / 2, -150, W / 2 + t / 2, cy - r + t / 2)
    out.append(('uni26B2', 0x26B2, W, union(p)))
    p = pathops.Path(); circle(p.getPen(), W / 2, xh / 2 + 30, W * 0.38); out.append(('uni26AB', 0x26AB, W, union(p)))
    return out

def make(O, W, asc, desc, gap, top, bot, stem, base_by_cp=None, have=(), dejavu_path=None):
    """[(glyphname, codepoint, advance, pathops.Path)] for the monospaced cut."""
    cy = round((asc + desc) / 2); box = Box(W, top, bot, cy, light=round(stem * 0.85), heavy=round(stem * 1.6))
    out = []
    for cp in range(0x2500, 0x2580): out.append(('uni%04X' % cp, cp, W, box.glyph(cp)))
    for cp in range(0x2580, 0x25A0): out.append(('uni%04X' % cp, cp, W, blocks(cp, W, top, bot)))
    for cp in range(0x2800, 0x2900): out.append(('uni%04X' % cp, cp, W, braille(cp, W, asc, desc, dot=round(stem * 1.15))))
    xh = round(max(pt[1] for seg in O['120']['contours'] for s in seg for pt in s[1:]))
    mk = marks(O, W, xh, desc)
    for cp, path in mk.items(): out.append(('uni%04X' % cp, cp, 0, path))
    out.append(('uni00A0', 0xA0, W, pathops.Path()))
    out += symbols(W, xh, stem)
    have = set(have) | {o[1] for o in out}
    if base_by_cp:
        comp = composed(base_by_cp, mk, W, xh, have); out += comp; have |= {o[1] for o in comp}
    if dejavu_path: out += dejavu(dejavu_path, have, W)
    return out
