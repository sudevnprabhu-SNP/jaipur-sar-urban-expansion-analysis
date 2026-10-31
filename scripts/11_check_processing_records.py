
from pathlib import Path
import xml.etree.ElementTree as ET
import rasterio

# --------------------------------------------------
# 1. PROJECT CONFIGURATION
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parents[1]

PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
REPORT_DIR = PROJECT_DIR / "reports" / "quality_analysis"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = REPORT_DIR / "processing_records_audit.txt"

YEARS = [2016, 2020, 2025]
POLARIZATIONS = ["VV", "VH"]

KEYWORDS = [
    "Apply-Orbit-File",
    "Calibration",
    "Speckle-Filter",
    "Terrain-Correction",
    "Subset",
    "orbit",
    "sigma0",
    "sigma_0",
    "filter",
    "windowSize",
    "filterSizeX",
    "filterSizeY",
    "mapProjection",
    "pixelSpacingInMeter",
    "demName",
    "resampling",
    "sourceProduct",
    "targetProduct"
]

METADATA_EXTENSIONS = {
    ".dim",
    ".xml",
    ".log",
    ".txt",
    ".graph",
    ".properties"
}

EXCLUDED_DIRS = {
    ".venv",
    "__pycache__",
    ".git"
}


# --------------------------------------------------
# 2. REPORT WRITER
# --------------------------------------------------

report_lines = []


def log(message=""):
    print(message)
    report_lines.append(str(message))


# --------------------------------------------------
# 3. CHECK GEOTIFF METADATA
# --------------------------------------------------

def inspect_geotiff(filepath):

    log("\n" + "=" * 65)
    log(f"GEOTIFF: {filepath.name}")
    log("=" * 65)

    try:
        with rasterio.open(filepath) as src:

            log(f"CRS: {src.crs}")
            log(f"Dimensions: {src.width} x {src.height}")
            log(f"Bands: {src.count}")
            log(f"Data type: {src.dtypes}")
            log(f"Resolution: {src.res}")
            log(f"NoData: {src.nodata}")
            log(f"Band descriptions: {src.descriptions}")

            log("\nDataset tags:")

            tags = src.tags()

            if tags:
                for key, value in tags.items():
                    log(f"  {key}: {value}")
            else:
                log("  No dataset tags found.")

            for band in range(1, src.count + 1):

                log(f"\nBand {band} tags:")

                band_tags = src.tags(band)

                if band_tags:
                    for key, value in band_tags.items():
                        log(f"  {key}: {value}")
                else:
                    log("  No band tags found.")

    except Exception as error:
        log(f"ERROR: {error}")


# --------------------------------------------------
# 4. FIND AVAILABLE METADATA FILES
# --------------------------------------------------

def find_metadata_files():

    found_files = []

    for path in PROJECT_DIR.rglob("*"):

        if not path.is_file():
            continue

        relative = path.relative_to(PROJECT_DIR)

        if any(
            part in EXCLUDED_DIRS
            for part in relative.parts
        ):
            continue

        # Avoid scanning the huge SAFE source directories.
        if relative.parts[0] == "data" and (
            len(relative.parts) > 2
            and relative.parts[1] == "raw"
        ):
            continue

        if path.suffix.lower() in METADATA_EXTENSIONS:
            found_files.append(path)

    return sorted(found_files)


# --------------------------------------------------
# 5. INSPECT SNAP XML / DIM / GRAPH FILES
# --------------------------------------------------

def inspect_metadata_file(filepath):

    log("\n" + "-" * 65)
    log(f"FILE: {filepath.relative_to(PROJECT_DIR)}")
    log("-" * 65)

    try:

        if filepath.suffix.lower() in {".xml", ".dim", ".graph"}:

            tree = ET.parse(filepath)
            root = tree.getroot()

            matches = []

            for element in root.iter():

                tag = element.tag.split("}")[-1]
                value = (element.text or "").strip()

                if not value:
                    continue

                combined = f"{tag} {value}".lower()

                if any(
                    keyword.lower() in combined
                    for keyword in KEYWORDS
                ):
                    matches.append((tag, value))

            if matches:

                for tag, value in matches[:100]:
                    log(f"  {tag}: {value}")

                if len(matches) > 100:
                    log(
                        f"  ... {len(matches) - 100} "
                        "additional matches omitted."
                    )

            else:
                log("  No relevant processing parameters found.")

        else:

            with filepath.open(
                "r",
                encoding="utf-8",
                errors="ignore"
            ) as file:

                matches = []

                for line_number, line in enumerate(file, 1):

                    if any(
                        keyword.lower() in line.lower()
                        for keyword in KEYWORDS
                    ):
                        matches.append(
                            (line_number, line.strip())
                        )

                if matches:

                    for line_number, line in matches[:100]:
                        log(f"  Line {line_number}: {line}")

                else:
                    log("  No relevant processing records found.")

    except ET.ParseError:
        log("  XML parsing failed; inspecting as plain text.")

        try:
            content = filepath.read_text(
                encoding="utf-8",
                errors="ignore"
            )

            for line_number, line in enumerate(
                content.splitlines(), 1
            ):

                if any(
                    keyword.lower() in line.lower()
                    for keyword in KEYWORDS
                ):
                    log(f"  Line {line_number}: {line.strip()}")

        except Exception as error:
            log(f"  Could not read file: {error}")

    except Exception as error:
        log(f"  Inspection error: {error}")


# --------------------------------------------------
# 6. CHECK SNAP PRODUCT FOLDERS
# --------------------------------------------------

def inspect_snap_products():

    log("\n" + "=" * 65)
    log("SNAP PRODUCT INVENTORY")
    log("=" * 65)

    dim_files = list(PROJECT_DIR.rglob("*.dim"))

    if not dim_files:
        log("No SNAP DIMAP .dim products found.")
    else:
        for dim in dim_files:
            log(f"Found SNAP product: {dim}")

            data_folder = dim.with_suffix(".data")

            if data_folder.exists():
                log(f"  Associated data folder: {data_folder}")
            else:
                log("  Associated .data folder not found.")


# --------------------------------------------------
# 7. MAIN AUDIT
# --------------------------------------------------

log("SENTINEL-1 PROCESSING RECORDS AUDIT")
log(f"Project: {PROJECT_DIR}")

log("\nSTEP 1: GEOTIFF INSPECTION")

for year in YEARS:

    for pol in POLARIZATIONS:

        candidates = [
            PROCESSED_DIR /
            f"Jaipur_S1_{year}_{pol}_singleband.tif",

            PROCESSED_DIR /
            "aligned_utm43n" /
            f"Jaipur_S1_{year}_{pol}_UTM43N_10m.tif"
        ]

        for filepath in candidates:

            if filepath.exists():
                inspect_geotiff(filepath)

log("\nSTEP 2: SNAP PRODUCT INVENTORY")

inspect_snap_products()

log("\nSTEP 3: SEARCH PROCESSING METADATA")

metadata_files = find_metadata_files()

log(f"Metadata files found outside raw SAFE folders: {len(metadata_files)}")

if not metadata_files:
    log("No external SNAP processing metadata files found.")

for filepath in metadata_files:
    inspect_metadata_file(filepath)

# --------------------------------------------------
# 8. SAVE REPORT
# --------------------------------------------------

OUTPUT_FILE.write_text(
    "\n".join(report_lines),
    encoding="utf-8"
)

log("\n" + "=" * 65)
log("AUDIT COMPLETED")
log(f"Report saved: {OUTPUT_FILE}")
log("=" * 65)
