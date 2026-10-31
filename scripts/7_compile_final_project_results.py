
from pathlib import Path
import pandas as pd
import numpy as np

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
    )
}

# ============================================================
# 2. VERIFY INPUT FILES
# ============================================================

print("=" * 70)
print("JAIPUR SAR PROJECT — FINAL RESULTS COMPILATION")
print("=" * 70)

missing = []

for name, path in FILES.items():
    if path.exists():
        print(f"FOUND: {name}")
    else:
        print(f"MISSING: {name} -> {path}")
        missing.append(name)

if missing:
    raise FileNotFoundError(
        "Required reports are missing: "
        + ", ".join(missing)
    )

# ============================================================
# 3. READ REPORTS
# ============================================================

data = {}

for name, path in FILES.items():
    data[name] = pd.read_csv(path)

print("\nAll five source reports loaded successfully.")

# ============================================================
# 4. CONSOLIDATED METRIC COLLECTION
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


# ------------------------------------------------------------
# A. SAR COVERAGE
# ------------------------------------------------------------

coverage = data["sar_coverage"]

row = coverage.iloc[0]

add_metric(
    "SAR Coverage",
    "Municipal rasterized area",
    row["municipal_raster_area_km2"],
    "km²",
    "SAR_Common_Municipal_Coverage.csv"
)

add_metric(
    "SAR Coverage",
    "Common valid pixels",
    row["common_valid_pixels"],
    "pixels",
    "SAR_Common_Municipal_Coverage.csv"
)

add_metric(
    "SAR Coverage",
    "Common valid area",
    row["common_valid_area_km2"],
    "km²",
    "SAR_Common_Municipal_Coverage.csv"
)

add_metric(
    "SAR Coverage",
    "Common municipal coverage",
    row["common_coverage_percentage"],
    "%",
    "SAR_Common_Municipal_Coverage.csv"
)

# Individual date and polarization coverage

for _, r in data["temporal_statistics"].iloc[0:0].iterrows():
    pass

# The individual acquisition coverage is reported separately
# in the original SAR_Municipal_Coverage_By_Date.csv.

individual_coverage_file = (
    PROJECT / "reports" / "sar_coverage_analysis"
    / "SAR_Municipal_Coverage_By_Date.csv"
)

if individual_coverage_file.exists():

    individual = pd.read_csv(individual_coverage_file)

    for _, r in individual.iterrows():

        add_metric(
            "SAR Coverage",
            f"{int(r['year'])} {r['polarization']} coverage",
            r["coverage_percentage"],
            "%",
            "SAR_Municipal_Coverage_By_Date.csv"
        )


# ------------------------------------------------------------
# B. TEMPORAL SAR CHANGE STATISTICS
# ------------------------------------------------------------

temporal = data["temporal_statistics"]

for _, r in temporal.iterrows():

    feature = r["feature"]

    add_metric(
        "Temporal SAR Change",
        f"{feature} median change",
        r["median_change_db"],
        "dB",
        "SAR_Temporal_Change_Statistics.csv"
    )

    add_metric(
        "Temporal SAR Change",
        f"{feature} 5th percentile",
        r["p05_db"],
        "dB",
        "SAR_Temporal_Change_Statistics.csv"
    )

    add_metric(
        "Temporal SAR Change",
        f"{feature} 95th percentile",
        r["p95_db"],
        "dB",
        "SAR_Temporal_Change_Statistics.csv"
    )


# ------------------------------------------------------------
# C. SPATIAL CHANGE CLUSTERS
# ------------------------------------------------------------

clusters = data["cluster_statistics"]

total_clusters = len(clusters)

total_cluster_area = clusters["area_km2"].sum()

largest_cluster = clusters["area_hectares"].max()

median_cluster = clusters["area_hectares"].median()

add_metric(
    "SAR Change Clusters",
    "Retained cluster count",
    total_clusters,
    "clusters",
    "SAR_Joint_Change_Cluster_Statistics.csv"
)

add_metric(
    "SAR Change Clusters",
    "Total retained candidate area",
    total_cluster_area,
    "km²",
    "SAR_Joint_Change_Cluster_Statistics.csv"
)

add_metric(
    "SAR Change Clusters",
    "Largest candidate cluster",
    largest_cluster,
    "hectares",
    "SAR_Joint_Change_Cluster_Statistics.csv"
)

add_metric(
    "SAR Change Clusters",
    "Median candidate cluster area",
    median_cluster,
    "hectares",
    "SAR_Joint_Change_Cluster_Statistics.csv"
)


# ------------------------------------------------------------
# D. OSM COMPARISON
# ------------------------------------------------------------

osm = data["osm_comparison"].iloc[0]

add_metric(
    "OSM Comparison",
    "Current OSM buildings in municipality",
    osm["current_osm_buildings_in_municipality"],
    "features",
    "SAR_Cluster_OSM_Overall_Summary.csv"
)

add_metric(
    "OSM Comparison",
    "Current OSM land-use features in municipality",
    osm["current_osm_landuse_features_in_municipality"],
    "features",
    "SAR_Cluster_OSM_Overall_Summary.csv"
)

add_metric(
    "OSM Comparison",
    "SAR candidate area overlapping current OSM buildings",
    osm["current_osm_building_overlap_km2"],
    "km²",
    "SAR_Cluster_OSM_Overall_Summary.csv"
)

add_metric(
    "OSM Comparison",
    "SAR candidate area overlapping current OSM buildings",
    osm["current_osm_building_overlap_percentage"],
    "%",
    "SAR_Cluster_OSM_Overall_Summary.csv"
)


# ------------------------------------------------------------
# E. OSM MUNICIPAL SPATIAL COVERAGE
# ------------------------------------------------------------

osm_municipal = data["osm_municipal"]

for _, r in osm_municipal.iterrows():

    category = r["category"]

    add_metric(
        "OSM Municipal Coverage",
        f"{category} feature count",
        r["municipal_feature_count"],
        "features",
        "OSM_Municipal_Spatial_Coverage.csv"
    )

    add_metric(
        "OSM Municipal Coverage",
        f"{category} mapped area",
        r["mapped_area_km2"],
        "km²",
        "OSM_Municipal_Spatial_Coverage.csv"
    )

    add_metric(
        "OSM Municipal Coverage",
        f"{category} municipal coverage",
        r["municipal_coverage_percentage"],
        "%",
        "OSM_Municipal_Spatial_Coverage.csv"
    )


# ============================================================
# 5. CREATE MASTER RESULTS CSV
# ============================================================

master = pd.DataFrame(metrics)

master_file = (
    OUTPUT_DIR / "Jaipur_SAR_Final_Results.csv"
)

master.to_csv(master_file, index=False)


# ============================================================
# 6. CREATE TECHNICAL SUMMARY TXT
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
    f.write("Analysis type: Multi-temporal SAR change analysis\n\n")

    f.write("1. SAR COVERAGE\n")
    f.write("-" * 75 + "\n")

    for _, r in master[
        master["category"] == "SAR Coverage"
    ].iterrows():

        f.write(
            f"{r['metric']}: {r['value']} {r['unit']}\n"
        )

    f.write("\n2. TEMPORAL SAR CHANGE\n")
    f.write("-" * 75 + "\n")

    for _, r in master[
        master["category"] == "Temporal SAR Change"
    ].iterrows():

        f.write(
            f"{r['metric']}: {r['value']:.4f} {r['unit']}\n"
        )

    f.write("\n3. SPATIAL CHANGE CLUSTERS\n")
    f.write("-" * 75 + "\n")

    for _, r in master[
        master["category"] == "SAR Change Clusters"
    ].iterrows():

        f.write(
            f"{r['metric']}: {r['value']:.4f} {r['unit']}\n"
        )

    f.write("\n4. OSM REFERENCE COMPARISON\n")
    f.write("-" * 75 + "\n")

    for _, r in master[
        master["category"] == "OSM Comparison"
    ].iterrows():

        f.write(
            f"{r['metric']}: {r['value']} {r['unit']}\n"
        )

    f.write("\n5. OSM MUNICIPAL COVERAGE\n")
    f.write("-" * 75 + "\n")

    for _, r in master[
        master["category"] == "OSM Municipal Coverage"
    ].iterrows():

        f.write(
            f"{r['metric']}: {r['value']} {r['unit']}\n"
        )

    f.write("\n6. INTERPRETATION AND LIMITATIONS\n")
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

    f.write("\n7. SOURCE REPORTS\n")
    f.write("-" * 75 + "\n")

    for name, path in FILES.items():
        f.write(f"{name}: {path.name}\n")

    f.write("\n" + "=" * 75 + "\n")
    f.write("END OF CONSOLIDATED RESULTS\n")
    f.write("=" * 75 + "\n")


# ============================================================
# 7. FINAL OUTPUT
# ============================================================

print("\n" + "=" * 70)
print("FINAL RESULTS COMPILATION COMPLETED")
print("=" * 70)

print(f"\nTotal consolidated metrics: {len(master)}")

print("\nCategory counts:")
print(master["category"].value_counts().to_string())

print("\nGenerated files:")
print(master_file)
print(summary_file)

print("\nOriginal source reports were not modified.")
