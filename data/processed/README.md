# Processed Data — Jaipur SAR-Based Urban Expansion Analysis

## 1. Overview

This directory contains the processed Sentinel-1 SAR datasets and derived spatial-analysis products used in the Jaipur SAR-Based Urban Expansion Analysis.

The study uses three Sentinel-1A IW GRDH dual-polarization acquisitions:

- 2016 — 2 March 2016
- 2020 — 5 March 2020
- 2025 — 3 March 2025

The processing workflow converts the original Sentinel-1 observations into calibrated, speckle-filtered, terrain-corrected and spatially aligned VV/VH datasets. These datasets are subsequently used for temporal backscatter analysis, SAR feature engineering, change detection, spatial clustering and comparison with OpenStreetMap reference data.

**Primary processing software:** ESA SNAP 14  
**Analysis environment:** Python 3  
**GIS software:** QGIS  
**Primary coordinate reference system for aligned analysis:** WGS 84 / UTM Zone 43N (EPSG:32643)

The directory contains both intermediate processing outputs and final derived analysis products.

> **Research interpretation:** SAR backscatter changes are used to identify candidate surface changes. These products do not independently establish a validated built-up classification or prove urban expansion.

---

## 2. Sentinel-1 Source Products

The original Sentinel-1 SAFE products are stored separately under `data/raw/`.

| Year | Sentinel-1 product |
|---|---|
| 2016 | `S1A_IW_GRDH_1SDV_20160302T005217_20160302T005242_010183_00F074_C380.SAFE` |
| 2020 | `S1A_IW_GRDH_1SDV_20200305T005233_20200305T005258_031533_03A1F5_7036.SAFE` |
| 2025 | `S1A_IW_GRDH_1SDV_20250303T005248_20250303T005313_058133_072E2C_6B0E.SAFE` |

All three acquisitions use Sentinel-1A IW GRDH dual-polarization data.

- Polarization 1: VV
- Polarization 2: VH
- Relative orbit: 136
- Orbit direction: Descending

The acquisitions were selected from a similar seasonal period in March to support multi-temporal comparison.

---

## 3. SAR Preprocessing Methodology

The intended SNAP preprocessing sequence for each acquisition is:

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
       GeoTIFF Outputs
              |
              v
     Single-band Extraction
              |
              v
       Raster Alignment
              |
              v
       SAR Feature Analysis
              |
              v
        Change Detection
```

### 3.1 Orbit Correction

**SNAP operator:** Apply Orbit File

Orbit information is updated using available orbit files.

### 3.2 Radiometric Calibration

**SNAP operator:** Calibration

The VV and VH polarization channels are calibrated to Sigma0 backscatter.

Expected calibrated bands:

- `Sigma0_VV`
- `Sigma0_VH`

### 3.3 Speckle Filtering

**SNAP operator:** Single Product Speckle Filter

The Lee Sigma filter was used.

Recorded parameters for the 2016 processing:

| Parameter | Value |
|---|---|
| Filter | Lee Sigma |
| Number of Looks | 1 |
| Window Size | 7 × 7 |
| Sigma | 0.9 |
| Target Window Size | 3 × 3 |

The same settings were intended for the other acquisition years. Their exact parameter consistency should not be considered independently verified without the corresponding saved processing records.

### 3.4 Terrain Correction

**SNAP operator:** Range-Doppler Terrain Correction

The terrain-correction stage addresses geometric distortions and georeferences the imagery.

Intended output settings:

- Projection: EPSG:32643
- Pixel spacing: approximately 10 m

### 3.5 Geographic Subsetting

A rectangular geographic subset was used to reduce the original Sentinel-1 scene to the Jaipur study region.

| Boundary | Coordinate |
|---|---:|
| North | 27.05° N |
| South | 26.75° N |
| West | 75.65° E |
| East | 76.05° E |

These bounds describe a rectangular study window, not an exact municipal boundary mask.

### 3.6 GeoTIFF Export

Separate VV and VH terrain-corrected GeoTIFF files were exported for each acquisition year.

Naming convention:

- `Jaipur_S1_YEAR_VV_TC.tif`
- `Jaipur_S1_YEAR_VH_TC.tif`

---

## 4. Directory Structure

The processed directory is organised into the following components:

```text
processed/
│
├── README.md
│
├── Jaipur_S1_2016_VV_TC.tif
├── Jaipur_S1_2016_VH_TC.tif
├── Jaipur_S1_2020_VV_TC.tif
├── Jaipur_S1_2020_VH_TC.tif
├── Jaipur_S1_2025_VV_TC.tif
├── Jaipur_S1_2025_VH_TC.tif
│
├── Jaipur_S1_2016_VV_singleband.tif
├── Jaipur_S1_2016_VH_singleband.tif
├── Jaipur_S1_2020_VV_singleband.tif
├── Jaipur_S1_2020_VH_singleband.tif
├── Jaipur_S1_2025_VV_singleband.tif
├── Jaipur_S1_2025_VH_singleband.tif
│
├── OSM_Jaipur_Clipped_Reference.gpkg
│
├── aligned_utm43n/
│   ├── Jaipur_S1_2016_VV_UTM43N_10m.tif
│   ├── Jaipur_S1_2016_VH_UTM43N_10m.tif
│   ├── Jaipur_S1_2020_VV_UTM43N_10m.tif
│   ├── Jaipur_S1_2020_VH_UTM43N_10m.tif
│   ├── Jaipur_S1_2025_VV_UTM43N_10m.tif
│   └── Jaipur_S1_2025_VH_UTM43N_10m.tif
│
├── common_footprint/
│   └── Jaipur_Common_Valid_Footprint.tif
│
├── sar_features/
│   ├── Jaipur_S1_2016_DualPol_Total_Backscatter_dB.tif
│   ├── Jaipur_S1_2016_VV_VH_Ratio_dB.tif
│   ├── Jaipur_S1_2020_DualPol_Total_Backscatter_dB.tif
│   ├── Jaipur_S1_2020_VV_VH_Ratio_dB.tif
│   ├── Jaipur_S1_2025_DualPol_Total_Backscatter_dB.tif
│   ├── Jaipur_S1_2025_VV_VH_Ratio_dB.tif
│   └── Jaipur_SAR_Feature_Stack_2016_2025.tif
│
└── change_detection/
    ├── VV_2016_2020_continuous.tif
    ├── VV_2016_2020_candidate_mask.tif
    ├── VV_2016_2025_continuous.tif
    ├── VV_2016_2025_candidate_mask.tif
    ├── VV_2020_2025_continuous.tif
    ├── VV_2020_2025_candidate_mask.tif
    ├── VH_2016_2020_continuous.tif
    ├── VH_2016_2020_candidate_mask.tif
    ├── VH_2016_2025_continuous.tif
    ├── VH_2016_2025_candidate_mask.tif
    ├── VH_2020_2025_continuous.tif
    ├── VH_2020_2025_candidate_mask.tif
    │
    └── spatial_clusters/
        ├── SAR_Joint_Change_Clusters.gpkg
        └── SAR_Joint_Change_Clusters.tif
```

---

## 5. Processed Dataset Descriptions

### 5.1 Terrain-Corrected VV/VH GeoTIFFs

**Location:** `data/processed/`

These are the primary SNAP-exported terrain-corrected polarization rasters.

Six files are available:

- 2016 VV and VH
- 2020 VV and VH
- 2025 VV and VH

They are retained as the initial processed raster inputs for subsequent Python workflows.

### 5.2 Single-Band Polarization Rasters

**Location:** `data/processed/`

These files contain separately extracted VV and VH polarization bands from the terrain-corrected products.

They provide the inputs for the raster alignment workflow.

### 5.3 Aligned SAR Rasters

**Location:** `aligned_utm43n/`

The six VV/VH rasters were aligned to a common projected grid.

Recorded grid characteristics:

| Parameter | Value |
|---|---|
| CRS | EPSG:32643 |
| Pixel size | 10 m |
| Width | 3993 pixels |
| Height | 3349 pixels |
| Number of rasters | 6 |

These aligned rasters are the principal inputs for pixel-wise temporal comparison and feature extraction.

### 5.4 Common Valid Footprint

**Location:** `common_footprint/`

File:

`Jaipur_Common_Valid_Footprint.tif`

This raster represents the common valid-data footprint calculated across the six aligned VV/VH datasets.

Recorded statistics:

- Common valid pixels: 13,202,823
- Percentage of the full rectangular grid: approximately 98.73%

The footprint supports consistent spatial comparisons by identifying pixels valid across the required input rasters.

### 5.5 SAR-Derived Features

**Location:** `sar_features/`

The feature-generation workflow produces two principal annual features.

**A. Dual-Polarization Total Backscatter**

Represents a combined VV/VH backscatter feature derived from the two polarization channels.

**B. VV/VH Ratio**

Represents the relationship between the VV and VH polarization responses.

The directory also contains:

`Jaipur_SAR_Feature_Stack_2016_2025.tif`

This is a 15-band raster stack containing annual polarization information, derived features and temporal change information.

The exact band order and calculation definitions should be interpreted using the feature-extraction scripts and their documentation.

### 5.6 Change-Detection Products

**Location:** `change_detection/`

The change-detection workflow generates continuous change rasters and candidate masks for three comparison periods:

- 2016–2020
- 2020–2025
- 2016–2025

For each period, both VV and VH products are available.

**Continuous change rasters**

Represent the pixel-wise backscatter differences between the selected acquisition dates.

**Candidate masks**

Identify pixels satisfying the selected change thresholds.

The candidate masks are intended for further spatial analysis. They should not be interpreted directly as built-up or newly urbanised land.

### 5.7 Spatial Change Clusters

**Location:** `change_detection/spatial_clusters/`

Files:

- `SAR_Joint_Change_Clusters.gpkg`
- `SAR_Joint_Change_Clusters.tif`

These products represent spatially connected candidate areas identified using the joint VV/VH change-detection workflow.

Recorded cluster statistics:

| Metric | Result |
|---|---:|
| Retained clusters | 196 |
| Minimum cluster area | 0.5 ha |
| Combined cluster area | 2.3042 km² |
| Mean cluster area | 1.1756 ha |
| Largest cluster | 6.17 ha |

These are SAR surface-change candidate statistics, not validated urban expansion measurements.

### 5.8 Clipped OSM Reference Dataset

**Location:** `data/processed/`

File:

`OSM_Jaipur_Clipped_Reference.gpkg`

This GeoPackage contains the clipped OpenStreetMap reference data used in the project.

The source reference dataset is stored under `data/raw/`.

Recorded clipping statistics:

- Original reference records: 145,169
- Retained records after clipping: 140,644

The dataset is used for spatial comparison with SAR change candidates and for exploratory assessment of current building-footprint overlap.

OSM data are not historical ground truth for the three Sentinel-1 acquisition years.

---

## 6. Data Quality and Spatial Consistency

Before multi-temporal analysis, the following properties were assessed:

1. CRS consistency.
2. Raster dimensions and pixel spacing.
3. Spatial grid alignment.
4. NoData values and raster footprints.
5. Common valid-data coverage.
6. VV/VH polarization identification.
7. Municipal boundary coverage.
8. Pixel-value distributions and extreme values.
9. Feature extraction quality.

The aligned datasets use EPSG:32643 and a common 10 m grid.

The municipal coverage analysis reported 100% valid aligned raster-mask coverage within the municipal polygon for the analysed dates. This describes the aligned raster-mask coverage and should not be interpreted as independent proof of complete original satellite observation coverage.

Matching geographic bounds alone does not guarantee pixel-level alignment.

---

## 7. Processing Scripts and Reproducibility

The processing and analysis scripts are maintained separately under:

`Project_02_Jaipur_SAR_Urban_Expansion/scripts/`

The main processing stages are:

| Stage | Scripts | Purpose |
|---|---|---|
| Input validation and extraction | 01–03 | Validate input rasters and extract VV/VH bands |
| Spatial alignment | 04–05 | Align rasters and assess quality |
| Raster diagnostics | 06–14 | Distribution, metadata, NoData and common footprint |
| Temporal analysis | 15 | Backscatter comparison |
| Feature engineering | 16–17, 31–32 | Generate and visualise SAR features |
| Boundary and OSM preparation | 18–28 | Prepare and assess reference data |
| Coverage and pixel audit | 29–30 | Municipal coverage and pixel-value checks |
| Change detection | 33 | Generate continuous changes and candidate masks |
| Spatial clustering | 34 | Identify connected change clusters |
| OSM comparison | 35 | Compare candidate clusters with current OSM data |
| Final analysis | 36–40 | Generate final maps, statistics and temporal visualisations |

The phase-wise Jupyter Notebook provides an organised entry point for running these scripts.

Some intermediate SNAP products were removed during the earlier processing workflow. The original SAFE products and retained GeoTIFF outputs should therefore be treated as the primary available source and processed datasets. Do not assume that unavailable intermediate SNAP products can be reconstructed exactly from the retained files alone.

---

## 8. Storage and GitHub Management

The processed directory contains large raster and vector datasets that are not suitable for direct storage in a standard GitHub repository.

The following should normally remain stored locally or in an appropriate external data repository:

- Terrain-corrected GeoTIFF rasters.
- Single-band VV/VH rasters.
- Aligned UTM43N rasters.
- Common footprint raster.
- SAR feature rasters and feature stack.
- Continuous change rasters and candidate masks.
- Spatial cluster GeoPackage and raster.
- Clipped OSM GeoPackage.

The GitHub repository should retain:

- This README.
- Processing and analysis scripts.
- Small CSV statistical outputs where appropriate.
- Selected final maps and figures.
- Data provenance and retrieval instructions.
- Project methodology and documentation.

Large data files should be excluded through `.gitignore` or managed through an appropriate external data-storage solution.

---

## 9. Important Research Limitations

The current processed dataset supports multi-temporal SAR backscatter analysis and candidate surface-change mapping.

It does not independently establish:

- A validated built-up/non-built-up classification.
- Historical urban boundaries for 2016, 2020 or 2025.
- A validated urban expansion rate.
- Actual built-up area growth.
- Classification accuracy based on contemporary OSM overlap.

Further validation using historical optical imagery, authoritative reference datasets or independently labelled samples is required before reporting quantitative urban expansion.

---

## 10. Next Analysis Stages

The processed datasets support the following research activities:

1. SAR backscatter visualisation and temporal comparison.
2. VV and VH feature analysis.
3. Polarization-ratio and other SAR-derived feature analysis.
4. Spatial change-candidate detection.
5. Spatial clustering and candidate-area investigation.
6. Comparison with current OSM reference features.
7. Historical built-up classification and independent validation.
8. Urban expansion area estimation after validation.
9. Final thematic maps and research publication.

---

## 11. References and Data Attribution

**Satellite data:** Sentinel-1A, Copernicus Sentinel-1 mission.

**Processing software:** European Space Agency (ESA), SNAP 14.

**Reference data:** OpenStreetMap contributors.

OSM-derived data must include appropriate attribution and comply with the Open Database License (ODbL).

The municipal boundary source and its licensing information should also be documented in the project-level README.

---

**Project:** Jaipur SAR-Based Urban Expansion Analysis  
**Satellite:** Sentinel-1A  
**Sensor mode:** IW GRDH  
**Polarizations:** VV and VH  
**Acquisition period:** 2016–2025  
**Processing software:** ESA SNAP 14  
**Analysis environment:** Python and QGIS  
**Aligned CRS:** EPSG:32643  
**Nominal aligned resolution:** 10 m
