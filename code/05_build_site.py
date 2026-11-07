"""Build index.html from code/page_template.html: every number is a {{path|format}} token from data/results.json; the
results, site.json and land.json are embedded; facts stated in words are checked here. 10.5281/zenodo.24043678, https://doi.org/10.5281/zenodo.24043678 and
https://blog.tristanhotham.com/2026/10/31/gough-map/ stay as placeholders for the publisher."""
import json
from common import *

R = jload(f"{DATA}/results.json"); SITE = jload(f"{DATA}/site.json")
U, SH, G, J, RD = R["units"], R["shape"], R["regions"], R["journeys"], R["roads"]
# facts stated in words (page, blog, paper, collage)
assert 85 <= SH["turn_deg"] <= 100 and SH["turn_deg"] > 90                 # "east at the top, but leaning a further"
assert SH["aniso"] < 1.2                                                   # "barely helps"
assert min(G, key=lambda k: G[k]["err_median_km"]) == "North" and sorted(G, key=lambda k: G[k]["err_median_km"])[1] == "South-east"
assert R["region_err_rank"][0] == "Wales" and G["Wales"]["scale_rel"] > 1.15 and G["North"]["scale_rel"] < 0.95
assert all(w["region"] == "Wales" for w in SH["worst"][:4]) and SH["worst"][3]["err_km"] > 60
assert R["scotland"]["Orkney"]["ratio"] < 0.85 and R["scotland"]["Perth"]["ratio"] < 0.8
assert U["statute_miles_road"] > 1.15                                     # "a longer mile"
assert R["units"]["misfits"][0]["from"] == "Rye" and R["units"]["misfits"][0]["to"] == "Winchelsea"
assert U["longest"]["from"] == "Bristol" and U["longest"]["value"] == 50 and U["longest"]["kpu"] < 1.5   # "one of the most generous"
br = U["by_region"]; assert min(br, key=lambda k: br[k]["kpu"]) == "South-west" and max(br, key=lambda k: br[k]["kpu"]) == "Midlands"
assert U["by_band"]["short"]["kpu"] > U["by_band"]["long"]["kpu"]
assert R["drawn"]["num_err_median_pct"] < R["drawn"]["draw_err_median_pct"] and R["drawn"]["num_better_pct"] > 50
assert max(J, key=lambda k: abs(J[k]["ratio"] - 1)) == "Exeter"
assert all(abs(J[k]["ratio"] - 1) < .05 for k in ("York", "Bristol", "Carlisle"))
assert abs(U["by_period"]["Roman"]["within25_pct"] - U["by_period"]["early modern"]["within25_pct"]) <= 5   # "much the same"
assert abs(U["by_period"]["Roman"]["kpu"] - U["by_period"]["early modern"]["kpu"]) < .1
assert R["located"]["missing_cornwall"] >= 5
assert abs(R["shape"]["turn_sure"] - R["shape"]["turn_deg"]) <= 3
assert R["meta"]["page"] == PAGE
import pandas as _pd
assert int(_pd.read_csv(f"{DATA}/red_lines.csv").query("value > 0").value.min()) == 4   # "run from 4"
assert R["source"]["image_w"] == 12224 and R["source"]["image_h"] == 6021


def build():
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = fill(tpl, R)
    J_ = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    html = html.replace("/*RESULTS*/", J_(R)).replace("/*SITE*/", J_(SITE)).replace("/*LAND*/", open(f"{DATA}/land.json", encoding="utf-8").read())
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
        assert bad not in vis, bad
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()
