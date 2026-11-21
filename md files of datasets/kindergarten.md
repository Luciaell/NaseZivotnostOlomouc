# kindergarten.geojson: kindergartens

| | |
|---|---|
| File | [datasets/kindergarten.geojson](../datasets/kindergarten.geojson) |
| Source | OpenStreetMap, exported with Overpass Turbo |
| Overpass query | TODO. Inferred from the data: `amenity=kindergarten` |
| Licence | ODbL (© OpenStreetMap contributors) |
| Export date | 2026-11-18 |
| Features | 47, all inside the Olomouc boundary |
| Geometry | Polygon (24), Point (23) |
| Used by the app | Yes: `CATEGORIES["kindergartens"]`, fallback name `MŠ (bez názvu)` |

## Properties
Numbers in brackets are how many of the 47 features have a value.

| Key | Meaning |
|---|---|
| `@id` (47) | OSM ID, e.g. `way/305249857` (ways are the polygons) |
| `amenity`, `education` (47) | Always `kindergarten` |
| `name` (37) | Name, e.g. `MŠ Herrmannova` |
| `website` (28) | Website |
| `check_date` (6), `opening_hours` (4), `preschool` (3) | Last survey date, opening hours, preschool flag |
| Others (1–2 each) | `operator`, `email`, `phone`, `min_age`/`max_age`, address tags, social media, diet tags |

## How the app uses it
- Polygons are reduced to their area centroid.
- 10 kindergartens have no `name`, so they show the fallback name `MŠ (bez názvu)`.

## Notes
- The polygons outline the building or grounds, so a kindergarten mapped as a polygon may be counted from a point a few dozen metres from its entrance.
- Kindergartens that are part of a primary school (`Základní škola a mateřská škola …`) may only be mapped as the school in OSM.
