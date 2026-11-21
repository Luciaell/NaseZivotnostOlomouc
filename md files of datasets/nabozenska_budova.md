# nabozenska_budova.geojson: churches and chapels

| | |
|---|---|
| File | [datasets/nabozenska_budova.geojson](../datasets/nabozenska_budova.geojson) |
| Source | OpenStreetMap, exported with Overpass Turbo |
| Overpass query | TODO. Inferred from the data: mostly `amenity=place_of_worship` |
| Licence | ODbL (© OpenStreetMap contributors) |
| Export date | 2026-11-20 |
| Features | 8, all inside the Olomouc boundary |
| Geometry | Point (8) |
| Used by the app | No |

## Content
| `amenity` | Count |
|---|---|
| `place_of_worship` | 7 |
| `community_centre` | 1 (the Church of Jesus Christ of Latter-day Saints) |

Religion: `christian` (7), not set (1). Denomination: `catholic` (2), `roman_catholic` (2), `mormon` (1), not set (3).

## Properties
Numbers in brackets are how many of the 8 features have a value.

| Key | Meaning |
|---|---|
| `@id` (8) | OSM ID |
| `amenity` (8) | See the table above |
| `name` (6) | `Kaplička`, `Kaple Božího těla`, `Kaple sv. Barbory`, `Nemocniční kaple`, `Církev Ježíše Krista Svatých posledních dnů`, `poustevna` |
| `religion` (7), `denomination` (5) | Religion and denomination |
| `building` (5), `historic` (2) | Building type, historic flag |
| `description` (3), `note` (1) | Free text |
| Others (1–2 each) | `website`, `url`, `wikidata`, `wikipedia`, `wikimedia_commons`, `opening_hours`, address, `operator`, `check_date` |

## Notes
- **Incomplete.** Only 8 features, all of them chapels or small congregations. Olomouc's large churches (e.g. St. Wenceslas Cathedral, St. Moritz) are missing, probably because they are mapped as ways or relations and the export kept only nodes. Re-export with `nwr` before using it.
- 2 features have no `name`. A fallback name would be needed, e.g. `Kostel (bez názvu)`.
