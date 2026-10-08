from pathlib import Path
import pandas as pd


class RetailDataProcessor:
    def __init__(self, raw_data_path: str | Path):
        self.raw_path = Path(raw_data_path)
        self.df = None
        self.df_cancelled = None
        self.df_valid = None
        self.audit_stats = {}

    def load_and_explore(self) -> pd.DataFrame:
        self.df = pd.read_excel(self.raw_path)
        return self.df

    def clean_data(self, deduplicate: bool = True, fill_guest: bool = True):
        if self.df is None or self.df.empty:
            raise ValueError("Dataframe rỗng hoặc chưa được tải.")

        df_work = self.df.copy()
        initial_rows = len(df_work)

        df_work['InvoiceNo'] = df_work['InvoiceNo'].astype('string').str.strip()
        df_work['InvoiceDate'] = pd.to_datetime(
            df_work['InvoiceDate'],
            errors='coerce'
        )
        df_work['Quantity'] = pd.to_numeric(
            df_work['Quantity'],
            errors='coerce'
        )
        df_work['UnitPrice'] = pd.to_numeric(
            df_work['UnitPrice'],
            errors='coerce'
        )

        temp_rev_before = (
            df_work['Quantity'].fillna(0)
            * df_work['UnitPrice'].fillna(0)
        ).sum()

        temp_qty_before = df_work['Quantity'].fillna(0).sum()

        dup_mask = df_work.duplicated(keep='first')
        dup_rows = int(dup_mask.sum())

        if deduplicate:
            df_work = df_work[~dup_mask].copy()

        after_dedup_rows = len(df_work)

        temp_rev_after = (
            df_work['Quantity'].fillna(0)
            * df_work['UnitPrice'].fillna(0)
        ).sum()

        temp_qty_after = df_work['Quantity'].fillna(0).sum()

        invoice_placeholder_mask = (
            df_work['InvoiceNo']
            .fillna('')
            .str.lower()
            .isin({'', 'nan', 'none', '<na>'})
        )

        missing_invoice_mask = (
            df_work['InvoiceNo'].isna()
            | invoice_placeholder_mask
        )

        invalid_invoice_date_mask = df_work['InvoiceDate'].isna()
        invalid_quantity_mask = df_work['Quantity'].isna()
        invalid_unit_price_mask = df_work['UnitPrice'].isna()

        invalid_core_mask = (
            missing_invoice_mask
            | invalid_invoice_date_mask
            | invalid_quantity_mask
            | invalid_unit_price_mask
        )

        invalid_core_rows = int(invalid_core_mask.sum())

        df_work = df_work[~invalid_core_mask].copy()

        is_cancelled = (
            df_work['InvoiceNo']
            .str.upper()
            .str.startswith('C', na=False)
        )

        self.df_cancelled = df_work[is_cancelled].copy()
        cancelled_rows = len(self.df_cancelled)

        df_non_cancelled = df_work[~is_cancelled].copy()

        invalid_qty_price_mask = (
            (df_non_cancelled['Quantity'] <= 0)
            | (df_non_cancelled['UnitPrice'] <= 0)
        )

        invalid_qty_price_rows = int(
            invalid_qty_price_mask.sum()
        )

        self.df_valid = df_non_cancelled[
            ~invalid_qty_price_mask
        ].copy()

        missing_cust_count = int(
            self.df_valid['CustomerID'].isna().sum()
        )

        if fill_guest:
            self.df_valid['CustomerID'] = (
                self.df_valid['CustomerID'].apply(
                    lambda x: (
                        'Guest'
                        if pd.isna(x)
                        else str(int(float(x)))
                        if str(x).replace('.', '', 1).isdigit()
                        else str(x)
                    )
                )
            )

        self.df_valid['Description'] = (
            self.df_valid['Description']
            .fillna('Unknown')
            .astype(str)
            .str.strip()
        )

        self.audit_stats = {
            'initial_rows': initial_rows,
            'duplicate_rows': dup_rows,
            'deduplication_applied': deduplicate,
            'after_dedup_rows': after_dedup_rows,
            'qty_diff_dedup': float(
                temp_qty_before - temp_qty_after
            ),
            'rev_diff_dedup': float(
                temp_rev_before - temp_rev_after
            ),
            'missing_invoice_rows': int(
                missing_invoice_mask.sum()
            ),
            'invalid_invoice_date_rows': int(
                invalid_invoice_date_mask.sum()
            ),
            'invalid_quantity_rows': int(
                invalid_quantity_mask.sum()
            ),
            'invalid_unit_price_rows': int(
                invalid_unit_price_mask.sum()
            ),
            'missing_core_rows': invalid_core_rows,
            'cancelled_rows': cancelled_rows,
            'invalid_qty_price_rows': invalid_qty_price_rows,
            'valid_rows': len(self.df_valid),
            'missing_customer_id_valid': missing_cust_count
        }

        print("\n=== BÁO CÁO AUDIT LÀM SẠCH DỮ LIỆU ===")

        print(
            f"1. Số dòng ban đầu:                 "
            f"{initial_rows:,}"
        )

        print(
            f"2. Số dòng trùng lặp (Duplicate):   "
            f"{dup_rows:,} "
            f"(Chênh lệch Qty: "
            f"{self.audit_stats['qty_diff_dedup']:,.0f}, "
            f"Rev: £{self.audit_stats['rev_diff_dedup']:,.2f})"
        )

        print(
            f"3. Số dòng sau khi xử lý Duplicate: "
            f"{after_dedup_rows:,}"
        )

        print(
            f"4. Lỗi thiếu/không hợp lệ trường cốt lõi: "
            f"{invalid_core_rows:,}"
        )

        print(
            f"5. Số dòng hóa đơn hủy (Prefix C):  "
            f"{cancelled_rows:,}"
        )

        print(
            f"6. Lỗi Quantity/UnitPrice <= 0:     "
            f"{invalid_qty_price_rows:,}"
        )

        print(
            f"7. Giao dịch bán hợp lệ giữ lại:    "
            f"{len(self.df_valid):,} "
            f"(Trong đó thiếu CustomerID: "
            f"{missing_cust_count:,})"
        )

    def engineer_features(self):
        if self.df_valid is None:
            raise ValueError(
                "Cần chạy clean_data() trước khi tạo đặc trưng."
            )

        self.df_valid['Revenue'] = (
            self.df_valid['Quantity']
            * self.df_valid['UnitPrice']
        )

        self.df_valid['YearMonth'] = (
            self.df_valid['InvoiceDate']
            .dt.to_period('M')
            .astype(str)
        )

        print(
            f"-> Tổng Revenue hợp lệ sau làm sạch: "
            f"£{self.df_valid['Revenue'].sum():,.2f}"
        )

    def analyze_revenue(self):
        """Phân tích doanh thu"""
        from eda import total_revenue, revenue_by_month, revenue_by_country, top_products
        return {
            'total': total_revenue(self.df_valid),
            'by_month': revenue_by_month(self.df_valid),
            'by_country': revenue_by_country(self.df_valid),
            'top_products': top_products(self.df_valid),
        }


    def export_data(
        self,
        clean_path: str | Path,
        cancelled_path: str | Path
    ):
        clean_path = Path(clean_path)
        cancelled_path = Path(cancelled_path)

        clean_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        cancelled_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.df_valid.to_csv(
            clean_path,
            index=False
        )

        self.df_cancelled.to_csv(
            cancelled_path,
            index=False
        )