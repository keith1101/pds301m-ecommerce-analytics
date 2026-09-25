import pandas as pd

class RetailDataProcessor:
    def __init__(self, raw_data_path: str):
        self.raw_path = raw_data_path
        self.df = None
        self.df_cancelled = None
        self.df_valid = None

    def load_and_explore(self):

        self.df = pd.read_excel(self.raw_path)
        print("--- Exploration (EDA) ---")
        print(f"Shape beginning: {self.df.shape}")
        print(f"Duplicated records: {self.df.duplicated().sum()}")
        print(f"Missing values (Null):\n{self.df.isnull().sum()}")
        print("\nDistribution of Quantity and UnitPrice:")
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
        
        print("\n--- Clean Data (DOCUMENTATION) ---")
        print(f"total: {initial_rows}")
        print(f"valid: {len(self.df_valid)}")
        print(f"removed: {len(self.df_cancelled)}")
        print(f"fault (Quantity/Price <= 0) has been removed: {initial_rows - len(self.df_valid) - len(self.df_cancelled)}")

    def engineer_features(self):
       
        self.df_valid['Revenue'] = self.df_valid['Quantity'] * self.df_valid['UnitPrice']
        self.df_valid['YearMonth'] = self.df_valid['InvoiceDate'].dt.to_period('M')

    def export_data(self, clean_path: str, cancelled_path: str):
        
        self.df_valid.to_csv(clean_path, index=False)
        self.df_cancelled.to_csv(cancelled_path, index=False)
        print(f"\nexported valid data: {clean_path}")
        print(f"exported cancelled data: {cancelled_path}")