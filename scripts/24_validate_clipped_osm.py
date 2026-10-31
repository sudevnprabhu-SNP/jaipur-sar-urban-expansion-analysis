
from pathlib import Path
import geopandas as gpd
import pandas as pd

# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_DIR = Path(
    r"C:\Users\ssat-\Documents\RemoteSensing_Projects"
    r"\Project_02_Jaipur_SAR_Urban_Expansion"
)

GPKG_FILE = (
    PROJECT_DIR
    / "data"
    / "processed"
    / "OSM_Jaipur_Clipped_Reference.gpkg"
)

BUFFER_FILE = (
    PROJECT_DIR
    / "data"
    / "boundaries"
    / "Jaipur_OSM_Reference_Buffer_10km.geojson"
)

REPORT_DIR = (
    PROJECT_DIR
    / "reports"
    / "osm_quality_analysis"
)

REPORT_DIR.mkdir(parents=True, exist_ok=True)

CSV_REPORT = REPORT_DIR / "Final_OSM_Validation.csv"
TXT_REPORT = REPORT_DIR / "Final_OSM_Validation.txt"

PROJECT_CRS = "EPSG:32643"

# Suspicious feature that should not exist in clipped output
EXCLUDED_OSM_ID = "11203285"

# ============================================================
# REPORT STORAGE
# ============================================================

results = []
report_lines = []

def log(message=""):
    print(message)
    report_lines.append(str(message))


# ============================================================
# INITIAL CHECKS
# ============================================================

log("=" * 70)
log("FINAL VALIDATION OF CLIPPED OSM REFERENCE DATA")
log("=" * 70)

if not GPKG_FILE.exists():
    raise FileNotFoundError(f"GeoPackage not found: {GPKG_FILE}")

if not BUFFER_FILE.exists():
    raise FileNotFoundError(f"Buffer boundary not found: {BUFFER_FILE}")

# Load exact buffer
buffer = gpd.read_file(BUFFER_FILE)

if buffer.empty:
    raise ValueError("The OSM reference buffer is empty.")

if buffer.crs is None:
    raise ValueError("Buffer CRS is missing.")

buffer = buffer.to_crs(PROJECT_CRS)
buffer_geometry = buffer.geometry.union_all()

log(f"\nValidation CRS: {PROJECT_CRS}")
log(f"Buffer area: {buffer_geometry.area / 1e6:.3f} km²")


# ============================================================
# DISCOVER GEOPACKAGE LAYERS
# ============================================================

layers = gpd.list_layers(GPKG_FILE)["name"].tolist()

log(f"\nTotal layers discovered: {len(layers)}")

if len(layers) != 10:
    log("WARNING: Expected 10 layers, but a different number was found.")

# ============================================================
# VALIDATE EACH LAYER
# ============================================================

total_features = 0
total_missing = 0
total_empty = 0
total_invalid = 0
total_outside = 0
total_crs_errors = 0
total_schema_fields = 0

for layer_name in layers:

    log("\n" + "-" * 70)
    log(f"LAYER: {layer_name}")
    log("-" * 70)

    gdf = gpd.read_file(GPKG_FILE, layer=layer_name)

    feature_count = len(gdf)
    total_features += feature_count

    source_crs = str(gdf.crs)

    missing_geometry = int(gdf.geometry.isna().sum())

    non_missing = gdf.loc[gdf.geometry.notna()]

    empty_geometry = int(non_missing.geometry.is_empty.sum())

    valid_candidates = non_missing.loc[
        ~non_missing.geometry.is_empty
    ]

    invalid_geometry = int(
        (~valid_candidates.geometry.is_valid).sum()
    )

    missing_count = missing_geometry
    total_missing += missing_geometry
    total_empty += empty_geometry
    total_invalid += invalid_geometry

    # CRS check
    crs_ok = gdf.crs is not None

    if not crs_ok:
        total_crs_errors += 1
        log("ERROR: Layer has no CRS.")
        outside_count = None

    else:
        gdf_projected = gdf.to_crs(PROJECT_CRS)

        # Check whether each geometry is fully covered by buffer.
        # A small tolerance accommodates floating-point reprojection.
        tolerance = 0.05  # metres

        outside_count = 0

        for geom in gdf_projected.geometry:

            if geom is None or geom.is_empty:
                continue

            if not buffer_geometry.buffer(tolerance).covers(geom):
                outside_count += 1

        total_outside += outside_count

    # Attribute checks
    fields = [column for column in gdf.columns if column != "geometry"]
    field_count = len(fields)
    total_schema_fields += field_count

    osm_id_present = "osm_id" in gdf.columns

    excluded_id_present = False

    if osm_id_present:
        excluded_id_present = (
            gdf["osm_id"].astype(str) == EXCLUDED_OSM_ID
        ).any()

    # Attribute completeness
    attribute_nulls = int(gdf[fields].isna().sum().sum()) if fields else 0

    log(f"Feature count: {feature_count:,}")
    log(f"CRS: {source_crs}")
    log(f"Missing geometries: {missing_geometry}")
    log(f"Empty geometries: {empty_geometry}")
    log(f"Invalid geometries: {invalid_geometry}")

    if outside_count is not None:
        log(f"Features extending outside buffer: {outside_count}")

    log(f"Attribute fields: {field_count}")
    log(f"Null attribute cells: {attribute_nulls}")
    log(f"OSM ID field present: {osm_id_present}")
    log(f"Excluded river-basin ID present: {excluded_id_present}")

    if outside_count is None:
        spatial_status = "NOT CHECKED - MISSING CRS"
    elif outside_count == 0:
        spatial_status = "PASS"
    else:
        spatial_status = "FAIL"

    geometry_status = (
        "PASS"
        if missing_geometry == 0
        and empty_geometry == 0
        and invalid_geometry == 0
        else "FAIL"
    )

    results.append({
        "layer": layer_name,
        "feature_count": feature_count,
        "crs": source_crs,
        "missing_geometries": missing_geometry,
        "empty_geometries": empty_geometry,
        "invalid_geometries": invalid_geometry,
        "features_outside_buffer": outside_count,
        "attribute_fields": field_count,
        "null_attribute_cells": attribute_nulls,
        "osm_id_field_present": osm_id_present,
        "river_basin_id_present": excluded_id_present,
        "geometry_status": geometry_status,
        "spatial_status": spatial_status
    })


# ============================================================
# FINAL DATASET SUMMARY
# ============================================================

log("\n" + "=" * 70)
log("FINAL DATASET SUMMARY")
log("=" * 70)

log(f"Total layers: {len(layers)}")
log(f"Total features: {total_features:,}")
log(f"Total missing geometries: {total_missing}")
log(f"Total empty geometries: {total_empty}")
log(f"Total invalid geometries: {total_invalid}")
log(f"Total features extending outside buffer: {total_outside}")
log(f"Layers with missing CRS: {total_crs_errors}")
log(f"Total attribute fields across layers: {total_schema_fields}")

# Check suspicious ID across every layer
river_basin_found = False

for layer_name in layers:

    temp = gpd.read_file(
        GPKG_FILE,
        layer=layer_name
    )

    if "osm_id" in temp.columns:
        if (
            temp["osm_id"].astype(str) == EXCLUDED_OSM_ID
        ).any():
            river_basin_found = True
            log(
                f"WARNING: River-basin ID found in layer: {layer_name}"
            )

log(
    "Ganga-Yamuna river-basin ID absent: "
    + ("YES" if not river_basin_found else "NO")
)

# ============================================================
# SAVE REPORTS
# ============================================================

validation_df = pd.DataFrame(results)

validation_df.to_csv(CSV_REPORT, index=False)

log("\n" + "=" * 70)
log("VALIDATION STATUS")
log("=" * 70)

overall_geometry_ok = (
    total_missing == 0
    and total_empty == 0
    and total_invalid == 0
)

overall_spatial_ok = (
    total_outside == 0
    and total_crs_errors == 0
)

overall_exclusion_ok = not river_basin_found

if (
    overall_geometry_ok
    and overall_spatial_ok
    and overall_exclusion_ok
):
    log("PASS: All tested geometry, CRS, spatial and exclusion checks passed.")
else:
    log("WARNING: One or more validation checks require investigation.")

log("\nReports saved:")
log(str(CSV_REPORT))
log(str(TXT_REPORT))

with open(TXT_REPORT, "w", encoding="utf-8") as file:
    file.write("\n".join(report_lines))

print("\nVALIDATION COMPLETED.")
