"""README.md, LICENSE and reddit/post.md, every number from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json")
U, SH, D, J, RD, L = R["units"], R["shape"], R["drawn"], R["journeys"], R["roads"], R["located"]
G = R["regions"]
readme = f"""# The Gough Map: Britain's oldest road map, measured

The Gough Map (Bodleian Library, MS. Gough Gen. Top. 16), drawn about 1360 with east at the top, set against the real island and its roads: {L['n']} of its {R['source']['stations']} way stations located by eye on a photograph of the map, its shape fitted to the true positions, and {U['n']} of the distances written on its red lines checked against the real routes traced by Oksanen and Brookes.

Interactive page: {PAGE}
Paper: https://doi.org/{{10.5281/zenodo.24043678}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/gough-map/}}
Code and data: {REPO}

## Headline results

- Orientation: the best similarity fit turns the map {SH['turn_deg']}° from north-up (east at the top, leaning a further {SH['turn_off']:.1f}°). At its average scale the median way station is misplaced by {SH['err_median_km']:.1f} km; {SH['err_within25_pct']}% are within 25 km. An affine fit adds little (stretch {SH['aniso']:.2f}).
- Regions: the north of England ({G['North']['err_median_km']:.1f} km) and the south-east ({G['South-east']['err_median_km']:.1f} km) are drawn best. Wales is drawn at {G['Wales']['scale_rel']:.2f} times the overall scale and misplaced by a median {G['Wales']['err_median_km']:.1f} km; {SH['worst'][0]['name']} is {SH['worst'][0]['err_km']} km out. Scotland is compressed: Orkney is drawn {R['scotland']['Orkney']['map_km']} km from Hadrian's Wall for {R['scotland']['Orkney']['true_km']} km in reality.
- Miles: one written mile is a median {U['km_per_unit_road']:.2f} km of road ({U['statute_miles_road']:.2f} statute miles) and {U['km_per_unit_gc']:.2f} km in a straight line. {U['within25_pct']}% of {U['n']} figures are within 25% of the road at that rate (rank correlation {U['spearman']:.2f}).
- Numbers beat drawing: for {D['n']} lines, the written figure is wrong by a median {D['num_err_median_pct']}% against {D['draw_err_median_pct']}% for the line as drawn, and is closer on {D['num_better_pct']}% of lines.
- Journeys: London to York is {J['York']['miles']} written miles, {J['York']['map_km']} km at the map's rate, against {J['York']['road_km']} km of road; to Bristol {J['Bristol']['map_km']} against {J['Bristol']['road_km']}; to Carlisle {J['Carlisle']['map_km']} against {J['Carlisle']['road_km']}.
- Roads: of {RD['km']:,} km of road under the red lines, {RD['by_period']['Roman']['pct']:.1f}% is Roman, {RD['medieval_pct']:.1f}% has medieval evidence and {RD['by_period']['early modern']['pct']:.1f}% is known only from the early modern road books. The figures are as good on Roman roads as on later ones.

## Files

| File | What it is |
|:-|:-|
| `index.html` | The interactive page (built by `code/05_build_site.py`; page data embedded; MapLibre GL JS 4.7.1 from jsDelivr). |
| `header.png` | Social card, 1200 x 630. |
| `tiles/` | The photograph of the map as 256 px JPEG tiles, zooms 0 to 6 (public domain). |
| `img/gough_small.jpg` | The map at 3,000 px wide (fallback view). |
| `fonts/` | MapLibre glyphs from the Inked World ("Ink Roman", "Ink Italic", "Ink Caps", from IM Fell and MedievalSharp, SIL OFL 1.1) and the IM Fell TTFs used in the figures. |
| `data/map_positions.csv` | My input: where each way station is drawn on the photograph (full-size pixels, x right, y down) with confidence and a note on how I found it. |
| `data/stations.csv` | The {R['source']['stations']} way stations and {L['controls']} control points: name, county, region, National Grid and WGS84 position, map position, confidence. |
| `data/located.csv` | The {L['n_fit']} located places with misplacement (km), its east and north parts, the map position taken back to the ground, and a leave-one-out check. |
| `data/red_lines.csv` | The {R['source']['red_lines']} red lines: ends, written figure, straight and road km, share of the road in each period code, the route segments used. |
| `data/mileages.csv` | The {U['n']} red lines with a legible figure and their km per written mile. |
| `data/results.json`, `data/site.json`, `data/fit.json`, `data/image.json` | Every number used; page data; the fits; the tile frame. |
| `data/roads.geojson`, `data/red_lines.geojson` | The traced roads (simplified, WGS84, with period) and the red lines as straight lines. |
| `data/grid_on_map.json`, `data/coast_on_map.json`, `data/morph.json` | The National Grid and coastline bent onto the map (image pixels), and England and Wales in the map's shape. |
| `data/land.json`, `data/ripples.json` | Natural Earth land and ripple lines for the ink map. |
| `code/` | Scripts, run in order, the page, paper and blog templates, and `qa.js`. |
| `release/` | Paper (`paper/`), blog post and figures (`blog/`), Zenodo files (`zenodo/`). |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |

## Method in brief

- Positions on the map: read by eye on gridded crops of the {R['source']['image_w']:,} x {R['source']['image_h']:,} px photograph, guided by an affine and then a thin-plate-spline prediction from the towns already found: {L['high']} by a legible label, {L['med']} by the right drawing on the right red line, {L['low']} uncertain; {L['missing']} not found ({L['missing_cornwall']} in Cornwall). Six control points in Scotland and on Hadrian's Wall. Leave-one-out check: median {L['loo_median_km']:.1f} km.
- Shape: similarity and affine least-squares fits from British National Grid to image pixels; misplacement = distance from the true place to the map place taken back through the inverse similarity. Region fits for at least 6 places. A thin-plate spline (smoothing 2) bends the grid, the coastline and the island for the figures and the page (England and Wales only).
- Distances: the traced routes as a vertex-level network; stations snapped to the nearest vertex; shortest path between the two stations of each red line, using the database's segment lengths. Km per mile = road km / figure. Journeys: shortest path over the red lines by written figure.
- Period codes (numeric in the database, key not reachable): read as 1 Roman road, 2 evidence before Domesday, 3 dated medieval evidence after Domesday, 4 other medieval evidence, 5 early modern road books only, 6 river, 0 undated or modern.
- Caveats: positions by eye (some uncertain, some missing); routes as identified by Oksanen and Brookes; fits summarise a map drawn without a projection; few points in Scotland.

## How to rerun

Needs Python 3 with numpy, pandas, geopandas, shapely, pyproj, scipy, networkx, matplotlib, Pillow and fontTools, xelatex (TeX Gyre Pagella, Inter) and pdftotext; node with Playwright for `code/qa.js`. Steps 01 and 02 read the raw files (paths in `code/common.py`): the three ADS shapefiles, the photograph and Natural Earth; intermediates go to `GMTMP`.

```
python3 code/01_data.py         # stations, red lines, road distances
python3 code/02_image.py        # tiles and images
python3 code/03_fit.py          # fits, bent grid and coast, morph, outlines
python3 code/04_results.py      # results.json, site.json
python3 code/05_build_site.py   # index.html
python3 code/06_figures.py      # header, paper and blog figures
python3 code/07_paper.py        # paper PDF
python3 reddit/collage.py       # collage
python3 code/08_readme.py       # README, LICENSE, Reddit post
python3 code/09_release.py      # blog post, Zenodo files
```

## Sources and licences

- Oksanen, E. and Brookes, S. (2024) The Routes and Roads of the Gough Map: GIS Database. Archaeology Data Service. https://doi.org/{ADS_DOI}. CC BY 4.0. Derived tables here are shared under the same licence, with credit.
- The Gough Map, about 1360, Bodleian Library, MS. Gough Gen. Top. 16. Photograph: Wikimedia Commons, {COMMONS}, a faithful reproduction of a two-dimensional public domain work (public domain).
- Natural Earth (public domain). Optional layers on the page: © OpenStreetMap contributors and © CARTO (modern map and labels), Esri (relief).
- Glyphs from the Inked World (IM Fell by Igino Marini, MedievalSharp; SIL Open Font Licence 1.1, licence in `fonts/ttf/`).

## Citation

Hotham, T. (2026) The Gough Map: Britain's oldest road map, measured. Zenodo. https://doi.org/{{10.5281/zenodo.24043678}}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)
lic = """MIT License (code)

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Text, figures and derived data: Creative Commons Attribution 4.0 International (CC BY 4.0), https://creativecommons.org/licenses/by/4.0/

Third-party data and media:
- Road database: Oksanen, E. and Brookes, S., The Routes and Roads of the Gough Map: GIS Database, Archaeology Data Service, https://doi.org/10.5284/1124312, CC BY 4.0.
- The Gough Map photograph (tiles/, img/): public domain (Wikimedia Commons).
- Natural Earth: public domain.
- fonts/: SIL Open Font Licence 1.1 (see fonts/ttf/OFL-IMFell.txt and OFL-MedievalSharp.txt).
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)
post = f"""# Reddit post (r/dataisbeautiful)

**Title:** [OC] Britain's oldest road map (about 1360) puts the typical town {SH['err_median_km']:.0f} km out of place, but {U['within25_pct']}% of the distances written on its roads are within 25% of the real road

**Body:**

The Gough Map is a map of Britain drawn about 1360, with east at the top. Its red lines between towns, each with a distance in Roman numerals, make it the oldest surviving road map of Britain.

I located {L['n']} of its {R['source']['stations']} towns by eye on a photograph of the map and fitted it to the real island, then checked {U['n']} of its written distances against the real roads traced by Oksanen and Brookes.

- Panel 1: the map as drawn, with the towns I found and the 25 km National Grid bent to fit.
- Panel 2: the real island, with an arrow from each town to where the map puts it. Wales is drawn {G['Wales']['scale_rel']:.2f} times too big and is the most out of place ({G['Wales']['err_median_km']:.0f} km median).
- Panel 3: written miles against the real road. One map mile is about {U['km_per_unit_road']:.2f} km of road.

The numbers beat the drawing: the written distance is off by a median {D['num_err_median_pct']}%, the drawn line by {D['draw_err_median_pct']}%. London to York adds up to {J['York']['miles']} miles on the map, {J['York']['map_km']} km, against {J['York']['road_km']} km of real road.

Interactive version with both maps side by side: {PAGE}

**Source comment:**

Data: Oksanen, E. and Brookes, S., The Routes and Roads of the Gough Map: GIS Database, Archaeology Data Service (CC BY 4.0), https://doi.org/{ADS_DOI}. Map: Bodleian Library, MS. Gough Gen. Top. 16, photograph on Wikimedia Commons (public domain). Coastline: Natural Earth. Positions on the map read by me; {L['low']} of them are uncertain. Tools: Python (geopandas, scipy, matplotlib). Write-up and code: {PAGE}
"""
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
for t in (readme, lic, post):
    for bad in ("—", "–", "--", "DSIT", "DCMS"):
        assert bad not in t, bad
print("README, LICENSE, post.md written")
