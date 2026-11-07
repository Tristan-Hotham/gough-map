"""Step 6. The social card (header.png), and the figures for the paper (release/paper/f_*) and the blog (release/blog/b_*).
All from data/ and the facsimile; every number printed comes from results.json."""
import json
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch
from figstyle import *

R = jload(f"{DATA}/results.json"); SITE = jload(f"{DATA}/site.json")
S = pd.read_csv(f"{DATA}/stations.csv"); LOC = pd.read_csv(f"{DATA}/located.csv"); RL = pd.read_csv(f"{DATA}/red_lines.csv")
GRID = jload(f"{DATA}/grid_on_map.json"); MORPH = jload(f"{DATA}/morph.json")
PAP, BLOG = f"{ROOT}/release/paper", f"{ROOT}/release/blog"
os.makedirs(PAP, exist_ok=True); os.makedirs(BLOG, exist_ok=True)
K = R["units"]["km_per_unit_road"]
E = dict(zip(S.id, zip(S.E / 1000, S.N / 1000)))


def save(fig, name, paper=True, blog=True, dpi=150):
    ext, kw = (".jpg", {"pil_kwargs": {"quality": 86}}) if name == "maps" else (".png", {})
    if paper: fig.savefig(f"{PAP}/f_{name}{ext}", dpi=dpi, **kw)
    if blog: fig.savefig(f"{BLOG}/b_{name}{ext}", dpi=1800 / fig.get_figwidth(), **kw)
    plt.close(fig)


def title(fig, t, sub=None, y=.965):
    fig.text(.03, y, t, fontproperties=DISP, fontsize=21, color=FG, va="top")
    if sub: fig.text(.03, y - .052, sub, fontsize=10.5, color=MUT, va="top")


def foot(fig, s="Data: Oksanen and Brookes (ADS, CC BY 4.0); Gough Map photograph, Wikimedia Commons (public domain).\nmaps.tristanhotham.com/gough-map"):
    fig.text(.03, .012, s, fontsize=8, color=MUT, linespacing=1.4)


# 1. the parchment with the located towns and the bent National Grid
im, k = facsimile()
fig = plt.figure(figsize=(14, 7.9)); ax = fig.add_axes([.01, .05, .98, .78]); ax.imshow(im); ax.axis("off")
for l in GRID:
    c = np.array(l["c"]) * k; ax.plot(c[:, 0], c[:, 1], color=BLUE, lw=.6, alpha=.75)
for r in LOC.itertuples():
    ax.add_patch(plt.Circle((r.x * k, r.y * k), 22, fill=False, ec=BLUE if r.kind == "control point" else FG, lw=1.3 if r.conf != "low" else .8, alpha=1 if r.conf != "low" else .7))
title(fig, "The Gough Map with the National Grid bent to fit",
      f"{R['located']['n']} way stations found by eye (black rings) and {R['located']['controls']} control points in Scotland and on Hadrian's Wall (blue).\nThe map was drawn about 1360. Blue lines: the 25 km National Grid. East is at the top.")
foot(fig); save(fig, "maps", dpi=170)

# 2. displacement arrows on the ink map
fig = plt.figure(figsize=(9, 11.5)); ax = fig.add_axes([.02, .05, .96, .82]); inkmap(ax, ext=(100, 680, -10, 640))
for r in LOC.itertuples():
    if r.kind != "way station" and r.N > 640000: continue
    c = RCOL[r.region]
    ax.add_patch(FancyArrowPatch((r.E / 1000, r.N / 1000), (r.E / 1000 + r.dE_km, r.N / 1000 + r.dN_km), arrowstyle="-|>", mutation_scale=8, color=c, lw=1.1, zorder=5))
    ax.plot(r.E / 1000, r.N / 1000, "o", ms=2.6, color=FG, zorder=6)
for w, (tx, ty) in zip(R["shape"]["worst"][:2], ((205, 262), (205, 318))):
    rr = LOC[LOC.name == w["name"]].iloc[0]
    ax.annotate(f"{w['name']}, {w['err_km']} km", (rr.E / 1000 + rr.dE_km, rr.N / 1000 + rr.dN_km), (tx, ty), fontproperties=FELL, fontsize=13, color=FG, ha="right", va="center", zorder=7,
                bbox=dict(fc=SEA, ec="none", alpha=.9, pad=1.2), arrowprops=dict(arrowstyle="-", color=MUT, lw=.6))
hs = [Line2D([], [], color=RCOL[n], lw=2.5, label=f"{n}: median {R['regions'][n]['err_median_km']:.0f} km") for n in RNAMES if n in R["regions"]]
ax.legend(handles=hs, loc="upper left", frameon=True, facecolor=SEA, edgecolor="none", fontsize=9.5, title="Region", title_fontsize=10)
title(fig, "Where the Gough Map puts each town", f"Arrow: from the true place to the map's place, at the map's average scale and turn (median {R['shape']['err_median_km']:.0f} km).", y=.975)
foot(fig, "Data: Oksanen and Brookes (ADS, CC BY 4.0); my positions on the map; Natural Earth. maps.tristanhotham.com/gough-map")
save(fig, "arrows")

# 3. the Gough shape against the true island
fig = plt.figure(figsize=(9, 10.5)); ax = fig.add_axes([.02, .05, .96, .82]); inkmap(ax, ext=(80, 680, -20, 620), land="#F6EEDA")
for m in MORPH:
    g = proj(np.array(m["gough"])); ax.add_patch(MPoly(g, closed=True, fc=RED, alpha=.13, ec=RED, lw=1.4, ls=(0, (4, 2)), zorder=4))
ax.legend(handles=[Line2D([], [], color=FG, lw=1.2, label="True coastline"), Line2D([], [], color=RED, lw=1.4, ls=(0, (4, 2)), label="The coastline in the Gough Map's shape")],
          loc="upper left", facecolor=SEA, edgecolor="none", fontsize=10)
title(fig, "England and Wales as the Gough Map draws them", "The modern coast taken onto the map through the located towns,\nand back at the map's average scale and turn.", y=.975)
foot(fig, "Thin-plate spline through the located towns; Scotland left out (too few points). Natural Earth; Oksanen and Brookes (ADS, CC BY 4.0).")
save(fig, "morph")

# 4. written miles against the road
v = RL[RL.value > 0].copy(); v["mp"] = v.main_period.fillna(0).astype(int)
fig = plt.figure(figsize=(10, 7.4)); ax = fig.add_axes([.09, .13, .56, .68])
xx = np.array([0, 52]); ax.fill_between(xx, xx * K * .8, xx * K * 1.25, color=RULE, alpha=.8, lw=0)
ax.plot(xx, xx * K, ls="--", color=FG, lw=1)
for p in (1, 2, 3, 4, 5, 6, 0):
    q = v[v.mp == p]
    if len(q): ax.scatter(q.value + (q.line % 7 - 3) / 15, q.road_km, s=24, color=PCOL[p], alpha=.85, ec="white", lw=.4, label=PSHORT[p].capitalize() + (" road" if p not in (6, 0) else ""), zorder=3)
spines(ax); ax.set_xlim(0, 52); ax.set_ylim(0, 105); ax.set_xlabel("miles written on the map"); ax.set_ylabel("km along the real road")
ax.text(44, 44 * K + 3, f"{K:.2f} km a mile", fontsize=10, color=FG, rotation=33, ha="center")
ax.legend(loc="center left", bbox_to_anchor=(1.03, .5), frameon=False, fontsize=9.5, title="Most of the road\nunder the line", title_fontsize=10)
title(fig, "The written miles against the real roads", f"{R['units']['n']} red lines with a legible figure. {R['units']['within25_pct']}% within 25% (shaded band) of {K:.2f} km a mile; rank correlation {R['units']['spearman']:.2f}.")
foot(fig); save(fig, "miles")

# 5. drawing against numbers
pos = LOC.set_index("id"); px = R["shape"]["px_per_km"]
d = v[v.a.isin(pos.index) & v.b.isin(pos.index)].copy()
d["dk"] = [np.hypot(pos.x[a] - pos.x[b], pos.y[a] - pos.y[b]) / px for a, b in zip(d.a, d.b)]
en, ed = np.abs(np.log(d.value * K / d.road_km)), np.abs(np.log(d.dk / d.road_km))
fig = plt.figure(figsize=(8.6, 8)); ax = fig.add_axes([.12, .1, .6, .66])
m = np.log(3); ax.plot([0, m], [0, m], ls="--", color=FG, lw=1)
ax.scatter(np.minimum(en, m), np.minimum(ed, m), s=22, c=[RED if a < b else BLUE for a, b in zip(en, ed)], alpha=.8, ec="white", lw=.4)
tk = [0, .25, .5, 1, 2]; ax.set_xticks(np.log1p(tk)); ax.set_yticks(np.log1p(tk)); ax.set_xticklabels([f"{t:.0%}" for t in tk]); ax.set_yticklabels([f"{t:.0%}" for t in tk])
ax.set_xlim(0, m); ax.set_ylim(0, m); spines(ax); ax.set_xlabel("error of the written figure"); ax.set_ylabel("error of the drawn length")
fig.text(.75, .62, f"Red: the number\nis closer\n({R['drawn']['num_better_pct']}% of lines)", color=RED, fontsize=11)
fig.text(.75, .3, "Blue: the drawing\nis closer", color=BLUE, fontsize=11)
title(fig, "The numbers beat the drawing", f"{R['drawn']['n']} red lines: median error {R['drawn']['num_err_median_pct']}% for the written figure, {R['drawn']['draw_err_median_pct']}% for the line as drawn.")
foot(fig, "Errors against the real road; drawn length at the map's average scale. Oksanen and Brookes (ADS, CC BY 4.0).")
save(fig, "drawn")

# 6. regions
D = sorted(R["regions_table"], key=lambda r: r["err_median_km"])
fig = plt.figure(figsize=(9, 5)); ax = fig.add_axes([.17, .13, .62, .66])
ax.barh(range(len(D)), [r["err_median_km"] for r in D], color=[RCOL[r["region"]] for r in D], height=.6)
for i, r in enumerate(D): ax.text(r["err_median_km"] + .6, i, f"{r['err_median_km']:.0f} km · scale {r['scale_rel']:.2f} · {r['n']} towns", va="center", fontsize=9.5)
ax.set_yticks(range(len(D))); ax.set_yticklabels([r["region"] for r in D]); spines(ax); ax.set_xlabel("median misplacement, km"); ax.set_xlim(0, 40)
title(fig, "Wales is drawn largest and furthest out", "Median misplacement of the towns, and each region's own best scale against the map's average.", y=.97)
foot(fig, "Oksanen and Brookes (ADS, CC BY 4.0); my positions on the map.")
save(fig, "regions", blog=False)

# 7. roads by period on the ink map
import geopandas as gpd
Rt = gpd.read_file(f"{RAW}/gough_routes/gough_routes.shp")
fig = plt.figure(figsize=(9, 10.5)); ax = fig.add_axes([.02, .05, .96, .82]); inkmap(ax, ext=(130, 670, -10, 600))
for p in (5, 0, 4, 3, 2, 6, 1):
    for g in Rt[Rt.period == p].geometry:
        for q in (g.geoms if g.geom_type == "MultiLineString" else [g]):
            c = np.array(q.coords) / 1000; ax.plot(c[:, 0], c[:, 1], color=PCOL[p], lw=1.6 if p == 1 else 1.2, zorder=4, solid_capstyle="round")
for r in S[S.kind == "way station"].itertuples(): ax.plot(r.E / 1000, r.N / 1000, "s", ms=2.4, color=FG, zorder=5)
bp = R["roads"]["by_period"]
ax.legend(handles=[Line2D([], [], color=PCOL[p], lw=2.4, label=f"{PERIODS[p]}: {bp[PSHORT[p]]['pct']:.0f}%") for p in (1, 2, 3, 4, 5)], loc="upper right", facecolor=SEA, edgecolor="none", fontsize=9.5)
title(fig, "The real roads under the red lines", f"{R['roads']['km']:,} km traced by Oksanen and Brookes, by the period of the earliest evidence.", y=.975)
foot(fig, "Period codes as I read them. Oksanen and Brookes (ADS, CC BY 4.0); Natural Earth.")
save(fig, "roads")

# 8. journeys
J = sorted(R["journeys"].items(), key=lambda kv: kv[1]["road_km"])
fig = plt.figure(figsize=(9.5, 6.6)); ax = fig.add_axes([.15, .17, .7, .64])
y = np.arange(len(J))
ax.barh(y + .18, [j["map_km"] for _, j in J], height=.34, color=RED, label="by the map's written miles")
ax.barh(y - .18, [j["road_km"] for _, j in J], height=.34, color=MUT, alpha=.55, label="along the real roads")
for i, (n, j) in enumerate(J): ax.text(max(j["map_km"], j["road_km"]) + 6, i, f"{j['miles']} miles", va="center", fontsize=9.5)
ax.set_yticks(y); ax.set_yticklabels([n for n, _ in J]); spines(ax); ax.set_xlabel("km from London"); ax.set_xlim(0, 600)
ax.legend(loc="lower right", frameon=False, fontsize=10)
title(fig, "Journeys from London, by the map's own figures", f"Shortest route over the red lines, written miles at {K:.2f} km a mile, against the real road beneath.", y=.97)
foot(fig); save(fig, "journeys")

# header 1200 x 630
fig = plt.figure(figsize=(12, 6.3), dpi=100); fig.patch.set_facecolor(BG)
ax = fig.add_axes([.43, .04, .55, .92]); crop = im.crop((int(6200 * k), int(500 * k), int(10300 * k), int(5400 * k))); ax.imshow(crop); ax.axis("off")
for r in LOC.itertuples():
    xx, yy = r.x * k - 6200 * k, r.y * k - 500 * k
    if 0 < xx < crop.width and 0 < yy < crop.height: ax.add_patch(plt.Circle((xx, yy), 14, fill=False, ec=FG, lw=1.1))
fig.text(.04, .86, "THE GOUGH", fontproperties=DISP, fontsize=50, color=FG, va="top")
fig.text(.04, .70, "Map", fontproperties=FELL, fontsize=64, color=RED, va="top")
fig.text(.04, .47, "Britain's oldest road map,\nmeasured", fontproperties=SERP, fontsize=21, color=FG, va="top", linespacing=1.3)
fig.text(.04, .26, f"{R['located']['n']} towns found by eye\n{R['units']['within25_pct']}% of written miles right to 25%", fontsize=13, color=MUT, va="top", linespacing=1.5)
fig.text(.04, .06, "Dr Tristan Hotham · maps.tristanhotham.com/gough-map", fontsize=10.5, color=MUT)
fig.savefig(f"{ROOT}/header.png", dpi=100); plt.close(fig)
print(sorted(os.listdir(PAP)), sorted(os.listdir(BLOG)))
