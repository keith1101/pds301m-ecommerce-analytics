import pandas as pd
try:
    from src.feature_engineering import assign_rfm_segment
except ImportError:
    from feature_engineering import assign_rfm_segment

def calculate_revenue(quantity, unit_price):
    """Calculate line item revenue: Quantity * UnitPrice."""
    return round(quantity * unit_price, 2)


def is_cancelled_invoice(invoice_no):
    """Identify cancelled invoices per data contract: code begins with 'C'."""
    return str(invoice_no).startswith('C')

def order_month(invoice_date):
    """Extract order month formatted as 'YYYY-MM' from InvoiceDate."""
    return pd.to_datetime(invoice_date).strftime('%Y-%m')

def assign_customer_segment(r_score, f_score, m_score):
    """Assign customer segment from R, F, M scores (wrapper of agreed RFM logic)."""
    row = pd.Series({'R_score': r_score, 'F_score': f_score, 'M_score': m_score})
    return assign_rfm_segment(row)
