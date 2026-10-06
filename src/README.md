# src/

Thư mục chứa mã nguồn chính của data pipeline và analytics.

Các module hiện tại:

- `data_processor.py`: data validation, cleaning, cancelled invoice separation và feature engineering.
- `anomaly_detector.py`: order aggregation, Revenue/Quantity IQR anomaly detection, business-impact analysis và chart generation.
- `feature_engineering.py`: RFM/customer feature engineering.
- `main.py`: entry point của pipeline.
- `scraper.py`: logic thu thập dữ liệu bổ sung.

Pipeline chính có thể chạy từ repository root bằng:

```bash
python src/main.py