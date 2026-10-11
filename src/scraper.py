import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path
import time

output_path = Path("data/processed/scraped_books.csv")

current_url = "https://books.toscrape.com/"
rating_map = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
}

def fetch_page(session, url):
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.content, "html.parser")
    except requests.exceptions.RequestException as exc:
        print(f"Cannot fetch {url}: {exc}")
        raise

def parse_book(book_tag, rating_map):
    title = book_tag.find("h3").find("a").get("title")  
    price = float(book_tag.find("p", class_ = "price_color").get_text().replace("£", ""))
    rating = rating_map[book_tag.find("p", class_ = "star-rating").get("class")[1]]
    book_info = {
            "title": title,
            "price": price,
            "rating": rating
    }

    return book_info



def validate_data(df):
    invalid_title = (
        (df["title"].isna()) |
        (df["title"].str.strip() == "")
    ).sum()

    invalid_price = (
        (df["price"].isna()) |
        (df["price"] <= 0)
    ).sum()

    invalid_rating = (
        ~df["rating"].isin([1, 2, 3, 4, 5])
    ).sum()

    duplicates = df.duplicated().sum()

    return {
        "total": len(df),
        "total_issues": (
            invalid_title + invalid_price
            + invalid_rating + duplicates
        ),
        "invalid_title": invalid_title,
        "invalid_price": invalid_price,
        "invalid_rating": invalid_rating,
        "duplicates": duplicates
    }

  

def save_csv(df, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding='utf-8-sig')

def scrape_books(start_url, rating_map, max_pages=None):
    books_data = []
    current_url = start_url
    page_number = 0

    with requests.Session() as session:

        while current_url is not None:

            # 1. Tải HTML của trang hiện tại
            page_soup = fetch_page(session, current_url)

            # 2. Tìm tất cả sách
            book_tags = page_soup.find_all(
                "article",
                class_="product_pod"
            )

            # Duyệt book_tags, gọi parse_book()
            # và lưu kết quả vào books_data

            for book_tag in book_tags:
                books_data.append(parse_book(book_tag, rating_map))

            page_number += 1

            print(
                f"Page {page_number}: "
                f"{len(book_tags)} books"
            )

            # 3. Kiểm tra giới hạn số trang
            if (
                max_pages is not None
                and page_number >= max_pages
            ):
                break

            # Tìm nút Next.
            # Nếu không còn Next, thoát vòng lặp.
            next_button = page_soup.select_one("li.next a")
            if next_button is None:
                break
            # Cập nhật current_url bằng urljoin()
            current_url = urljoin(current_url, next_button.get("href"))
            # Nghỉ 1 giây trước request tiếp theo
            time.sleep(1)

    return books_data


if __name__ == "__main__":
    books_data = scrape_books(
        start_url="https://books.toscrape.com/",
        rating_map=rating_map,
        max_pages=50
    )

    df = pd.DataFrame(books_data, columns=["title", "price", "rating"])

    report = validate_data(df)

    print("\nValidation report:")
    for key, value in report.items():
        print(f"{key}: {value}")

    print(f"\nDataFrame shape: {df.shape}")

    if df.empty:
        print("No books scraped. CSV was not saved.")
    elif report["total_issues"] == 0:
        save_csv(df, output_path)
        print(f"Saved {len(df)} books to {output_path}")
    else:
        print("Validation failed. CSV was not saved.")
