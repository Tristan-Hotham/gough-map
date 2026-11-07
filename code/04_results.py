"""Step 4. Every number used anywhere, in data/results.json, and the page data in data/site.json.

  * Units: km per written unit = road km (or straight km) / the figure, over red lines with a legible figure.
  * Agreement: a line agrees within 25% when its figure times the median km per unit is within 25% of its road km.
  * Drawing against numbers: for lines with both ends located, the drawn length (facsimile px / the global similarity scale)
    against the road km, beside the written figure (times the median km per unit) against the road km.
  * Journeys: shortest path over the red lines from London, weighted by the written figure (faded figures filled with the
    road km / median km per unit); compared with the sum of the road km along the same lines and the straight line.
  * Roads: the unique route segments under the red lines, by period code (km and share)."""
import numpy as np, pandas as pd, networkx as nx
from scipy.stats import spearmanr, pearsonr
from common import *

S = pd.read_csv(f"{DATA}/stations.csv")
RL = pd.read_csv(f"{DATA}/red_lines.csv")
LOC = pd.read_csv(f"{DATA}/located.csv")
FIT = jload(f"{DATA}/fit.json")
IMGJ = jload(f"{DATA}/image.json")
R = {"meta": {"page": PAGE, "repo": REPO, "slug": SLUG}}
ws = S[S.kind == "way station"]
R["source"] = {"stations": int(len(ws)), "red_lines": int(len(RL)), "routes": 455, "legible_names": int((ws.legibility == 1).sum()),
               "faded": int(RL.faded.sum()), "with_figure": int((~RL.faded).sum()), "image_w": IMGJ["full"][0], "image_h": IMGJ["full"][1],
               "route_km_all": 4542, "counties": int(ws.county.nunique()), "tiles": IMGJ["tiles"]}
lw = LOC[LOC.kind == "way station"]
R["located"] = {"n": int(len(lw)), "pct": round(100 * len(lw) / len(ws)), "high": int((lw.conf == "high").sum()), "med": int((lw.conf == "med").sum()),
                "low": int((lw.conf == "low").sum()), "missing": int(len(ws) - len(lw)), "controls": int((LOC.kind == "control point").sum()),
                "n_fit": int(len(LOC)), "n_sure": FIT["n_sure"], "loo_median_km": FIT["loo_median_km"],
                "missing_cornwall": int(((ws.county == "Cornwall") & ws.x.isna()).sum())}

# shape
sim = FIT["sim"]
R["shape"] = {"turn_deg": round(sim["turn_deg"]), "turn_off": round(abs(sim["turn_deg"] - 90), 1), "turn_sure": round(sim["turn_deg_sure"]),
              "px_per_km": sim["px_per_km"], "rms_km": sim["rms_km"], "aniso": round(FIT["affine"]["aniso"], 2), "aniso_sure": round(FIT["affine"]["aniso_sure"], 2),
              "err_median_km": round(float(lw.err_km.median()), 1), "err_within25_pct": round(100 * float((lw.err_km <= 25).mean())),
              "err_over50": int((lw.err_km > 50).sum())}
worst = lw.sort_values("err_km", ascending=False).head(5)
R["shape"]["worst"] = [{"name": r.name, "err_km": round(r.err_km), "region": r.region} for r in worst.itertuples()]
R["regions"] = FIT["regions"]
order = sorted(FIT["regions"], key=lambda k: -FIT["regions"][k]["err_median_km"])
R["region_err_rank"] = order
R["scotland"] = FIT["scotland"]
cp = LOC[LOC.kind == "control point"].set_index("id")
R["controls"] = {"orkney_err_km": round(float(cp.err_km[901])), "may_err_km": round(float(cp.err_km[902])), "bass_err_km": round(float(cp.err_km[903])), "perth_err_km": round(float(cp.err_km[904])),
                 "wall_err_km": round(float(cp.err_km[[905, 906]].mean())), "scot_median_km": round(float(cp.err_km[[901, 902, 903, 904]].median()), 1)}

# units and agreement
v = RL[~RL.faded].copy()
v["kpu_road"], v["kpu_gc"] = v.road_km / v.value, v.straight_km / v.value
K = float(v.kpu_road.median()); Kg = float(v.kpu_gc.median())
v["est"] = v.value * K; v["r"] = v.road_km / v.est
w25 = float(((v.r >= 0.8) & (v.r <= 1.25)).mean()); w50 = float(((v.r >= 2 / 3) & (v.r <= 1.5)).mean())
rho = spearmanr(v.value, v.road_km).correlation; pr = pearsonr(v.value, v.road_km)[0]
R["units"] = {"n": int(len(v)), "km_per_unit_road": round(K, 2), "km_per_unit_gc": round(Kg, 2), "q25": round(float(v.kpu_road.quantile(.25)), 2), "q75": round(float(v.kpu_road.quantile(.75)), 2),
              "statute_miles_road": round(K / MILE_KM, 2), "statute_miles_gc": round(Kg / MILE_KM, 2), "mile_km": MILE_KM,
              "within25_pct": round(100 * w25), "within50_pct": round(100 * w50), "spearman": round(rho, 2), "pearson": round(pr, 2),
              "road_over_gc": round(float((RL.road_km / RL.straight_km).median()), 2), "max_value": int(v.value.max()),
              "value_median": int(v.value.median())}
# short and long lines: is the unit constant?
v["band"] = pd.cut(v.value, [0, 8, 12, 99], labels=["short", "mid", "long"])
R["units"]["by_band"] = {b: {"n": int((v.band == b).sum()), "kpu": round(float(v[v.band == b].kpu_road.median()), 2)} for b in ("short", "mid", "long")}
# by region of the first station
reg_of = dict(zip(S.id, S.region))
v["region"] = v.a.map(reg_of)
R["units"]["by_region"] = {r: {"n": int((v.region == r).sum()), "kpu": round(float(v[v.region == r].kpu_road.median()), 2)} for r in RNAMES if (v.region == r).sum() >= 8}
# by main period
v["mp"] = v.main_period.fillna(-1).astype(int)
R["units"]["by_period"] = {PSHORT[p]: {"n": int((v.mp == p).sum()), "kpu": round(float(v[v.mp == p].kpu_road.median()), 2), "within25_pct": round(100 * float(((v[v.mp == p].r >= .8) & (v[v.mp == p].r <= 1.25)).mean()))}
                           for p in (1, 2, 3, 4, 5) if (v.mp == p).sum() >= 8}
long_ = v.sort_values("value", ascending=False).iloc[0]
R["units"]["longest"] = {"from": long_["from"], "to": long_["to"], "value": int(long_.value), "road_km": round(long_.road_km), "kpu": round(long_.kpu_road, 2)}
bad = v.assign(lr=np.abs(np.log(v.r))).sort_values("lr", ascending=False).head(6)
R["units"]["misfits"] = [{"from": r["from"], "to": r["to"], "value": int(r.value), "road_km": round(r.road_km, 1), "ratio": round(r.r, 2)} for _, r in bad.iterrows()]

# drawing against numbers
pos = LOC.set_index("id")
d = v[v.a.isin(pos.index) & v.b.isin(pos.index)].copy()
d["drawn_km"] = [float(np.hypot(pos.x[a] - pos.x[b], pos.y[a] - pos.y[b])) / sim["px_per_km"] for a, b in zip(d.a, d.b)]
e_draw = np.abs(np.log(d.drawn_km / d.road_km)); e_num = np.abs(np.log(d.est / d.road_km))
R["drawn"] = {"n": int(len(d)), "draw_err_median_pct": round(100 * float(np.expm1(e_draw.median()))), "num_err_median_pct": round(100 * float(np.expm1(e_num.median()))),
              "num_better_pct": round(100 * float((e_num < e_draw).mean())), "draw_within25_pct": round(100 * float(((d.drawn_km / d.road_km).between(.8, 1.25)).mean())),
              "num_within25_pct": round(100 * float(((d.est / d.road_km).between(.8, 1.25)).mean())),
              "spearman_draw": round(spearmanr(d.drawn_km, d.road_km).correlation, 2), "spearman_num": round(spearmanr(d.value, d.road_km).correlation, 2)}

# roads under the red lines, by period
import geopandas as gpd
Rt = gpd.read_file(f"{RAW}/gough_routes/gough_routes.shp")
used = set()
for s_ in RL.segments.dropna(): used |= {int(x) for x in str(s_).split()}
U = Rt[Rt.id.isin(used)]
tot = float(U.length_m.sum() / 1000)
R["roads"] = {"segments_used": int(len(U)), "km": round(tot), "by_period": {PSHORT[p]: {"km": round(float(U[U.period == p].length_m.sum() / 1000)), "pct": round(100 * float(U[U.period == p].length_m.sum() / 1000 / tot), 1)} for p in PERIODS},
              "lines_mainly_roman": int((RL.main_period == 1).sum()), "lines_mainly_roman_pct": round(100 * float((RL.main_period == 1).mean())),
              "lines_mainly_early_modern": int((RL.main_period == 5).sum()), "margary_named": int(Rt.margary_no.notna().sum())}
R["roads"]["medieval_pct"] = round(R["roads"]["by_period"]["pre-1086"]["pct"] + R["roads"]["by_period"]["medieval, dated"]["pct"] + R["roads"]["by_period"]["medieval, other"]["pct"], 1)

# journeys from London over the red lines
G = nx.Graph()
for r in RL.itertuples():
    wv = r.value if r.value > 0 else r.road_km / K
    G.add_edge(r.a, r.b, w=wv, road=r.road_km, val=r.value, gc=r.straight_km)
nid = dict(zip(ws.name, ws.id)); nm = dict(zip(ws.id, ws.name)); E = dict(zip(ws.id, zip(ws.E, ws.N)))
LON = nid["London"]
R["network"] = {"components": nx.number_connected_components(G), "largest": len(max(nx.connected_components(G), key=len))}
J = {}
for dest in ("York", "Carlisle", "Lancaster", "Chester", "Bristol", "Exeter", "St David's", "Norwich", "Lincoln", "Canterbury", "Caernarfon", "Southampton", "Scarborough"):
    t = nid[dest]
    if not nx.has_path(G, LON, t): continue
    p = nx.shortest_path(G, LON, t, weight="w")
    ed = [G[a][b] for a, b in zip(p[:-1], p[1:])]
    miles = sum(e["w"] for e in ed); road = sum(e["road"] for e in ed); gc = float(np.hypot(*(np.array(E[LON]) - E[t]))) / 1000
    J[dest] = {"miles": round(miles), "map_km": round(miles * K), "road_km": round(road), "gc_km": round(gc), "legs": len(ed), "faded": sum(1 for e in ed if e["val"] == 0),
               "ratio": round(miles * K / road, 2), "via": [nm[x] for x in p[1:-1]]}
R["journeys"] = J
print(J["York"], J["Carlisle"])

R["regions_table"] = [{"region": k, **FIT["regions"][k]} for k in RNAMES if k in FIT["regions"]]
jsave(R, f"{DATA}/results.json", indent=1)

# page data
reg_i = {n: i for i, n in enumerate(RNAMES)}
SITE = {"regions": [[n, RCOL[n]] for n in RNAMES], "periods": [[p, PERIODS[p], PSHORT[p], PCOL[p]] for p in PERIODS],
        "cols": ["id", "name", "county", "reg", "lon", "lat", "x", "y", "conf", "map_lon", "map_lat", "err", "kind"],
        "st": [[int(r.id), r.name, r.county, reg_i[r.region], r.lon, r.lat, None if pd.isna(r.x) else int(r.x), None if pd.isna(r.y) else int(r.y),
                r.conf if isinstance(r.conf, str) else None,
                None, None, None, 0 if r.kind == "way station" else 1] for r in S.itertuples()],
        "lines": [[int(r.line), int(r.a), int(r.b), int(r.value), r.straight_km, r.road_km, None if pd.isna(r.main_period) else int(r.main_period)] for r in RL.itertuples()],
        "K": round(K, 3), "sim": sim, "image": IMGJ}
lk = LOC.set_index("id")
for row in SITE["st"]:
    if row[0] in lk.index:
        row[9], row[10], row[11] = float(lk.map_lon[row[0]]), float(lk.map_lat[row[0]]), float(lk.err_km[row[0]])
SITE["morph"] = jload(f"{DATA}/morph.json")
SITE["coast_on_map"] = jload(f"{DATA}/coast_on_map.json")
SITE["grid"] = [l["c"] for l in jload(f"{DATA}/grid_on_map.json")]
jsave(SITE, f"{DATA}/site.json")
v[["line", "from", "to", "value", "straight_km", "road_km", "kpu_road", "kpu_gc", "r", "main_period"]].round(3).to_csv(f"{DATA}/mileages.csv", index=False)
print("results ok; site.json", os.path.getsize(f"{DATA}/site.json") // 1024, "KB")
print(json.dumps({k: R[k] for k in ("units", "drawn", "roads", "shape")}, indent=0)[:3500])
