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
            raise ValueError("DataFrame is empty or not loaded.")

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

        print("\n=== DATA CLEANING AUDIT REPORT ===")

        print(
            f"1. Initial row count:                 "
            f"{initial_rows:,}"
        )

        print(
            f"2. Duplicate rows:                    "
            f"{dup_rows:,} "
            f"(Variance Qty: "
            f"{self.audit_stats['qty_diff_dedup']:,.0f}, "
            f"Rev: £{self.audit_stats['rev_diff_dedup']:,.2f})"
        )

        print(
            f"3. Rows after deduplication:          "
            f"{after_dedup_rows:,}"
        )

        print(
            f"4. Missing/invalid core field rows:   "
            f"{invalid_core_rows:,}"
        )

        print(
            f"5. Cancelled invoice rows (Prefix C): "
            f"{cancelled_rows:,}"
        )

        print(
            f"6. Quantity/UnitPrice <= 0 invalid:   "
            f"{invalid_qty_price_rows:,}"
        )

        print(
            f"7. Valid sales transactions retained: "
            f"{len(self.df_valid):,} "
            f"(Including missing CustomerID / Guest: "
            f"{missing_cust_count:,})"
        )

    def engineer_features(self):
        if self.df_valid is None:
            raise ValueError(
                "clean_data() must be executed before feature engineering."
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
            f"-> Total valid sales revenue after cleaning: "
            f"£{self.df_valid['Revenue'].sum():,.2f}"
        )

    def analyze_revenue(self):
        """Analyze revenue metrics."""
        try:
            from src.eda import total_revenue, revenue_by_month, revenue_by_country, top_products
        except ImportError:
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

class TikiDataProcessor(RetailDataProcessor):
    """Normalize harvested Tiki reviews into the project's canonical retail schema.

    One verified-purchase review (``purchased == True``) becomes one canonical
    transaction row.  The class intentionally keeps Tiki as a separate dataset;
    it does not join Tiki rows into the UCI Online Retail dataset.
    """

    CANONICAL_COLUMNS = [
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

    def __init__(self, raw_data_path: str | Path = 'data/raw/tiki'):
        super().__init__(raw_data_path)
        self.raw_dir = Path(raw_data_path)
        self.products_df: pd.DataFrame | None = None
        self.reviews_df: pd.DataFrame | None = None

    @staticmethod
    def _normalise_id(value) -> str | None:
        """Return a stable string identifier without a trailing ``.0``."""
        if pd.isna(value):
            return None

        text = str(value).strip()
        if not text or text.lower() in {'nan', 'none', '<na>'}:
            return None

        try:
            number = float(text)
            if number.is_integer():
                return str(int(number))
        except (TypeError, ValueError, OverflowError):
            pass

        return text

    @staticmethod
    def _coerce_purchased(value) -> bool:
        """Interpret Tiki's purchased flag consistently for JSON/CSV inputs."""
        if isinstance(value, bool):
            return value
        if pd.isna(value):
            return False
        if isinstance(value, (int, float)):
            return value == 1
        return str(value).strip().casefold() in {
            'true', '1', 'yes', 'y', 'verified', 'purchased'
        }

    @staticmethod
    def _unix_or_datetime(series: pd.Series) -> pd.Series:
        """Parse Unix-second timestamps while remaining tolerant of datetime text."""
        numeric = pd.to_numeric(series, errors='coerce')
        parsed_numeric = pd.to_datetime(
            numeric,
            unit='s',
            errors='coerce',
            utc=True,
        ).dt.tz_convert(None)

        parsed_text = pd.to_datetime(
            series.where(numeric.isna()),
            errors='coerce',
            utc=True,
        ).dt.tz_convert(None)

        return parsed_numeric.fillna(parsed_text)

    def _load_products(self) -> pd.DataFrame:
        json_path = self.raw_dir / 'all_products.json'
        csv_path = self.raw_dir / 'raw_tiki_products.csv'

        if json_path.exists():
            import json

            with json_path.open('r', encoding='utf-8') as handle:
                raw_products = json.load(handle)

            records = []
            for item in raw_products:
                if not isinstance(item, dict):
                    continue
                records.append({
                    'id': item.get('id'),
                    'name': item.get('name'),
                    'price': item.get('price'),
                })
            return pd.DataFrame(records)

        if csv_path.exists():
            return pd.read_csv(csv_path)

        raise FileNotFoundError(
            'Tiki product source not found. Expected '
            f'{json_path} or {csv_path}.'
        )

    def _load_reviews(self) -> pd.DataFrame:
        json_path = self.raw_dir / 'all_reviews.json'
        csv_path = self.raw_dir / 'raw_tiki_reviews.csv'

        if json_path.exists():
            import json

            with json_path.open('r', encoding='utf-8') as handle:
                raw_reviews = json.load(handle)

            records = []
            for item in raw_reviews:
                if not isinstance(item, dict):
                    continue

                created_by = item.get('created_by') or {}
                purchased = (
                    item.get('purchased')
                    if 'purchased' in item
                    else created_by.get('purchased', False)
                )

                records.append({
                    'id': item.get('id'),
                    'product_id': item.get('product_id'),
                    'customer_id': (
                        item.get('customer_id')
                        if item.get('customer_id') is not None
                        else created_by.get('id')
                    ),
                    'purchased': purchased,
                    'created_at': item.get('created_at'),
                })
            return pd.DataFrame(records)

        if csv_path.exists():
            return pd.read_csv(csv_path)

        raise FileNotFoundError(
            'Tiki review source not found. Expected '
            f'{json_path} or {csv_path}.'
        )

    def load_data(self) -> pd.DataFrame:
        """Load Tiki products/reviews and create the pre-cleaning joined frame."""
        self.products_df = self._load_products()
        self.reviews_df = self._load_reviews()

        required_products = {'id', 'name', 'price'}
        required_reviews = {
            'id', 'product_id', 'customer_id', 'purchased', 'created_at'
        }

        missing_products = required_products.difference(self.products_df.columns)
        missing_reviews = required_reviews.difference(self.reviews_df.columns)

        if missing_products:
            raise ValueError(
                'Tiki products data is missing columns: '
                + ', '.join(sorted(missing_products))
            )
        if missing_reviews:
            raise ValueError(
                'Tiki reviews data is missing columns: '
                + ', '.join(sorted(missing_reviews))
            )

        products = self.products_df.copy()
        reviews = self.reviews_df.copy()

        products['_product_key'] = products['id'].map(self._normalise_id)
        reviews['_product_key'] = reviews['product_id'].map(self._normalise_id)

        # Product ID is the logical catalogue key. Keeping the first row avoids
        # multiplying review rows when a raw catalogue cache contains duplicates.
        products = products.drop_duplicates(
            subset=['_product_key'],
            keep='first',
        )

        self.df = reviews.merge(
            products[['_product_key', 'name', 'price']],
            on='_product_key',
            how='left',
            validate='many_to_one',
        )

        return self.df

    def clean_data(self, deduplicate: bool = True, fill_guest: bool = True):
        """Map verified Tiki reviews into the canonical transaction schema."""
        if self.df is None or self.df.empty:
            raise ValueError('Tiki data is empty or not loaded. Call load_data() first.')

        source = self.df.copy()
        initial_rows = len(source)

        purchased_mask = source['purchased'].map(self._coerce_purchased)
        verified = source[purchased_mask].copy()
        unverified_rows = int((~purchased_mask).sum())

        canonical = pd.DataFrame(index=verified.index)
        review_ids = verified['id'].map(self._normalise_id)
        product_ids = verified['product_id'].map(self._normalise_id)

        canonical['InvoiceNo'] = review_ids.map(
            lambda value: f'TIKI_REV_{value}' if value is not None else pd.NA
        ).astype('string')
        canonical['StockCode'] = pd.Series(
            product_ids,
            index=verified.index,
            dtype='string',
        )
        canonical['Description'] = (
            verified['name']
            .fillna('Unknown')
            .astype('string')
            .str.strip()
            .replace('', 'Unknown')
        )
        canonical['Quantity'] = 1
        canonical['InvoiceDate'] = self._unix_or_datetime(verified['created_at'])
        canonical['UnitPrice'] = pd.to_numeric(
            verified['price'],
            errors='coerce',
        )

        customer_ids = verified['customer_id'].map(self._normalise_id)
        if fill_guest:
            canonical['CustomerID'] = pd.Series(
                customer_ids,
                index=verified.index,
                dtype='string',
            ).fillna('Guest')
        else:
            canonical['CustomerID'] = pd.Series(
                customer_ids,
                index=verified.index,
                dtype='string',
            )

        canonical['Country'] = 'Vietnam'

        temp_revenue_before = (
            canonical['Quantity']
            * canonical['UnitPrice'].fillna(0)
        ).sum()
        temp_quantity_before = canonical['Quantity'].sum()

        dup_mask = canonical.duplicated(keep='first')
        duplicate_rows = int(dup_mask.sum())

        if deduplicate:
            canonical = canonical[~dup_mask].copy()

        after_dedup_rows = len(canonical)
        temp_revenue_after = (
            canonical['Quantity']
            * canonical['UnitPrice'].fillna(0)
        ).sum()
        temp_quantity_after = canonical['Quantity'].sum()

        missing_invoice_mask = canonical['InvoiceNo'].isna()
        missing_stock_mask = canonical['StockCode'].isna()
        invalid_date_mask = canonical['InvoiceDate'].isna()
        invalid_price_mask = canonical['UnitPrice'].isna()

        invalid_core_mask = (
            missing_invoice_mask
            | missing_stock_mask
            | invalid_date_mask
            | invalid_price_mask
        )

        non_positive_price_mask = canonical['UnitPrice'].fillna(0) <= 0
        invalid_sales_mask = invalid_core_mask | non_positive_price_mask

        # Tiki review data has no UCI-style cancellation code.  Keep an empty
        # canonical frame for API compatibility instead of mislabelling
        # unverified reviews or invalid catalogue rows as cancellations.
        self.df_cancelled = pd.DataFrame(
            columns=self.CANONICAL_COLUMNS
        )

        self.df_valid = canonical[~invalid_sales_mask].copy()

        self.audit_stats = {
            'initial_rows': initial_rows,
            'verified_purchase_rows': len(verified),
            'unverified_review_rows': unverified_rows,
            'duplicate_rows': duplicate_rows,
            'deduplication_applied': deduplicate,
            'after_dedup_rows': after_dedup_rows,
            'qty_diff_dedup': float(
                temp_quantity_before - temp_quantity_after
            ),
            'rev_diff_dedup': float(
                temp_revenue_before - temp_revenue_after
            ),
            'missing_invoice_rows': int(missing_invoice_mask.sum()),
            'missing_stock_code_rows': int(missing_stock_mask.sum()),
            'invalid_invoice_date_rows': int(invalid_date_mask.sum()),
            'invalid_unit_price_rows': int(invalid_price_mask.sum()),
            'non_positive_price_rows': int(non_positive_price_mask.sum()),
            'invalid_core_rows': int(invalid_core_mask.sum()),
            'valid_rows': len(self.df_valid),
            'guest_rows': int(
                self.df_valid['CustomerID'].eq('Guest').sum()
            ) if 'CustomerID' in self.df_valid else 0,
        }

    def engineer_features(self):
        """Create canonical Revenue and YearMonth features."""
        if self.df_valid is None:
            raise ValueError(
                'clean_data() must be executed before feature engineering.'
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

        self.df_valid = self.df_valid[self.CANONICAL_COLUMNS].copy()
        self.df_cancelled = self.df_cancelled.reindex(
            columns=self.CANONICAL_COLUMNS
        )

    def export_data(
        self,
        clean_path: str | Path = 'data/processed/cleaned_tiki.csv',
        cancelled_path: str | Path = 'data/processed/cancelled_tiki.csv',
    ):
        """Export canonical Tiki outputs without mixing them into UCI files."""
        if self.df_valid is None:
            raise ValueError(
                'clean_data() and engineer_features() must run before export.'
            )
        if 'Revenue' not in self.df_valid.columns:
            raise ValueError(
                'engineer_features() must be executed before export_data().'
            )

        clean_path = Path(clean_path)
        cancelled_path = Path(cancelled_path)
        clean_path.parent.mkdir(parents=True, exist_ok=True)
        cancelled_path.parent.mkdir(parents=True, exist_ok=True)

        self.df_valid.to_csv(clean_path, index=False)
        self.df_cancelled.to_csv(cancelled_path, index=False)
