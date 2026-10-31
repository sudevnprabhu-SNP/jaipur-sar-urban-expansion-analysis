
from pathlib import Path

import numpy as np
import geopandas as gpd
import rasterio
from rasterio.features import geometry_mask
from shapely.geometry import mapping
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D


# ============================================================
# 1. PROJECT PATHS
# ============================================================

PROJECT = Path(
    r"C:\Users\ssat-\Documents\RemoteSensing_Projects"
    r"\Project_02_Jaipur_SAR_Urban_Expansion"
)

BOUNDARY_FILE = (
    PROJECT / "data" / "boundaries"
    / "Jaipur_JMC_Municipal_Boundary.geojson"
)

ALIGNED_DIR = PROJECT / "data" / "processed" / "aligned_utm43n"

CLUSTER_FILE = (
    PROJECT / "data" / "processed"
    / "change_detection" / "spatial_clusters"
    / "SAR_Joint_Change_Clusters.gpkg"
)

OSM_FILE = (
    PROJECT / "data" / "processed"
    / "OSM_Jaipur_Clipped_Reference.gpkg"
)

OUTPUT = PROJECT / "reports" / "final_maps_v2"
OUTPUT.mkdir(parents=True, exist_ok=True)

CRS = "EPSG:32643"

YEARS = [2016, 2020, 2025]
POLARIZATIONS = ["VV", "VH"]

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 10,
    "figure.titlesize": 17,
})


# ============================================================
# 2. LOAD MUNICIPAL BOUNDARY
# ============================================================

print("Loading Jaipur municipal boundary...")

boundary = gpd.read_file(BOUNDARY_FILE).to_crs(CRS)

municipal = boundary.geometry.union_all()

minx, miny, maxx, maxy = boundary.total_bounds

xmargin = (maxx - minx) * 0.035
ymargin = (maxy - miny) * 0.035

MAP_EXTENT = (
    minx - xmargin,
    maxx + xmargin,
    miny - ymargin,
    maxy + ymargin,
)


# ============================================================
# 3. LOAD AND VALIDATE ALIGNED SAR RASTERS
# ============================================================

def raster_path(year, polarization):
    return (
        ALIGNED_DIR
        / f"Jaipur_S1_{year}_{polarization}_UTM43N_10m.tif"
    )


def load_sar_stack(polarization):

    arrays = []
    reference = None
    reference_transform = None
    reference_crs = None

    for year in YEARS:

        path = raster_path(year, polarization)

        if not path.exists():
            raise FileNotFoundError(
                f"Missing SAR raster: {path}"
            )

        with rasterio.open(path) as src:

            if reference is None:
                reference = (src.height, src.width)
                reference_transform = src.transform
                reference_crs = src.crs

                municipal_mask = geometry_mask(
                    [mapping(municipal)],
                    out_shape=reference,
                    transform=reference_transform,
                    invert=True
                )

            else:
                if (src.height, src.width) != reference:
                    raise ValueError(
                        f"Raster dimensions do not match: {path}"
                    )

                if src.transform != reference_transform:
                    raise ValueError(
                        f"Raster transforms do not match: {path}"
                    )

                if src.crs != reference_crs:
                    raise ValueError(
                        f"Raster CRS does not match: {path}"
                    )

            data = src.read(1, masked=True).astype("float32")

            array = np.asarray(data.filled(np.nan))

            array[~np.isfinite(array)] = np.nan
            array[~municipal_mask] = np.nan

            # Convert linear Sigma0 to decibels if needed.
            # The project rasters contain linear values.
            valid = np.isfinite(array)

            if np.any(array[valid] <= 0):
                raise ValueError(
                    f"Non-positive valid SAR values found in {path}"
                )

            array[valid] = 10.0 * np.log10(array[valid])

            arrays.append(array)

    return (
        np.stack(arrays),
        reference_transform,
        municipal_mask
    )


print("Loading VV and VH data...")

vv_stack, transform, municipal_mask = load_sar_stack("VV")
vh_stack, _, _ = load_sar_stack("VH")

height, width = vv_stack.shape[1:]


# ============================================================
# 4. COMMON DISPLAY EXTENT
# ============================================================

raster_extent = [
    transform.c,
    transform.c + transform.a * width,
    transform.f + transform.e * height,
    transform.f
]


# ============================================================
# 5. MAP DECORATION
# ============================================================

def decorate_map(ax):

    boundary.boundary.plot(
        ax=ax,
        color="black",
        linewidth=0.9,
        zorder=5
    )

    ax.set_xlim(MAP_EXTENT[0], MAP_EXTENT[1])
    ax.set_ylim(MAP_EXTENT[2], MAP_EXTENT[3])
    ax.set_aspect("equal")

    ax.set_xlabel("Easting (m)")
    ax.set_ylabel("Northing (m)")

    ax.tick_params(labelsize=8)

    # North arrow
    ax.annotate(
        "N",
        xy=(0.94, 0.94),
        xytext=(0.94, 0.86),
        xycoords="axes fraction",
        ha="center",
        va="center",
        fontsize=12,
        fontweight="bold",
        arrowprops=dict(
            facecolor="black",
            width=2,
            headwidth=8
        ),
        zorder=10
    )


def add_scale_bar(ax):

    length = 5000  # 5 km

    x_start = MAP_EXTENT[0] + (
        MAP_EXTENT[1] - MAP_EXTENT[0]
    ) * 0.06

    y_position = MAP_EXTENT[2] + (
        MAP_EXTENT[3] - MAP_EXTENT[2]
    ) * 0.055

    ax.plot(
        [x_start, x_start + length],
        [y_position, y_position],
        color="black",
        linewidth=3,
        solid_capstyle="butt",
        zorder=10
    )

    ax.text(
        x_start + length / 2,
        y_position + (MAP_EXTENT[3] - MAP_EXTENT[2]) * 0.018,
        "5 km",
        ha="center",
        fontsize=8,
        fontweight="bold",
        color="black"
    )


def finish_map(ax):
    decorate_map(ax)
    add_scale_bar(ax)


# ============================================================
# 6. MAPS 1 AND 2: THREE-YEAR BACKSCATTER MAPS
# ============================================================

def create_temporal_backscatter_map(stack, polarization):

    valid_values = stack[np.isfinite(stack)]

    vmin, vmax = np.percentile(valid_values, [2, 98])

    fig, axes = plt.subplots(
        1, 3,
        figsize=(19, 8),
        constrained_layout=True
    )

    for i, ax in enumerate(axes):

        im = ax.imshow(
            stack[i],
            extent=raster_extent,
            origin="upper",
            cmap="gray",
            vmin=vmin,
            vmax=vmax,
            interpolation="nearest"
        )

        finish_map(ax)

        ax.set_title(
            f"{YEARS[i]}",
            fontsize=15,
            fontweight="bold"
        )

    colorbar = fig.colorbar(
        im,
        ax=axes,
        shrink=0.72,
        pad=0.02
    )

    colorbar.set_label(
        f"{polarization} backscatter (dB)",
        fontsize=11
    )

    fig.suptitle(
        f"Jaipur Municipal Corporation — Sentinel-1 "
        f"{polarization} Backscatter",
        fontweight="bold"
    )

    output_file = (
        OUTPUT / f"01_{polarization}_Backscatter_2016_2020_2025.png"
    )

    fig.savefig(
        output_file,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close(fig)

    print("Generated:", output_file.name)


create_temporal_backscatter_map(vv_stack, "VV")
create_temporal_backscatter_map(vh_stack, "VH")


# ============================================================
# 7. MAPS 3 AND 4: TEMPORAL CHANGE MAPS
# ============================================================

PERIODS = [
    (0, 1, "2016–2020"),
    (1, 2, "2020–2025"),
    (0, 2, "2016–2025"),
]


def create_change_map(stack, polarization):

    changes = []

    for start, end, label in PERIODS:
        changes.append(stack[end] - stack[start])

    changes = np.stack(changes)

    valid_values = changes[np.isfinite(changes)]

    limit = np.percentile(np.abs(valid_values), 98)

    fig, axes = plt.subplots(
        1, 3,
        figsize=(19, 8),
        constrained_layout=True
    )

    for i, ax in enumerate(axes):

        im = ax.imshow(
            changes[i],
            extent=raster_extent,
            origin="upper",
            cmap="RdBu_r",
            vmin=-limit,
            vmax=limit,
            interpolation="nearest"
        )

        finish_map(ax)

        ax.set_title(
            PERIODS[i][2],
            fontsize=14,
            fontweight="bold"
        )

    colorbar = fig.colorbar(
        im,
        ax=axes,
        shrink=0.72,
        pad=0.02
    )

    colorbar.set_label(
        f"{polarization} backscatter change (dB)",
        fontsize=11
    )

    fig.suptitle(
        f"Jaipur — Sentinel-1 {polarization} Temporal Change",
        fontweight="bold"
    )

    output_file = (
        OUTPUT / f"02_{polarization}_Change_Maps.png"
    )

    fig.savefig(
        output_file,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close(fig)

    print("Generated:", output_file.name)


create_change_map(vv_stack, "VV")
create_change_map(vh_stack, "VH")


# ============================================================
# 8. MAP 5: SAR CHANGE CANDIDATE CLUSTERS
# ============================================================

print("Loading SAR clusters...")

clusters = gpd.read_file(
    CLUSTER_FILE,
    layer="change_clusters"
).to_crs(CRS)

fig, ax = plt.subplots(figsize=(11, 11))

boundary.plot(
    ax=ax,
    facecolor="#f4f3ee",
    edgecolor="black",
    linewidth=1
)

clusters.plot(
    ax=ax,
    color="#d73027",
    edgecolor="#7f0000",
    linewidth=0.2,
    alpha=0.85
)

finish_map(ax)

ax.set_title(
    "Jaipur — Spatially Connected SAR Change Candidates\n"
    "2016–2025 | 196 retained clusters",
    fontsize=14,
    fontweight="bold"
)

cluster_legend = [
    Patch(
        facecolor="#d73027",
        edgecolor="#7f0000",
        label="SAR change candidate clusters"
    ),
    Patch(
        facecolor="#f4f3ee",
        edgecolor="black",
        label="Municipal area"
    )
]

ax.legend(
    handles=cluster_legend,
    loc="lower right",
    frameon=True,
    fontsize=9
)

plt.tight_layout()

output_file = OUTPUT / "03_SAR_Change_Candidate_Clusters.png"

plt.savefig(
    output_file,
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print("Generated:", output_file.name)


# ============================================================
# 9. MAP 6: SAR CANDIDATES AND CURRENT OSM BUILDINGS
# ============================================================

print("Loading current OSM building footprints...")

buildings = gpd.read_file(
    OSM_FILE,
    layer="buildings_polygon"
).to_crs(CRS)

buildings = buildings[
    buildings.geometry.intersects(municipal)
].copy()

buildings.geometry = buildings.geometry.intersection(municipal)

buildings = buildings[
    ~buildings.geometry.is_empty
].copy()

fig, ax = plt.subplots(figsize=(11, 11))

boundary.plot(
    ax=ax,
    facecolor="#f7f7f7",
    edgecolor="black",
    linewidth=1
)

buildings.plot(
    ax=ax,
    color="#444444",
    edgecolor="none",
    alpha=0.65
)

clusters.plot(
    ax=ax,
    color="#ff4b36",
    edgecolor="#8c0000",
    linewidth=0.2,
    alpha=0.75
)

finish_map(ax)

ax.set_title(
    "Jaipur — SAR Change Candidates and Current OSM Buildings\n"
    "OSM is a present-day reference, not historical validation",
    fontsize=13,
    fontweight="bold"
)

legend_items = [
    Patch(
        facecolor="#ff4b36",
        edgecolor="#8c0000",
        label="SAR change candidates"
    ),
    Patch(
        facecolor="#444444",
        label="Current OSM building footprints"
    ),
    Line2D(
        [0], [0],
        color="black",
        linewidth=1,
        label="Municipal boundary"
    )
]

ax.legend(
    handles=legend_items,
    loc="lower right",
    fontsize=8
)

plt.tight_layout()

output_file = OUTPUT / "04_SAR_Candidates_OSM_Buildings.png"

plt.savefig(
    output_file,
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print("Generated:", output_file.name)


# ============================================================
# 10. SUMMARY
# ============================================================

print("\n" + "=" * 65)
print("MULTI-YEAR SAR MAP GENERATION COMPLETED")
print("=" * 65)

print("Municipal boundary features:", len(boundary))
print("Retained SAR clusters:", len(clusters))
print("Current OSM buildings:", len(buildings))

print("\nOutput directory:")
print(OUTPUT)

print("\nGenerated maps:")

for file in sorted(OUTPUT.glob("*.png")):
    print(" -", file.name)

print("\nOriginal SAR data and existing maps were not modified.")
