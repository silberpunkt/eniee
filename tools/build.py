# build.py -- an OpenType (CFF) font, and its WOFF and WOFF2, from trace.py's outlines. fontTools.
#   python3 build.py glyphdir outdir "Family" "Style" weightclass mono(0/1) space version
# The character slots are METAFONT's (OCR-B's own layout, which follows TeX's old text layout); the map below
# gives each the Unicode it answers to. (TeX's dash ligatures stay in TeX; the OpenType fonts have none:)
#   - -    the message, "do not hide / in typography." (slot 2; also U+2013, where an en dash would be)
#   - - -  the hyphen made twice (slot 3; also U+2014)
import sys, os, json
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.agl import UV2AGL
from fontTools.ttLib import TTFont

gd, od, fam, sty, wt, mono, space, ver = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]), sys.argv[6] == '1', float(sys.argv[7]), sys.argv[8]
gap = int(sys.argv[9]) if len(sys.argv) > 9 else 0   # line gap in units (monad: 150, about two pixels at 13 px, so code can breathe)
O = json.load(open(os.path.join(gd, 'outlines.json')))

U = {c: [c] for c in range(32, 127)}
U[39] = [0x27, 0x2019]; U[96] = [0x60, 0x2018]; U[34] = [0x22, 0x201C]; U[45] = [0x2D, 0x2010]
U.update({0: [0x393], 1: [0x394], 2: [0x2013], 3: [0x2014], 4: [0x39E], 5: [0x3A0], 6: [0x3A3], 7: [0x3A5], 8: [0x3A6],
          9: [0x3A8], 10: [0x3A9], 11: [0x2191], 12: [0x2193], 13: [0x2032], 14: [0xA1], 15: [0xBF], 16: [0x131],
          17: [0x237], 18: [0x2CB], 19: [0xB4], 20: [0x2C7], 21: [0x2D8], 22: [0xAF], 23: [0x2DA], 24: [0xB8],
          25: [0xDF], 26: [0xE6], 27: [0x153], 28: [0xF8], 29: [0xC6], 30: [0x152], 31: [0xD8],
          127: [0xA8], 128: [0xE4], 129: [0xF6], 130: [0xFC], 131: [0xC4], 132: [0xD6], 133: [0xDC],
          134: [0xA7], 135: [0xA4], 136: [0xA6], 137: [0x201D], 138: [0xB7]})   # 138: the middle dot
special = {2: 'endash', 3: 'emdash', 13: 'minute', 32: 'space'}

def name(c):
    if c in special: return special[c]
    u = U[c][0]
    return UV2AGL.get(u, 'uni%04X' % u)

codes = sorted(int(k) for k in O)
order = ['.notdef'] + [name(c) for c in codes]
cmap, widths, charstrings = {}, {'.notdef': 500}, {}
for c in codes:
    g = O[str(c)]; n = name(c)
    w = round(space * 1000) if c == 32 else round(g['tfmw'] * 1000)
    widths[n] = w
    for u in U[c]: cmap[u] = n
    cs = g['contours']
    # potrace alternates direction outer/hole; CFF wants the outer ones counter-clockwise
    def area(seg):
        pts = [s[-1] for s in seg]; return sum(pts[i - 1][0] * pts[i][1] - pts[i][0] * pts[i - 1][1] for i in range(len(pts))) / 2
    rev = bool(cs) and area(max(cs, key=lambda s: abs(area(s)))) < 0
    pen = T2CharStringPen(w, None); dp = ReverseContourPen(pen) if rev else pen
    for seg in cs:
        for s in seg:
            if s[0] == 'M': dp.moveTo(tuple(s[1]))
            elif s[0] == 'L': dp.lineTo(tuple(s[1]))
            else: dp.curveTo(tuple(s[1]), tuple(s[2]), tuple(s[3]))
        dp.closePath()
    charstrings[n] = pen.getCharString()
nd = T2CharStringPen(500, None); nd.moveTo((50, 0)); nd.lineTo((450, 0)); nd.lineTo((450, 700)); nd.lineTo((50, 700)); nd.closePath()
nd.moveTo((100, 50)); nd.lineTo((100, 650)); nd.lineTo((400, 650)); nd.lineTo((400, 50)); nd.closePath(); charstrings['.notdef'] = nd.getCharString()

def bounds(c):
    bp = BoundsPen(None); g = O[str(c)]
    for seg in g['contours']:
        for s in seg:
            if s[0] == 'M': bp.moveTo(tuple(s[1]))
            elif s[0] == 'L': bp.lineTo(tuple(s[1]))
            else: bp.curveTo(tuple(s[1]), tuple(s[2]), tuple(s[3]))
        bp.closePath()
    return bp.bounds
asc = round(max(bounds(c)[3] for c in (98, 100, 108))); desc = round(min(bounds(c)[1] for c in (103, 112, 113)))
xh = round(bounds(120)[3]); cap = round(bounds(72)[3])
allb = [bounds(c) for c in codes if O[str(c)]['contours']]
ymax = round(max(b[3] for b in allb)); ymin = round(min(b[1] for b in allb))
# alignment zones for the hinter: the baseline, the x-height, the capitals, the ascenders, each from flat letters to round
# ones (the overshoot); and the descenders below. The hinter will not start without them.
def zone(flat, round_, top):
    a, b = (round(min(bounds(c)[1] for c in round_)), round(min(bounds(c)[1] for c in flat))) if not top else (round(max(bounds(c)[3] for c in flat)), round(max(bounds(c)[3] for c in round_)))
    a, b = min(a, b), max(a, b); return [a, b if b > a else a + 1]
blues = sorted(zone((120, 122, 118), (111, 99, 115), False) + zone((120, 122, 118), (111, 99, 115), True) + zone((72, 69, 84), (79, 67, 83), True) + zone((100, 108, 98), (100, 108, 98), True))
blues = [v for z in sorted([blues[i:i + 2] for i in range(0, len(blues), 2)]) for v in z]
others = zone((112, 113), (103, 106), False)
# the stems, measured on METAFONT's own bitmaps: an upright (the I's, across its middle row) and a bar (the hyphen's,
# down its middle column). A flat nib at 40 degrees makes them nearly equal, as the README says.
def stem(code, across):
    import numpy as np
    b = open(os.path.join(gd, f'{code}.pbm'), 'rb').read(); pp = b.split(b'\n', 2); w, h = map(int, pp[1].split()); bw = (w + 7) // 8
    a = np.unpackbits(np.frombuffer(pp[2][:bw * h], dtype=np.uint8).reshape(h, bw), axis=1)[:, :w].astype(bool)
    line = a[h // 2, :] if across else a[:, w // 2]
    runs, n = [], 0
    for v in line:
        if v: n += 1
        elif n: runs.append(n); n = 0
    if n: runs.append(n)
    meta = json.load(open(os.path.join(gd, 'glyphs.json'))); PX = 4800 / 72.27 * meta['design']
    return round(max(runs) * 1000 / PX)
vw, hw = stem(73, True), stem(45, False)
# the monospaced cut also gets the characters OCR-B never had (box drawing, blocks, Braille, combining marks), made by
# extras.py to its exact cell, so a YOWL deck in an editor never borrows a glyph of another width
if mono:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import extras
    # the line box the editor actually gives: ascender and descender, the gap split above and below. Boxes and blocks
    # fill exactly this, so they tile line to line; Windows' own metrics (GDI) are set to the same box below.
    top, bot = asc + gap // 2, desc - (gap - gap // 2)
    base_by_cp = {u: O[str(c)]['contours'] for c in codes for u in U[c]}
    dv = os.environ.get('DEJAVU', '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf')
    for gn, cp, adv, path in extras.make(O, round(space * 1000), asc, desc, gap, top, bot, vw, base_by_cp, set(cmap), dv if os.path.exists(dv) else None):
        pen = T2CharStringPen(adv, None); path.draw(pen); charstrings[gn] = pen.getCharString(); widths[gn] = adv; order.append(gn); cmap[cp] = gn

ps = fam.replace(' ', '') + '-Regular'
fb = FontBuilder(1000, isTTF=False)
fb.setupGlyphOrder(order)
fb.setupCharacterMap(cmap)
fb.setupCFF(ps, {'FullName': fam + ' ' + sty, 'FamilyName': fam, 'Weight': sty, 'version': ver}, charstrings, {'BlueValues': blues, 'OtherBlues': others, 'BlueScale': 0.039625, 'BlueShift': 7, 'BlueFuzz': 1, 'StdVW': vw, 'StdHW': hw})
fb.setupHorizontalMetrics({n: (widths[n], 0) for n in order})
fb.setupHorizontalHeader(ascent=asc, descent=desc, lineGap=gap)
fb.setupNameTable({
    'familyName': fam, 'styleName': 'Regular',
    'typographicFamily': 'Eniee', 'typographicSubfamily': sty,
    'uniqueFontIdentifier': ps + ';' + ver, 'fullName': fam, 'psName': ps,
    'version': 'Version ' + ver,
    'copyright': 'Copyright 1995, 2010 Norbert Schwarz (OCR-B in METAFONT, after Adrian Frutiger). Eniee: flat-nib dry-cut, 2026, User1 (silberpunkt) and eniamb.' + (' Fallback glyphs from DejaVu Sans Mono: Copyright (c) 2003 by Bitstream, Inc.; DejaVu changes are in the public domain; Bitstream Vera licence, see LICENSE-DejaVu.txt.' if mono else ''),
    'designer': 'User1 (silberpunkt), with eniamb; after Norbert Schwarz and Adrian Frutiger',
    'description': 'OCR-B drawn again with a flat nib at 40 degrees. Cut in METAFONT, traced at 4800 dpi.',
    'licenseDescription': 'Norbert Schwarz: "You may freely use, modify, and/or distribute this file, without limitation." The same holds for Eniee.',
})
fb.setupOS2(sTypoAscender=asc, sTypoDescender=desc, sTypoLineGap=gap, usWinAscent=(asc + gap // 2) if mono else max(ymax, asc), usWinDescent=(gap - gap // 2 - desc) if mono else max(-ymin, -desc),
            sxHeight=xh, sCapHeight=cap, usWeightClass=wt, fsSelection=0x40 | 0x80, achVendID='NONE', version=4)
from fontTools.ttLib.tables.O_S_2f_2 import Panose
pan = Panose(); pan.bFamilyType = 2; pan.bProportion = 9 if mono else 0
for k in ('bSerifStyle','bWeight','bContrast','bStrokeVariation','bArmStyle','bLetterForm','bMidline','bXHeight'): setattr(pan, k, 0)
fb.font['OS/2'].panose = pan
fb.setupPost(isFixedPitch=1 if mono else 0, underlinePosition=-100, underlineThickness=50)
# No ligatures (Poetas, 11 xi 2026): two hyphens stay two hyphens, as typed. TeX's -- and --- live on in the METAFONT
# source for TeX; in the OpenType fonts the message and the doubled hyphen answer only to U+2013 and U+2014.
os.makedirs(od, exist_ok=True)
base = os.path.join(od, ps)
fb.font.save(base + '.otf')
# hinting (Adobe's autohinter, psautohint) and subroutines (cffsubr): the same outlines, lighter to draw and to carry
import subprocess, cffsubr
subprocess.run([sys.executable, '-m', 'psautohint', base + '.otf'], check=True, capture_output=True)
f = TTFont(base + '.otf'); cffsubr.subroutinize(f); f.save(base + '.otf')
for flavor in ('woff', 'woff2'):
    f = TTFont(base + '.otf'); f.flavor = flavor; f.save(base + '.' + flavor)
print(ps, len(order), 'glyphs; ascender', asc, 'descender', desc, 'x', xh, 'cap', cap, 'bounds', ymin, ymax)
