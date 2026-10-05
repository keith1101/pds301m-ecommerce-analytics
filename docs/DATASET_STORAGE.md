# Dataset Storage and Reproducibility

The UCI Online Retail dataset and regenerated CSVs are **not committed to Git**. Store them locally for reproducible analysis and upload the shared versions to the [PDS301m datasets folder on Google Drive](https://drive.google.com/drive/folders/1DK_GnMEpRMcgrnnZ52CT33Opvto9i9qn).

- `data/raw/online_retail.xlsx`: Original UCI Online Retail dataset.
- `data/processed/cleaned_retail.csv`: Valid sales transactions (524,878 rows; total `Revenue` = £10,642,110.80).
- `data/processed/cancelled_retail.csv`: Cancelled transactions with `InvoiceNo` starting with `C` (9,251 rows across 3,836 invoices; total returned quantity = 275,560).
- `data/processed/anomaly_orders.csv`: High-value or high-quantity outlier invoices flagged via upper-tail IQR (`Q3 + 1.5 * IQR`).

## Output Schema (`cleaned_retail.csv`)

| Column | Type | Cleaning / Contract Rule |
|---|---|---|
| `InvoiceNo` | `string` | Trimmed string; non-cancelled valid invoices only (no `C` prefix) |
| `StockCode` | `string` | Product code |
| `Description` | `string` | Trimmed string; missing values filled with `'Unknown'` |
| `Quantity` | `int64` | Strictly positive (`> 0`) |
| `InvoiceDate` | `datetime` | Validated timestamp (`YYYY-MM-DD HH:MM:SS`) |
| `UnitPrice` | `float64` | Strictly positive (`> 0.0`) |
| `CustomerID` | `string` | Normalised integer string (e.g., `'17850'`); missing IDs filled with `'Guest'` (132,186 rows kept for EDA revenue, excluded in RFM) |
| `Country` | `string` | Country name |
| `Revenue` | `float64` | `Quantity * UnitPrice` |
| `YearMonth` | `string` | `YYYY-MM` period extracted from `InvoiceDate` |

## Local Workflow (Run from Repository Root)

1. Place `online_retail.xlsx` in `data/raw/online_retail.xlsx`.
2. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt