import json
from pathlib import Path

import pandas as pd

from src.data_processor import TikiDataProcessor


EXPECTED_COLUMNS = [
    'InvoiceNo',
    'StockCode',
    'Description',
    'Quantity',
    'InvoiceDate',
    'UnitPrice',
    'CustomerID',
    'Country',
    'Revenue',
    'YearMonth',
]


def _write_csv_fixture(base: Path):
    products = pd.DataFrame([
        {'id': 101, 'name': 'Notebook', 'price': 25000},
        {'id': 102, 'name': None, 'price': 10000},
        {'id': 103, 'name': 'Invalid Price', 'price': 0},
    ])
    reviews = pd.DataFrame([
        {
            'id': 9001,
            'product_id': 101,
            'customer_id': 501,
            'purchased': True,
            'created_at': 1700000000,
        },
        {
            'id': 9002,
            'product_id': 102,
            'customer_id': None,
            'purchased': True,
            'created_at': 1700086400,
        },
        {
            'id': 9003,
            'product_id': 101,
            'customer_id': 502,
            'purchased': False,
            'created_at': 1700172800,
        },
        {
            'id': 9004,
            'product_id': 103,
            'customer_id': 503,
            'purchased': True,
            'created_at': 1700259200,
        },
    ])
    products.to_csv(base / 'raw_tiki_products.csv', index=False)
    reviews.to_csv(base / 'raw_tiki_reviews.csv', index=False)


def test_tiki_processor_maps_verified_reviews_to_canonical_schema(tmp_path: Path):
    _write_csv_fixture(tmp_path)

    processor = TikiDataProcessor(tmp_path)
    processor.load_data()
    processor.clean_data()
    processor.engineer_features()

    assert processor.df_valid.columns.tolist() == EXPECTED_COLUMNS
    assert processor.df_valid['InvoiceNo'].tolist() == [
        'TIKI_REV_9001',
        'TIKI_REV_9002',
    ]
    assert processor.df_valid['StockCode'].tolist() == ['101', '102']
    assert processor.df_valid['Quantity'].tolist() == [1, 1]
    assert processor.df_valid['Country'].tolist() == ['Vietnam', 'Vietnam']
    assert processor.df_valid['CustomerID'].tolist() == ['501', 'Guest']
    assert processor.df_valid['Description'].tolist() == ['Notebook', 'Unknown']
    assert processor.df_valid['Revenue'].tolist() == [25000, 10000]
    assert processor.df_valid['YearMonth'].tolist() == ['2023-11', '2023-11']
    assert processor.df_valid[EXPECTED_COLUMNS].isna().sum().sum() == 0


def test_tiki_processor_revenue_is_quantity_times_unit_price(tmp_path: Path):
    _write_csv_fixture(tmp_path)

    processor = TikiDataProcessor(tmp_path)
    processor.load_data()
    processor.clean_data()
    processor.engineer_features()

    expected = processor.df_valid['Quantity'] * processor.df_valid['UnitPrice']
    pd.testing.assert_series_equal(
        processor.df_valid['Revenue'],
        expected,
        check_names=False,
    )


def test_tiki_processor_duplicate_audit_and_deduplication(tmp_path: Path):
    products = pd.DataFrame([
        {'id': 101, 'name': 'Notebook', 'price': 25000},
    ])
    duplicate_review = {
        'id': 9001,
        'product_id': 101,
        'customer_id': 501,
        'purchased': True,
        'created_at': 1700000000,
    }
    reviews = pd.DataFrame([duplicate_review, duplicate_review])
    products.to_csv(tmp_path / 'raw_tiki_products.csv', index=False)
    reviews.to_csv(tmp_path / 'raw_tiki_reviews.csv', index=False)

    processor = TikiDataProcessor(tmp_path)
    processor.load_data()
    processor.clean_data(deduplicate=True)
    processor.engineer_features()

    assert processor.audit_stats['duplicate_rows'] == 1
    assert processor.audit_stats['qty_diff_dedup'] == 1.0
    assert processor.audit_stats['rev_diff_dedup'] == 25000.0
    assert len(processor.df_valid) == 1


def test_tiki_processor_deduplicate_false_keeps_duplicates(tmp_path: Path):
    products = pd.DataFrame([
        {'id': 101, 'name': 'Notebook', 'price': 25000},
    ])
    duplicate_review = {
        'id': 9001,
        'product_id': 101,
        'customer_id': 501,
        'purchased': True,
        'created_at': 1700000000,
    }
    reviews = pd.DataFrame([duplicate_review, duplicate_review])
    products.to_csv(tmp_path / 'raw_tiki_products.csv', index=False)
    reviews.to_csv(tmp_path / 'raw_tiki_reviews.csv', index=False)

    processor = TikiDataProcessor(tmp_path)
    processor.load_data()
    processor.clean_data(deduplicate=False)
    processor.engineer_features()

    assert processor.audit_stats['duplicate_rows'] == 1
    assert processor.audit_stats['qty_diff_dedup'] == 0.0
    assert processor.audit_stats['rev_diff_dedup'] == 0.0
    assert len(processor.df_valid) == 2


def test_tiki_processor_loads_consolidated_json(tmp_path: Path):
    with (tmp_path / 'all_products.json').open('w', encoding='utf-8') as handle:
        json.dump([
            {'id': 101, 'name': 'Notebook', 'price': 25000},
        ], handle)

    with (tmp_path / 'all_reviews.json').open('w', encoding='utf-8') as handle:
        json.dump([
            {
                'id': 9001,
                'product_id': 101,
                'created_at': 1700000000,
                'created_by': {
                    'id': 501,
                    'purchased': True,
                },
            }
        ], handle)

    processor = TikiDataProcessor(tmp_path)
    loaded = processor.load_data()
    processor.clean_data()
    processor.engineer_features()

    assert len(loaded) == 1
    assert processor.df_valid.iloc[0]['InvoiceNo'] == 'TIKI_REV_9001'
    assert processor.df_valid.iloc[0]['CustomerID'] == '501'


def test_tiki_processor_export_creates_cleaned_tiki_csv(tmp_path: Path):
    raw_dir = tmp_path / 'raw'
    out_dir = tmp_path / 'processed'
    raw_dir.mkdir()
    _write_csv_fixture(raw_dir)

    processor = TikiDataProcessor(raw_dir)
    processor.load_data()
    processor.clean_data()
    processor.engineer_features()

    clean_path = out_dir / 'cleaned_tiki.csv'
    cancelled_path = out_dir / 'cancelled_tiki.csv'
    processor.export_data(clean_path, cancelled_path)

    assert clean_path.exists()
    assert cancelled_path.exists()

    exported = pd.read_csv(clean_path)
    assert exported.columns.tolist() == EXPECTED_COLUMNS
    assert exported[EXPECTED_COLUMNS].isna().sum().sum() == 0
    assert (exported['Revenue'] == exported['Quantity'] * exported['UnitPrice']).all()
