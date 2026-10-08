import pandas as pd
from feature_engineering import assign_rfm_segment

def calculate_revenue(quantity, unit_price):
    """Tính doanh thu một dòng: Quantity * UnitPrice."""
    return round(quantity * unit_price, 2)


def is_cancelled_invoice(invoice_no):
    """Nhận diện hóa đơn hủy theo data contract: mã bắt đầu bằng 'C'."""
    return str(invoice_no).startswith('C')

def order_month(invoice_date):
    """Lấy tháng đơn hàng dạng 'YYYY-MM' từ InvoiceDate."""
    return pd.to_datetime(invoice_date).strftime('%Y-%m')

def assign_customer_segment(r_score, f_score, m_score):
    """Gán nhãn phân khúc từ 3 điểm R, F, M (wrapper của logic đã thống nhất)."""
    row = pd.Series({'R_score': r_score, 'F_score': f_score, 'M_score': m_score})
    return assign_rfm_segment(row)
