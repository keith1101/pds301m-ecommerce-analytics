import pandas as pd

from src.anomaly_detector import OrderAnomalyDetector
from src.feature_engineering import calculate_rfm

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

    

def test_tiki_rfm_excludes_guest_and_scores_ties():
    transactions = pd.DataFrame({
        "InvoiceNo": ["T001", "T002", "T003", "T004", "T005", "T006"],
        "Quantity": [1] * 6,
        "InvoiceDate": [
            "2026-01-01", "2026-01-03",
            "2026-01-01", "2026-01-03",
            "2026-01-02", "2026-01-10",
        ],
        "UnitPrice": [100, 200, 100, 200, 50, 500],
        "CustomerID": ["C1", "C1", "C2", "C2", "C3", "Guest"],
    })

    rfm, metadata = calculate_rfm(transactions, return_metadata=True)
    by_customer = rfm.set_index("CustomerID")

    assert set(by_customer.index) == {"C1", "C2", "C3"}
    assert metadata["valid_transaction_rows"] == 5
    assert metadata["reference_date"] == pd.Timestamp("2026-01-04")
    assert by_customer.loc["C1", "Frequency"] == 2
    assert by_customer.loc["C1", "Monetary"] == 300
    assert by_customer.loc["C1", "Recency"] == 1
    assert by_customer.loc["C1", "RFM_score"] == by_customer.loc["C2", "RFM_score"]
    assert by_customer.loc["C1", "Segment"] == by_customer.loc["C2", "Segment"]