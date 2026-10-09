# notebooks/

Jupyter notebooks are used for exploratory analysis, validation and reproducible project deliverables. Stable reusable transformations live in `src/`; notebooks import those functions rather than duplicating business logic.

Current notebooks:

- `04_customer_segmentation.ipynb` — Issue #8 production RFM segmentation, validation, customer/segment analysis, chart generation and local `customer_segments.csv` export.
- `05_python_oop_demo.ipynb` — Python/OOP demonstration for the project pipeline.

For `04_customer_segmentation.ipynb`, place the latest reviewed dataset at `data/processed/cleaned_retail.csv` before execution.

- `06_final_integrated_analysis.ipynb` — Issue #22 final integration, reusable src analytics and KPI #18 reconciliation; run with Jupyter from repo root or notebooks directory.
