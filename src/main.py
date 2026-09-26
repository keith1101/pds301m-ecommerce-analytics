# src/main.py
import os
from data_processor import RetailDataProcessor

def main():
    RAW_DATA_PATH = os.path.join('..', 'data', 'raw', 'online_retail.xlsx')
    CLEAN_DATA_PATH = os.path.join('..', 'data', 'processed', 'cleaned_retail.csv')
    CANCELLED_DATA_PATH = os.path.join('..', 'data', 'processed', 'cancelled_retail.csv')

    if not os.path.exists(RAW_DATA_PATH):
        print(f"Lỗi: Không tìm thấy file dữ liệu gốc tại {RAW_DATA_PATH}")
        return

    print("=== CHẠY PIPELINE LÀM SẠCH DỮ LIỆU ===")
    
    processor = RetailDataProcessor(RAW_DATA_PATH)
    
    print("\n1. Đang tải và khám phá dữ liệu...")
    processor.load_and_explore()
    
    print("\n2. Đang làm sạch dữ liệu...")
    processor.clean_data()
    
    print("\n3. Đang tạo thêm các đặc trưng phân tích (Feature Engineering)...")
    processor.engineer_features()
    
    print("\n4. Đang xuất file...")
    processor.export_data(CLEAN_DATA_PATH, CANCELLED_DATA_PATH)
    
    print("\n=== HOÀN TẤT PIPELINE ===")

if __name__ == "__main__":
    main()