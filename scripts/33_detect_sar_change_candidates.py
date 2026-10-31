
from pathlib import Path
import numpy as np
import rasterio
import pandas as pd
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
    / "data"
    / "processed"
    / "change_detection"
)

REPORT_DIR = (
    PROJECT_DIR
    / "reports"
    / "change_detection"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

NODATA = -9999.0

# Band indices are 1-based
CHANGE_BANDS = {
    "VV_2016_2020": 10,
    "VH_2016_2020": 11,
    "VV_2020_2025": 12,
    "VH_2020_2025": 13,
    "VV_2016_2025": 14,
    "VH_2016_2025": 15,
}

# Percentile thresholds for exploratory candidate mapping
LOW_PERCENTILE = 5
HIGH_PERCENTILE = 95

# ============================================================
# LOAD FEATURE STACK
# ============================================================

print("=" * 70)
print("PRELIMINARY SAR CHANGE DETECTION")
print("=" * 70)

records = []

with rasterio.open(STACK_FILE) as src:

    profile = src.profile.copy()

    for feature_name, band_number in CHANGE_BANDS.items():

        print("\n" + "-" * 70)
        print(feature_name)
        print("-" * 70)

        data = src.read(band_number, masked=True)

        values = np.asarray(data.data, dtype=np.float32)

        valid = (
            ~np.ma.getmaskarray(data)
            & np.isfinite(values)
            & (values != NODATA)
        )

        sample = values[valid]

        if sample.size == 0:
            raise ValueError(f"No valid pixels: {feature_name}")

        low_threshold = np.percentile(
            sample, LOW_PERCENTILE
        )

        high_threshold = np.percentile(
            sample, HIGH_PERCENTILE
        )

        median = np.median(sample)

        positive = valid & (values >= high_threshold)
        negative = valid & (values <= low_threshold)

        print(f"Valid pixels: {sample.size:,}")
        print(f"Median change: {median:.3f} dB")
        print(f"5th percentile: {low_threshold:.3f} dB")
        print(f"95th percentile: {high_threshold:.3f} dB")
        print(f"High-change candidates: {positive.sum():,}")
        print(f"Low-change candidates: {negative.sum():,}")

        records.append({
            "feature": feature_name,
            "valid_pixels": int(sample.size),
            "median_change_db": float(median),
            "p05_db": float(low_threshold),
            "p95_db": float(high_threshold),
            "high_change_pixels": int(positive.sum()),
            "low_change_pixels": int(negative.sum()),
            "high_change_area_km2": float(positive.sum() * 0.0001),
            "low_change_area_km2": float(negative.sum() * 0.0001)
        })

        # ====================================================
        # SAVE CONTINUOUS CHANGE RASTER
        # ====================================================

        continuous_path = (
            OUTPUT_DIR / f"{feature_name}_continuous.tif"
        )

        out = np.full(values.shape, NODATA, dtype=np.float32)
        out[valid] = values[valid]

        output_profile = profile.copy()
        output_profile.update(
            count=1,
            dtype="float32",
            nodata=NODATA,
            compress="lzw",
            tiled=True,
            blockxsize=256,
            blockysize=256
        )

        with rasterio.open(
            continuous_path, "w", **output_profile
        ) as dst:
            dst.write(out, 1)
            dst.set_band_description(1, feature_name)

        # ====================================================
        # SAVE CANDIDATE MASK
        # 0 = valid, 1 = lower-tail decrease,
        # 2 = middle range, 3 = upper-tail increase,
        # 255 = NoData
        # ====================================================

        candidate = np.full(
            values.shape, 255, dtype=np.uint8
        )

        candidate[valid] = 2
        candidate[negative] = 1
        candidate[positive] = 3

        mask_path = (
            OUTPUT_DIR / f"{feature_name}_candidate_mask.tif"
        )

        mask_profile = output_profile.copy()
        mask_profile.update(
            dtype="uint8",
            nodata=255
        )

        with rasterio.open(
            mask_path, "w", **mask_profile
        ) as dst:
            dst.write(candidate, 1)

        # ====================================================
        # SAVE DIAGNOSTIC MAP
        # ====================================================

        fig, ax = plt.subplots(figsize=(10, 9))

        display = np.where(valid, values, np.nan)

        limit = max(
            abs(low_threshold),
            abs(high_threshold)
        )

        image = ax.imshow(
            display,
            cmap="RdBu_r",
            vmin=-limit,
            vmax=limit
        )

        ax.set_title(
            f"{feature_name} SAR Backscatter Change\n"
            f"Candidate tails: below {low_threshold:.2f} dB "
            f"and above {high_threshold:.2f} dB",
            fontsize=12,
            fontweight="bold"
        )

        ax.set_axis_off()

        fig.colorbar(
            image,
            ax=ax,
            shrink=0.75,
            label="Backscatter change (dB)"
        )

        plt.tight_layout()

        plt.savefig(
            REPORT_DIR / f"{feature_name}_change_map.png",
            dpi=250,
            bbox_inches="tight"
        )

        plt.close()

# ============================================================
# SAVE STATISTICS
# ============================================================

df = pd.DataFrame(records)

report_path = (
    REPORT_DIR / "SAR_Change_Candidate_Statistics.csv"
)

df.to_csv(report_path, index=False)

# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print("CHANGE DETECTION COMPLETED")
print("=" * 70)

print(df.to_string(index=False))

print("\nChange rasters:", OUTPUT_DIR)
print("Change maps:", REPORT_DIR)
print("Statistics:", report_path)

print("\nThese are exploratory SAR change candidates, not")
print("validated urban expansion labels.")
