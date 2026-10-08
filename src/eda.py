import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

# Mã dịch vụ/phí: không phải hàng hóa, loại khỏi bảng xếp hạng sản phẩm
# nhưng vẫn giữ trong tổng doanh thu.
SERVICE_CODES = ['DOT', 'POST', 'M', 'AMAZONFEE', 'm', 'DCGSSBOY', 'DCGSSGIRL', 'S', 'PADS', 'B']


def load_cleaned_data(base_path):
    """Đọc cleaned_retail.csv thành DataFrame."""
    return pd.read_csv(
        base_path + '\\data\\processed\\cleaned_retail.csv',
        dtype={'InvoiceNo': str},
    )


def total_revenue(df):
    """Tính tổng doanh thu toàn dataset."""
    return df['Revenue'].sum()


def revenue_by_month(df):
    """Tính doanh thu theo từng tháng (YearMonth)."""
    return df.groupby('YearMonth')['Revenue'].sum()


def revenue_by_country(df):
    """Tính doanh thu theo quốc gia, xếp giảm dần."""
    return df.groupby('Country')['Revenue'].sum().sort_values(ascending=False)


def top_products(df, metric='Revenue', n=10):
    """Top n sản phẩm theo metric ('Revenue' hoặc 'Quantity'), đã loại mã dịch vụ."""
    products = df[~df['StockCode'].isin(SERVICE_CODES)]
    return products.groupby('StockCode')[metric].sum().sort_values(ascending=False).head(n)


def order_values(df):
    """Giá trị từng hóa đơn, dùng vẽ boxplot."""
    return df.groupby('InvoiceNo')['Revenue'].sum()


def save_chart(series, filepath, kind='bar', xlabel=''):
    """Vẽ chart từ một Series và lưu thành file."""
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

    save_chart(revenue_by_month(df), base_path + '\\charts\\revenue_monthly_line.png',
               kind='line', xlabel='YearMonth')
    save_chart(revenue_by_country(df).head(10), base_path + '\\charts\\revenue_country.png',
               xlabel='Country')
    save_chart(top_products(df, metric='Quantity'), base_path + '\\charts\\top_products_quantity.png',
               xlabel='StockCode')
    save_chart(top_products(df, metric='Revenue'), base_path + '\\charts\\top_products_revenue.png',
               xlabel='StockCode')

    plt.figure()
    sns.boxplot(x=order_values(df))
    plt.tight_layout()
    plt.savefig(base_path + '\\charts\\order_value_boxplot.png')
    plt.close()


if __name__ == '__main__':
    main()
