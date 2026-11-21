# CLAUDE.md

## Project overview

**Walker15** (formerly *Naše životnost Olomouc*) is a Streamlit web app that rates how livable an address in Olomouc (Czech Republic) is. The user searches for an address. The app shows it on a map with an adjustable radius (sidebar slider, 1 km by default) and lists the nearby amenities in that radius: transport, schools, shops, pharmacies and leisure.

It is a small team project, and the planned features are in [roadmap.txt](roadmap.txt). Code (identifiers, comments, docstrings, error messages) is in **English**. User-facing strings (summary lines, marker tooltips, fallback names such as `"Lékárna (bez názvu)"`) are in **Czech**.

## Running

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
streamlit run front_end.py
python back_end.py          # quick manual test of the backend (prints amenities near Horní náměstí)
```

`.env` is gitignored and loaded by VS Code (`python.terminal.useEnvFile`). `python-dotenv` is a dependency in preparation for a future LLM API key (see the roadmap). There are no tests, linter or build step.

### Secrets
- `CARTO_API_KEY` (optional) selects CARTO basemap tiles. The app reads it from `.streamlit/secrets.toml` (`CARTO_API_KEY = "..."`) and falls back to the environment variable. Without a key, the map uses plain OpenStreetMap tiles.
- `ANTHROPIC_API_KEY` (optional) enables the AI chatbot. It is read the same way as the CARTO key. Without it, the chatbot section shows an info message instead.
- Both `.env` and `.streamlit/secrets.toml` are gitignored. Never commit keys.

## Architecture

| File | Role |
|---|---|
| [front_end.py](front_end.py) | Streamlit UI: address search box, Folium map, list of results |
| [back_end.py](back_end.py) | Backend: loads GeoJSON datasets and finds amenities within a radius of a point |
| [chatbot.py](chatbot.py) | AI chatbot (Claude API): area summary and follow-up chat. **All chatbot details are in [CHATBOT.md](CHATBOT.md). Read and update it when working on the chatbot.** |
| [datasets/](datasets/) | GeoJSON datasets (see [Datasets](#datasets)) and the Olomouc city boundary |

### front_end.py
- **Settings**: constants at the top of the file: `DEFAULT_RADIUS_M` (1000) with the slider range `MIN_RADIUS_M`/`MAX_RADIUS_M`/`RADIUS_STEP_M` (200–2000 m, step 100), `DEFAULT_CENTER`, `DEFAULT_ZOOM` (12.5, start view). After choosing an address, `fit_radius` zooms the map so the whole radius circle is visible.
- **Radius**: chosen with the "Okruh hledání" slider in the sidebar (`settings()` returns it). There is no global radius constant: every function that needs it takes a `radius` argument (search, circle, distance colours, score, metric cards, chatbot). Changing the radius starts a new chat conversation. The `KINDS` dict holds each type's Czech label, marker colour and Font Awesome icon.
- **Address autocomplete**: `fetch_addresses()` queries the **Overpass API** for every address point in the Olomouc bounding box. If the first server fails, it tries a fallback mirror. Results are cached for 24 h. Labels use the Czech `conscription/orientation` number format (e.g. `Kateřinská 123/4`). `suggest()` matches without diacritics: results that start with the search text come first, then results that only contain it.
- **Free-text fallback**: `search_location()` uses Nominatim (geopy), bounded to the Olomouc bbox.
- **Map tiles**: `make_map(coords, zoom, style)` builds the Folium map. With a CARTO key (`get_carto_key()`), it uses CARTO raster tiles in one of three styles (`CARTO_STYLES`): `voyager` (default), `positron` or `dark_matter`. Without a key, it uses plain OSM tiles.
- **Heatmap layer**: the sidebar toggle "Pocitová teplotní mapa" (off by default, returned by `settings()`) adds a felt-temperature heatmap from `back_end.heat_points()` to both the start map and the results map (`show_map`, `add_heat_layer`, folium `HeatMap` plugin), with a legend caption under the map. Look and feel: `HEAT_GRADIENT`, `HEAT_RADIUS`, `HEAT_BLUR`, `HEAT_MAX_ZOOM`. Map only: it does not affect the score or the chatbot.
- **Results** (`show_results`): an address outside the city boundary gets an error message instead. For each type in `back_end.TYPES`, the app calls `back_end.find_institutions(coords, kind, radius / 1000)` and adds one marker per result. `draw_selected_location` draws the radius circle and a house marker. The circle is green when every type has at least one result, orange when one type has none, and red when two or more types have none (`circle_color`).
- **Nearest-amenity summary** (`summary_line`): next to the map, one coloured line per type shows the nearest result, e.g. `Nejbližší lékárna: … (120 m)`. It uses Streamlit's `:color[...]` markdown. `dist_color()` colours the line green under 300 m, orange under 500 m and red otherwise. A type with no results gets a red line saying none are within the radius.

### back_end.py (public API)
- `TYPES`: tuple of the valid type keys: `bus_stops`, `kindergartens`, `pharmacies`, `schools`, `supermarkets`.
- `find_institutions(point, kind, radius_km=1.0)` (alias `find`): `point` is `(lat, lon)`. Returns a list of `{name, distance_m, lat, lon, osm_id}` sorted by distance. It raises `ValueError` if the type is unknown or the point is outside Olomouc.
- `is_in_olomouc(lat, lon)`: point-in-polygon test against `olomouc_boundary.geojson`.
- `heat_points()`: the felt-temperature survey as a cached tuple of `(lat, lon, weight)`, weight 0–1 (hot = 1). Weights are in `HEAT_WEIGHTS` / `HEAT_FALLBACK`; oversized polygons (`MAX_HEAT_AREA_M2`) and answers outside Olomouc are dropped.
- Polygon features are reduced to their area centroid. For MultiPolygons, only the part with the most vertices in its outer ring is used. Geometry is treated as planar lon/lat (acceptable at city scale), and distances use `geopy.distance.geodesic`.
- Datasets are filtered to the city boundary and cached with `lru_cache`. Supermarket and school data cover a wider region, which is why the filter matters.
- Features with the same name at the same point are loaded only once, because the regional school data lists a school once per school type.
- Bus stop platforms with the same name are merged into one result, keeping the nearest platform (`_merge_platforms`).
- The name comes from the first key in `NAME_KEYS` (`name`, `NAZEV`, `ORG_NAZEV`) that is set. Failing that, the result uses `brand`, and then a fallback name such as `"Lékárna (bez názvu)"`.

## Datasets

This file is the documentation of the whole project. Each dataset has its own detailed page in [md files of datasets/](md%20files%20of%20datasets/), named after the GeoJSON file (e.g. `bus_stop.geojson` → `bus_stop.md`). A page covers the source, export date, feature counts, every property key and its meaning, and known quirks. Read the page before using a dataset.

There are two kinds of source:
- **OpenStreetMap exports from Overpass Turbo.** Names are in `properties.name` (sometimes `brand`), and features can be Points or Polygons.
- **Open data from the Olomouc Region (`zakladni_skola`, `knihovna`).** Property keys are UPPERCASE and every feature is a Point. They have no `name` key: school names are in `ORG_NAZEV` and library names in `NAZEV`. There is no OSM ID, so `osm_id` is `None`. Both files cover the whole region, so the city-boundary filter matters.

| File | Content | Source | Used by `CATEGORIES` |
|---|---|---|---|
| `bus_stop` | bus stops | OSM | `bus_stops` |
| `kindergarten` | kindergartens | OSM | `kindergartens` |
| `pharmacy` | pharmacies | OSM | `pharmacies` |
| `supermarket` | supermarkets | OSM | `supermarkets` |
| `zakladni_skola` | primary schools | region | `schools` |
| `tramvaj_zastavka` | tram stops | OSM | no |
| `vlak_zastavka` | train stations and halts | OSM | no |
| `knihovna` | public libraries | region | no |
| `nabozenska_budova` | churches and chapels | OSM | no |
| `divadlo`, `kino` | theatres, cinemas | OSM | no |
| `gym`, `sportovni_hala` | gyms, sports halls | OSM | no |
| `restaurace_hospody_bary_cluby` | restaurants, pubs, bars, clubs | OSM | no |
| `olomouc_boundary` | city boundary polygon | OSM/Nominatim | used by `is_in_olomouc` |
| `pocitova-teplotni-mapa-olomouce-2` | felt-temperature survey 2020 (personal data removed) | city survey | used by `heat_points` (heatmap layer) |

## Adding a new amenity type
1. Save the GeoJSON in `datasets/`.
2. Add an entry to `CATEGORIES` in [back_end.py](back_end.py): `"key": ("file.geojson", "Fallback name (bez názvu)")`.
3. If the dataset stores names under a key missing from `NAME_KEYS`, add it there. Otherwise every result gets the fallback name.
4. Add a label and marker style to `KINDS` in [front_end.py](front_end.py). Otherwise the markers are gray and the summary shows the raw key.

## Known issues / gotchas
- `__pycache__/` is committed to git and should be added to `.gitignore`.
- External services (Nominatim, Overpass) have rate limits, so keep `st.cache_data` on any function that calls them.
- A running Streamlit server can keep an old copy of `back_end` after it is edited (for example, after renames). If the app reports a missing attribute, restart `streamlit run`.
