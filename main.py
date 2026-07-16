from data.market_data import download_stock


print("=" * 50)
print("APEX ALPHA")
print("Investment Intelligence Platform")
print("=" * 50)


stocks = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN"]


for stock in stocks:
    print(f"\nScanning {stock}...")

    data = download_stock(stock)

    if data.empty:
        print(f"{stock} could not be analysed because no data was returned.")
        continue

    close_prices = data["Close"]

    # yfinance may return Close as a one-column DataFrame.
    # This extracts that column as a Series of prices.
    if close_prices.ndim == 2:
        close_prices = close_prices.iloc[:, 0]

    latest_close = close_prices.iloc[-1]
    highest_close = close_prices.max()
    lowest_close = close_prices.min()
    average_close = close_prices.mean()

    print(f"\n{stock} Summary")
    print(f"Latest Close : ${latest_close:.2f}")
    print(f"Highest Close: ${highest_close:.2f}")
    print(f"Lowest Close : ${lowest_close:.2f}")
    print(f"Average Close: ${average_close:.2f}")