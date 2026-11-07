"""Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.24043678, https://doi.org/10.5281/zenodo.24043678 and https://blog.tristanhotham.com/2026/10/31/gough-map/ stay as placeholders for the publisher."""
import json as _json, shutil, zipfile, importlib.util
from common import *

spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "05_build_site.py"))
spec.loader.exec_module(importlib.util.module_from_spec(spec))          # shared fact checks
R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release"); NAME = "Hotham_Gough_Map"
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}
# words and alt text in the blog
assert len(R["journeys"]) == 10                                        # "ten journeys"
assert R["units"]["n"] == 169 and abs(R["units"]["km_per_unit_road"] - 2.08) < .005   # alt text of b_miles
assert R["shape"]["worst"][0]["name"] == "Aberystwyth" and R["shape"]["worst"][0]["err_km"] == 70
assert R["regions"]["North"]["scale_rel"] < 1

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG)([^}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u_), post, re.M) for u_ in used) and "wp:image" not in post
from PIL import Image
for img in used:
    assert Image.open(f"{REL}/blog/{img}").size[0] == 1800, img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{([^|}]+)\}\}", post)) <= KEEP
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS"):
    assert bad not in vis, bad
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
sh, u = R["shape"], R["units"]
meta = {"title": "The Gough Map: Britain's oldest road map, measured",
        "slug": "gough-map",
        "excerpt": f"I found {R['located']['n']} towns by eye on a map of Britain drawn about 1360. Its shape puts a typical town {sh['err_median_km']:.0f} km out of place and blows Wales up, yet {u['within25_pct']}% of the miles written along its red roads are within 25% of the real road.",
        "seo_description": f"The Gough Map of about 1360 measured: {R['located']['n']} towns located, a shape {sh['err_median_km']:.0f} km out, and written miles right to 25% on {u['within25_pct']}% of roads.",
        "tags": ["maps", "history", "Gough Map", "medieval", "roads", "cartography", "data visualisation", "Britain"],
        "header_alt": f"Title card reading 'The Gough Map' in black and red on pale paper, beside a crop of the medieval map of England and Wales with small black rings on the towns, and the lines '{R['located']['n']} towns found by eye' and '{u['within25_pct']}% of written miles right to 25%'."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/gough-map_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for dd in ("code", "data"):
        for fn in sorted(os.listdir(os.path.join(ROOT, dd))):
            if fn.endswith(".pyc") or fn == "__pycache__":
                continue
            z.write(os.path.join(ROOT, dd, fn), f"gough-map/{dd}/{fn}")
    for fn in ("README.md", "LICENSE", "index.html", "img/gough_small.jpg"):
        z.write(os.path.join(ROOT, fn), f"gough-map/{fn}")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), "gough-map/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("\\textdegree{}", "°")
zmeta = {"title": "The Gough Map: Britain's Oldest Road Map, Measured",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {{https://blog.tristanhotham.com/2026/10/31/gough-map/}}.</p><p>Sources: E. Oksanen and S. Brookes, The Routes and Roads of the Gough Map: GIS Database, Archaeology Data Service, https://doi.org/{ADS_DOI} (CC BY 4.0); the Gough Map, Bodleian Library MS. Gough Gen. Top. 16, photograph on Wikimedia Commons (public domain); Natural Earth (public domain). Positions on the map located by the author.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["Gough Map", "medieval cartography", "road networks", "itineraries", "map distortion", "historical GIS", "Britain", "open data"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": ADS_DOI, "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.naturalearthdata.com/", "relation": "isDerivedFrom", "resource_type": "dataset"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj
jsave(zmeta, f"{Z}/metadata.json", indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
