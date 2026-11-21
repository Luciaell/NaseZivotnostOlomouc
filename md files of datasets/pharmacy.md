# pharmacy.geojson: pharmacies

| | |
|---|---|
| File | [datasets/pharmacy.geojson](../datasets/pharmacy.geojson) |
| Source | OpenStreetMap, exported with Overpass Turbo |
| Overpass query | TODO. Inferred from the data: `amenity=pharmacy` |
| Licence | ODbL (© OpenStreetMap contributors) |
| Export date | 2026-11-18 |
| Features | 37, all inside the Olomouc boundary |
| Geometry | Point (35), Polygon (2) |
| Used by the app | Yes: `CATEGORIES["pharmacies"]`, fallback name `Lékárna (bez názvu)` |

## Properties
Numbers in brackets are how many of the 37 features have a value.

| Key | Meaning |
|---|---|
| `@id` (37) | OSM ID |
| `amenity`, `healthcare` (37) | Always `pharmacy` |
| `name` (37) | Name, e.g. `Lékárna Rena`. Chain pharmacies are often named after the chain (`Dr. Max`) |
| `opening_hours` (32) | Opening hours in OSM syntax |
| `email` (27), `phone` (24), `website` (20), `contact:*` (6–9) | Contacts (both plain and `contact:` keys are used) |
| `brand`, `brand:wikidata` (14) | Chain: `Dr. Max` (9), `Benu` (4), `Agel` (1) |
| `ref:SUKL` (13) | Pharmacy code in the SÚKL (State Institute for Drug Control) register |
| `wheelchair` (13) | Wheelchair access |
| `dispensing` (5) | `yes` = dispenses prescription drugs |
| Others | address tags, `level`, `check_date`, payment methods, building tags (on the 2 polygons) |

## How the app uses it
- Every feature has a `name`, so the fallback is not used.
- Polygons are reduced to their area centroid.

## Notes
- Hospital pharmacies are included, e.g. `( Z ) Lékárna FN Olomouc`.
- Several pharmacies share a chain name (`Dr. Max`), so names alone do not identify a branch. Use `osm_id`.
