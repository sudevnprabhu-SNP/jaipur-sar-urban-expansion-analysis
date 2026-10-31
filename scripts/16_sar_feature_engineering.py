
from pathlib import Path

import numpy as np
import rasterio

# --------------------------------------------------
# PATHS
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
    PROJECT_DIR / "data" / "processed"
    / "sar_features"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

YEARS = [2016, 2020, 2025]

# --------------------------------------------------
# LOAD COMMON MASK
# --------------------------------------------------

with rasterio.open(MASK_PATH) as src:

    common_mask = src.read(1) == 1
    reference_profile = src.profile.copy()

# --------------------------------------------------
# PROCESS EACH YEAR
# --------------------------------------------------

for year in YEARS:

    print("\n" + "=" * 55)
    print(f"PROCESSING YEAR: {year}")
    print("=" * 55)

    vv_path = (
        ALIGNED_DIR
        / f"Jaipur_S1_{year}_VV_UTM43N_10m.tif"
    )

    vh_path = (
        ALIGNED_DIR
        / f"Jaipur_S1_{year}_VH_UTM43N_10m.tif"
    )

    with rasterio.open(vv_path) as vv_src, \
         rasterio.open(vh_path) as vh_src:

        vv = vv_src.read(1)
        vh = vh_src.read(1)

        valid = (
            common_mask
            & (vv_src.read_masks(1) > 0)
            & (vh_src.read_masks(1) > 0)
            & np.isfinite(vv)
            & np.isfinite(vh)
            & (vv > 0)
            & (vh > 0)
        )

        if not np.array_equal(
            vv_src.transform, vh_src.transform
        ):
            raise ValueError("VV and VH grids do not match.")

    # --------------------------------------------------
    # FEATURE 1: VV/VH RATIO IN dB
    # --------------------------------------------------

    ratio_db = np.full(
        vv.shape, -9999, dtype=np.float32
    )

    ratio_db[valid] = (
        10.0 * np.log10(vv[valid] / vh[valid])
    )

    # --------------------------------------------------
    # FEATURE 2: DUAL-POLARIZATION TOTAL BACKSCATTER
    # --------------------------------------------------

    total_db = np.full(
        vv.shape, -9999, dtype=np.float32
    )

    total_db[valid] = (
        10.0 * np.log10(vv[valid] + vh[valid])
    )

    # --------------------------------------------------
    # SAVE FEATURES
    # --------------------------------------------------

    profile = reference_profile.copy()

    profile.update(
        driver="GTiff",
        count=1,
        dtype="float32",
        nodata=-9999.0,
        compress="lzw",
        predictor=3
    )

    features = {
        "VV_VH_Ratio_dB": ratio_db,
        "DualPol_Total_Backscatter_dB": total_db
    }

    for name, data in features.items():

        output_path = (
            OUTPUT_DIR / f"Jaipur_S1_{year}_{name}.tif"
        )

        with rasterio.open(
            output_path, "w", **profile
        ) as dst:

            dst.write(data, 1)
            dst.set_band_description(1, name)

        values = data[valid]

        print(f"\n{name}")
        print(f"Mean: {np.mean(values):.3f} dB")
        print(f"Median: {np.median(values):.3f} dB")
        print(f"Minimum: {np.min(values):.3f} dB")
        print(f"Maximum: {np.max(values):.3f} dB")

        print("Saved:", output_path)

    del vv, vh, ratio_db, total_db, valid

print("\n" + "=" * 55)
print("SAR FEATURE ENGINEERING COMPLETED")
print("Output directory:", OUTPUT_DIR)
print("=" * 55)
