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
**£10,642,110.80** trên 524,878 giao dịch.

Verified:
- Tính lại độc lập từ Quantity × UnitPrice khớp tuyệt đối với cột Revenue.
- Phần non-Guest: £8,887,208.89, khớp benchmark độc lập (£8.89M).
- Chênh lệch với benchmark net £9.75M đúng bằng £894K tiền hoàn/hủy đã tách riêng
  sang file cancelled.
- Top 5 dòng lớn nhất đều là đơn sỉ hợp lệ, không có dòng lỗi phình tổng.

### 3.2 Xu hướng theo tháng
- Đỉnh tháng 11/2011 (~£1.5M), gấp đôi mức trung bình các tháng còn lại: mùa mua sắm
  Giáng sinh.
- Đáy tháng 2/2011 và tháng 4/2011 (~£0.52M).
- Tháng 12/2010 và 12/2011 không đầy đủ dữ liệu (dataset bắt đầu 12/2010, kết thúc
  09/12/2011) nên không so sánh trực tiếp với các tháng đủ.
- Xu hướng chung: đi ngang nửa đầu năm, tăng tốc từ tháng 9 đến tháng 11/2011.

### 3.3 Doanh thu theo quốc gia
- United Kingdom: **84.6%** (~£9.0M). Business phụ thuộc gần như hoàn toàn vào thị trường nội địa Anh.
- 9 nước tiếp theo (Netherlands, EIRE, Germany, France, Australia, Spain, Switzerland, Belgium, Sweden) cộng lại chỉ ~15%.

### 3.4 Top sản phẩm
Đã loại 4 mã phí/dịch vụ khỏi xếp hạng (nhưng giữ trong tổng doanh thu):

- DOT → DOTCOM POSTAGE (£206,249, đứng hạng 1 nếu không loại)
- POST → POSTAGE
- M → Manual
- AMAZONFEE → AMAZON FEE

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
