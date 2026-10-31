
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

CRS = "EPSG:32643"

# ============================================================
# LOAD REFERENCE BUFFER
# ============================================================

buffer = gpd.read_file(BUFFER_FILE).to_crs(CRS)
buffer_geom = buffer.geometry.union_all()

buffer_area_km2 = buffer_geom.area / 1e6

print("=" * 70)
print("OSM SPATIAL COVERAGE AND AREA ANALYSIS")
print("=" * 70)

print(f"Reference buffer area: {buffer_area_km2:.3f} km²")

# ============================================================
# LOAD LAND-USE POLYGONS
# ============================================================

landuse = gpd.read_file(
    GPKG_FILE,
    layer="landuse_polygon"
).to_crs(CRS)

landuse["area_km2"] = landuse.geometry.area / 1e6

landuse_area = (
    landuse.groupby("landuse", dropna=False)
    .agg(
        feature_count=("osm_id", "count"),
        total_area_km2=("area_km2", "sum"),
        mean_area_km2=("area_km2", "mean")
    )
    .reset_index()
)

landuse_area["percentage_of_buffer"] = (
    landuse_area["total_area_km2"]
    / buffer_area_km2 * 100
)

landuse_area = landuse_area.sort_values(
    "total_area_km2",
    ascending=False
)

# ============================================================
# BUILDING FOOTPRINT AREA
# ============================================================

buildings = gpd.read_file(
    GPKG_FILE,
    layer="buildings_polygon"
).to_crs(CRS)

buildings["area_km2"] = buildings.geometry.area / 1e6

building_area_km2 = buildings["area_km2"].sum()

building_coverage = (
    building_area_km2 / buffer_area_km2 * 100
)

# ============================================================
# OPEN PUBLIC SPACE AREA
# ============================================================

parks = gpd.read_file(
    GPKG_FILE,
    layer="open_public_spaces_polygon"
).to_crs(CRS)

parks["area_km2"] = parks.geometry.area / 1e6

parks_area_km2 = parks["area_km2"].sum()

parks_coverage = (
    parks_area_km2 / buffer_area_km2 * 100
)

# ============================================================
# WATER POLYGON AREA
# ============================================================

water = gpd.read_file(
    GPKG_FILE,
    layer="water_polygons_polygon"
).to_crs(CRS)

water["area_km2"] = water.geometry.area / 1e6

water_area_km2 = water["area_km2"].sum()

water_coverage = (
    water_area_km2 / buffer_area_km2 * 100
)

# ============================================================
# PRINT RESULTS
# ============================================================

print("\nLAND-USE AREA DISTRIBUTION")
print("-" * 70)

for _, row in landuse_area.iterrows():

    category = str(row["landuse"])

    print(
        f"{category:<22}"
        f"{row['feature_count']:>6.0f} features | "
        f"{row['total_area_km2']:>10.3f} km² | "
        f"{row['percentage_of_buffer']:>8.3f}%"
    )

print("\n" + "=" * 70)
print("OTHER SPATIAL COVERAGE STATISTICS")
print("=" * 70)

print(f"Total building footprint: {building_area_km2:.3f} km²")
print(f"Building coverage: {building_coverage:.3f}%")

print(f"\nOpen public space area: {parks_area_km2:.3f} km²")
print(f"Open public space coverage: {parks_coverage:.3f}%")

print(f"\nWater polygon area: {water_area_km2:.3f} km²")
print(f"Water coverage: {water_coverage:.3f}%")

# ============================================================
# SAVE REPORTS
# ============================================================

landuse_file = REPORT_DIR / "OSM_Landuse_Area_Distribution.csv"

coverage_file = REPORT_DIR / "OSM_Spatial_Coverage_Summary.csv"

landuse_area.to_csv(landuse_file, index=False)

coverage_df = pd.DataFrame([
    {
        "category": "Building footprints",
        "feature_count": len(buildings),
        "area_km2": building_area_km2,
        "percentage_of_buffer": building_coverage
    },
    {
        "category": "Open public spaces",
        "feature_count": len(parks),
        "area_km2": parks_area_km2,
        "percentage_of_buffer": parks_coverage
    },
    {
        "category": "Water polygons",
        "feature_count": len(water),
        "area_km2": water_area_km2,
        "percentage_of_buffer": water_coverage
    }
])

coverage_df.to_csv(coverage_file, index=False)

print("\nReports saved:")
print(landuse_file)
print(coverage_file)

print("\nAREA ANALYSIS COMPLETED.")
print("Original GeoPackage was not modified.")
