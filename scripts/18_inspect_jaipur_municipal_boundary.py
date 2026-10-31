from shapely.geometry import box
from shapely import transform as shapely_transform
from pathlib import Path

import geopandas as gpd
import pandas as pd


# ============================================================
# 1. PROJECT PATHS
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent.parent

BOUNDARY_FILE = (
    PROJECT_DIR
    / "data"
    / "boundaries"
    / "Jaipur_JMC_Wards.geojson"
)

OUTPUT_DIR = PROJECT_DIR / "data" / "boundaries"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 2. LOAD GEOJSON
# ============================================================

print("\n" + "=" * 65)
print("JAIPUR MUNICIPAL BOUNDARY INSPECTION")
print("=" * 65)

if not BOUNDARY_FILE.exists():
    raise FileNotFoundError(
        f"Boundary file not found: {BOUNDARY_FILE}"
    )

wards = gpd.read_file(BOUNDARY_FILE)

print("\n[1] DATASET INFORMATION")
print("-" * 65)

print("File:", BOUNDARY_FILE.name)
print("Number of features:", len(wards))
print("CRS:", wards.crs)
print("Geometry types:")
print(wards.geom_type.value_counts())

print("\nAttribute columns:")
print(list(wards.columns))


# ============================================================
# 3. INSPECT GEOMETRIES
# ============================================================

print("\n[2] GEOMETRY VALIDATION")
print("-" * 65)

print("Missing geometries:", wards.geometry.isna().sum())
print("Empty geometries:", wards.geometry.is_empty.sum())

valid_before = wards.geometry.is_valid.sum()

print("Valid geometries before repair:", valid_before)
print("Invalid geometries before repair:",
      len(wards) - valid_before)

# Repair invalid geometries
invalid_mask = (
    wards.geometry.notna()
    & ~wards.geometry.is_valid
)

if invalid_mask.any():
    wards.loc[invalid_mask, "geometry"] = (
        wards.loc[invalid_mask, "geometry"].make_valid()
    )

# Remove missing and empty geometries
wards = wards[
    wards.geometry.notna()
    & ~wards.geometry.is_empty
].copy()

print("Valid geometries after repair:",
      wards.geometry.is_valid.sum())


# ============================================================
# 4. CHECK COORDINATE REFERENCE SYSTEM
# ============================================================

if wards.crs is None:
    raise ValueError(
        "GeoJSON has no CRS. Do not assume its coordinate system."
    )

print("\n[3] CRS INFORMATION")
print("-" * 65)

print("Source CRS:", wards.crs)

# ============================================================
# 3A. CORRECT REVERSED COORDINATE AXES
# ============================================================

print("\n[3A] COORDINATE AXIS CHECK")
print("-" * 65)

bounds = wards.total_bounds

print("Original bounds:", bounds)

# Expected Jaipur geographic coordinate ranges.
# The source appears to have latitude stored as X
# and longitude stored as Y.

if (
    20 <= bounds[0] <= 30
    and 70 <= bounds[1] <= 85
    and 20 <= bounds[2] <= 30
    and 70 <= bounds[3] <= 85
):
    print("Reversed coordinate order detected.")
    print("Swapping X and Y coordinates...")

    wards.geometry = wards.geometry.apply(
        lambda geom: shapely_transform(
            geom,
            lambda coordinates: coordinates[:, ::-1]
        )
    )

    print("Coordinate order corrected.")

else:
    print("No reversed-axis pattern detected.")

print("Corrected bounds:", wards.total_bounds)

# GeoJSON geographic coordinates are expected to be WGS84.
# We inspect the source CRS rather than assigning one blindly.


# ============================================================
# 5. DISSOLVE ALL WARDS
# ============================================================

print("\n[4] MUNICIPAL BOUNDARY")
print("-" * 65)

municipality = wards.dissolve()

print("Ward features used:", len(wards))
print("Dissolved geometry type:",
      municipality.geom_type.iloc[0])


# ============================================================
# 6. CALCULATE AREA
# ============================================================

# UTM Zone 43N is suitable for Jaipur.
wards_utm = wards.to_crs(epsg=32643)
municipality_utm = municipality.to_crs(epsg=32643)

municipal_area_km2 = (
    municipality_utm.geometry.area.sum() / 1_000_000
)

print("\n[5] MUNICIPAL AREA")
print("-" * 65)

print(f"Municipal area: {municipal_area_km2:.3f} km²")


# ============================================================
# 7. COMPARE WITH EXISTING SAR STUDY RECTANGLE
# ============================================================

print("\n[6] SAR STUDY AREA COMPARISON")
print("-" * 65)

# Original study rectangle:
# West: 75.65 E
# East: 76.05 E
# South: 26.75 N
# North: 27.05 N

study_area = gpd.GeoDataFrame(
    {"name": ["SAR Study Rectangle"]},
    geometry=[box(75.65, 26.75, 76.05, 27.05)],
    crs="EPSG:4326"
)



study_area_utm = study_area.to_crs(epsg=32643)



study_area_km2 = (
    study_area_utm.geometry.area.sum() / 1_000_000
)

municipality_geometry = municipality_utm.geometry.iloc[0]
study_geometry = study_area_utm.geometry.iloc[0]

overlap_geometry = municipality_geometry.intersection(
    study_geometry
)

overlap_area_km2 = overlap_geometry.area / 1_000_000

# ============================================================
# DIAGNOSTIC: CHECK GEOGRAPHIC EXTENTS
# ============================================================

print("\n[DIAGNOSTIC] GEOGRAPHIC COORDINATES")
print("-" * 65)

print("Ward boundary bounds (EPSG:4326):")
print(wards.total_bounds)

print("\nSAR rectangle bounds (EPSG:4326):")
print(study_area.total_bounds)

print("\nWard boundary centroid (longitude, latitude):")
print(
    municipality.to_crs(epsg=4326)
    .geometry.iloc[0].centroid.coords[0]
)

print("\nSAR rectangle centroid (longitude, latitude):")
print(
    study_area.geometry.iloc[0].centroid.coords[0]
)

print("\nWard boundary bounds (UTM 43N):")
print(municipality_utm.total_bounds)

print("\nSAR rectangle bounds (UTM 43N):")
print(study_area_utm.total_bounds)

print("\nDo the geometries intersect?")
print(municipality_geometry.intersects(study_geometry))

print("\nDistance between geometries (km):")
print(
    municipality_geometry.distance(study_geometry) / 1000
)

print(f"SAR rectangle area: {study_area_km2:.3f} km²")
print(f"Municipal area:     {municipal_area_km2:.3f} km²")
print(f"Overlap area:       {overlap_area_km2:.3f} km²")

print(
    "Municipal area inside SAR rectangle: "
    f"{(overlap_area_km2 / municipal_area_km2) * 100:.2f}%"
    if municipal_area_km2 > 0
    else "Municipal area inside SAR rectangle: N/A"
)

print(
    "SAR rectangle covered by municipality: "
    f"{(overlap_area_km2 / study_area_km2) * 100:.2f}%"
    if study_area_km2 > 0
    else "SAR rectangle covered by municipality: N/A"
)


# ============================================================
# 8. SAVE OUTPUTS
# ============================================================

municipality_file = (
    OUTPUT_DIR / "Jaipur_JMC_Municipal_Boundary.geojson"
)

wards.to_file(
    OUTPUT_DIR / "Jaipur_JMC_Wards_Validated.geojson",
    driver="GeoJSON"
)

municipality.to_file(
    municipality_file,
    driver="GeoJSON"
)

print("\n[7] OUTPUT FILES")
print("-" * 65)

print("Validated wards:")
print(OUTPUT_DIR / "Jaipur_JMC_Wards_Validated.geojson")

print("Dissolved municipality:")
print(municipality_file)

print("\nBOUNDARY INSPECTION COMPLETED")
print("=" * 65)
