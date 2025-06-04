import pandas as pd
import numpy as np

def generate_sample_stock_data(filename="historical_prices.csv", days=300):
    np.random.seed(42)
    dates = pd.date_range(end=pd.Timestamp.today(), periods=days)
    prices = np.cumsum(np.random.normal(0, 2, size=days)) + 150  # Random walk around 150

    df = pd.DataFrame({
        "date": dates,
        "close": prices
    })

    df.to_csv(filename, index=False)
    print(f"✅ Sample data generated in {filename}")

# Run this to generate data
if __name__ == "__main__":
    generate_sample_stock_data()
