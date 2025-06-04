from fastapi import FastAPI, HTTPException, Depends, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Numeric, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, date
from typing import Optional, List
import os
from dotenv import load_dotenv
import asyncpg
import asyncio
import boto3
import pandas as pd
from celery import Celery
import logging
import json
import websockets
import httpx
from fastapi import FastAPI, Request, Response
import sys
from pathlib import Path

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

# FastAPI app
app = FastAPI(
    title="TradeOps API",
    description="Real-Time Stock Trading API and Analytics System",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Celery configuration
celery_app = Celery(
    "tradeops",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

# AWS S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)

# Database setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Pydantic models
class TradeCreate(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol (e.g., AAPL)")
    side: str = Field(..., description="Trade side: 'buy' or 'sell'")
    quantity: int = Field(..., gt=0, description="Number of shares")
    price: float = Field(..., gt=0, description="Price per share")
    user_id: Optional[int] = Field(None, description="User ID (optional)")

class TradeResponse(BaseModel):
    id: int
    ticker: str
    side: str
    quantity: int
    price: float
    timestamp: datetime
    user_id: Optional[int]

class StockPriceUpdate(BaseModel):
    ticker: str
    price: float
    timestamp: datetime

class AnalyticsRequest(BaseModel):
    date: str = Field(..., description="Date in YYYY-MM-DD format")

class LambdaRequest(BaseModel):
    date: str

class AlgorithmRequest(BaseModel):
    csv_path: str = Field(..., description="Path to the CSV file containing ticker data")
    initial_cash: Optional[float] = Field(10000, gt=0, description="Initial cash amount for each ticker (default: 10000)")

class TradeDetail(BaseModel):
    date: str
    action: str
    price: float
    shares: Optional[int] = None
    profit: Optional[float] = None

class TickerResult(BaseModel):
    ticker: str
    trades: List[List]  # Raw trade data
    final_cash: float
    profit_or_loss: float
    trade_count: int

class AlgorithmResponse(BaseModel):
    status: str
    csv_path: str
    initial_cash_per_ticker: float
    total_tickers: int
    total_initial_investment: float
    overall_profit_loss: float
    overall_return_percentage: float
    ticker_results: List[TickerResult]
    summary: dict

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Database connection for async operations
async def get_async_db():
    conn = await asyncpg.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        database=os.getenv('DB_NAME'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT')
    )
    return conn

@app.get("/")
async def root():
    return {
        "message": "TradeOps API - Real-Time Stock Trading and Analytics System",
        "version": "1.0.0",
        "endpoints": {
            "trades": "/trades/",
            "websocket": "ws://localhost:8000/ws",
            "analytics": "/analytics/",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        conn = await get_async_db()
        await conn.close()
        return {"status": "healthy", "database": "connected", "timestamp": datetime.now()}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e), "timestamp": datetime.now()}

@app.post("/trades/", response_model=TradeResponse)
async def create_trade(trade: TradeCreate):
    """Create a new trade entry"""
    try:
        conn = await get_async_db()
        
        # Insert trade into existing trading_api_trade table
        query = """
            INSERT INTO trading_api_trade (ticker, side, quantity, price, timestamp, user_id)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, ticker, side, quantity, price, timestamp, user_id
        """
        
        result = await conn.fetchrow(
            query,
            trade.ticker.upper(),
            trade.side.lower(),
            trade.quantity,
            trade.price,
            datetime.now(),
            trade.user_id
        )
        
        await conn.close()
        
        if result:
            return TradeResponse(**dict(result))
        else:
            raise HTTPException(status_code=500, detail="Failed to create trade")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/trades/", response_model=List[TradeResponse])
async def get_trades(
    ticker: Optional[str] = Query(None, description="Filter by ticker symbol"),
    from_date: Optional[str] = Query(None, description="From date (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, description="To date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000, description="Number of trades to return")
):
    """Retrieve trades with optional filtering"""
    try:
        conn = await get_async_db()
        
        # Build query with filters
        base_query = "SELECT id, ticker, side, quantity, price, timestamp, user_id FROM trading_api_trade"
        conditions = []
        params = []
        param_count = 0
        
        if ticker:
            param_count += 1
            conditions.append(f"ticker = ${param_count}")
            params.append(ticker.upper())
            
        if from_date:
            param_count += 1
            conditions.append(f"timestamp >= ${param_count}")
            params.append(from_date)
            
        if to_date:
            param_count += 1
            conditions.append(f"timestamp <= ${param_count}")
            params.append(to_date)
        
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
            
        base_query += f" ORDER BY timestamp DESC LIMIT ${param_count + 1}"
        params.append(limit)
        
        results = await conn.fetch(base_query, *params)
        await conn.close()
        
        return [TradeResponse(**dict(result)) for result in results]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/trades/stats")
async def get_trade_stats():
    """Get trading statistics"""
    try:
        conn = await get_async_db()
        
        stats_query = """
            SELECT 
                COUNT(*) as total_trades,
                COUNT(DISTINCT ticker) as unique_tickers,
                SUM(CASE WHEN side = 'buy' THEN quantity * price ELSE 0 END) as total_buy_volume,
                SUM(CASE WHEN side = 'sell' THEN quantity * price ELSE 0 END) as total_sell_volume,
                AVG(price) as avg_price
            FROM trading_api_trade
            WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days'
        """
        
        result = await conn.fetchrow(stats_query)
        await conn.close()
        
        return {
            "total_trades": result['total_trades'],
            "unique_tickers": result['unique_tickers'],
            "total_buy_volume": float(result['total_buy_volume'] or 0),
            "total_sell_volume": float(result['total_sell_volume'] or 0),
            "avg_price": float(result['avg_price'] or 0),
            "period": "Last 30 days"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/analytics/process")
async def trigger_analytics(request: AnalyticsRequest):
    """Trigger AWS Lambda analytics for a specific date"""
    try:
        # Parse date
        target_date = datetime.strptime(request.date, "%Y-%m-%d").date()
        
        # Check if data exists in S3
        s3_key = f"trading-data/2025/{target_date.month:02d}/{target_date.day:02d}/trades.csv"
        
        try:
            s3_client.head_object(Bucket=os.getenv('S3_BUCKET_NAME'), Key=s3_key)
        except:
            raise HTTPException(status_code=404, detail=f"No trading data found for {request.date}")
        
        # Trigger analytics processing (simulate Lambda function)
        analytics_result = await process_trading_analytics(request.date)
        
        return {
            "status": "success",
            "date": request.date,
            "analytics": analytics_result,
            "s3_key": s3_key
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics processing error: {str(e)}")

async def process_trading_analytics(date_str: str):
    """Process trading analytics (simulates AWS Lambda function)"""
    try:
        # Download CSV from S3
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        s3_key = f"trading-data/2025/{target_date.month:02d}/{target_date.day:02d}/trades.csv"
        
        response = s3_client.get_object(Bucket=os.getenv('S3_BUCKET_NAME'), Key=s3_key)
        df = pd.read_csv(response['Body'])
        
        # Perform analytics
        analytics = {
            "total_volume": df['quantity'].sum(),
            "total_value": (df['quantity'] * df['price']).sum(),
            "avg_price": df['price'].mean(),
            "unique_tickers": df['ticker'].nunique(),
            "top_tickers": df.groupby('ticker')['quantity'].sum().sort_values(ascending=False).head(5).to_dict()
        }
        
        # Save results back to S3
        result_key = f"analytics/2025/{target_date.month:02d}/{target_date.day:02d}/analysis_{date_str}.csv"
        result_df = pd.DataFrame([analytics])
        
        csv_buffer = result_df.to_csv(index=False)
        s3_client.put_object(
            Bucket=os.getenv('S3_BUCKET_NAME'),
            Key=result_key,
            Body=csv_buffer.encode('utf-8'),
            ContentType='text/csv'
        )
        
        return analytics
        
    except Exception as e:
        raise Exception(f"Analytics processing failed: {str(e)}")

@celery_app.task
def calculate_average_price(ticker: str, minutes: int = 5):
    """Celery task to calculate average price over specified minutes"""
    try:
        # This would typically connect to the database and calculate averages
        # For now, return a placeholder
        return {
            "ticker": ticker,
            "avg_price": 150.0,  # Placeholder
            "period_minutes": minutes,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/tickers/{ticker}/average")
async def get_ticker_average(ticker: str, minutes: int = Query(5, ge=1, le=60)):
    """Get average price for a ticker over specified minutes"""
    try:
        conn = await get_async_db()
        
        query = """
            SELECT AVG(price) as avg_price, COUNT(*) as trade_count
            FROM trading_api_trade
            WHERE ticker = $1 AND timestamp >= NOW() - INTERVAL '%s minutes'
        """ % minutes
        
        result = await conn.fetchrow(query, ticker.upper())
        await conn.close()
        
        return {
            "ticker": ticker.upper(),
            "avg_price": float(result['avg_price'] or 0),
            "trade_count": result['trade_count'],
            "period_minutes": minutes,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    backend_uri = "ws://localhost:8765"  # Your backend WebSocket server
    try:
        async with websockets.connect(backend_uri) as backend_ws:
            async def to_backend():
                while True:
                    data = await websocket.receive_text()
                    await backend_ws.send(data)
            async def from_backend():
                while True:
                    msg = await backend_ws.recv()
                    await websocket.send_text(msg)
            # Run both directions concurrently
            await asyncio.gather(to_backend(), from_backend())
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.close()

LAMBDA_API_URL = "https://hibjr4191a.execute-api.eu-north-1.amazonaws.com/default/moneyai"

@app.post("/moneyai")
async def proxy_to_lambda(request_data: LambdaRequest):
    body = request_data.json()
    async with httpx.AsyncClient() as client:
        lambda_response = await client.post(
            LAMBDA_API_URL,
            content=body,
            headers={"Content-Type": "application/json"}
        )
    try:
        lambda_json = lambda_response.json()
        return Response(
            content=json.dumps(lambda_json),
            status_code=lambda_response.status_code,
            media_type="application/json"
        )
    except Exception:
        return Response(
            content=lambda_response.content,
            status_code=lambda_response.status_code,
            headers=dict(lambda_response.headers)
        )

# Add the trading-algorithm directory to Python path
TRADING_ALGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trading-algorithim")
sys.path.append(TRADING_ALGO_PATH)

# Import the algorithm function
from algorithim import simulate_moving_average_strategy

@app.post("/algorithm/run", response_model=AlgorithmResponse)
async def run_trading_algorithm(request: AlgorithmRequest):
    """
    Run the moving average crossover trading algorithm on provided CSV data
    
    This endpoint accepts a CSV file path and optional initial cash amount,
    runs the trading algorithm, and returns detailed results in JSON format.
    """
    try:
        # Validate CSV file exists
        csv_path = request.csv_path
        if not os.path.isabs(csv_path):
            # If relative path, make it relative to the trading-algorithm directory
            csv_path = os.path.join(TRADING_ALGO_PATH, csv_path)
        
        if not os.path.exists(csv_path):
            raise HTTPException(
                status_code=404, 
                detail=f"CSV file not found: {csv_path}"
            )
        
        # Run the algorithm
        all_trades, overall_profit_loss = simulate_moving_average_strategy(
            csv_path=csv_path,
            initial_cash=request.initial_cash
        )
        
        # Process results for JSON response
        ticker_results = []
        total_tickers = len(all_trades)
        total_initial_investment = total_tickers * request.initial_cash
        
        profitable_count = 0
        losing_count = 0
        neutral_count = 0
        
        for ticker, data in all_trades.items():
            # Count performance categories
            if data['profit_or_loss'] > 0:
                profitable_count += 1
            elif data['profit_or_loss'] < 0:
                losing_count += 1
            else:
                neutral_count += 1
            
            ticker_result = TickerResult(
                ticker=ticker,
                trades=data['trades'],
                final_cash=data['final_cash'],
                profit_or_loss=data['profit_or_loss'],
                trade_count=len(data['trades'])
            )
            ticker_results.append(ticker_result)
        
        # Calculate summary statistics
        active_tickers = profitable_count + losing_count
        win_rate = (profitable_count / active_tickers * 100) if active_tickers > 0 else 0
        avg_return_per_active = overall_profit_loss / active_tickers if active_tickers > 0 else 0
        
        summary = {
            "profitable_tickers": profitable_count,
            "losing_tickers": losing_count,
            "neutral_tickers": neutral_count,
            "active_tickers": active_tickers,
            "win_rate_percentage": round(win_rate, 2),
            "average_return_per_active_ticker": round(avg_return_per_active, 2)
        }
        
        # Build response
        response = AlgorithmResponse(
            status="success",
            csv_path=csv_path,
            initial_cash_per_ticker=request.initial_cash,
            total_tickers=total_tickers,
            total_initial_investment=total_initial_investment,
            overall_profit_loss=overall_profit_loss,
            overall_return_percentage=round((overall_profit_loss / total_initial_investment) * 100, 2),
            ticker_results=ticker_results,
            summary=summary
        )
        
        return response
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid data format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Algorithm execution error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)