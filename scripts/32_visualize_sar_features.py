
from pathlib import Path
import numpy as np
import rasterio
import matplotlib.pyplot as plt

# ============================================================
# PATHS
# ============================================================

PROJECT_DIR = Path(
    r"C:\Users\ssat-\Documents\RemoteSensing_Projects"
    r"\Project_02_Jaipur_SAR_Urban_Expansion"
)

STACK_FILE = (
    PROJECT_DIR
    / "data"
    / "processed"
    / "sar_features"
    / "Jaipur_SAR_Feature_Stack_2016_2025.tif"
)

OUTPUT_DIR = (
    PROJECT_DIR
    / "reports"
    / "sar_coverage_analysis"
    / "feature_maps"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# BAND DEFINITIONS
# ============================================================

BANDS = {
    1: "2016 VV Backscatter (dB)",
    2: "2016 VH Backscatter (dB)",
    3: "2016 VV-VH Difference (dB)",
    4: "2020 VV Backscatter (dB)",
    5: "2020 VH Backscatter (dB)",
    6: "2020 VV-VH Difference (dB)",
    7: "2025 VV Backscatter (dB)",
    8: "2025 VH Backscatter (dB)",
    9: "2025 VV-VH Difference (dB)",
    10: "VV Change 2016-2020 (dB)",
    11: "VH Change 2016-2020 (dB)",
    12: "VV Change 2020-2025 (dB)",
    13: "VH Change 2020-2025 (dB)",
    14: "VV Change 2016-2025 (dB)",
    15: "VH Change 2016-2025 (dB)"
}

# ============================================================
# READ STACK
# ============================================================

print("=" * 70)
print("SAR FEATURE VISUALIZATION")
print("=" * 70)

with rasterio.open(STACK_FILE) as src:

    print(f"Raster dimensions: {src.width} x {src.height}")
    print(f"Bands: {src.count}")
    print(f"CRS: {src.crs}")

    if src.count != 15:
        raise ValueError("Expected 15 feature bands.")

    # Read only every fifth pixel for fast visualization
    arrays = {}

    for band, title in BANDS.items():

        data = src.read(
            band,
            masked=True,
            out_shape=(
                max(1, src.height // 5),
                max(1, src.width // 5)
            )
        )

        array = np.asarray(
            data.data,
            dtype=np.float32
        )

        mask = np.ma.getmaskarray(data)

        array[mask] = np.nan
        array[~np.isfinite(array)] = np.nan

        arrays[band] = array

# ============================================================
# VISUALIZATION FUNCTION
# ============================================================

def save_map(array, title, filename, cmap="viridis",
             symmetric=False):

    fig, ax = plt.subplots(figsize=(10, 9))

    valid = array[np.isfinite(array)]

    if valid.size == 0:
        raise ValueError(f"No valid data in {title}")

    low, high = np.percentile(valid, [2, 98])

    if symmetric:
        limit = max(abs(low), abs(high))
        low, high = -limit, limit

    image = ax.imshow(
        array,
        cmap=cmap,
        vmin=low,
        vmax=high
    )

    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.set_axis_off()

    fig.colorbar(
        image,
        ax=ax,
        shrink=0.75,
        label="Backscatter / change (dB)"
    )

    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / filename,
        dpi=250,
        bbox_inches="tight"
    )

    plt.close()

# ============================================================
# ANNUAL BACKSCATTER MAPS
# ============================================================

for band in [1, 2, 4, 5, 7, 8]:

    save_map(
        arrays[band],
        BANDS[band],
        f"Band_{band:02d}.png"
    )

# ============================================================
# TEMPORAL CHANGE MAPS
# ============================================================

for band in [10, 11, 12, 13, 14, 15]:

    save_map(
        arrays[band],
        BANDS[band],
        f"Band_{band:02d}_Change.png",
        cmap="RdBu_r",
        symmetric=True
    )

# ============================================================
# VV-VH DIFFERENCE MAPS
# ============================================================

for band in [3, 6, 9]:

    save_map(
        arrays[band],
        BANDS[band],
        f"Band_{band:02d}_Difference.png"
    )

# ============================================================
# COMPLETE
# ============================================================

print("\n" + "=" * 70)
print("VISUALIZATION COMPLETED")
print("=" * 70)

print(f"Generated 15 maps in:\n{OUTPUT_DIR}")
