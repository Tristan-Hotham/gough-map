"""The Reddit collage (r/dataisbeautiful style, light paper): the parchment with the towns I found and the bent grid, the
true island with arrows to where the map puts each town, and the written miles against the real roads.
Every number from data/results.json. Output: reddit/gough_map.png (2,880 x 1,800 px)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code"))
from figstyle import *
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch
import matplotlib.patheffects as pe

R = jload(f"{DATA}/results.json"); LOC = pd.read_csv(f"{DATA}/located.csv"); RL = pd.read_csv(f"{DATA}/red_lines.csv")
GRID = jload(f"{DATA}/grid_on_map.json")
K = R["units"]["km_per_unit_road"]
NUMF = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Semibold.ttf")
HALO = [pe.withStroke(linewidth=4, foreground=BG)]
fig = plt.figure(figsize=(24, 15), dpi=120)
fig.text(.02, .965, "The Gough Map draws Britain on its side, with a typical town "
         f"{R['shape']['err_median_km']:.0f} km out of place", fontproperties=DISP, fontsize=34, color=FG, va="top")
fig.text(.02, .915, f"Britain's oldest road map, drawn about 1360. But the miles written along its red roads are right to within 25% on {R['units']['within25_pct']}% of them.\n"
         f"I found {R['located']['n']} of its {R['source']['stations']} towns by eye and checked {R['units']['n']} distances.",
         fontproperties=SERP, fontsize=19, color=MUT, va="top", linespacing=1.3)

# the parchment
im, k = facsimile()
ax = fig.add_axes([.015, .37, .58, .46]); ax.imshow(im); ax.axis("off")
for l in GRID:
    c = np.array(l["c"]) * k; ax.plot(c[:, 0], c[:, 1], color=BLUE, lw=.7, alpha=.7)
for r in LOC.itertuples():
    ax.add_patch(plt.Circle((r.x * k, r.y * k), 26, fill=False, ec=BLUE if r.kind == "control point" else FG, lw=1.4 if r.conf != "low" else .9))
ax.text(.01, 1.005, "1. As drawn: east at the top. Rings: the towns I found. Blue: the 25 km National Grid bent to fit",
        transform=ax.transAxes, fontsize=13.5, color=FG, va="bottom")
for txt, (x, y) in (("SCOTLAND", (1300, 3100)), ("WALES", (8100, 4650)), ("KENT", (8650, 520)), ("LONDON", (8840, 1610)), ("ORKNEY", (1900, 2400))):
    ax.text(x * k, y * k, txt, fontproperties=DISP, fontsize=15, color=RED, ha="center", va="center", path_effects=[pe.withStroke(linewidth=4, foreground="#F6EEDA")])

# the true island with arrows
ax2 = fig.add_axes([.60, .04, .39, .775]); inkmap(ax2, ext=(110, 680, -125, 640))
for r in LOC.itertuples():
    if r.N > 640000: continue
    ax2.add_patch(FancyArrowPatch((r.E / 1000, r.N / 1000), (r.E / 1000 + r.dE_km, r.N / 1000 + r.dN_km), arrowstyle="-|>", mutation_scale=10, color=RCOL[r.region], lw=1.3, zorder=5))
    ax2.plot(r.E / 1000, r.N / 1000, "o", ms=3, color=FG, zorder=6)
ax2.text(.02, 1.005, "2. England and Wales only (no red lines in Scotland).\nArrow: from a town's true place to where the map puts it", transform=ax2.transAxes, fontsize=13.5, color=FG, va="bottom")
hs = [Line2D([], [], color=RCOL[n], lw=3, label=f"{n}: median {R['regions'][n]['err_median_km']:.0f} km") for n in RNAMES if n in R["regions"]]
ax2.legend(handles=hs, loc="lower left", facecolor=SEA, edgecolor="none", fontsize=12.5, title="Median misplacement by region", title_fontsize=13)
w0 = R["shape"]["worst"][0]; rr = LOC[LOC.name == w0["name"]].iloc[0]
ax2.annotate(f"{w0['name']}\n{w0['err_km']} km out", (rr.E / 1000 + rr.dE_km, rr.N / 1000 + rr.dN_km), (165, 455), fontproperties=FELL, fontsize=17, color=FG, ha="center",
             arrowprops=dict(arrowstyle="-", color=MUT, lw=.8), path_effects=HALO)
ax2.text(470, -15, "Wales is drawn at\n" + f"{R['regions']['Wales']['scale_rel']:.2f} times the scale\nof the rest", fontproperties=FELL, fontsize=16, color=FG, ha="center", path_effects=HALO)

# miles scatter
ax3 = fig.add_axes([.055, .085, .25, .25])
v = RL[RL.value > 0]; xx = np.array([0, 52])
ax3.fill_between(xx, xx * K * .8, xx * K * 1.25, color=RULE, lw=0)
ax3.plot(xx, xx * K, ls="--", color=FG, lw=1)
ax3.scatter(v.value + (v.line % 7 - 3) / 15, v.road_km, s=20, color=RED, alpha=.75, ec="white", lw=.4, zorder=3)
spines(ax3); ax3.set_xlim(0, 52); ax3.set_ylim(0, 100); ax3.set_xlabel("miles written on the map", fontsize=12); ax3.set_ylabel("km along the real road", fontsize=12)
ax3.text(0, 1.06, f"3. Written miles against the real roads: one mile = {K:.2f} km", transform=ax3.transAxes, fontsize=13.5, color=FG)
ax3.text(30, 15, f"shaded: within 25%\n({R['units']['within25_pct']}% of {R['units']['n']} lines)", fontsize=11.5, color=MUT)

# big numbers
for i, (num, txt, col) in enumerate(((f"{R['drawn']['num_err_median_pct']}%", "median error of the written miles", RED),
                                     (f"{R['drawn']['draw_err_median_pct']}%", "median error of the same\nroads as drawn", BLUE),
                                     (f"{R['journeys']['York']['miles']}", f"miles from London to York:\n{R['journeys']['York']['map_km']} km by the map,\n{R['journeys']['York']['road_km']} km of real road", GREEN))):
    y = .30 - i * .095
    fig.text(.355, y, num, fontproperties=NUMF, fontsize=40, color=col, va="center")
    fig.text(.445, y, txt, fontsize=13.5, color=FG, va="center", linespacing=1.35)
fig.text(.02, .012, "Data: Oksanen and Brookes, The Routes and Roads of the Gough Map, Archaeology Data Service (CC BY 4.0). Map: Bodleian Library, MS. Gough Gen. Top. 16, "
         "photograph, Wikimedia Commons (public domain). Natural Earth.   maps.tristanhotham.com/gough-map",
         fontsize=11, color=MUT)
out = os.path.join(ROOT, "reddit", "gough_map.png")
fig.savefig(out, dpi=120); plt.close(fig)
from PIL import Image
print(out, Image.open(out).size)
