# gym.geojson: gyms and fitness centres

| | |
|---|---|
| File | [datasets/gym.geojson](../datasets/gym.geojson) |
| Source | OpenStreetMap, exported with Overpass Turbo |
| Overpass query | TODO. Inferred from the data: `leisure=fitness_centre` |
| Licence | ODbL (© OpenStreetMap contributors) |
| Export date | 2026-11-20 |
| Features | 17, all inside the Olomouc boundary |
| Geometry | Point (17) |
| Used by the app | No |

## Properties
Numbers in brackets are how many of the 17 features have a value.

| Key | Meaning |
|---|---|
| `@id` (17) | OSM ID |
| `leisure` (17) | Always `fitness_centre` |
| `name` (17) | Name, e.g. `MTWO`, `TJ Sokol Nový Svět` |
| `opening_hours` (7), `website` (6), `phone` (5), `email` (3) | Opening hours and contacts |
| `sport` (4) | Sports offered, e.g. `yoga`, `fitness`, `boxing;kickboxing;martial_arts;crossfit;fitness` |
| `addr:*` (1–3) | Address |
| Others (1 each) | `alt_name`, `alt_name_1`, `operator`, `brand`, `level`, `wheelchair`, `description`, `source`, `check_date`, `contact:facebook` |

## Notes
- `fitness_centre` also covers yoga studios and other small studios (e.g. `AURA-SOMA a FENG SHUI`, `Dákiní`), not only gyms with equipment.
- Only nodes are included, so gyms mapped only as buildings would be missing.
- For sports halls see [sportovni_hala.md](sportovni_hala.md).
