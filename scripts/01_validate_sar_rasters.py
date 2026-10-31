import numpy as np
from pathlib import Path
import rasterio

# Project directory
PROJECT_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"

# Six expected GeoTIFF files
raster_files = [
    "Jaipur_S1_2016_VV_TC.tif",
    "Jaipur_S1_2016_VH_TC.tif",
    "Jaipur_S1_2020_VV_TC.tif",
    "Jaipur_S1_2020_VH_TC.tif",
    "Jaipur_S1_2025_VV_TC.tif",
    "Jaipur_S1_2025_VH_TC.tif",
]

print("=" * 65)
print("JAIPUR SAR PROJECT - RASTER VALIDATION")
print("=" * 65)

for filename in raster_files:

    filepath = PROCESSED_DIR / filename

    print(f"\nFILE: {filename}")
    print("-" * 65)

    if not filepath.exists():
        print("ERROR: File not found!")
        continue

    with rasterio.open(filepath) as src:

        print("\nBAND VALUE INSPECTION:")

        for i in range(1, src.count + 1):

            # Read a small sample rather than the entire raster
            sample = src.read(
                i,
                out_shape=(500, 500)
            )

            valid = sample[np.isfinite(sample)]

            print(f"\nBand {i}:")
            print(f"  Minimum : {np.min(valid):.6f}")
            print(f"  Maximum : {np.max(valid):.6f}")
            print(f"  Mean    : {np.mean(valid):.6f}")
            print(f"  Std Dev : {np.std(valid):.6f}")

        print(f"CRS              : {src.crs}")
        print(f"Dimensions       : {src.width} x {src.height}")
        print(f"Band count       : {src.count}")
        print(f"Band descriptions: {src.descriptions}")
        print(f"Band units       : {src.units}")
        print(f"Band scales      : {src.scales}")
        print(f"Band offsets     : {src.offsets}")

        for i in range(1, src.count + 1):
            print(f"Band {i} metadata: {src.tags(i)}")
        print(f"Resolution       : {src.res}")
        print(f"Bounds           : {src.bounds}")
        print(f"Data type        : {src.dtypes}")
        print(f"NoData value     : {src.nodata}")
        print(f"File size        : {filepath.stat().st_size / (1024**3):.3f} GB")

print("\n" + "=" * 65)
print("VALIDATION COMPLETE")
print("=" * 65)
