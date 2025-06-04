import pandas as pd

def simulate_moving_average_strategy(csv_path, initial_cash=10000):
    """
    Simulate a moving average crossover trading strategy.
    
    Args:
        csv_path (str): Path to CSV file with stock data
        initial_cash (float): Starting cash amount for each ticker
        
    Returns:
        tuple: (all_trades dict, overall_profit_loss float)
    """
    try:
        df = pd.read_csv(csv_path, parse_dates=["date"])
    except FileNotFoundError:
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    except Exception as e:
        raise Exception(f"Error reading CSV file: {e}")
    
    # Validate required columns
    required_columns = ["date", "ticker", "close"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    df.sort_values(["ticker", "date"], inplace=True)

    tickers = df["ticker"].unique()
    all_trades = {}
    overall_profit_loss = 0

    for ticker in tickers:
        stock_df = df[df["ticker"] == ticker].copy()

        stock_df["50ma"] = stock_df["close"].rolling(window=50).mean()
        stock_df["200ma"] = stock_df["close"].rolling(window=200).mean()

        position = None
        buy_price = 0
        cash = initial_cash
        shares = 0
        trades = []

        for i in range(1, len(stock_df)):
            today = stock_df.iloc[i]
            yesterday = stock_df.iloc[i - 1]            # Generate Buy Signal
            if (
                yesterday["50ma"] < yesterday["200ma"]
                and today["50ma"] >= today["200ma"]
                and position is None
                and not pd.isna(yesterday["50ma"]) 
                and not pd.isna(today["50ma"])
            ):
                shares = int(cash // today["close"])
                buy_price = float(today["close"])
                cash -= shares * buy_price
                position = "LONG"
                trades.append((str(today["date"].date()), "BUY", round(buy_price, 2), shares))            # Generate Sell Signal
            elif (
                yesterday["50ma"] > yesterday["200ma"]
                and today["50ma"] <= today["200ma"]
                and position == "LONG"
                and not pd.isna(yesterday["50ma"]) 
                and not pd.isna(today["50ma"])
            ):
                sell_price = float(today["close"])
                cash += shares * sell_price
                profit = (sell_price - buy_price) * shares
                trades.append((str(today["date"].date()), "SELL", round(sell_price, 2), shares, round(profit, 2)))
                position = None
                shares = 0        # Final valuation if holding
        if position == "LONG":
            eod_price = float(stock_df.iloc[-1]["close"])
            cash += shares * eod_price
            profit = (eod_price - buy_price) * shares
            trades.append((str(stock_df.iloc[-1]["date"].date()), "SELL (EOD)", round(eod_price, 2), shares, round(profit, 2)))

        final_pnl = cash - initial_cash
        overall_profit_loss += final_pnl

        print(f"\n📊 {ticker} Trade Summary:")
        for trade in trades:
            print(trade)
        print(f"Final Cash for {ticker}: ₹{cash:.2f}")
        print(f"Total P/L for {ticker}: ₹{final_pnl:.2f}")

        all_trades[ticker] = {
            "trades": trades,
            "final_cash": round(cash, 2),
            "profit_or_loss": round(final_pnl, 2),
        }

    print(f"\n💼 Overall Profit/Loss across all tickers: ₹{overall_profit_loss:.2f}")
    return all_trades, overall_profit_loss

def print_detailed_summary(all_trades, total_pnl, initial_cash_per_ticker=10000):
    """Print a detailed summary of the trading strategy results."""
    print("\n" + "="*60)
    print("📈 TRADING STRATEGY PERFORMANCE SUMMARY")
    print("="*60)
    
    total_initial_investment = len(all_trades) * initial_cash_per_ticker
    
    print(f"Strategy: Moving Average Crossover (50-day vs 200-day)")
    print(f"Initial Investment per Ticker: ₹{initial_cash_per_ticker:,.2f}")
    print(f"Total Tickers Analyzed: {len(all_trades)}")
    print(f"Total Initial Investment: ₹{total_initial_investment:,.2f}")
    
    profitable_tickers = sum(1 for ticker_data in all_trades.values() if ticker_data['profit_or_loss'] > 0)
    losing_tickers = sum(1 for ticker_data in all_trades.values() if ticker_data['profit_or_loss'] < 0)
    neutral_tickers = sum(1 for ticker_data in all_trades.values() if ticker_data['profit_or_loss'] == 0)
    
    print(f"\n📊 TICKER PERFORMANCE:")
    print(f"Profitable Tickers: {profitable_tickers}")
    print(f"Losing Tickers: {losing_tickers}")
    print(f"No Trades (Neutral): {neutral_tickers}")
    
    print(f"\n💰 FINANCIAL RESULTS:")
    print(f"Total P/L: ₹{total_pnl:,.2f}")
    print(f"Total Return: {(total_pnl/total_initial_investment)*100:.2f}%")
    print(f"Win Rate: {(profitable_tickers/(profitable_tickers+losing_tickers)*100):.1f}%" if (profitable_tickers+losing_tickers) > 0 else "Win Rate: N/A")
    
    if profitable_tickers + losing_tickers > 0:
        avg_return_per_active_ticker = total_pnl / (profitable_tickers + losing_tickers)
        print(f"Average Return per Active Ticker: ₹{avg_return_per_active_ticker:,.2f}")
        print("\n" + "="*60)

# Run the simulation
if __name__ == "__main__":
    try:
        trades, total_pnl = simulate_moving_average_strategy("multi_ticker_data.csv")
        print_detailed_summary(trades, total_pnl)
    except FileNotFoundError:
        print("❌ Error: multi_ticker_data.csv not found. Please run sample-generator.py first.")
    except Exception as e:
        print(f"❌ Error running algorithm: {e}")
