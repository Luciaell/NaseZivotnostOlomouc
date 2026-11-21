# zakladni_skola.geojson: primary schools

| | |
|---|---|
| File | [datasets/zakladni_skola.geojson](../datasets/zakladni_skola.geojson) |
| Source | Open data of the Olomouc Region. Layer name in the file: `VZDE_zakladni_skoly` |
| Source URL | TODO |
| Licence | TODO |
| Export date | TODO (not recorded in the file) |
| Features | 437 for the whole region, of which **57** are inside the Olomouc boundary (51 after duplicates are removed) |
| Geometry | Point (437) |
| Coordinates | WGS 84 lon/lat (`crs` = `urn:ogc:def:crs:OGC:1.3:CRS84`) |
| Used by the app | Yes: `CATEGORIES["schools"]`, fallback name `ZŠ (bez názvu)` |

## Content
One row per **school facility at one site** from the Czech school register (rejstřík škol). A school organisation can have several facilities and sites, and the same site can appear once per school type.

## Properties
All keys are UPPERCASE. Numbers in brackets are how many of the 437 features have a value.

| Key | Meaning |
|---|---|
| `OBJECTID` (437) | Row ID in the source layer |
| `ID_MISTA` (437) | ID of the site where teaching takes place |
| `FK_IZO` (437) | IZO, the register ID of the school facility |
| `FK_RED_IZO` (437) | RED IZO, the register ID of the whole school organisation |
| `ZAR_DRUH_KOD`, `ZAR_DRUH_NAZEV` (437) | Facility kind. Always `B` / `základní vzdělávání` |
| `ZAR_TYP_KOD`, `ZAR_TYP_NAZEV` (437) | Facility type, e.g. `Základní škola`, `Základní škola speciální`, `Základní škola praktická`, school in a hospital |
| `ZAR_KAPACITA` (437) | Capacity (number of pupils) |
| `ADRESA`, `ADRESA1`–`ADRESA3` | Site address, whole and split into lines |
| `ULICE` (269), `CP` (437), `CO_CISLO` (163), `CO_PISMENO` | Street, conscription number, orientation number and its letter |
| `CAST_OBCE`, `OBEC`, `PSC` (437) | Part of the municipality, municipality, postcode |
| `ADR_MISTO_KOD` (437) | RÚIAN address point code |
| `ORG_NAZEV` (437) | **Name of the school organisation**, e.g. `Základní škola Olomouc, tř. Spojenců 8, příspěvková organizace` |
| `ORG_ICO` (437) | Company ID (IČO) of the organisation |
| `ORG_PRAVNI_FORMA` (437) | Legal form, e.g. `Příspěvková organizace` |
| `ORG_ADRESA` (437) | Address of the organisation's seat |
| `ORG_WEB` (432), `ORG_TELEFON` (426), `ORG_IDDS` (138) | Website, phone, data box ID |
| `ORG_ZRIZ_TYP`, `ORG_ZRIZ_NAZEV` (437) | Founder type (`Obec`, `Kraj`, `Církev`, `Privátní sektor`, `Státní správa ve školství`) and name |
| `ORG_KOD_OK` (54) | Unclear: a numeric code (e.g. `1040`) present on only 54 rows |

## How the app uses it
- The name is `ORG_NAZEV` (via `NAME_KEYS`). Every row has one, so the fallback is not used.
- The file has no OSM ID, so `osm_id` is `None` in results.
- Rows with the same `ORG_NAZEV` at the same point are loaded once. In Olomouc this reduces 57 rows to 51, e.g. `Základní škola a Střední škola CREDO` appeared 3 times.

## Notes
- `ORG_NAZEV` is the organisation name, which is often long and may include a kindergarten or secondary school (`Základní škola a Mateřská škola …`).
- The same organisation can appear at different sites (e.g. the Montessori school at 646 m and 913 m from Horní náměstí). These are real separate sites and are kept.
- Special-needs, practical and hospital schools are included. Filter by `ZAR_TYP_NAZEV` if only mainstream schools should count.
- This file replaced the deleted OSM export `primary_school.geojson`.
