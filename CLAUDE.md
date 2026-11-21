# CLAUDE.md

## Project overview

**Naše životnost Olomouc** is a Streamlit web app that rates how livable an address in Olomouc (Czech Republic) is. The user searches for an address. The app shows it on a map with a 500 m radius and lists the nearby amenities in that radius: bus stops, kindergartens, pharmacies, primary schools and supermarkets.

It is a small team project, and the planned features are in [roadmap.txt](roadmap.txt). Identifiers, user-facing strings and some comments are in **Czech**. Keep that convention when extending the backend (e.g. `nazev` = name, `vzdalenost_m` = distance in metres, `zastavky` = stops).

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
- Both `.env` and `.streamlit/secrets.toml` are gitignored. Never commit keys.

## Architecture

| File | Role |
|---|---|
| [front_end.py](front_end.py) | Streamlit UI: address search box, Folium map, list of results |
| [back_end.py](back_end.py) | Backend: loads GeoJSON datasets and finds amenities within a radius of a point |
| [datasets/](datasets/) | GeoJSON datasets (see [Datasets](#datasets)) and the Olomouc city boundary |

### front_end.py
- **Address autocomplete**: `fetch_addresses()` queries the **Overpass API** for every address point in the Olomouc bounding box. If the first server fails, it tries a fallback mirror. Results are cached for 24 h. Labels use the Czech `conscription/orientation` number format (e.g. `Kateřinská 123/4`). `suggest()` matches without diacritics: results that start with the search text come first, then results that only contain it.
- **Free-text fallback**: `search_location()` uses Nominatim (geopy), bounded to the Olomouc bbox.
- **Map tiles**: `make_map(coords, zoom, style)` builds the Folium map. With a CARTO key (`get_carto_key()`), it uses CARTO raster tiles in one of three styles: `voyager` (default), `positron` or `dark_matter`. Without a key, it uses plain OSM tiles. The start view is the city centre at zoom 12.5. A selected address opens at zoom 15.5.
- **Results**: for each type in `back_end.TYPY`, the app calls `najdi_instituce(coords, typ, radius / 1000)` and adds one marker per result, styled by `MARKER_STYLES` (Font Awesome icons). The radius circle is green when every type has at least one result, orange when one type has none, and red when two or more types have none (`circle_color`).
- **Nearest-amenity summary**: below the map, one coloured line per type shows the nearest result, e.g. `Nejbližší lekarny: … (120 m)`. It uses Streamlit's `:color[...]` markdown. `dist_color()` colours the line green under 200 m, orange under 350 m and red otherwise. A type with no results gets a red line saying none are within the radius.

### back_end.py (public API)
- `TYPY`: tuple of the valid type keys: `zastavky`, `skolky`, `lekarny`, `skoly`, `supermarkety`.
- `najdi_instituce(bod, typ, radius_km=1.0)` (alias `najdi`): `bod` is `(lat, lon)`. Returns a list of `{nazev, vzdalenost_m, lat, lon, osm_id}` sorted by distance. It raises `ValueError` if the type is unknown or the point is outside Olomouc.
- `je_v_olomouci(lat, lon)`: point-in-polygon test against `olomouc_boundary.geojson`.
- Polygon features are reduced to their area centroid. For MultiPolygons, only the part with the most vertices in its outer ring is used. Geometry is treated as planar lon/lat (acceptable at city scale), and distances use `geopy.distance.geodesic`.
- Datasets are filtered to the city boundary and cached with `lru_cache`. Supermarket data covers a wider region, which is why the filter matters.
- Bus stop platforms with the same name are merged into one result, keeping the nearest platform (`_sluc_nastupiste`).
- If a feature has no `name`, the result uses its `brand`, and failing that a fallback name such as `"Lékárna (bez názvu)"`.

## Datasets

There are two kinds of source:
- **OpenStreetMap exports from Overpass Turbo.** Names are in `properties.name` (sometimes `brand`), and features can be Points or Polygons.
- **Open data from the Olomouc Region (`zakladni_skola`, `knihovna`).** Property keys are UPPERCASE and every feature is a Point. They have no `name` key: school names are in `ORG_NAZEV` and library names in `NAZEV`. Both files cover the whole region, so the city-boundary filter matters.

| File | Content | Source | Used by `KATEGORIE` |
|---|---|---|---|
| `bus_stop` | bus stops | OSM | `zastavky` |
| `kindergarten` | kindergartens | OSM | `skolky` |
| `pharmacy` | pharmacies | OSM | `lekarny` |
| `supermarket` | supermarkets | OSM | `supermarkety` |
| `zakladni_skola` | primary schools, with names (replaces the deleted `primary_school`) | region | not yet, `skoly` still points to the deleted file |
| `tramvaj_zastavka` | tram stops | OSM | no |
| `vlak_zastavka` | train stations and halts | OSM | no |
| `knihovna` | public libraries | region | no |
| `nabozenska_budova` | churches and chapels | OSM | no |
| `divadlo`, `kino` | theatres, cinemas | OSM | no |
| `gym`, `sportovni_hala` | gyms, sports halls | OSM | no |
| `restaurace_hospody_bary_cluby` | restaurants, pubs, bars, clubs | OSM | no |
| `olomouc_boundary` | city boundary polygon | OSM/Nominatim | used by `je_v_olomouci` |

## Adding a new amenity type
1. Save the GeoJSON in `datasets/`.
2. Add an entry to `KATEGORIE` in [back_end.py](back_end.py): `"key": ("file.geojson", "Fallback name (bez názvu)")`.
3. For the regional datasets, extend the name lookup in `_nacti_kategorii` so it also reads `NAZEV` and `ORG_NAZEV`. Otherwise every result gets the fallback name.
4. Add a marker style to `MARKER_STYLES` in [front_end.py](front_end.py). Otherwise the markers are gray.

## Known issues / gotchas
- **The app does not start.** [front_end.py](front_end.py) still runs `import instituce` and uses `instituce.TYPY` / `instituce.najdi_instituce`, but the module was renamed to `back_end`. The usage docstring in `back_end.py` also still says `from instituce import`.
- **The `skoly` type is broken.** `KATEGORIE["skoly"]` points to `primary_school.geojson`, which was deleted. Loading schools raises `FileNotFoundError` until it points to `zakladni_skola.geojson` and the name lookup handles `ORG_NAZEV`.
- **back_end.py runs code when imported.** The pharmacy-printing loop at the bottom of the file is outside the `if __name__ == "__main__":` block, so it prints to the console every time the Streamlit app imports the module.
- The summary lines show raw type keys (`Nejbližší lekarny`) instead of readable Czech labels.
- `najdi_instituce` raises `ValueError` for addresses outside the city boundary, and the frontend does not catch it.
- `__pycache__/` is committed to git and should be added to `.gitignore`.
- External services (Nominatim, Overpass) have rate limits, so keep `st.cache_data` on any function that calls them.
