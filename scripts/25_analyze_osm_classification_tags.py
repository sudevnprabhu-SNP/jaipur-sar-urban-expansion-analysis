
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

REPORT_DIR = (
    PROJECT_DIR
    / "reports"
    / "osm_quality_analysis"
)

REPORT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# TAGS TO ANALYZE
# ============================================================

TAG_FIELDS = [
    "landuse",
    "building",
    "amenity",
    "leisure",
    "natural",
    "water",
    "waterway",
    "highway",
    "railway",
    "industrial",
    "military",
    "sport",
    "surface",
    "boundary",
]

# Layers where each tag is likely to be relevant
LAYER_FIELDS = {
    "landuse_polygon": [
        "landuse", "industrial", "military", "natural",
        "boundary"
    ],
    "buildings_polygon": [
        "building", "amenity", "leisure", "military"
    ],
    "roads_line": [
        "highway", "surface"
    ],
    "roads_point": [
        "highway"
    ],
    "open_public_spaces_polygon": [
        "leisure", "landuse", "natural", "sport"
    ],
    "open_public_spaces_point": [
        "leisure", "amenity", "sport"
    ],
    "water_polygons_polygon": [
        "natural", "water", "landuse"
    ],
    "water_lines_line": [
        "waterway"
    ],
    "water_lines_point": [
        "waterway"
    ],
    "landuse_point": [
        "landuse"
    ],
}

# ============================================================
# STORAGE
# ============================================================

distribution_records = []
summary_records = []
layer_summary_records = []

print("=" * 70)
print("OSM CLASSIFICATION TAG ANALYSIS")
print("=" * 70)

layers = gpd.list_layers(GPKG_FILE)["name"].tolist()

# ============================================================
# ANALYZE EACH LAYER
# ============================================================

for layer_name in layers:

    print("\n" + "-" * 70)
    print(f"LAYER: {layer_name}")
    print("-" * 70)

    gdf = gpd.read_file(
        GPKG_FILE,
        layer=layer_name
    )

    total_features = len(gdf)

    print(f"Total features: {total_features:,}")

    relevant_fields = LAYER_FIELDS.get(
        layer_name,
        TAG_FIELDS
    )

    layer_tagged_features = set()

    for field in relevant_fields:

        if field not in gdf.columns:
            continue

        values = (
            gdf[field]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        # Blank values represent missing tags
        non_blank = values[values != ""]

        tagged_count = len(non_blank)
        missing_count = total_features - tagged_count

        unique_categories = non_blank.nunique()

        print(f"\nTag field: {field}")
        print(f"  Tagged features: {tagged_count:,}")
        print(f"  Missing values: {missing_count:,}")
        print(f"  Unique categories: {unique_categories}")

        layer_tagged_features.update(
            non_blank.index.tolist()
        )

        # Category distribution
        counts = non_blank.value_counts()

        for category, count in counts.items():

            percentage = (
                count / total_features * 100
                if total_features > 0
                else 0
            )

            distribution_records.append({
                "layer": layer_name,
                "tag_field": field,
                "category": category,
                "feature_count": int(count),
                "percentage_of_layer": round(percentage, 3)
            })

        summary_records.append({
            "layer": layer_name,
            "tag_field": field,
            "total_features": total_features,
            "tagged_features": tagged_count,
            "missing_values": missing_count,
            "unique_categories": unique_categories,
            "tag_coverage_percentage": round(
                tagged_count / total_features * 100,
                3
            ) if total_features else 0
        })

    layer_summary_records.append({
        "layer": layer_name,
        "total_features": total_features,
        "features_with_any_relevant_tag": len(layer_tagged_features),
        "features_without_any_relevant_tag": (
            total_features - len(layer_tagged_features)
        )
    })

# ============================================================
# SAVE REPORTS
# ============================================================

distribution_df = pd.DataFrame(distribution_records)
summary_df = pd.DataFrame(summary_records)
layer_summary_df = pd.DataFrame(layer_summary_records)

distribution_file = (
    REPORT_DIR / "OSM_Tag_Category_Distribution.csv"
)

summary_file = (
    REPORT_DIR / "OSM_Tag_Coverage_Summary.csv"
)

layer_summary_file = (
    REPORT_DIR / "OSM_Layer_Tag_Completeness.csv"
)

distribution_df.to_csv(
    distribution_file,
    index=False
)

summary_df.to_csv(
    summary_file,
    index=False
)

layer_summary_df.to_csv(
    layer_summary_file,
    index=False
)

# ============================================================
# PRINT IMPORTANT CATEGORY DISTRIBUTIONS
# ============================================================

print("\n" + "=" * 70)
print("IMPORTANT TAG DISTRIBUTIONS")
print("=" * 70)

important_fields = [
    "landuse",
    "building",
    "highway",
    "amenity",
    "leisure",
    "natural",
    "water",
    "waterway",
    "industrial",
    "military",
]

for field in important_fields:

    selected = distribution_df[
        distribution_df["tag_field"] == field
    ]

    if selected.empty:
        continue

    print(f"\n{field.upper()}")

    totals = (
        selected.groupby("category")["feature_count"]
        .sum()
        .sort_values(ascending=False)
    )

    for category, count in totals.items():

        print(f"  {category}: {count:,}")

# ============================================================
# FINAL OUTPUT
# ============================================================

print("\n" + "=" * 70)
print("ANALYSIS COMPLETED")
print("=" * 70)

print("\nReports generated:")

print(distribution_file)
print(summary_file)
print(layer_summary_file)

print("\nTotal category records:", len(distribution_df))
print("Total tag coverage records:", len(summary_df))

print("\nOriginal and processed GeoPackages were not modified.")
