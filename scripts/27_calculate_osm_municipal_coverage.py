
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

BOUNDARY_FILE = (
    PROJECT_DIR
    / "data"
    / "boundaries"
    / "Jaipur_JMC_Municipal_Boundary.geojson"
)

REPORT_DIR = (
    PROJECT_DIR
    / "reports"
    / "osm_quality_analysis"
)

REPORT_DIR.mkdir(parents=True, exist_ok=True)

CRS = "EPSG:32643"

# ============================================================
# LOAD MUNICIPAL BOUNDARY
# ============================================================

boundary = gpd.read_file(BOUNDARY_FILE)

if boundary.empty:
    raise ValueError("Municipal boundary is empty.")

boundary = boundary.to_crs(CRS)

municipal_geometry = boundary.geometry.union_all()

municipal_area_km2 = municipal_geometry.area / 1e6

print("=" * 70)
print("OSM MUNICIPAL COVERAGE ANALYSIS")
print("=" * 70)

print(f"Municipal area: {municipal_area_km2:.3f} km²")

# ============================================================
# LAYERS TO ANALYZE
# ============================================================

layers = {
    "landuse_polygon": "Land use",
    "buildings_polygon": "Building footprints",
    "open_public_spaces_polygon": "Open public spaces",
    "water_polygons_polygon": "Water polygons",
}

area_records = []
category_records = []

# ============================================================
# CLIP EACH LAYER TO MUNICIPAL BOUNDARY
# ============================================================

for layer_name, display_name in layers.items():

    print("\n" + "-" * 70)
    print(display_name.upper())
    print("-" * 70)

    gdf = gpd.read_file(
        GPKG_FILE,
        layer=layer_name
    ).to_crs(CRS)

    original_count = len(gdf)

    # Exact intersection with municipal boundary
    clipped = gpd.clip(
        gdf,
        municipal_geometry
    )

    clipped = clipped[
        clipped.geometry.notna()
        & ~clipped.geometry.is_empty
    ].copy()

    clipped["area_km2"] = (
        clipped.geometry.area / 1e6
    )

    total_area_km2 = clipped["area_km2"].sum()

    coverage_percentage = (
        total_area_km2 / municipal_area_km2 * 100
    )

    print(f"Original features: {original_count:,}")
    print(f"Features intersecting municipality: {len(clipped):,}")
    print(f"Total mapped area: {total_area_km2:.4f} km²")
    print(f"Percentage of municipality: {coverage_percentage:.4f}%")

    area_records.append({
        "layer": layer_name,
        "category": display_name,
        "original_feature_count": original_count,
        "municipal_feature_count": len(clipped),
        "mapped_area_km2": total_area_km2,
        "municipal_area_km2": municipal_area_km2,
        "municipal_coverage_percentage": coverage_percentage
    })

    # Category-level areas for land use
    if layer_name == "landuse_polygon" and "landuse" in clipped.columns:

        category_area = (
            clipped.groupby("landuse", dropna=False)
            .agg(
                feature_count=("area_km2", "count"),
                area_km2=("area_km2", "sum")
            )
            .reset_index()
        )

        category_area["municipal_coverage_percentage"] = (
            category_area["area_km2"]
            / municipal_area_km2 * 100
        )

        for _, row in category_area.iterrows():

            category_records.append({
                "landuse_category": row["landuse"],
                "feature_count": row["feature_count"],
                "area_km2": row["area_km2"],
                "municipal_coverage_percentage": (
                    row["municipal_coverage_percentage"]
                )
            })

# ============================================================
# SAVE REPORTS
# ============================================================

area_df = pd.DataFrame(area_records)

category_df = pd.DataFrame(category_records)

area_report = (
    REPORT_DIR / "OSM_Municipal_Spatial_Coverage.csv"
)

category_report = (
    REPORT_DIR / "OSM_Municipal_Landuse_Area.csv"
)

area_df.to_csv(area_report, index=False)

category_df.to_csv(category_report, index=False)

# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("MUNICIPAL COVERAGE SUMMARY")
print("=" * 70)

print(
    area_df[
        [
            "category",
            "municipal_feature_count",
            "mapped_area_km2",
            "municipal_coverage_percentage"
        ]
    ].to_string(index=False)
)

print("\nReports saved:")
print(area_report)
print(category_report)

print("\nMunicipal coverage analysis completed.")
print("Original OSM GeoPackage was not modified.")
