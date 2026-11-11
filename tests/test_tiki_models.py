import pandas as pd

from src.anomaly_detector import OrderAnomalyDetector


def test_tiki_iqr_flags_revenue_without_dropping_orders(tmp_path):
    # Mỗi review đã xác thực tương ứng một giao dịch, Quantity = 1.
    transactions = pd.DataFrame({
        "InvoiceNo": [f"T{i:03d}" for i in range(10)],
        "StockCode": ["P001"] * 10,
        "Quantity": [1] * 10,
        "Revenue": [100_000] * 9 + [1_000_000],
    })
    output_path = tmp_path / "tiki_anomaly_orders.csv"

    detector = OrderAnomalyDetector(
        df_valid=transactions,
        currency_prefix="VND ",
    )
    orders = detector.detect_iqr_anomalies(output_csv_path=output_path)
    exported = pd.read_csv(output_path, dtype={"InvoiceNo": str})

    assert len(orders) == 10  # Không xóa đơn dị biệt hoặc đơn bình thường.
    assert detector.metrics["ub_rev"] == 100_000
    assert detector.metrics["ub_qty"] == 1
    assert orders["IsRevenueAnomaly"].sum() == 1
    assert orders["IsQuantityAnomaly"].sum() == 0
    assert orders["IsAnomaly"].sum() == 1
    assert exported["InvoiceNo"].tolist() == ["T009"]
    assert len(exported) == 1