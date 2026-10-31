# Contributing

Contributions that improve reproducibility, documentation, code quality or scientific interpretation are welcome.

## Before contributing

1. Open an issue describing the proposed change.
2. Keep raw Sentinel-1 `.SAFE` products and large processed rasters out of Git.
3. Do not commit credentials, personal data, temporary files or locally generated audit files.
4. Preserve source attribution and licence information for every external dataset.

## Code changes

- Use clear, descriptive file and variable names.
- Document processing parameters and assumptions.
- Keep scripts reproducible from the documented project structure.
- Avoid hard-coded machine-specific paths.
- Explain any change that affects geospatial CRS, pixel alignment, masks, thresholds or area calculations.

## Scientific reporting

Do not describe SAR backscatter-change candidates as confirmed new construction or validated urban expansion without independent reference data. Clearly distinguish observations, candidate detections and validated classifications.

## Pull requests

Include:
- A concise description of the change
- The reason for the change
- Any processing or dependency changes
- A reproducible test or example, where practical
- Updated documentation when outputs or methods change
