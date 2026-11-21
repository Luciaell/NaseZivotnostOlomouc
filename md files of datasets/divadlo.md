# divadlo.geojson: theatres

| | |
|---|---|
| File | [datasets/divadlo.geojson](../datasets/divadlo.geojson) |
| Source | OpenStreetMap, exported with Overpass Turbo |
| Overpass query | TODO. Inferred from the data: `amenity=theatre` |
| Licence | ODbL (© OpenStreetMap contributors) |
| Export date | 2026-11-20 |
| Features | 6, all inside the Olomouc boundary |
| Geometry | Point (6) |
| Used by the app | No |

## Content
Moravské divadlo, Divadlo hudby, Divadlo Tramtárie, Divadlo na Šantovce, o.p.s., Na Cucky and Moravská filharmonie (a concert venue tagged as a theatre).

## Properties
Numbers in brackets are how many of the 6 features have a value.

| Key | Meaning |
|---|---|
| `@id` (6) | OSM ID |
| `amenity` (6) | Always `theatre` |
| `name` (6) | Name |
| `website` (3), `contact:facebook` (1) | Website, Facebook |
| `wikipedia` (3), `wikidata` (2), `wikimedia_commons` (1) | Links |
| `wheelchair` (1), `theatre:type` (1) | Wheelchair access, kind of theatre |

## Notes
- Only nodes are included. Theatres mapped only as buildings (ways) would be missing, so check the export query before relying on the count.
- Every feature has a `name`.
