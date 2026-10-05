import pandas as pd
from src.anomaly_detector import OrderAnomalyDetector


def test_iqr_anomaly_and_cancelled_stats():
    valid_df = pd.DataFrame({
        'InvoiceNo': [
            '101',
            '101',
            '102',
            '103',
            '104',
            '105',
            '999'
        ],

        'StockCode': [
            'A',
            'B',
            'A',
            'A',
            'A',
            'A',
            'Z'
        ],

        'Quantity': [
            1,
            1,
            2,
            2,
            3,
            3,
            500
        ],

        'Revenue': [
            50.0,
            50.0,
            110.0,
            120.0,
            130.0,
            140.0,
            10000.0
        ]
    })

    cancel_df = pd.DataFrame({
        'InvoiceNo': [
            'C201',
            'C201'
        ],

        'Quantity': [
            -10,
            -5
        ]
    })

    detector = OrderAnomalyDetector(
        df_valid=valid_df,
        df_cancelled=cancel_df
    )

    cancel_stats = (
        detector.analyze_cancelled_orders()
    )

    assert (
        cancel_stats[
            'cancelled_invoices'
        ]
        == 1
    )

    assert (
        cancel_stats[
            'cancelled_lines'
        ]
        == 2
    )

    assert (
        cancel_stats[
            'total_returned_qty'
        ]
        == 15
    )

    detector.aggregate_orders()

    order_stats = (
        detector.detect_iqr_anomalies()
    )

    anomaly_row = (
        order_stats.loc[
            order_stats[
                'InvoiceNo'
            ]
            == '999'
        ]
        .iloc[0]
    )

    assert (
        len(order_stats)
        == 6
    )

    assert (
        bool(
            anomaly_row[
                'IsRevenueAnomaly'
            ]
        )
        is True
    )

    assert (
        bool(
            anomaly_row[
                'IsQuantityAnomaly'
            ]
        )
        is True
    )

    assert (
        bool(
            anomaly_row[
                'IsAnomaly'
            ]
        )
        is True
    )


def test_quantity_only_anomaly_is_combined_anomaly(
    tmp_path
):
    valid_df = pd.DataFrame({
        'InvoiceNo': [
            '101',
            '102',
            '103',
            '104',
            '105',
            '999'
        ],

        'StockCode': [
            'A'
        ] * 6,

        'Quantity': [
            1,
            2,
            2,
            3,
            3,
            100
        ],

        'Revenue': [
            100.0,
            110.0,
            120.0,
            130.0,
            140.0,
            150.0
        ]
    })

    output_path = (
        tmp_path
        / 'anomaly_orders.csv'
    )

    detector = OrderAnomalyDetector(
        df_valid=valid_df,
        df_cancelled=pd.DataFrame()
    )

    detector.aggregate_orders()

    stats = (
        detector.detect_iqr_anomalies(
            output_csv_path=output_path
        )
    )

    row = (
        stats.loc[
            stats[
                'InvoiceNo'
            ]
            == '999'
        ]
        .iloc[0]
    )

    assert (
        bool(
            row[
                'IsRevenueAnomaly'
            ]
        )
        is False
    )

    assert (
        bool(
            row[
                'IsQuantityAnomaly'
            ]
        )
        is True
    )

    assert (
        bool(
            row[
                'IsAnomaly'
            ]
        )
        is True
    )

    exported = pd.read_csv(
        output_path,
        dtype={
            'InvoiceNo': str
        }
    )

    assert (
        exported[
            'InvoiceNo'
        ].tolist()
        == ['999']
    )

    assert (
        exported[
            'IsAnomaly'
        ].all()
    )


def test_empty_dataframe():
    detector = OrderAnomalyDetector(
        df_valid=pd.DataFrame(),
        df_cancelled=pd.DataFrame()
    )

    detector.aggregate_orders()

    stats = (
        detector.detect_iqr_anomalies()
    )

    impact = (
        detector.evaluate_business_impact()
    )

    assert stats.empty

    assert list(
        stats.columns
    ) == [
        'InvoiceNo',
        'Revenue',
        'TotalQuantity',
        'LineCount',
        'IsRevenueAnomaly',
        'IsQuantityAnomaly',
        'IsAnomaly'
    ]

    assert (
        impact[
            'total_revenue'
        ]
        == 0.0
    )

    assert (
        impact[
            'combined'
        ][
            'anomaly_orders'
        ]
        == 0
    )


def test_zero_iqr_edge_case():
    zero_iqr_df = pd.DataFrame({
        'InvoiceNo': [
            '1',
            '2',
            '3',
            '4'
        ],

        'StockCode': [
            'A',
            'A',
            'A',
            'A'
        ],

        'Quantity': [
            5,
            5,
            5,
            5
        ],

        'Revenue': [
            100.0,
            100.0,
            100.0,
            100.0
        ]
    })

    detector = OrderAnomalyDetector(
        df_valid=zero_iqr_df,
        df_cancelled=pd.DataFrame()
    )

    detector.aggregate_orders()

    stats = (
        detector.detect_iqr_anomalies()
    )

    assert (
        stats[
            'IsRevenueAnomaly'
        ].sum()
        == 0
    )

    assert (
        stats[
            'IsQuantityAnomaly'
        ].sum()
        == 0
    )

    assert (
        stats[
            'IsAnomaly'
        ].sum()
        == 0
    )


def test_business_impact_reports_revenue_quantity_and_combined():
    valid_df = pd.DataFrame({
        'InvoiceNo': [
            '101',
            '102',
            '103',
            '104',
            '105',
            '106',
            '999'
        ],

        'StockCode': [
            'A'
        ] * 7,

        'Quantity': [
            1,
            2,
            2,
            3,
            3,
            100,
            4
        ],

        'Revenue': [
            100.0,
            110.0,
            120.0,
            130.0,
            140.0,
            150.0,
            10000.0
        ]
    })

    detector = OrderAnomalyDetector(
        df_valid=valid_df,
        df_cancelled=pd.DataFrame()
    )

    detector.aggregate_orders()
    detector.detect_iqr_anomalies()

    impact = (
        detector.evaluate_business_impact()
    )

    assert (
        impact[
            'revenue'
        ][
            'anomaly_orders'
        ]
        == 1
    )

    assert (
        impact[
            'quantity'
        ][
            'anomaly_orders'
        ]
        == 1
    )

    assert (
        impact[
            'combined'
        ][
            'anomaly_orders'
        ]
        == 2
    )

    assert (
        impact[
            'anomaly_revenue'
        ]
        ==
        impact[
            'combined'
        ][
            'anomaly_revenue'
        ]
    )

    assert (
        impact[
            'impact_ratio'
        ]
        ==
        impact[
            'combined'
        ][
            'revenue_ratio'
        ]
    )