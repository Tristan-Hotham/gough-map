# Reddit post (r/dataisbeautiful)

**Title:** [OC] Britain's oldest road map (about 1360) puts the typical town 18 km out of place, but 72% of the distances written on its roads are within 25% of the real road

**Body:**

The Gough Map is a map of Britain drawn about 1360, with east at the top. Its red lines between towns, each with a distance in Roman numerals, make it the oldest surviving road map of Britain.

I located 157 of its 179 towns by eye on a photograph of the map and fitted it to the real island, then checked 169 of its written distances against the real roads traced by Oksanen and Brookes.

- Panel 1: the map as drawn, with the towns I found and the 25 km National Grid bent to fit.
- Panel 2: the real island, with an arrow from each town to where the map puts it. Wales is drawn 1.22 times too big and is the most out of place (33 km median).
- Panel 3: written miles against the real road. One map mile is about 2.08 km of road.

The numbers beat the drawing: the written distance is off by a median 13%, the drawn line by 31%. London to York adds up to 202 miles on the map, 420 km, against 424 km of real road.

Interactive version with both maps side by side: https://maps.tristanhotham.com/gough-map/

**Source comment:**

Data: Oksanen, E. and Brookes, S., The Routes and Roads of the Gough Map: GIS Database, Archaeology Data Service (CC BY 4.0), https://doi.org/10.5284/1124312. Map: Bodleian Library, MS. Gough Gen. Top. 16, photograph on Wikimedia Commons (public domain). Coastline: Natural Earth. Positions on the map read by me; 68 of them are uncertain. Tools: Python (geopandas, scipy, matplotlib). Write-up and code: https://maps.tristanhotham.com/gough-map/
