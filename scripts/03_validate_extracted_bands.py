from pathlib import Path
import rasterio

PROJECT_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"

YEARS = [2016, 2020, 2025]
POLARIZATIONS = ["VV", "VH"]

for year in YEARS:
    for pol in POLARIZATIONS:
        filename = (
            f"Jaipur_S1_{year}_{pol}_singleband.tif"
        )
        filepath = PROCESSED_DIR / filename

        print(f"\nChecking: {filename}")

        if not filepath.exists():
            print("  ERROR: File not found.")
            continue

        with rasterio.open(filepath) as src:
            print(f"  Bands:       {src.count}")
            print(f"  Dimensions:  {src.width} x {src.height}")
            print(f"  CRS:         {src.crs}")
            print(f"  Resolution:  {src.res}")
            print(f"  NoData:      {src.nodata}")
            print(f"  Description: {src.descriptions}")

            if src.count != 1:
                print("  VALIDATION FAILED: Expected one band.")
                continue

            data = src.read(1, masked=True)

            print(f"  Minimum:     {data.min():.6f}")
            print(f"  Maximum:     {data.max():.6f}")
            print(f"  Mean:        {data.mean():.6f}")
            print("  STATUS:      PASS")

print("\nValidation completed.")