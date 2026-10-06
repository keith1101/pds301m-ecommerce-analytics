# tests/

Thư mục chứa automated tests cho data pipeline.

Các test hiện tại kiểm tra:

- data cleaning;
- duplicate handling;
- missing `InvoiceNo`;
- invalid `InvoiceDate`;
- non-numeric `Quantity`;
- non-numeric `UnitPrice`;
- cancelled invoices;
- Revenue calculation;
- Revenue anomaly;
- Quantity anomaly;
- combined `IsAnomaly`;
- empty DataFrame;
- zero-IQR edge case;
- anomaly CSV output;
- Revenue / Quantity / Combined business impact;
- RFM logic.

Chạy toàn bộ test từ repository root:

```bash
python -m pytest -q