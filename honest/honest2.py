# honest2.py -- the honest-form kept whole (User1, 7 xi 2026: "One keeps the more fulsome of the xor's outputs",
# remembering the reversed wood types, where the ground is cut and the letter is what remains).
# A letter and its mirror cover one field between them. XOR splits that field in two: where they differ (the
# handedness) and where they agree (the core). Both halves are themselves mirror-symmetric. The fuller one is kept:
# a letter that is nearly its own mirror (H, T, I) keeps its core; a handed one (1, j, l) keeps its difference.
#   python3 honest2.py glyphdir font.otf sheet.png line.png
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
gd, fontp, sheet, linep = sys.argv[1:5]
meta = json.load(open(os.path.join(gd, 'glyphs.json')))
def pbm(c):
    b = open(os.path.join(gd, f'{c}.pbm'), 'rb').read(); parts = b.split(b'\n', 2); w, h = map(int, parts[1].split()); bw = (w + 7) // 8
    return np.unpackbits(np.frombuffer(parts[2][:bw * h], dtype=np.uint8).reshape(h, bw), axis=1)[:, :w].astype(bool)
def honest(c):
    bm = pbm(c); mi = bm[:, ::-1]; x = bm ^ mi; a = bm & mi
    return (x, 'x') if x.sum() > a.sum() else (a, 'a')
chars = [ord(c) for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789']
font = ImageFont.truetype(fontp, 22); S = 0.25
top = max(meta[str(c)]['maxn'] for c in chars); bot = min(meta[str(c)]['minn'] for c in chars)
CH = int((top - bot + 1) * S) + 20; CW = 150; cols = 13; rows = (len(chars) + cols - 1) // cols
img = Image.new('RGB', (cols * CW, rows * (CH + 34) + 20), (0, 0, 0)); d = ImageDraw.Draw(img); kept = {}
for k, c in enumerate(chars):
    g = meta[str(c)]; form, how = honest(c); kept[chr(c)] = how
    rgb = np.zeros(form.shape + (3,), np.uint8); rgb[form] = (240, 236, 226) if how == 'x' else (226, 214, 160)
    im = Image.fromarray(rgb).resize((max(1, int(form.shape[1] * S)), max(1, int(form.shape[0] * S))), Image.LANCZOS)
    cx = (k % cols) * CW + CW // 2; img.paste(im, (cx - im.width // 2, 10 + (k // cols) * (CH + 34) + int((top - g['maxn']) * S)))
    d.text((cx, 10 + (k // cols) * (CH + 34) + CH + 4), chr(c) + (' differs' if how == 'x' else ' agrees'), fill=(143, 152, 165), font=font, anchor='mt')
img.save(sheet)
# a line set in honest-forms, each at its letter's own width (the forms keep the letters' boxes, so the setting is Eniee's)
def setline(text, S=0.16):
    PXu = 664.17; sp = 0.303635 * PXu
    W = int(sum((meta[str(ord(ch))]['tfmw'] * PXu if ch != ' ' else sp) for ch in text) * S) + 40
    H = int((top - bot + 1) * S) + 20; im = Image.new('L', (W, H), 0); x = 20
    for ch in text:
        if ch == ' ': x += sp * S; continue
        c = ord(ch); g = meta[str(c)]; form, _ = honest(c)
        p = Image.fromarray((form * 255).astype(np.uint8)).resize((max(1, int(form.shape[1] * S)), max(1, int(form.shape[0] * S))), Image.LANCZOS)
        im.paste(p, (int(x + g['minm'] * S), 10 + int((top - g['maxn']) * S)), p); x += g['tfmw'] * PXu * S
    return im
lines = [setline(t) for t in ('Up with Antidisestablishmentarianism', 'Supercalifragilisticexpialidocious Be it', 'A wandering minstrel I')]
out = Image.new('L', (max(l.width for l in lines), sum(l.height for l in lines)), 0); y = 0
for l in lines: out.paste(l, (0, y)); y += l.height
out.save(linep)
print('kept the core (agrees):', ''.join(k for k, v in kept.items() if v == 'a'))
print('kept the difference:   ', ''.join(k for k, v in kept.items() if v == 'x'))
