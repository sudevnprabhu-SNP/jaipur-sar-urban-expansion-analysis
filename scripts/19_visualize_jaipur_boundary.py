
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

WARDS_FILE = BOUNDARY_DIR / "Jaipur_JMC_Wards_Validated.geojson"
MUNICIPAL_FILE = BOUNDARY_DIR / "Jaipur_JMC_Municipal_Boundary.geojson"

# ============================================================
# 2. LOAD DATA
# ============================================================

wards = gpd.read_file(WARDS_FILE)
municipality = gpd.read_file(MUNICIPAL_FILE)

# ============================================================
# 3. CREATE SAR STUDY RECTANGLE
# ============================================================

study_area = gpd.GeoDataFrame(
    {"name": ["SAR Study Area"]},
    geometry=[box(75.65, 26.75, 76.05, 27.05)],
    crs="EPSG:4326"
)

# ============================================================
# 4. REPROJECT TO UTM 43N
# ============================================================

wards = wards.to_crs(epsg=32643)
municipality = municipality.to_crs(epsg=32643)
study_area = study_area.to_crs(epsg=32643)

# ============================================================
# 5. PLOT
# ============================================================

fig, ax = plt.subplots(figsize=(12, 10))

# SAR study rectangle
study_area.plot(
    ax=ax,
    facecolor="none",
    edgecolor="black",
    linewidth=2,
    linestyle="--",
    label="SAR Study Rectangle"
)

# Individual wards
wards.plot(
    ax=ax,
    facecolor="#F4C56A",
    edgecolor="white",
    linewidth=0.45,
    label="Municipal Wards"
)

# Municipal outer boundary
municipality.boundary.plot(
    ax=ax,
    color="#C62828",
    linewidth=2,
    label="Municipal Boundary"
)

# ============================================================
# 6. MAP DECORATION
# ============================================================

ax.set_title(
    "Jaipur Municipal Boundary and SAR Study Extent",
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
    xytext=(0.94, 0.85),
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

# ============================================================
# 7. SAVE
# ============================================================

output_file = REPORT_DIR / "Jaipur_Municipal_Boundary_SAR_Extent.png"

plt.tight_layout()
plt.savefig(output_file, dpi=300, bbox_inches="tight")
plt.show()

print("\nMAP SAVED SUCCESSFULLY")
print(output_file)
