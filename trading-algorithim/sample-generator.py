import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

def generate_multi_ticker_data(filename="multi_ticker_data.csv", days=300):
    np.random.seed(42)
    tickers = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "META", "NFLX", "AMD", "INTC"]
    start_date = datetime.today() - timedelta(days=days)

    all_data = []

    for ticker in tickers:
        price = random.uniform(100, 300)  # Starting price per ticker

        for i in range(days):
            date = start_date + timedelta(days=i)
            change = np.random.normal(0, 2)
            price = max(price + change, 1)  # Price should be positive
            all_data.append({
                "date": date.date().isoformat(),
                "ticker": ticker,
                "close": round(price, 2)
            })

    df = pd.DataFrame(all_data)
    df.to_csv(filename, index=False)
    print(f"✅ Multi-ticker data written to {filename}")

# Run this
if __name__ == "__main__":
    generate_multi_ticker_data()
