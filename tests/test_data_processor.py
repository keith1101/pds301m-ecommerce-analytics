import pandas as pd
from src.data_processor import RetailDataProcessor


def test_clean_data_and_revenue():
    raw_df = pd.DataFrame({
        'InvoiceNo': ['536365', '536365', 'C536366', '536367', '536368'],
        'StockCode': ['85123A', '85123A', '71053', '84406B', '84406C'],
        'Description': ['Item A', 'Item A', 'Item B', 'Item C', 'Item D'],
        'Quantity': [2, 2, -3, -5, 4],
        'InvoiceDate': ['2010-12-01 08:26:00'] * 5,
        'UnitPrice': [10.0, 10.0, 5.0, 5.0, 2.5],
        'CustomerID': [17850.0, 17850.0, 17850.0, None, None],
        'Country': ['UK'] * 5
    })

    processor = RetailDataProcessor("dummy.xlsx")
    processor.df = raw_df
    processor.clean_data(deduplicate=True, fill_guest=True)
    processor.engineer_features()

    assert processor.audit_stats['initial_rows'] == 5
    assert processor.audit_stats['duplicate_rows'] == 1
    assert processor.audit_stats['cancelled_rows'] == 1
    assert processor.audit_stats['invalid_qty_price_rows'] == 1
    assert processor.audit_stats['valid_rows'] == 2
    assert processor.df_valid['Revenue'].sum() == 30.0
    assert 'Guest' in processor.df_valid['CustomerID'].values