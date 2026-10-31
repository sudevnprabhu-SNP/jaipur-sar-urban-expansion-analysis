from pathlib import Path
import csv
import numpy as np
import rasterio

# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

PROJECT_DIR = Path(
    r"C:\Users\ssat-\Documents\RemoteSensing_Projects"
    r"\Project_02_Jaipur_SAR_Urban_Expansion"
)

PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
ALIGNED_DIR = PROCESSED_DIR / "aligned_utm43n"

REPORT_DIR = PROJECT_DIR / "reports" / "quality_analysis"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

YEARS = [2016, 2020, 2025]
POLARIZATIONS = ["VV", "VH"]


# --------------------------------------------------
# INSPECT ONE RASTER
# --------------------------------------------------

def inspect_raster(path):

    with rasterio.open(path) as src:

        data = src.read(1)

        # Rasterio's interpretation of the internal mask
        mask = src.read_masks(1)

        # Dataset-level mask
        dataset_mask = src.dataset_mask()

        valid_mask = mask > 0
        finite_mask = np.isfinite(data)

        valid_pixels = np.count_nonzero(valid_mask)
        invalid_pixels = valid_mask.size - valid_pixels

        finite_pixels = np.count_nonzero(finite_mask)
        zero_pixels = np.count_nonzero(data == 0)
        negative_pixels = np.count_nonzero(data < 0)

        valid_finite = valid_mask & finite_mask

        if np.any(valid_finite):
            minimum = float(np.min(data[valid_finite]))
            maximum = float(np.max(data[valid_finite]))
            mean = float(np.mean(data[valid_finite]))
        else:
            minimum = maximum = mean = np.nan

        dataset_valid = np.count_nonzero(dataset_mask > 0)

        result = {
            "file": path.name,
            "width": src.width,
            "height": src.height,
            "crs": str(src.crs),
            "nodata": src.nodata,
            "mask_flags": str(src.mask_flag_enums),
            "mask_valid_pixels": valid_pixels,
            "mask_invalid_pixels": invalid_pixels,
            "mask_valid_percent": (
                valid_pixels / mask.size * 100
            ),
            "dataset_mask_valid_pixels": dataset_valid,
            "finite_pixels": finite_pixels,
            "zero_pixels": zero_pixels,
            "negative_pixels": negative_pixels,
            "minimum": minimum,
            "maximum": maximum,
            "mean": mean,
        }

        print("\n" + "=" * 65)
        print(path.name)
        print("=" * 65)

        for key, value in result.items():
            if key != "file":
                print(f"{key}: {value}")

        return result


# --------------------------------------------------
# CHECK ORIGINAL SINGLE-BAND RASTERS
# --------------------------------------------------

results = []

print("\nORIGINAL SINGLE-BAND RASTERS")

for year in YEARS:
    for pol in POLARIZATIONS:

        path = (
            PROCESSED_DIR
            / f"Jaipur_S1_{year}_{pol}_singleband.tif"
        )

        if path.exists():
            results.append(inspect_raster(path))
        else:
            print(f"\nMISSING: {path}")


# --------------------------------------------------
# CHECK ALIGNED RASTERS
# --------------------------------------------------

print("\n\nALIGNED UTM43N RASTERS")

for year in YEARS:
    for pol in POLARIZATIONS:

        path = (
            ALIGNED_DIR
            / f"Jaipur_S1_{year}_{pol}_UTM43N_10m.tif"
        )

        if path.exists():
            results.append(inspect_raster(path))
        else:
            print(f"\nMISSING: {path}")


# --------------------------------------------------
# SAVE REPORT
# --------------------------------------------------

csv_path = REPORT_DIR / "nodata_footprint_audit.csv"

if results:

    fieldnames = list(results[0].keys())

    with open(csv_path, "w", newline="", encoding="utf-8") as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(results)

    print("\n" + "=" * 65)
    print("AUDIT COMPLETED")
    print("=" * 65)
    print(f"Report saved to: {csv_path}")

else:
    print("No raster files were found.")