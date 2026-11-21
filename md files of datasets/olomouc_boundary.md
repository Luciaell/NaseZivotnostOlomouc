# olomouc_boundary.geojson: city boundary

| | |
|---|---|
| File | [datasets/olomouc_boundary.geojson](../datasets/olomouc_boundary.geojson) |
| Source | OpenStreetMap relation [437057](https://www.openstreetmap.org/relation/437057), exported via Nominatim |
| Licence | ODbL (© OpenStreetMap contributors) |
| Export date | 2026-11-20 |
| Features | 1 |
| Geometry | Polygon: 1 outer ring with 2554 vertices, no holes |
| Used by the app | Yes: `is_in_olomouc()` in back_end.py |

## Properties
| Key | Value |
|---|---|
| `name` | `Olomouc` |
| `boundary` | `administrative` |
| feature `id` | `relation/437057` |

## How the app uses it
- `_boundary()` loads the polygon once (cached). `is_in_olomouc(lat, lon)` runs a ray-casting point-in-polygon test on it.
- Every amenity dataset is filtered to features whose point lies inside this polygon.
- `find_institutions` raises `ValueError` for points outside it, and the frontend shows "That location is outside Olomouc." instead of results.

## Notes
- This is the administrative city, including its outlying parts (e.g. Chomoutov, Radíkov, Svatý Kopeček). It is not the whole Olomouc district.
- The backend also handles a MultiPolygon boundary, in case a future export has several parts.
