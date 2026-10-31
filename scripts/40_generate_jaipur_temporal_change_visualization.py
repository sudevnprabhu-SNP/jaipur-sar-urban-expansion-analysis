
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.features import geometry_mask
from shapely.geometry import mapping

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch


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

OUTPUT = (
    PROJECT / "reports"
    / "final_temporal_change_analysis"
)

OUTPUT.mkdir(parents=True, exist_ok=True)

YEARS = [2016, 2020, 2025]

CRS = "EPSG:32643"

PIXEL_AREA_M2 = 100
PIXEL_AREA_KM2 = PIXEL_AREA_M2 / 1_000_000

# Percentile thresholds used for significant candidate detection.
UPPER_PERCENTILE = 95
LOWER_PERCENTILE = 5

# Main visual layer: VV.
# VH is used as supporting evidence for joint candidates.

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 10,
    "figure.titlesize": 17
})


# ============================================================
# 2. LOAD JAIPUR MUNICIPAL BOUNDARY
# ============================================================

print("\nLoading Jaipur municipal boundary...")

boundary = gpd.read_file(
    BOUNDARY_FILE
).to_crs(CRS)

municipal = boundary.geometry.union_all()

municipal_area_km2 = municipal.area / 1_000_000

print(f"Municipal area: {municipal_area_km2:.4f} km²")


# ============================================================
# 3. LOAD SAR RASTERS
# ============================================================

def get_raster_path(year, polarization):

    return (
        ALIGNED_DIR
        / f"Jaipur_S1_{year}_{polarization}_UTM43N_10m.tif"
    )


def load_sar_stack(polarization):

    arrays = []

    reference_shape = None
    reference_transform = None
    reference_crs = None
    municipal_mask = None

    for year in YEARS:

        path = get_raster_path(year, polarization)

        if not path.exists():
            raise FileNotFoundError(
                f"Missing raster: {path}"
            )

        print(f"Loading {year} {polarization}...")

        with rasterio.open(path) as src:

            if reference_shape is None:

                reference_shape = (
                    src.height,
                    src.width
                )

                reference_transform = src.transform
                reference_crs = src.crs

                municipal_mask = geometry_mask(
                    [mapping(municipal)],
                    out_shape=reference_shape,
                    transform=reference_transform,
                    invert=True
                )

            else:

                if (
                    src.height,
                    src.width
                ) != reference_shape:

                    raise ValueError(
                        "Raster dimensions do not match."
                    )

                if src.transform != reference_transform:
                    raise ValueError(
                        "Raster transforms do not match."
                    )

                if src.crs != reference_crs:
                    raise ValueError(
                        "Raster CRS does not match."
                    )

            data = src.read(
                1,
                masked=True
            ).astype("float32")

            array = np.asarray(
                data.filled(np.nan)
            )

            array[~np.isfinite(array)] = np.nan

            array[~municipal_mask] = np.nan

            valid = np.isfinite(array)

            # Project processing record identifies the aligned
            # rasters as linear Sigma0 values.
            if np.any(array[valid] <= 0):
                raise ValueError(
                    f"Non-positive linear values in {path}"
                )

            # Linear Sigma0 to decibels.
            array[valid] = (
                10.0 * np.log10(array[valid])
            )

            arrays.append(array)

    return (
        np.stack(arrays),
        reference_transform,
        municipal_mask
    )


vv, transform, municipal_mask = load_sar_stack("VV")

vh, _, _ = load_sar_stack("VH")

height, width = vv.shape[1:]

print("\nSAR raster dimensions:", vv.shape)


# ============================================================
# 4. COMMON MAP EXTENT
# ============================================================

raster_extent = [
    transform.c,
    transform.c + transform.a * width,
    transform.f + transform.e * height,
    transform.f
]

minx, miny, maxx, maxy = boundary.total_bounds

xmargin = (maxx - minx) * 0.035
ymargin = (maxy - miny) * 0.035

map_xlim = (
    minx - xmargin,
    maxx + xmargin
)

map_ylim = (
    miny - ymargin,
    maxy + ymargin
)


# ============================================================
# 5. MAP DECORATION
# ============================================================

def decorate_map(ax):

    boundary.boundary.plot(
        ax=ax,
        color="black",
        linewidth=0.85,
        zorder=5
    )

    ax.set_xlim(map_xlim)
    ax.set_ylim(map_ylim)

    ax.set_aspect("equal")

    ax.set_xlabel("Easting (m)")
    ax.set_ylabel("Northing (m)")

    ax.tick_params(labelsize=8)

    # North arrow.
    ax.annotate(
        "N",
        xy=(0.94, 0.95),
        xytext=(0.94, 0.87),
        xycoords="axes fraction",
        ha="center",
        va="center",
        fontsize=11,
        fontweight="bold",
        arrowprops=dict(
            facecolor="black",
            width=2,
            headwidth=8
        )
    )


def add_scale_bar(ax):

    length = 5000

    x_start = map_xlim[0] + (
        map_xlim[1] - map_xlim[0]
    ) * 0.06

    y_position = map_ylim[0] + (
        map_ylim[1] - map_ylim[0]
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
        y_position + (
            map_ylim[1] - map_ylim[0]
        ) * 0.018,
        "5 km",
        ha="center",
        fontsize=8,
        fontweight="bold"
    )


def finish_map(ax):

    decorate_map(ax)
    add_scale_bar(ax)


# ============================================================
# 6. CALCULATE TEMPORAL CHANGES
# ============================================================

vv_2016 = vv[0]
vv_2020 = vv[1]
vv_2025 = vv[2]

vh_2016 = vh[0]
vh_2020 = vh[1]
vh_2025 = vh[2]

# VV changes.
vv_16_20 = vv_2020 - vv_2016
vv_20_25 = vv_2025 - vv_2020
vv_16_25 = vv_2025 - vv_2016

# VH changes.
vh_16_20 = vh_2020 - vh_2016
vh_20_25 = vh_2025 - vh_2020
vh_16_25 = vh_2025 - vh_2016

period_data = {
    "2016-2020": {
        "vv": vv_16_20,
        "vh": vh_16_20
    },
    "2020-2025": {
        "vv": vv_20_25,
        "vh": vh_20_25
    },
    "2016-2025": {
        "vv": vv_16_25,
        "vh": vh_16_25
    }
}


# ============================================================
# 7. IDENTIFY STRONG JOINT CHANGE CANDIDATES
# ============================================================

def identify_joint_candidates(vv_change, vh_change):

    valid = (
        np.isfinite(vv_change)
        & np.isfinite(vh_change)
    )

    vv_values = vv_change[valid]
    vh_values = vh_change[valid]

    vv_increase_threshold = np.percentile(
        vv_values,
        UPPER_PERCENTILE
    )

    vh_increase_threshold = np.percentile(
        vh_values,
        UPPER_PERCENTILE
    )

    vv_decrease_threshold = np.percentile(
        vv_values,
        LOWER_PERCENTILE
    )

    vh_decrease_threshold = np.percentile(
        vh_values,
        LOWER_PERCENTILE
    )

    # Both polarizations must show a strong increase.
    increase = (
        (vv_change > vv_increase_threshold)
        & (vh_change > vh_increase_threshold)
        & valid
    )

    # Both polarizations must show a strong decrease.
    decrease = (
        (vv_change < vv_decrease_threshold)
        & (vh_change < vh_decrease_threshold)
        & valid
    )

    return {
        "increase": increase,
        "decrease": decrease,
        "vv_increase_threshold": vv_increase_threshold,
        "vh_increase_threshold": vh_increase_threshold,
        "vv_decrease_threshold": vv_decrease_threshold,
        "vh_decrease_threshold": vh_decrease_threshold
    }


candidate_data = {}

for period, data in period_data.items():

    candidate_data[period] = identify_joint_candidates(
        data["vv"],
        data["vh"]
    )


# ============================================================
# 8. BASELINE MAP — 2016
# ============================================================

print("\nGenerating baseline map...")

fig, ax = plt.subplots(figsize=(10, 11))

values = vv_2016[np.isfinite(vv_2016)]

vmin, vmax = np.percentile(
    values,
    [2, 98]
)

im = ax.imshow(
    vv_2016,
    extent=raster_extent,
    origin="upper",
    cmap="gray",
    vmin=vmin,
    vmax=vmax,
    interpolation="nearest"
)

finish_map(ax)

ax.set_title(
    "Jaipur — Sentinel-1 VV Backscatter Baseline\n"
    "2016",
    fontsize=15,
    fontweight="bold"
)

cbar = fig.colorbar(
    im,
    ax=ax,
    shrink=0.75
)

cbar.set_label("VV backscatter (dB)")

plt.tight_layout()

fig.savefig(
    OUTPUT / "01_Jaipur_2016_Baseline.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close(fig)


# ============================================================
# 9. PERIOD CHANGE MAPS
# ============================================================

def create_period_map(period, data):

    vv_change = data["vv"]

    candidates = candidate_data[period]

    valid_values = vv_change[
        np.isfinite(vv_change)
    ]

    limit = np.percentile(
        np.abs(valid_values),
        98
    )

    fig, ax = plt.subplots(figsize=(10, 11))

    # Continuous VV change background.
    im = ax.imshow(
        vv_change,
        extent=raster_extent,
        origin="upper",
        cmap="RdBu_r",
        vmin=-limit,
        vmax=limit,
        interpolation="nearest"
    )

    # Significant joint increase.
    increase_overlay = np.ma.masked_where(
        ~candidates["increase"],
        np.ones_like(vv_change)
    )

    ax.imshow(
        increase_overlay,
        extent=raster_extent,
        origin="upper",
        cmap=ListedColormap(["#ff2020"]),
        vmin=0,
        vmax=1,
        interpolation="nearest",
        alpha=0.85
    )

    # Significant joint decrease.
    decrease_overlay = np.ma.masked_where(
        ~candidates["decrease"],
        np.ones_like(vv_change)
    )

    ax.imshow(
        decrease_overlay,
        extent=raster_extent,
        origin="upper",
        cmap=ListedColormap(["#1769d2"]),
        vmin=0,
        vmax=1,
        interpolation="nearest",
        alpha=0.85
    )

    finish_map(ax)

    ax.set_title(
        f"Jaipur — SAR Surface Change: {period}\n"
        "VV change background with joint VV/VH candidates",
        fontsize=13,
        fontweight="bold"
    )

    cbar = fig.colorbar(
        im,
        ax=ax,
        shrink=0.72
    )

    cbar.set_label("VV backscatter change (dB)")

    legend = [
        Patch(
            facecolor="#ff2020",
            label="Strong joint increase"
        ),
        Patch(
            facecolor="#1769d2",
            label="Strong joint decrease"
        )
    ]

    ax.legend(
        handles=legend,
        loc="lower right",
        fontsize=8
    )

    plt.tight_layout()

    filename = (
        period.replace("-", "_")
    )

    fig.savefig(
        OUTPUT / f"02_Change_{filename}.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.close(fig)


print("Generating period change maps...")

create_period_map(
    "2016-2020",
    period_data["2016-2020"]
)

create_period_map(
    "2020-2025",
    period_data["2020-2025"]
)

create_period_map(
    "2016-2025",
    period_data["2016-2025"]
)


# ============================================================
# 10. FINAL TEMPORAL CHANGE CLASSIFICATION
# ============================================================

print("Generating combined temporal change map...")

early_inc = candidate_data["2016-2020"]["increase"]
early_dec = candidate_data["2016-2020"]["decrease"]

late_inc = candidate_data["2020-2025"]["increase"]
late_dec = candidate_data["2020-2025"]["decrease"]

valid_all = (
    np.isfinite(vv_16_20)
    & np.isfinite(vv_20_25)
    & np.isfinite(vh_16_20)
    & np.isfinite(vh_20_25)
)

# Classes:
# 0 = Other / no strong joint candidate
# 1 = Increase in 2016-2020 only
# 2 = Increase in 2020-2025 only
# 3 = Increase in both periods
# 4 = Decrease in 2016-2020 only
# 5 = Decrease in 2020-2025 only
# 6 = Decrease in both periods

combined = np.zeros(
    vv_16_20.shape,
    dtype=np.uint8
)

combined[early_inc & ~late_inc] = 1
combined[late_inc & ~early_inc] = 2
combined[early_inc & late_inc] = 3

combined[early_dec & ~late_dec] = 4
combined[late_dec & ~early_dec] = 5
combined[early_dec & late_dec] = 6

combined[~valid_all] = 255

colors = [
    "#d9d9d9",  # Other
    "#e31a1c",  # Early increase
    "#ff9f1c",  # Late increase
    "#8e44ad",  # Increase both periods
    "#3182bd",  # Early decrease
    "#00a6ca",  # Late decrease
    "#084081"   # Decrease both periods
]

cmap = ListedColormap(colors)
cmap.set_bad("white")

masked_combined = np.ma.masked_equal(
    combined,
    255
)

fig, ax = plt.subplots(figsize=(11, 11))

ax.imshow(
    masked_combined,
    extent=raster_extent,
    origin="upper",
    cmap=cmap,
    vmin=-0.5,
    vmax=6.5,
    interpolation="nearest"
)

finish_map(ax)

ax.set_title(
    "Jaipur — Multi-Temporal SAR Change Classification\n"
    "2016–2020–2025",
    fontsize=15,
    fontweight="bold"
)

legend_items = [
    Patch(facecolor=colors[0], label="Other / no strong joint candidate"),
    Patch(facecolor=colors[1], label="Strong increase: 2016–2020"),
    Patch(facecolor=colors[2], label="Strong increase: 2020–2025"),
    Patch(facecolor=colors[3], label="Strong increase: both periods"),
    Patch(facecolor=colors[4], label="Strong decrease: 2016–2020"),
    Patch(facecolor=colors[5], label="Strong decrease: 2020–2025"),
    Patch(facecolor=colors[6], label="Strong decrease: both periods")
]

ax.legend(
    handles=legend_items,
    loc="lower right",
    fontsize=8,
    framealpha=0.95
)

plt.tight_layout()

fig.savefig(
    OUTPUT / "03_Jaipur_Combined_Temporal_Change.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close(fig)


# ============================================================
# 11. CHANGE STATISTICS BY PERIOD
# ============================================================

print("Calculating period-wise statistics...")

statistics = []

for period, data in period_data.items():

    vv_change = data["vv"]
    vh_change = data["vh"]

    candidates = candidate_data[period]

    valid = (
        np.isfinite(vv_change)
        & np.isfinite(vh_change)
    )

    vv_values = vv_change[valid]
    vh_values = vh_change[valid]

    vv_increase_pixels = int(
        np.sum(vv_values > 0)
    )

    vv_decrease_pixels = int(
        np.sum(vv_values < 0)
    )

    vh_increase_pixels = int(
        np.sum(vh_values > 0)
    )

    vh_decrease_pixels = int(
        np.sum(vh_values < 0)
    )

    joint_increase_pixels = int(
        candidates["increase"].sum()
    )

    joint_decrease_pixels = int(
        candidates["decrease"].sum()
    )

    statistics.append({

        "period": period,

        "valid_pixels": int(valid.sum()),

        "vv_mean_change_db": np.mean(vv_values),
        "vv_median_change_db": np.median(vv_values),

        "vh_mean_change_db": np.mean(vh_values),
        "vh_median_change_db": np.median(vh_values),

        "vv_increase_pixels": vv_increase_pixels,
        "vv_decrease_pixels": vv_decrease_pixels,

        "vv_increase_area_km2": (
            vv_increase_pixels * PIXEL_AREA_KM2
        ),

        "vv_decrease_area_km2": (
            vv_decrease_pixels * PIXEL_AREA_KM2
        ),

        "vh_increase_pixels": vh_increase_pixels,
        "vh_decrease_pixels": vh_decrease_pixels,

        "joint_increase_pixels": joint_increase_pixels,
        "joint_decrease_pixels": joint_decrease_pixels,

        "joint_increase_area_km2": (
            joint_increase_pixels * PIXEL_AREA_KM2
        ),

        "joint_decrease_area_km2": (
            joint_decrease_pixels * PIXEL_AREA_KM2
        ),

        "vv_increase_threshold_db": (
            candidates["vv_increase_threshold"]
        ),

        "vh_increase_threshold_db": (
            candidates["vh_increase_threshold"]
        ),

        "vv_decrease_threshold_db": (
            candidates["vv_decrease_threshold"]
        ),

        "vh_decrease_threshold_db": (
            candidates["vh_decrease_threshold"]
        )
    })


statistics_df = pd.DataFrame(statistics)

statistics_df.to_csv(
    OUTPUT / "01_Temporal_Change_Statistics.csv",
    index=False
)


# ============================================================
# 12. FINAL COMBINED FOUR-PANEL README FIGURE
# ============================================================

print("Generating README figure...")

fig, axes = plt.subplots(
    2, 2,
    figsize=(17, 17),
    constrained_layout=True
)

# Panel 1: 2016 baseline.
values = vv_2016[np.isfinite(vv_2016)]

baseline_min, baseline_max = np.percentile(
    values,
    [2, 98]
)

im1 = axes[0, 0].imshow(
    vv_2016,
    extent=raster_extent,
    origin="upper",
    cmap="gray",
    vmin=baseline_min,
    vmax=baseline_max
)

axes[0, 0].set_title(
    "A. 2016 — Baseline",
    fontweight="bold"
)

finish_map(axes[0, 0])

# Panel 2: 2016-2020.
early_limit = np.percentile(
    np.abs(vv_16_20[np.isfinite(vv_16_20)]),
    98
)

im2 = axes[0, 1].imshow(
    vv_16_20,
    extent=raster_extent,
    origin="upper",
    cmap="RdBu_r",
    vmin=-early_limit,
    vmax=early_limit
)

axes[0, 1].set_title(
    "B. 2016–2020 — Backscatter Change",
    fontweight="bold"
)

finish_map(axes[0, 1])

# Panel 3: 2020-2025.
late_limit = np.percentile(
    np.abs(vv_20_25[np.isfinite(vv_20_25)]),
    98
)

im3 = axes[1, 0].imshow(
    vv_20_25,
    extent=raster_extent,
    origin="upper",
    cmap="RdBu_r",
    vmin=-late_limit,
    vmax=late_limit
)

axes[1, 0].set_title(
    "C. 2020–2025 — Backscatter Change",
    fontweight="bold"
)

finish_map(axes[1, 0])

# Panel 4: Combined temporal candidates.
im4 = axes[1, 1].imshow(
    masked_combined,
    extent=raster_extent,
    origin="upper",
    cmap=cmap,
    vmin=-0.5,
    vmax=6.5,
    interpolation="nearest"
)

axes[1, 1].set_title(
    "D. 2016–2025 — Combined Change Candidates",
    fontweight="bold"
)

finish_map(axes[1, 1])

fig.suptitle(
    "JAIPUR — MULTI-TEMPORAL SENTINEL-1 SAR CHANGE ANALYSIS\n"
    "2016 | 2020 | 2025",
    fontsize=19,
    fontweight="bold"
)

fig.savefig(
    OUTPUT / "04_Jaipur_SAR_Temporal_Change_README.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close(fig)


# ============================================================
# 13. SUMMARY REPORT
# ============================================================

summary_file = (
    OUTPUT / "Jaipur_Temporal_Change_Summary.txt"
)

with open(
    summary_file,
    "w",
    encoding="utf-8"
) as f:

    f.write(
        "JAIPUR MULTI-TEMPORAL SENTINEL-1 SAR ANALYSIS\n"
    )

    f.write("=" * 70 + "\n\n")

    f.write(
        f"Municipal area: {municipal_area_km2:.4f} km²\n\n"
    )

    f.write(
        "TEMPORAL BACKSCATTER CHANGE STATISTICS\n"
    )

    f.write(
        statistics_df.to_string(index=False)
    )

    f.write("\n\n")

    f.write(
        "INTERPRETATION\n"
    )

    f.write(
        "Positive backscatter change indicates an increase "
        "in radar backscatter response. Negative change "
        "indicates a decrease. These changes may be related "
        "to changes in surface properties but are not "
        "direct evidence of urban construction or demolition.\n\n"
    )

    f.write(
        "The joint candidate masks identify pixels in which "
        "both VV and VH changes exceed their respective "
        "period-specific 95th or 5th percentile thresholds. "
        "They are exploratory SAR change candidates, not "
        "validated urban expansion classes.\n"
    )


# ============================================================
# 14. FINAL OUTPUT
# ============================================================

print("\n" + "=" * 75)
print("JAIPUR TEMPORAL SAR CHANGE ANALYSIS COMPLETED")
print("=" * 75)

print("\nMunicipal area:")
print(f"{municipal_area_km2:.4f} km²")

print("\nPeriod-wise statistics:")
print(statistics_df.to_string(index=False))

print("\nOutput directory:")
print(OUTPUT)

print("\nGenerated files:")

for file in sorted(OUTPUT.iterdir()):

    if file.is_file():
        print(" -", file.name)

print("\nOriginal datasets and previous outputs were not modified.")
