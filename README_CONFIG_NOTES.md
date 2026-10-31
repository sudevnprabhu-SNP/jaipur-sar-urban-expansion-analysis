# Configuration bundle notes

Copy the files in this bundle into the root of the project repository.

## Important checks before publishing

1. `requirements.txt` is an initial dependency list inferred from the documented workflow. It has not yet been checked against every import in all scripts. Verify it before claiming that a fresh install reproduces the entire project.
2. `LICENSE` applies to original project code only. Third-party data retain their own licence conditions.
3. Verify the exact OpenCity/BharatAtlas municipal-boundary licence and source attribution before redistributing boundary files.
4. `.gitignore` intentionally excludes processed GeoTIFF/IMG/DIM outputs and GeoPackages. It keeps source code, documentation, notebooks, GeoJSON boundary files and report figures eligible for Git.
5. If a small derived vector file or raster is essential to reproduce a demonstration, consider publishing a small sample in a dedicated `data/sample/` directory with its own source and licence notes. Do not remove ignore rules globally just to force large datasets into Git.
6. SNAP is an external desktop processing application; it is not installed by `pip install -r requirements.txt`.
