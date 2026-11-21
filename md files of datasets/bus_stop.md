# bus_stop.geojson: bus stops

| | |
|---|---|
| File | [datasets/bus_stop.geojson](../datasets/bus_stop.geojson) |
| Source | OpenStreetMap, exported with Overpass Turbo |
| Overpass query | TODO. Inferred from the data: `highway=bus_stop` + `public_transport=platform` |
| Licence | ODbL (© OpenStreetMap contributors) |
| Export date | 2026-11-18 |
| Features | 189, all inside the Olomouc boundary |
| Geometry | Point (189) |
| Used by the app | Yes: `CATEGORIES["bus_stops"]`, fallback name `Zastávka (bez názvu)` |

## Content
Each feature is one **platform** (one side of the road), not one stop. The 189 platforms have 90 distinct names. All features have `bus=yes`.

## Properties
Numbers in brackets are how many of the 189 features have a value.

| Key | Meaning |
|---|---|
| `@id` (189) | OSM ID, e.g. `node/25756448`. Also in the feature's `id` field |
| `name` (188) | Stop name, e.g. `Fibichova`. One platform has no name |
| `highway`, `public_transport`, `bus` (189) | Always `bus_stop`, `platform` and `yes` |
| `shelter` (168), `bench` (154), `bin` (151), `lit` (125) | Platform equipment (`yes`/`no`) |
| `tactile_paving` (138) | Tactile paving for blind people |
| `departures_board` (45) | `timetable` (40) or `realtime` (5) |
| `network`, `network:short`, `network:wikidata` (≈58) | Transport network: `Integrovaný dopravní systém Olomouckého kraje` (56), plus one `Flixbus` and one `RegioJet` platform |
| `local_ref` (45) | Platform letter or number within a stop |
| `official_name` (18), `operator*` (≈14) | Official name, operator |
| Others (1–2 each) | `ref`, `route_ref`, `source`, `start_date`, `description`, check dates |

## How the app uses it
- The name is `name`. The one unnamed platform shows the fallback name.
- `_merge_platforms` merges platforms that share a name into one result (the nearest one), so a stop is listed once. Unnamed platforms are never merged.

## Notes
- Some names describe a part of a stop, e.g. `Autobusové nádraží, podchod`. These count as separate stops.
- Tram stops are in a separate file ([tramvaj_zastavka.md](tramvaj_zastavka.md)) and are not included here.
