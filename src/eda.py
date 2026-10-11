import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

# Service/fee codes: non-merchandise charges excluded from product rankings
# but retained in total revenue calculations.
SERVICE_CODES = ['DOT', 'POST', 'M', 'm', 'AMAZONFEE', 'B']


def load_cleaned_data(base_path):
    """Load cleaned_retail.csv into a DataFrame."""
    data_path = Path(base_path) / 'data' / 'processed' / 'cleaned_retail.csv'
    return pd.read_csv(
        data_path,
        dtype={'InvoiceNo': str},
    )


def total_revenue(df):
    """Calculate total dataset revenue."""
    return df['Revenue'].sum()


def revenue_by_month(df):
    """Calculate revenue by month (YearMonth)."""
    return df.groupby('YearMonth')['Revenue'].sum()


def revenue_by_country(df):
    """Calculate revenue by country, sorted descending."""
    return df.groupby('Country')['Revenue'].sum().sort_values(ascending=False)


def top_products(df, metric='Revenue', n=10):
    """Top n products by metric ('Revenue' or 'Quantity'), excluding service codes."""
    products = df[~df['StockCode'].isin(SERVICE_CODES)]
    return products.groupby('StockCode')[metric].sum().sort_values(ascending=False).head(n)


def order_values(df):
    """Compute per-invoice order values for boxplot distribution."""
    return df.groupby('InvoiceNo')['Revenue'].sum()


def save_chart(series, filepath, kind='bar', xlabel=''):
    """Render chart from a Series and save to file."""
    plt.figure()
    series.plot(kind=kind)
    plt.xlabel(xlabel)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(filepath)
    plt.close()


def main():
    base_path = str(Path(__file__).resolve().parents[1])
    df = load_cleaned_data(base_path)
    print('Shape:', df.shape)
    print('Total revenue:', round(total_revenue(df), 2))

    charts_path = Path(base_path) / 'charts'

    save_chart(
        revenue_by_month(df),
        charts_path / 'revenue_monthly_line.png',
        kind='line',
        xlabel='YearMonth'
    )

    save_chart(
        revenue_by_country(df).head(10),
        charts_path / 'revenue_country.png',
        xlabel='Country'
    )

    save_chart(
        top_products(df, metric='Quantity'),
        charts_path / 'top_products_quantity.png',
        xlabel='StockCode'
    )

    save_chart(
        top_products(df, metric='Revenue'),
        charts_path / 'top_products_revenue.png',
        xlabel='StockCode'
    )

    plt.figure()
    sns.boxplot(x=order_values(df))
    plt.tight_layout()
    plt.savefig(charts_path / 'order_value_boxplot.png')
    plt.close()


if __name__ == '__main__':
    main()
