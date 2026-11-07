"""House style for the static figures: paper and ink. Fonts (static Fraunces cut from the variable font, Source Serif,
IBM Plex Mono, IM Fell from the Inked World), the palette, and an ink map of Britain: paper land, black coast, blue
ripple lines on a pale sea wash, in British National Grid km."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly
import numpy as np, pandas as pd
from PIL import Image
from pyproj import Transformer
from common import *

FD = os.path.join(WORK, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    for w, nm in ((900, "Black"), (700, "Bold")):
        instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": w, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-{nm}.ttf")
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf")
DISPB = fm.FontProperties(fname=f"{FD}/Fraunces-Bold.ttf")
SERP = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Regular.ttf")
SERI = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-It.ttf")
FELL = fm.FontProperties(fname=f"{ROOT}/fonts/ttf/IMFeENrm28P.ttf")
FELLI = fm.FontProperties(fname=f"{ROOT}/fonts/ttf/IMFeGPit28P.ttf")
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
MONO = "IBM Plex Mono"
BG, FG, MUT, RULE = "#F6EEDA", "#2B2119", "#6B5D4C", "#E2D3B0"
PAPER, SEA, RIP = "#F3E5BF", "#D5E2EA", "#6F9DC6"
RED, BLUE, GOLD, GREEN = "#A3261B", "#3D6E9E", "#9C7A2E", "#6E8250"
plt.rcParams.update({"font.family": MONO, "font.size": 12, "axes.edgecolor": MUT, "axes.labelcolor": FG, "xtick.color": MUT, "ytick.color": MUT,
                     "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG})
TO27 = Transformer.from_crs(4326, 27700, always_xy=True)


def proj(c):
    c = np.asarray(c); e, n = TO27.transform(c[:, 0], c[:, 1]); return np.c_[e, n] / 1000


LANDP = []
for f in jload(f"{DATA}/land.json")["features"]:
    g = f["geometry"]; ps = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    LANDP += [proj(p[0]) for p in ps]
RIPL = [(f["properties"]["d"], proj(f["geometry"]["coordinates"])) for f in jload(f"{DATA}/ripples.json")["features"]]


def inkmap(ax, ext=(-20, 680, -20, 1000), land=PAPER, ripples=True, lw=.9):
    ax.set_facecolor(SEA)
    if ripples:
        for d, c in RIPL:
            ax.plot(c[:, 0], c[:, 1], color=RIP, lw={3: .9, 7: .65}.get(d, .45), alpha={3: .8, 7: .6}.get(d, .45), zorder=1)
    for p in LANDP:
        ax.add_patch(MPoly(p, closed=True, fc=land, ec=FG, lw=lw, zorder=2))
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect(1)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_visible(False)


def spines(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def facsimile():
    """The 7,000 px facsimile (WORK) and the factor from full-size pixels to it."""
    im = Image.open(f"{WORK}/gough_fig.jpg")
    return im, im.width / 12224
