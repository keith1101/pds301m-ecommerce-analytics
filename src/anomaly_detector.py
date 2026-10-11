from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


class OrderAnomalyDetector:
    def __init__(
        self,
        cleaned_data_path: str | Path = None,
        cancelled_data_path: str | Path = None,
        df_valid: pd.DataFrame = None,
        df_cancelled: pd.DataFrame = None
    ):
        self.df = (
            df_valid
            if df_valid is not None
            else pd.read_csv(
                cleaned_data_path,
                dtype={
                    'InvoiceNo': str,
                    'CustomerID': str
                }
            )
        )

        if df_cancelled is not None:
            self.df_cancelled = df_cancelled

        elif (
            cancelled_data_path
            and Path(cancelled_data_path).exists()
        ):
            self.df_cancelled = pd.read_csv(
                cancelled_data_path,
                dtype={'InvoiceNo': str}
            )

        else:
            self.df_cancelled = pd.DataFrame()

        self.order_stats = None
        self.metrics = {}

    def analyze_cancelled_orders(self) -> dict:
        print(
            "\n=== 1. THỐNG KÊ HÓA ĐƠN HỦY/HOÀN TRẢ ==="
        )

        if self.df_cancelled.empty:
            stats = {
                'cancelled_invoices': 0,
                'cancelled_lines': 0,
                'total_returned_qty': 0
            }

            print("- Không có dữ liệu hóa đơn hủy.")

            return stats

        num_invoices = int(
            self.df_cancelled['InvoiceNo'].nunique()
        )

        num_lines = int(
            len(self.df_cancelled)
        )

        total_returned_qty = int(
            self.df_cancelled['Quantity']
            .abs()
            .sum()
        )

        stats = {
            'cancelled_invoices': num_invoices,
            'cancelled_lines': num_lines,
            'total_returned_qty': total_returned_qty
        }

        print(
            f"- Số hóa đơn hủy duy nhất:          "
            f"{num_invoices:,}"
        )

        print(
            f"- Số dòng giao dịch hủy:            "
            f"{num_lines:,}"
        )

        print(
            f"- Tổng số lượng sản phẩm hoàn trả:  "
            f"{total_returned_qty:,}"
        )

        return stats

    def aggregate_orders(self) -> pd.DataFrame:
        if self.df.empty:
            self.order_stats = pd.DataFrame(
                columns=[
                    'InvoiceNo',
                    'Revenue',
                    'TotalQuantity',
                    'LineCount'
                ]
            )

            return self.order_stats

        self.order_stats = (
            self.df
            .groupby(
                'InvoiceNo',
                as_index=False
            )
            .agg(
                Revenue=('Revenue', 'sum'),
                TotalQuantity=('Quantity', 'sum'),
                LineCount=('StockCode', 'count')
            )
        )

        return self.order_stats

    @staticmethod
    def _calc_iqr_bounds(
        series: pd.Series
    ) -> tuple[float, float, float, float]:

        if series.empty:
            return 0.0, 0.0, 0.0, 0.0

        q1 = float(
            series.quantile(0.25)
        )

        q3 = float(
            series.quantile(0.75)
        )

        iqr = q3 - q1

        upper_bound = (
            q3 + 1.5 * iqr
        )

        return (
            q1,
            q3,
            iqr,
            upper_bound
        )

    def detect_iqr_anomalies(
        self,
        output_csv_path: str | Path = None
    ) -> pd.DataFrame:

        if self.order_stats is None:
            self.aggregate_orders()

        if self.order_stats.empty:
            self.order_stats[
                'IsRevenueAnomaly'
            ] = pd.Series(dtype=bool)

            self.order_stats[
                'IsQuantityAnomaly'
            ] = pd.Series(dtype=bool)

            self.order_stats[
                'IsAnomaly'
            ] = pd.Series(dtype=bool)

            if output_csv_path:
                out_path = Path(
                    output_csv_path
                )

                out_path.parent.mkdir(
                    parents=True,
                    exist_ok=True
                )

                self.order_stats.to_csv(
                    out_path,
                    index=False
                )

            return self.order_stats

        (
            q1_rev,
            q3_rev,
            iqr_rev,
            ub_rev
        ) = self._calc_iqr_bounds(
            self.order_stats['Revenue']
        )

        (
            q1_qty,
            q3_qty,
            iqr_qty,
            ub_qty
        ) = self._calc_iqr_bounds(
            self.order_stats[
                'TotalQuantity'
            ]
        )

        self.order_stats[
            'IsRevenueAnomaly'
        ] = (
            self.order_stats['Revenue']
            > ub_rev
        )

        self.order_stats[
            'IsQuantityAnomaly'
        ] = (
            self.order_stats['TotalQuantity']
            > ub_qty
        )

        self.order_stats[
            'IsAnomaly'
        ] = (
            self.order_stats[
                'IsRevenueAnomaly'
            ]
            |
            self.order_stats[
                'IsQuantityAnomaly'
            ]
        )

        self.metrics.update({
            'q1_rev': q1_rev,
            'q3_rev': q3_rev,
            'iqr_rev': iqr_rev,
            'ub_rev': ub_rev,

            'q1_qty': q1_qty,
            'q3_qty': q3_qty,
            'iqr_qty': iqr_qty,
            'ub_qty': ub_qty
        })

        print(
            "\n=== 2. PHÁT HIỆN NGOẠI LỆ GIÁ TRỊ CAO "
            "(UPPER-TAIL IQR) ==="
        )

        print(
            f"- Doanh thu (Revenue): "
            f"Q1=£{q1_rev:,.2f}, "
            f"Q3=£{q3_rev:,.2f}, "
            f"IQR=£{iqr_rev:,.2f} "
            f"-> Ngưỡng Q3 + 1.5*IQR "
            f"= £{ub_rev:,.2f}"
        )

        print(
            f"- Số lượng (Quantity): "
            f"Q1={q1_qty:,.1f}, "
            f"Q3={q3_qty:,.1f}, "
            f"IQR={iqr_qty:,.1f} "
            f"-> Ngưỡng Q3 + 1.5*IQR "
            f"= {ub_qty:,.1f}"
        )

        print(
            f"- Số đơn ngoại lệ theo Revenue:     "
            f"{int(self.order_stats['IsRevenueAnomaly'].sum()):,}"
        )

        print(
            f"- Số đơn ngoại lệ theo Quantity:    "
            f"{int(self.order_stats['IsQuantityAnomaly'].sum()):,}"
        )

        print(
            f"- Số đơn ngoại lệ Combined:         "
            f"{int(self.order_stats['IsAnomaly'].sum()):,}"
        )

        if output_csv_path:
            out_path = Path(
                output_csv_path
            )

            out_path.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            anomalies = (
                self.order_stats[
                    self.order_stats[
                        'IsAnomaly'
                    ]
                ]
                .sort_values(
                    by='Revenue',
                    ascending=False
                )
            )

            anomalies.to_csv(
                out_path,
                index=False
            )

        return self.order_stats

    def _build_impact_summary(
        self,
        flag_column: str
    ) -> dict:

        total_orders = len(
            self.order_stats
        )

        total_revenue = float(
            self.order_stats[
                'Revenue'
            ].sum()
        )

        flagged = (
            self.order_stats[
                flag_column
            ]
            .fillna(False)
            .astype(bool)
        )

        anomaly_orders = int(
            flagged.sum()
        )

        anomaly_revenue = float(
            self.order_stats.loc[
                flagged,
                'Revenue'
            ].sum()
        )

        normal_revenue = (
            total_revenue
            - anomaly_revenue
        )

        order_ratio = (
            anomaly_orders
            / total_orders
            * 100
            if total_orders > 0
            else 0.0
        )

        revenue_ratio = (
            anomaly_revenue
            / total_revenue
            * 100
            if total_revenue > 0
            else 0.0
        )

        return {
            'anomaly_orders':
                anomaly_orders,

            'total_orders':
                total_orders,

            'order_ratio':
                order_ratio,

            'anomaly_revenue':
                anomaly_revenue,

            'normal_revenue':
                normal_revenue,

            'revenue_ratio':
                revenue_ratio
        }

    def evaluate_business_impact(
        self
    ) -> dict:

        if self.order_stats is None:
            self.aggregate_orders()

        if self.order_stats.empty:
            empty_summary = {
                'anomaly_orders': 0,
                'total_orders': 0,
                'order_ratio': 0.0,
                'anomaly_revenue': 0.0,
                'normal_revenue': 0.0,
                'revenue_ratio': 0.0
            }

            return {
                'total_revenue': 0.0,
                'normal_revenue': 0.0,
                'anomaly_revenue': 0.0,
                'impact_ratio': 0.0,
                'order_ratio': 0.0,

                'revenue':
                    empty_summary.copy(),

                'quantity':
                    empty_summary.copy(),

                'combined':
                    empty_summary.copy()
            }

        required_flags = {
            'IsRevenueAnomaly',
            'IsQuantityAnomaly',
            'IsAnomaly'
        }

        if not required_flags.issubset(
            self.order_stats.columns
        ):
            self.detect_iqr_anomalies()

        total_revenue = float(
            self.order_stats[
                'Revenue'
            ].sum()
        )

        revenue_impact = (
            self._build_impact_summary(
                'IsRevenueAnomaly'
            )
        )

        quantity_impact = (
            self._build_impact_summary(
                'IsQuantityAnomaly'
            )
        )

        combined_impact = (
            self._build_impact_summary(
                'IsAnomaly'
            )
        )

        print(
            "\n=== 3. TÁC ĐỘNG BUSINESS "
            "CỦA ANOMALY ==="
        )

        print(
            f"- Tổng doanh thu: "
            f"£{total_revenue:,.2f}"
        )

        print(
            "- Revenue anomaly: "
            f"{revenue_impact['anomaly_orders']:,} đơn, "
            f"£{revenue_impact['anomaly_revenue']:,.2f} "
            f"({revenue_impact['revenue_ratio']:.2f}% revenue)"
        )

        print(
            "- Quantity anomaly: "
            f"{quantity_impact['anomaly_orders']:,} đơn, "
            f"£{quantity_impact['anomaly_revenue']:,.2f} "
            f"({quantity_impact['revenue_ratio']:.2f}% revenue)"
        )

        print(
            "- Combined anomaly: "
            f"{combined_impact['anomaly_orders']:,} đơn, "
            f"£{combined_impact['anomaly_revenue']:,.2f} "
            f"({combined_impact['revenue_ratio']:.2f}% revenue)"
        )

        print(
            "- Nhận xét: Các đơn vượt ngưỡng IQR "
            "được gắn cờ để review; không tự động "
            "xóa chỉ vì có Revenue hoặc Quantity lớn."
        )

        return {
            'total_revenue':
                total_revenue,

            'normal_revenue':
                combined_impact[
                    'normal_revenue'
                ],

            'anomaly_revenue':
                combined_impact[
                    'anomaly_revenue'
                ],

            'impact_ratio':
                combined_impact[
                    'revenue_ratio'
                ],

            'order_ratio':
                combined_impact[
                    'order_ratio'
                ],

            'revenue':
                revenue_impact,

            'quantity':
                quantity_impact,

            'combined':
                combined_impact
        }

    def visualize_distribution(
        self,
        output_img_path: str | Path
    ):
        if (
            self.order_stats is None
            or self.order_stats.empty
        ):
            return

        out_path = Path(
            output_img_path
        )

        out_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        plt.figure(
            figsize=(12, 4)
        )

        sns.boxplot(
            x=self.order_stats[
                'Revenue'
            ],
            color='#3498db'
        )

        plt.axvline(
            self.metrics.get(
                'ub_rev',
                0
            ),
            color='r',
            linestyle='--',
            label=(
                f"Upper Bound "
                f"(£{self.metrics.get('ub_rev', 0):,.2f})"
            )
        )

        plt.title(
            'Order Revenue Distribution '
            '(Valid Sales Orders)'
        )

        plt.xlabel(
            'Order Revenue (£)'
        )

        plt.legend()
        plt.tight_layout()

        plt.savefig(
            out_path,
            dpi=300
        )

        plt.close()