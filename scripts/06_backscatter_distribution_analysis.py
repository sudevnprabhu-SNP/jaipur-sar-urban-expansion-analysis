
from pathlib import Path
import numpy as np
import rasterio
import matplotlib.pyplot as plt

PROJECT_DIR = Path(__file__).resolve().parents[1]

INPUT_DIR = (
    PROJECT_DIR / "data" / "processed" / "aligned_utm43n"
)

OUTPUT_DIR = (
    PROJECT_DIR / "reports" / "quality_analysis"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

YEARS = [2016, 2020, 2025]
POLARIZATIONS = ["VV", "VH"]

for pol in POLARIZATIONS:

    fig, axes = plt.subplots(
        3, 2,
        figsize=(13, 14)
    )

    for row, year in enumerate(YEARS):

        filename = (
            f"Jaipur_S1_{year}_{pol}_UTM43N_10m.tif"
        )

        filepath = INPUT_DIR / filename

        with rasterio.open(filepath) as src:

            data = src.read(1)

            valid_mask = np.isfinite(data)

            if src.nodata is not None:
                valid_mask &= data != src.nodata

            valid = data[valid_mask]

            p999 = np.percentile(valid, 99.9)

            # Full distribution, using logarithmic x-axis
            ax = axes[row, 0]

            ax.hist(
                valid,
                bins=150,
                range=(0, p999),
                density=True
            )

            ax.set_xscale("log")
            ax.set_title(
                f"{year} {pol} - Distribution"
            )
            ax.set_xlabel("Linear Sigma0")
            ax.set_ylabel("Density")
            ax.grid(alpha=0.25)

            # Spatial locations of extreme pixels
            ax = axes[row, 1]

            extreme_mask = (
                valid_mask & (data > p999)
            )

            extreme_count = np.count_nonzero(
                extreme_mask
            )

            ax.imshow(
                extreme_mask,
                cmap="gray",
                interpolation="nearest"
            )

            ax.set_title(
                f"{year} {pol} - Above 99.9th percentile "
                f"({extreme_count:,} pixels)"
            )

            ax.set_axis_off()

            print(
                f"{year} {pol}: "
                f"99.9th percentile = {p999:.6f}, "
                f"extreme pixels = {extreme_count:,}"
            )

    plt.tight_layout()

    output_file = (
        OUTPUT_DIR / f"{pol}_distribution_analysis.png"
    )

    plt.savefig(
        output_file,
        dpi=200,
        bbox_inches="tight"
    )

    plt.close(fig)

    print(f"Saved: {output_file}")

print("\nDistribution analysis completed.")
