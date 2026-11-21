# restaurace_hospody_bary_cluby.geojson: restaurants

| | |
|---|---|
| File | [datasets/restaurace_hospody_bary_cluby.geojson](../datasets/restaurace_hospody_bary_cluby.geojson) |
| Source | OpenStreetMap, exported with Overpass Turbo |
| Overpass query | TODO. Inferred from the data: `amenity=restaurant` |
| Licence | ODbL (© OpenStreetMap contributors) |
| Export date | 2026-11-20 |
| Features | 128, of which 127 are inside the Olomouc boundary |
| Geometry | Point (128) |
| Used by the app | No |

## Content
**Despite the file name, every feature is `amenity=restaurant`.** Pubs (`amenity=pub`), bars (`amenity=bar`) and clubs (`amenity=nightclub`) are not in the file. Some restaurants are pub-like (e.g. `Kozlovna`, `Radegast`, breweries), but places tagged only as pubs or bars are missing.

The one feature outside the city boundary is `Hostinec Citadela` (49.6090, 17.1939).

## Properties
Numbers in brackets are how many of the 128 features have a value.

| Key | Meaning |
|---|---|
| `@id` (128) | OSM ID |
| `amenity` (128) | Always `restaurant` |
| `name` (127) | Name, e.g. `Pizzeria u Jana` |
| `opening_hours` (83) | Opening hours |
| `cuisine` (57) | Cuisine, e.g. `regional` (7), `pizza` (7), `italian` (5), `asian` (4), `vietnamese` (3). Several values are separated by `;` |
| `website` (57), `phone` (41), `email` (24), `contact:facebook` (10) | Contacts |
| `addr:*` (33–51) | Address |
| `wheelchair` (33) | Wheelchair access |
| `outdoor_seating` (27), `indoor_seating` (22) | Seating |
| `smoking` (21), `air_conditioning` (18), `internet_access` (20) | Facilities |
| `diet:vegetarian` (20), `diet:vegan` (18), `diet:gluten_free` (20), `diet:halal` / `diet:kosher` (15) | Diet options |
| `payment:*` (4–22) | Payment methods, incl. Bitcoin Lightning via Qerko |
| `takeaway` (7), `delivery` (7), `brewery` (6) | Other services |
| Others | `level`, `toilets`, `changing_table`, `note`, `website:menu`, check dates |

## Notes
- If pubs, bars and clubs are wanted, re-export with `amenity~"^(restaurant|pub|bar|nightclub)$"`, or rename the file to match its content.
- 1 feature has no `name`, so a fallback name would be needed.
