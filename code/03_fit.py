"""Step 3. Fit the map's shape to the ground, and the outlines for the page and figures.

  * Global fits, from British National Grid km to facsimile pixels (y turned up): a similarity (scale, turn, shift) and an
    affine (adds stretch and shear), by least squares over the located places (way stations and control points; "all")
    and over the high and medium confidence ones only ("sure"), as a check.
  * Displacement: each place's facsimile position taken back to the ground through the inverse of the global similarity;
    the arrow from the true place to that point is how far the map misplaces it, at the map's own average scale.
  * Regions: a similarity per region (at least 6 places): its scale against the whole map's and its turn against the whole
    map's turn; and an affine for the stretch (ratio of singular values).
  * Warp: a thin-plate spline (smoothing 2 on km) from ground to facsimile, and the reverse. With it: a 25 km grid of the
    National Grid drawn onto the facsimile (only within 45 km of a located place), the modern coastline bent onto the
    facsimile, and "the Gough shape": the coastline taken to the facsimile and back to the ground by the inverse global
    similarity, for the morph on the page.
  * Outlines: Natural Earth 10m countries clipped to the British Isles and the near Continent (land.json), with ripple lines
    offset 3, 7 and 12 km out to sea for the ink look (ripples.json).
Outputs: data/fit.json, data/located.csv, data/grid_on_map.json, data/coast_on_map.json, data/morph.json, data/land.json,
data/ripples.json."""
import numpy as np, pandas as pd, geopandas as gpd
from scipy.interpolate import RBFInterpolator
from shapely.geometry import box, LineString, MultiLineString, Point
from shapely.ops import unary_union
from pyproj import Transformer
from common import *

S = pd.read_csv(f"{DATA}/stations.csv")
Lc = S[S.x.notna()].copy().reset_index(drop=True)
X = np.c_[Lc.E, Lc.N] / 1000.0                  # ground km
Y = np.c_[Lc.x, -Lc.y]                           # facsimile px, y up
sure = Lc.conf.isin(["high", "med"]).values


def similarity(X, Y):
    """Y ~ s R X + t, complex least squares. Returns s, theta (deg, anticlockwise), t, and a predict function."""
    zx = X[:, 0] + 1j * X[:, 1]; zy = Y[:, 0] + 1j * Y[:, 1]
    A = np.c_[zx, np.ones(len(zx))]
    (a, b), *_ = np.linalg.lstsq(A, zy, rcond=None)
    f = lambda P: (lambda z: np.c_[z.real, z.imag])(a * (P[:, 0] + 1j * P[:, 1]) + b)
    inv = lambda Q: (lambda z: np.c_[z.real, z.imag])(((Q[:, 0] + 1j * Q[:, 1]) - b) / a)
    return abs(a), float(np.degrees(np.angle(a))), f, inv


def affine(X, Y):
    A = np.c_[X, np.ones(len(X))]
    C, *_ = np.linalg.lstsq(A, Y, rcond=None)
    M = C[:2].T                                   # 2x2 linear part
    sv = np.linalg.svd(M, compute_uv=False)
    return M, C, float(sv[0] / sv[1]), lambda P: np.c_[P, np.ones(len(P))] @ C


s_all, th_all, f_all, inv_all = similarity(X, Y)
s_sure, th_sure, _, _ = similarity(X[sure], Y[sure])
M, C, aniso_all, aff_all = affine(X, Y)
_, _, aniso_sure, _ = affine(X[sure], Y[sure])
rms_sim = float(np.sqrt(((f_all(X) - Y) ** 2).sum(1).mean()) / s_all)
rms_aff = float(np.sqrt(((aff_all(X) - Y) ** 2).sum(1).mean()) / s_all)
print(f"similarity: {s_all:.3f} px/km, turn {th_all:.1f} deg; sure only {s_sure:.3f}, {th_sure:.1f}; rms km sim {rms_sim:.1f} affine {rms_aff:.1f}; aniso {aniso_all:.2f}/{aniso_sure:.2f}")
# where on the ground the map puts each place, at the map's average scale and turn
G = inv_all(Y)
Lc["mapE"], Lc["mapN"] = (G[:, 0] * 1000).round(0), (G[:, 1] * 1000).round(0)
Lc["err_km"] = np.hypot(G[:, 0] - X[:, 0], G[:, 1] - X[:, 1]).round(1)
Lc["dE_km"], Lc["dN_km"] = (G[:, 0] - X[:, 0]).round(1), (G[:, 1] - X[:, 1]).round(1)
tf = Transformer.from_crs(27700, 4326, always_xy=True)
lo, la = tf.transform(Lc.mapE.values, Lc.mapN.values)
Lc["map_lon"], Lc["map_lat"] = np.round(lo, 4), np.round(la, 4)

# north on the map: the direction a ground vector pointing north takes on the facsimile
north_dir = (90 + th_all) % 360          # in facsimile coords with y up, measured anticlockwise from the right
reg = {}
for rn in RNAMES:
    m = (Lc.region == rn).values
    if m.sum() < 6: continue
    s, th, f, _ = similarity(X[m], Y[m]); _, _, an, _ = affine(X[m], Y[m])
    res = np.hypot(*(f(X[m]) - Y[m]).T) / s
    reg[rn] = {"n": int(m.sum()), "scale_rel": round(s / s_all, 3), "turn_deg": round(((th - th_all + 180) % 360) - 180, 1),
               "aniso": round(an, 2), "rms_km": round(float(np.sqrt((res ** 2).mean())), 1), "err_median_km": round(float(Lc.err_km[m].median()), 1)}
    print(rn, reg[rn])

# Scotland: control points north of the Wall against the Wall, at the map's average scale
W_mid = Lc[Lc.id.isin([905, 906])][["E", "N", "x", "y"]].mean()
sc = {}
for i, nm in ((901, "Orkney"), (902, "Isle of May"), (903, "Bass Rock"), (904, "Perth")):
    r = Lc[Lc.id == i].iloc[0]
    true_km = float(np.hypot(r.E - W_mid.E, r.N - W_mid.N) / 1000)
    map_km = float(np.hypot(r.x - W_mid.x, r.y - W_mid.y) / s_all)
    sc[nm] = {"true_km": round(true_km), "map_km": round(map_km), "ratio": round(map_km / true_km, 2)}
print("Scotland", sc)

# thin-plate splines both ways
fwd = RBFInterpolator(X, Y, kernel="thin_plate_spline", smoothing=2.0)
bwd = RBFInterpolator(Y, X, kernel="thin_plate_spline", smoothing=2.0)
loo = []
for i in range(len(X)):
    k = np.arange(len(X)) != i
    p = RBFInterpolator(X[k], Y[k], kernel="thin_plate_spline", smoothing=2.0)(X[i:i + 1])[0]
    loo.append(float(np.hypot(*(p - Y[i])) / s_all))
Lc["loo_km"] = np.round(loo, 1)
near = lambda P: np.min(np.hypot(P[:, None, 0] - X[None, :, 0], P[:, None, 1] - X[None, :, 1]), axis=1)

# 25 km grid onto the facsimile
lines = []
for v in range(0, 700, 25):
    for vert in (True,):
        t = np.arange(0, 1250, 2.0)
        P = np.c_[np.full_like(t, v), t] if vert else np.c_[t, np.full_like(t, v)]
        if not vert and v > 1225: continue
        ok = (near(P) < 45) & (P[:, 1] < 600)
        Q = fwd(P)
        run = []
        for o, q in zip(ok, Q):
            if o: run.append([round(float(q[0])), round(float(-q[1]))])
            elif len(run) > 1: lines.append({"v": v, "dir": "E" if vert else "N", "c": run}); run = []
            else: run = []
        if len(run) > 1: lines.append({"v": v, "dir": "E" if vert else "N", "c": run})
for v in range(0, 1250, 25):
    t = np.arange(0, 700, 2.0); P = np.c_[t, np.full_like(t, v)]; ok = (near(P) < 45) & (P[:, 1] < 600); Q = fwd(P); run = []
    for o, q in zip(ok, Q):
        if o: run.append([round(float(q[0])), round(float(-q[1]))])
        elif len(run) > 1: lines.append({"v": v, "dir": "N", "c": run}); run = []
        else: run = []
    if len(run) > 1: lines.append({"v": v, "dir": "N", "c": run})
lines = [l for l in lines if not (l["dir"] == "N" and l["v"] > 1225)]
# the grid stops at N 600 km: north of the Wall there are too few places to bend it

jsave(lines, f"{DATA}/grid_on_map.json")

# coastline of Great Britain (NE 10m) in BNG
C0 = gpd.read_file(f"{GEO}/ne_10m_admin_0_countries.geojson")
gb = C0[C0.ADMIN == "United Kingdom"].to_crs(27700).geometry.iloc[0]
polys = sorted(gb.geoms, key=lambda p: -p.area)
gbmain = [p for p in polys if p.area > 30e6 and p.centroid.x > 0 and not (p.centroid.x < 190000 and p.centroid.y < 600000)]   # not Northern Ireland
coast_map, morph = [], []
south = box(0, -10000, 800000, 585000)                    # England and Wales: south of a line just north of the Wall
for p in gbmain:
    for q in (lambda g: g.geoms if hasattr(g, "geoms") else [g])(p.intersection(south)):
        if q.geom_type != "Polygon" or q.area < 30e6: continue
        ring = np.array(q.exterior.simplify(800).coords) / 1000
        Q = fwd(ring); Gs = inv_all(Q)
        a = np.array(tf.transform(ring[:, 0] * 1000, ring[:, 1] * 1000)).T
        b = np.array(tf.transform(Gs[:, 0] * 1000, Gs[:, 1] * 1000)).T
        morph.append({"true": np.round(a, 4).tolist(), "gough": np.round(b, 4).tolist(), "area": round(q.area / 1e6)})
        ok = near(ring) < 60; run = []
        for o, qq in zip(ok, Q):
            if o: run.append([round(float(qq[0])), round(float(-qq[1]))])
            else:
                if len(run) > 1: coast_map.append(run)
                run = []
        if len(run) > 1: coast_map.append(run)
jsave(coast_map, f"{DATA}/coast_on_map.json")
jsave(morph, f"{DATA}/morph.json")
print("coast parts", len(coast_map), "morph vertices", sum(len(m["true"]) for m in morph))

# land and ripples for the ink map (WGS84)
clip = box(-12, 48.5, 4.5, 61.5)
land = unary_union([g.intersection(clip) for g in C0[C0.geometry.intersects(clip)].geometry]).simplify(0.008)
feats = [{"type": "Feature", "properties": {}, "geometry": g.__geo_interface__} for g in (land.geoms if hasattr(land, "geoms") else [land]) if g.area > 0.0008]
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/land.json")
L27 = gpd.GeoSeries([land], crs=4326).to_crs(27700).iloc[0]
rip = []
for d in (3000, 7000, 12000):
    b = L27.buffer(d, resolution=4).simplify(600)
    rings = [g.exterior for g in (b.geoms if hasattr(b, "geoms") else [b]) if g.area > 2e8]
    for r in rings:
        c = np.array(tf.transform(*np.array(r.coords).T)).T
        rip.append({"type": "Feature", "properties": {"d": d // 1000}, "geometry": {"type": "LineString", "coordinates": np.round(c, 3).tolist()}})
jsave({"type": "FeatureCollection", "features": rip}, f"{DATA}/ripples.json")

cols = ["id", "name", "kind", "county", "region", "lon", "lat", "E", "N", "x", "y", "conf", "map_lon", "map_lat", "dE_km", "dN_km", "err_km", "loo_km", "note"]
Lc[cols].to_csv(f"{DATA}/located.csv", index=False)
jsave({"n": int(len(Lc)), "n_sure": int(sure.sum()), "sim": {"px_per_km": round(s_all, 4), "turn_deg": round(th_all, 2), "px_per_km_sure": round(s_sure, 4), "turn_deg_sure": round(th_sure, 2),
       "rms_km": round(rms_sim, 1)}, "affine": {"M": np.round(M, 5).tolist(), "C": np.round(C, 4).tolist(), "aniso": round(aniso_all, 3), "aniso_sure": round(aniso_sure, 3), "rms_km": round(rms_aff, 1)},
       "north_dir_deg": round(north_dir, 1), "regions": reg, "scotland": sc, "loo_median_km": round(float(np.median(loo)), 1)}, f"{DATA}/fit.json", indent=1)
for f in ("grid_on_map.json", "coast_on_map.json", "morph.json", "land.json", "ripples.json", "located.csv"):
    print(f, os.path.getsize(f"{DATA}/{f}") // 1024, "KB")
