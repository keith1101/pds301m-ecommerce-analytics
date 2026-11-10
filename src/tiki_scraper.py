"""
Tiki E-Commerce Data Scraper Module.
Extracts product catalog and customer review data from public Tiki APIs.
Features:
- Browser impersonation headers and User-Agent rotation pool.
- Connection pooling with exponential backoff retries via urllib3.
- Circuit breaker pattern to prevent IP bans.
- Local idempotent JSON caching.
"""
from __future__ import annotations

import json
import logging
import random
import time
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

# --- 1. Logging Configuration (Exceptions only) ---
logger = logging.getLogger("TikiScraper")

# --- 2. API Endpoints & Default Constants ---
TIKI_PRODUCTS_API = "https://tiki.vn/api/v2/products"
TIKI_REVIEWS_API = "https://tiki.vn/api/v2/reviews"

# Browser impersonation headers to pass WAF verification
DEFAULT_TIKI_HEADERS: Dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://tiki.vn/",
    "Origin": "https://tiki.vn",
    "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Connection": "keep-alive",
}

# User-Agent rotation pool to prevent static session tracking
USER_AGENT_POOL: List[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Edg/124.0.0.0 Safari/537.36",
]


# --- 3. Circuit Breaker Implementation ---
class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreaker:
    """
    Manages circuit breaker state to avoid IP bans during continuous upstream errors.
    """
    def __init__(self, failure_threshold: int = 3, cooldown_seconds: float = 60.0):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.state = CircuitState.CLOSED
        self.consecutive_failures = 0
        self.last_failure_time = 0.0

    def can_execute(self) -> bool:
        """Determines whether the next HTTP request is permitted to proceed."""
        now = time.time()
        if self.state == CircuitState.OPEN:
            if now - self.last_failure_time >= self.cooldown_seconds:
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        return True

    def record_success(self) -> None:
        """Records a successful request, resetting failures and transitioning to CLOSED."""
        self.consecutive_failures = 0
        if self.state != CircuitState.CLOSED:
            self.state = CircuitState.CLOSED

    def record_failure(self, status_code: Optional[int] = None) -> None:
        """
        Records a critical failure (403, 429, 5xx, or network timeout).
        HTTP 400 and 404 represent expected domain conditions and are not counted.
        """
        self.consecutive_failures += 1
        self.last_failure_time = time.time()

        if self.consecutive_failures >= self.failure_threshold:
            self.state = CircuitState.OPEN


# --- 4. Resilient Session Factory ---
def build_resilient_session(
    retries: int = 5,
    backoff_factor: float = 1.5,
    pool_connections: int = 10,
    pool_maxsize: int = 10,
) -> requests.Session:
    """
    Constructs a requests.Session configured with connection pooling and exponential retries.
    """
    session = requests.Session()
    session.headers.update(DEFAULT_TIKI_HEADERS)

    retry_strategy = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False,
    )

    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=pool_connections,
        pool_maxsize=pool_maxsize,
    )

    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


# --- 5. Main TikiScraper Engine ---
class TikiScraper:
    """
    Harvests standardized Tiki catalog and review datasets for downstream analytics.
    """
    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        min_delay: float = 1.0,
        max_delay: float = 2.0,
        enable_cache: bool = True,
    ):
        self.session = build_resilient_session()
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, cooldown_seconds=60.0)
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.enable_cache = enable_cache

        # Raw cache directories
        self.cache_dir = cache_dir or Path("data/raw/tiki")
        self.products_cache_dir = self.cache_dir / "products"
        self.reviews_cache_dir = self.cache_dir / "reviews"

        self.products_cache_dir.mkdir(parents=True, exist_ok=True)
        self.reviews_cache_dir.mkdir(parents=True, exist_ok=True)

    def _sleep_polite(self) -> None:
        """Applies randomized uniform jitter delay between consecutive requests."""
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)

    def _rotate_user_agent(self) -> None:
        """Randomly selects a User-Agent string from the pool."""
        ua = random.choice(USER_AGENT_POOL)
        self.session.headers["User-Agent"] = ua

    def get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Executes a guarded HTTP GET request respecting circuit breaker and rate limits.
        """
        if not self.circuit_breaker.can_execute():
            return None

        self._sleep_polite()
        self._rotate_user_agent()

        try:
            res = self.session.get(url, params=params, timeout=12)

            if res.status_code == 200:
                content_type = res.headers.get("Content-Type", "")
                if "application/json" not in content_type:
                    self.circuit_breaker.record_failure(429)
                    return None

                try:
                    payload = res.json()
                    self.circuit_breaker.record_success()
                    return payload
                except ValueError as exc:
                    logger.exception("Failed to parse JSON payload: %s", exc)
                    self.circuit_breaker.record_failure()
                    return None

            elif res.status_code in (400, 404):
                return None
            else:
                self.circuit_breaker.record_failure(res.status_code)
                return None

        except (requests.exceptions.RequestException, Exception) as exc:
            logger.exception("Network transport exception occurred: %s", exc)
            self.circuit_breaker.record_failure()
            return None

    def crawl_category_products(
        self,
        category_id: int,
        max_items: int = 2000,
        limit_per_page: int = 40,
    ) -> List[Dict[str, Any]]:
        """
        Extracts product catalog records for a designated category.
        """
        all_products: List[Dict[str, Any]] = []
        page = 1

        while len(all_products) < max_items:
            cache_file = self.products_cache_dir / f"cat_{category_id}_page_{page}.json"

            if self.enable_cache and cache_file.exists():
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    items = data.get("data", [])
                    all_products.extend(items)

                    paging = data.get("paging", {})
                    last_page = paging.get("last_page", 1)
                    if page >= last_page or len(items) == 0:
                        break

                    page += 1
                    continue
                except Exception as exc:
                    logger.exception("Failed to read cache file %s: %s", cache_file, exc)

            params = {
                "category": category_id,
                "page": page,
                "limit": limit_per_page,
                "sort": "top_seller",
            }

            data = self.get(TIKI_PRODUCTS_API, params=params)
            if not data or "data" not in data or not data["data"]:
                break

            items = data["data"]
            all_products.extend(items)

            if self.enable_cache:
                try:
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                except Exception as exc:
                    logger.exception("Failed to write cache file %s: %s", cache_file, exc)

            paging = data.get("paging", {})
            last_page = paging.get("last_page", 1)
            if page >= last_page:
                break

            page += 1

        return all_products[:max_items]

    def crawl_product_reviews(
        self,
        product_id: int,
        max_reviews: int = 100,
        limit_per_page: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Extracts verified customer reviews for a given product identifier.
        """
        all_reviews: List[Dict[str, Any]] = []
        page = 1

        while len(all_reviews) < max_reviews:
            cache_file = self.reviews_cache_dir / f"prod_{product_id}_page_{page}.json"

            if self.enable_cache and cache_file.exists():
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    items = data.get("data", [])
                    all_reviews.extend(items)
                    if len(items) < limit_per_page or len(items) == 0:
                        break
                    page += 1
                    continue
                except Exception as exc:
                    logger.exception("Failed to read cache file %s: %s", cache_file, exc)

            params = {
                "product_id": product_id,
                "page": page,
                "limit": limit_per_page,
                "sort": "score",
            }

            data = self.get(TIKI_REVIEWS_API, params=params)
            if not data or "data" not in data or not data["data"]:
                break

            items = data["data"]
            all_reviews.extend(items)

            if self.enable_cache:
                try:
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                except Exception as exc:
                    logger.exception("Failed to write cache file %s: %s", cache_file, exc)

            if len(items) < limit_per_page:
                break

            page += 1

        return all_reviews[:max_reviews]


def flatten_products(products_raw: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Transforms raw Tiki product JSON records into a flattened tabular DataFrame.
    """
    records: List[Dict[str, Any]] = []
    for item in products_raw:
        if not isinstance(item, dict):
            continue

        quantity_sold_data = item.get("quantity_sold")
        quantity_sold_value = 0
        quantity_sold_text = ""
        if isinstance(quantity_sold_data, dict):
            quantity_sold_value = quantity_sold_data.get("value", 0) or 0
            quantity_sold_text = quantity_sold_data.get("text", "") or ""

        records.append({
            "id": item.get("id"),
            "sku": item.get("sku"),
            "name": item.get("name"),
            "price": item.get("price"),
            "original_price": item.get("original_price"),
            "discount": item.get("discount", 0),
            "discount_rate": item.get("discount_rate", 0),
            "rating_average": item.get("rating_average", 0.0),
            "review_count": item.get("review_count", 0),
            "seller_id": item.get("seller_id"),
            "seller_name": item.get("seller_name"),
            "primary_category_name": item.get("primary_category_name"),
            "quantity_sold": quantity_sold_value,
            "quantity_sold_text": quantity_sold_text,
        })

    df = pd.DataFrame(records)
    if not df.empty and "id" in df.columns:
        df = df.drop_duplicates(subset=["id"]).reset_index(drop=True)
    return df


def flatten_reviews(reviews_raw: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Transforms raw Tiki review JSON records into a flattened tabular DataFrame.
    """
    records: List[Dict[str, Any]] = []
    for item in reviews_raw:
        if not isinstance(item, dict):
            continue

        created_by = item.get("created_by") or {}
        customer_id = item.get("customer_id") or created_by.get("id")
        customer_name = created_by.get("name", "")
        purchased = created_by.get("purchased", True)
        purchased_at = created_by.get("purchased_at")

        records.append({
            "id": item.get("id"),
            "product_id": item.get("product_id"),
            "customer_id": customer_id,
            "customer_name": customer_name,
            "purchased": purchased,
            "purchased_at": purchased_at,
            "rating": item.get("rating"),
            "created_at": item.get("created_at"),
            "title": item.get("title", ""),
            "content": item.get("content", ""),
        })

    df = pd.DataFrame(records)
    if not df.empty and "id" in df.columns:
        df = df.drop_duplicates(subset=["id"]).reset_index(drop=True)
    return df


def export_cached_to_csv(cache_dir: Optional[Path] = None) -> Tuple[Optional[Path], Optional[Path]]:
    """
    Scans cached JSON artifacts (or consolidated files) and exports raw CSV files.
    Returns:
        tuple of (products_csv_path, reviews_csv_path)
    """
    base_dir = cache_dir or Path("data/raw/tiki")
    products_dir = base_dir / "products"
    reviews_dir = base_dir / "reviews"

    prod_csv_path: Optional[Path] = base_dir / "raw_tiki_products.csv"
    rev_csv_path: Optional[Path] = base_dir / "raw_tiki_reviews.csv"

    # 1. Export Products CSV
    all_products: List[Dict[str, Any]] = []
    consolidated_prod = base_dir / "all_products.json"
    if consolidated_prod.exists():
        try:
            with open(consolidated_prod, "r", encoding="utf-8") as f:
                all_products = json.load(f)
        except Exception as exc:
            logger.exception("Failed to read consolidated products JSON: %s", exc)

    if not all_products and products_dir.exists():
        for file in sorted(products_dir.glob("cat_*_page_*.json")):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    all_products.extend(data.get("data", []))
            except Exception as exc:
                logger.exception("Failed to read product cache file %s: %s", file, exc)

    if all_products:
        df_prod = flatten_products(all_products)
        df_prod.to_csv(prod_csv_path, index=False, encoding="utf-8-sig")
        print(f"Exported {len(df_prod):,} raw products to: {prod_csv_path}")
    else:
        prod_csv_path = None

    # 2. Export Reviews CSV
    all_reviews: List[Dict[str, Any]] = []
    consolidated_rev = base_dir / "all_reviews.json"
    if consolidated_rev.exists():
        try:
            with open(consolidated_rev, "r", encoding="utf-8") as f:
                all_reviews = json.load(f)
        except Exception as exc:
            logger.exception("Failed to read consolidated reviews JSON: %s", exc)

    if not all_reviews and reviews_dir.exists():
        for file in sorted(reviews_dir.glob("prod_*_page_*.json")):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    all_reviews.extend(data.get("data", []))
            except Exception as exc:
                logger.exception("Failed to read review cache file %s: %s", file, exc)

    if all_reviews:
        df_rev = flatten_reviews(all_reviews)
        df_rev.to_csv(rev_csv_path, index=False, encoding="utf-8-sig")
        print(f"Exported {len(df_rev):,} raw reviews to: {rev_csv_path}")
    else:
        rev_csv_path = None

    return prod_csv_path, rev_csv_path


def run_harvest_pipeline(
    target_categories: Optional[List[int]] = None,
    items_per_category: int = 700,
    min_reviews_to_crawl: int = 5000,
) -> None:
    """
    Executes an automated multi-category product and customer review harvesting pipeline:
    1. Crawls catalog products for designated category IDs.
    2. Filters items with active reviews to crawl customer transaction records.
    3. Persists consolidated JSON and flattened CSV artifacts to disk for downstream processing.
    """
    categories = target_categories or [8322, 1815, 1882]
    scraper = TikiScraper(min_delay=1.0, max_delay=1.8, enable_cache=True)

    print("============================================================")
    print("STARTING TIKI DATA HARVESTING PIPELINE")
    print(f"Target categories: {categories}")
    print(f"Target quotas: {items_per_category * len(categories)} products, {min_reviews_to_crawl} reviews")
    print("============================================================\n")

    # Step 1: Harvest product catalogs
    all_products: List[Dict[str, Any]] = []
    for cat_id in categories:
        products = scraper.crawl_category_products(
            category_id=cat_id,
            max_items=items_per_category,
            limit_per_page=40,
        )
        all_products.extend(products)
        print(f"Category {cat_id}: gathered {len(products)} products (total: {len(all_products)})")

    # Persist products JSON and CSV
    products_file = scraper.cache_dir / "all_products.json"
    with open(products_file, "w", encoding="utf-8") as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(all_products)} products to: {products_file}")

    df_prod = flatten_products(all_products)
    prod_csv_file = scraper.cache_dir / "raw_tiki_products.csv"
    df_prod.to_csv(prod_csv_file, index=False, encoding="utf-8-sig")
    print(f"Exported {len(df_prod):,} raw products to: {prod_csv_file}")

    # Step 2: Harvest customer reviews
    all_reviews: List[Dict[str, Any]] = []
    eligible_products = [p for p in all_products if p.get("review_count", 0) >= 5]
    print(f"\nIdentified {len(eligible_products)} products with review_count >= 5 for review crawling.")

    for idx, prod in enumerate(eligible_products, 1):
        if len(all_reviews) >= min_reviews_to_crawl:
            print(f"\nTarget quota reached: gathered {len(all_reviews)} reviews.")
            break

        prod_id = prod["id"]
        rev_count = prod.get("review_count", 0)

        reviews = scraper.crawl_product_reviews(
            product_id=prod_id,
            max_reviews=min(rev_count, 50),
            limit_per_page=20,
        )
        all_reviews.extend(reviews)

        if idx % 10 == 0 or len(all_reviews) >= min_reviews_to_crawl:
            print(
                f"Progress: [{idx}/{len(eligible_products)} products] -> "
                f"{len(all_reviews)}/{min_reviews_to_crawl} reviews gathered."
            )

    # Persist reviews JSON and CSV
    reviews_file = scraper.cache_dir / "all_reviews.json"
    with open(reviews_file, "w", encoding="utf-8") as f:
        json.dump(all_reviews, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(all_reviews)} reviews to: {reviews_file}")

    df_rev = flatten_reviews(all_reviews)
    rev_csv_file = scraper.cache_dir / "raw_tiki_reviews.csv"
    df_rev.to_csv(rev_csv_file, index=False, encoding="utf-8-sig")
    print(f"Exported {len(df_rev):,} raw reviews to: {rev_csv_file}")

    print("\n============================================================")
    print("TIKI DATA HARVESTING COMPLETED")
    print(f"Total products harvested: {len(all_products):,}")
    print(f"Total reviews harvested:  {len(all_reviews):,}")
    print("============================================================\n")


if __name__ == "__main__":
    run_harvest_pipeline()
