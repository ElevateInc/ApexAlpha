import yfinance as yf


def download_stock(symbol):

    print(f"Downloading {symbol}...")

    data = yf.download(symbol, period="1y")

    return data