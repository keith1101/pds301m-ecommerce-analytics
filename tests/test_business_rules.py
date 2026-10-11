import pytest
from src.business_rules import (
    calculate_revenue,
    is_cancelled_invoice,
    order_month,
    assign_customer_segment,
)


def test_calculate_revenue():
    assert calculate_revenue(2, 10.5) == 21.0
    assert calculate_revenue(3, 3.333) == 10.0
    assert calculate_revenue(0, 50.0) == 0.0


def test_is_cancelled_invoice():
    assert is_cancelled_invoice('C536365') is True
    assert is_cancelled_invoice('c536365') is False
    assert is_cancelled_invoice('536365') is False
    assert is_cancelled_invoice(536365) is False


def test_order_month():
    assert order_month('2011-12-01 08:26:00') == '2011-12'
    assert order_month('2010-01-15') == '2010-01'


def test_assign_customer_segment():
    assert assign_customer_segment(5, 5, 5) == "Champions"
    assert assign_customer_segment(1, 1, 1) == "Hibernating"
    assert assign_customer_segment(1, 4, 4) == "At Risk"
    assert assign_customer_segment(3, 4, 4) == "Loyal Customers"
    assert assign_customer_segment(4, 2, 2) == "Potential Loyalists"
