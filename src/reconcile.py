import pandas as pd
from pathlib import Path


def load_inputs(base_path):
    """Đọc cleaned_retail.csv, customer_segments.csv, cancelled_retail.csv."""
    proc = Path(base_path) / 'data' / 'processed' 
    cr1 = pd.read_csv(proc / 'cleaned_retail.csv', dtype={"InvoiceNo": str})
    cs = pd.read_csv(proc / 'customer_segments.csv', dtype={"CustomerID": str})
    cr2 = pd.read_csv(proc / 'cancelled_retail.csv', dtype={"InvoiceNo": str})
    return cr1, cs, cr2


def revenue_totals(df):
    """Tổng Revenue, non-Guest, Guest."""
    from eda import total_revenue
    return (total_revenue(df),
            df[df['CustomerID'] != 'Guest']['Revenue'].sum(),
            df[df['CustomerID'] == 'Guest']['Revenue'].sum())


def rfm_monetary_total(seg):
    """Tổng Monetary từ customer_segments.csv."""
    return seg['Monetary'].sum()


def data_quality_counts(df, cancelled):
    """Đếm duplicate, invalid, cancelled để đối chiếu audit."""
    return (df.duplicated().sum(),
            df[(df['Quantity'] <= 0) | (df['UnitPrice'] <= 0)].shape[0],
            cancelled.shape[0])


def revenue_by_segment(df, seg, output_path):
    """Join Segment vào transaction, tính Revenue theo segment, lưu CSV."""
    merged = df.merge(seg[['CustomerID', 'Segment']], on='CustomerID', how='left')
    merged.groupby('Segment')['Revenue'].sum().to_csv(output_path)
    return merged


def main():
    base_path = str(Path(__file__).resolve().parents[1])
    cr1, cs, cr2 = load_inputs(base_path)
    print("Revenue totals (total, non-Guest, Guest):", revenue_totals(cr1))
    print("RFM Monetary total:", rfm_monetary_total(cs))
    print("Quality counts (dup, invalid, cancelled):", data_quality_counts(cr1, cr2))
    output_path = (
    Path(base_path)
        / 'data'
        / 'processed'
        / 'revenue_by_segment.csv'
    )

    revenue_by_segment(
        cr1,
        cs,
        output_path
    )
    print("Saved revenue_by_segment.csv")


if __name__ == '__main__':
    main()
