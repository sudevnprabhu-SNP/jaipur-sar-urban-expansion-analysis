
from pathlib import Path

import geopandas as gpd
import pandas as pd


# ============================================================
# 1. PROJECT PATHS
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent.parent

INPUT_GPKG = (
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

OUTPUT_DIR = PROJECT_DIR / "data" / "processed"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_GPKG = (
    OUTPUT_DIR / "OSM_Jaipur_Clipped_Reference.gpkg"
)

REPORT_DIR = (
    PROJECT_DIR
    / "reports"
    / "osm_quality_analysis"
)

REPORT_DIR.mkdir(parents=True, exist_ok=True)

SUMMARY_FILE = (
    REPORT_DIR / "OSM_Clipping_Summary.csv"
)

# ============================================================
# 2. CHECK INPUTS AND OUTPUT
# ============================================================

print("\n" + "=" * 70)
print("JAIPUR OSM SPATIAL FILTERING AND CLIPPING")
print("=" * 70)

if not INPUT_GPKG.exists():
    raise FileNotFoundError(INPUT_GPKG)

if not BUFFER_FILE.exists():
    raise FileNotFoundError(BUFFER_FILE)

# Never overwrite an existing result automatically.
if OUTPUT_GPKG.exists():
    raise FileExistsError(
        f"Output already exists: {OUTPUT_GPKG}\n"
        "Rename or move the existing output before rerunning."
    )

# ============================================================
# 3. LOAD REFERENCE BUFFER
# ============================================================

buffer = gpd.read_file(BUFFER_FILE)

if buffer.empty or buffer.crs is None:
    raise ValueError("Invalid or empty reference buffer.")

buffer_utm = buffer.to_crs(epsg=32643)

# Dissolve to one exact clipping geometry.
buffer_geometry = buffer_utm.geometry.union_all()

buffer_mask = gpd.GeoDataFrame(
    {"name": ["Jaipur_10km_Buffer"]},
    geometry=[buffer_geometry],
    crs="EPSG:32643"
)

buffer_area_km2 = (
    buffer_geometry.area / 1_000_000
)

print("\n[1] REFERENCE BUFFER")
print("-" * 70)

print("CRS: EPSG:32643")
print(f"Buffer area: {buffer_area_km2:.3f} km²")
print("Bounds:", buffer_utm.total_bounds)

# ============================================================
# 4. IDENTIFY SOURCE LAYERS
# ============================================================

layers = gpd.list_layers(INPUT_GPKG)["name"].tolist()

print("\n[2] INPUT GEOPACKAGE")
print("-" * 70)

print("Number of layers:", len(layers))

for layer in layers:
    print("-", layer)

# ============================================================
# 5. PROCESS EACH LAYER
# ============================================================

summary = []

total_before = 0
total_after = 0

first_layer = True

for layer_name in layers:

    print("\n" + "-" * 70)
    print("PROCESSING:", layer_name)
    print("-" * 70)

    # Read original layer.
    gdf = gpd.read_file(
        INPUT_GPKG,
        layer=layer_name
    )

    count_before = len(gdf)
    total_before += count_before

    if gdf.crs is None:
        raise ValueError(
            f"Layer has no CRS: {layer_name}"
        )

    # Remove only missing and empty geometries.
    # Original source GeoPackage remains untouched.
    gdf = gdf[
        gdf.geometry.notna()
        & ~gdf.geometry.is_empty
    ].copy()

    # Reproject to metric CRS.
    gdf_utm = gdf.to_crs(epsg=32643)

    # Count features that intersect the buffer.
    intersects_mask = (
        gdf_utm.geometry.intersects(buffer_geometry)
    )

    intersecting_count = int(intersects_mask.sum())

    # --------------------------------------------------------
    # Inspect unusually large polygon geometries.
    # --------------------------------------------------------

    if (
        "polygon" in layer_name.lower()
        and not gdf_utm.empty
    ):

        areas_km2 = (
            gdf_utm.geometry.area / 1_000_000
        )

        large = areas_km2[areas_km2 > 10]

        if not large.empty:

            print(
                "Large source polygons (>10 km²):",
                len(large)
            )

            top_indices = (
                areas_km2.nlargest(5).index
            )

            for idx in top_indices:

                osm_id = (
                    gdf_utm.loc[idx, "osm_id"]
                    if "osm_id" in gdf_utm.columns
                    else "Unknown"
                )

                print(
                    f"  OSM ID: {osm_id}, "
                    f"area: {areas_km2.loc[idx]:.3f} km²"
                )

    # --------------------------------------------------------
    # Clip to exact buffer geometry.
    # --------------------------------------------------------

    if intersecting_count == 0:

        print("No features intersect the buffer.")
        print("Layer skipped.")

        continue

    clipped = gpd.clip(
        gdf_utm,
        buffer_mask,
        keep_geom_type=False
    )

    # Remove empty geometries after clipping.
    clipped = clipped[
        clipped.geometry.notna()
        & ~clipped.geometry.is_empty
    ].copy()

    # Convert back to geographic CRS for OSM data storage.
    clipped = clipped.to_crs(epsg=4326)

    count_after = len(clipped)
    total_after += count_after

    # --------------------------------------------------------
    # Save to separate GeoPackage.
    # --------------------------------------------------------

    if count_after > 0:

        clipped.to_file(
            OUTPUT_GPKG,
            layer=layer_name,
            driver="GPKG",
            mode="w" if first_layer else "a",
            index=False
        )

        first_layer = False

    # --------------------------------------------------------
    # Summary.
    # --------------------------------------------------------

    print("Original features:", count_before)
    print("Features intersecting buffer:", intersecting_count)
    print("Features after clipping:", count_after)
    print("Removed missing/empty or non-intersecting:",
          count_before - count_after)

    if not clipped.empty:
        print("Output geometry types:")
        print(clipped.geom_type.value_counts().to_dict())

    summary.append({
        "layer": layer_name,
        "original_features": count_before,
        "intersecting_features": intersecting_count,
        "clipped_features": count_after,
        "features_not_in_output": count_before - count_after,
        "output_crs": "EPSG:4326"
    })


# ============================================================
# 6. SAVE CLIPPING SUMMARY
# ============================================================

summary_df = pd.DataFrame(summary)

summary_df.to_csv(
    SUMMARY_FILE,
    index=False
)

# ============================================================
# 7. FINAL REPORT
# ============================================================

print("\n" + "=" * 70)
print("CLIPPING SUMMARY")
print("=" * 70)

print("Original total features:", total_before)
print("Clipped total features:", total_after)
print("Features not retained:", total_before - total_after)

print(f"\nReference buffer: {buffer_area_km2:.3f} km²")

print("\nOutput GeoPackage:")
print(OUTPUT_GPKG)

print("\nCSV summary:")
print(SUMMARY_FILE)

print("\nOSM SPATIAL CLIPPING COMPLETED")
print("=" * 70)
