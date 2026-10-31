
from pathlib import Path
import csv

import numpy as np
import rasterio
import matplotlib.pyplot as plt

# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

PROJECT_DIR = Path(
    r"C:\Users\ssat-\Documents\RemoteSensing_Projects"
    r"\Project_02_Jaipur_SAR_Urban_Expansion"
)

ALIGNED_DIR = (
    PROJECT_DIR / "data" / "processed" / "aligned_utm43n"
)

MASK_PATH = (
    PROJECT_DIR / "data" / "processed"
    / "common_footprint"
    / "Jaipur_Common_Valid_Footprint.tif"
)

OUTPUT_DIR = (
    PROJECT_DIR / "reports"
    / "temporal_backscatter_analysis"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

YEARS = [2016, 2020, 2025]
POLS = ["VV", "VH"]

# Fixed random seed for reproducible plotting samples
RNG = np.random.default_rng(42)

# --------------------------------------------------
# LOAD COMMON MASK
# --------------------------------------------------

with rasterio.open(MASK_PATH) as src:
    common_mask = src.read(1) == 1
    reference_transform = src.transform
    reference_crs = src.crs
    reference_shape = (src.height, src.width)

print("COMMON FOOTPRINT")
print("Valid pixels:", np.count_nonzero(common_mask))
print("Grid shape:", reference_shape)
print("CRS:", reference_crs)

# --------------------------------------------------
# STORAGE
# --------------------------------------------------

statistics = []
plot_samples = {pol: {} for pol in POLS}

# --------------------------------------------------
# PROCESS EACH POLARIZATION AND YEAR
# --------------------------------------------------

for pol in POLS:

    print("\n" + "=" * 60)
    print(f"POLARIZATION: {pol}")
    print("=" * 60)

    for year in YEARS:

        raster_path = (
            ALIGNED_DIR
            / f"Jaipur_S1_{year}_{pol}_UTM43N_10m.tif"
        )

        with rasterio.open(raster_path) as src:

            if (src.height, src.width) != reference_shape:
                raise ValueError("Raster dimensions do not match.")

            if src.transform != reference_transform:
                raise ValueError("Raster transform mismatch.")

            if src.crs != reference_crs:
                raise ValueError("Raster CRS mismatch.")

            linear_data = src.read(1)

            # Use only common valid pixels
            valid = (
                common_mask
                & (src.read_masks(1) > 0)
                & np.isfinite(linear_data)
                & (linear_data > 0)
            )

            linear_values = linear_data[valid]

        # Convert linear Sigma0 to dB
        db_values = 10.0 * np.log10(linear_values)

        # Statistical calculations
        result = {
            "year": year,
            "polarization": pol,
            "valid_pixels": len(db_values),
            "mean_db": float(np.mean(db_values)),
            "median_db": float(np.median(db_values)),
            "std_db": float(np.std(db_values)),
            "p05_db": float(np.percentile(db_values, 5)),
            "p25_db": float(np.percentile(db_values, 25)),
            "p75_db": float(np.percentile(db_values, 75)),
            "p95_db": float(np.percentile(db_values, 95)),
        }

        statistics.append(result)

        # Store a random sample for plotting
        sample_size = min(200_000, len(db_values))

        sample_indices = RNG.choice(
            len(db_values),
            size=sample_size,
            replace=False
        )

        plot_samples[pol][year] = db_values[sample_indices]

        print(
            f"{year}: "
            f"Mean={result['mean_db']:.3f} dB | "
            f"Median={result['median_db']:.3f} dB | "
            f"Std={result['std_db']:.3f} dB"
        )

        del linear_data, linear_values, db_values, valid

# --------------------------------------------------
# SAVE STATISTICAL SUMMARY
# --------------------------------------------------

csv_path = OUTPUT_DIR / "temporal_backscatter_statistics.csv"

with open(csv_path, "w", newline="", encoding="utf-8") as f:

    writer = csv.DictWriter(
        f,
        fieldnames=list(statistics[0].keys())
    )

    writer.writeheader()
    writer.writerows(statistics)

print("\nStatistics saved:", csv_path)

# --------------------------------------------------
# GENERATE HISTOGRAMS
# --------------------------------------------------

for pol in POLS:

    plt.figure(figsize=(10, 6))

    for year in YEARS:

        values = plot_samples[pol][year]

        plt.hist(
            values,
            bins=120,
            density=True,
            histtype="step",
            linewidth=1.5,
            label=str(year)
        )

    plt.title(
        f"Temporal {pol} Backscatter Distribution"
    )

    plt.xlabel("Sigma0 Backscatter (dB)")
    plt.ylabel("Probability Density")
    plt.legend(title="Year")
    plt.grid(alpha=0.25)

    plt.tight_layout()

    path = OUTPUT_DIR / f"{pol}_temporal_histogram.png"

    plt.savefig(path, dpi=300)
    plt.close()

    print("Saved:", path)

# --------------------------------------------------
# GENERATE BOXPLOTS
# --------------------------------------------------

for pol in POLS:

    data = [
        plot_samples[pol][year]
        for year in YEARS
    ]

    plt.figure(figsize=(9, 6))

    plt.boxplot(
        data,
        tick_labels=[str(year) for year in YEARS],
        showfliers=False
    )

    plt.title(
        f"Temporal {pol} Backscatter Comparison"
    )

    plt.xlabel("Year")
    plt.ylabel("Sigma0 Backscatter (dB)")
    plt.grid(axis="y", alpha=0.25)

    plt.tight_layout()

    path = OUTPUT_DIR / f"{pol}_temporal_boxplot.png"

    plt.savefig(path, dpi=300)
    plt.close()

    print("Saved:", path)

# --------------------------------------------------
# FINAL MESSAGE
# --------------------------------------------------

print("\n" + "=" * 60)
print("TEMPORAL BACKSCATTER ANALYSIS COMPLETED")
print("=" * 60)

print("Output directory:", OUTPUT_DIR)
