"""Build the paper: fill code/paper_template.tex from data/results.json, add the tables, compile with xelatex.
Output: release/paper/Hotham_Gough_Map.pdf and .tex (figures f_*.png beside them). The DOI stays as the 10.5281/zenodo.24043678 placeholder."""
import subprocess
import pandas as pd
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Gough_Map"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")
# statements made in words in the paper only
assert all(w["name"] in ("Aberystwyth", "Aberdovey", "Barmouth", "Harlech", "Llanenddwyn") for w in R["shape"]["worst"][:5])   # "all on the coast of Cardigan Bay"
assert abs(R["shape"]["turn_sure"] - R["shape"]["turn_deg"]) < 2 and abs(jload(f"{DATA}/fit.json")["sim"]["turn_deg_sure"] - jload(f"{DATA}/fit.json")["sim"]["turn_deg"]) < 2
assert all(18 < R["regions"][k]["err_median_km"] < 22 for k in ("Midlands", "East", "South-west"))   # "near 20 km"
assert R["scotland"]["Isle of May"]["ratio"] > 1 and R["scotland"]["Bass Rock"]["ratio"] > 1


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    return tex(str(v))


rows = "".join(f"{tex(r['region'])} & {r['n']} & {r['err_median_km']:.1f} & {r['rms_km']:.1f} & {r['scale_rel']:.2f} & {r['turn_deg']:+.1f} & {r['aniso']:.2f}\\\\\n" for r in R["regions_table"])
TR = ("\\begin{table}[tbp]\\centering\\small\\caption{Regions (groups of historic counties): located places; median misplacement at the overall similarity (km); RMS residual of the region's own similarity fit (km); its scale relative to the whole map; its rotation relative to the whole map (degrees, anticlockwise positive); and the stretch of its affine fit.}\\label{tab:regions}"
      "\\begin{tabular}{lrrrrrr}\\toprule Region & Places & Misplaced & RMS & Scale & Turn & Stretch\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
L = pd.read_csv(f"{DATA}/located.csv").sort_values(["region", "name"])
rows = "".join(f"{tex(r.name)} & {tex(r.county)} & {int(r.x):,} & {int(r.y):,} & {r.conf} & {r.err_km:.0f}\\\\\n" for r in L.itertuples())
TL = ("{\\footnotesize\\setlength{\\tabcolsep}{4pt}\\begin{longtable}{p{5.4cm}p{4.2cm}rrlr}\\caption{The " + str(len(L)) + " places located on the photograph of the Gough Map (12,224 by 6,021 pixels; x to the right, y down), with confidence and misplacement (km) at the overall similarity, by region and name.}\\label{tab:located}\\\\"
      "\\toprule Place & County & x & y & Read & km\\\\\\midrule\\endfirsthead\\toprule Place & County & x & y & Read & km\\\\\\midrule\\endhead\n" + rows + "\\bottomrule\\end{longtable}}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
t = t.replace("PAGEURL", PAGE).replace("REPOURL", REPO).replace("DOIPLACEHOLDER", "https://doi.org/\\{\\{DOI\\}\\}")
t = re.sub(r"\{\{(?!TABLE_)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
t = t.replace("{{TABLE_REGIONS}}", TR).replace("{{TABLE_LOCATED}}", TL)
assert "--" not in t and "—" not in t and "–" not in t
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(3):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
print([l for l in log.splitlines() if l.startswith("!")][:5])
for ext in (".aux", ".log", ".out", ".bbl", ".blg"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("—") + txt.count("–") + txt.count("--"))
