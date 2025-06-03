from celery import Celery
import os
from dotenv import load_dotenv
import asyncpg
import asyncio
import pandas as pd
import boto3
from datetime import datetime, timedelta
import json
import logging

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Celery app configuration
app = Celery('tradeops')
app.config_from_object('celeryconfig')

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'database': os.getenv('DB_NAME'),
    'password': os.getenv('DB_PASSWORD'),
    'port': os.getenv('DB_PORT')
}

# AWS S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)

async def get_db_connection():
    """Get async database connection"""
    return await asyncpg.connect(**DB_CONFIG)

@app.task
def calculate_5min_average_prices():
    """Calculate 5-minute average prices for all stocks"""
    async def _calculate():
        try:
            conn = await get_db_connection()
            
            # Get unique tickers from recent trades
            tickers_query = """
                SELECT DISTINCT ticker 
                FROM trading_api_trade 
                WHERE timestamp >= NOW() - INTERVAL '5 minutes'
            """
            tickers = await conn.fetch(tickers_query)
            
            results = {}
            for ticker_row in tickers:
                ticker = ticker_row['ticker']
                
                # Calculate average price for this ticker in last 5 minutes
                avg_query = """
                    SELECT 
                        AVG(price) as avg_price,
                        COUNT(*) as trade_count,
                        SUM(quantity * price) as total_volume
                    FROM trading_api_trade
                    WHERE ticker = $1 AND timestamp >= NOW() - INTERVAL '5 minutes'
                """
                
                result = await conn.fetchrow(avg_query, ticker)
                
                if result['avg_price']:
                    results[ticker] = {
                        'avg_price': float(result['avg_price']),
                        'trade_count': result['trade_count'],
                        'total_volume': float(result['total_volume'] or 0),
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # Store in strategy performance table
                    insert_query = """
                        INSERT INTO algorithmic_trading_strategyperformance 
                        (strategy_id, date, portfolio_value, daily_return, cumulative_return)
                        VALUES ($1, $2, $3, $4, $5)
                    """
                    
                    await conn.execute(
                        insert_query,
                        1,  # Default strategy ID
                        datetime.now().date(),
                        result['avg_price'],
                        0.0,  # Placeholder for daily return
                        0.0   # Placeholder for cumulative return
                    )
            
            await conn.close()
            logger.info(f"Calculated 5-minute averages for {len(results)} tickers")
            return results
            
        except Exception as e:
            logger.error(f"Error calculating 5-minute averages: {e}")
            return {}
    
    # Run the async function
    return asyncio.run(_calculate())

@app.task
def process_s3_trading_data(date_str):
    """Process trading data from S3 for analytics"""
    try:
        # Parse date
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        # S3 key for trading data
        s3_key = f"trading-data/2025/{target_date.month:02d}/{target_date.day:02d}/trades.csv"
        
        # Download CSV from S3
        try:
            response = s3_client.get_object(Bucket=os.getenv('S3_BUCKET_NAME'), Key=s3_key)
            df = pd.read_csv(response['Body'])
        except Exception as e:
            logger.error(f"Failed to download {s3_key}: {e}")
            return {"error": f"No data found for {date_str}"}
        
        # Perform analytics
        analytics = {
            "date": date_str,
            "total_trades": len(df),
            "total_volume": int(df['quantity'].sum()) if 'quantity' in df.columns else 0,
            "total_value": float((df['quantity'] * df['price']).sum()) if all(col in df.columns for col in ['quantity', 'price']) else 0,
            "avg_price": float(df['price'].mean()) if 'price' in df.columns else 0,
            "unique_tickers": int(df['ticker'].nunique()) if 'ticker' in df.columns else 0,
            "price_range": {
                "min": float(df['price'].min()) if 'price' in df.columns else 0,
                "max": float(df['price'].max()) if 'price' in df.columns else 0
            }
        }
        
        # Top tickers by volume
        if all(col in df.columns for col in ['ticker', 'quantity']):
            top_tickers = df.groupby('ticker')['quantity'].sum().sort_values(ascending=False).head(5)
            analytics["top_tickers_by_volume"] = top_tickers.to_dict()
        
        # Top tickers by value
        if all(col in df.columns for col in ['ticker', 'quantity', 'price']):
            df['trade_value'] = df['quantity'] * df['price']
            top_value = df.groupby('ticker')['trade_value'].sum().sort_values(ascending=False).head(5)
            analytics["top_tickers_by_value"] = top_value.to_dict()
        
        # Save analytics results back to S3
        result_key = f"analytics/2025/{target_date.month:02d}/{target_date.day:02d}/analysis_{date_str}.csv"
        
        # Convert analytics to DataFrame
        analytics_df = pd.DataFrame([analytics])
        
        # Upload to S3
        csv_buffer = analytics_df.to_csv(index=False)
        s3_client.put_object(
            Bucket=os.getenv('S3_BUCKET_NAME'),
            Key=result_key,
            Body=csv_buffer.encode('utf-8'),
            ContentType='text/csv'
        )
        
        logger.info(f"Analytics completed for {date_str}, saved to {result_key}")
        return analytics
        
    except Exception as e:
        logger.error(f"Error processing S3 data for {date_str}: {e}")
        return {"error": str(e)}

@app.task
def generate_trading_signals():
    """Generate trading signals based on recent market data"""
    async def _generate():
        try:
            conn = await get_db_connection()
            
            # Get recent price movements for analysis
            query = """
                SELECT 
                    ticker,
                    AVG(price) as avg_price,
                    STDDEV(price) as price_volatility,
                    COUNT(*) as trade_count,
                    MAX(price) as max_price,
                    MIN(price) as min_price
                FROM trading_api_trade
                WHERE timestamp >= NOW() - INTERVAL '1 hour'
                GROUP BY ticker
                HAVING COUNT(*) >= 5
            """
            
            results = await conn.fetch(query)
            signals = []
            
            for row in results:
                ticker = row['ticker']
                avg_price = float(row['avg_price'])
                volatility = float(row['price_volatility'] or 0)
                max_price = float(row['max_price'])
                min_price = float(row['min_price'])
                
                # Simple signal generation logic
                price_range = ((max_price - min_price) / avg_price) * 100
                
                signal_type = "HOLD"
                confidence = 0.5
                
                if volatility > avg_price * 0.02:  # High volatility
                    if price_range > 3:  # Price moved significantly
                        signal_type = "SELL"
                        confidence = 0.8
                elif volatility < avg_price * 0.005:  # Low volatility
                    signal_type = "BUY"
                    confidence = 0.7
                
                # Store signal in database
                insert_query = """
                    INSERT INTO algorithmic_trading_tradingsignal 
                    (ticker, signal_type, price, confidence, timestamp, metadata, strategy_id)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """
                
                metadata = {
                    "volatility": volatility,
                    "price_range_percent": price_range,
                    "trade_count": row['trade_count'],
                    "analysis_period": "1_hour"
                }
                
                await conn.execute(
                    insert_query,
                    ticker,
                    signal_type,
                    avg_price,
                    confidence,
                    datetime.now(),
                    json.dumps(metadata),
                    1  # Default strategy ID
                )
                
                signals.append({
                    "ticker": ticker,
                    "signal": signal_type,
                    "confidence": confidence,
                    "price": avg_price,
                    "metadata": metadata
                })
            
            await conn.close()
            logger.info(f"Generated {len(signals)} trading signals")
            return signals
            
        except Exception as e:
            logger.error(f"Error generating trading signals: {e}")
            return []
    
    return asyncio.run(_generate())

@app.task
def cleanup_old_data():
    """Clean up old data from the database"""
    async def _cleanup():
        try:
            conn = await get_db_connection()
            
            # Delete trades older than 30 days
            delete_trades = """
                DELETE FROM trading_api_trade 
                WHERE timestamp < NOW() - INTERVAL '30 days'
            """
            trades_deleted = await conn.execute(delete_trades)
            
            # Delete old trading signals older than 7 days
            delete_signals = """
                DELETE FROM algorithmic_trading_tradingsignal 
                WHERE timestamp < NOW() - INTERVAL '7 days'
            """
            signals_deleted = await conn.execute(delete_signals)
            
            # Delete old performance data older than 90 days
            delete_performance = """
                DELETE FROM algorithmic_trading_strategyperformance 
                WHERE date < CURRENT_DATE - INTERVAL '90 days'
            """
            performance_deleted = await conn.execute(delete_performance)
            
            await conn.close()
            
            result = {
                "trades_deleted": trades_deleted,
                "signals_deleted": signals_deleted,
                "performance_deleted": performance_deleted,
                "cleanup_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Cleanup completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return {"error": str(e)}
    
    return asyncio.run(_cleanup())

# Periodic task scheduling
from celery.schedules import crontab

app.conf.beat_schedule = {
    'calculate-5min-averages': {
        'task': 'celery_tasks.calculate_5min_average_prices',
        'schedule': 300.0,  # Every 5 minutes
    },
    'generate-trading-signals': {
        'task': 'celery_tasks.generate_trading_signals',
        'schedule': 3600.0,  # Every hour
    },
    'cleanup-old-data': {
        'task': 'celery_tasks.cleanup_old_data',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
}

app.conf.timezone = 'UTC'

if __name__ == "__main__":
    app.start()
