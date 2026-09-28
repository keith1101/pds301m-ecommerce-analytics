import pandas as pd
from src.anomaly_detector import OrderAnomalyDetector


def test_iqr_anomaly_and_cancelled_stats():
    valid_df = pd.DataFrame({
        'InvoiceNo': ['101', '101', '102', '103', '104', '105', '999'],
        'StockCode': ['A', 'B', 'A', 'A', 'A', 'A', 'Z'],
        'Quantity': [1, 1, 2, 2, 3, 3, 500],
        'Revenue': [50.0, 50.0, 110.0, 120.0, 130.0, 140.0, 10000.0]
    })
    cancel_df = pd.DataFrame({
        'InvoiceNo': ['C201', 'C201'],
        'Quantity': [-10, -5]
    })

    detector = OrderAnomalyDetector(df_valid=valid_df, df_cancelled=cancel_df)
    cancel_stats = detector.analyze_cancelled_orders()
    assert cancel_stats['cancelled_invoices'] == 1
    assert cancel_stats['cancelled_lines'] == 2
    assert cancel_stats['total_returned_qty'] == 15

    detector.aggregate_orders()
    order_stats = detector.detect_iqr_anomalies()
    assert len(order_stats) == 6
    assert bool(order_stats.loc[order_stats['InvoiceNo'] == '999', 'IsRevenueAnomaly'].iloc[0]) is True


def test_empty_and_zero_iqr_edge_cases():
    zero_iqr_df = pd.DataFrame({
        'InvoiceNo': ['1', '2', '3', '4'],
        'StockCode': ['A', 'A', 'A', 'A'],
        'Quantity': [5, 5, 5, 5],
        'Revenue': [100.0, 100.0, 100.0, 100.0]
    })
    detector = OrderAnomalyDetector(df_valid=zero_iqr_df, df_cancelled=pd.DataFrame())
    detector.aggregate_orders()
    stats = detector.detect_iqr_anomalies()
    assert stats['IsRevenueAnomaly'].sum() == 0