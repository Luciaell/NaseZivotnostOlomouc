# pocitova-teplotni-mapa-olomouce-2.geojson: felt-temperature survey

| | |
|---|---|
| File | [datasets/pocitova-teplotni-mapa-olomouce-2.geojson](../datasets/pocitova-teplotni-mapa-olomouce-2.geojson) |
| Source | Olomouc city survey "Pocitová teplotní mapa Olomouce" (participatory map: residents drew places on a map and answered questions) |
| Licence | TODO: check the city's open-data licence |
| Collected | 2020-05 (2,083 answers) and 2021 (8 answers) |
| Features | 2,091 |
| Geometry | Polygon (1,423), Point (668) |
| Used by the app | Yes: felt-temperature heatmap layer (`back_end.heat_points`, toggled in the sidebar) |

## Content
Each feature is one answer to one of two questions:

| `typ_ident` | Question (`typ_nazev`) | Count |
|---|---|---|
| `a` | Where in Olomouc do you feel **un**comfortable on hot summer days? | 1,128 |
| `b` | Where in Olomouc do you feel comfortable on hot summer days? | 963 |

`typ_ident` and `typ_nazev` disagree in 11 features. The app does not rely on either when a rating (`desc_teplota`) is present.

## Properties
Numbers in brackets are how many of the 2,091 features have a value.

| Key | Meaning |
|---|---|
| `typ_ident` (2,091) | `a` = unpleasant on hot days, `b` = pleasant |
| `typ_nazev` (2,091) | Full question text |
| `desc_teplota` (1,823) | Felt temperature: `velká zima`, `zima`, `chladno`, `mírně chladno`, `neutrální`, `mírně teplo`, `teplo`, `horko`, `velmi horko` |
| `desc_aktivity[]` (1,819) | What the person does there (e.g. `chůze`, `práce`) |
| `desc_opatreni[]` (721), `desc_opatreni` (1,020) | Suggested measures against heat (list or single value) |
| `desc_frekvence` (1,686) | How often the person is there |
| `desc_straveny_cas` (1,776) | How long the person stays there |
| `datum` (2,091) | Date of the answer (`YYYY-MM-DD`) |

## Personal data removed
On 2026-11-21 the file was rewritten without personal data. Removed keys: `ip`, `user_id`, `vek`, `pohlavi`, `postava`, `povolani`, `bydliste`, `vztah`, `jak_dlouho_v_olomouci`, `startTime`, `endTime`, the time of day from `datetime` (now `datum`), and the free-text answers `desc_aktivity_jine`, `desc_opatreni_jine` and `desc_detail` (free text can contain personal details). **The original file with this data is still in the git history** (commit `e7645ac`).

## How the app uses it (`back_end.heat_points`)
- Polygons are reduced to their area centroid. Points are used as they are.
- Polygons larger than 2 km² (`MAX_HEAT_AREA_M2`) are dropped as drawing mistakes. There are 26, and one covers half a continent.
- Answers outside the Olomouc boundary are dropped.
- Weight from `desc_teplota` via `HEAT_WEIGHTS` (`velmi horko` = 1.0 down to `zima` = 0). Without a rating, `HEAT_FALLBACK` uses the question (`a` = 0.8, `b` = 0.2). Answers with weight 0 are skipped.
- Result: 2,000 weighted points.

## Notes
- This is perceived temperature from a 2020 survey, not measured temperature. Dense areas reflect where many people answered as well as how hot it feels.
- Answers cluster in the city centre, so outlying districts look cooler partly because fewer people marked them.
