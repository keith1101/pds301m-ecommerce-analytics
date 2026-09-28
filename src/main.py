import os
from data_processor import RetailDataProcessor
from anomaly_detector import OrderAnomalyDetector

def main():
    RAW_DATA_PATH = os.path.join('..', 'data', 'raw', 'online_retail.xlsx')
    CLEAN_DATA_PATH = os.path.join('..', 'data', 'processed', 'cleaned_retail.csv')
    CANCELLED_DATA_PATH = os.path.join('..', 'data', 'processed', 'cancelled_retail.csv')
    
    CHART_OUTPUT_PATH = os.path.join('..', 'charts', 'revenue_boxplot.png')
    ANOMALY_CSV_PATH = os.path.join('..', 'data', 'processed', 'anomaly_orders.csv')

    print("=== [PHASE 1] DATA CLEANING ===")
    if not os.path.exists(CLEAN_DATA_PATH):
        processor = RetailDataProcessor(RAW_DATA_PATH)
        processor.load_and_explore()
        processor.clean_data()
        processor.engineer_features()
        processor.export_data(CLEAN_DATA_PATH, CANCELLED_DATA_PATH)
    else:
        print("[Skip] clean data already exists.")

    print("\n=== [PHASE 2] ORDER ANOMALY DETECTION ===")
    if os.path.exists(CLEAN_DATA_PATH):
        detector = OrderAnomalyDetector(CLEAN_DATA_PATH, CANCELLED_DATA_PATH)
        detector.analyze_cancelled_orders()
        detector.aggregate_orders()
        detector.detect_iqr_anomalies(ANOMALY_CSV_PATH)
        detector.evaluate_business_impact()
        detector.visualize_distribution(CHART_OUTPUT_PATH)
    else:
        print("[Error] Missing file cleaned_retail.csv.")

if __name__ == "__main__":
    main()