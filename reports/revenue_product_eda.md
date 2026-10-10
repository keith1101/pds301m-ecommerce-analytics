# Revenue & Product EDA — Issue #7

## 1. Câu hỏi phân tích
Nhóm khách hàng/sản phẩm nào tạo doanh thu cao? Xu hướng doanh thu theo thời gian ra sao?
(Câu hỏi P4: Phân tích khách hàng và sản phẩm trong bán lẻ online)

## 2. Dữ liệu
- Nguồn: `data/processed/cleaned_retail.csv`, sinh bởi pipeline sau PR #26 (issue #16)
- Phạm vi: 524,878 giao dịch bán hợp lệ, 12/2010–12/2011, cửa hàng quà tặng online tại Anh
- Population: đã loại hóa đơn hủy (InvoiceNo bắt đầu bằng C), Quantity và UnitPrice > 0,
  đã khử trùng lặp; giữ dòng Guest (khách vãng lai)
- Định nghĩa: Revenue = Quantity × UnitPrice

## 3. Kết quả

### 3.1 Tổng doanh thu

| Chỉ số | Giá trị |
|---|---:|
| Valid transaction rows | 524,878 |
| Total Revenue | £10,642,110.80 |
| Non-Guest Revenue | £8,887,208.89 |
| Guest Revenue | £1,754,901.91 |

Kiểm tra consistency:

- `Revenue = Quantity × UnitPrice` được tính lại độc lập và khớp với cột `Revenue`.
- Non-Guest Revenue khớp với population dùng cho RFM.
- Guest vẫn được giữ trong tổng Revenue nhưng không tham gia RFM.
- Cancelled invoices được tách sang `cancelled_retail.csv` và không nằm trong sales revenue population.

### 3.2 Xu hướng doanh thu theo tháng

Các điểm đáng chú ý:

- Revenue đạt đỉnh vào **11/2011**, khoảng **£1.5M**.
- Revenue thấp hơn rõ rệt vào **02/2011** và **04/2011**, khoảng **£0.52M**.
- Revenue tăng mạnh từ khoảng tháng 9 đến tháng 11/2011.
- `12/2010` và `12/2011` là các tháng không đầy đủ dữ liệu nên không nên so sánh trực tiếp với các tháng đầy đủ.

Chart:

`charts/revenue_monthly_line.png`

### 3.3 Doanh thu theo quốc gia
- United Kingdom: **84.6%** (~£9.0M). Business phụ thuộc gần như hoàn toàn vào thị trường nội địa Anh.
- 9 nước tiếp theo (Netherlands, EIRE, Germany, France, Australia, Spain, Switzerland, Belgium, Sweden) cộng lại chỉ ~15%.

### 3.4 Top sản phẩm

Các mã dịch vụ hoặc bút toán không đại diện cho sản phẩm vật lý được loại khỏi bảng xếp hạng sản phẩm, nhưng vẫn được giữ trong tổng doanh thu:

| StockCode | Description / Meaning | Xử lý |
|---|---|---|
| DOT | DOTCOM POSTAGE | Loại khỏi product ranking |
| POST | POSTAGE | Loại khỏi product ranking |
| M | Manual | Loại khỏi product ranking |
| m | Manual | Loại khỏi product ranking |
| AMAZONFEE | AMAZON FEE | Loại khỏi product ranking |
| B | Adjust bad debt | Loại khỏi product ranking |

Các mã `DCGSSBOY` và `DCGSSGIRL` được giữ lại vì chúng tương ứng với sản phẩm thật (`BOYS PARTY BAG` và `GIRLS PARTY BAG`).

Service codes chỉ bị loại khỏi product ranking; chúng không bị xóa khỏi `cleaned_retail.csv` và vẫn được giữ khi tính tổng Revenue.

Top 3 theo doanh thu: 22423 (£174,157), 23843 (£168,470), 85123A (£104,463).

Top 3 theo số lượng: 23843, 23166, 22197.

Chỉ có 23843 lọt cả hai top 3. 22423 dẫn đầu doanh thu nhưng không lọt top 3
số lượng: giá cao, bán ít. 23166 bán chạy hạng 2 nhưng doanh thu chỉ hạng 6:
giá rẻ, bán nhiều. Kết luận: "bán chạy nhất" và "tạo doanh thu cao nhất" là hai
tập sản phẩm khác nhau.

### 3.5 Phân bố giá trị đơn hàng
Boxplot cho thấy đơn hàng điển hình chỉ vài trăm bảng; ngưỡng trên (IQR) £1,006.11;
đuôi outliers kéo tới £168K là các đơn sỉ (wholesale), không phải lỗi dữ liệu.
Kết quả này làm đầu vào cho phân tích anomaly (issue #16).

## 4. Phương pháp
- Code: `src/eda.py`
- Charts: 5 file trong `charts/`

## 5. Hạn chế
- Dataset quan sát 1 năm, 1 cửa hàng tại Anh: không suy rộng ra toàn ngành bán lẻ.
- Tháng 12/2010 và 12/2011 thiếu dữ liệu.
- Mã sản phẩm dạng số chưa map sang tên/mô tả cụ thể trong báo cáo này.
- Phân tích mô tả, không kết luận nhân quả 
## 6. Charts
- `charts/revenue_monthly_line.png`
- `charts/revenue_country.png`
- `charts/top_products_quantity.png`
- `charts/top_products_revenue.png`
- `charts/order_value_boxplot.png`
