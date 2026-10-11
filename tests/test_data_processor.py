import pandas as pd
from src.data_processor import RetailDataProcessor


def test_clean_data_and_revenue():
    raw_df = pd.DataFrame({
        'InvoiceNo': [
            '536365',
            '536365',
            'C536366',
            '536367',
            '536368'
        ],
        'StockCode': [
            '85123A',
            '85123A',
            '71053',
            '84406B',
            '84406C'
        ],
        'Description': [
            'Item A',
            'Item A',
            'Item B',
            'Item C',
            'Item D'
        ],
        'Quantity': [
            2,
            2,
            -3,
            -5,
            4
        ],
        'InvoiceDate': [
            '2010-12-01 08:26:00'
        ] * 5,
        'UnitPrice': [
            10.0,
            10.0,
            5.0,
            5.0,
            2.5
        ],
        'CustomerID': [
            17850.0,
            17850.0,
            17850.0,
            None,
            None
        ],
        'Country': [
            'UK'
        ] * 5
    })

    processor = RetailDataProcessor(
        "dummy.xlsx"
    )

    processor.df = raw_df

    processor.clean_data(
        deduplicate=True,
        fill_guest=True
    )

    processor.engineer_features()

    assert (
        processor.audit_stats[
            'initial_rows'
        ]
        == 5
    )

    assert (
        processor.audit_stats[
            'duplicate_rows'
        ]
        == 1
    )

    assert (
        processor.audit_stats[
            'deduplication_applied'
        ]
        is True
    )

    assert (
        processor.audit_stats[
            'cancelled_rows'
        ]
        == 1
    )

    assert (
        processor.audit_stats[
            'invalid_qty_price_rows'
        ]
        == 1
    )

    assert (
        processor.audit_stats[
            'valid_rows'
        ]
        == 2
    )

    assert (
        processor.df_valid[
            'Revenue'
        ].sum()
        == 30.0
    )

    assert (
        'Guest'
        in processor.df_valid[
            'CustomerID'
        ].values
    )


def test_missing_and_invalid_core_fields_are_removed():
    raw_df = pd.DataFrame({
        'InvoiceNo': [
            '10001',
            None,
            float('nan'),
            pd.NA,
            '   ',
            '10006',
            '10007',
            '10008'
        ],

        'StockCode': [
            'A'
        ] * 8,

        'Description': [
            'Item'
        ] * 8,

        'Quantity': [
            1,
            1,
            1,
            1,
            1,
            1,
            'not-a-number',
            1
        ],

        'InvoiceDate': [
            '2010-12-01 08:26:00',
            '2010-12-01 08:26:00',
            '2010-12-01 08:26:00',
            '2010-12-01 08:26:00',
            '2010-12-01 08:26:00',
            'not-a-date',
            '2010-12-01 08:26:00',
            '2010-12-01 08:26:00'
        ],

        'UnitPrice': [
            10,
            10,
            10,
            10,
            10,
            10,
            10,
            'not-a-number'
        ],

        'CustomerID': [
            17850.0
        ] * 8,

        'Country': [
            'UK'
        ] * 8
    })

    processor = RetailDataProcessor(
        "dummy.xlsx"
    )

    processor.df = raw_df

    processor.clean_data(
        deduplicate=False
    )

    assert (
        processor.df_valid[
            'InvoiceNo'
        ].tolist()
        == ['10001']
    )

    assert (
        processor.audit_stats[
            'missing_invoice_rows'
        ]
        == 4
    )

    assert (
        processor.audit_stats[
            'invalid_invoice_date_rows'
        ]
        == 1
    )

    assert (
        processor.audit_stats[
            'invalid_quantity_rows'
        ]
        == 1
    )

    assert (
        processor.audit_stats[
            'invalid_unit_price_rows'
        ]
        == 1
    )

    assert (
        processor.audit_stats[
            'missing_core_rows'
        ]
        == 7
    )


def test_deduplicate_false_keeps_exact_duplicates():
    raw_df = pd.DataFrame({
        'InvoiceNo': [
            '10001',
            '10001'
        ],

        'StockCode': [
            'A',
            'A'
        ],

        'Description': [
            'Item',
            'Item'
        ],

        'Quantity': [
            2,
            2
        ],

        'InvoiceDate': [
            '2010-12-01 08:26:00',
            '2010-12-01 08:26:00'
        ],

        'UnitPrice': [
            10.0,
            10.0
        ],

        'CustomerID': [
            17850.0,
            17850.0
        ],

        'Country': [
            'UK',
            'UK'
        ]
    })

    processor = RetailDataProcessor(
        "dummy.xlsx"
    )

    processor.df = raw_df

    processor.clean_data(
        deduplicate=False
    )

    processor.engineer_features()

    assert (
        processor.audit_stats[
            'duplicate_rows'
        ]
        == 1
    )

    assert (
        processor.audit_stats[
            'deduplication_applied'
        ]
        is False
    )

    assert (
        processor.audit_stats[
            'after_dedup_rows'
        ]
        == 2
    )

    assert (
        processor.audit_stats[
            'qty_diff_dedup'
        ]
        == 0.0
    )

    assert (
        processor.audit_stats[
            'rev_diff_dedup'
        ]
        == 0.0
    )

    assert (
        processor.audit_stats[
            'valid_rows'
        ]
        == 2
    )

    assert (
        processor.df_valid[
            'Revenue'
        ].sum()
        == 40.0
    )