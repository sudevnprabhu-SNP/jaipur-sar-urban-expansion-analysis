
from pathlib import Path

import geopandas as gpd
import pandas as pd



# ============================================================
# 1. PROJECT PATHS
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent.parent

GPKG_FILE = (
    PROJECT_DIR
    / "data"
    / "raw"
    / "Jaipur_India_Rajasthan_Reference.gpkg"
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

SUMMARY_FILE = REPORT_DIR / "OSM_Layer_Audit.csv"
REPORT_FILE = REPORT_DIR / "OSM_Dataset_Audit.txt"


# ============================================================
# 2. CHECK INPUT FILES
# ============================================================

print("\n" + "=" * 70)
print("JAIPUR OSM REFERENCE DATA AUDIT")
print("=" * 70)

if not GPKG_FILE.exists():
    raise FileNotFoundError(
        f"GeoPackage not found: {GPKG_FILE}"
    )

if not BUFFER_FILE.exists():
    raise FileNotFoundError(
        f"Reference buffer not found: {BUFFER_FILE}"
    )

# List GeoPackage layers
layers = gpd.list_layers(GPKG_FILE)["name"].tolist()

print("\n[1] GEOPACKAGE INFORMATION")
print("-" * 70)

print("File:", GPKG_FILE.name)
print("File size (MB):", round(GPKG_FILE.stat().st_size / (1024 ** 2), 3))
print("Number of layers:", len(layers))

for layer in layers:
    print(" -", layer)


# ============================================================
# 3. LOAD REFERENCE BUFFER
# ============================================================

buffer = gpd.read_file(BUFFER_FILE)

if buffer.empty:
    raise ValueError("Reference buffer is empty.")

if buffer.crs is None:
    raise ValueError("Reference buffer has no CRS.")

buffer = buffer.to_crs(epsg=4326)

buffer_geometry = buffer.geometry.union_all()

print("\n[2] REFERENCE EXTENT")
print("-" * 70)

print("CRS:", buffer.crs)
print("Bounds:", buffer.total_bounds)


# ============================================================
# 4. AUDIT EACH OSM LAYER
# ============================================================

summary_records = []
report_lines = []

total_features = 0
total_invalid = 0
total_missing = 0
total_empty = 0

report_lines.append("JAIPUR OSM REFERENCE DATA AUDIT")
report_lines.append("=" * 70)

for layer_name in layers:

    print("\n" + "-" * 70)
    print("LAYER:", layer_name)
    print("-" * 70)

    gdf = gpd.read_file(
        GPKG_FILE,
        layer=layer_name
    )

    feature_count = len(gdf)
    total_features += feature_count

    crs = str(gdf.crs)

    geometry_types = (
        gdf.geom_type.value_counts().to_dict()
    )

    missing_geometry = int(gdf.geometry.isna().sum())

    empty_geometry = int(
        gdf.geometry.is_empty.sum()
    )

    valid_mask = (
        gdf.geometry.notna()
        & ~gdf.geometry.is_empty
    )

    valid_geometries = gdf.loc[valid_mask]

    invalid_geometry = int(
        (~valid_geometries.geometry.is_valid).sum()
    )

    total_missing += missing_geometry
    total_empty += empty_geometry
    total_invalid += invalid_geometry

    # --------------------------------------------------------
    # Spatial information
    # --------------------------------------------------------

    if gdf.crs is not None and not valid_geometries.empty:

        gdf_4326 = valid_geometries.to_crs(epsg=4326)

        bounds = gdf_4326.total_bounds

        intersects_buffer = (
            gdf_4326.geometry.intersects(buffer_geometry)
        )

        inside_buffer_count = int(intersects_buffer.sum())

        outside_buffer_count = (
            len(gdf_4326) - inside_buffer_count
        )

        bounds_text = str(bounds.tolist())

    else:

        inside_buffer_count = None
        outside_buffer_count = None
        bounds_text = "Unavailable"

    # --------------------------------------------------------
    # Attribute information
    # --------------------------------------------------------

    columns = list(gdf.columns)

    attribute_columns = [
        col for col in columns
        if col != "geometry"
    ]

    print("Features:", feature_count)
    print("CRS:", crs)
    print("Geometry types:", geometry_types)
    print("Missing geometries:", missing_geometry)
    print("Empty geometries:", empty_geometry)
    print("Invalid geometries:", invalid_geometry)

    print("Attribute fields:")
    print(attribute_columns)

    print("Geographic bounds:", bounds_text)

    if inside_buffer_count is not None:
        print("Features intersecting reference buffer:",
              inside_buffer_count)
        print("Features not intersecting reference buffer:",
              outside_buffer_count)

    # --------------------------------------------------------
    # Inspect OSM tags
    # --------------------------------------------------------

    print("\nSample records:")

    if not gdf.empty:
        print(
            gdf.drop(columns="geometry")
            .head(3)
            .to_string(index=False)
        )

    # --------------------------------------------------------
    # Save layer summary
    # --------------------------------------------------------

    summary_records.append({
        "layer": layer_name,
        "feature_count": feature_count,
        "crs": crs,
        "geometry_types": str(geometry_types),
        "missing_geometries": missing_geometry,
        "empty_geometries": empty_geometry,
        "invalid_geometries": invalid_geometry,
        "features_intersecting_buffer": inside_buffer_count,
        "features_outside_buffer": outside_buffer_count,
        "bounds_epsg4326": bounds_text,
        "attribute_fields": ", ".join(attribute_columns)
    })

    report_lines.extend([
        "",
        "=" * 70,
        f"LAYER: {layer_name}",
        "=" * 70,
        f"Feature count: {feature_count}",
        f"CRS: {crs}",
        f"Geometry types: {geometry_types}",
        f"Missing geometries: {missing_geometry}",
        f"Empty geometries: {empty_geometry}",
        f"Invalid geometries: {invalid_geometry}",
        f"Geographic bounds: {bounds_text}",
        f"Features intersecting buffer: {inside_buffer_count}",
        f"Features outside buffer: {outside_buffer_count}",
        f"Attribute fields: {attribute_columns}"
    ])


# ============================================================
# 5. TOTAL DATASET SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("[3] COMPLETE DATASET SUMMARY")
print("=" * 70)

print("Total layers:", len(layers))
print("Total features:", total_features)
print("Missing geometries:", total_missing)
print("Empty geometries:", total_empty)
print("Invalid geometries:", total_invalid)

report_lines.extend([
    "",
    "=" * 70,
    "COMPLETE DATASET SUMMARY",
    "=" * 70,
    f"Total layers: {len(layers)}",
    f"Total features: {total_features}",
    f"Missing geometries: {total_missing}",
    f"Empty geometries: {total_empty}",
    f"Invalid geometries: {total_invalid}"
])


# ============================================================
# 6. SAVE AUDIT RESULTS
# ============================================================

summary_df = pd.DataFrame(summary_records)

summary_df.to_csv(
    SUMMARY_FILE,
    index=False
)

with open(
    REPORT_FILE,
    "w",
    encoding="utf-8"
) as file:

    file.write("\n".join(report_lines))


# ============================================================
# 7. FINAL STATUS
# ============================================================

print("\n[4] AUDIT REPORTS")
print("-" * 70)

print("CSV summary:", SUMMARY_FILE)
print("Text report:", REPORT_FILE)

print("\nOSM DATA AUDIT COMPLETED")
print("=" * 70)
