# kino.geojson: cinemas

| | |
|---|---|
| File | [datasets/kino.geojson](../datasets/kino.geojson) |
| Source | OpenStreetMap, exported with Overpass Turbo |
| Overpass query | TODO. Inferred from the data: `amenity=cinema` |
| Licence | ODbL (© OpenStreetMap contributors) |
| Export date | 2026-11-20 |
| Features | 4, all inside the Olomouc boundary |
| Geometry | Point (4) |
| Used by the app | No |

## Content
Cinestar, Multikino - Premiere Cinemas, 5D cinema Maxim and Čekárna.

## Properties
Numbers in brackets are how many of the 4 features have a value.

| Key | Meaning |
|---|---|
| `@id` (4) | OSM ID |
| `amenity` (4) | Always `cinema` |
| `name` (4) | Name |
| `wheelchair` (2) | Wheelchair access |
| `brand`, `brand:wikidata`, `brand:wikipedia` (1) | Chain (`CineStar`) |
| `indoor:area`, `indoor:level`, `level` (1) | Position inside a shopping centre |
| Others (1 each) | address tags, `phone`, `email`, `website`, `contact:facebook`, `opening_hours`, `note`, `start_date` |

## Notes
- Small art-house cinemas mapped only as buildings (ways) would be missing, so check the export query before relying on the count.
- Every feature has a `name`.
