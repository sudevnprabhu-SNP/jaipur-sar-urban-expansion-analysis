
from pathlib import Path
import geopandas as gpd
import matplotlib.pyplot as plt

# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_DIR = Path(
    r"C:\Users\ssat-\Documents\RemoteSensing_Projects"
    r"\Project_02_Jaipur_SAR_Urban_Expansion"
)

GPKG_FILE = (
    PROJECT_DIR
    / "data"
    / "processed"
    / "OSM_Jaipur_Clipped_Reference.gpkg"
)

BOUNDARY_FILE = (
    PROJECT_DIR
    / "data"
    / "boundaries"
    / "Jaipur_JMC_Municipal_Boundary.geojson"
)

OUTPUT_DIR = (
    PROJECT_DIR
    / "reports"
    / "osm_quality_analysis"
    / "maps"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CRS = "EPSG:32643"

# ============================================================
# LOAD MUNICIPAL BOUNDARY
# ============================================================

boundary = gpd.read_file(BOUNDARY_FILE).to_crs(CRS)

# ============================================================
# LOAD OSM REFERENCE LAYERS
# ============================================================

buildings = gpd.read_file(
    GPKG_FILE,
    layer="buildings_polygon"
).to_crs(CRS)

landuse = gpd.read_file(
    GPKG_FILE,
    layer="landuse_polygon"
).to_crs(CRS)

parks = gpd.read_file(
    GPKG_FILE,
    layer="open_public_spaces_polygon"
).to_crs(CRS)

water = gpd.read_file(
    GPKG_FILE,
    layer="water_polygons_polygon"
).to_crs(CRS)

# ============================================================
# CLIP TO MUNICIPAL BOUNDARY
# ============================================================

municipal_geometry = boundary.geometry.union_all()

buildings = gpd.clip(buildings, municipal_geometry)
landuse = gpd.clip(landuse, municipal_geometry)
parks = gpd.clip(parks, municipal_geometry)
water = gpd.clip(water, municipal_geometry)

# ============================================================
# PLOT SETTINGS
# ============================================================

def prepare_map(ax, title):

    boundary.boundary.plot(
        ax=ax,
        linewidth=1.3,
        color="black"
    )

    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.set_aspect("equal")
    ax.set_axis_off()


# ============================================================
# MAP 1: BUILDINGS
# ============================================================

fig, ax = plt.subplots(figsize=(10, 10))

prepare_map(ax, "OSM Building Footprints — Jaipur Municipality")

buildings.plot(
    ax=ax,
    color="red",
    linewidth=0,
    alpha=0.7
)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "01_Jaipur_OSM_Buildings.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# ============================================================
# MAP 2: LAND USE
# ============================================================

fig, ax = plt.subplots(figsize=(10, 10))

prepare_map(ax, "OSM Land Use — Jaipur Municipality")

landuse.plot(
    ax=ax,
    column="landuse",
    categorical=True,
    legend=True,
    legend_kwds={
        "loc": "upper left",
        "fontsize": 7,
        "title": "Land use"
    },
    alpha=0.75,
    linewidth=0.2,
    edgecolor="black"
)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "02_Jaipur_OSM_Landuse.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# ============================================================
# MAP 3: PARKS AND WATER
# ============================================================

fig, ax = plt.subplots(figsize=(10, 10))

prepare_map(ax, "OSM Open Spaces and Water — Jaipur Municipality")

parks.plot(
    ax=ax,
    color="green",
    alpha=0.65,
    linewidth=0
)

water.plot(
    ax=ax,
    color="blue",
    alpha=0.75,
    linewidth=0
)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "03_Jaipur_OSM_Parks_Water.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# ============================================================
# MAP 4: COMBINED REFERENCE DATA
# ============================================================

fig, ax = plt.subplots(figsize=(12, 12))

prepare_map(ax, "Combined OSM Reference Data — Jaipur Municipality")

landuse.plot(
    ax=ax,
    color="orange",
    alpha=0.35,
    linewidth=0
)

parks.plot(
    ax=ax,
    color="green",
    alpha=0.6,
    linewidth=0
)

water.plot(
    ax=ax,
    color="blue",
    alpha=0.75,
    linewidth=0
)

buildings.plot(
    ax=ax,
    color="red",
    alpha=0.7,
    linewidth=0
)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "04_Jaipur_OSM_Combined_Reference.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# ============================================================
# SUMMARY
# ============================================================

print("=" * 70)
print("OSM MUNICIPAL REFERENCE MAPS GENERATED")
print("=" * 70)

print(f"Buildings: {len(buildings):,}")
print(f"Land-use polygons: {len(landuse):,}")
print(f"Open spaces: {len(parks):,}")
print(f"Water polygons: {len(water):,}")

print("\nOutput directory:")
print(OUTPUT_DIR)

print("\nOriginal GeoPackage was not modified.")
