# specimen.py -- specimen.png: the same lines in each of the three cuts, each under its name (a Rosetta stone).
#   python3 tools/specimen.py            (from the repository's top)
import os
from PIL import Image, ImageDraw, ImageFont
TOP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = lambda n, s: ImageFont.truetype(os.path.join(TOP, 'fonts', f'Eniee{n}-Regular.otf'), s)
SZ, LAB = 50, 24
PITCH = round(SZ * 1.16)       # leading: close set, no air
lines = ["Of ballads, songs and snatches, and dreamy lullaby!",
         "Up with Antidisestablishmentarianism.",
         "Supercalifragilisticexpialidocious: Be it!",
         "(define (sqrt x) (fixed-point (lambda (y) (/ x y)) 1.0))",
         "æ œ Æ Œ ß ø Ø ä ö ü Ä Ö Ü § ¤ ¡ ¿ ‘quote’ “x” Γ Δ Ω ↑ ↓ a---b",
         "0123456789 {|} ~ @#$%^&*_+=<>? it's iiii mmmm"]
W, H = 1800, 40 + PITCH + 3 * (LAB + 14 + PITCH * len(lines) + 22)
img = Image.new('L', (W, H), 0); d = ImageDraw.Draw(img)   # black, the type in light (User1: "Blacken the type samples")
y = 18
d.text((24, y), "A wandering minstrel I -- a thing of shreds and patches,", font=F('Adria', SZ), fill=235); y += PITCH + 18
for name, label in (('Adria', 'Eniee adria'), ('Slender', 'Eniee slender'), ('Monad', 'Eniee monad')):
    d.text((24, y), label, font=F('Adria', LAB), fill=235); y += LAB + 14
    for t in lines:
        d.text((24, y), t, font=F(name, SZ), fill=235); y += PITCH
    y += 22
img.crop((0, 0, W, y)).save(os.path.join(TOP, 'specimen.png'))
print('specimen.png', W, y)
