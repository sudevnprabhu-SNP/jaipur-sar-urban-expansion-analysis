
from pathlib import Path

import geopandas as gpd
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent

SOURCE_GPKG = (
    PROJECT_DIR / "data/raw/Jaipur_India_Rajasthan_Reference.gpkg"
)

CLIPPED_GPKG = (
    PROJECT_DIR / "data/processed/OSM_Jaipur_Clipped_Reference.gpkg"
)

OUTPUT_DIR = (
    PROJECT_DIR / "reports/osm_quality_analysis"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SUSPICIOUS_IDS = [
    "11203285",
    "17303305",
    "874643949",
    "1008772934",
    "1008772935"
]

print("\n" + "=" * 70)
print("INVESTIGATION OF LARGE OSM LAND-USE POLYGONS")
print("=" * 70)

# Load original and clipped land-use layers
source = gpd.read_file(
    SOURCE_GPKG,
    layer="landuse_polygon"
)

clipped = gpd.read_file(
    CLIPPED_GPKG,
    layer="landuse_polygon"
)

# Use strings for safe OSM ID comparison
source["osm_id_check"] = source["osm_id"].astype(str)
clipped["osm_id_check"] = clipped["osm_id"].astype(str)

source = source.to_crs(epsg=32643)
clipped = clipped.to_crs(epsg=32643)

records = []

for osm_id in SUSPICIOUS_IDS:

    original = source[
        source["osm_id_check"] == osm_id
    ]

    result = clipped[
        clipped["osm_id_check"] == osm_id
    ]

    print("\n" + "-" * 70)
    print("OSM ID:", osm_id)
    print("-" * 70)

    if original.empty:
        print("Not found in original dataset.")
        continue

    original_row = original.iloc[0]

    original_area = (
        original_row.geometry.area / 1_000_000
    )

    print(f"Original area: {original_area:.3f} km²")
    print("Original bounds:", original.total_bounds)

    # Show all available non-geometry attributes
    attributes = original.drop(
        columns=["geometry", "osm_id_check"]
    ).iloc[0]

    print("\nOSM attributes:")

    for field, value in attributes.items():

        if pd.notna(value):
            print(f"{field}: {value}")

    if result.empty:

        print("\nNo clipped feature found.")
        clipped_area = 0

    else:

        clipped_area = (
            result.geometry.area.sum() / 1_000_000
        )

        print("\nClipped feature count:", len(result))
        print(f"Clipped area: {clipped_area:.3f} km²")
        print("Clipped bounds:", result.total_bounds)

    records.append({
        "osm_id": osm_id,
        "original_area_km2": original_area,
        "clipped_area_km2": clipped_area,
        "clipped_feature_count": len(result),
        "landuse": original_row.get("landuse"),
        "name": original_row.get("name"),
        "industrial": original_row.get("industrial"),
        "residential": original_row.get("residential"),
        "type": original_row.get("type")
    })


# Save investigation results
report = pd.DataFrame(records)

output_file = OUTPUT_DIR / "Large_Landuse_Investigation.csv"

report.to_csv(output_file, index=False)

print("\n" + "=" * 70)
print("INVESTIGATION COMPLETED")
print("Report:", output_file)
print("=" * 70)
