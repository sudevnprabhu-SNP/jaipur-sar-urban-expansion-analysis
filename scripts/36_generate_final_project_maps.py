
from pathlib import Path
import numpy as np
import geopandas as gpd
import rasterio
import matplotlib.pyplot as plt

# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT = Path(
    r"C:\Users\ssat-\Documents\RemoteSensing_Projects"
    r"\Project_02_Jaipur_SAR_Urban_Expansion"
)

BOUNDARY_FILE = (
    PROJECT / "data" / "boundaries"
    / "Jaipur_JMC_Municipal_Boundary.geojson"
)

CHANGE_RASTER = (
    PROJECT / "data" / "processed"
    / "change_detection" / "VV_2016_2025_continuous.tif"
)

CLUSTER_FILE = (
    PROJECT / "data" / "processed"
    / "change_detection" / "spatial_clusters"
    / "SAR_Joint_Change_Clusters.gpkg"
)

OSM_FILE = (
    PROJECT / "data" / "processed"
    / "OSM_Jaipur_Clipped_Reference.gpkg"
)

OUTPUT = PROJECT / "reports" / "final_maps"
OUTPUT.mkdir(parents=True, exist_ok=True)

CRS = "EPSG:32643"

# ============================================================
# LOAD VECTOR DATA
# ============================================================

boundary = gpd.read_file(BOUNDARY_FILE).to_crs(CRS)

clusters = gpd.read_file(
    CLUSTER_FILE,
    layer="change_clusters"
).to_crs(CRS)

buildings = gpd.read_file(
    OSM_FILE,
    layer="buildings_polygon"
).to_crs(CRS)

municipal = boundary.geometry.union_all()

buildings = buildings[
    buildings.geometry.intersects(municipal)
].copy()

buildings.geometry = buildings.geometry.intersection(
    municipal
)

buildings = buildings[
    ~buildings.geometry.is_empty
]

# ============================================================
# COMMON MAP EXTENT
# ============================================================

minx, miny, maxx, maxy = boundary.total_bounds

xmargin = (maxx - minx) * 0.04
ymargin = (maxy - miny) * 0.04

xlim = (minx - xmargin, maxx + xmargin)
ylim = (miny - ymargin, maxy + ymargin)

# ============================================================
# MAP 1: VV BACKSCATTER CHANGE
# ============================================================

with rasterio.open(CHANGE_RASTER) as src:

    data = src.read(1, masked=True)

    array = np.asarray(data.data, dtype=np.float32)

    mask = np.ma.getmaskarray(data)
    array[mask] = np.nan
    array[~np.isfinite(array)] = np.nan

    # Use a reduced-resolution display array
    factor = 3

    display = array[::factor, ::factor]

    transform = src.transform

    extent = [
        transform.c,
        transform.c + transform.a * src.width,
        transform.f + transform.e * src.height,
        transform.f
    ]

    values = display[np.isfinite(display)]

    low, high = np.percentile(values, [2, 98])

fig, ax = plt.subplots(figsize=(11, 11))

im = ax.imshow(
    display,
    extent=extent,
    origin="upper",
    cmap="RdBu_r",
    vmin=low,
    vmax=high
)

boundary.boundary.plot(
    ax=ax,
    color="black",
    linewidth=1.2
)

ax.set_xlim(xlim)
ax.set_ylim(ylim)
ax.set_aspect("equal")

ax.set_title(
    "Jaipur Municipality — Sentinel-1 VV Backscatter Change\n"
    "2016–2025",
    fontsize=15,
    fontweight="bold"
)

ax.set_xlabel("Easting (m)")
ax.set_ylabel("Northing (m)")

fig.colorbar(
    im,
    ax=ax,
    shrink=0.72,
    label="VV backscatter change (dB)"
)

plt.tight_layout()

plt.savefig(
    OUTPUT / "01_VV_Backscatter_Change_2016_2025.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# ============================================================
# MAP 2: SAR CHANGE CANDIDATE CLUSTERS
# ============================================================

fig, ax = plt.subplots(figsize=(11, 11))

boundary.plot(
    ax=ax,
    facecolor="#f7f7f7",
    edgecolor="black",
    linewidth=1.2
)

clusters.plot(
    ax=ax,
    color="red",
    edgecolor="darkred",
    linewidth=0.2,
    alpha=0.8
)

ax.set_xlim(xlim)
ax.set_ylim(ylim)
ax.set_aspect("equal")

ax.set_title(
    "Jaipur Municipality — SAR Change Candidate Clusters\n"
    "2016–2025 | 196 retained clusters",
    fontsize=15,
    fontweight="bold"
)

ax.set_xlabel("Easting (m)")
ax.set_ylabel("Northing (m)")

plt.tight_layout()

plt.savefig(
    OUTPUT / "02_SAR_Change_Candidate_Clusters.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# ============================================================
# MAP 3: SAR CANDIDATES AND CURRENT OSM BUILDINGS
# ============================================================

fig, ax = plt.subplots(figsize=(11, 11))

boundary.plot(
    ax=ax,
    facecolor="#fafafa",
    edgecolor="black",
    linewidth=1.2
)

buildings.plot(
    ax=ax,
    color="lightgrey",
    edgecolor="none",
    alpha=0.8
)

clusters.plot(
    ax=ax,
    color="red",
    edgecolor="darkred",
    linewidth=0.2,
    alpha=0.7
)

ax.set_xlim(xlim)
ax.set_ylim(ylim)
ax.set_aspect("equal")

ax.set_title(
    "Jaipur Municipality — SAR Change Candidates and OSM Buildings\n"
    "Current OSM reference data; not historical validation",
    fontsize=14,
    fontweight="bold"
)

ax.set_xlabel("Easting (m)")
ax.set_ylabel("Northing (m)")

from matplotlib.patches import Patch

legend_items = [
    Patch(facecolor="red", edgecolor="darkred",
          label="SAR change candidates"),
    Patch(facecolor="lightgrey", edgecolor="grey",
          label="Current OSM buildings"),
    Patch(facecolor="none", edgecolor="black",
          label="Municipal boundary")
]

ax.legend(
    handles=legend_items,
    loc="lower right"
)

plt.tight_layout()

plt.savefig(
    OUTPUT / "03_SAR_Candidates_OSM_Buildings.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# ============================================================
# SUMMARY
# ============================================================

print("=" * 70)
print("FINAL PROJECT MAPS GENERATED")
print("=" * 70)

print("Municipal boundary:", len(boundary))
print("SAR candidate clusters:", len(clusters))
print("Current OSM buildings:", len(buildings))

print("\nOutput directory:")
print(OUTPUT)

for file in sorted(OUTPUT.glob("*.png")):
    print(file.name)

print("\nOriginal datasets were not modified.")
