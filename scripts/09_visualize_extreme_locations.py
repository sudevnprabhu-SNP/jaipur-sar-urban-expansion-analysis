
from pathlib import Path

import numpy as np
import rasterio
import matplotlib.pyplot as plt

from rasterio.windows import from_bounds, Window


# --------------------------------------------------
# 1. PROJECT CONFIGURATION
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parents[1]

INPUT_DIR = PROJECT_DIR / "data" / "processed"

OUTPUT_DIR = (
    PROJECT_DIR / "reports" / "extreme_location_analysis"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

YEARS = [2016, 2020, 2025]
POLARIZATIONS = ["VV", "VH"]

# Approximately 1 km x 1 km viewing area
HALF_SIZE = 0.005

LOCATIONS = {
    "A": {
        "name": "Persistent Target A",
        "lon": 75.7864,
        "lat": 26.9797
    },
    "B": {
        "name": "Persistent Target B",
        "lon": 75.9095,
        "lat": 26.8994
    },
    "C": {
        "name": "2025 Prominent Target C",
        "lon": 75.8389,
        "lat": 26.7777
    },
    "D": {
        "name": "2025 Prominent Target D",
        "lon": 75.8225,
        "lat": 26.7553
    }
}


# --------------------------------------------------
# 2. READ LOCAL RASTER PATCH
# --------------------------------------------------

def read_patch(year, polarization, lon, lat):

    filename = (
        f"Jaipur_S1_{year}_{polarization}_singleband.tif"
    )

    filepath = INPUT_DIR / filename

    with rasterio.open(filepath) as src:

        if src.crs.to_epsg() != 4326:
            raise ValueError(
                f"{filename} is not EPSG:4326."
            )

        requested_bounds = (
            lon - HALF_SIZE,
            lat - HALF_SIZE,
            lon + HALF_SIZE,
            lat + HALF_SIZE
        )

        # Clip requested area to raster extent
        left = max(requested_bounds[0], src.bounds.left)
        bottom = max(requested_bounds[1], src.bounds.bottom)
        right = min(requested_bounds[2], src.bounds.right)
        top = min(requested_bounds[3], src.bounds.top)

        if left >= right or bottom >= top:
            raise ValueError(
                f"Location outside raster: {filename}"
            )

        window = from_bounds(
            left, bottom, right, top,
            transform=src.transform
        ).round_offsets().round_lengths()

        full_window = Window(
            0, 0, src.width, src.height
        )

        window = window.intersection(full_window)

        data = src.read(
            1,
            window=window,
            masked=True
        )

        # Convert linear Sigma0 to dB for display
        valid = (
            ~np.ma.getmaskarray(data)
            & np.isfinite(data.data)
            & (data.data > 0)
        )

        db = np.full(
            data.shape,
            np.nan,
            dtype="float32"
        )

        db[valid] = (
            10.0 * np.log10(data.data[valid])
        )

        transform = src.window_transform(window)

        extent = (
            transform.c,
            transform.c + transform.a * data.shape[1],
            transform.f + transform.e * data.shape[0],
            transform.f
        )

        return db, extent


# --------------------------------------------------
# 3. CREATE COMPARATIVE FIGURES
# --------------------------------------------------

for location_id, location in LOCATIONS.items():

    print(
        f"\nGenerating Location {location_id}: "
        f"{location['name']}"
    )

    patches = {}
    all_values = {
        "VV": [],
        "VH": []
    }

    # Read all six local patches
    for year in YEARS:

        for pol in POLARIZATIONS:

            db, extent = read_patch(
                year,
                pol,
                location["lon"],
                location["lat"]
            )

            patches[(year, pol)] = (db, extent)

            values = db[np.isfinite(db)]

            if values.size:
                all_values[pol].append(values)

    # Common display limits per polarization
    limits = {}

    for pol in POLARIZATIONS:

        combined = np.concatenate(all_values[pol])

        limits[pol] = (
            np.percentile(combined, 2),
            np.percentile(combined, 98)
        )

    # Create 3 x 2 comparison
    fig, axes = plt.subplots(
        3, 2,
        figsize=(12, 14)
    )

    for row, year in enumerate(YEARS):

        for col, pol in enumerate(POLARIZATIONS):

            ax = axes[row, col]

            db, extent = patches[(year, pol)]

            vmin, vmax = limits[pol]

            image = ax.imshow(
                db,
                extent=extent,
                origin="upper",
                cmap="gray",
                vmin=vmin,
                vmax=vmax,
                interpolation="nearest"
            )

            ax.set_title(
                f"{year} — {pol} Backscatter"
            )

            ax.set_xlabel("Longitude")
            ax.set_ylabel("Latitude")

            fig.colorbar(
                image,
                ax=ax,
                label="Sigma0 (dB)",
                shrink=0.85
            )

    fig.suptitle(
        f"Location {location_id}: {location['name']}\n"
        f"Centre: {location['lon']}, {location['lat']}",
        fontsize=14
    )

    plt.tight_layout()

    output_file = (
        OUTPUT_DIR /
        f"Location_{location_id}_comparison.png"
    )

    plt.savefig(
        output_file,
        dpi=200,
        bbox_inches="tight"
    )

    plt.close(fig)

    print(f"Saved: {output_file}")


print("\nAll location comparisons completed.")
