
from pathlib import Path
import math

import rasterio
from rasterio.warp import (
    calculate_default_transform,
    transform_bounds,
    reproject,
    Resampling
)
from rasterio.transform import from_origin


# --------------------------------------------------
# 1. PROJECT SETTINGS
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parents[1]

INPUT_DIR = PROJECT_DIR / "data" / "processed"
OUTPUT_DIR = INPUT_DIR / "aligned_utm43n"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

YEARS = [2016, 2020, 2025]
POLARIZATIONS = ["VV", "VH"]

TARGET_CRS = "EPSG:32643"
TARGET_RESOLUTION = 10.0
OUTPUT_NODATA = -9999.0


# --------------------------------------------------
# 2. IDENTIFY INPUT FILES
# --------------------------------------------------

input_files = []

for year in YEARS:
    for polarization in POLARIZATIONS:
        filename = (
            f"Jaipur_S1_{year}_{polarization}_singleband.tif"
        )

        filepath = INPUT_DIR / filename

        if not filepath.exists():
            raise FileNotFoundError(
                f"Missing input file: {filepath}"
            )

        input_files.append(filepath)


# --------------------------------------------------
# 3. CALCULATE COMMON PROJECTED EXTENT
# --------------------------------------------------

projected_bounds = []

print("\nCalculating projected bounds...")

for filepath in input_files:

    with rasterio.open(filepath) as src:

        if src.crs is None:
            raise ValueError(
                f"Missing CRS: {filepath.name}"
            )

        bounds = transform_bounds(
            src.crs,
            TARGET_CRS,
            *src.bounds,
            densify_pts=21
        )

        projected_bounds.append(bounds)

        print(f"{filepath.name}")
        print(f"  Projected bounds: {bounds}")


# Find the intersection shared by all six rasters
left = max(b[0] for b in projected_bounds)
bottom = max(b[1] for b in projected_bounds)
right = min(b[2] for b in projected_bounds)
top = min(b[3] for b in projected_bounds)

if left >= right or bottom >= top:
    raise ValueError(
        "The six rasters do not have a common overlapping area."
    )


# Snap bounds inward to a common 10 m grid
resolution = TARGET_RESOLUTION

left = math.ceil(left / resolution) * resolution
bottom = math.ceil(bottom / resolution) * resolution
right = math.floor(right / resolution) * resolution
top = math.floor(top / resolution) * resolution

width = int(round((right - left) / resolution))
height = int(round((top - bottom) / resolution))

if width <= 0 or height <= 0:
    raise ValueError("Invalid common grid dimensions.")

target_transform = from_origin(
    left,
    top,
    resolution,
    resolution
)

print("\nCOMMON GRID")
print(f"CRS: {TARGET_CRS}")
print(f"Resolution: {resolution} metres")
print(f"Width: {width}")
print(f"Height: {height}")
print(f"Bounds: {left}, {bottom}, {right}, {top}")


# --------------------------------------------------
# 4. REPROJECT AND ALIGN ALL SIX RASTERS
# --------------------------------------------------

print("\nStarting reprojection and alignment...")

for filepath in input_files:

    output_name = (
        filepath.stem.replace(
            "_singleband",
            "_UTM43N_10m"
        ) + ".tif"
    )

    output_path = OUTPUT_DIR / output_name

    print(f"\nProcessing: {filepath.name}")

    with rasterio.open(filepath) as src:

        source_data = src.read(1)

        destination_data = (
            __import__("numpy").full(
                (height, width),
                OUTPUT_NODATA,
                dtype="float32"
            )
        )

        reproject(
            source=source_data,
            destination=destination_data,
            src_transform=src.transform,
            src_crs=src.crs,
            src_nodata=src.nodata,
            dst_transform=target_transform,
            dst_crs=TARGET_CRS,
            dst_nodata=OUTPUT_NODATA,
            resampling=Resampling.bilinear
        )

        profile = {
            "driver": "GTiff",
            "height": height,
            "width": width,
            "count": 1,
            "dtype": "float32",
            "crs": TARGET_CRS,
            "transform": target_transform,
            "nodata": OUTPUT_NODATA,
            "compress": "deflate",
            "predictor": 3
        }

        with rasterio.open(
            output_path,
            "w",
            **profile
        ) as dst:

            dst.write(destination_data, 1)

            dst.set_band_description(
                1,
                src.descriptions[0]
                or filepath.stem
            )

        print(f"  Saved: {output_name}")


# --------------------------------------------------
# 5. VERIFY COMMON GRID
# --------------------------------------------------

print("\nFINAL ALIGNMENT VALIDATION")

reference = None

for filepath in sorted(OUTPUT_DIR.glob("*.tif")):

    with rasterio.open(filepath) as src:

        current = (
            src.crs,
            src.width,
            src.height,
            src.transform,
            src.count
        )

        if reference is None:
            reference = current
            status = "PASS"
        elif current == reference:
            status = "PASS"
        else:
            status = "FAIL"

        print(f"\n{filepath.name}")
        print(f"  CRS: {src.crs}")
        print(f"  Dimensions: {src.width} x {src.height}")
        print(f"  Resolution: {src.res}")
        print(f"  Bands: {src.count}")
        print(f"  Validation: {status}")

        if status == "FAIL":
            raise ValueError(
                "Output rasters do not share the same grid."
            )

print("\nAll six rasters aligned successfully.")
