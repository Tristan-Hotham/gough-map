# The Gough Map: Britain's oldest road map, measured

The Gough Map (Bodleian Library, MS. Gough Gen. Top. 16), drawn about 1360 with east at the top, set against the real island and its roads: 157 of its 179 way stations located by eye on a photograph of the map, its shape fitted to the true positions, and 169 of the distances written on its red lines checked against the real routes traced by Oksanen and Brookes.

Interactive page: https://maps.tristanhotham.com/gough-map/
Paper: https://doi.org/10.5281/zenodo.24043678
Blog post: https://blog.tristanhotham.com/2026/10/31/gough-map/
Code and data: https://github.com/Tristan-Hotham/gough-map

## Headline results

- Orientation: the best similarity fit turns the map 95° from north-up (east at the top, leaning a further 4.6°). At its average scale the median way station is misplaced by 17.6 km; 76% are within 25 km. An affine fit adds little (stretch 1.11).
- Regions: the north of England (12.6 km) and the south-east (13.9 km) are drawn best. Wales is drawn at 1.22 times the overall scale and misplaced by a median 33.2 km; Aberystwyth is 70 km out. Scotland is compressed: Orkney is drawn 356 km from Hadrian's Wall for 450 km in reality.
- Miles: one written mile is a median 2.08 km of road (1.29 statute miles) and 1.89 km in a straight line. 72% of 169 figures are within 25% of the road at that rate (rank correlation 0.74).
- Numbers beat drawing: for 146 lines, the written figure is wrong by a median 13% against 31% for the line as drawn, and is closer on 66% of lines.
- Journeys: London to York is 202 written miles, 420 km at the map's rate, against 424 km of road; to Bristol 202 against 203; to Carlisle 485 against 493.
- Roads: of 4,505 km of road under the red lines, 35.4% is Roman, 28.9% has medieval evidence and 32.7% is known only from the early modern road books. The figures are as good on Roman roads as on later ones.

## Files

| File | What it is |
|:-|:-|
| `index.html` | The interactive page (built by `code/05_build_site.py`; page data embedded; MapLibre GL JS 4.7.1 from jsDelivr). |
| `header.png` | Social card, 1200 x 630. |
| `tiles/` | The photograph of the map as 256 px JPEG tiles, zooms 0 to 6 (public domain). |
| `img/gough_small.jpg` | The map at 3,000 px wide (fallback view). |
| `fonts/` | MapLibre glyphs from the Inked World ("Ink Roman", "Ink Italic", "Ink Caps", from IM Fell and MedievalSharp, SIL OFL 1.1) and the IM Fell TTFs used in the figures. |
| `data/map_positions.csv` | My input: where each way station is drawn on the photograph (full-size pixels, x right, y down) with confidence and a note on how I found it. |
| `data/stations.csv` | The 179 way stations and 6 control points: name, county, region, National Grid and WGS84 position, map position, confidence. |
| `data/located.csv` | The 163 located places with misplacement (km), its east and north parts, the map position taken back to the ground, and a leave-one-out check. |
| `data/red_lines.csv` | The 188 red lines: ends, written figure, straight and road km, share of the road in each period code, the route segments used. |
| `data/mileages.csv` | The 169 red lines with a legible figure and their km per written mile. |
| `data/results.json`, `data/site.json`, `data/fit.json`, `data/image.json` | Every number used; page data; the fits; the tile frame. |
| `data/roads.geojson`, `data/red_lines.geojson` | The traced roads (simplified, WGS84, with period) and the red lines as straight lines. |
| `data/grid_on_map.json`, `data/coast_on_map.json`, `data/morph.json` | The National Grid and coastline bent onto the map (image pixels), and England and Wales in the map's shape. |
| `data/land.json`, `data/ripples.json` | Natural Earth land and ripple lines for the ink map. |
| `code/` | Scripts, run in order, the page, paper and blog templates, and `qa.js`. |
| `release/` | Paper (`paper/`), blog post and figures (`blog/`), Zenodo files (`zenodo/`). |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |

## Method in brief

- Positions on the map: read by eye on gridded crops of the 12,224 x 6,021 px photograph, guided by an affine and then a thin-plate-spline prediction from the towns already found: 33 by a legible label, 56 by the right drawing on the right red line, 68 uncertain; 22 not found (6 in Cornwall). Six control points in Scotland and on Hadrian's Wall. Leave-one-out check: median 8.1 km.
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

- Oksanen, E. and Brookes, S. (2024) The Routes and Roads of the Gough Map: GIS Database. Archaeology Data Service. https://doi.org/10.5284/1124312. CC BY 4.0. Derived tables here are shared under the same licence, with credit.
- The Gough Map, about 1360, Bodleian Library, MS. Gough Gen. Top. 16. Photograph: Wikimedia Commons, https://commons.wikimedia.org/wiki/File:Gough_Kaart_(hoge_resolutie).jpg, a faithful reproduction of a two-dimensional public domain work (public domain).
- Natural Earth (public domain). Optional layers on the page: © OpenStreetMap contributors and © CARTO (modern map and labels), Esri (relief).
- Glyphs from the Inked World (IM Fell by Igino Marini, MedievalSharp; SIL Open Font Licence 1.1, licence in `fonts/ttf/`).

## Citation

Hotham, T. (2026) The Gough Map: Britain's oldest road map, measured. Zenodo. https://doi.org/10.5281/zenodo.24043678

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
