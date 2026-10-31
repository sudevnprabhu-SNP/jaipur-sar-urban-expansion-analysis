
from pathlib import Path
import numpy as np
import rasterio

# Project directories
PROJECT_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"

# Based on the remembered SNAP band order:
# Band 1 = Sigma0_VH
# Band 2 = Sigma0_VV
BAND_MAP = {
    "VH": 1,
    "VV": 2
}

YEARS = [2016, 2020, 2025]


def extract_bands(year):
    vv_file = PROCESSED_DIR / f"Jaipur_S1_{year}_VV_TC.tif"
    vh_file = PROCESSED_DIR / f"Jaipur_S1_{year}_VH_TC.tif"

    if not vv_file.exists() or not vh_file.exists():
        raise FileNotFoundError(
            f"Missing input TIFF for {year}:\n"
            f"{vv_file}\n{vh_file}"
        )

    print(f"\nProcessing {year}...")

    with rasterio.open(vv_file) as vv_src, \
         rasterio.open(vh_file) as vh_src:

        # Check spatial metadata
        if (
            vv_src.width != vh_src.width
            or vv_src.height != vh_src.height
            or vv_src.transform != vh_src.transform
            or vv_src.crs != vh_src.crs
            or vv_src.count != vh_src.count
        ):
            raise ValueError(
                f"{year}: VV and VH input files have different metadata."
            )

        if vv_src.count != 2:
            raise ValueError(
                f"{year}: Expected 2 bands, found {vv_src.count}."
            )

        # Confirm whether the two named TIFFs contain identical data
        identical = True

        for _, window in vv_src.block_windows(1):
            vv_data = vv_src.read(window=window)
            vh_data = vh_src.read(window=window)

            if not np.array_equal(vv_data, vh_data, equal_nan=True):
                identical = False
                break

        if not identical:
            raise ValueError(
                f"{year}: The two input TIFFs are not identical. "
                "Stopping to avoid extracting from an uncertain source."
            )

        print("  Input TIFFs contain identical data.")

        # Single-band output profile
        profile = vv_src.profile.copy()
        profile.update(
            count=1,
            compress="deflate",
            predictor=3
        )

        # Extract VH and VV separately
        for polarization, band_index in BAND_MAP.items():

            output_file = (
                PROCESSED_DIR
                / f"Jaipur_S1_{year}_{polarization}_singleband.tif"
            )

            data = vv_src.read(band_index)

            with rasterio.open(output_file, "w", **profile) as dst:
                dst.write(data, 1)
                dst.set_band_description(
                    1, f"Sigma0_{polarization}"
                )

            print(
                f"  Saved: {output_file.name} "
                f"(source band {band_index})"
            )

    print(f"  {year} extraction completed.")


if __name__ == "__main__":
    for year in YEARS:
        extract_bands(year)

    print("\nAll three years processed successfully.")
