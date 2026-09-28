import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

class OrderAnomalyDetector:
    def __init__(self, cleaned_data_path: str, cancelled_data_path: str):
        self.df = pd.read_csv(cleaned_data_path, dtype={'InvoiceNo': str})
        
        if os.path.exists(cancelled_data_path):
            self.df_cancelled = pd.read_csv(cancelled_data_path, dtype={'InvoiceNo': str})
        else:
            self.df_cancelled = pd.DataFrame()
            
        self.order_stats = None
        self.upper_bound = 0

    def analyze_cancelled_orders(self):
        if not self.df_cancelled.empty:
            num_cancelled = self.df_cancelled['InvoiceNo'].nunique()
            print(f"- Number of cancelled orders: {num_cancelled:,}")
            print(f"- Number of returned items: {len(self.df_cancelled):,}")
        else:
            print("- No cancelled order data available for analysis.")

    def aggregate_orders(self):
        self.order_stats = self.df.groupby('InvoiceNo', as_index=False)['Revenue'].sum()

    def detect_iqr_anomalies(self, output_csv_path: str):
        q1 = self.order_stats['Revenue'].quantile(0.25)
        q3 = self.order_stats['Revenue'].quantile(0.75)
        iqr = q3 - q1
        self.upper_bound = q3 + 1.5 * iqr
        
        self.order_stats['IsAnomaly'] = self.order_stats['Revenue'] > self.upper_bound
        
        anomalies = self.order_stats[self.order_stats['IsAnomaly']].sort_values(by='Revenue', ascending=False)
        os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
        anomalies.to_csv(output_csv_path, index=False)
        
        print("\n=== 2. ANOMALY DETECTION ===")
        print(f"- Anomaly Threshold (Upper Bound): £{self.upper_bound:,.2f}")
        print(f"- Anomaly list saved to: {output_csv_path}")

    def evaluate_business_impact(self):
        total_revenue = self.order_stats['Revenue'].sum()
        normal_revenue = self.order_stats[~self.order_stats['IsAnomaly']]['Revenue'].sum()
        anomaly_revenue = total_revenue - normal_revenue
        
        total_orders = len(self.order_stats)
        anomaly_orders = self.order_stats['IsAnomaly'].sum()
        
        impact_ratio = (anomaly_revenue / total_revenue) * 100 if total_revenue > 0 else 0
        order_ratio = (anomaly_orders / total_orders) * 100 if total_orders > 0 else 0
        
        print("\n=== 3. COMPARISON & BUSINESS IMPACT ===")
        print(f"- Total Revenue (Including Anomalies): £{total_revenue:,.2f}")
        print(f"- Revenue (Excluding Anomalies): £{normal_revenue:,.2f}")
        print(f"- Difference (Revenue from Anomalies): £{anomaly_revenue:,.2f}")
        
        print("\n=== 4. BUSINESS INSIGHTS ===")
        print(f"Only with {order_ratio:.2f}% of total orders (Whales), this group contributes up to {impact_ratio:.2f}% of the total revenue.")
        print("NOTE: These are statistical anomalies (bulk purchasing behavior, B2B customers), NOT system data errors (e.g., negative values or garbage data). These records should not be automatically removed from the training/RFM analysis dataset.")

    def visualize_distribution(self, output_img_path: str):
        plt.figure(figsize=(12, 4))
        sns.boxplot(x=self.order_stats['Revenue'], color='#3498db')
        
        plt.axvline(self.upper_bound, color='r', linestyle='--', label=f'Upper Bound (£{self.upper_bound:,.0f})')
        
        plt.title('Distribution of Order Revenue (Valid Orders Only)')
        plt.xlabel('Revenue (£)')
        plt.legend()
        
        plt.tight_layout()
        plt.savefig(output_img_path, dpi=300)