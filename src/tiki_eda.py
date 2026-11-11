from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import json 


def plot_price_distribution(
    cleaned_path="data/processed/cleaned_tiki.csv",
    output_path="charts/tiki_price_distribution.png",
):
    df = pd.read_csv(cleaned_path)
    prices = pd.to_numeric(df["UnitPrice"], errors="coerce")
    prices = prices[prices > 0].dropna()

    if prices.empty:
        raise ValueError("Không có giá Tiki hợp lệ để vẽ.")

    bins = np.geomspace(prices.min(), prices.max(), 36)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(prices, bins=bins, color="#1677A8", edgecolor="white")
    ax.set_xscale("log")
    ax.set_title("Tiki purchase price distribution")
    ax.set_xlabel("Unit price (VND, log scale)")
    ax.set_ylabel("Verified purchase reviews")
    ax.grid(axis="y", alpha=0.25)

    fig.text(
        0.5, 0.01,
        "Review-derived transactions only; not all Tiki orders.",
        ha="center", fontsize=9, color="#555555",
    )
    fig.tight_layout(rect=(0, 0.05, 1, 1))

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=300, bbox_inches="tight")
    plt.close(fig)

    return len(prices)

def plot_top_products_sold(
    products_path="data/raw/tiki/all_products.json",
    output_path="charts/tiki_top_products_sold.png",
):
    with Path(products_path).open(encoding="utf-8") as file:
        products = pd.DataFrame(json.load(file))

    products = products.drop_duplicates(subset="id").copy()
    products["UnitsSold"] = pd.to_numeric(
        products["quantity_sold"].map(
            lambda value: value.get("value") if isinstance(value, dict) else None
        ),
        errors="coerce",
    )
    top = (
        products.dropna(subset=["UnitsSold"])
        .sort_values(["UnitsSold", "id"], ascending=[False, True])
        .head(10)
        .iloc[::-1]
    )

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(top["id"].astype(str), top["UnitsSold"], color="#1677A8")
    ax.bar_label(bars, labels=[f"{v:,.0f}" for v in top["UnitsSold"]], padding=4)
    ax.set_xlim(0, top["UnitsSold"].max() * 1.18)
    ax.set_title("Top 10 sampled Tiki products by reported units sold")
    ax.set_xlabel("Reported units sold")
    ax.set_ylabel("Product ID")
    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)

    fig.text(
        0.5, 0.01,
        "Catalog snapshot of sampled products; not a ranking of all Tiki products.",
        ha="center", fontsize=9, color="#555555",
    )
    fig.tight_layout(rect=(0, 0.05, 1, 1))

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=300, bbox_inches="tight")
    plt.close(fig)

    return len(top)

def plot_discount_distribution(
    products_path="data/raw/tiki/all_products.json",
    output_path="charts/tiki_discount_distribution.png",
):
    with Path(products_path).open(encoding="utf-8") as file:
        products = pd.DataFrame(json.load(file))

    products = products.drop_duplicates(subset="id")
    rates = pd.to_numeric(products["discount_rate"], errors="coerce")
    rates = rates[rates.between(0, 100)].dropna()

    if rates.empty:
        raise ValueError("No valid discount rates found.")

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(rates, bins=np.arange(0, 105, 5), color="#1677A8", edgecolor="white")
    ax.axvline(
        rates.median(), color="#C44736", linestyle="--",
        label=f"Median: {rates.median():.0f}%",
    )
    ax.set_title("Discount rates of sampled Tiki products")
    ax.set_xlabel("Discount rate (%)")
    ax.set_ylabel("Number of products")
    ax.set_xlim(0, 100)
    ax.grid(axis="y", alpha=0.25)
    ax.legend()

    fig.text(
        0.5, 0.01,
        "Catalog snapshot of sampled products; not all Tiki products.",
        ha="center", fontsize=9, color="#555555",
    )
    fig.tight_layout(rect=(0, 0.05, 1, 1))

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=300, bbox_inches="tight")
    plt.close(fig)

    return len(rates)

def plot_product_correlations(
    products_path="data/raw/tiki/all_products.json",
    output_path="charts/tiki_product_correlations.png",
):
    with Path(products_path).open(encoding="utf-8") as file:
        products = pd.DataFrame(json.load(file))

    products = products.drop_duplicates(subset="id").copy()
    products["units_sold"] = products["quantity_sold"].map(
        lambda value: value.get("value") if isinstance(value, dict) else None
    )

    columns = ["rating_average", "review_count", "units_sold"]
    for column in columns:
        products[column] = pd.to_numeric(products[column], errors="coerce")

    valid = products.dropna(subset=columns)
    valid = valid[
        valid["rating_average"].gt(0)
        & valid["review_count"].gt(0)
        & valid["units_sold"].gt(0)
    ]
    if len(valid) < 2:
        raise ValueError("Not enough rated products for correlation analysis.")

    correlation = valid[columns].corr(method="spearman")
    labels = ["Average rating", "Review count", "Reported units sold"]

    fig, ax = plt.subplots(figsize=(7, 6))
    image = ax.imshow(correlation, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(3), labels=labels, rotation=30, ha="right")
    ax.set_yticks(range(3), labels=labels)
    ax.set_title("Spearman correlation of sampled Tiki products")

    for row in range(3):
        for col in range(3):
            value = correlation.iloc[row, col]
            color = "white" if abs(value) > 0.5 else "black"
            ax.text(col, row, f"{value:.2f}", ha="center", va="center", color=color)

    fig.colorbar(image, ax=ax, label="Spearman correlation")
    fig.text(
        0.5, 0.01,
        f"{len(valid):,} rated products with reported sales; correlation is not causation.",
        ha="center", fontsize=9, color="#555555",
    )
    fig.tight_layout(rect=(0, 0.05, 1, 1))

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=300, bbox_inches="tight")
    plt.close(fig)

    return len(valid)

if __name__ == "__main__":
    count = plot_price_distribution()
    print(f"Đã vẽ phân phối giá từ {count} giao dịch.")
    count = plot_top_products_sold()
    print(f"Đã vẽ top sản phẩm bán chạy từ {count} sản phẩm.")
    count = plot_discount_distribution()
    print(f"Đã vẽ phân phối chiết khấu từ {count} sản phẩm.")
    count = plot_product_correlations()
    print(f"Đã vẽ mối quan hệ giữa các sản phẩm từ {count} sản phẩm.")