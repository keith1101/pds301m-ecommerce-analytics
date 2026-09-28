import pandas as pd
import pytest

from src.feature_engineering import (
    CUSTOMER_SEGMENTS_COLUMNS,
    assign_rfm_segment,
    calculate_rfm,
    prepare_rfm_transactions,
    score_rfm_metric,
)


def sample_transactions() -> pd.DataFrame:
    return pd.DataFrame(
        [
            ["10001", "A", 1, "2011-12-01 10:00", 10.0, "1"],
            ["10001", "B", 2, "2011-12-01 10:00", 5.0, "1"],
            ["10002", "C", 1, "2011-12-05 10:00", 20.0, "1"],
            ["10003", "A", 1, "2011-12-09 09:00", 10.0, "2"],
            ["10004", "A", 2, "2011-12-07 09:00", 10.0, "3"],
            ["10005", "A", 2, "2011-12-07 09:00", 10.0, "4"],
            ["C10006", "A", -1, "2011-12-08 09:00", 10.0, "5"],
            ["10007", "A", 1, "2011-12-08 09:00", 10.0, None],
            ["10008", "A", 1, "2011-12-08 09:00", 10.0, "Guest"],
            ["10009", "A", 0, "2011-12-08 09:00", 10.0, "6"],
            ["10010", "A", 1, "2011-12-08 09:00", 0.0, "7"],
            ["10011", "D", 1, "2011-12-06 09:00", 15.0, "8"],
            ["10011", "D", 1, "2011-12-06 09:00", 15.0, "8"],
        ],
        columns=[
            "InvoiceNo", "StockCode", "Quantity",
            "InvoiceDate", "UnitPrice", "CustomerID",
        ],
    )


def test_multiple_product_lines_same_invoice_count_once():
    rfm = calculate_rfm(sample_transactions(), reference_date="2011-12-10")
    c1 = rfm.loc[rfm["CustomerID"].eq("1")].iloc[0]
    assert c1["Frequency"] == 2
    assert c1["Monetary"] == pytest.approx(40.0)


def test_latest_purchase_has_recency_one():
    rfm = calculate_rfm(sample_transactions(), reference_date="2011-12-10")
    c2 = rfm.loc[rfm["CustomerID"].eq("2")].iloc[0]
    assert c2["Recency"] == 1


def test_cancelled_missing_guest_and_invalid_rows_are_excluded():
    valid = prepare_rfm_transactions(sample_transactions())
    assert set(valid["CustomerID"].unique()) == {"1", "2", "3", "4", "8"}
    assert not valid["InvoiceNo"].str.startswith("C").any()
    assert "Guest" not in set(valid["CustomerID"])


def test_exact_duplicates_removed():
    rfm = calculate_rfm(sample_transactions(), reference_date="2011-12-10")
    c8 = rfm.loc[rfm["CustomerID"].eq("8")].iloc[0]
    assert c8["Frequency"] == 1
    assert c8["Monetary"] == pytest.approx(15.0)


def test_equal_rfm_values_receive_equal_scores():
    rfm = calculate_rfm(sample_transactions(), reference_date="2011-12-10")
    c3 = rfm.loc[rfm["CustomerID"].eq("3")].iloc[0]
    c4 = rfm.loc[rfm["CustomerID"].eq("4")].iloc[0]
    assert tuple(c3[["Recency", "Frequency", "Monetary"]]) == tuple(
        c4[["Recency", "Frequency", "Monetary"]]
    )
    assert tuple(c3[["R_score", "F_score", "M_score"]]) == tuple(
        c4[["R_score", "F_score", "M_score"]]
    )


def test_percentile_rank_scoring_is_tie_safe():
    values = pd.Series([1, 1, 1, 2, 2, 3], dtype=float)
    scores, meta = score_rfm_metric(values, higher_is_better=True)

    assert scores.tolist() == [2, 2, 2, 4, 4, 5]
    assert scores[values.eq(1)].nunique() == 1
    assert scores[values.eq(2)].nunique() == 1
    assert meta["method"] == "percentile_rank_average"
    assert meta["rank_method"] == "average"


def test_single_unique_value_is_stable_under_percentile_method():
    scores, meta = score_rfm_metric(
        pd.Series([7, 7, 7], dtype=float),
        higher_is_better=True,
    )
    assert scores.tolist() == [4, 4, 4]
    assert meta["method"] == "percentile_rank_average"


def test_recency_direction_is_reversed():
    values = pd.Series([1, 10, 30, 60, 120, 300], dtype=float)
    scores, meta = score_rfm_metric(values, higher_is_better=False)

    assert scores.iloc[0] > scores.iloc[-1]
    assert meta["higher_is_better"] is False


def test_auto_reference_date_is_day_after_latest_purchase():
    rfm, meta = calculate_rfm(sample_transactions(), return_metadata=True)
    assert meta["reference_date"] == pd.Timestamp("2011-12-10")
    assert rfm["ReferenceDate"].nunique() == 1
    assert rfm["ReferenceDate"].iloc[0] == pd.Timestamp("2011-12-10")


def test_reference_date_must_be_after_latest_purchase():
    with pytest.raises(ValueError, match="reference_date must be after"):
        calculate_rfm(sample_transactions(), reference_date="2011-12-09")


def test_scores_always_within_one_to_five():
    rfm = calculate_rfm(sample_transactions(), reference_date="2011-12-10")
    for column in ["R_score", "F_score", "M_score"]:
        assert rfm[column].between(1, 5).all()


def test_customer_segments_schema():
    rfm = calculate_rfm(sample_transactions(), reference_date="2011-12-10")

    assert rfm.columns.tolist() == CUSTOMER_SEGMENTS_COLUMNS
    assert rfm["CustomerID"].is_unique
    assert rfm["CustomerID"].notna().all()
    assert rfm["Recency"].ge(1).all()
    assert rfm["Frequency"].ge(1).all()
    assert rfm["Monetary"].gt(0).all()
    assert rfm["RFM_score"].astype(str).str.fullmatch(r"[1-5]{3}").all()
    assert rfm["RFM_total"].between(3, 15).all()


def test_segment_precedence():
    champion = pd.Series({"R_score": 5, "F_score": 5, "M_score": 5})
    loyal = pd.Series({"R_score": 3, "F_score": 4, "M_score": 2})
    at_risk = pd.Series({"R_score": 1, "F_score": 5, "M_score": 5})

    assert assign_rfm_segment(champion) == "Champions"
    assert assign_rfm_segment(loyal) == "Loyal Customers"
    assert assign_rfm_segment(at_risk) == "At Risk"
