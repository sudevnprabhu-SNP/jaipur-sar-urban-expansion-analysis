
from pathlib import Path
import re
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
import matplotlib.pyplot as plt

from rasterio.features import geometry_mask

# ============================================================
# 1. PROJECT PATHS
# ============================================================

PROJECT_DIR = Path(
    r"C:\Users\ssat-\Documents\RemoteSensing_Projects"
    r"\Project_02_Jaipur_SAR_Urban_Expansion"
)

RASTER_DIR = PROJECT_DIR / "data" / "processed"

BOUNDARY_FILE = (
    PROJECT_DIR
    / "data"
    / "boundaries"
    / "Jaipur_JMC_Municipal_Boundary.geojson"
)

OUTPUT_DIR = (
    PROJECT_DIR
    / "reports"
    / "sar_coverage_analysis"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

YEARS = [2016, 2020, 2025]
POLARIZATIONS = ["VV", "VH"]


# ============================================================
# 2. EXPLICIT PATHS TO SIX ALIGNED SAR RASTERS
# ============================================================

ALIGNED_DIR = (
    PROJECT_DIR
    / "data"
    / "processed"
    / "aligned_utm43n"
)

RASTERS = {
    (2016, "VV"): ALIGNED_DIR / "Jaipur_S1_2016_VV_UTM43N_10m.tif",
    (2016, "VH"): ALIGNED_DIR / "Jaipur_S1_2016_VH_UTM43N_10m.tif",

    (2020, "VV"): ALIGNED_DIR / "Jaipur_S1_2020_VV_UTM43N_10m.tif",
    (2020, "VH"): ALIGNED_DIR / "Jaipur_S1_2020_VH_UTM43N_10m.tif",

    (2025, "VV"): ALIGNED_DIR / "Jaipur_S1_2025_VV_UTM43N_10m.tif",
    (2025, "VH"): ALIGNED_DIR / "Jaipur_S1_2025_VH_UTM43N_10m.tif",
}

print("\nSelected aligned SAR rasters:")

for key, path in RASTERS.items():

    if not path.exists():
        raise FileNotFoundError(
            f"Expected aligned raster not found: {path}"
        )

    print(f"{key[0]} {key[1]}: {path}")


# ============================================================
# 3. LOAD MUNICIPAL BOUNDARY
# ============================================================

boundary = gpd.read_file(BOUNDARY_FILE)

if boundary.empty:
    raise ValueError("Municipal boundary is empty.")

if boundary.crs is None:
    raise ValueError("Municipal boundary CRS is missing.")

# ============================================================
# 4. CHECK RASTER GRID ALIGNMENT
# ============================================================

reference_path = RASTERS[(2016, "VV")]

with rasterio.open(reference_path) as src:

    reference_crs = src.crs
    reference_transform = src.transform
    reference_shape = (src.height, src.width)
    reference_profile = src.profile.copy()

if reference_crs is None:
    raise ValueError("Reference raster CRS is missing.")

boundary = boundary.to_crs(reference_crs)

print("\nReference raster properties:")
print(f"CRS: {reference_crs}")
print(f"Raster dimensions: {reference_shape}")
print(f"Pixel size: {reference_transform.a}, "
      f"{reference_transform.e}")

for key, path in RASTERS.items():

    with rasterio.open(path) as src:

        aligned = (
            src.crs == reference_crs
            and (src.height, src.width) == reference_shape
            and src.transform == reference_transform
        )

        print(
            f"{key[0]} {key[1]} grid alignment: "
            f"{'PASS' if aligned else 'FAIL'}"
        )

        if not aligned:
            raise ValueError(
                f"{path.name} is not aligned with the reference grid. "
                "Do not calculate common coverage until all rasters "
                "are aligned."
            )

# ============================================================
# 5. CREATE MUNICIPAL PIXEL MASK
# ============================================================

municipal_geometry = boundary.geometry.union_all()

municipal_mask = geometry_mask(
    [municipal_geometry],
    out_shape=reference_shape,
    transform=reference_transform,
    invert=True,
    all_touched=False
)

pixel_area_m2 = abs(
    reference_transform.a * reference_transform.e
    - reference_transform.b * reference_transform.d
)

municipal_pixel_count = int(municipal_mask.sum())

municipal_raster_area_km2 = (
    municipal_pixel_count * pixel_area_m2 / 1e6
)

print("\nMunicipal raster coverage:")
print(f"Municipal pixels: {municipal_pixel_count:,}")
print(f"Rasterized municipal area: "
      f"{municipal_raster_area_km2:.3f} km²")

# ============================================================
# 6. READ VALID PIXELS FOR ALL SIX RASTERS
# ============================================================

valid_masks = {}
statistics = []

for (year, polarization), path in RASTERS.items():

    print(f"\nReading {year} {polarization}...")

    with rasterio.open(path) as src:

        data = src.read(1, masked=True)

        values = np.asarray(data.data)

        valid = (
            ~np.ma.getmaskarray(data)
            & np.isfinite(values)
        )

        valid_inside = valid & municipal_mask

        valid_count = int(valid_inside.sum())

        percentage = (
            valid_count / municipal_pixel_count * 100
            if municipal_pixel_count else 0
        )

        valid_masks[(year, polarization)] = valid

        statistics.append({
            "year": year,
            "polarization": polarization,
            "valid_municipal_pixels": valid_count,
            "municipal_pixels": municipal_pixel_count,
            "valid_area_km2": (
                valid_count * pixel_area_m2 / 1e6
            ),
            "coverage_percentage": percentage
        })

        print(f"Valid municipal pixels: {valid_count:,}")
        print(f"Valid area: {valid_count * pixel_area_m2 / 1e6:.3f} km²")
        print(f"Coverage: {percentage:.3f}%")

# ============================================================
# 7. COMMON VALID FOOTPRINT ACROSS ALL SIX RASTERS
# ============================================================

common_mask = municipal_mask.copy()

for key in valid_masks:
    common_mask &= valid_masks[key]

common_pixel_count = int(common_mask.sum())

common_area_km2 = (
    common_pixel_count * pixel_area_m2 / 1e6
)

common_percentage = (
    common_pixel_count / municipal_pixel_count * 100
    if municipal_pixel_count else 0
)

print("\n" + "=" * 70)
print("COMMON THREE-DATE SAR COVERAGE")
print("=" * 70)

print(f"Municipal rasterized area: {municipal_raster_area_km2:.3f} km²")
print(f"Common valid pixels: {common_pixel_count:,}")
print(f"Common valid area: {common_area_km2:.3f} km²")
print(f"Common municipal coverage: {common_percentage:.3f}%")
print(
    f"Outside common footprint: "
    f"{100 - common_percentage:.3f}%"
)

# ============================================================
# 8. SAVE STATISTICAL REPORTS
# ============================================================

stats_df = pd.DataFrame(statistics)

stats_file = OUTPUT_DIR / "SAR_Municipal_Coverage_By_Date.csv"

stats_df.to_csv(stats_file, index=False)

common_summary = pd.DataFrame([{
    "municipal_raster_area_km2": municipal_raster_area_km2,
    "common_valid_pixels": common_pixel_count,
    "common_valid_area_km2": common_area_km2,
    "common_coverage_percentage": common_percentage,
    "outside_common_percentage": 100 - common_percentage,
    "pixel_area_m2": pixel_area_m2
}])

common_file = OUTPUT_DIR / "SAR_Common_Municipal_Coverage.csv"

common_summary.to_csv(common_file, index=False)

# ============================================================
# 9. SAVE COMMON FOOTPRINT RASTER
# ============================================================

mask_file = OUTPUT_DIR / "SAR_Common_Municipal_Footprint.tif"

output_profile = reference_profile.copy()

output_profile.update(
    dtype="uint8",
    count=1,
    nodata=0,
    compress="lzw"
)

with rasterio.open(mask_file, "w", **output_profile) as dst:

    dst.write(
        common_mask.astype("uint8"),
        1
    )

# ============================================================
# 10. VISUALIZE COMMON SAR FOOTPRINT
# ============================================================

fig, ax = plt.subplots(figsize=(11, 11))

left = reference_transform.c
top = reference_transform.f

right = (
    left
    + reference_transform.a * reference_shape[1]
)

bottom = (
    top
    + reference_transform.e * reference_shape[0]
)

ax.imshow(
    np.where(common_mask, 1, np.nan),
    extent=[left, right, bottom, top],
    origin="upper",
    cmap="Greens",
    interpolation="nearest"
)

boundary.boundary.plot(
    ax=ax,
    color="black",
    linewidth=1.3
)

ax.set_title(
    "Common Sentinel-1 SAR Footprint — Jaipur Municipality\n"
    f"2016, 2020 and 2025 | Coverage: {common_percentage:.2f}%",
    fontsize=13,
    fontweight="bold"
)

ax.set_xlabel(f"Easting ({reference_crs})")
ax.set_ylabel("Northing")

ax.set_aspect("equal")

plt.tight_layout()

map_file = OUTPUT_DIR / "SAR_Common_Municipal_Footprint.png"

plt.savefig(
    map_file,
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# ============================================================
# 11. FINAL OUTPUT
# ============================================================

print("\n" + "=" * 70)
print("SCRIPT 29 COMPLETED")
print("=" * 70)

print("\nGenerated files:")
print(stats_file)
print(common_file)
print(mask_file)
print(map_file)

print("\nOriginal SAR rasters and municipal boundary were not modified.")
