import pandas as pd

def simulate_moving_average_strategy(csv_path, initial_cash=10000):
    df = pd.read_csv(csv_path, parse_dates=["date"])
    df.sort_values("date", inplace=True)

    df["50ma"] = df["close"].rolling(window=50).mean()
    df["200ma"] = df["close"].rolling(window=200).mean()

    position = None
    buy_price = 0
    cash = initial_cash
    shares = 0
    trades = []

    for i in range(1, len(df)):
        today = df.iloc[i]
        yesterday = df.iloc[i - 1]

        # Generate Buy Signal
        if (
            yesterday["50ma"] < yesterday["200ma"]
            and today["50ma"] >= today["200ma"]
            and position is None
        ):
            # Buy as much as we can
            shares = cash // today["close"]
            buy_price = today["close"]
            cash -= shares * buy_price
            position = "LONG"
            trades.append((today["date"], "BUY", buy_price))

        # Generate Sell Signal
        elif (
            yesterday["50ma"] > yesterday["200ma"]
            and today["50ma"] <= today["200ma"]
            and position == "LONG"
        ):
            # Sell all
            sell_price = today["close"]
            cash += shares * sell_price
            profit = (sell_price - buy_price) * shares
            trades.append((today["date"], "SELL", sell_price, profit))
            position = None
            shares = 0

    # Final valuation
    if position == "LONG":
        cash += shares * df.iloc[-1]["close"]
        trades.append((df.iloc[-1]["date"], "SELL (EOD)", df.iloc[-1]["close"]))

    profit_or_loss = cash - initial_cash

    # Print report
    print("\nTrade Summary:")
    for trade in trades:
        print(trade)

    print(f"\nFinal Cash: ₹{cash:.2f}")
    print(f"Total P/L: ₹{profit_or_loss:.2f}")

    return trades, cash, profit_or_loss
