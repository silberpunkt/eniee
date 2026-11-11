# trace.py -- turn the METAFONT bitmaps (from gf2glyphs.js) into outlines, with potrace (the potracer package).
#   python3 trace.py glyphdir [seconds]      -> glyphdir/outlines.json, resumable: run again until it says DONE
# Each outline is in font units (1000 to the em), its origin the character's reference point. The bitmaps are cut at
# 4800 dpi (METAFONT, mode ljfour, mag 8): a 10 pt em is 664.17 pixels, so one pixel is 1.506 units.
import sys, os, json, time
import numpy as np
import potrace

gd = sys.argv[1]; budget = float(sys.argv[2]) if len(sys.argv) > 2 else 35
meta = json.load(open(os.path.join(gd, 'glyphs.json')))
PX = 4800 / 72.27 * meta['design']; S = 1000 / PX
outF = os.path.join(gd, 'outlines.json')
done = json.load(open(outF)) if os.path.exists(outF) else {}
t0 = time.time()

def pbm(path):
    b = open(path, 'rb').read(); parts = b.split(b'\n', 2); w, h = map(int, parts[1].split()); bw = (w + 7) // 8
    a = np.unpackbits(np.frombuffer(parts[2][:bw * h], dtype=np.uint8).reshape(h, bw), axis=1)[:, :w]
    return a.astype(bool)

for k, g in meta.items():
    if k == 'design' or k in done: continue
    if 'minm' not in g: done[k] = {'tfmw': g['tfmw'], 'contours': []}; continue
    if time.time() - t0 > budget: break
    bm = pbm(os.path.join(gd, k + '.pbm'))
    # potracer takes an image (True = light) and inverts it; the bitmap here is True = ink, so it goes in inverted
    # opttolerance 1.0 (was 0.2): about 40 percent fewer curves, the outline moving by about a pixel at 4800 dpi, which
    # is a fiftieth of a pixel in a 13-pixel editor. Corners are kept as they were (alphamax 1.0).
    path = potrace.Bitmap(~bm).trace(turdsize=4, alphamax=1.0, opticurve=True, opttolerance=float(os.environ.get('TOL', 1.0)))
    X = lambda p: (round((g['minm'] + p[0]) * S, 1), round((g['maxn'] + 1 - p[1]) * S, 1))
    cs = []
    for c in path:
        seg = [['M', X((c.start_point.x, c.start_point.y))]]
        for s in c.segments:
            if s.is_corner: seg.append(['L', X((s.c.x, s.c.y))]); seg.append(['L', X((s.end_point.x, s.end_point.y))])
            else: seg.append(['C', X((s.c1.x, s.c1.y)), X((s.c2.x, s.c2.y)), X((s.end_point.x, s.end_point.y))])
        cs.append(seg)
    done[k] = {'tfmw': g['tfmw'], 'contours': cs}

json.dump(done, open(outF, 'w'))
left = [k for k in meta if k != 'design' and k not in done]
print('DONE' if not left else f'{len(done)} traced, {len(left)} to go')
