# honest.py -- each letter XORed with itself turned left for right (User1, 7 xi 2026: "There is an honest-form").
# What is left is what the letter does that a mirror would undo: its handedness. A letter that is its own mirror
# leaves nothing but the nib's own lean (the flat nib at 40 degrees is never its own mirror). The result is always
# itself mirror-symmetric, as audio is, left and right equal.
#   python3 honest.py glyphdir out.png
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
gd, outp = sys.argv[1], sys.argv[2]
meta = json.load(open(os.path.join(gd, 'glyphs.json')))
def pbm(c):
    b = open(os.path.join(gd, f'{c}.pbm'), 'rb').read(); parts = b.split(b'\n', 2); w, h = map(int, parts[1].split()); bw = (w + 7) // 8
    return np.unpackbits(np.frombuffer(parts[2][:bw * h], dtype=np.uint8).reshape(h, bw), axis=1)[:, :w].astype(bool)
chars = [ord(c) for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789']
S = 0.25; top = max(meta[str(c)]['maxn'] for c in chars); bot = min(meta[str(c)]['minn'] for c in chars)
CH = int((top - bot + 1) * S) + 20; CW = 150; cols = 13
rows = (len(chars) + cols - 1) // cols
img = Image.new('RGB', (cols * CW * 2 // 2, rows * (CH + 34) + 20), (0, 0, 0)); d = ImageDraw.Draw(img)
font = ImageFont.truetype(sys.argv[3], 22) if len(sys.argv) > 3 else None
res = []
for k, c in enumerate(chars):
    g = meta[str(c)]; bm = pbm(c); x = bm ^ bm[:, ::-1]
    ink = bm.sum(); hand = x.sum() / (2 * ink)   # 0: its own mirror; 1: nothing in common with its mirror
    res.append((chr(c), hand))
    rgb = np.zeros(bm.shape + (3,), np.uint8); rgb[bm & ~x] = (70, 70, 64); rgb[x] = (240, 236, 226)
    im = Image.fromarray(rgb).resize((max(1, int(bm.shape[1] * S)), max(1, int(bm.shape[0] * S))), Image.LANCZOS)
    cx = (k % cols) * CW + CW // 2; y0 = 10 + (k // cols) * (CH + 34) + int((top - g['maxn']) * S)
    img.paste(im, (cx - im.width // 2, y0))
    d.text((cx, 10 + (k // cols) * (CH + 34) + CH + 4), f'{chr(c)} {hand:.2f}', fill=(143, 152, 165), font=font, anchor='mt')
img.save(outp)
res.sort(key=lambda r: r[1])
print('most its own mirror:', ' '.join(f'{a}{h:.2f}' for a, h in res[:10]))
print('most handed:        ', ' '.join(f'{a}{h:.2f}' for a, h in res[-10:]))
