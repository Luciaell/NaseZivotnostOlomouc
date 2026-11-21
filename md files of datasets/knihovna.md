# knihovna.geojson: public libraries

| | |
|---|---|
| File | [datasets/knihovna.geojson](../datasets/knihovna.geojson) |
| Source | Open data of the Olomouc Region. Layer name in the file: `KUCR_verejne_knihovny_OK` |
| Source URL | TODO |
| Licence | TODO |
| Data date | `Aktualizace` values are mostly from early 2025 (e.g. 2025-01-31, 2025-03-10) |
| Features | 467 for the whole region, of which **8** are inside the Olomouc boundary |
| Geometry | Point (467) |
| Coordinates | WGS 84 lon/lat (`crs` = `urn:ogc:def:crs:OGC:1.3:CRS84`) |
| Used by the app | No |

## Content
Libraries registered with the Ministry of Culture in the five districts of the region (Olomouc 126, Přerov 126, Prostějov 108, Šumperk 84, Jeseník 23).

The 8 libraries inside the city:

| `NAZEV` | `ZARAZENI` |
|---|---|
| Knihovna města Olomouce | profesionální |
| Vědecká knihovna v Olomouci | profesionální |
| Místní knihovna Nedvězí | neprofesionální |
| Místní knihovna Slavonín | neprofesionální |
| Místní knihovna Chomoutov | neprofesionální |
| Místní knihovna Droždín | neprofesionální |
| Místní knihovna Svatý Kopeček | neprofesionální |
| Místní knihovna Radíkov | neprofesionální |

## Properties
All keys are UPPERCASE except `Aktualizace`. Numbers in brackets are how many of the 467 features have a value.

| Key | Meaning |
|---|---|
| `OBJECTID`, `ID` (467) | Row IDs in the source layer |
| `EVIDENCNI_CISLO` (439) | Registration number at the Ministry of Culture |
| `SIGLA` (428) | Library sigla (standard library code) |
| `NAZEV` (467) | **Library name** |
| `ZARAZENI` (467) | `profesionální` (professional staff) or `neprofesionální` (volunteer-run village library) |
| `STREDISKO` (359) | Regional centre library that services it |
| `POBOCKA_KNIHOVNY` (77) | Parent library if this is a branch |
| `UMISTENI_POPIS` (13) | Where in the building the library is |
| `ADRESA` (467), `ADRESNI_MISTO_KOD` (463) | Address, RÚIAN address point code |
| `OBEC`, `OBEC_KOD`, `CAST_OBCE`, `ORP`, `OKRES` (467) | Municipality and its code, part, administrative district (ORP), district |
| `ZRIZOVATEL` (467), `ZRIZOVATEL_WEB` / `_TELEFON` / `_EMAIL` (≈460) | Founder and its contacts |
| `WEB` (466) | Library website |
| `PROVOZNI_DOBA` (466) | Opening hours as free text, e.g. `PÁ 18.00-20.00 hod.` |
| `REGISTRACNI_POPLATEK` (466) | Registration fee, e.g. `bez poplatku` |
| `INTERNET` (467), `POCET_PC_VEREJNOST` (463) | Internet connection, number of public computers |
| `STUDIJNI_MISTA` (461) | Number of study places |
| `KNIZNI_FOND` (460), `ROCNI_PRIRUSTEK_KF` (438) | Size of the collection, yearly additions |
| `POCET_UZIVATELU` (463), `POCET_OBYVATEL` (460) | Registered users, population of the municipality |
| `X`, `Y`, `WKT` (467) | Coordinates in a second system with negative values, most likely S-JTSK (EPSG:5514). The app should use the GeoJSON geometry instead |
| `Aktualizace` (467) | Date the row was last updated |
| `POZNAMKA` (4) | Note |

## If it is added to the app
- The name lookup already reads `NAZEV` (`NAME_KEYS`). Every row has one.
- There is no OSM ID, so `osm_id` will be `None`.
- Only 8 libraries are in the city, so most addresses will have none within 500 m.
