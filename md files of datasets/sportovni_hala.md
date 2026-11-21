# sportovni_hala.geojson: sports halls

| | |
|---|---|
| File | [datasets/sportovni_hala.geojson](../datasets/sportovni_hala.geojson) |
| Source | OpenStreetMap, exported with Overpass Turbo |
| Overpass query | TODO. Inferred from the data: `leisure=sports_hall` |
| Licence | ODbL (© OpenStreetMap contributors) |
| Export date | 2026-11-20 |
| Features | 1, inside the Olomouc boundary |
| Geometry | Point (1) |
| Used by the app | No |

## Properties
| Key | Value |
|---|---|
| `@id` | `node/12272992596` |
| `leisure` | `sports_hall` |
| `name` | `TJ Sokol` |

## Notes
- **Almost empty.** Sports halls in OSM are usually mapped as buildings (ways) or as `leisure=sports_centre`, and this export apparently kept only nodes tagged `sports_hall`. Re-export with `nwr` and consider `leisure=sports_centre` before using it.
