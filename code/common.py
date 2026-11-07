"""Shared paths and helpers for the gough-map study ("The Gough Map: Britain's oldest road map, measured").

Raw inputs (read in place, never modified; from step 03 onward only data/, img/ and tiles/ are needed):
  RAW/gough_way_stations/gough_way_stations.shp
      Oksanen, E. and Brookes, S., The Routes and Roads of the Gough Map: GIS Database, Archaeology Data Service,
      https://doi.org/10.5284/1124312, CC BY 4.0. 179 way stations (settlements joined by a red line), modern name,
      historic county, legibility (0/1). British National Grid (EPSG:27700).
  RAW/gough_red_lines/gough_red_lines.shp     188 red lines between way stations; value = the Roman numeral distance
      written on the map (0 = absent or faded); notes.
  RAW/gough_routes/gough_routes.shp           455 ground-truthed route segments (the real road each red line most likely
      stands for), with period code, category, Margary number, evidence and comments, length_m.
  RAW/Gough_Kaart_hoge_resolutie.jpg          the Gough Map (Bodleian Library, MS. Gough Gen. Top. 16, about 1360),
      12,224 x 6,021 px, Wikimedia Commons "Gough Kaart (hoge resolutie).jpg", a faithful photograph of a
      two-dimensional public domain work (PD-Art).
  GEO    /home/claude/newdata/raw/geo/        Natural Earth 10m land, countries, populated places (public domain).
  FONTS  /home/claude/ref/fonts, INKF /home/claude/studies/ink-map/fonts  Fraunces, Source Serif 4, IBM Plex Mono;
         the Inked World's SDF glyphs and TTFs (IM Fell, MedievalSharp; SIL OFL 1.1).
My own input: data/map_positions.csv (where each way station sits on the facsimile, read by eye; see 02_image.py).
"""
import json, gzip, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("GM_RAW", "/home/claude/newdata/raw_new6/gough")
GEO = os.environ.get("GM_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("GM_FONTS", "/home/claude/ref/fonts")
INKF = os.environ.get("GM_INKF", "/home/claude/studies/ink-map/fonts")
DATA = os.path.join(ROOT, "data")
IMG = os.path.join(ROOT, "img")
WORK = os.path.join(os.environ.get("GMTMP", "/home/claude/work/new6/gough-map"), "work")
for d in (DATA, WORK, IMG):
    os.makedirs(d, exist_ok=True)

SLUG = "gough-map"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
ADS_DOI = "10.5284/1124312"
COMMONS = "https://commons.wikimedia.org/wiki/File:Gough_Kaart_(hoge_resolutie).jpg"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
MILE_KM = 1.609344          # statute mile (1593 Act), for comparison only

# Period codes of gough_routes, as I read them from the attributes and comments (the ADS metadata file was not reachable)
PERIODS = {1: "Roman road", 2: "Evidence before Domesday (1086)", 3: "Dated medieval evidence after Domesday",
           4: "Other medieval evidence", 5: "Early modern road books only", 6: "River", 0: "Undated or modern road"}
PSHORT = {1: "Roman", 2: "pre-1086", 3: "medieval, dated", 4: "medieval, other", 5: "early modern", 6: "river", 0: "undated"}
PCOL = {1: "#A3261B", 2: "#C9A24A", 3: "#3D6E9E", 4: "#6E8250", 5: "#8A6A4E", 6: "#6F9DC6", 0: "#9A9284"}

# Regions: groups of historic counties
REGIONS = [
    ("South-east", "#A3261B", {"Kent", "Sussex", "Surrey", "Middlesex", "Essex", "Hertfordshire", "Berkshire", "Hampshire", "Buckinghamshire", "Oxfordshire", "Bedfordshire"}),
    ("South-west", "#8A6A4E", {"Wiltshire", "Dorset", "Somerset", "Devonshire", "Cornwall", "Gloucestershire"}),
    ("Midlands", "#3D6E9E", {"Warwickshire", "Worcestershire", "Staffordshire", "Leicestershire", "Northamptonshire", "Derbyshire", "Nottinghamshire", "Shropshire", "Herefordshire", "Cheshire"}),
    ("East", "#C9A24A", {"Norfolk", "Suffolk", "Cambridgeshire", "Huntingdonshire", "Lincolnshire"}),
    ("North", "#6E8250", {"Yorkshire", "Yorkshire, North Riding", "Yorkshire, West Riding", "Yorkshire, East Riding", "Lancashire", "Westmorland", "Cumberland", "Northumberland"}),
    ("Wales", "#2F8274", {"Merionethshire", "Denbighshire", "Cardiganshire", "Carnarvonshire", "Carmarthenshire", "Pembrokeshire", "Brecknockshire", "Radnorshire", "Flintshire"}),
    ("Scotland", "#475E78", {"Scotland"}),
]
RNAMES = [r[0] for r in REGIONS]
RCOL = {r[0]: r[1] for r in REGIONS}


def region_of(county):
    for n, c, s in REGIONS:
        if county in s:
            return n
    raise KeyError(county)


# Extra control points beyond the way stations (Scotland and Hadrian's Wall), placed by eye like the stations.
# Coordinates: standard positions (latitude, longitude), rounded to about 1 km.
EXTRA = [
    # id, name, county, lat, lon, x, y, conf, note
    (901, "Orkney (Mainland)", "Scotland", 59.00, -3.10, 1900, 2050, "low", "Insula de Orkeney: the middle of the island drawn"),
    (902, "Isle of May", "Scotland", 56.186, -2.557, 3550, 3080, "med", "small island labelled Mai"),
    (903, "Bass Rock", "Scotland", 56.077, -2.641, 3850, 3410, "med", "island labelled Bass"),
    (904, "Perth", "Scotland", 56.396, -3.437, 4140, 3720, "low", "vignette by the label Perthe"),
    (905, "Hadrian's Wall, east end (Wallsend)", "Northumberland", 54.988, -1.533, 5060, 2850, "med", "upper end of the crenellated wall"),
    (906, "Hadrian's Wall, west end (Bowness-on-Solway)", "Cumberland", 54.953, -3.215, 5320, 3740, "med", "lower end of the crenellated wall"),
]


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from text (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def nonan(v):
    if isinstance(v, float) and v != v:
        return None
    if isinstance(v, list):
        return [nonan(x) for x in v]
    if isinstance(v, dict):
        return {k: nonan(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    obj = dash(nonan(obj))
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "wt", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, allow_nan=False, indent=indent, separators=None if indent else (",", ":"))


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    raise ValueError(f)


def fill(tpl, R, keep=("DOI", "BLOG_URL", "DOI_URL")):
    """Replace {{path|fmt}} tokens with numbers from results.json; placeholders in keep stay."""
    out = re.sub(r"\{\{(?!(?:%s)\}\})([^}|]+)(\|(\w+))?\}\}" % "|".join(keep), lambda m: fmt(get(R, m.group(1).strip()), m.group(3)), tpl)
    left = set(re.findall(r"\{\{([^}]*)\}\}", out))
    assert left <= set(keep), left
    return out


def title_name(s):
    s = s.title().replace("'S", "'s").replace("-In-", "-in-").replace("-Upon-", " upon ").replace("-On-", "-on-").replace("-Under-", "-under-").replace("-The-", "-the-")
    s = s.replace(" In Lindsey", " in Lindsey").replace("Upon-", "upon ").replace(" Upon ", " upon ")
    return s.replace("Barton upon Humber", "Barton-upon-Humber")
