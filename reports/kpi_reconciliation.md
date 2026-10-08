# KPI Reconciliation — Issue #18

## 1. Mục đích
Đối chiếu chéo các chỉ số cốt lõi giữa pipeline làm sạch (#16), phân tích doanh thu (#7) và phân khúc RFM (#8), đảm bảo không có mâu thuẫn nào không giải thích được trước khi làm notebook và report cuối (#22, #19).

## 2. Bảng reconciliation

| Metric | Population | Nguồn | Giá trị | Kết luận |
|---|---|---|---|---|
| Total Revenue (cleaned) | 524,878 giao dịch hợp lệ | `cleaned_retail.csv` | £10,642,110.80 | Baseline |
| Total Revenue (EDA) | cùng population | `eda.total_revenue()` | £10,642,110.80 | = baseline ✅ |
| Revenue non-Guest | CustomerID != Guest | cleaned | £8,887,208.89 | = baseline − Guest |
| Revenue Guest | CustomerID == Guest | cleaned | £1,754,901.91 | Chênh lệch chủ đích |
| Total Monetary (RFM) | CustomerID hợp lệ | `customer_segments.csv` | £8,887,208.89 | = non-Guest ✅ |
| Revenue theo segment (6 nhóm) | CustomerID hợp lệ | merge CustomerID | £8,887,208.89 | = non-Guest ✅ |
| Dòng trùng trong file cleaned | — | cleaned | 0 | Đã loại ở pipeline (5,268 dòng, £21,740.98) |
| Hóa đơn hủy | prefix C | `cancelled_retail.csv` | 9,251 hóa đơn | Khớp audit report |
| Dòng invalid còn sót | Qty/Price <= 0 | cleaned | 0 | Đã loại ở pipeline (2,512 dòng) |

Định nghĩa chung: `Revenue = Quantity × UnitPrice`, chỉ tính trên giao dịch bán hợp lệ (không phải hóa đơn hủy, Quantity và UnitPrice > 0).

## 3. Chênh lệch chủ đích

- **Guest £1,754,901.91** (~16.5% tổng): dòng Guest tính vào doanh thu nhưng loại khỏi RFM theo data contract. Đây là chênh lệch lớn nhất và hoàn toàn chủ đích.
- **Service codes** (DOT, POST, M, m, AMAZONFEE, B): giữ trong tổng doanh thu, loại khỏi bảng xếp hạng sản phẩm (#7). 90.3% dòng service-code là Guest nên hầu như không ảnh hưởng RFM; phần còn lại (~£38K, < 0.5% tổng Monetary) không đáng kể.
- **Hóa đơn hủy và dòng invalid**: nằm ngoài population tính toán ở mọi bước, số lượng khớp audit report của pipeline.

## 4. Phát hiện từ Revenue theo segment

| Segment | Revenue (£) | Tỉ trọng* |
|---|---|---|
| Champions | 5,676,143.38 | 63.9% |
| At Risk | 1,161,835.10 | 13.1% |
| Loyal Customers | 823,495.76 | 9.3% |
| Potential Loyalists | 583,120.23 | 6.6% |
| Others | 465,436.79 | 5.2% |
| Hibernating | 177,177.63 | 2.0% |

*Tỉ trọng trên tổng £8,887,208.89 của khách hàng định danh.

- **Champions gánh 64%** doanh thu khách định danh: nhóm nhỏ nhưng giá trị nhất.
- **At Risk đứng thứ hai (13%, £1.16M)**: khách giá trị cao đang có dấu hiệu rời bỏ, là nhóm đáng đầu tư giữ chân nhất.
- Tổng 6 segment = £8,887,208.89 khớp tuyệt đối với revenue non-Guest tính độc lập: merge không rớt dòng, không nhân đôi.

## 5. Output cho #22 và #19

- `data/processed/revenue_by_segment.csv`: doanh thu theo từng RFM segment (sinh bởi `src/reconcile.py`).
- Bảng reconciliation mục 2 và bảng segment mục 4: dùng trực tiếp trong Final Notebook và Final Report.
- Không vẽ lại chart của #7/#8.

## 6. Cách tái tạo

```bash
cd src
python reconcile.py
```

Script đọc `cleaned_retail.csv`, `customer_segments.csv`, `cancelled_retail.csv` từ `data/processed/`, in toàn bộ chỉ số đối chiếu và sinh `revenue_by_segment.csv`. Mọi số liệu trong báo cáo này đều tái tạo được từ code đã merge vào `develop`.

## 7. Kết luận

Không có KPI cốt lõi nào mâu thuẫn mà không giải thích được. Ba nguồn độc lập (pipeline, EDA, RFM) cùng cho ra các con số nhất quán. Issue #18 đạt điều kiện nghiệm thu.
