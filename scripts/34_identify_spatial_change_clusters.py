
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
import matplotlib.pyplot as plt
from shapely.geometry import shape

from scipy.ndimage import label
from rasterio.features import shapes

# ============================================================
# 1. PATHS AND SETTINGS
# ============================================================

PROJECT_DIR = Path(
    r"C:\Users\ssat-\Documents\RemoteSensing_Projects"
    r"\Project_02_Jaipur_SAR_Urban_Expansion"
)

CHANGE_DIR = (
    PROJECT_DIR
    / "data"
    / "processed"
    / "change_detection"
)

OUTPUT_DIR = (
    PROJECT_DIR
    / "data"
    / "processed"
    / "change_detection"
    / "spatial_clusters"
)

REPORT_DIR = (
    PROJECT_DIR
    / "reports"
    / "change_detection"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

VV_FILE = CHANGE_DIR / "VV_2016_2025_continuous.tif"
VH_FILE = CHANGE_DIR / "VH_2016_2025_continuous.tif"

PERCENTILE = 95
MIN_PATCH_PIXELS = 50

NODATA = -9999.0

# ============================================================
# 2. LOAD AND CHECK RASTERS
# ============================================================

print("=" * 70)
print("SPATIAL SAR CHANGE CLUSTER ANALYSIS")
print("=" * 70)

with rasterio.open(VV_FILE) as vv_src, rasterio.open(VH_FILE) as vh_src:

    if (
        vv_src.crs != vh_src.crs
        or vv_src.transform != vh_src.transform
        or vv_src.shape != vh_src.shape
    ):
        raise ValueError("VV and VH change rasters are not aligned.")

    vv_data = vv_src.read(1, masked=True)
    vh_data = vh_src.read(1, masked=True)

    vv = np.asarray(vv_data.data, dtype=np.float32)
    vh = np.asarray(vh_data.data, dtype=np.float32)

    vv_valid = (
        ~np.ma.getmaskarray(vv_data)
        & np.isfinite(vv)
        & (vv != NODATA)
    )

    vh_valid = (
        ~np.ma.getmaskarray(vh_data)
        & np.isfinite(vh)
        & (vh != NODATA)
    )

    profile = vv_src.profile.copy()
    transform = vv_src.transform
    crs = vv_src.crs

    pixel_area_m2 = abs(
        transform.a * transform.e
        - transform.b * transform.d
    )

# ============================================================
# 3. COMMON VALID PIXELS
# ============================================================

valid = vv_valid & vh_valid

if not valid.any():
    raise ValueError("No common valid VV/VH pixels.")

vv_values = vv[valid]
vh_values = vh[valid]

vv_threshold = np.percentile(vv_values, PERCENTILE)
vh_threshold = np.percentile(vh_values, PERCENTILE)

print(f"\nValid common pixels: {valid.sum():,}")
print(f"VV {PERCENTILE}th percentile: {vv_threshold:.4f} dB")
print(f"VH {PERCENTILE}th percentile: {vh_threshold:.4f} dB")

# ============================================================
# 4. IDENTIFY JOINT HIGH-INCREASE PIXELS
# ============================================================

vv_high = vv >= vv_threshold
vh_high = vh >= vh_threshold

joint_candidates = (
    valid
    & vv_high
    & vh_high
)

candidate_count = int(joint_candidates.sum())

print(
    "\nPixels with high VV AND high VH increase:",
    f"{candidate_count:,}"
)

print(
    "Candidate area:",
    f"{candidate_count * pixel_area_m2 / 1e6:.4f} km²"
)

# ============================================================
# 5. CONNECTED COMPONENT ANALYSIS
# ============================================================

# Eight-neighbour connectivity
structure = np.ones((3, 3), dtype=np.uint8)

labels, component_count = label(
    joint_candidates,
    structure=structure
)

component_sizes = np.bincount(labels.ravel())

# Ignore background label 0
large_component_ids = np.where(
    component_sizes >= MIN_PATCH_PIXELS
)[0]

large_component_ids = large_component_ids[
    large_component_ids != 0
]

cluster_mask = np.isin(
    labels,
    large_component_ids
)

print("\nConnected components detected:", component_count)
print("Clusters meeting minimum size:", len(large_component_ids))

print(
    "Minimum cluster area:",
    f"{MIN_PATCH_PIXELS * pixel_area_m2 / 10000:.3f} hectares"
)

print(
    "Retained candidate area:",
    f"{cluster_mask.sum() * pixel_area_m2 / 1e6:.4f} km²"
)

# ============================================================
# 6. CLUSTER STATISTICS
# ============================================================

cluster_records = []

for cluster_id in large_component_ids:

    pixels = labels == cluster_id

    count = int(pixels.sum())

    cluster_records.append({
        "cluster_id": int(cluster_id),
        "pixel_count": count,
        "area_m2": count * pixel_area_m2,
        "area_hectares": count * pixel_area_m2 / 10000,
        "area_km2": count * pixel_area_m2 / 1e6,
        "mean_vv_change_db": float(np.mean(vv[pixels])),
        "mean_vh_change_db": float(np.mean(vh[pixels])),
        "median_vv_change_db": float(np.median(vv[pixels])),
        "median_vh_change_db": float(np.median(vh[pixels]))
    })

cluster_df = pd.DataFrame(cluster_records)

if not cluster_df.empty:
    cluster_df = cluster_df.sort_values(
        "area_hectares",
        ascending=False
    )

cluster_csv = (
    REPORT_DIR / "SAR_Joint_Change_Cluster_Statistics.csv"
)

cluster_df.to_csv(cluster_csv, index=False)

# ============================================================
# 7. SAVE CLUSTER RASTER
# ============================================================

cluster_raster = np.zeros(
    vv.shape,
    dtype=np.uint8
)

cluster_raster[~valid] = 255
cluster_raster[cluster_mask] = 1

raster_profile = profile.copy()

raster_profile.update(
    driver="GTiff",
    count=1,
    dtype="uint8",
    nodata=255,
    compress="lzw",
    tiled=True,
    blockxsize=256,
    blockysize=256
)

cluster_raster_path = (
    OUTPUT_DIR / "SAR_Joint_Change_Clusters.tif"
)

with rasterio.open(
    cluster_raster_path,
    "w",
    **raster_profile
) as dst:

    dst.write(cluster_raster, 1)
    dst.set_band_description(
        1,
        "Joint VV and VH high-increase clusters"
    )

# ============================================================
# 8. POLYGONIZE RETAINED CLUSTERS
# ============================================================

polygon_records = []

for geometry, value in shapes(
    labels.astype(np.int32),
    mask=cluster_mask,
    transform=transform,
    connectivity=8
):

    if value == 0:
        continue

    polygon_records.append({
        "cluster_id": int(value),
        "geometry": shape(geometry)
    })   

if polygon_records:

    polygons = gpd.GeoDataFrame(
        polygon_records,
        geometry="geometry",
        crs=crs
    )

    polygons = polygons.merge(
        cluster_df,
        on="cluster_id",
        how="left"
    )

    polygon_file = (
        OUTPUT_DIR / "SAR_Joint_Change_Clusters.gpkg"
    )

    polygons.to_file(
        polygon_file,
        layer="change_clusters",
        driver="GPKG"
    )

else:
    polygon_file = None

# ============================================================
# 9. VISUALIZE CANDIDATE CLUSTERS
# ============================================================

fig, ax = plt.subplots(figsize=(11, 10))

display = np.where(cluster_mask, 1, np.nan)

image = ax.imshow(
    display,
    extent=[
        transform.c,
        transform.c + transform.a * vv.shape[1],
        transform.f + transform.e * vv.shape[0],
        transform.f
    ],
    cmap="Reds",
    interpolation="nearest"
)

ax.set_title(
    "Joint VV and VH Increase Clusters\n"
    "2016–2025 | Exploratory SAR Change Candidates",
    fontsize=13,
    fontweight="bold"
)

ax.set_xlabel(f"Easting ({crs})")
ax.set_ylabel("Northing")

ax.set_aspect("equal")

fig.colorbar(
    image,
    ax=ax,
    shrink=0.75,
    label="Retained candidate cluster"
)

plt.tight_layout()

map_file = (
    REPORT_DIR / "SAR_Joint_Change_Clusters.png"
)

plt.savefig(
    map_file,
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# ============================================================
# 10. FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("SPATIAL CLUSTER ANALYSIS COMPLETED")
print("=" * 70)

print(f"Joint high-increase pixels: {candidate_count:,}")
print(f"Retained clusters: {len(large_component_ids)}")

if not cluster_df.empty:

    print("\nLargest candidate clusters:")
    print(
        cluster_df.head(15).to_string(index=False)
    )

print("\nGenerated files:")
print(cluster_raster_path)
print(cluster_csv)
print(map_file)

if polygon_file:
    print(polygon_file)

print(
    "\nThese clusters are exploratory SAR change candidates. "
    "They are not confirmed urban expansion."
)
