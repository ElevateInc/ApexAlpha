from data.market_data import download_stock

print("=" * 50)
print("APEX ALPHA")
print("Investment Intelligence Platform")
print("=" * 50)

apple = download_stock("AAPL")

print(apple.head())