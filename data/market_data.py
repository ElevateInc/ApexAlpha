import yfinance as yf


def download_stock(symbol):
    print(f"Downloading {symbol}...")

    data = yf.download(symbol, period="1y")

    if data.empty:
        print(f"No data returned for {symbol}.")
        return data

    file_path = f"database/{symbol}.csv"
    data.to_csv(file_path)

    print(f"{symbol} saved to {file_path}.")

    return data 