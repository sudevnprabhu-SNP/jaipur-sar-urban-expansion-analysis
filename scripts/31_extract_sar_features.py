
from pathlib import Path
import numpy as np
import pandas as pd
import rasterio
import geopandas as gpd

from rasterio.features import geometry_mask

# ============================================================
# 1. PROJECT PATHS
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
    PROJECT_DIR / "data" / "processed" / "sar_features"
)

REPORT_DIR = (
    PROJECT_DIR / "reports" / "sar_coverage_analysis"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

YEARS = [2016, 2020, 2025]
POLS = ["VV", "VH"]

NODATA = -9999.0

# ============================================================
# 2. LOAD MUNICIPAL BOUNDARY
# ============================================================

boundary = gpd.read_file(BOUNDARY_FILE)

if boundary.empty or boundary.crs is None:
    raise ValueError("Invalid municipal boundary.")

# ============================================================
# 3. LOAD AND VALIDATE SAR RASTERS
# ============================================================

reference_path = (
    RASTER_DIR / "Jaipur_S1_2016_VV_UTM43N_10m.tif"
)

with rasterio.open(reference_path) as src:

    reference_profile = src.profile.copy()
    reference_crs = src.crs
    reference_transform = src.transform
    reference_shape = (src.height, src.width)

boundary = boundary.to_crs(reference_crs)

municipal_geometry = boundary.geometry.union_all()

municipal_mask = geometry_mask(
    [municipal_geometry],
    out_shape=reference_shape,
    transform=reference_transform,
    invert=True,
    all_touched=False
)

# ============================================================
# 4. READ BACKSCATTER AND CONVERT TO dB
# ============================================================

features = {}
quality_records = []

for year in YEARS:

    print("\n" + "=" * 65)
    print(f"PROCESSING YEAR: {year}")
    print("=" * 65)

    for pol in POLS:

        filename = (
            f"Jaipur_S1_{year}_{pol}_UTM43N_10m.tif"
        )

        input_path = RASTER_DIR / filename

        if not input_path.exists():
            raise FileNotFoundError(input_path)

        with rasterio.open(input_path) as src:

            if (
                src.crs != reference_crs
                or (src.height, src.width) != reference_shape
                or src.transform != reference_transform
            ):
                raise ValueError(
                    f"Grid mismatch: {input_path.name}"
                )

            data = src.read(1, masked=True)

            values = np.asarray(
                data.data,
                dtype=np.float32
            )

            valid = (
                municipal_mask
                & ~np.ma.getmaskarray(data)
                & np.isfinite(values)
                & (values > 0)
            )

            # Convert linear Sigma0 to decibels.
            db = np.full(
                reference_shape,
                NODATA,
                dtype=np.float32
            )

            db[valid] = (
                10.0 * np.log10(values[valid])
            )

            features[(year, pol)] = db

            valid_values = db[valid]

            quality_records.append({
                "year": year,
                "polarization": pol,
                "valid_pixels": int(valid.sum()),
                "minimum_db": float(valid_values.min()),
                "median_db": float(np.median(valid_values)),
                "maximum_db": float(valid_values.max()),
                "p01_db": float(np.percentile(valid_values, 1)),
                "p99_db": float(np.percentile(valid_values, 99))
            })

            print(f"{pol} valid pixels: {valid.sum():,}")
            print(
                f"{pol} median: "
                f"{np.median(valid_values):.3f} dB"
            )
            print(
                f"{pol} range: "
                f"{valid_values.min():.3f} to "
                f"{valid_values.max():.3f} dB"
            )

# ============================================================
# 5. CREATE POLARIZATION DIFFERENCE
# ============================================================

for year in YEARS:

    vv = features[(year, "VV")]
    vh = features[(year, "VH")]

    valid = (
        (vv != NODATA)
        & (vh != NODATA)
    )

    ratio_db = np.full(
        reference_shape,
        NODATA,
        dtype=np.float32
    )

    ratio_db[valid] = vv[valid] - vh[valid]

    features[(year, "VV_VH_DIFF")] = ratio_db

    print(
        f"\n{year} VV-VH difference median: "
        f"{np.median(ratio_db[valid]):.3f} dB"
    )

# ============================================================
# 6. TEMPORAL DIFFERENCES
# ============================================================

temporal_features = {}

periods = [
    (2016, 2020),
    (2020, 2025),
    (2016, 2025)
]

for start_year, end_year in periods:

    for pol in POLS:

        start = features[(start_year, pol)]
        end = features[(end_year, pol)]

        valid = (
            (start != NODATA)
            & (end != NODATA)
        )

        difference = np.full(
            reference_shape,
            NODATA,
            dtype=np.float32
        )

        difference[valid] = (
            end[valid] - start[valid]
        )

        name = (
            f"{pol}_{start_year}_{end_year}_CHANGE"
        )

        temporal_features[name] = difference

        print(
            f"\n{name}: "
            f"median change = "
            f"{np.median(difference[valid]):.3f} dB"
        )

# ============================================================
# 7. ASSEMBLE FEATURE STACK
# ============================================================

bands = []
band_names = []

for year in YEARS:

    for pol in ["VV", "VH", "VV_VH_DIFF"]:

        bands.append(features[(year, pol)])

        if pol == "VV_VH_DIFF":
            band_names.append(f"{year}_VV_MINUS_VH_dB")
        else:
            band_names.append(f"{year}_{pol}_dB")

for name, array in temporal_features.items():

    bands.append(array)
    band_names.append(name)

# ============================================================
# 8. SAVE MULTI-BAND FEATURE STACK
# ============================================================

stack_path = (
    OUTPUT_DIR / "Jaipur_SAR_Feature_Stack_2016_2025.tif"
)

output_profile = reference_profile.copy()

output_profile.update(
    driver="GTiff",
    dtype="float32",
    count=len(bands),
    nodata=NODATA,
    compress="lzw",
    tiled=True,
    blockxsize=256,
    blockysize=256,
    BIGTIFF="IF_SAFER"
)

with rasterio.open(
    stack_path,
    "w",
    **output_profile
) as dst:

    for index, (array, name) in enumerate(
        zip(bands, band_names),
        start=1
    ):

        dst.write(array, index)
        dst.set_band_description(index, name)

# ============================================================
# 9. SAVE QUALITY REPORT
# ============================================================

quality_df = pd.DataFrame(quality_records)

quality_path = (
    REPORT_DIR / "SAR_Feature_Extraction_Quality.csv"
)

quality_df.to_csv(quality_path, index=False)

# ============================================================
# 10. SAVE TEMPORAL STATISTICS
# ============================================================

temporal_records = []

for name, array in temporal_features.items():

    valid = array != NODATA

    values = array[valid]

    temporal_records.append({
        "feature": name,
        "valid_pixels": int(valid.sum()),
        "mean_change_db": float(np.mean(values)),
        "median_change_db": float(np.median(values)),
        "std_change_db": float(np.std(values)),
        "p05_change_db": float(np.percentile(values, 5)),
        "p95_change_db": float(np.percentile(values, 95))
    })

temporal_df = pd.DataFrame(temporal_records)

temporal_path = (
    REPORT_DIR / "SAR_Temporal_Change_Statistics.csv"
)

temporal_df.to_csv(temporal_path, index=False)

# ============================================================
# 11. FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("SAR FEATURE EXTRACTION COMPLETED")
print("=" * 70)

print(f"Total feature bands: {len(bands)}")

for index, name in enumerate(band_names, start=1):
    print(f"Band {index}: {name}")

print("\nFeature stack:")
print(stack_path)

print("\nQuality report:")
print(quality_path)

print("\nTemporal statistics:")
print(temporal_path)

print("\nOriginal SAR rasters were not modified.")
