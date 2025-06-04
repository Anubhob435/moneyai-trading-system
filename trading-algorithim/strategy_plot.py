import pandas as pd
import matplotlib.pyplot as plt

def simulate_strategy_with_plot(csv_path):
    df = pd.read_csv(csv_path, parse_dates=["date"])
    df.sort_values(["ticker", "date"], inplace=True)

    tickers = df["ticker"].unique()

    for ticker in tickers:
        stock_df = df[df["ticker"] == ticker].copy()

        stock_df["50ma"] = stock_df["close"].rolling(window=50).mean()
        stock_df["200ma"] = stock_df["close"].rolling(window=200).mean()

        position = None
        buy_signals = []
        sell_signals = []

        for i in range(1, len(stock_df)):
            today = stock_df.iloc[i]
            yesterday = stock_df.iloc[i - 1]

            # Buy Signal
            if (
                yesterday["50ma"] < yesterday["200ma"]
                and today["50ma"] >= today["200ma"]
                and position is None
            ):
                buy_signals.append((today["date"], today["close"]))
                position = "LONG"

            # Sell Signal
            elif (
                yesterday["50ma"] > yesterday["200ma"]
                and today["50ma"] <= today["200ma"]
                and position == "LONG"
            ):
                sell_signals.append((today["date"], today["close"]))
                position = None

        # Plotting for the current ticker
        plt.figure(figsize=(14, 7))
        plt.plot(stock_df["date"], stock_df["close"], label="Close Price", color="gray", alpha=0.5)
        plt.plot(stock_df["date"], stock_df["50ma"], label="50-Day MA", color="blue")
        plt.plot(stock_df["date"], stock_df["200ma"], label="200-Day MA", color="orange")

        if buy_signals:
            buy_dates, buy_prices = zip(*buy_signals)
            plt.scatter(buy_dates, buy_prices, marker="^", color="green", label="Buy", s=100)

        if sell_signals:
            sell_dates, sell_prices = zip(*sell_signals)
            plt.scatter(sell_dates, sell_prices, marker="v", color="red", label="Sell", s=100)

        plt.title(f"Moving Average Crossover Strategy - {ticker}")
        plt.xlabel("Date")
        plt.ylabel("Price")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()

# Run this after generating CSV
if __name__ == "__main__":
    simulate_strategy_with_plot("multi_ticker_data.csv")
