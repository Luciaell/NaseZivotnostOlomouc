# supermarket.geojson: supermarkets

| | |
|---|---|
| File | [datasets/supermarket.geojson](../datasets/supermarket.geojson) |
| Source | OpenStreetMap, exported with Overpass Turbo |
| Overpass query | TODO. Inferred from the data: `shop=supermarket` over an area much larger than Olomouc |
| Licence | ODbL (© OpenStreetMap contributors) |
| Export date | 2026-11-11 |
| Features | 1035, of which **38** are inside the Olomouc boundary |
| Geometry | Point (621), Polygon (414) |
| Used by the app | Yes: `CATEGORIES["supermarkets"]`, fallback name `Supermarket (bez názvu)` |

## Content
The export covers a wide region, which is why the backend filters it to the city boundary. It is also the largest file (about 1 MB).

## Properties
Numbers in brackets are how many of the 1035 features have a value.

| Key | Meaning |
|---|---|
| `@id` (1035) | OSM ID (nodes, ways and relations) |
| `shop` (1035) | Always `supermarket` |
| `name` (1012) | Name, usually the chain, e.g. `Billa`, `Lidl` |
| `brand`, `brand:wikidata` (≈820), `brand:wikipedia` (498) | Chain |
| `opening_hours` (672) | Opening hours |
| `website` (435), `operator` (425), `phone` (165), `email` (60) | Contacts and operator |
| `building`, `building:levels` (≈410 / 186) | Building tags (on polygons) |
| `addr:*` (≈330–390) | Address, incl. Czech `addr:conscriptionnumber` / `addr:streetnumber` |
| `branch` (89) | Branch name, e.g. which Lidl |
| `ref:ruian:building`, `ref:minvskaddress`, `source:addr` | Links to Czech (RÚIAN) and Slovak address registers |
| Others | wheelchair, payment methods, `level`, `start_date`, check dates |

## How the app uses it
- The name is `name`, then `brand`, then the fallback.
- Polygons are reduced to their area centroid. Relations (MultiPolygons) use the part with the most vertices.

## Notes
- The `ref:minvskaddress` key and the name `Biedronka` show that the export also reaches into Slovakia and Poland. Only the 38 features inside Olomouc matter.
- Names are mostly chain names, so the summary line shows e.g. `Nejbližší supermarket: Lidl (…)` without the branch.
