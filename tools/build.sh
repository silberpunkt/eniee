#!/bin/sh
# build.sh -- from the METAFONT sources to OpenType, WOFF and WOFF2.
#   sh tools/build.sh            (run from the repository's top; needs mf, qjs, python3 with potracer and fontTools[woff])
# 1. METAFONT cuts each font at 4800 dpi (ljfour, mag 8): a 10 pt em is 664 pixels.
# 2. gf2glyphs.js (QuickJS) reads METAFONT's GF file: each character's bitmap, its box, its width.
# 3. trace.py (potrace) turns each bitmap into curves, in units of 1/1000 em.
# 4. build.py (fontTools) makes the CFF OpenType font, with TeX's dash ligatures, then WOFF and WOFF2.
# The widths, the word space and the ligatures are METAFONT's own; only the outlines pass through tracing.
set -e
TOP=$(cd "$(dirname "$0")/.." && pwd); W=${TMPDIR:-/tmp}/eniee-build; QJS=${QJS:-qjs}; VER=${VER:-1.320}
mkdir -p $W; cp $TOP/source/*.mf $W/; cd $W
for f in eniee-adria eniee-slender eniee-monad; do
  mf "\\mode=ljfour; mag=8; nonstopmode; input $f" >/dev/null
  rm -rf g_$f; mkdir g_$f; $QJS --std $TOP/tools/gf2glyphs.js $f.4800gf g_$f
  until python3 $TOP/tools/trace.py g_$f 600 | grep -q DONE; do :; done
done
python3 $TOP/tools/build.py g_eniee-adria   $TOP/fonts "Eniee Adria"   Adria   400 0 0.303635 $VER
python3 $TOP/tools/build.py g_eniee-slender $TOP/fonts "Eniee Slender" Slender 300 0 0.303635 $VER
python3 $TOP/tools/build.py g_eniee-monad   $TOP/fonts "Eniee Monad"   Monad   400 1 0.54438  $VER 150   # a line gap of 150 units: code breathes
# (the word spaces are the fonts' SPACE, from  tftopl eniee-adria.tfm  and so on)
