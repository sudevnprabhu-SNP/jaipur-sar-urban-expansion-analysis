
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio

from rasterio.features import geometry_mask

# ============================================================
# PATHS
# ============================================================

PROJECT_DIR = Path(
    r"C:\Users\ssat-\Documents\RemoteSensing_Projects"
    r"\Project_02_Jaipur_SAR_Urban_Expansion"
)

RASTER_DIR = (
    PROJECT_DIR / "data" / "processed" / "aligned_utm43n"
)

BOUNDARY_FILE = (
    PROJECT_DIR
    / "data"
    / "boundaries"
    / "Jaipur_JMC_Municipal_Boundary.geojson"
)

OUTPUT_DIR = (
    PROJECT_DIR / "reports" / "sar_coverage_analysis"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

YEARS = [2016, 2020, 2025]
POLS = ["VV", "VH"]

# ============================================================
# LOAD BOUNDARY
# ============================================================

boundary = gpd.read_file(BOUNDARY_FILE)

if boundary.empty or boundary.crs is None:
    raise ValueError("Municipal boundary is empty or has no CRS.")

# ============================================================
# AUDIT EACH ALIGNED RASTER
# ============================================================

records = []

print("=" * 75)
print("SAR PIXEL VALUE AND NODATA AUDIT")
print("=" * 75)

for year in YEARS:
    for pol in POLS:

        path = (
            RASTER_DIR
            / f"Jaipur_S1_{year}_{pol}_UTM43N_10m.tif"
        )

        if not path.exists():
            raise FileNotFoundError(path)

        print("\n" + "-" * 75)
        print(f"{year} {pol}")
        print("-" * 75)

        with rasterio.open(path) as src:

            if src.crs is None:
                raise ValueError(f"Missing CRS: {path}")

            boundary_projected = boundary.to_crs(src.crs)

            municipal_geometry = (
                boundary_projected.geometry.union_all()
            )

            inside = geometry_mask(
                [municipal_geometry],
                out_shape=(src.height, src.width),
                transform=src.transform,
                invert=True,
                all_touched=False
            )

            data = src.read(1, masked=True)

            values = np.asarray(data.data, dtype=np.float64)

            raster_mask = np.ma.getmaskarray(data)

            finite = np.isfinite(values)

            valid_candidate = inside & ~raster_mask & finite

            samples = values[valid_candidate]

            if samples.size == 0:
                raise ValueError(
                    f"No readable pixels inside municipality: {path}"
                )

            zero_count = int(np.count_nonzero(samples == 0))
            near_zero_count = int(
                np.count_nonzero(np.abs(samples) <= 1e-6)
            )

            positive_count = int(np.count_nonzero(samples > 0))
            negative_count = int(np.count_nonzero(samples < 0))

            q = np.percentile(
                samples,
                [0, 1, 5, 25, 50, 75, 95, 99, 100]
            )

            print(f"File: {path.name}")
            print(f"CRS: {src.crs}")
            print(f"Data type: {src.dtypes[0]}")
            print(f"NoData metadata: {src.nodata}")
            print(f"Mask flags: {src.mask_flag_enums}")
            print(f"Municipal pixels: {int(inside.sum()):,}")
            print(f"Unmasked finite pixels: {len(samples):,}")
            print(f"Zero pixels: {zero_count:,}")
            print(f"Near-zero pixels: {near_zero_count:,}")
            print(f"Positive pixels: {positive_count:,}")
            print(f"Negative pixels: {negative_count:,}")

            print("\nPixel-value distribution:")
            print(f"Minimum: {q[0]:.6f}")
            print(f"1st percentile: {q[1]:.6f}")
            print(f"5th percentile: {q[2]:.6f}")
            print(f"25th percentile: {q[3]:.6f}")
            print(f"Median: {q[4]:.6f}")
            print(f"75th percentile: {q[5]:.6f}")
            print(f"95th percentile: {q[6]:.6f}")
            print(f"99th percentile: {q[7]:.6f}")
            print(f"Maximum: {q[8]:.6f}")

            tags = src.tags()

            print("\nRaster tags:")
            for key, value in tags.items():
                print(f"{key}: {value}")

            records.append({
                "year": year,
                "polarization": pol,
                "filename": path.name,
                "crs": str(src.crs),
                "dtype": src.dtypes[0],
                "nodata_metadata": src.nodata,
                "mask_flags": str(src.mask_flag_enums),
                "municipal_pixels": int(inside.sum()),
                "unmasked_finite_pixels": len(samples),
                "zero_pixels": zero_count,
                "zero_percentage": zero_count / len(samples) * 100,
                "near_zero_pixels": near_zero_count,
                "positive_pixels": positive_count,
                "negative_pixels": negative_count,
                "minimum": q[0],
                "p01": q[1],
                "p05": q[2],
                "p25": q[3],
                "median": q[4],
                "p75": q[5],
                "p95": q[6],
                "p99": q[7],
                "maximum": q[8]
            })

# ============================================================
# SAVE REPORT
# ============================================================

df = pd.DataFrame(records)

report_file = OUTPUT_DIR / "SAR_Pixel_Value_Audit.csv"

df.to_csv(report_file, index=False)

print("\n" + "=" * 75)
print("AUDIT COMPLETED")
print("=" * 75)

print(df[
    [
        "year",
        "polarization",
        "nodata_metadata",
        "zero_pixels",
        "zero_percentage",
        "minimum",
        "median",
        "maximum"
    ]
].to_string(index=False))

print("\nReport saved:")
print(report_file)

print("\nNo original raster was modified.")
