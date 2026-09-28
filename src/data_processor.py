import pandas as pd

class RetailDataProcessor:
    def __init__(self, raw_data_path: str):
        self.raw_path = raw_data_path
        self.df = None
        self.df_cancelled = None
        self.df_valid = None

    def load_and_explore(self):

        self.df = pd.read_excel(self.raw_path)
        print("--- THỐNG KÊ KHÁM PHÁ (EDA) ---")
        print(f"Kích thước ban đầu: {self.df.shape}")
        print(f"Bản ghi trùng lặp: {self.df.duplicated().sum()}")
        print(f"Giá trị thiếu (Null):\n{self.df.isnull().sum()}")
        print("\nPhân bố Quantity và UnitPrice:")
        print(self.df[['Quantity', 'UnitPrice']].describe())

    def clean_data(self):
        
        initial_rows = len(self.df)
        
        self.df = self.df.drop_duplicates()
        self.df['InvoiceDate'] = pd.to_datetime(self.df['InvoiceDate'])
        
        is_cancelled = self.df['InvoiceNo'].astype(str).str.startswith('C')
        self.df_cancelled = self.df[is_cancelled].copy()
        
        valid_mask = (~is_cancelled) & (self.df['Quantity'] > 0) & (self.df['UnitPrice'] > 0)
        self.df_valid = self.df[valid_mask].copy()
        
        self.df_valid['CustomerID'] = self.df_valid['CustomerID'].fillna('Guest').astype(str)
        self.df_valid['Description'] = self.df_valid['Description'].fillna('Unknown').str.strip()
        
        print("\n--- TÀI LIỆU LÀM SẠCH (DOCUMENTATION) ---")
        print(f"Số bản ghi trước khi làm sạch: {initial_rows}")
        print(f"Số bản ghi hợp lệ (bán hàng): {len(self.df_valid)}")
        print(f"Số bản ghi hủy (lưu trữ riêng): {len(self.df_cancelled)}")
        print(f"Số bản ghi lỗi (Quantity/Price <= 0) đã bị loại bỏ: {initial_rows - len(self.df_valid) - len(self.df_cancelled)}")

    def engineer_features(self):
       
        self.df_valid['Revenue'] = self.df_valid['Quantity'] * self.df_valid['UnitPrice']
        self.df_valid['YearMonth'] = self.df_valid['InvoiceDate'].dt.to_period('M')

    def export_data(self, clean_path: str, cancelled_path: str):
        
        self.df_valid.to_csv(clean_path, index=False)
        self.df_cancelled.to_csv(cancelled_path, index=False)
        print(f"\nĐã xuất file hợp lệ: {clean_path}")
        print(f"Đã xuất file đơn hủy: {cancelled_path}")