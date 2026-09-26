# Dataset storage and reproducibility

The UCI Online Retail dataset and regenerated CSVs are **not committed to Git**. Store them locally for reproducible analysis and upload the shared versions to the [PDS301m datasets folder on Google Drive](https://drive.google.com/drive/folders/1DK_GnMEpRMcgrnnZ52CT33Opvto9i9qn).

- [`raw/` on Drive](https://drive.google.com/drive/folders/1Wj6svF0XP1-Tvl70_SCzWTB92PAcdgXG): `online_retail.xlsx`, originally available from [UCI Online Retail](https://archive.ics.uci.edu/dataset/352/online+retail).
- [`processed/` on Drive](https://drive.google.com/drive/folders/19a60cttjkEcWZ02qW83Y3sBrQWlmQx1P): generated `cleaned_retail.csv`, `cancelled_retail.csv`, and, after Issue #6, `anomaly_orders.csv`.

## Local workflow

1. Obtain `online_retail.xlsx` from UCI or the group's Drive; save it to `data/raw/online_retail.xlsx`.
2. Install dependencies: `python -m pip install -r requirements.txt`.
3. Run the cleaning script from `src/` with `python main.py` (the original script currently assumes that working directory; adjust its paths before running from repo root).
4. Share processed CSVs in Drive `processed/`, keeping dataset version and cleaning rules consistent among all members.

Keep the large files outside Git and preserve the README files in the data folders. The two original, unrelated-history branches remain read-only source references during migration. This transplanted code has not yet passed automated tests; review CustomerID handling and relative file paths before the cleaning PR is merged.
