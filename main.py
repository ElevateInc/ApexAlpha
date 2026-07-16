from data.market_data import download_stock
from indicators.moving_averages import add_simple_moving_average


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

    data = add_simple_moving_average(data, period=20)

    close_prices = data["Close"]
    sma_20_values = data["SMA_20"]

    if close_prices.ndim == 2:
        close_prices = close_prices.iloc[:, 0]

    if sma_20_values.ndim == 2:
        sma_20_values = sma_20_values.iloc[:, 0]

    latest_close = close_prices.iloc[-1]
    highest_close = close_prices.max()
    lowest_close = close_prices.min()
    average_close = close_prices.mean()
    latest_sma_20 = sma_20_values.iloc[-1]

    if latest_close > latest_sma_20:
        trend_status = "ABOVE 20-DAY SMA — SHORT-TERM BULLISH"
    elif latest_close < latest_sma_20:
        trend_status = "BELOW 20-DAY SMA — SHORT-TERM BEARISH"
    else:
        trend_status = "AT 20-DAY SMA — NEUTRAL"

    print(f"\n{stock} Summary")
    print("-" * 45)
    print(f"Latest Close : ${latest_close:.2f}")
    print(f"Highest Close: ${highest_close:.2f}")
    print(f"Lowest Close : ${lowest_close:.2f}")
    print(f"Average Close: ${average_close:.2f}")
    print(f"20-Day SMA   : ${latest_sma_20:.2f}")
    print(f"Trend Status : {trend_status}")