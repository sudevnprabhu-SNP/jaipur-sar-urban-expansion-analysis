
from pathlib import Path
import xml.etree.ElementTree as ET

# --------------------------------------------------
# 1. PROJECT PATHS
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_DIR / "data" / "raw"

SAFE_PRODUCTS = {
    2016: (
        "S1A_IW_GRDH_1SDV_20160302T005217_"
        "20160302T005242_010183_00F074_C380.SAFE"
    ),
    2020: (
        "S1A_IW_GRDH_1SDV_20200305T005233_"
        "20200305T005258_031533_03A1F5_7036.SAFE"
    ),
    2025: (
        "S1A_IW_GRDH_1SDV_20250303T005248_"
        "20250303T005313_058133_072E2C_6B0E.SAFE"
    )
}

KEYWORDS = [
    "mission",
    "mode",
    "producttype",
    "productclass",
    "polarisation",
    "polarization",
    "pass",
    "relativeorbit",
    "absoluteorbit",
    "orbitnumber",
    "starttime",
    "stoptime",
    "slicenumber",
    "total slices",
    "datatake",
    "platform",
    "instrument"
]


def local_name(tag):
    """Remove XML namespace from tag name."""
    return tag.split("}")[-1]


def inspect_xml(xml_path):

    print(f"\nXML FILE: {xml_path.name}")

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as error:
        print(f"XML parsing error: {error}")
        return

    found = set()

    for element in root.iter():

        tag = local_name(element.tag)
        value = (element.text or "").strip()

        if not value:
            continue

        tag_lower = tag.lower()

        if any(keyword in tag_lower for keyword in KEYWORDS):

            entry = (tag, value)

            if entry not in found:
                found.add(entry)
                print(f"  {tag}: {value}")


# --------------------------------------------------
# 2. INSPECT ALL THREE SAFE PRODUCTS
# --------------------------------------------------

for year, safe_name in SAFE_PRODUCTS.items():

    safe_dir = RAW_DIR / safe_name

    print("\n" + "=" * 65)
    print(f"SENTINEL-1 METADATA: {year}")
    print("=" * 65)

    if not safe_dir.exists():
        print(f"ERROR: SAFE folder not found: {safe_dir}")
        continue

    manifest = safe_dir / "manifest.safe"

    if not manifest.exists():
        print("ERROR: manifest.safe not found.")
        continue

    print(f"SAFE PRODUCT: {safe_name}")

    inspect_xml(manifest)

    # Find annotation product XML files
    annotation_dir = safe_dir / "annotation"

    if annotation_dir.exists():

        annotation_files = sorted(
            annotation_dir.glob("*.xml")
        )

        print(
            f"\nAnnotation XML files found: "
            f"{len(annotation_files)}"
        )

        # Inspect the first product annotation XML
        product_xml = [
            file for file in annotation_files
            if "calibration" not in file.parts
            and "noise" not in file.parts
        ]

        if product_xml:
            inspect_xml(product_xml[0])

    else:
        print("Annotation directory not found.")

print("\nMetadata inspection completed.")
