
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

# ============================================================
# 1. PATHS
# ============================================================

PROJECT_DIR = Path(
    r"C:\Users\ssat-\Documents\RemoteSensing_Projects"
    r"\Project_02_Jaipur_SAR_Urban_Expansion"
)

CLUSTER_FILE = (
    PROJECT_DIR / "data" / "processed"
    / "change_detection" / "spatial_clusters"
    / "SAR_Joint_Change_Clusters.gpkg"
)

OSM_FILE = (
    PROJECT_DIR / "data" / "processed"
    / "OSM_Jaipur_Clipped_Reference.gpkg"
)

BOUNDARY_FILE = (
    PROJECT_DIR / "data" / "boundaries"
    / "Jaipur_JMC_Municipal_Boundary.geojson"
)

OUTPUT_DIR = (
    PROJECT_DIR / "reports"
    / "change_detection" / "osm_comparison"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET_CRS = "EPSG:32643"

# ============================================================
# 2. LOAD DATA
# ============================================================

print("=" * 70)
print("SAR CLUSTER AND OSM REFERENCE COMPARISON")
print("=" * 70)

clusters = gpd.read_file(
    CLUSTER_FILE,
    layer="change_clusters"
).to_crs(TARGET_CRS)

boundary = gpd.read_file(
    BOUNDARY_FILE
).to_crs(TARGET_CRS)

buildings = gpd.read_file(
    OSM_FILE,
    layer="buildings_polygon"
).to_crs(TARGET_CRS)

landuse = gpd.read_file(
    OSM_FILE,
    layer="landuse_polygon"
).to_crs(TARGET_CRS)

print(f"SAR clusters: {len(clusters):,}")
print(f"OSM buildings in reference buffer: {len(buildings):,}")
print(f"OSM land-use features in reference buffer: {len(landuse):,}")

# ============================================================
# 3. CLIP OSM REFERENCE FEATURES TO MUNICIPALITY
# ============================================================

municipal_geometry = boundary.geometry.union_all()

buildings_municipal = buildings[
    buildings.geometry.intersects(municipal_geometry)
].copy()

landuse_municipal = landuse[
    landuse.geometry.intersects(municipal_geometry)
].copy()

buildings_municipal["geometry"] = (
    buildings_municipal.geometry.intersection(
        municipal_geometry
    )
)

landuse_municipal["geometry"] = (
    landuse_municipal.geometry.intersection(
        municipal_geometry
    )
)

buildings_municipal = buildings_municipal[
    ~buildings_municipal.geometry.is_empty
].copy()

landuse_municipal = landuse_municipal[
    ~landuse_municipal.geometry.is_empty
].copy()

print("\nMunicipal OSM reference:")
print(f"Buildings: {len(buildings_municipal):,}")
print(f"Land-use features: {len(landuse_municipal):,}")

# ============================================================
# 4. BUILD CURRENT OSM BUILDING UNION
# ============================================================

building_union = buildings_municipal.geometry.union_all()

# ============================================================
# 5. ANALYSE EACH SAR CLUSTER
# ============================================================

records = []

for _, row in clusters.iterrows():

    geom = row.geometry

    cluster_area = geom.area

    building_intersection = geom.intersection(
        building_union
    )

    building_overlap_area = building_intersection.area

    record = {
        "cluster_id": int(row["cluster_id"]),
        "cluster_area_ha": cluster_area / 10000,
        "vv_median_change_db": row["median_vv_change_db"],
        "vh_median_change_db": row["median_vh_change_db"],
        "current_osm_building_overlap_m2": building_overlap_area,
        "current_osm_building_overlap_ha": (
            building_overlap_area / 10000
        ),
        "current_osm_building_overlap_percentage": (
            building_overlap_area / cluster_area * 100
            if cluster_area > 0 else 0
        )
    }

    # Calculate overlap with each mapped land-use category.
    for category in [
        "residential",
        "industrial",
        "commercial",
        "retail",
        "construction",
        "greenfield",
        "farmland",
        "grass",
        "forest",
        "military"
    ]:

        category_features = landuse_municipal[
            landuse_municipal["landuse"] == category
        ]

        if len(category_features) > 0:

            category_union = (
                category_features.geometry.union_all()
            )

            overlap = geom.intersection(
                category_union
            ).area

        else:
            overlap = 0.0

        record[f"{category}_overlap_m2"] = overlap

    records.append(record)

# ============================================================
# 6. SAVE CLUSTER COMPARISON TABLE
# ============================================================

comparison = pd.DataFrame(records)

comparison = comparison.sort_values(
    "cluster_area_ha",
    ascending=False
)

comparison_file = (
    OUTPUT_DIR / "SAR_Cluster_OSM_Comparison.csv"
)

comparison.to_csv(
    comparison_file,
    index=False
)

# ============================================================
# 7. OVERALL SUMMARY
# ============================================================

total_cluster_area = clusters.geometry.area.sum()

total_building_overlap = (
    clusters.geometry.intersection(
        building_union
    ).area.sum()
)

# Union of all candidate patches avoids double-counting
# any overlapping cluster geometries.
cluster_union = clusters.geometry.union_all()

overall_building_overlap = (
    cluster_union.intersection(building_union).area
)

summary = pd.DataFrame([{
    "cluster_count": len(clusters),
    "total_cluster_area_km2": total_cluster_area / 1e6,
    "current_osm_building_overlap_km2": (
        overall_building_overlap / 1e6
    ),
    "current_osm_building_overlap_percentage": (
        overall_building_overlap / cluster_union.area * 100
        if cluster_union.area > 0 else 0
    ),
    "current_osm_buildings_in_municipality": len(
        buildings_municipal
    ),
    "current_osm_landuse_features_in_municipality": len(
        landuse_municipal
    )
}])

summary_file = (
    OUTPUT_DIR / "SAR_Cluster_OSM_Overall_Summary.csv"
)

summary.to_csv(summary_file, index=False)

# ============================================================
# 8. MAP: MUNICIPALITY + BUILDINGS + CLUSTERS
# ============================================================

fig, ax = plt.subplots(figsize=(12, 12))

# Municipal boundary
boundary.boundary.plot(
    ax=ax,
    color="black",
    linewidth=1.5,
    label="Municipal boundary"
)

# Current OSM buildings
buildings_municipal.plot(
    ax=ax,
    color="lightgrey",
    edgecolor="none",
    alpha=0.75,
    label="Current OSM buildings"
)

# SAR candidate clusters
clusters.plot(
    ax=ax,
    color="red",
    edgecolor="darkred",
    linewidth=0.25,
    alpha=0.75,
    label="SAR change candidates"
)

minx, miny, maxx, maxy = boundary.total_bounds

xmargin = (maxx - minx) * 0.04
ymargin = (maxy - miny) * 0.04

ax.set_xlim(minx - xmargin, maxx + xmargin)
ax.set_ylim(miny - ymargin, maxy + ymargin)

ax.set_aspect("equal")

ax.set_title(
    "Jaipur Municipality: SAR Change Candidates and Current OSM Buildings\n"
    "2016–2025 | Spatial Reference Comparison",
    fontsize=14,
    fontweight="bold"
)

ax.set_xlabel("Easting (m)")
ax.set_ylabel("Northing (m)")

ax.legend(loc="lower right")

plt.tight_layout()

map_file = (
    OUTPUT_DIR / "SAR_Clusters_OSM_Buildings_Map.png"
)

plt.savefig(
    map_file,
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# ============================================================
# 9. PRINT RESULTS
# ============================================================

print("\n" + "=" * 70)
print("OSM COMPARISON COMPLETED")
print("=" * 70)

print(summary.to_string(index=False))

print("\nLargest candidate clusters and building overlap:")

print(
    comparison[
        [
            "cluster_id",
            "cluster_area_ha",
            "current_osm_building_overlap_percentage"
        ]
    ].head(15).to_string(index=False)
)

print("\nGenerated reports:")
print(comparison_file)
print(summary_file)
print(map_file)

print(
    "\nIMPORTANT: OSM is current reference data, "
    "not historical validation for 2016 or 2020."
)

print("Original SAR and OSM datasets were not modified.")
