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

## Architecture

| File | Role |
|---|---|
| [front_end.py](front_end.py) | Streamlit UI: address search box, Folium map, list of results |
| [back_end.py](back_end.py) | Backend: loads GeoJSON datasets and finds amenities within a radius of a point |
| [datasets/](datasets/) | OpenStreetMap GeoJSON exports (Overpass Turbo) and the Olomouc city boundary |

### front_end.py
- **Address autocomplete**: `fetch_addresses()` queries the **Overpass API** for every address point in the Olomouc bounding box. If the first server fails, it tries a fallback mirror. Results are cached for 24 h. Labels use the Czech `conscription/orientation` number format (e.g. `Kateřinská 123/4`). `suggest()` matches without diacritics: results that start with the search text come first, then results that only contain it.
- **Free-text fallback**: `search_location()` uses Nominatim (geopy), bounded to the Olomouc bbox.
- **Map**: for each type in `back_end.TYPY`, it calls `najdi_instituce(coords, typ, radius_km)`. Each result gets a marker styled by `MARKER_STYLES` (Font Awesome icons). The radius circle is green when every type has at least one result, orange when one type has none, and red when two or more types have none (`circle_color`).

### back_end.py (public API)
- `TYPY`: tuple of the valid type keys: `zastavky`, `skolky`, `lekarny`, `skoly`, `supermarkety`.
- `najdi_instituce(bod, typ, radius_km=1.0)` (alias `najdi`): `bod` is `(lat, lon)`. Returns a list of `{nazev, vzdalenost_m, lat, lon, osm_id}` sorted by distance. It raises `ValueError` if the type is unknown or the point is outside Olomouc.
- `je_v_olomouci(lat, lon)`: point-in-polygon test against `olomouc_boundary.geojson`.
- Polygon features are reduced to their area centroid. For MultiPolygons, only the part with the most vertices in its outer ring is used. Geometry is treated as planar lon/lat (acceptable at city scale), and distances use `geopy.distance.geodesic`.
- Datasets are filtered to the city boundary and cached with `lru_cache`. Supermarket data covers a wider region, which is why the filter matters.
- Bus stop platforms with the same name are merged into one result, keeping the nearest platform (`_sluc_nastupiste`).
- If a feature has no `name`, the result uses its `brand`, and failing that a fallback name such as `"Lékárna (bez názvu)"`.

## Adding a new amenity type
1. Export the data from Overpass Turbo as GeoJSON and save it in `datasets/`.
2. Add an entry to `KATEGORIE` in [back_end.py](back_end.py): `"key": ("file.geojson", "Fallback name (bez názvu)")`.
3. Add a marker style to `MARKER_STYLES` in [front_end.py](front_end.py). Otherwise the markers are gray.

Some datasets are already downloaded but not wired in yet: `divadlo` (theatres), `kino` (cinemas), `gym`, `sportovni_hala` (sports halls) and `restaurace_hospody_bary_cluby` (restaurants, pubs, bars and clubs).

## Known issues / gotchas
- **back_end.py runs code when imported.** The pharmacy-printing loop at the bottom of the file is outside the `if __name__ == "__main__":` block, so it prints to the console every time the Streamlit app imports the module.
- **front_end.py crashes when a search finds nothing.** If the location is not found, the code still calls `draw_circle(...)` with `coords=None`, and `results` is undefined at that point, so a `NameError` follows the error message.
- `najdi_instituce` raises `ValueError` for addresses outside the city boundary, and the frontend does not catch it.
- `__pycache__/` is committed to git and should be added to `.gitignore`.
- External services (Nominatim, Overpass) have rate limits, so keep `st.cache_data` on any function that calls them.
