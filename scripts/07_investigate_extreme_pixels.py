
from pathlib import Path
import numpy as np
import rasterio

PROJECT_DIR = Path(__file__).resolve().parents[1]

ALIGNED_DIR = (
    PROJECT_DIR / "data" / "processed" / "aligned_utm43n"
)

SOURCE_DIR = PROJECT_DIR / "data" / "processed"

YEARS = [2016, 2020, 2025]
THRESHOLDS = [1, 5, 10, 50, 100, 500]


def inspect_raster(filepath, label):

    with rasterio.open(filepath) as src:

        data = src.read(1)

        valid = (
            np.isfinite(data)
            & (data != src.nodata)
        )

        values = data[valid]

        print(f"\n{label}")
        print("-" * 55)

        print(f"Maximum: {values.max():.6f}")
        print(f"99.9 percentile: {np.percentile(values, 99.9):.6f}")

        print("\nThreshold counts:")

        for threshold in THRESHOLDS:
            count = np.count_nonzero(
                valid & (data > threshold)
            )

            print(
                f"  Above {threshold:>3}: {count:,} pixels"
            )

        # Locate the maximum pixel
        masked = np.where(valid, data, -np.inf)

        row, col = np.unravel_index(
            np.argmax(masked),
            data.shape
        )

        x, y = rasterio.transform.xy(
            src.transform,
            row,
            col
        )

        print("\nMaximum pixel location:")
        print(f"  Row: {row}")
        print(f"  Column: {col}")
        print(f"  Easting: {x:.2f} m")
        print(f"  Northing: {y:.2f} m")

        # Check whether extreme pixels are near raster edges
        extreme = valid & (data > 100)

        edge_width = 20

        edge_mask = np.zeros(data.shape, dtype=bool)

        edge_mask[:edge_width, :] = True
        edge_mask[-edge_width:, :] = True
        edge_mask[:, :edge_width] = True
        edge_mask[:, -edge_width:] = True

        extreme_count = np.count_nonzero(extreme)

        edge_count = np.count_nonzero(
            extreme & edge_mask
        )

        if extreme_count:
            print(
                f"\nPixels above 100 near edges: "
                f"{edge_count:,} / {extreme_count:,}"
            )


for year in YEARS:

    aligned_file = (
        ALIGNED_DIR
        / f"Jaipur_S1_{year}_VV_UTM43N_10m.tif"
    )

    original_file = (
        SOURCE_DIR
        / f"Jaipur_S1_{year}_VV_singleband.tif"
    )

    inspect_raster(
        original_file,
        f"{year} ORIGINAL VV"
    )

    inspect_raster(
        aligned_file,
        f"{year} ALIGNED VV"
    )

print("\nExtreme-value investigation completed.")
