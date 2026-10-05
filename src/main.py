from pathlib import Path
from data_processor import RetailDataProcessor
from anomaly_detector import OrderAnomalyDetector


def main():
    ROOT_DIR = Path(__file__).resolve().parent.parent
    RAW_DATA_PATH = ROOT_DIR / 'data' / 'raw' / 'online_retail.xlsx'
    CLEAN_DATA_PATH = ROOT_DIR / 'data' / 'processed' / 'cleaned_retail.csv'
    CANCELLED_DATA_PATH = ROOT_DIR / 'data' / 'processed' / 'cancelled_retail.csv'
    ANOMALY_CSV_PATH = ROOT_DIR / 'data' / 'processed' / 'anomaly_orders.csv'
    CHART_OUTPUT_PATH = ROOT_DIR / 'charts' / 'revenue_boxplot.png'

    print("=== [PHASE 1] DATA CLEANING & FEATURE ENGINEERING ===")
    if not (CLEAN_DATA_PATH.exists() and CANCELLED_DATA_PATH.exists()):
        if not RAW_DATA_PATH.exists():
            raise FileNotFoundError(
                f"Thiếu dữ liệu đầu vào: Không tìm thấy {RAW_DATA_PATH} để tái tạo "
                f"{CLEAN_DATA_PATH.name} và {CANCELLED_DATA_PATH.name}."
            )
        processor = RetailDataProcessor(RAW_DATA_PATH)
        processor.load_and_explore()
        processor.clean_data(deduplicate=True, fill_guest=True)
        processor.engineer_features()
        processor.export_data(CLEAN_DATA_PATH, CANCELLED_DATA_PATH)
    else:
        print(f"[Info] Đã tìm thấy đủ {CLEAN_DATA_PATH.name} và {CANCELLED_DATA_PATH.name}.")

    print("\n=== [PHASE 2] ORDER ANOMALY DETECTION ===")
    detector = OrderAnomalyDetector(
        cleaned_data_path=CLEAN_DATA_PATH,
        cancelled_data_path=CANCELLED_DATA_PATH
    )
    detector.analyze_cancelled_orders()
    detector.aggregate_orders()
    detector.detect_iqr_anomalies(output_csv_path=ANOMALY_CSV_PATH)
    detector.evaluate_business_impact()
    detector.visualize_distribution(output_img_path=CHART_OUTPUT_PATH)


if __name__ == "__main__":
    main()