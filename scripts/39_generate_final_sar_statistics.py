
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.features import geometry_mask
from shapely.geometry import mapping
import matplotlib.pyplot as plt


# ============================================================
# 1. PROJECT CONFIGURATION
# ============================================================

PROJECT = Path(
    r"C:\Users\ssat-\Documents\RemoteSensing_Projects"
    r"\Project_02_Jaipur_SAR_Urban_Expansion"
)

BOUNDARY_FILE = (
    PROJECT / "data" / "boundaries"
    / "Jaipur_JMC_Municipal_Boundary.geojson"
)

ALIGNED_DIR = (
    PROJECT / "data" / "processed" / "aligned_utm43n"
)

CLUSTER_FILE = (
    PROJECT / "data" / "processed"
    / "change_detection" / "spatial_clusters"
    / "SAR_Joint_Change_Clusters.gpkg"
)

OUTPUT = PROJECT / "reports" / "final_statistics_v2"
OUTPUT.mkdir(parents=True, exist_ok=True)

YEARS = [2016, 2020, 2025]
POLARIZATIONS = ["VV", "VH"]

PIXEL_AREA_KM2 = 0.0001  # 10 m x 10 m


# ============================================================
# 2. LOAD MUNICIPAL BOUNDARY
# ============================================================

print("\nLoading municipal boundary...")

boundary = gpd.read_file(BOUNDARY_FILE).to_crs("EPSG:32643")

municipal = boundary.geometry.union_all()

municipal_area_km2 = municipal.area / 1_000_000

print(f"Municipal area: {municipal_area_km2:.4f} km²")


# ============================================================
# 3. LOAD AND ALIGNMENT-CHECK SAR RASTERS
# ============================================================

def get_path(year, pol):
    return (
        ALIGNED_DIR
        / f"Jaipur_S1_{year}_{pol}_UTM43N_10m.tif"
    )


def load_stack(pol):

    stack = []
    reference_shape = None
    reference_transform = None
    reference_crs = None
    municipal_mask = None

    for year in YEARS:

        path = get_path(year, pol)

        if not path.exists():
            raise FileNotFoundError(path)

        with rasterio.open(path) as src:

            if reference_shape is None:

                reference_shape = (src.height, src.width)
                reference_transform = src.transform
                reference_crs = src.crs

                municipal_mask = geometry_mask(
                    [mapping(municipal)],
                    out_shape=reference_shape,
                    transform=reference_transform,
                    invert=True
                )

            else:

                if (src.height, src.width) != reference_shape:
                    raise ValueError("Raster dimensions differ.")

                if src.transform != reference_transform:
                    raise ValueError("Raster transforms differ.")

                if src.crs != reference_crs:
                    raise ValueError("Raster CRS differs.")

            data = src.read(1, masked=True).astype("float32")
            arr = np.asarray(data.filled(np.nan))

            arr[~np.isfinite(arr)] = np.nan
            arr[~municipal_mask] = np.nan

            valid = np.isfinite(arr)

            if np.any(arr[valid] <= 0):
                raise ValueError(
                    f"Non-positive linear Sigma0 values in {path}"
                )

            # Convert linear Sigma0 to dB.
            arr[valid] = 10 * np.log10(arr[valid])

            stack.append(arr)

    return np.stack(stack), municipal_mask


print("Loading VV stack...")
vv, municipal_mask = load_stack("VV")

print("Loading VH stack...")
vh, _ = load_stack("VH")

print("Raster dimensions:", vv.shape)
print("Valid municipal grid cells:", int(municipal_mask.sum()))


# ============================================================
# 4. TEMPORAL BACKSCATTER STATISTICS
# ============================================================

def describe_array(arr):

    values = arr[np.isfinite(arr)]

    if len(values) == 0:
        raise ValueError("No valid pixels found.")

    return {
        "valid_pixels": len(values),
        "mean_db": np.mean(values),
        "median_db": np.median(values),
        "std_db": np.std(values),
        "minimum_db": np.min(values),
        "maximum_db": np.max(values),
        "p05_db": np.percentile(values, 5),
        "p25_db": np.percentile(values, 25),
        "p75_db": np.percentile(values, 75),
        "p95_db": np.percentile(values, 95)
    }


annual_rows = []

for pol, stack in [("VV", vv), ("VH", vh)]:

    for i, year in enumerate(YEARS):

        stats = describe_array(stack[i])

        stats["polarization"] = pol
        stats["year"] = year

        annual_rows.append(stats)

annual_df = pd.DataFrame(annual_rows)

annual_df = annual_df[
    [
        "year", "polarization", "valid_pixels",
        "mean_db", "median_db", "std_db",
        "minimum_db", "maximum_db",
        "p05_db", "p25_db", "p75_db", "p95_db"
    ]
]

annual_df.to_csv(
    OUTPUT / "01_Annual_Backscatter_Statistics.csv",
    index=False
)


# ============================================================
# 5. TEMPORAL CHANGE STATISTICS
# ============================================================

periods = [
    (0, 1, "2016_2020", 4),
    (1, 2, "2020_2025", 5),
    (0, 2, "2016_2025", 9)
]

change_rows = []

for pol, stack in [("VV", vv), ("VH", vh)]:

    for start, end, label, years_elapsed in periods:

        change = stack[end] - stack[start]

        stats = describe_array(change)

        values = change[np.isfinite(change)]

        stats["polarization"] = pol
        stats["period"] = label
        stats["years_elapsed"] = years_elapsed

        stats["increase_pixels"] = int(
            np.sum(values > 0)
        )

        stats["decrease_pixels"] = int(
            np.sum(values < 0)
        )

        stats["unchanged_pixels"] = int(
            np.sum(values == 0)
        )

        stats["increase_percent"] = (
            100 * stats["increase_pixels"] / len(values)
        )

        stats["decrease_percent"] = (
            100 * stats["decrease_pixels"] / len(values)
        )

        stats["mean_change_per_year_db"] = (
            stats["mean_db"] / years_elapsed
        )

        stats["median_change_per_year_db"] = (
            stats["median_db"] / years_elapsed
        )

        change_rows.append(stats)

change_df = pd.DataFrame(change_rows)

change_df.to_csv(
    OUTPUT / "02_Temporal_Change_Statistics.csv",
    index=False
)


# ============================================================
# 6. PIXEL-WISE VV/VH CORRELATION
# ============================================================

correlation_rows = []

rng = np.random.default_rng(42)

for i, year in enumerate(YEARS):

    valid = (
        np.isfinite(vv[i])
        & np.isfinite(vh[i])
    )

    vv_values = vv[i][valid]
    vh_values = vh[i][valid]

    correlation = np.corrcoef(
        vv_values,
        vh_values
    )[0, 1]

    # Random sample for a readable scatter plot.
    sample_size = min(30000, len(vv_values))

    sample_idx = rng.choice(
        len(vv_values),
        size=sample_size,
        replace=False
    )

    correlation_rows.append({
        "year": year,
        "valid_pixels": len(vv_values),
        "vv_vh_pearson_correlation": correlation
    })

    plt.figure(figsize=(7, 6))

    plt.scatter(
        vv_values[sample_idx],
        vh_values[sample_idx],
        s=2,
        alpha=0.15
    )

    plt.xlabel("VV backscatter (dB)")
    plt.ylabel("VH backscatter (dB)")

    plt.title(
        f"Jaipur VV–VH Backscatter Relationship — {year}\n"
        f"Pearson correlation = {correlation:.3f}"
    )

    plt.grid(alpha=0.2)
    plt.tight_layout()

    plt.savefig(
        OUTPUT / f"VV_VH_Correlation_{year}.png",
        dpi=300
    )

    plt.close()


correlation_df = pd.DataFrame(correlation_rows)

correlation_df.to_csv(
    OUTPUT / "03_VV_VH_Correlation.csv",
    index=False
)


# ============================================================
# 7. SAR CHANGE CANDIDATE STATISTICS
# ============================================================

print("\nLoading candidate clusters...")

clusters = gpd.read_file(
    CLUSTER_FILE,
    layer="change_clusters"
).to_crs("EPSG:32643")

clusters = clusters[
    clusters.geometry.notna()
    & ~clusters.geometry.is_empty
].copy()

clusters["area_km2"] = (
    clusters.geometry.area / 1_000_000
)

clusters["area_hectares"] = (
    clusters["area_km2"] * 100
)

total_cluster_area = clusters["area_km2"].sum()

cluster_summary = {
    "cluster_count": len(clusters),
    "total_cluster_area_km2": total_cluster_area,
    "mean_cluster_area_ha": clusters["area_hectares"].mean(),
    "median_cluster_area_ha": clusters["area_hectares"].median(),
    "minimum_cluster_area_ha": clusters["area_hectares"].min(),
    "maximum_cluster_area_ha": clusters["area_hectares"].max(),
    "total_municipal_area_km2": municipal_area_km2,
    "cluster_area_percent_of_municipality": (
        100 * total_cluster_area / municipal_area_km2
    )
}

pd.DataFrame([cluster_summary]).to_csv(
    OUTPUT / "04_Cluster_Summary.csv",
    index=False
)

clusters.sort_values(
    "area_hectares",
    ascending=False
).to_csv(
    OUTPUT / "05_Individual_Cluster_Areas.csv",
    index=False
)


# ============================================================
# 8. CHANGE THRESHOLD DISTRIBUTION
# ============================================================

vv_change = vv[2] - vv[0]
vh_change = vh[2] - vh[0]

valid = (
    np.isfinite(vv_change)
    & np.isfinite(vh_change)
)

vv_valid = vv_change[valid]
vh_valid = vh_change[valid]

vv_threshold = np.percentile(vv_valid, 95)
vh_threshold = np.percentile(vh_valid, 95)

joint_mask = (
    (vv_change > vv_threshold)
    & (vh_change > vh_threshold)
    & valid
)

joint_pixels = int(joint_mask.sum())
joint_area = joint_pixels * PIXEL_AREA_KM2

threshold_summary = pd.DataFrame([{
    "vv_p95_threshold_db": vv_threshold,
    "vh_p95_threshold_db": vh_threshold,
    "joint_candidate_pixels": joint_pixels,
    "joint_candidate_area_km2": joint_area,
    "joint_candidate_percent_of_municipality": (
        100 * joint_area / municipal_area_km2
    )
}])

threshold_summary.to_csv(
    OUTPUT / "06_Joint_Change_Threshold_Statistics.csv",
    index=False
)


# ============================================================
# 9. GRAPH 1 — ANNUAL MEDIAN BACKSCATTER
# ============================================================

fig, ax = plt.subplots(figsize=(9, 6))

for pol in POLARIZATIONS:

    subset = annual_df[
        annual_df["polarization"] == pol
    ]

    ax.plot(
        subset["year"],
        subset["median_db"],
        marker="o",
        linewidth=2,
        markersize=8,
        label=pol
    )

ax.set_title(
    "Jaipur — Median Sentinel-1 Backscatter Trend",
    fontweight="bold"
)

ax.set_xlabel("Year")
ax.set_ylabel("Median backscatter (dB)")

ax.set_xticks(YEARS)
ax.grid(alpha=0.3)
ax.legend(title="Polarization")

plt.tight_layout()

plt.savefig(
    OUTPUT / "Graph_01_Annual_Backscatter_Trends.png",
    dpi=300
)

plt.close()


# ============================================================
# 10. GRAPH 2 — TEMPORAL CHANGE BY PERIOD
# ============================================================

fig, axes = plt.subplots(
    1, 2,
    figsize=(13, 5)
)

for ax, pol in zip(axes, POLARIZATIONS):

    subset = change_df[
        change_df["polarization"] == pol
    ]

    ax.bar(
        subset["period"],
        subset["median_db"]
    )

    ax.axhline(0, color="black", linewidth=0.8)

    ax.set_title(f"{pol} Median Backscatter Change")
    ax.set_ylabel("Median change (dB)")
    ax.grid(axis="y", alpha=0.25)

plt.suptitle(
    "Temporal SAR Backscatter Change by Period",
    fontweight="bold"
)

plt.tight_layout()

plt.savefig(
    OUTPUT / "Graph_02_Period_Change.png",
    dpi=300
)

plt.close()


# ============================================================
# 11. GRAPH 3 — BACKSCATTER DISTRIBUTIONS
# ============================================================

fig, axes = plt.subplots(
    1, 2,
    figsize=(13, 5)
)

for ax, pol, stack in [
    (axes[0], "VV", vv),
    (axes[1], "VH", vh)
]:

    distributions = [
        stack[i][np.isfinite(stack[i])][::20]
        for i in range(3)
    ]

    ax.boxplot(
        distributions,
        tick_labels=[str(y) for y in YEARS],
        showfliers=False
    )

    ax.set_title(f"{pol} Backscatter Distribution")
    ax.set_xlabel("Year")
    ax.set_ylabel("Backscatter (dB)")
    ax.grid(axis="y", alpha=0.25)

plt.suptitle(
    "Distribution of Sentinel-1 Backscatter",
    fontweight="bold"
)

plt.tight_layout()

plt.savefig(
    OUTPUT / "Graph_03_Backscatter_Distributions.png",
    dpi=300
)

plt.close()


# ============================================================
# 12. GRAPH 4 — CLUSTER AREA DISTRIBUTION
# ============================================================

fig, ax = plt.subplots(figsize=(9, 5))

ax.hist(
    clusters["area_hectares"],
    bins=20,
    edgecolor="black"
)

ax.set_title(
    "Distribution of SAR Change Candidate Cluster Sizes",
    fontweight="bold"
)

ax.set_xlabel("Cluster area (hectares)")
ax.set_ylabel("Number of clusters")
ax.grid(axis="y", alpha=0.25)

plt.tight_layout()

plt.savefig(
    OUTPUT / "Graph_04_Cluster_Area_Distribution.png",
    dpi=300
)

plt.close()


# ============================================================
# 13. GRAPH 5 — CUMULATIVE CLUSTER AREA
# ============================================================

ordered = clusters.sort_values(
    "area_hectares",
    ascending=False
).copy()

ordered["cumulative_area_km2"] = (
    ordered["area_km2"].cumsum()
)

fig, ax = plt.subplots(figsize=(9, 5))

ax.plot(
    np.arange(1, len(ordered) + 1),
    ordered["cumulative_area_km2"],
    linewidth=2
)

ax.set_title(
    "Cumulative Area of SAR Change Candidate Clusters",
    fontweight="bold"
)

ax.set_xlabel("Clusters ranked by area")
ax.set_ylabel("Cumulative area (km²)")
ax.grid(alpha=0.3)

plt.tight_layout()

plt.savefig(
    OUTPUT / "Graph_05_Cumulative_Cluster_Area.png",
    dpi=300
)

plt.close()


# ============================================================
# 14. GRAPH 6 — VV/VH CORRELATION TREND
# ============================================================

fig, ax = plt.subplots(figsize=(8, 5))

ax.plot(
    correlation_df["year"],
    correlation_df["vv_vh_pearson_correlation"],
    marker="o",
    linewidth=2
)

ax.set_title(
    "Temporal Trend in VV–VH Pixel-wise Correlation",
    fontweight="bold"
)

ax.set_xlabel("Year")
ax.set_ylabel("Pearson correlation coefficient")
ax.set_xticks(YEARS)
ax.grid(alpha=0.3)

plt.tight_layout()

plt.savefig(
    OUTPUT / "Graph_06_VV_VH_Correlation.png",
    dpi=300
)

plt.close()


# ============================================================
# 15. GENERATE FINAL TEXT SUMMARY
# ============================================================

summary_file = OUTPUT / "Jaipur_SAR_Statistical_Summary.txt"

with open(summary_file, "w", encoding="utf-8") as f:

    f.write("JAIPUR MULTI-TEMPORAL SENTINEL-1 SAR ANALYSIS\n")
    f.write("=" * 65 + "\n\n")

    f.write("STUDY AREA\n")
    f.write(f"Municipal area: {municipal_area_km2:.4f} km²\n\n")

    f.write("ANNUAL BACKSCATTER STATISTICS\n")
    f.write(annual_df.to_string(index=False))
    f.write("\n\n")

    f.write("TEMPORAL CHANGE STATISTICS\n")
    f.write(change_df.to_string(index=False))
    f.write("\n\n")

    f.write("VV-VH CORRELATION\n")
    f.write(correlation_df.to_string(index=False))
    f.write("\n\n")

    f.write("SAR CHANGE CLUSTER SUMMARY\n")

    for key, value in cluster_summary.items():
        f.write(f"{key}: {value}\n")

    f.write("\nJOINT CHANGE THRESHOLD RESULTS\n")
    f.write(threshold_summary.to_string(index=False))

    f.write("\n\nINTERPRETATION LIMITATION\n")
    f.write(
        "These results describe SAR backscatter behaviour and "
        "statistically selected change candidates. They do not "
        "constitute a validated built-up area classification, "
        "urban expansion estimate or urbanisation rate. "
        "Historical land-cover reference data and independent "
        "validation are required for those claims.\n"
    )


# ============================================================
# 16. FINAL OUTPUT
# ============================================================

print("\n" + "=" * 70)
print("FINAL SAR STATISTICAL ANALYSIS COMPLETED")
print("=" * 70)

print("\nAnnual backscatter statistics:")
print(annual_df.to_string(index=False))

print("\nTemporal change statistics:")
print(change_df.to_string(index=False))

print("\nVV-VH correlation:")
print(correlation_df.to_string(index=False))

print("\nCluster summary:")
print(cluster_summary)

print("\nJoint candidate threshold:")
print(threshold_summary.to_string(index=False))

print("\nAll outputs saved to:")
print(OUTPUT)

print("\nOriginal datasets were not modified.")
