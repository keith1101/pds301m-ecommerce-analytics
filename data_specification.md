# Data Specification

## 1. Nguồn dữ liệu
- Dataset: **UCI Online Retail**
- File raw chuẩn: `data/raw/Online Retail.xlsx`
- Kích thước tham chiếu: 541,909 dòng × 8 cột.
- Dữ liệu làm sạch đầu ra: `data/processed/cleaned_retail.csv`

## 2. Khảo sát cột và kiểu dữ liệu (raw)
| Column | Raw dtype (pandas) | Null count | Type mục tiêu sau chuẩn hóa | Mô tả |
|---|---:|---:|---|---|
| InvoiceNo | object | 0 | string | Mã hóa đơn |
| StockCode | object | 0 | string | Mã sản phẩm |
| Description | object | 1,454 | string | Mô tả sản phẩm |
| Quantity | int64 | 0 | int | Số lượng sản phẩm |
| InvoiceDate | datetime64[us] | 0 | datetime | Thời gian giao dịch |
| UnitPrice | float64 | 0 | float | Đơn giá |
| CustomerID | float64 | 135,080 | string | Mã khách hàng (ép string khi xử lý) |
| Country | str | 0 | string | Quốc gia |

## 3. Quy tắc làm sạch dữ liệu
1. **Thiếu dữ liệu**
   - Bỏ các dòng thiếu `CustomerID` khi làm phân tích theo khách hàng (RFM).
   - Bỏ các dòng thiếu `Description` nếu cần phân tích theo tên sản phẩm.
2. **Hóa đơn hủy**
   - Xác định hóa đơn hủy khi `InvoiceNo` bắt đầu bằng ký tự `C`.
   - Loại bỏ hóa đơn hủy khỏi các phân tích doanh thu tiêu chuẩn.
3. **Giá trị không hợp lệ**
   - Loại bỏ dòng có `Quantity <= 0` hoặc `UnitPrice <= 0` trong tập clean chính.
4. **Chuẩn hóa kiểu dữ liệu**
   - `InvoiceDate` -> datetime.
   - `CustomerID` -> string (tránh lỗi mất số 0/ép float khi xử lý tiếp).

## 4. Công thức chỉ số
- **Revenue = Quantity × UnitPrice**

## 5. Cấu trúc file cleaned_retail.csv
| Column | Type | Quy tắc |
|---|---|---|
| InvoiceNo | string | Không bắt đầu bằng `C` |
| StockCode | string |  |
| Description | string | Khuyến nghị không null cho phân tích sản phẩm |
| Quantity | int | `> 0` |
| InvoiceDate | datetime |  |
| UnitPrice | float | `> 0` |
| CustomerID | string | Không null cho phân tích khách hàng |
| Country | string |  |
| Revenue | float | `Quantity * UnitPrice` |
