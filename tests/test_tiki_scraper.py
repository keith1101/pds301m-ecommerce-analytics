"""
Unit test suite for Tiki Scraper module (src/tiki_scraper.py).
100% offline tests using standard library unittest.mock.
Verifies:
- Default headers and User-Agent rotation.
- Resilient session configuration (connection pooling and retries).
- Circuit breaker state machine transitions (Closed -> Open -> Half-Open -> Closed).
- Parsing and extraction of product catalog and verified reviews.
- Idempotent local caching mechanism.
"""
import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.tiki_scraper import (
    DEFAULT_TIKI_HEADERS,
    TIKI_PRODUCTS_API,
    TIKI_REVIEWS_API,
    USER_AGENT_POOL,
    CircuitBreaker,
    CircuitState,
    TikiScraper,
    build_resilient_session,
)


# --- 1. Header and Configuration Tests ---
def test_default_headers_contain_browser_fingerprint():
    """Verify default headers contain valid browser fingerprint metadata."""
    assert "User-Agent" in DEFAULT_TIKI_HEADERS
    assert "Referer" in DEFAULT_TIKI_HEADERS
    assert "Sec-Ch-Ua" in DEFAULT_TIKI_HEADERS
    assert "Chrome" in DEFAULT_TIKI_HEADERS["User-Agent"]


def test_build_resilient_session_mounts_adapters():
    """Verify requests session mounts HTTPAdapter and retry strategy."""
    session = build_resilient_session()
    assert "https://" in session.adapters
    assert "http://" in session.adapters
    assert session.headers.get("Referer") == "https://tiki.vn/"


# --- 2. Circuit Breaker State Machine Tests ---
def test_circuit_breaker_initial_state():
    """Verify initial state is CLOSED with zero failures and execution allowed."""
    cb = CircuitBreaker(failure_threshold=3, cooldown_seconds=2.0)
    assert cb.state == CircuitState.CLOSED
    assert cb.consecutive_failures == 0
    assert cb.can_execute() is True


def test_circuit_breaker_trips_to_open_after_threshold():
    """Verify circuit transitions to OPEN after consecutive failure threshold is reached."""
    cb = CircuitBreaker(failure_threshold=3, cooldown_seconds=2.0)

    cb.record_failure(status_code=500)
    assert cb.state == CircuitState.CLOSED
    assert cb.consecutive_failures == 1

    cb.record_failure(status_code=429)
    assert cb.state == CircuitState.CLOSED
    assert cb.consecutive_failures == 2

    cb.record_failure(status_code=403)
    assert cb.state == CircuitState.OPEN
    assert cb.consecutive_failures == 3
    assert cb.can_execute() is False


def test_circuit_breaker_half_open_recovery():
    """Verify circuit transitions to HALF_OPEN after cooldown and recovers to CLOSED upon success."""
    cb = CircuitBreaker(failure_threshold=2, cooldown_seconds=0.1)

    cb.record_failure(500)
    cb.record_failure(500)
    assert cb.state == CircuitState.OPEN

    time.sleep(0.15)
    assert cb.can_execute() is True
    assert cb.state == CircuitState.HALF_OPEN

    cb.record_success()
    assert cb.state == CircuitState.CLOSED
    assert cb.consecutive_failures == 0


# --- 3. Scraper Resilience and Boundary Handling Tests ---
def test_scraper_ignores_400_and_404_in_circuit_breaker(tmp_path: Path):
    """Verify HTTP 400 and 404 client errors do not increment circuit breaker failures."""
    scraper = TikiScraper(cache_dir=tmp_path, min_delay=0.0, max_delay=0.0)

    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.url = "https://tiki.vn/api/v2/products/0"

    with patch.object(scraper.session, "get", return_value=mock_resp):
        result = scraper.get("https://tiki.vn/api/v2/products/0")
        assert result is None
        assert scraper.circuit_breaker.consecutive_failures == 0
        assert scraper.circuit_breaker.state == CircuitState.CLOSED


def test_scraper_records_failure_on_500_error(tmp_path: Path):
    """Verify HTTP 500 error increments circuit breaker failure counter."""
    scraper = TikiScraper(cache_dir=tmp_path, min_delay=0.0, max_delay=0.0)

    mock_resp = MagicMock()
    mock_resp.status_code = 500

    with patch.object(scraper.session, "get", return_value=mock_resp):
        result = scraper.get(TIKI_PRODUCTS_API)
        assert result is None
        assert scraper.circuit_breaker.consecutive_failures == 1


# --- 4. Mock Harvesting and Parsing Tests ---
def test_crawl_category_products_success(tmp_path: Path):
    """Verify category product crawling and structure parsing."""
    scraper = TikiScraper(cache_dir=tmp_path, min_delay=0.0, max_delay=0.0)

    mock_data = {
        "data": [
            {
                "id": 101,
                "name": "Mathematics Textbook",
                "price": 50000,
                "review_count": 10,
                "quantity_sold": {"value": 150},
            },
            {
                "id": 102,
                "name": "Ballpoint Pen",
                "price": 25000,
                "review_count": 0,
                "quantity_sold": {"value": 30},
            },
        ],
        "paging": {"last_page": 1, "total": 2},
    }

    with patch.object(scraper, "get", return_value=mock_data) as mock_get:
        products = scraper.crawl_category_products(category_id=8322, max_items=10)

        assert len(products) == 2
        assert products[0]["id"] == 101
        assert products[0]["name"] == "Mathematics Textbook"
        assert products[1]["price"] == 25000
        mock_get.assert_called_once()


def test_crawl_product_reviews_success(tmp_path: Path):
    """Verify review extraction and verified buyer field handling."""
    scraper = TikiScraper(cache_dir=tmp_path, min_delay=0.0, max_delay=0.0)

    mock_review_data = {
        "data": [
            {
                "id": 9991,
                "customer_id": 12345,
                "rating": 5,
                "created_at": 1700000000,
                "created_by": {"purchased": True, "name": "Nguyen Van A"},
            }
        ]
    }

    with patch.object(scraper, "get", return_value=mock_review_data):
        reviews = scraper.crawl_product_reviews(product_id=101, max_reviews=5)

        assert len(reviews) == 1
        assert reviews[0]["customer_id"] == 12345
        assert reviews[0]["rating"] == 5
        assert reviews[0]["created_by"]["purchased"] is True


# --- 5. Caching Idempotency Test ---
def test_caching_mechanism_prevents_duplicate_network_calls(tmp_path: Path):
    """Verify cached files on disk bypass external network calls completely."""
    scraper = TikiScraper(cache_dir=tmp_path, min_delay=0.0, max_delay=0.0, enable_cache=True)

    cached_content = {
        "data": [{"id": 888, "name": "Cached Product Item", "price": 99000}],
        "paging": {"last_page": 1, "total": 1},
    }
    cache_file = tmp_path / "products" / "cat_8322_page_1.json"
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(cached_content, f)

    with patch.object(scraper, "get") as mock_get:
        products = scraper.crawl_category_products(category_id=8322, max_items=5)

        assert len(products) == 1
        assert products[0]["id"] == 888
        assert products[0]["name"] == "Cached Product Item"
        mock_get.assert_not_called()


# --- 6. JSON to CSV Export Tests ---
def test_flatten_products_and_reviews_dataframes():
    """Verify raw JSON dicts are properly converted to flattened DataFrames."""
    from src.tiki_scraper import flatten_products, flatten_reviews

    raw_products = [
        {
            "id": 1,
            "sku": "SKU1",
            "name": "Product 1",
            "price": 10000,
            "quantity_sold": {"value": 50, "text": "Đã bán 50"},
        }
    ]
    df_p = flatten_products(raw_products)
    assert len(df_p) == 1
    assert df_p.iloc[0]["id"] == 1
    assert df_p.iloc[0]["quantity_sold"] == 50

    raw_reviews = [
        {
            "id": 99,
            "product_id": 1,
            "rating": 5,
            "created_by": {"id": 123, "name": "Customer A", "purchased": True},
        }
    ]
    df_r = flatten_reviews(raw_reviews)
    assert len(df_r) == 1
    assert df_r.iloc[0]["customer_id"] == 123
    assert bool(df_r.iloc[0]["purchased"]) is True


def test_export_cached_to_csv_creates_valid_csv_files(tmp_path: Path):
    """Verify export_cached_to_csv creates readable CSV files from JSON cache."""
    from src.tiki_scraper import export_cached_to_csv
    import pandas as pd

    products_dir = tmp_path / "products"
    reviews_dir = tmp_path / "reviews"
    products_dir.mkdir()
    reviews_dir.mkdir()

    # Create mock product cache
    with open(products_dir / "cat_8322_page_1.json", "w", encoding="utf-8") as f:
        json.dump({"data": [{"id": 10, "name": "Book A", "price": 20000}]}, f)

    # Create mock review cache
    with open(reviews_dir / "prod_10_page_1.json", "w", encoding="utf-8") as f:
        json.dump({"data": [{"id": 201, "product_id": 10, "rating": 5, "customer_id": 999}]}, f)

    prod_csv, rev_csv = export_cached_to_csv(cache_dir=tmp_path)

    assert prod_csv is not None and prod_csv.exists()
    assert rev_csv is not None and rev_csv.exists()

    df_p = pd.read_csv(prod_csv)
    df_r = pd.read_csv(rev_csv)

    assert len(df_p) == 1
    assert df_p.iloc[0]["id"] == 10
    assert len(df_r) == 1
    assert df_r.iloc[0]["customer_id"] == 999
