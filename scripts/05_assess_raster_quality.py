
from pathlib import Path
import numpy as np
import rasterio

PROJECT_DIR = Path(__file__).resolve().parents[1]
INPUT_DIR = (
    PROJECT_DIR / "data" / "processed" / "aligned_utm43n"
)

YEARS = [2016, 2020, 2025]
POLARIZATIONS = ["VV", "VH"]

for year in YEARS:
    for pol in POLARIZATIONS:

        filename = (
            f"Jaipur_S1_{year}_{pol}_UTM43N_10m.tif"
        )
        filepath = INPUT_DIR / filename

        print("\n" + "=" * 55)
        print(f"FILE: {filename}")

        if not filepath.exists():
            raise FileNotFoundError(filepath)

        with rasterio.open(filepath) as src:

            data = src.read(1)

            # Identify valid pixels
            valid_mask = np.isfinite(data)

            if src.nodata is not None:
                valid_mask &= data != src.nodata

            valid = data[valid_mask]

            total_pixels = data.size
            valid_pixels = valid.size
            invalid_pixels = total_pixels - valid_pixels

            if valid_pixels == 0:
                raise ValueError(
                    f"No valid pixels found in {filename}"
                )

            print(f"CRS:             {src.crs}")
            print(f"Dimensions:      {src.width} x {src.height}")
            print(f"Total pixels:    {total_pixels:,}")
            print(f"Valid pixels:    {valid_pixels:,}")
            print(f"Invalid pixels:  {invalid_pixels:,}")
            print(
                f"Valid coverage:  "
                f"{valid_pixels / total_pixels * 100:.2f}%"
            )

            print("\nPIXEL VALUE STATISTICS")
            print(f"Minimum:         {np.min(valid):.6f}")
            print(f"Maximum:         {np.max(valid):.6f}")
            print(f"Mean:            {np.mean(valid):.6f}")
            print(f"Median:          {np.median(valid):.6f}")
            print(f"Standard dev:    {np.std(valid):.6f}")

            print("\nPERCENTILES")
            for percentile in [1, 5, 25, 50, 75, 95, 99, 99.9]:
                value = np.percentile(valid, percentile)
                print(f"{percentile:5.1f}%:          {value:.6f}")

            print("\nADDITIONAL CHECKS")
            print(f"Zero pixels:     {np.count_nonzero(valid == 0):,}")
            print(f"Negative pixels: {np.count_nonzero(valid < 0):,}")

print("\nRaster quality assessment completed.")
