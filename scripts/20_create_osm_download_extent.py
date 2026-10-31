
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import box

# ============================================================
# 1. PROJECT PATHS
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent.parent

BOUNDARY_DIR = PROJECT_DIR / "data" / "boundaries"
REPORT_DIR = PROJECT_DIR / "reports" / "boundary_analysis"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

MUNICIPAL_FILE = (
    BOUNDARY_DIR / "Jaipur_JMC_Municipal_Boundary.geojson"
)

# Output files
BUFFER_FILE = (
    BOUNDARY_DIR / "Jaipur_OSM_Reference_Buffer_10km.geojson"
)

EXTENT_FILE = (
    BOUNDARY_DIR / "Jaipur_OSM_Extraction_Extent.geojson"
)

MAP_FILE = (
    REPORT_DIR / "Jaipur_OSM_Reference_Extent_10km.png"
)

# ============================================================
# 2. LOAD MUNICIPAL BOUNDARY
# ============================================================

print("\n" + "=" * 65)
print("JAIPUR OSM DOWNLOAD EXTENT GENERATION")
print("=" * 65)

municipality = gpd.read_file(MUNICIPAL_FILE)

if municipality.empty:
    raise ValueError("Municipal boundary dataset is empty.")

if municipality.crs is None:
    raise ValueError("Municipal boundary has no CRS.")

print("\n[1] MUNICIPAL BOUNDARY")
print("-" * 65)

print("CRS:", municipality.crs)
print("Geometry:", municipality.geom_type.iloc[0])

# ============================================================
# 3. PROJECT TO UTM ZONE 43N
# ============================================================

municipality_utm = municipality.to_crs(epsg=32643)

municipal_area_km2 = (
    municipality_utm.geometry.area.sum() / 1_000_000
)

# ============================================================
# 4. GENERATE 10 KM BUFFER
# ============================================================

BUFFER_DISTANCE = 10_000  # metres

buffer_geometry = municipality_utm.geometry.union_all().buffer(
    BUFFER_DISTANCE
)

buffer_gdf = gpd.GeoDataFrame(
    {"name": ["Jaipur Municipal Boundary + 10 km Buffer"]},
    geometry=[buffer_geometry],
    crs="EPSG:32643"
)

buffer_area_km2 = buffer_gdf.geometry.area.sum() / 1_000_000

# ============================================================
# 5. CREATE OSM EXTRACTION EXTENT
# ============================================================

# This is the municipal area plus its surrounding 10 km buffer.
# The buffer includes the original municipal area.

extent = buffer_gdf.to_crs(epsg=4326)

# ============================================================
# 6. PRINT AREA STATISTICS
# ============================================================

print("\n[2] BUFFER STATISTICS")
print("-" * 65)

print(f"Municipal area: {municipal_area_km2:.3f} km²")
print(f"Buffer distance: {BUFFER_DISTANCE / 1000:.1f} km")
print(f"Buffered extraction area: {buffer_area_km2:.3f} km²")
print(
    f"Additional contextual area: "
    f"{buffer_area_km2 - municipal_area_km2:.3f} km²"
)

print("\nExtraction extent bounds (EPSG:4326):")
print(extent.total_bounds)

# ============================================================
# 7. SAVE GEOJSON FILES
# ============================================================

buffer_gdf.to_crs(epsg=4326).to_file(
    BUFFER_FILE,
    driver="GeoJSON"
)

extent.to_file(
    EXTENT_FILE,
    driver="GeoJSON"
)

print("\n[3] SAVED FILES")
print("-" * 65)

print("Buffer boundary:", BUFFER_FILE)
print("OSM extraction extent:", EXTENT_FILE)

# ============================================================
# 8. CREATE VISUALIZATION
# ============================================================

municipality_plot = municipality_utm
buffer_plot = buffer_gdf

fig, ax = plt.subplots(figsize=(12, 10))

# Buffer area
buffer_plot.plot(
    ax=ax,
    facecolor="#B8D8F0",
    edgecolor="#1769AA",
    linewidth=1.8,
    alpha=0.55,
    label="10 km Reference Buffer"
)

# Municipal wards
municipality_plot.plot(
    ax=ax,
    facecolor="#F4C56A",
    edgecolor="white",
    linewidth=0.35,
    label="Municipal Wards"
)

# Municipal outer boundary
municipality_plot.boundary.plot(
    ax=ax,
    color="#C62828",
    linewidth=2,
    label="Municipal Boundary"
)

ax.set_title(
    "Jaipur Municipal Boundary and OSM Reference Extent",
    fontsize=15,
    fontweight="bold",
    pad=16
)

ax.set_xlabel("Easting (m) — UTM Zone 43N")
ax.set_ylabel("Northing (m) — UTM Zone 43N")

ax.grid(
    True,
    linestyle=":",
    linewidth=0.6,
    alpha=0.6
)

ax.set_aspect("equal")

ax.legend(
    loc="lower right",
    frameon=True
)

# North arrow
ax.annotate(
    "N",
    xy=(0.94, 0.94),
    xytext=(0.94, 0.86),
    xycoords="axes fraction",
    textcoords="axes fraction",
    arrowprops=dict(
        facecolor="black",
        width=3,
        headwidth=10
    ),
    ha="center",
    fontsize=12,
    fontweight="bold"
)

plt.tight_layout()

plt.savefig(
    MAP_FILE,
    dpi=300,
    bbox_inches="tight"
)

plt.show()

print("\n[4] MAP SAVED")
print(MAP_FILE)

print("\nOSM EXTRACTION EXTENT GENERATION COMPLETED")
print("=" * 65)
