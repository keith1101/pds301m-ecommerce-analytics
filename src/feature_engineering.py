"""Reusable RFM utilities for the Issue #5 baseline and Issue #15 follow-up."""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

REQUIRED_RFM_COLUMNS = {
    "InvoiceNo",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
    "CustomerID",
}

DEFAULT_ANONYMOUS_CUSTOMER_LABELS = ("Guest",)

CUSTOMER_SEGMENTS_COLUMNS = [
    "CustomerID",
    "Recency",
    "Frequency",
    "Monetary",
    "R_score",
    "F_score",
    "M_score",
    "RFM_score",
    "RFM_total",
    "Segment",
    "LastPurchaseDate",
    "ReferenceDate",
]


def _normalise_customer_id(series: pd.Series) -> pd.Series:
    """Return CustomerID as stable strings; e.g. 17850.0 -> 17850."""
    result = series.astype("string").str.strip()
    return result.str.replace(r"\.0$", "", regex=True)


def audit_rfm_input(
    df: pd.DataFrame,
    anonymous_customer_labels: tuple[str, ...] = DEFAULT_ANONYMOUS_CUSTOMER_LABELS,
) -> dict[str, int]:
    """Return a non-exclusive audit of rows affected by RFM eligibility rules."""
    missing = REQUIRED_RFM_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    invoice = df["InvoiceNo"].astype("string").str.strip()
    customer = df["CustomerID"].astype("string").str.strip()

    quantity_raw = df["Quantity"]
    quantity_text = quantity_raw.astype("string").str.strip()
    quantity = pd.to_numeric(quantity_raw, errors="coerce")

    unit_price_raw = df["UnitPrice"]
    unit_price_text = unit_price_raw.astype("string").str.strip()
    unit_price = pd.to_numeric(unit_price_raw, errors="coerce")

    invoice_date = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    anonymous = {label.strip().casefold() for label in anonymous_customer_labels}

    is_missing_invoice = invoice.isna() | invoice.eq("").fillna(False)
    is_missing_customer = customer.isna() | customer.eq("").fillna(False)
    is_anonymous_customer = customer.str.casefold().isin(anonymous).fillna(False)

    is_missing_quantity = (
        quantity_raw.isna() | quantity_text.eq("").fillna(False)
    )
    is_nonnumeric_quantity = quantity.isna() & ~is_missing_quantity
    is_nonpositive_quantity = quantity.notna() & quantity.le(0)

    is_missing_unit_price = (
        unit_price_raw.isna() | unit_price_text.eq("").fillna(False)
    )
    is_nonnumeric_unit_price = unit_price.isna() & ~is_missing_unit_price
    is_nonpositive_unit_price = unit_price.notna() & unit_price.le(0)

    return {
        "input_rows": int(len(df)),
        "missing_invoice_rows": int(is_missing_invoice.sum()),
        "cancelled_rows": int(invoice.str.startswith("C", na=False).sum()),
        "missing_customer_rows": int(is_missing_customer.sum()),
        "anonymous_customer_rows": int(is_anonymous_customer.sum()),
        "missing_quantity_rows": int(is_missing_quantity.sum()),
        "nonnumeric_quantity_rows": int(is_nonnumeric_quantity.sum()),
        "nonpositive_quantity_rows": int(is_nonpositive_quantity.sum()),
        "missing_unit_price_rows": int(is_missing_unit_price.sum()),
        "nonnumeric_unit_price_rows": int(is_nonnumeric_unit_price.sum()),
        "nonpositive_unit_price_rows": int(is_nonpositive_unit_price.sum()),
        "invalid_invoice_date_rows": int(invoice_date.isna().sum()),
        "exact_duplicate_rows": int(df.duplicated().sum()),
    }


def prepare_rfm_transactions(
    df: pd.DataFrame,
    anonymous_customer_labels: tuple[str, ...] = DEFAULT_ANONYMOUS_CUSTOMER_LABELS,
) -> pd.DataFrame:
    """Return the valid purchase population used for customer-level RFM."""
    missing = REQUIRED_RFM_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    x = df.copy()
    x["InvoiceNo"] = x["InvoiceNo"].astype("string").str.strip()
    x["CustomerID"] = x["CustomerID"].astype("string").str.strip()
    x["InvoiceDate"] = pd.to_datetime(x["InvoiceDate"], errors="coerce")
    x["Quantity"] = pd.to_numeric(x["Quantity"], errors="coerce")
    x["UnitPrice"] = pd.to_numeric(x["UnitPrice"], errors="coerce")

    anonymous = {label.strip().casefold() for label in anonymous_customer_labels}
    valid_invoice = (
        x["InvoiceNo"].notna()
        & x["InvoiceNo"].ne("")
        & ~x["InvoiceNo"].str.startswith("C", na=False)
    )
    valid_customer = (
        x["CustomerID"].notna()
        & x["CustomerID"].ne("")
        & ~x["CustomerID"].str.casefold().isin(anonymous).fillna(False)
    )

    valid = (
        valid_invoice
        & valid_customer
        & x["InvoiceDate"].notna()
        & x["Quantity"].gt(0)
        & x["UnitPrice"].gt(0)
    )

    # Duplicate handling belongs to the upstream cleaning pipeline.
    # RFM must not silently apply an independent deduplication policy.
    x = x.loc[valid].copy()
    x["CustomerID"] = _normalise_customer_id(x["CustomerID"])
    x["Revenue"] = x["Quantity"] * x["UnitPrice"]
    return x


def score_rfm_metric(
    series: pd.Series,
    *,
    higher_is_better: bool,
) -> tuple[pd.Series, dict[str, Any]]:
    """Score one RFM metric 1–5 using tie-safe average percentile ranks.

    Formula:
        base_score = ceil(percentile_rank * 5)

    Frequency/Monetary:
        score = base_score

    Recency:
        score = 6 - base_score

    ``rank(method="average")`` ensures equal raw values receive equal scores.
    When the metric is constant, all observations receive neutral score 3
    because there is no relative ordering information.
    """
    numeric = pd.to_numeric(series, errors="coerce")

    if numeric.isna().any():
        raise ValueError(
            f"RFM metric contains {int(numeric.isna().sum())} "
            "null/non-numeric values."
        )
    if numeric.empty:
        raise ValueError("Cannot score an empty RFM metric.")

    percentile_rank = numeric.rank(
        method="average",
        pct=True,
        ascending=True,
    )
    n_unique = int(numeric.nunique())

    if n_unique == 1:
        score = pd.Series(3, index=series.index, dtype="Int64")
        metadata: dict[str, Any] = {
            "method": "percentile_rank_average",
            "rank_method": "average",
            "n_unique": n_unique,
            "higher_is_better": bool(higher_is_better),
            "min_percentile_rank": float(percentile_rank.min()),
            "max_percentile_rank": float(percentile_rank.max()),
            "constant_metric": True,
            "constant_score": 3,
        }
        return score, metadata

    base_score = pd.Series(
        np.ceil(percentile_rank.to_numpy(dtype=float) * 5).astype(int),
        index=series.index,
        dtype="Int64",
    ).clip(1, 5)

    score = base_score if higher_is_better else (6 - base_score)
    score = score.clip(1, 5).astype("Int64")

    metadata = {
        "method": "percentile_rank_average",
        "rank_method": "average",
        "n_unique": n_unique,
        "higher_is_better": bool(higher_is_better),
        "min_percentile_rank": float(percentile_rank.min()),
        "max_percentile_rank": float(percentile_rank.max()),
        "constant_metric": False,
        "constant_score": None,
    }
    return score, metadata


def assign_rfm_segment(row: pd.Series) -> str:
    """Assign one mutually exclusive segment; first matching rule wins."""
    r = int(row["R_score"])
    f = int(row["F_score"])
    m = int(row["M_score"])

    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"
    if r >= 3 and f >= 4:
        return "Loyal Customers"
    if r <= 2 and (f >= 3 or m >= 3):
        return "At Risk"
    if r >= 4 and 2 <= f <= 3:
        return "Potential Loyalists"
    if r <= 2 and f <= 2 and m <= 2:
        return "Hibernating"
    return "Others"


def calculate_rfm(
    df: pd.DataFrame,
    reference_date: str | pd.Timestamp | None = None,
    *,
    anonymous_customer_labels: tuple[str, ...] = DEFAULT_ANONYMOUS_CUSTOMER_LABELS,
    return_metadata: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, dict[str, Any]]:
    """Calculate customer-level RFM metrics, percentile scores and segments."""
    transactions = prepare_rfm_transactions(
        df,
        anonymous_customer_labels=anonymous_customer_labels,
    )
    if transactions.empty:
        raise ValueError("No valid purchase rows remain after RFM eligibility rules.")

    last_valid_purchase = transactions["InvoiceDate"].max()

    if reference_date is None:
        reference = last_valid_purchase.normalize() + pd.Timedelta(days=1)
    else:
        reference = pd.Timestamp(reference_date).normalize()
        if reference <= last_valid_purchase.normalize():
            raise ValueError(
                "reference_date must be after the latest valid purchase date "
                f"({last_valid_purchase.normalize().date()})."
            )

    rfm = (
        transactions.groupby("CustomerID", as_index=False)
        .agg(
            LastPurchaseDate=("InvoiceDate", "max"),
            Frequency=("InvoiceNo", "nunique"),
            Monetary=("Revenue", "sum"),
        )
    )

    rfm["LastPurchaseDate"] = rfm["LastPurchaseDate"].dt.normalize()
    rfm["Recency"] = (reference - rfm["LastPurchaseDate"]).dt.days.astype(int)

    rfm["R_score"], r_meta = score_rfm_metric(
        rfm["Recency"], higher_is_better=False
    )
    rfm["F_score"], f_meta = score_rfm_metric(
        rfm["Frequency"], higher_is_better=True
    )
    rfm["M_score"], m_meta = score_rfm_metric(
        rfm["Monetary"], higher_is_better=True
    )

    rfm["RFM_score"] = (
        rfm["R_score"].astype(str)
        + rfm["F_score"].astype(str)
        + rfm["M_score"].astype(str)
    )
    rfm["RFM_total"] = (
        rfm[["R_score", "F_score", "M_score"]].sum(axis=1).astype(int)
    )
    rfm["Segment"] = rfm.apply(assign_rfm_segment, axis=1)
    rfm["ReferenceDate"] = reference

    rfm = (
        rfm[CUSTOMER_SEGMENTS_COLUMNS]
        .sort_values(
            ["RFM_total", "Monetary", "CustomerID"],
            ascending=[False, False, True],
        )
        .reset_index(drop=True)
    )

    metadata: dict[str, Any] = {
        "reference_date": reference,
        "last_valid_purchase": last_valid_purchase,
        "valid_transaction_rows": int(len(transactions)),
        "customers": int(rfm["CustomerID"].nunique()),
        "invoices": int(transactions["InvoiceNo"].nunique()),
        "scoring": {
            "Recency": r_meta,
            "Frequency": f_meta,
            "Monetary": m_meta,
        },
    }

    if return_metadata:
        return rfm, metadata
    return rfm
