from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


class OrderAnomalyDetector:
    def __init__(self, cleaned_data_path: str | Path = None, cancelled_data_path: str | Path = None,
                 df_valid: pd.DataFrame = None, df_cancelled: pd.DataFrame = None):
        self.df = df_valid if df_valid is not None else pd.read_csv(cleaned_data_path, dtype={'InvoiceNo': str, 'CustomerID': str})
        if df_cancelled is not None:
            self.df_cancelled = df_cancelled
        elif cancelled_data_path and Path(cancelled_data_path).exists():
            self.df_cancelled = pd.read_csv(cancelled_data_path, dtype={'InvoiceNo': str})
        else:
            self.df_cancelled = pd.DataFrame()

        self.order_stats = None
        self.metrics = {}

    def analyze_cancelled_orders(self) -> dict:
        print("\n=== 1. THỐNG KÊ HÓA ĐƠN HỦY/HOÀN TRẢ ===")
        if self.df_cancelled.empty:
            stats = {'cancelled_invoices': 0, 'cancelled_lines': 0, 'total_returned_qty': 0}
            print("- Không có dữ liệu hóa đơn hủy.")
            return stats

        num_invoices = int(self.df_cancelled['InvoiceNo'].nunique())
        num_lines = int(len(self.df_cancelled))
        total_returned_qty = int(self.df_cancelled['Quantity'].abs().sum())

        stats = {
            'cancelled_invoices': num_invoices,
            'cancelled_lines': num_lines,
            'total_returned_qty': total_returned_qty
        }
        print(f"- Số hóa đơn hủy duy nhất:          {num_invoices:,}")
        print(f"- Số dòng giao dịch hủy:            {num_lines:,}")
        print(f"- Tổng số lượng sản phẩm hoàn trả:  {total_returned_qty:,}")
        return stats

    def aggregate_orders(self) -> pd.DataFrame:
        if self.df.empty:
            self.order_stats = pd.DataFrame(columns=['InvoiceNo', 'Revenue', 'TotalQuantity', 'LineCount'])
            return self.order_stats

        self.order_stats = self.df.groupby('InvoiceNo', as_index=False).agg(
            Revenue=('Revenue', 'sum'),
            TotalQuantity=('Quantity', 'sum'),
            LineCount=('StockCode', 'count')
        )
        return self.order_stats

    @staticmethod
    def _calc_iqr_bounds(series: pd.Series) -> tuple[float, float, float, float]:
        if series.empty:
            return 0.0, 0.0, 0.0, 0.0
        q1 = float(series.quantile(0.25))
        q3 = float(series.quantile(0.75))
        iqr = q3 - q1
        upper_bound = q3 + 1.5 * iqr
        return q1, q3, iqr, upper_bound

    def detect_iqr_anomalies(self, output_csv_path: str | Path = None) -> pd.DataFrame:
        if self.order_stats is None:
            self.aggregate_orders()

        if self.order_stats.empty:
            self.order_stats['IsRevenueAnomaly'] = pd.Series(dtype=bool)
            self.order_stats['IsQuantityAnomaly'] = pd.Series(dtype=bool)
            self.order_stats['IsAnomaly'] = pd.Series(dtype=bool)
            return self.order_stats

        q1_rev, q3_rev, iqr_rev, ub_rev = self._calc_iqr_bounds(self.order_stats['Revenue'])
        q1_qty, q3_qty, iqr_qty, ub_qty = self._calc_iqr_bounds(self.order_stats['TotalQuantity'])

        self.order_stats['IsRevenueAnomaly'] = (self.order_stats['Revenue'] > ub_rev) if iqr_rev >= 0 else False
        self.order_stats['IsQuantityAnomaly'] = (self.order_stats['TotalQuantity'] > ub_qty) if iqr_qty >= 0 else False
        self.order_stats['IsAnomaly'] = self.order_stats['IsRevenueAnomaly']

        self.metrics.update({
            'q1_rev': q1_rev, 'q3_rev': q3_rev, 'iqr_rev': iqr_rev, 'ub_rev': ub_rev,
            'q1_qty': q1_qty, 'q3_qty': q3_qty, 'iqr_qty': iqr_qty, 'ub_qty': ub_qty
        })

        print("\n=== 2. PHÁT HIỆN NGOẠI LỆ GIÁ TRỊ CAO (UPPER-TAIL IQR) ===")
        print(f"- Doanh thu (Revenue): Q1=£{q1_rev:,.2f}, Q3=£{q3_rev:,.2f}, IQR=£{iqr_rev:,.2f} -> Ngưỡng Q3 + 1.5*IQR = £{ub_rev:,.2f}")
        print(f"- Số lượng (Quantity): Q1={q1_qty:,.1f}, Q3={q3_qty:,.1f}, IQR={iqr_qty:,.1f} -> Ngưỡng Q3 + 1.5*IQR = {ub_qty:,.1f}")
        print(f"- Số đơn ngoại lệ theo Revenue:     {int(self.order_stats['IsRevenueAnomaly'].sum()):,}")
        print(f"- Số đơn ngoại lệ theo Quantity:    {int(self.order_stats['IsQuantityAnomaly'].sum()):,}")

        if output_csv_path:
            out_path = Path(output_csv_path)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            anomalies = self.order_stats[self.order_stats['IsRevenueAnomaly'] | self.order_stats['IsQuantityAnomaly']].sort_values(by='Revenue', ascending=False)
            anomalies.to_csv(out_path, index=False)

        return self.order_stats

    def evaluate_business_impact(self) -> dict:
        if self.order_stats is None or self.order_stats.empty:
            return {'total_revenue': 0.0, 'normal_revenue': 0.0, 'anomaly_revenue': 0.0, 'impact_ratio': 0.0}

        total_rev = float(self.order_stats['Revenue'].sum())
        normal_rev = float(self.order_stats[~self.order_stats['IsRevenueAnomaly']]['Revenue'].sum())
        anomaly_rev = total_rev - normal_rev
        total_orders = len(self.order_stats)
        anomaly_orders = int(self.order_stats['IsRevenueAnomaly'].sum())

        order_ratio = (anomaly_orders / total_orders * 100) if total_orders > 0 else 0.0
        impact_ratio = (anomaly_rev / total_rev * 100) if total_rev > 0 else 0.0

        print("\n=== 3. TÁC ĐỘNG DOANH THU & NHẬN XÉT ===")
        print(f"- Tổng doanh thu (Bao gồm ngoại lệ):    £{total_rev:,.2f}")
        print(f"- Doanh thu khi tạm loại ngoại lệ:      £{normal_rev:,.2f}")
        print(f"- Doanh thu từ nhóm đơn ngoại lệ:       £{anomaly_rev:,.2f} ({impact_ratio:.2f}%)")
        print(f"- Tỷ lệ số đơn ngoại lệ:                {anomaly_orders:,} / {total_orders:,} đơn ({order_ratio:.2f}%)")
        print("- Nhận xét: Các đơn vượt ngưỡng IQR phản ánh phân phối lệch phải mạnh (heavy right-skewed). Không tự động xóa các đơn hợp lệ này và cần kiểm tra chi tiết từng mặt hàng thay vì mặc định mọi đơn lớn đều là giao dịch B2B.")

        return {
            'total_revenue': total_rev,
            'normal_revenue': normal_rev,
            'anomaly_revenue': anomaly_rev,
            'impact_ratio': impact_ratio,
            'order_ratio': order_ratio
        }

    def visualize_distribution(self, output_img_path: str | Path):
        if self.order_stats is None or self.order_stats.empty:
            return
        out_path = Path(output_img_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        plt.figure(figsize=(12, 4))
        sns.boxplot(x=self.order_stats['Revenue'], color='#3498db')
        plt.axvline(self.metrics.get('ub_rev', 0), color='r', linestyle='--', label=f"Upper Bound (£{self.metrics.get('ub_rev', 0):,.2f})")
        plt.title('Order Revenue Distribution (Valid Sales Orders)')
        plt.xlabel('Order Revenue (£)')
        plt.legend()
        plt.tight_layout()
        plt.savefig(out_path, dpi=300)
        plt.close()