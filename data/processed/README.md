# Raw Data — Jaipur SAR-Based Urban Expansion Analysis

## 1. Overview

This directory stores the original source datasets used in the Jaipur SAR-Based Urban Expansion Analysis.

It contains:

1. Original Sentinel-1A SAR satellite products in SAFE format.
2. Original OpenStreetMap (OSM) reference data in GeoPackage format.

The Sentinel-1 products provide the primary radar observations for multi-temporal analysis, while the OSM dataset provides contemporary geographic reference information for spatial comparison.

Original source datasets are retained separately from derived processing outputs to support reproducibility and data integrity.

**Satellite mission:** Sentinel-1A  
**Sensor:** C-band Synthetic Aperture Radar  
**Acquisition mode:** Interferometric Wide Swath (IW)  
**Product type:** Ground Range Detected (GRD)  
**Polarizations:** VV and VH  
**Acquisition years:** 2016, 2020 and 2025

---

## 2. Sentinel-1 Source Data

Three Sentinel-1A acquisitions are used in this project.

### 2.1 2016 Acquisition

**Product:**

`S1A_IW_GRDH_1SDV_20160302T005217_20160302T005242_010183_00F074_C380.SAFE`

- Acquisition date: 02 March 2016
- Satellite: Sentinel-1A
- Acquisition mode: IW
- Product type: GRDH
- Polarizations: VV and VH
- Relative orbit: 136
- Orbit direction: Descending

### 2.2 2020 Acquisition

**Product:**

`S1A_IW_GRDH_1SDV_20200305T005233_20200305T005258_031533_03A1F5_7036.SAFE`

- Acquisition date: 05 March 2020
- Satellite: Sentinel-1A
- Acquisition mode: IW
- Product type: GRDH
- Polarizations: VV and VH
- Relative orbit: 136
- Orbit direction: Descending

### 2.3 2025 Acquisition

**Product:**

`S1A_IW_GRDH_1SDV_20250303T005248_20250303T005313_058133_072E2C_6B0E.SAFE`

- Acquisition date: 03 March 2025
- Satellite: Sentinel-1A
- Acquisition mode: IW
- Product type: GRDH
- Polarizations: VV and VH
- Relative orbit: 136
- Orbit direction: Descending

The acquisitions were selected from a similar seasonal period in March to support multi-temporal comparison.

---

## 3. OpenStreetMap Reference Data

The raw directory also contains the original OSM reference dataset used for the project's geographic reference and spatial-comparison analysis.

**Dataset filename:**

`Jaipur_India_Rajasthan_Reference.gpkg`

**Format:** GeoPackage (`.gpkg`)

**Purpose:**

- Provide geographic reference features for Jaipur and its surrounding region.
- Support building-footprint and land-use investigations.
- Provide input for spatial clipping to the project study area.
- Support exploratory comparison between SAR change candidates and current mapped building features.

**Recorded dataset statistics:**

| Metric | Value |
|---|---:|
| Original records | 145,169 |
| Number of source layers | 10 |
| File size | Approximately 56.62 MB |

The original GeoPackage is retained in `data/raw/`. A spatially clipped version is stored separately under `data/processed/OSM_Jaipur_Clipped_Reference.gpkg`.

### Important limitation

OpenStreetMap represents geographic features mapped at the time of data extraction. It does not provide historical building footprints for all three Sentinel-1 acquisition years.

Therefore, this dataset is used as contemporary reference information and must not be treated as historical ground truth for validating urban expansion between 2016 and 2025.

OSM-derived data require appropriate attribution and compliance with the Open Database License (ODbL).

---

## 4. Directory Structure

The raw data directory is organised as follows:

```text
raw/
│
├── README.md
│
├── Jaipur_India_Rajasthan_Reference.gpkg
│
├── S1A_IW_GRDH_1SDV_20160302T005217_005242_010183_00F074_C380.SAFE/
│   ├── manifest.safe
│   ├── annotation/
│   ├── measurement/
│   ├── preview/
│   └── other SAFE metadata files
│
├── S1A_IW_GRDH_1SDV_20200305T005233_005258_031533_03A1F5_7036.SAFE/
│   └── Sentinel-1 SAFE product contents
│
└── S1A_IW_GRDH_1SDV_20250303T005248_005313_058133_072E2C_6B0E.SAFE/
    └── Sentinel-1 SAFE product contents
```

Each SAFE directory contains additional annotation, measurement, calibration, noise and metadata files.

The structure shown above is illustrative; the complete original SAFE directory contents must be preserved.

---

## 5. Sentinel-1 SAFE Product Structure

A Sentinel-1 SAFE product is a structured directory containing radar measurements and supporting metadata.

Important components include:

| Component | Purpose |
|---|---|
| `manifest.safe` | Main product manifest and metadata |
| `annotation/` | Image annotations and acquisition information |
| `annotation/calibration/` | Radiometric calibration lookup tables |
| `annotation/calibration/noise/` or associated noise metadata | Noise information, depending on product structure |
| `measurement/` | Actual SAR measurement data |
| `preview/` | Browse images and previews |

The measurement data contain the original radar observations. Annotation and calibration information support the interpretation and processing of those observations.

The complete SAFE structure should remain intact.

---

## 6. Data Handling and Preservation

The following rules apply to the raw source datasets:

1. Preserve all original Sentinel-1 SAFE products.
2. Do not manually delete or modify individual files inside SAFE directories.
3. Preserve `manifest.safe`, annotation, measurement, calibration, noise and other supporting metadata.
4. Do not overwrite original raw datasets during processing.
5. Perform SAR preprocessing using SNAP and save derived outputs under `data/processed/`.
6. Preserve the original OSM GeoPackage separately from its clipped derivative.
7. Keep source-data documentation and attribution information.
8. Verify that SAFE products have been completely extracted before opening them in SNAP.

For SNAP, open the Sentinel-1 product using its `manifest.safe` file or the extracted SAFE product directory.

The raw directory should be treated as read-only source data.

---

## 7. Processing Relationship

The raw Sentinel-1 products are used as inputs for the following preprocessing workflow:

```text
Original Sentinel-1 SAFE Product
              |
              v
       Apply Orbit File
              |
              v
     Radiometric Calibration
              |
              v
       Lee Sigma Filtering
              |
              v
 Range-Doppler Terrain Correction
              |
              v
     Geographic Subsetting
              |
              v
       VV and VH Export
              |
              v
      Processed GeoTIFFs
              |
              v
       Raster Alignment
              |
              v
      SAR Feature Analysis
              |
              v
       Change Detection
              |
              v
      Spatial Clustering
```

The original OSM reference dataset follows a separate workflow:

```text
Original OSM GeoPackage
          |
          v
     Data Audit
          |
          v
   Spatial Clipping
          |
          v
  Geometry Validation
          |
          v
  Tag and Coverage Analysis
          |
          v
 SAR Candidate Comparison
```

All derived datasets are stored separately under:

`data/processed/`

---

## 8. Data Integrity and Reproducibility

The raw datasets serve as the original source inputs for the research.

Retaining them makes it possible to:

- Reproduce the Sentinel-1 preprocessing workflow.
- Reapply different calibration and filtering parameters.
- Verify acquisition metadata and radar geometry.
- Investigate processing errors.
- Generate additional SAR-derived datasets.
- Reprocess the OSM reference data using different spatial extents.
- Verify the provenance of derived spatial-analysis products.

The original SAFE products and OSM GeoPackage should therefore remain unchanged throughout the project.

For stronger reproducibility, file checksums such as SHA-256 can be generated and recorded in a separate data-integrity manifest.

---

## 9. Storage and GitHub Management

The raw directory contains large source datasets that should not normally be uploaded directly to a standard GitHub repository.

The following files should remain in local or appropriate external storage:

- Three original Sentinel-1 SAFE products.
- Original OSM GeoPackage.

The GitHub repository should retain:

- This README.
- Data-source and acquisition information.
- Processing and analysis scripts.
- Relevant data-retrieval instructions.
- Appropriate source attribution and licensing information.

Large source datasets should be excluded through `.gitignore` or managed through a suitable external data-storage solution.

---

## 10. Data Sources and Attribution

**Satellite data:** Copernicus Sentinel-1 mission, Sentinel-1A.

**Processing software:** European Space Agency (ESA), SNAP 14.

**Geographic reference data:** OpenStreetMap contributors.

OSM data are distributed under the Open Database License (ODbL). Appropriate attribution and licence compliance are required when using and redistributing derived OSM data.

The precise download source, extraction date and any additional source-specific metadata should be recorded in the project's data provenance documentation.

---

**Project:** Jaipur SAR-Based Urban Expansion Analysis  
**Satellite:** Sentinel-1A  
**Product type:** GRD  
**Acquisition years:** 2016, 2020 and 2025  
**Polarizations:** VV and VH  
**Reference dataset:** OpenStreetMap GeoPackage  
**Processing software:** ESA SNAP 14
