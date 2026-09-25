# PDS301m — E-commerce Analytics

Dự án phân tích dữ liệu thương mại điện tử cho môn PDS301m. Phạm vi ban đầu sử dụng **UCI Online Retail** để khám phá doanh thu, hành vi mua hàng, phân khúc khách hàng theo RFM và phát hiện đơn hàng bất thường.

> Branch `develop` hiện chỉ chứa **cấu trúc thư mục và tài liệu hướng dẫn**. Chưa có mã nguồn, dataset, notebook hay kết quả phân tích.

## Mục tiêu

- Thu thập và tìm hiểu dữ liệu giao dịch bán lẻ.
- Làm sạch, kiểm tra chất lượng và chuẩn hóa dữ liệu.
- Phân tích doanh thu, sản phẩm và phân khúc khách hàng (Recency, Frequency, Monetary — RFM).
- Khảo sát các đơn hàng bất thường và trực quan hóa kết quả.
- Tổng hợp kết quả thành báo cáo có thể tái lập.

## Cấu trúc dự án

```text
pds301m-ecommerce-analytics/
├── README.md                 # Giới thiệu dự án và quy ước chung
├── data/
│   ├── README.md             # Quy tắc quản lý dữ liệu
│   ├── raw/
│   │   └── README.md         # Dữ liệu gốc, không chỉnh sửa
│   └── processed/
│       └── README.md         # Dữ liệu sau khi xử lý
├── notebooks/
│   └── README.md             # Khám phá dữ liệu và thử nghiệm
├── src/
│   └── README.md             # Mã nguồn xử lý, phân tích (chưa triển khai)
├── charts/
│   └── README.md             # Biểu đồ và hình trực quan hóa
├── reports/
│   └── README.md             # Báo cáo, kết quả và diễn giải
├── docs/
│   └── README.md             # Đặc tả dữ liệu và phương pháp
└── tests/
    └── README.md             # Kiểm thử pipeline (chưa triển khai)
```

Mỗi thư mục có một `README.md` giải thích chức năng, loại tài liệu dự kiến và quy tắc sử dụng.

## Quy trình dự kiến

1. **Data ingestion:** Lấy bộ dữ liệu UCI Online Retail và lưu nguyên trạng trong `data/raw/`.
2. **Preprocessing:** Kiểm tra dữ liệu thiếu, hóa đơn hủy, số lượng/giá trị không hợp lệ; lưu kết quả trong `data/processed/`.
3. **Exploratory data analysis:** Khám phá phân phối và xu hướng trong `notebooks/`.
4. **Analytics:** Phân tích doanh thu, sản phẩm, quốc gia; tính RFM và kiểm tra outlier bằng IQR hoặc Z-score.
5. **Communication:** Xuất biểu đồ sang `charts/` và báo cáo sang `reports/`.

**Dữ liệu ban đầu:** [UCI Online Retail](https://archive.ics.uci.edu/dataset/352/online+retail). Nếu mở rộng sang web scraping, lưu dữ liệu từ nguồn bổ sung riêng, ghi lại nguồn và không trộn lẫn với giao dịch UCI khi chưa chuẩn hóa.

## Quy ước làm việc

- `main`: nhánh ổn định; `develop`: nhánh tích hợp trong quá trình phát triển.
- Tạo nhánh tính năng từ `develop`, mở pull request để review trước khi merge.
- Không chỉnh sửa trực tiếp dữ liệu trong `data/raw/`. Các kết quả `processed`, `charts`, `reports` cần có khả năng tái tạo.
- Chỉ thêm mã nguồn, thư viện và dữ liệu thực khi bắt đầu giai đoạn triển khai. Cập nhật README liên quan mỗi khi thay đổi cấu trúc hoặc quy trình.
