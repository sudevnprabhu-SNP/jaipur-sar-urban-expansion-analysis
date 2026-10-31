
from pathlib import Path
import numpy as np
import rasterio

PROJECT_DIR = Path(__file__).resolve().parents[1]

INPUT_DIR = PROJECT_DIR / "data" / "processed"

YEARS = [2016, 2020, 2025]

for year in YEARS:

    filepath = (
        INPUT_DIR /
        f"Jaipur_S1_{year}_VV_singleband.tif"
    )

    print("\n" + "=" * 65)
    print(f"YEAR: {year}")
    print("=" * 65)

    with rasterio.open(filepath) as src:

        data = src.read(1)

        valid = (
            np.isfinite(data)
            & (data != src.nodata)
        )

        values = data[valid]

        # Find the 20 highest pixel values
        flat_indices = np.argpartition(
            np.where(valid, data, -np.inf).ravel(),
            -20
        )[-20:]

        flat_indices = flat_indices[
            np.argsort(
                data.ravel()[flat_indices]
            )[::-1]
        ]

        print("\nTOP 20 VV PIXELS")

        for rank, flat_index in enumerate(
            flat_indices, start=1
        ):

            row, col = np.unravel_index(
                flat_index, data.shape
            )

            value = data[row, col]

            x, y = rasterio.transform.xy(
                src.transform, row, col
            )

            # Extract 5x5 neighbourhood
            r0 = max(0, row - 2)
            r1 = min(src.height, row + 3)
            c0 = max(0, col - 2)
            c1 = min(src.width, col + 3)

            neighbourhood = data[r0:r1, c0:c1]

            neighbourhood_valid = (
                np.isfinite(neighbourhood)
                & (neighbourhood != src.nodata)
            )

            local_values = neighbourhood[
                neighbourhood_valid
            ]

            local_median = np.median(local_values)
            local_mean = np.mean(local_values)

            if src.crs.is_geographic:
                location = (
                    f"Lon: {x:.6f}, Lat: {y:.6f}"
                )
            else:
                location = (
                    f"Easting: {x:.2f}, "
                    f"Northing: {y:.2f}"
                )

            print(
                f"\nRank {rank}: {value:.6f}"
            )
            print(f"  Row/Column: {row}/{col}")
            print(f"  Location: {location}")
            print(f"  Local 5x5 median: {local_median:.6f}")
            print(f"  Local 5x5 mean: {local_mean:.6f}")

            if local_median > 0:
                print(
                    f"  Value / local median: "
                    f"{value / local_median:.2f}"
                )

print("\nExtreme pixel inspection completed.")
