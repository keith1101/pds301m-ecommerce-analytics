"""Production-level integration checks for Issue #8 customer RFM segmentation."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.feature_engineering import (
    CUSTOMER_SEGMENTS_COLUMNS,
    calculate_rfm,
    prepare_rfm_transactions,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "cleaned_retail.csv"

ALLOWED_SEGMENTS = {
    "Champions",
    "Loyal Customers",
    "At Risk",
    "Potential Loyalists",
    "Hibernating",
    "Others",
}


@pytest.mark.skipif(
    not DATA_PATH.exists(),
    reason="cleaned_retail.csv is a generated local artifact",
)
def test_production_rfm_reconciles_with_latest_cleaned_dataset():
    cleaned = pd.read_csv(
        DATA_PATH,
        dtype={"InvoiceNo": "string", "CustomerID": "string"},
        low_memory=False,
    )

    valid_transactions = prepare_rfm_transactions(cleaned)
    customer_segments, metadata = calculate_rfm(
        cleaned,
        return_metadata=True,
    )

    assert customer_segments.columns.tolist() == CUSTOMER_SEGMENTS_COLUMNS
    assert customer_segments["CustomerID"].notna().all()
    assert customer_segments["CustomerID"].is_unique
    assert set(customer_segments["Segment"]).issubset(ALLOWED_SEGMENTS)

    assert metadata["valid_transaction_rows"] == len(valid_transactions)
    assert metadata["customers"] == customer_segments["CustomerID"].nunique()
    assert metadata["invoices"] == valid_transactions["InvoiceNo"].nunique()

    assert np.isclose(
        customer_segments["Monetary"].sum(),
        valid_transactions["Revenue"].sum(),
        rtol=0,
        atol=1e-6,
    )

    segment_summary = (
        customer_segments.groupby("Segment", as_index=False)
        .agg(
            CustomerCount=("CustomerID", "nunique"),
            Revenue=("Monetary", "sum"),
        )
    )
    segment_summary["RevenueShare"] = (
        segment_summary["Revenue"] / segment_summary["Revenue"].sum()
    )

    assert segment_summary["CustomerCount"].sum() == len(customer_segments)
    assert np.isclose(
        segment_summary["Revenue"].sum(),
        customer_segments["Monetary"].sum(),
        rtol=0,
        atol=1e-6,
    )
    assert np.isclose(segment_summary["RevenueShare"].sum(), 1.0)
