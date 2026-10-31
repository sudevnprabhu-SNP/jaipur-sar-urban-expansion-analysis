
from pathlib import Path

import numpy as np
import rasterio
import matplotlib.pyplot as plt

PROJECT_DIR = Path(
    r"C:\Users\ssat-\Documents\RemoteSensing_Projects"
    r"\Project_02_Jaipur_SAR_Urban_Expansion"
)

FEATURE_DIR = (
    PROJECT_DIR / "data" / "processed" / "sar_features"
)

OUTPUT_DIR = (
    PROJECT_DIR / "reports" / "sar_feature_analysis"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

YEARS = [2016, 2020, 2025]

FEATURES = {
    "VV_VH_Ratio_dB": "VV/VH Ratio (dB)",
    "DualPol_Total_Backscatter_dB":
        "Dual-Polarization Total Backscatter (dB)"
}

# --------------------------------------------------
# PROCESS EACH FEATURE
# --------------------------------------------------

for feature_name, title in FEATURES.items():

    print("\n" + "=" * 65)
    print(title)
    print("=" * 65)

    arrays = {}
    statistics = {}

    for year in YEARS:

        path = (
            FEATURE_DIR
            / f"Jaipur_S1_{year}_{feature_name}.tif"
        )

        with rasterio.open(path) as src:

            data = src.read(1)

            valid = (
                (src.read_masks(1) > 0)
                & np.isfinite(data)
            )

            values = data[valid]

            arrays[year] = data

            statistics[year] = {
                "valid_pixels": len(values),
                "minimum": np.min(values),
                "p01": np.percentile(values, 1),
                "p05": np.percentile(values, 5),
                "median": np.median(values),
                "p95": np.percentile(values, 95),
                "p99": np.percentile(values, 99),
                "maximum": np.max(values),
                "mean": np.mean(values)
            }

            print(f"\nYEAR: {year}")

            for key, value in statistics[year].items():
                print(f"{key}: {value}")

    # --------------------------------------------------
    # SPATIAL COMPARISON MAPS
    # --------------------------------------------------

    fig, axes = plt.subplots(
        1, 3, figsize=(19, 7)
    )

    # Common colour limits for all years
    all_values = np.concatenate([
        arrays[year][
            (arrays[year] != -9999)
            & np.isfinite(arrays[year])
        ]
        for year in YEARS
    ])

    vmin = np.percentile(all_values, 2)
    vmax = np.percentile(all_values, 98)

    for ax, year in zip(axes, YEARS):

        data = arrays[year].copy()
        data[data == -9999] = np.nan

        im = ax.imshow(
            data,
            cmap="viridis",
            vmin=vmin,
            vmax=vmax
        )

        ax.set_title(str(year))
        ax.set_xlabel("Column")
        ax.set_ylabel("Row")

    fig.suptitle(
        f"Temporal {title} Comparison",
        fontsize=15
    )

    fig.colorbar(
        im,
        ax=axes,
        label=title,
        shrink=0.8
    )

    plt.tight_layout()

    map_path = (
        OUTPUT_DIR
        / f"{feature_name}_spatial_comparison.png"
    )

    plt.savefig(
        map_path,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    # --------------------------------------------------
    # DISTRIBUTION COMPARISON
    # --------------------------------------------------

    fig, ax = plt.subplots(figsize=(10, 6))

    for year in YEARS:

        data = arrays[year]
        values = data[
            (data != -9999) & np.isfinite(data)
        ]

        # Random sample for plotting
        rng = np.random.default_rng(42 + year)

        sample = rng.choice(
            values,
            size=min(200000, len(values)),
            replace=False
        )

        ax.hist(
            sample,
            bins=120,
            density=True,
            histtype="step",
            linewidth=1.5,
            label=str(year)
        )

    ax.set_title(f"Distribution of {title}")
    ax.set_xlabel(title)
    ax.set_ylabel("Probability Density")
    ax.legend(title="Year")
    ax.grid(alpha=0.25)

    plt.tight_layout()

    histogram_path = (
        OUTPUT_DIR
        / f"{feature_name}_histogram.png"
    )

    plt.savefig(
        histogram_path,
        dpi=300
    )

    plt.close()

    print("\nSaved:", map_path)
    print("Saved:", histogram_path)

print("\nFEATURE VISUALIZATION COMPLETED")
print("Output directory:", OUTPUT_DIR)
