"""Step 1. Read the ADS GIS layers, join the by-eye positions, and measure every red line along the real roads.

  * Stations: 179 way stations, to WGS84; region from the historic county; my position on the facsimile from
    data/map_positions.csv (157 located) plus six extra control points in Scotland and on Hadrian's Wall (common.EXTRA).
  * Red lines: each line's two end stations (end points coincide with a station; five are within 0.6 km).
    Straight line = distance between the stations in British National Grid metres.
  * Roads: the 455 route segments become a graph (segment ends joined within 60 m); each station is put on the nearest
    graph node within 3 km; the road distance of a red line is the shortest path between its stations, kept if it is
    at most twice the straight line plus 10 km. Its period mix is the share of that path's length in each period code.
Outputs: data/stations.csv, data/red_lines.csv, data/roads.geojson, data/red_lines.geojson, WORK/graph.json."""
import numpy as np, pandas as pd, geopandas as gpd, networkx as nx
from shapely.geometry import LineString
from common import *

W = gpd.read_file(f"{RAW}/gough_way_stations/gough_way_stations.shp")
L = gpd.read_file(f"{RAW}/gough_red_lines/gough_red_lines.shp")
Rt = gpd.read_file(f"{RAW}/gough_routes/gough_routes.shp")
from shapely.ops import linemerge
Rt["geometry"] = [linemerge(g) if g.geom_type == "MultiLineString" else g for g in Rt.geometry]
Rt["geometry"] = [max(g.geoms, key=lambda q: q.length) if g.geom_type == "MultiLineString" else g for g in Rt.geometry]   # a handful of split parts: keep the main one for ends
assert len(W) == 179 and len(L) == 188 and len(Rt) == 455
W["E"], W["N"] = W.geometry.x, W.geometry.y
g = W.to_crs(4326); W["lon"], W["lat"] = g.geometry.x.round(5), g.geometry.y.round(5)
W["name"] = W.settlement.map(title_name)
W["region"] = W.county.map(region_of)
P = pd.read_csv(f"{DATA}/map_positions.csv")
W = W.merge(P[["id", "x", "y", "conf", "note"]], on="id", how="left")
S = W[["id", "name", "county", "region", "legibility", "E", "N", "lon", "lat", "x", "y", "conf", "note"]].copy()
S["kind"] = "way station"
from pyproj import Transformer
tf = Transformer.from_crs(4326, 27700, always_xy=True)
ex = []
for i, n, c, la, lo, x, y, cf, nt in EXTRA:
    e, no = tf.transform(lo, la)
    ex.append(dict(id=i, name=n, county=c, region="Scotland" if c == "Scotland" else "North", legibility=None, E=round(e, 1), N=round(no, 1), lon=lo, lat=la, x=x, y=y, conf=cf, note=nt, kind="control point"))
S = pd.concat([S, pd.DataFrame(ex)], ignore_index=True)
S["E"], S["N"] = S.E.round(1), S.N.round(1)

# red lines to station pairs
PT = W[["E", "N"]].values
rows = []
for r in L.itertuples():
    c = list(r.geometry.coords)
    da, db = np.hypot(*(PT - c[0]).T), np.hypot(*(PT - c[-1]).T)
    a, b = int(da.argmin()), int(db.argmin())
    assert da.min() < 600 and db.min() < 600, r.id
    rows.append(dict(line=int(r.id), a=int(W.id[a]), b=int(W.id[b]), value=int(r.value), note=r.notes if isinstance(r.notes, str) else ""))
RL = pd.DataFrame(rows)
RL["faded"] = RL.value == 0
RL["straight_km"] = [np.hypot(*(PT[W.index[W.id == a][0]] - PT[W.index[W.id == b][0]])) / 1000 for a, b in zip(RL.a, RL.b)]

# road graph
G = nx.Graph(); key = lambda p: (round(p[0] / 30), round(p[1] / 30))
NODE = {}
def node(p):
    k = key(p)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            kk = (k[0] + dx, k[1] + dy)
            if kk in NODE: return NODE[kk]
    NODE[k] = len(NODE); G.add_node(NODE[k], xy=p); return NODE[k]
from scipy.spatial import cKDTree
RAWR = gpd.read_file(f"{RAW}/gough_routes/gough_routes.shp")
for r in RAWR.itertuples():
    parts = r.geometry.geoms if r.geometry.geom_type == "MultiLineString" else [r.geometry]
    k = r.length_m / 1000 / sum(q.length / 1000 for q in parts)          # scale vertex steps to the stated length_m
    for q in parts:
        c = list(q.coords)
        for p0, p1 in zip(c[:-1], c[1:]):
            u, v = node(p0), node(p1)
            if u == v: continue
            ln = np.hypot(p1[0] - p0[0], p1[1] - p0[1]) / 1000 * k
            if G.has_edge(u, v) and G[u][v]["km"] <= ln: continue
            G.add_edge(u, v, km=ln, seg=int(r.id), period=int(r.period))
# loose ends: join each degree-1 node to the nearest node of another segment within 400 m
xy = np.array([G.nodes[n]["xy"] for n in G.nodes]); ids = list(G.nodes); tree = cKDTree(xy)
segof = {n: {G[n][m]["seg"] for m in G[n]} for n in G.nodes}
for i, n in enumerate(ids):
    if G.degree(n) != 1: continue
    for d, j in zip(*tree.query(xy[i], k=12, distance_upper_bound=400)):
        if j >= len(ids) or ids[j] == n or segof[ids[j]] & segof[n]: continue
        G.add_edge(n, ids[j], km=d / 1000, seg=-1, period=next(iter(G[n].values()))["period"]); break
NXY = np.array([G.nodes[n]["xy"] for n in G.nodes]); NID = list(G.nodes)
snap = {}; snapd = {}
for s in W.itertuples():
    d = np.hypot(*(NXY - (s.E, s.N)).T); i = int(d.argmin())
    if d[i] < 3000: snap[s.id] = NID[i]; snapd[s.id] = d[i] / 1000
print("max snap km", round(max(snapd.values()), 2), "median", round(float(np.median(list(snapd.values()))), 3))
print("graph", G.number_of_nodes(), "nodes", G.number_of_edges(), "edges; stations snapped", len(snap), "components", nx.number_connected_components(G))
road, mix, segs = [], [], []
for r in RL.itertuples():
    km, m, sg = None, {}, []
    if r.a in snap and r.b in snap:
        try:
            path = nx.shortest_path(G, snap[r.a], snap[r.b], weight="km")
            es = [G[u][v] for u, v in zip(path[:-1], path[1:])]
            k = sum(e["km"] for e in es) + snapd[r.a] + snapd[r.b]
            if k <= 2 * r.straight_km + 10:
                km = k; sg = sorted({e["seg"] for e in es if e["seg"] > 0})
                for e in es: m[e["period"]] = m.get(e["period"], 0) + e["km"] / k
        except nx.NetworkXNoPath:
            pass
    road.append(km); mix.append(m); segs.append(sg)
RL["road_km"] = road
for p in PERIODS: RL[f"p{p}"] = [round(m.get(p, 0), 3) for m in mix]
RL["main_period"] = [max(m, key=m.get) if m else None for m in mix]
RL["segments"] = [" ".join(map(str, s)) for s in segs]
nm = dict(zip(W.id, W.name))
RL["from"], RL["to"] = RL.a.map(nm), RL.b.map(nm)
print("red lines with road", RL.road_km.notna().sum(), "of", len(RL))
RL["straight_km"] = RL.straight_km.round(2); RL["road_km"] = RL.road_km.round(2)
RL[["line", "a", "from", "b", "to", "value", "faded", "straight_km", "road_km", "main_period"] + [f"p{p}" for p in PERIODS] + ["segments", "note"]].to_csv(f"{DATA}/red_lines.csv", index=False)
S.to_csv(f"{DATA}/stations.csv", index=False)

# web layers (WGS84, simplified)
R4 = Rt.copy(); R4["geometry"] = R4.geometry.simplify(40); R4 = R4.to_crs(4326)
feats = [{"type": "Feature", "properties": {"id": int(r.id), "p": int(r.period), "m": r.margary_no if isinstance(r.margary_no, str) else "", "km": round(r.length_m / 1000, 1),
          "c": (r.comments if isinstance(r.comments, str) else "")[:160]},
          "geometry": {"type": "LineString", "coordinates": [[round(x, 4), round(y, 4)] for x, y in r.geometry.coords]}} for r in R4.itertuples()]
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/roads.geojson")
ll = dict(zip(W.id, zip(W.lon, W.lat)))
jsave({"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"line": int(r.line), "v": int(r.value), "a": int(r.a), "b": int(r.b)},
       "geometry": {"type": "LineString", "coordinates": [list(ll[r.a]), list(ll[r.b])]}} for r in RL.itertuples()]}, f"{DATA}/red_lines.geojson")
print({f: os.path.getsize(f"{DATA}/{f}") // 1024 for f in ("roads.geojson", "red_lines.geojson", "stations.csv", "red_lines.csv")})
