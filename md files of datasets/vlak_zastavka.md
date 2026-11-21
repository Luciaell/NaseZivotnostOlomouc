# vlak_zastavka.geojson: train stations and halts

| | |
|---|---|
| File | [datasets/vlak_zastavka.geojson](../datasets/vlak_zastavka.geojson) |
| Source | OpenStreetMap, exported with Overpass Turbo |
| Overpass query | TODO. Inferred from the data: `railway=station`, `railway=halt` and `railway=stop` |
| Licence | ODbL (© OpenStreetMap contributors) |
| Export date | 2026-11-20 |
| Features | 11, all inside the Olomouc boundary |
| Geometry | Point (11) |
| Used by the app | No |

## Content
| `railway` | Count | Meaning |
|---|---|---|
| `station` | 3 | Station with tracks to switch, e.g. `Olomouc hlavní nádraží` |
| `halt` | 5 | Simple halt, e.g. `Olomouc-Řepčín` |
| `stop` | 3 | Stop position on the track (`public_transport=stop_position`) |

## Properties
Numbers in brackets are how many of the 11 features have a value.

| Key | Meaning |
|---|---|
| `@id` (11) | OSM ID |
| `name` (11) | Name, e.g. `Olomouc-Smetanovy sady`, `Nemilany` |
| `operator` (11), `operator:short`, `operator:wikidata` (5) | Operator: `Správa železnic` (5) or its old name `cz:SŽDC` (6) |
| `railway` (11), `public_transport` (7), `train` (5) | Kind of feature (see the table above) |
| `railway:ref` (8), `uic_ref` (1) | Railway station code, UIC code |
| `wikidata` (8), `wikipedia` (2) | Links |
| `name:de` (6), `name:cs`, `name:pl`, `short_name` (1) | Other names |
| Others | `wheelchair`, `ele` (altitude), `platforms`, `start_date` |

## If it is added to the app
- The `stop` features probably duplicate a `station` or `halt` with the same or a similar name. Merge by name, or keep only `station` and `halt`.
- Every feature has a `name`.
