// gf2glyphs.js -- read a METAFONT GF file and write each character's bitmap, its box and its TFM width. QuickJS.
//   qjs --std gf2glyphs.js font.4800gf outdir     -> outdir/<code>.pbm (P4) and outdir/glyphs.json
// GF is METAFONT's own output: per character, rows of black runs (paint), boxed by min_m..max_m, min_n..max_n in
// pixels about the character's reference point (the left end of its baseline). The postamble holds each width.
const [gfF, out] = [scriptArgs[1], scriptArgs[2]];
const f = std.open(gfF, 'rb'); const all = []; { const b = new ArrayBuffer(1 << 16); let n; while ((n = f.read(b, 0, b.byteLength)) > 0) all.push(new Uint8Array(b.slice(0, n))); } f.close();
const len = all.reduce((a, c) => a + c.length, 0), g = new Uint8Array(len); { let o = 0; for (const c of all) { g.set(c, o); o += c.length; } }
let p = 0;
const u = (k) => { let v = 0; for (let i = 0; i < k; i++) v = v * 256 + g[p++]; return v; };
const s = (k) => { let v = u(k); if (v >= 2 ** (8 * k - 1)) v -= 2 ** (8 * k); return v; };
const glyphs = {};
let cur = null, m = 0, n = 0, black = false, rows = null;
const paint = (d) => { if (black) for (let x = m; x < m + d; x++) rows[cur.maxn - n][x - cur.minm] = 1; m += d; black = !black; };
while (p < len) {
  const op = g[p++];
  if (op <= 63) paint(op);
  else if (op <= 66) paint(u(op - 63));
  else if (op === 67 || op === 68) {                     // boc, boc1
    let c, minm, maxm, minn, maxn;
    if (op === 67) { c = s(4); s(4); minm = s(4); maxm = s(4); minn = s(4); maxn = s(4); }
    else { c = u(1); const dm = u(1); maxm = u(1); minm = maxm - dm; const dn = u(1); maxn = u(1); minn = maxn - dn; }
    cur = { code: ((c % 256) + 256) % 256, minm, maxm, minn, maxn }; rows = [];
    for (let y = 0; y <= maxn - minn; y++) rows.push(new Uint8Array(maxm - minm + 1));
    m = minm; n = maxn; black = false;
  }
  else if (op === 69) { cur.rows = rows; glyphs[cur.code] = cur; cur = null; }   // eoc
  else if (op === 70) { n -= 1; m = cur.minm; black = false; }                  // skip0
  else if (op >= 71 && op <= 73) { n -= 1 + u(op - 70); m = cur.minm; black = false; }
  else if (op >= 74 && op <= 238) { n -= 1; m = cur.minm + (op - 74); black = true; }   // new_row_k
  else if (op >= 239 && op <= 242) { const k = u(op - 238); p += k; }                          // xxx
  else if (op === 243) p += 4;                                                   // yyy
  else if (op === 244) { }                                                       // no_op
  else if (op === 245 || op === 246) {                                           // char_loc, char_loc0
    const c = u(1); let dx;
    if (op === 245) { dx = s(4) / 65536; s(4); } else { dx = u(1); }
    const w = s(4) / 2 ** 20; s(4);
    (glyphs[c] = glyphs[c] || { code: c }).tfmw = w; glyphs[c].dx = dx;
  }
  else if (op === 247) { p++; const k = u(1); p += k; }                                       // pre
  else if (op === 248) { p += 4; glyphs.design = s(4) / 2 ** 20; p += 28; }   // post: pointer, design size, checksum, hppp, vppp, bounds
  else if (op === 249) break;                                                    // post_post
}
const meta = {};
for (const k in glyphs) { const G = glyphs[k]; if (k === 'design') continue; if (!G.rows) { meta[k] = { tfmw: G.tfmw }; continue; }
  const W = G.maxm - G.minm + 1, H = G.maxn - G.minn + 1, bw = Math.ceil(W / 8), body = new Uint8Array(bw * H);
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) if (G.rows[y][x]) body[y * bw + (x >> 3)] |= 0x80 >> (x & 7);
  const head = `P4\n${W} ${H}\n`, o = std.open(`${out}/${k}.pbm`, 'wb'), hb = new Uint8Array([...head].map((c) => c.charCodeAt(0)));
  o.write(hb.buffer, 0, hb.length); o.write(body.buffer, 0, body.length); o.close();
  meta[k] = { minm: G.minm, maxm: G.maxm, minn: G.minn, maxn: G.maxn, tfmw: G.tfmw, dx: G.dx };
}
meta.design = glyphs.design;
const o = std.open(`${out}/glyphs.json`, 'w'); o.puts(JSON.stringify(meta)); o.close();
print(Object.keys(meta).length - 1, 'characters');
