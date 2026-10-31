
from pathlib import Path
import pandas as pd

# ============================================================
# 1. PROJECT CONFIGURATION
# ============================================================

PROJECT = Path(
    r"C:\Users\ssat-\Documents\RemoteSensing_Projects"
    r"\Project_02_Jaipur_SAR_Urban_Expansion"
)

OUTPUT_DIR = PROJECT / "reports" / "final_results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FILES = {
    "sar_coverage": (
        PROJECT / "reports" / "sar_coverage_analysis"
        / "SAR_Common_Municipal_Coverage.csv"
    ),

    "temporal_statistics": (
        PROJECT / "reports" / "sar_coverage_analysis"
        / "SAR_Temporal_Change_Statistics.csv"
    ),

    "cluster_statistics": (
        PROJECT / "reports" / "change_detection"
        / "SAR_Joint_Change_Cluster_Statistics.csv"
    ),

    "osm_comparison": (
        PROJECT / "reports" / "change_detection"
        / "osm_comparison"
        / "SAR_Cluster_OSM_Overall_Summary.csv"
    ),

    "osm_municipal": (
        PROJECT / "reports" / "osm_quality_analysis"
        / "OSM_Municipal_Spatial_Coverage.csv"
    ),

    "individual_coverage": (
        PROJECT / "reports" / "sar_coverage_analysis"
        / "SAR_Municipal_Coverage_By_Date.csv"
    )
}

# ============================================================
# 2. VERIFY AND LOAD INPUT FILES
# ============================================================

print("=" * 70)
print("JAIPUR SAR PROJECT — FINAL RESULTS COMPILATION")
print("=" * 70)

data = {}

for name, path in FILES.items():

    if path.exists():
        data[name] = pd.read_csv(path)
        print(f"FOUND: {name}")

    elif name == "individual_coverage":
        print(f"OPTIONAL REPORT NOT FOUND: {name}")

    else:
        raise FileNotFoundError(
            f"Required report missing: {path}"
        )

print("\nSource reports loaded successfully.")

# ============================================================
# 3. REQUIRED COLUMN VALIDATION
# ============================================================

required_columns = {
    "sar_coverage": [
        "municipal_raster_area_km2",
        "common_valid_pixels",
        "common_valid_area_km2",
        "common_coverage_percentage"
    ],

    "temporal_statistics": [
        "feature",
        "valid_pixels",
        "mean_change_db",
        "median_change_db",
        "std_change_db",
        "p05_change_db",
        "p95_change_db"
    ],

    "cluster_statistics": [
        "cluster_id",
        "pixel_count",
        "area_hectares",
        "area_km2",
        "mean_vv_change_db",
        "mean_vh_change_db"
    ],

    "osm_comparison": [
        "cluster_count",
        "total_cluster_area_km2",
        "current_osm_building_overlap_km2",
        "current_osm_building_overlap_percentage",
        "current_osm_buildings_in_municipality",
        "current_osm_landuse_features_in_municipality"
    ],

    "osm_municipal": [
        "category",
        "municipal_feature_count",
        "mapped_area_km2",
        "municipal_coverage_percentage"
    ]
}

for name, columns in required_columns.items():

    missing = [
        col for col in columns
        if col not in data[name].columns
    ]

    if missing:
        raise ValueError(
            f"{name} is missing columns: {missing}"
        )

print("Column validation: PASS")

# ============================================================
# 4. METRIC COLLECTION
# ============================================================

metrics = []

def add_metric(category, metric, value, unit, source):

    metrics.append({
        "category": category,
        "metric": metric,
        "value": value,
        "unit": unit,
        "source_report": source
    })


# ============================================================
# 5. SAR COVERAGE
# ============================================================

coverage = data["sar_coverage"].iloc[0]

coverage_metrics = [
    (
        "Municipal rasterized area",
        coverage["municipal_raster_area_km2"],
        "km²"
    ),
    (
        "Common valid pixels",
        coverage["common_valid_pixels"],
        "pixels"
    ),
    (
        "Common valid area",
        coverage["common_valid_area_km2"],
        "km²"
    ),
    (
        "Common municipal coverage",
        coverage["common_coverage_percentage"],
        "%"
    )
]

for name, value, unit in coverage_metrics:

    add_metric(
        "SAR Coverage",
        name,
        value,
        unit,
        "SAR_Common_Municipal_Coverage.csv"
    )


# Individual acquisition coverage

if "individual_coverage" in data:

    for _, row in data["individual_coverage"].iterrows():

        add_metric(
            "SAR Coverage",
            f"{int(row['year'])} {row['polarization']} coverage",
            row["coverage_percentage"],
            "%",
            "SAR_Municipal_Coverage_By_Date.csv"
        )


# ============================================================
# 6. TEMPORAL SAR CHANGE STATISTICS
# ============================================================

temporal = data["temporal_statistics"]

for _, row in temporal.iterrows():

    feature = row["feature"]

    statistics = [
        ("Mean", row["mean_change_db"]),
        ("Median", row["median_change_db"]),
        ("Standard deviation", row["std_change_db"]),
        ("5th percentile", row["p05_change_db"]),
        ("95th percentile", row["p95_change_db"])
    ]

    for statistic, value in statistics:

        add_metric(
            "Temporal SAR Change",
            f"{feature} — {statistic}",
            value,
            "dB",
            "SAR_Temporal_Change_Statistics.csv"
        )

    add_metric(
        "Temporal SAR Change",
        f"{feature} — valid pixels",
        row["valid_pixels"],
        "pixels",
        "SAR_Temporal_Change_Statistics.csv"
    )


# ============================================================
# 7. SPATIAL CHANGE CLUSTERS
# ============================================================

clusters = data["cluster_statistics"]

cluster_count = len(clusters)

total_cluster_area = clusters["area_km2"].sum()

largest_cluster = clusters["area_hectares"].max()

median_cluster = clusters["area_hectares"].median()

cluster_metrics = [
    ("Retained cluster count", cluster_count, "clusters"),
    ("Total retained candidate area", total_cluster_area, "km²"),
    ("Largest candidate cluster", largest_cluster, "hectares"),
    ("Median candidate cluster area", median_cluster, "hectares")
]

for name, value, unit in cluster_metrics:

    add_metric(
        "SAR Change Clusters",
        name,
        value,
        unit,
        "SAR_Joint_Change_Cluster_Statistics.csv"
    )


# ============================================================
# 8. OSM COMPARISON
# ============================================================

osm = data["osm_comparison"].iloc[0]

osm_metrics = [
    (
        "Current OSM buildings in municipality",
        osm["current_osm_buildings_in_municipality"],
        "features"
    ),
    (
        "Current OSM land-use features in municipality",
        osm["current_osm_landuse_features_in_municipality"],
        "features"
    ),
    (
        "Candidate area overlapping current OSM buildings",
        osm["current_osm_building_overlap_km2"],
        "km²"
    ),
    (
        "Candidate area overlapping current OSM buildings",
        osm["current_osm_building_overlap_percentage"],
        "%"
    )
]

for name, value, unit in osm_metrics:

    add_metric(
        "OSM Comparison",
        name,
        value,
        unit,
        "SAR_Cluster_OSM_Overall_Summary.csv"
    )


# ============================================================
# 9. OSM MUNICIPAL COVERAGE
# ============================================================

osm_municipal = data["osm_municipal"]

for _, row in osm_municipal.iterrows():

    category = row["category"]

    add_metric(
        "OSM Municipal Coverage",
        f"{category} feature count",
        row["municipal_feature_count"],
        "features",
        "OSM_Municipal_Spatial_Coverage.csv"
    )

    add_metric(
        "OSM Municipal Coverage",
        f"{category} mapped area",
        row["mapped_area_km2"],
        "km²",
        "OSM_Municipal_Spatial_Coverage.csv"
    )

    add_metric(
        "OSM Municipal Coverage",
        f"{category} municipal coverage",
        row["municipal_coverage_percentage"],
        "%",
        "OSM_Municipal_Spatial_Coverage.csv"
    )


# ============================================================
# 10. SAVE MASTER RESULTS CSV
# ============================================================

master = pd.DataFrame(metrics)

master_file = (
    OUTPUT_DIR / "Jaipur_SAR_Final_Results.csv"
)

master.to_csv(master_file, index=False)


# ============================================================
# 11. GENERATE TECHNICAL SUMMARY
# ============================================================

summary_file = (
    OUTPUT_DIR / "Jaipur_SAR_Final_Results.txt"
)

with open(summary_file, "w", encoding="utf-8") as f:

    f.write("=" * 75 + "\n")
    f.write("JAIPUR SAR-BASED URBAN CHANGE ANALYSIS\n")
    f.write("CONSOLIDATED PROJECT RESULTS\n")
    f.write("=" * 75 + "\n\n")

    f.write("STUDY OVERVIEW\n")
    f.write("-" * 75 + "\n")

    f.write("Study area: Jaipur Municipal Corporation boundary\n")
    f.write("Sensor: Sentinel-1A SAR\n")
    f.write("Acquisition years: 2016, 2020 and 2025\n")
    f.write("Polarizations: VV and VH\n")
    f.write("Raster resolution: 10 m\n")
    f.write("Projected CRS: EPSG:32643\n")
    f.write("Feature bands: 15\n")
    f.write("Analysis: Multi-temporal SAR backscatter change\n\n")

    categories = [
        "SAR Coverage",
        "Temporal SAR Change",
        "SAR Change Clusters",
        "OSM Comparison",
        "OSM Municipal Coverage"
    ]

    for category in categories:

        f.write("\n" + category.upper() + "\n")
        f.write("-" * 75 + "\n")

        subset = master[
            master["category"] == category
        ]

        for _, row in subset.iterrows():

            value = row["value"]

            if isinstance(value, (int, float)):
                value_text = f"{value:,.4f}"
            else:
                value_text = str(value)

            f.write(
                f"{row['metric']}: "
                f"{value_text} {row['unit']}\n"
            )

    f.write("\nINTERPRETATION AND LIMITATIONS\n")
    f.write("-" * 75 + "\n")

    f.write(
        "The detected SAR clusters represent exploratory "
        "backscatter-change candidates.\n"
    )

    f.write(
        "They are not independently verified urban expansion "
        "or construction labels.\n"
    )

    f.write(
        "Current OpenStreetMap data were used as spatial "
        "reference information.\n"
    )

    f.write(
        "Current OSM building footprints do not establish "
        "the historical presence or absence of buildings "
        "in 2016 or 2020.\n"
    )

    f.write(
        "The percentage of SAR candidate area overlapping "
        "current OSM buildings is a spatial overlap statistic, "
        "not a classification accuracy score.\n"
    )

    f.write(
        "Further historical imagery interpretation and "
        "independent validation are required before claiming "
        "quantified urban expansion.\n"
    )

    f.write("\nSOURCE REPORTS\n")
    f.write("-" * 75 + "\n")

    for name, path in FILES.items():

        if path.exists():
            f.write(f"{name}: {path.name}\n")

    f.write("\n" + "=" * 75 + "\n")
    f.write("END OF CONSOLIDATED RESULTS\n")
    f.write("=" * 75 + "\n")


# ============================================================
# 12. FINAL VERIFICATION
# ============================================================

print("\n" + "=" * 70)
print("FINAL RESULTS COMPILATION COMPLETED")
print("=" * 70)

print(f"Consolidated metrics: {len(master)}")

print("\nCategory counts:")
print(master["category"].value_counts().to_string())

print("\nGenerated files:")

for path in [master_file, summary_file]:

    if path.exists():
        print(f"VERIFIED: {path}")
    else:
        raise RuntimeError(f"Output missing: {path}")

print("\nOriginal source reports were not modified.")
