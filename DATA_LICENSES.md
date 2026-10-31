# Data sources, licences and attribution

This repository contains original analysis code and documentation alongside references to third-party geospatial datasets. The repository's software licence does **not** replace or override the licences that apply to those datasets.

## 1. Sentinel-1 satellite data

The analysis uses Sentinel-1A Level-1 IW GRDH dual-polarisation (VV/VH) products obtained through the Copernicus data access ecosystem.

Copernicus Sentinel data are made available on a free, full and open basis, subject to the applicable legal notice and terms. Users should retain source identification and check the current legal notice when redistributing data or derived products.

Suggested attribution:

> Contains modified Copernicus Sentinel-1 data (2016, 2020 and 2025).

Official information:
- Sentinel data legal notice: https://cds.climate.copernicus.eu/licences/ec-sentinel
- Copernicus Data Space terms: https://dataspace.copernicus.eu/terms-and-conditions

The original `.SAFE` products are not included in this Git repository because of their size. See `data/raw/README.md` for product identifiers and acquisition details.

## 2. OpenStreetMap data

OpenStreetMap data are licensed under the Open Data Commons Open Database License (ODbL) 1.0.

Required attribution:

> © OpenStreetMap contributors

Licence and attribution information:
- https://www.openstreetmap.org/copyright
- https://opendatacommons.org/licenses/odbl/

The project uses OpenStreetMap data as a contemporary reference layer for spatial comparison. OSM building footprints must not be interpreted as a complete or historically accurate record of buildings for 2016, 2020 or 2025.

If OSM data or an adapted OSM database are redistributed, review the ODbL share-alike requirements. Do not assume that every analytical output automatically has the same licensing status; the treatment depends on whether the item is a produced work or a derivative database.

## 3. Jaipur municipal boundary

The project uses a Jaipur municipal boundary dataset sourced from OpenCity/BharatAtlas, described in the project records as containing 150 municipal ward polygons.

Before redistributing the boundary GeoJSON or any adapted boundary dataset, verify the licence and attribution terms on the exact source page or download record. Do not assume that the software licence in this repository applies to this dataset.

Record the following in the boundary data documentation:
- Exact source page and dataset title
- Dataset publisher/provider
- Download date
- Licence stated by the provider
- Any modifications made for this analysis (including coordinate-axis correction and dissolve operations)

## 4. Project code, figures and derived data

Unless a separate notice is attached, the original source code in this repository is released under the MIT License in `LICENSE`.

The MIT License does not automatically apply to:
- Sentinel-1 source products
- OpenStreetMap data or adapted OSM databases
- Third-party municipal boundary data
- Third-party software, libraries, basemaps or reference material

Project-generated figures and analytical outputs should retain appropriate source attribution wherever third-party data contribute to them. Consult the relevant data licence before redistributing data products.

## 5. Software dependencies

Python packages are distributed under their respective licences. See each package's official project page for its licence and terms. SNAP/ESA software is a separate dependency and is not included in `requirements.txt`.
