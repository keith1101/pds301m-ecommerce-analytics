import pandas as pd
import pytest

from src.feature_engineering import (
    CUSTOMER_SEGMENTS_COLUMNS,
    audit_rfm_input,
    assign_rfm_segment,
    calculate_rfm,
    prepare_rfm_transactions,
    score_rfm_metric,
)


ALLOWED_SEGMENTS = {
    "Champions",
    "Loyal Customers",
    "At Risk",
    "Potential Loyalists",
    "Hibernating",
    "Others",
}


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
            [None, "E", 1, "2011-12-08 09:00", 12.0, "9"],
            ["   ", "F", 1, "2011-12-08 09:00", 13.0, "10"],
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


def test_cancelled_missing_invoice_missing_customer_guest_and_invalid_rows_are_excluded():
    valid = prepare_rfm_transactions(sample_transactions())
    assert set(valid["CustomerID"].unique()) == {"1", "2", "3", "4", "8"}
    assert valid["InvoiceNo"].notna().all()
    assert valid["InvoiceNo"].str.strip().ne("").all()
    assert not valid["InvoiceNo"].str.startswith("C").any()
    assert "Guest" not in set(valid["CustomerID"])


def test_audit_reports_missing_invoice_and_duplicate_rows():
    audit = audit_rfm_input(sample_transactions())
    assert audit["missing_invoice_rows"] == 2
    assert audit["exact_duplicate_rows"] == 1


def test_rfm_does_not_silently_deduplicate_input():
    valid = prepare_rfm_transactions(sample_transactions())
    c8_rows = valid.loc[valid["CustomerID"].eq("8")]
    assert len(c8_rows) == 2
    assert c8_rows.duplicated().sum() == 1

    rfm = calculate_rfm(sample_transactions(), reference_date="2011-12-10")
    c8 = rfm.loc[rfm["CustomerID"].eq("8")].iloc[0]
    assert c8["Frequency"] == 1
    assert c8["Monetary"] == pytest.approx(30.0)


def test_numeric_audit_separates_missing_nonnumeric_and_nonpositive_values():
    df = pd.DataFrame({
        "InvoiceNo": [f"1{i:04d}" for i in range(6)],
        "Quantity": [1, None, "", "abc", 0, -1],
        "InvoiceDate": ["2011-12-01"] * 6,
        "UnitPrice": [1, None, "", "xyz", 0, -2],
        "CustomerID": [str(i) for i in range(6)],
    })

    audit = audit_rfm_input(df)

    assert audit["missing_quantity_rows"] == 2
    assert audit["nonnumeric_quantity_rows"] == 1
    assert audit["nonpositive_quantity_rows"] == 2
    assert audit["missing_unit_price_rows"] == 2
    assert audit["nonnumeric_unit_price_rows"] == 1
    assert audit["nonpositive_unit_price_rows"] == 2


def test_guest_variants_are_never_grouped_as_customers():
    df = pd.DataFrame({
        "InvoiceNo": ["10001", "10002", "10003", "10004", "10005"],
        "Quantity": [1] * 5,
        "InvoiceDate": ["2011-12-01"] * 5,
        "UnitPrice": [10.0] * 5,
        "CustomerID": ["Guest", "guest", "GUEST", "  Guest  ", "12345"],
    })

    audit = audit_rfm_input(df)
    assert audit["anonymous_customer_rows"] == 4

    valid = prepare_rfm_transactions(df)
    assert valid["CustomerID"].tolist() == ["12345"]

    rfm = calculate_rfm(df, reference_date="2011-12-02")
    assert rfm["CustomerID"].tolist() == ["12345"]


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
    assert meta["constant_metric"] is False


@pytest.mark.parametrize("higher_is_better", [True, False])
@pytest.mark.parametrize("size", [1, 2, 3, 10])
def test_constant_metric_receives_neutral_score(higher_is_better, size):
    scores, meta = score_rfm_metric(
        pd.Series([7.0] * size),
        higher_is_better=higher_is_better,
    )

    assert scores.tolist() == [3] * size
    assert meta["n_unique"] == 1
    assert meta["constant_metric"] is True
    assert meta["constant_score"] == 3


def test_small_nonconstant_dataset_keeps_percentile_method():
    values = pd.Series([1.0, 2.0, 3.0])
    scores, meta = score_rfm_metric(values, higher_is_better=True)

    assert scores.tolist() == [2, 4, 5]
    assert scores.is_monotonic_increasing
    assert meta["n_unique"] == 3
    assert meta["constant_metric"] is False
    assert meta["constant_score"] is None


def test_scoring_is_stable_under_row_reordering():
    original = pd.Series([1, 1, 1, 2, 2, 3], dtype=float)
    shuffled = original.sample(frac=1, random_state=42)

    original_scores, _ = score_rfm_metric(original, higher_is_better=True)
    shuffled_scores, _ = score_rfm_metric(shuffled, higher_is_better=True)

    original_map = (
        pd.DataFrame({"value": original, "score": original_scores})
        .groupby("value")["score"]
        .first()
        .to_dict()
    )
    shuffled_map = (
        pd.DataFrame({"value": shuffled, "score": shuffled_scores})
        .groupby("value")["score"]
        .first()
        .to_dict()
    )

    assert original_map == shuffled_map


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


@pytest.mark.parametrize(
    ("scores", "expected"),
    [
        ((5, 5, 5), "Champions"),
        ((3, 4, 2), "Loyal Customers"),
        ((2, 3, 1), "At Risk"),
        ((5, 3, 1), "Potential Loyalists"),
        ((1, 1, 1), "Hibernating"),
        ((5, 1, 1), "Others"),
    ],
)
def test_all_segment_rules_and_precedence(scores, expected):
    r, f, m = scores
    row = pd.Series({"R_score": r, "F_score": f, "M_score": m})
    assert assign_rfm_segment(row) == expected


def test_segment_labels_follow_six_label_contract_without_new_customers():
    rfm = calculate_rfm(sample_transactions(), reference_date="2011-12-10")

    assert set(rfm["Segment"]).issubset(ALLOWED_SEGMENTS)
    assert "New Customers" not in ALLOWED_SEGMENTS
    assert "New Customers" not in set(rfm["Segment"])

    recent_low_frequency = pd.Series(
        {"R_score": 5, "F_score": 1, "M_score": 1}
    )
    assert assign_rfm_segment(recent_low_frequency) == "Others"


def test_alphanumeric_non_cancelled_invoice_is_allowed():
    df = pd.DataFrame({
        "InvoiceNo": ["A563185"],
        "Quantity": [1],
        "InvoiceDate": ["2011-12-01"],
        "UnitPrice": [10.0],
        "CustomerID": ["12345"],
    })

    valid = prepare_rfm_transactions(df)
    assert valid["InvoiceNo"].tolist() == ["A563185"]
