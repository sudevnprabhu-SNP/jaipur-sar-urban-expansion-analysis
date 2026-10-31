from pathlib import Path

import numpy as np
import rasterio

PROJECT_DIR = Path(
    r"C:\Users\ssat-\Documents\RemoteSensing_Projects"
    r"\Project_02_Jaipur_SAR_Urban_Expansion"
)

ALIGNED_DIR = (
    PROJECT_DIR / "data" / "processed" / "aligned_utm43n"
)

OUTPUT_DIR = (
    PROJECT_DIR / "data" / "processed"
    / "common_footprint"
)

REPORT_DIR = (
    PROJECT_DIR / "reports" / "quality_analysis"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

YEARS = [2016, 2020, 2025]
POLS = ["VV", "VH"]

reference_profile = None
common_masks = {}
individual_masks = {}

# --------------------------------------------------
# READ AND VERIFY MASKS
# --------------------------------------------------

for pol in POLS:

    masks = []

    print(f"\nPOLARIZATION: {pol}")

    for year in YEARS:

        path = (
            ALIGNED_DIR
            / f"Jaipur_S1_{year}_{pol}_UTM43N_10m.tif"
        )

        with rasterio.open(path) as src:

            mask = src.read_masks(1) > 0

            if reference_profile is None:
                reference_profile = src.profile.copy()

            if src.width != reference_profile["width"]:
                raise ValueError("Raster width mismatch")

            if src.height != reference_profile["height"]:
                raise ValueError("Raster height mismatch")

            if src.transform != reference_profile["transform"]:
                raise ValueError("Raster transform mismatch")

            if src.crs != reference_profile["crs"]:
                raise ValueError("Raster CRS mismatch")

            masks.append(mask)

            print(
                f"{year}: "
                f"{np.count_nonzero(mask):,} valid pixels"
            )

    individual_masks[pol] = masks

    # Pixels valid in every year
    common = np.logical_and.reduce(masks)

    common_masks[pol] = common

    print(
        f"Common valid pixels ({pol}): "
        f"{np.count_nonzero(common):,}"
    )

# --------------------------------------------------
# VERIFY VV AND VH MASK CONSISTENCY
# --------------------------------------------------

print("\nVV / VH MASK COMPARISON")

for year_index, year in enumerate(YEARS):

    vv_mask = individual_masks["VV"][year_index]
    vh_mask = individual_masks["VH"][year_index]

    difference = np.count_nonzero(vv_mask != vh_mask)

    print(f"{year}: {difference:,} differing pixels")

# --------------------------------------------------
# COMMON MASK ACROSS ALL YEARS AND POLARIZATIONS
# --------------------------------------------------

common_all = (
    common_masks["VV"] & common_masks["VH"]
)

total_pixels = common_all.size
common_pixels = np.count_nonzero(common_all)

print("\n" + "=" * 55)
print("FINAL COMMON FOOTPRINT")
print("=" * 55)

print(f"Total grid pixels: {total_pixels:,}")
print(f"Common valid pixels: {common_pixels:,}")

print(
    f"Common grid proportion: "
    f"{common_pixels / total_pixels * 100:.4f}%"
)

# --------------------------------------------------
# SAVE COMMON MASK
# --------------------------------------------------

profile = reference_profile.copy()

profile.update(
    driver="GTiff",
    count=1,
    dtype="uint8",
    nodata=0,
    compress="lzw"
)

output_path = OUTPUT_DIR / "Jaipur_Common_Valid_Footprint.tif"

with rasterio.open(output_path, "w", **profile) as dst:

    dst.write(common_all.astype("uint8"), 1)

    dst.set_band_description(
        1,
        "Common valid-grid mask across 2016, 2020 and 2025"
    )

print(f"\nCommon footprint saved: {output_path}")