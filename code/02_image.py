"""Step 2. The facsimile for the web and the figures.

  * Positions: data/map_positions.csv holds where each way station sits on the facsimile, in full-size pixels
    (12,224 x 6,021; x to the right, y down; the map is drawn with east at the top, so north is to the left). I found them by
    eye on zoomed crops with a pixel grid: first a few unmistakable places (London, York, Exeter, St David's), then an
    affine and later a thin-plate-spline fit from those to predict where the rest should be, then each one read on the
    crop: the label where legible, otherwise the town drawing at the end of the right red line with the right numeral.
    conf: high (label read), med (the right drawing on the right red line), low (faded, or one of several candidates).
  * Tiles: the image is laid on a Web Mercator world 16,384 px wide (zoom 6), one image pixel per world pixel, centred on
    the equator, and cut into 256 px JPEG tiles for zooms 0 to 6. The page converts image pixels to these pseudo
    coordinates (fit offsets in data/image.json).
  * Images: img/gough_small.jpg (3,000 px wide, fallback and collage) and WORK/gough_fig.jpg (7,000 px, figures)."""
import shutil
import numpy as np
from PIL import Image
from common import *

Image.MAX_IMAGE_PIXELS = None
im = Image.open(f"{RAW}/Gough_Kaart_hoge_resolutie.jpg").convert("RGB")
FW, FH = im.size
assert (FW, FH) == (12224, 6021)
Z = 6; WORLD = 256 * 2 ** Z
X0, Y0 = (WORLD - FW) // 2, (WORLD - FH) // 2
T = os.path.join(ROOT, "tiles")
if os.path.exists(T): shutil.rmtree(T)
PAPER = (226, 214, 184)
n, nb = 0, 0
for z in range(0, Z + 1):
    s = 2 ** (z - Z)
    w, h = max(1, round(FW * s)), max(1, round(FH * s))
    S = im if s == 1 else im.resize((w, h), Image.LANCZOS)
    ox, oy = X0 * s, Y0 * s
    for tx in range(int(ox // 256), int((ox + w - 1) // 256) + 1):
        for ty in range(int(oy // 256), int((oy + h - 1) // 256) + 1):
            t = Image.new("RGB", (256, 256), PAPER)
            t.paste(S, (int(round(ox - tx * 256)), int(round(oy - ty * 256))))
            os.makedirs(f"{T}/{z}/{tx}", exist_ok=True)
            fn = f"{T}/{z}/{tx}/{ty}.jpg"; t.save(fn, quality=70, optimize=True, progressive=True)
            n += 1; nb += os.path.getsize(fn)
print("tiles", n, nb // 1024, "KB")
im.resize((3000, round(FH * 3000 / FW)), Image.LANCZOS).save(f"{IMG}/gough_small.jpg", quality=80, optimize=True, progressive=True)
im.resize((7000, round(FH * 7000 / FW)), Image.LANCZOS).save(f"{WORK}/gough_fig.jpg", quality=86)
jsave({"full": [FW, FH], "world": WORLD, "x0": X0, "y0": Y0, "maxzoom": Z, "tiles": n, "tile_kb": nb // 1024, "small": [3000, round(FH * 3000 / FW)]}, f"{DATA}/image.json", indent=1)
