from pathlib import Path

import numpy as np
import rasterio
import matplotlib.pyplot as plt

PROJECT_DIR = Path(
    r"C:\Users\ssat-\Documents\RemoteSensing_Projects"
    r"\Project_02_Jaipur_SAR_Urban_Expansion"
)

ALIGNED_DIR = (
    PROJECT_DIR / "data" / "processed" / "aligned_utm43n"
)

OUTPUT_DIR = (
    PROJECT_DIR / "reports" / "quality_analysis"
    / "nodata_footprints"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

YEARS = [2016, 2020, 2025]


fig, axes = plt.subplots(
    1, 3,
    figsize=(18, 7)
)

for ax, year in zip(axes, YEARS):

    path = (
        ALIGNED_DIR
        / f"Jaipur_S1_{year}_VV_UTM43N_10m.tif"
    )

    with rasterio.open(path) as src:

        mask = src.read_masks(1)

        valid = mask > 0
        invalid = ~valid

        valid_percent = np.mean(valid) * 100

        ax.imshow(
            valid,
            cmap="gray",
            interpolation="nearest"
        )

        ax.set_title(
            f"{year}\nValid grid: {valid_percent:.3f}%"
        )

        ax.set_xlabel("Column")
        ax.set_ylabel("Row")

        print(
            f"{year}: "
            f"Valid={np.count_nonzero(valid)}, "
            f"Invalid={np.count_nonzero(invalid)}"
        )

fig.suptitle(
    "Spatial Distribution of NoData Pixels "
    "in Aligned Sentinel-1 VV Rasters",
    fontsize=14
)

plt.tight_layout()

output_path = OUTPUT_DIR / "nodata_footprint_comparison.png"

plt.savefig(
    output_path,
    dpi=300,
    bbox_inches="tight"
)

plt.show()

print(f"\nSaved: {output_path}")