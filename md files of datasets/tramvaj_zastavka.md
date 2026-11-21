# tramvaj_zastavka.geojson: tram stops

| | |
|---|---|
| File | [datasets/tramvaj_zastavka.geojson](../datasets/tramvaj_zastavka.geojson) |
| Source | OpenStreetMap, exported with Overpass Turbo |
| Overpass query | TODO. Inferred from the data: `railway=tram_stop` |
| Licence | ODbL (© OpenStreetMap contributors) |
| Export date | 2026-11-20 |
| Features | 74, all inside the Olomouc boundary |
| Geometry | Point (74) |
| Used by the app | No |

## Content
Each feature is a **stop position** on the track (`public_transport=stop_position`), usually one per direction. The 74 positions have 37 distinct names.

## Properties
Numbers in brackets are how many of the 74 features have a value.

| Key | Meaning |
|---|---|
| `@id` (74) | OSM ID |
| `name` (74) | Stop name, e.g. `Hlavní nádraží` |
| `railway`, `public_transport`, `tram` (74) | Always `tram_stop`, `stop_position` and `yes` |
| `bus` (10) | `yes` where buses also stop at this position |
| `network*`, `operator*`, `local_ref` (6) | Network (`Integrovaný dopravní systém Olomouckého kraje`), operator (`Dopravní podnik města Olomouce`, short `DPMO`), platform number |
| `name:de` (3) | German name |
| Others (1–3 each) | `wheelchair`, `description`, `fixme`, `wikidata`, `bench`, `shelter` |

## If it is added to the app
- Like bus stops, positions sharing a name should be merged into one stop. The current merge only runs for `bus_stops`, so the check in `find_institutions` would need to include the new key.
- Some names also exist in [bus_stop.md](bus_stop.md) (e.g. `Autobusové nádraží, podchod`). Decide whether trams and buses are shown separately or as one "public transport" type.
- Fallback name: every feature has a `name`.
