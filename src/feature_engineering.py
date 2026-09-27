"""RFM feature engineering utilities for PDS301m Online Retail.

Issue #5: RFM Methodology & Prototype.

The module is deliberately defensive: even if ``cleaned_retail.csv`` has
already been cleaned, the RFM population is validated again before customer
aggregation so the methodology is reproducible from either raw-like samples
or the processed project dataset.
"""
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
QUANTILES = (0.20, 0.40, 0.60, 0.80)


def _normalise_customer_id(series: pd.Series) -> pd.Series:
    """Return CustomerID as stable strings; convert UCI values like 17850.0 -> 17850."""
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
    quantity = pd.to_numeric(df["Quantity"], errors="coerce")
    unit_price = pd.to_numeric(df["UnitPrice"], errors="coerce")
    invoice_date = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    anonymous = {label.casefold() for label in anonymous_customer_labels}

    is_missing_customer = customer.isna() | customer.eq("")
    is_anonymous_customer = customer.str.casefold().isin(anonymous).fillna(False)

    return {
        "input_rows": int(len(df)),
        "cancelled_rows": int(invoice.str.startswith("C", na=False).sum()),
        "missing_customer_rows": int(is_missing_customer.sum()),
        "anonymous_customer_rows": int(is_anonymous_customer.sum()),
        "nonpositive_quantity_rows": int(quantity.le(0).fillna(True).sum()),
        "nonpositive_unit_price_rows": int(unit_price.le(0).fillna(True).sum()),
        "invalid_invoice_date_rows": int(invoice_date.isna().sum()),
        "exact_duplicate_rows": int(df.duplicated().sum()),
    }


def prepare_rfm_transactions(
    df: pd.DataFrame,
    anonymous_customer_labels: tuple[str, ...] = DEFAULT_ANONYMOUS_CUSTOMER_LABELS,
) -> pd.DataFrame:
    """Filter transaction rows to the valid purchase population used by RFM.

    Eligibility rules
    -----------------
    * InvoiceNo does not start with ``C``.
    * CustomerID is present and is not an anonymous placeholder such as Guest.
    * Quantity > 0 and UnitPrice > 0.
    * InvoiceDate is parseable.
    * Exact duplicate rows are removed.

    Revenue is always recalculated as ``Quantity * UnitPrice`` so Monetary uses
    the same formula regardless of whether an input Revenue column already exists.
    """
    missing = REQUIRED_RFM_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    x = df.copy()
    x["InvoiceNo"] = x["InvoiceNo"].astype("string").str.strip()
    x["CustomerID"] = x["CustomerID"].astype("string").str.strip()
    x["InvoiceDate"] = pd.to_datetime(x["InvoiceDate"], errors="coerce")
    x["Quantity"] = pd.to_numeric(x["Quantity"], errors="coerce")
    x["UnitPrice"] = pd.to_numeric(x["UnitPrice"], errors="coerce")

    anonymous = {label.casefold() for label in anonymous_customer_labels}
    valid_customer = (
        x["CustomerID"].notna()
        & x["CustomerID"].ne("")
        & ~x["CustomerID"].str.casefold().isin(anonymous).fillna(False)
    )

    valid = (
        ~x["InvoiceNo"].str.startswith("C", na=False)
        & valid_customer
        & x["InvoiceDate"].notna()
        & x["Quantity"].gt(0)
        & x["UnitPrice"].gt(0)
    )

    x = x.loc[valid].drop_duplicates().copy()
    x["CustomerID"] = _normalise_customer_id(x["CustomerID"])
    x["Revenue"] = x["Quantity"] * x["UnitPrice"]
    return x


def _dense_fallback_score(series: pd.Series) -> pd.Series:
    """Map ordered unique values onto 1..5 when quantile edges are duplicated.

    Equal raw values always receive equal scores. With one unique value every
    observation receives neutral score 3. With 2-4 unique values, available
    values are spread deterministically across the 1..5 scale.
    """
    unique_values = np.sort(series.dropna().unique())
    n_unique = len(unique_values)

    if n_unique == 0:
        raise ValueError("Cannot score an empty/all-null series.")
    if n_unique == 1:
        return pd.Series(3, index=series.index, dtype="Int64")

    # Half-up rounding, avoiding Python's bankers rounding.
    raw_scores = 1 + np.floor(
        (np.arange(n_unique) * 4 / (n_unique - 1)) + 0.5
    ).astype(int)
    mapping = dict(zip(unique_values, raw_scores))
    return series.map(mapping).astype("Int64")


def score_rfm_metric(
    series: pd.Series,
    *,
    higher_is_better: bool,
) -> tuple[pd.Series, dict[str, Any]]:
    """Score one RFM metric on 1..5 using quintile cutoffs with a tie-safe fallback.

    Primary method: empirical 20/40/60/80% quantile thresholds. Threshold
    assignment uses ``searchsorted(..., side='left')`` so observations exactly
    equal to a cutoff stay together in the lower raw bucket.

    Fallback: if quantile edges are duplicated (or the metric has too few
    distinct values), use dense-value scaling. This prevents qcut duplicate-bin
    errors and avoids splitting equal raw values across different scores.
    """
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.isna().any():
        raise ValueError(f"RFM metric contains {int(numeric.isna().sum())} null/non-numeric values.")
    if numeric.empty:
        raise ValueError("Cannot score an empty RFM metric.")

    cutoffs = numeric.quantile(list(QUANTILES)).to_numpy(dtype=float)
    unique_cutoffs = np.unique(cutoffs)

    if len(unique_cutoffs) == len(QUANTILES):
        raw = np.searchsorted(cutoffs, numeric.to_numpy(dtype=float), side="left") + 1
        base_score = pd.Series(raw, index=series.index, dtype="Int64")
        method = "quantile"
    else:
        base_score = _dense_fallback_score(numeric)
        method = "dense_fallback"

    score = base_score if higher_is_better else (6 - base_score)
    score = score.clip(1, 5).astype("Int64")

    metadata = {
        "method": method,
        "q20": float(cutoffs[0]),
        "q40": float(cutoffs[1]),
        "q60": float(cutoffs[2]),
        "q80": float(cutoffs[3]),
        "n_unique": int(numeric.nunique()),
        "higher_is_better": bool(higher_is_better),
    }
    return score, metadata


def assign_rfm_segment(row: pd.Series) -> str:
    """Assign one mutually exclusive rule-based RFM segment.

    Rule precedence is intentional; the first matching rule wins.
    """
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
    if r >= 4 and f == 1:
        return "New Customers"
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
    """Calculate customer-level RFM metrics, scores and segments.

    Reference date rule: one calendar day after the latest valid purchase date.
    A supplied reference date must be strictly after the latest valid purchase
    date, so a customer purchasing on the final transaction date has Recency=1.
    """
    transactions = prepare_rfm_transactions(
        df, anonymous_customer_labels=anonymous_customer_labels
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
    rfm["RFM_total"] = rfm[["R_score", "F_score", "M_score"]].sum(axis=1).astype(int)
    rfm["Segment"] = rfm.apply(assign_rfm_segment, axis=1)
    rfm["ReferenceDate"] = reference

    columns = [
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
    rfm = rfm[columns].sort_values(
        ["RFM_total", "Monetary", "CustomerID"],
        ascending=[False, False, True],
    ).reset_index(drop=True)

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
