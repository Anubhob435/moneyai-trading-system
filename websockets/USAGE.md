# TradeOps System Usage Guide

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL database (configured in `.env`)
- Redis server (optional, for background tasks)
- AWS S3 access (configured in `.env`)

### 1. Install and Start
```powershell
# Install dependencies
pip install -r requirements.txt

# Start all services (Windows)
.\start.ps1

# Or start manually
python run_services.py
```

### 2. Verify System
```powershell
# Run system tests
python test_system.py
```

## 📡 API Endpoints

### Base URL: `http://localhost:8000`

#### Health Check
```bash
GET /health
```

#### Trading Operations

**Create Trade**
```bash
POST /trades/
Content-Type: application/json

{
  "ticker": "AAPL",
  "side": "buy",
  "quantity": 100,
  "price": 150.50,
  "user_id": 1
}
```

**Get Trades**
```bash
GET /trades/
GET /trades/?ticker=AAPL
GET /trades/?from_date=2025-06-01&to_date=2025-06-03
GET /trades/?ticker=AAPL&limit=50
```

**Get Trade Statistics**
```bash
GET /trades/stats
```

**Get Ticker Average**
```bash
GET /tickers/AAPL/average?minutes=5
```

#### Analytics

**Process S3 Data**
```bash
POST /analytics/process
Content-Type: application/json

{
  "date": "2025-06-03"
}
```

## 🔌 WebSocket Real-Time Monitoring

### Connection: `ws://localhost:8765`

### Message Types

**Subscribe to Tickers**
```json
{
  "type": "subscribe",
  "tickers": ["AAPL", "GOOGL", "MSFT"]
}
```

**Get Price History**
```json
{
  "type": "get_history",
  "ticker": "AAPL"
}
```

### Received Messages

**Current Prices**
```json
{
  "type": "current_prices",
  "data": {
    "AAPL": 150.0,
    "GOOGL": 2500.0
  },
  "timestamp": "2025-06-03T10:00:00"
}
```

**Price Updates**
```json
{
  "type": "price_update",
  "data": {
    "AAPL": 151.2,
    "GOOGL": 2505.3
  },
  "timestamp": "2025-06-03T10:00:01"
}
```

**Price Alerts**
```json
{
  "type": "price_alert",
  "ticker": "AAPL",
  "change_percent": 2.5,
  "current_price": 153.75,
  "previous_price": 150.0,
  "message": "AAPL increased by 2.5% in the last minute!",
  "timestamp": "2025-06-03T10:01:00"
}
```

## 🖥️ Command Line Tools

### Real-Time Monitoring
```powershell
python realtime_monitor.py
```
- Connects to WebSocket server
- Shows live price updates
- Displays alerts for 2%+ price increases
- Subscribes to default tickers: AAPL, GOOGL, MSFT, TSLA

### S3 Analytics Processing
```powershell
python s3_analytics.py
```
- Processes trading data from S3
- Generates comprehensive analytics
- Saves results back to S3
- Creates sample data if none exists

### System Tests
```powershell
python test_system.py
```
- Tests all API endpoints
- Verifies WebSocket connectivity
- Checks database connections
- Validates S3 analytics

## ⚙️ Background Tasks (Celery)

### Available Tasks

1. **5-Minute Average Calculation**
   - Runs every 5 minutes
   - Calculates average prices for all active tickers
   - Stores results in database

2. **Trading Signal Generation**
   - Runs every hour
   - Analyzes market data for trading opportunities
   - Generates BUY/SELL/HOLD signals

3. **Data Cleanup**
   - Runs daily at 2 AM
   - Removes old trades (30+ days)
   - Cleans up old signals (7+ days)

4. **S3 Analytics Processing**
   - On-demand processing
   - Analyzes daily trading data
   - Generates comprehensive reports

### Manual Task Execution
```powershell
# Activate virtual environment first
.\venv\Scripts\Activate.ps1

# Calculate averages
celery -A celery_tasks call calculate_5min_average_prices

# Generate signals
celery -A celery_tasks call generate_trading_signals

# Process S3 data
celery -A celery_tasks call process_s3_trading_data --args='["2025-06-03"]'

# Cleanup old data
celery -A celery_tasks call cleanup_old_data
```

## 📊 Database Schema

### Trading Tables

**trading_api_trade**
- `id`: Primary key
- `ticker`: Stock symbol
- `side`: 'buy' or 'sell'
- `quantity`: Number of shares
- `price`: Price per share
- `timestamp`: Trade timestamp
- `user_id`: Associated user (optional)

**trading_api_portfolio**
- User portfolio information
- Total value and cash balance

**trading_api_position**
- Current stock positions
- Quantity and average price

### Analytics Tables

**algorithmic_trading_tradingsignal**
- Generated trading signals
- Signal type, confidence, metadata

**algorithmic_trading_strategyperformance**
- Strategy performance metrics
- Daily returns and portfolio values

## ☁️ AWS S3 Structure

### Trading Data
```
s3://moneyai/
├── trading-data/
│   └── 2025/
│       └── 06/           # Month
│           ├── 01/       # Day
│           │   └── trades.csv
│           ├── 02/
│           │   └── trades.csv
│           └── 03/
│               └── trades.csv
```

### Analytics Results
```
s3://moneyai/
├── analytics/
│   └── 2025/
│       └── 06/
│           ├── 01/
│           │   ├── analysis_2025-06-01.csv
│           │   └── analysis_2025-06-01.json
│           └── 02/
│               ├── analysis_2025-06-02.csv
│               └── analysis_2025-06-02.json
```

## 🔧 Troubleshooting

### Common Issues

**1. Database Connection Failed**
- Check `.env` file configuration
- Verify database credentials
- Ensure database is accessible

**2. WebSocket Connection Refused**
- Check if WebSocket server is running on port 8765
- Verify firewall settings
- Look for port conflicts

**3. Redis Connection Failed**
- Install Redis: `docker run -d -p 6379:6379 redis`
- Or install Redis locally
- Background tasks will fail without Redis

**4. S3 Access Denied**
- Verify AWS credentials in `.env`
- Check S3 bucket permissions
- Ensure correct region is specified

**5. Import Errors**
- Activate virtual environment
- Install missing packages: `pip install -r requirements.txt`
- Check Python version compatibility

### Service Management

**Check Running Services**
```powershell
# Windows
netstat -an | findstr ":8000"  # FastAPI
netstat -an | findstr ":8765"  # WebSocket
netstat -an | findstr ":6379"  # Redis

# Check processes
tasklist | findstr python
```

**Restart Individual Services**
```powershell
# Stop all services (Ctrl+C in run_services.py terminal)
# Then restart specific components:

# FastAPI only
python api-app.py

# WebSocket only  
python websocket-server.py

# Celery worker only
celery -A celery_tasks worker --loglevel=info --pool=solo

# Celery beat only
celery -A celery_tasks beat --loglevel=info
```

## 📈 Monitoring and Logs

### API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Log Locations
- FastAPI: Console output
- WebSocket: Console output  
- Celery: Console output
- Background tasks: Check Celery worker logs

### Health Monitoring
```bash
# API health
curl http://localhost:8000/health

# Database connectivity
python check_db.py

# Full system test
python test_system.py
```

## 🎯 Example Workflows

### 1. Create and Monitor Trades
```python
import requests

# Create a trade
trade_data = {
    "ticker": "AAPL",
    "side": "buy", 
    "quantity": 100,
    "price": 150.50
}
response = requests.post("http://localhost:8000/trades/", json=trade_data)
print(response.json())

# Get recent trades
trades = requests.get("http://localhost:8000/trades/?limit=10")
print(trades.json())
```

### 2. Real-Time Price Monitoring
```python
import asyncio
import websockets
import json

async def monitor_prices():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        async for message in websocket:
            data = json.loads(message)
            if data["type"] == "price_update":
                print(f"Price update: {data['data']}")

asyncio.run(monitor_prices())
```

### 3. Process Daily Analytics
```python
import requests

# Trigger analytics for specific date
analytics_request = {"date": "2025-06-03"}
response = requests.post(
    "http://localhost:8000/analytics/process", 
    json=analytics_request
)
print(response.json())
```

## 🔐 Security Notes

- Database credentials are stored in `.env` file
- AWS credentials are stored in `.env` file
- WebSocket server accepts all connections (configure authentication for production)
- API has no authentication (add JWT/OAuth for production)
- CORS is enabled for all origins (restrict for production)

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Run `python test_system.py` to identify problems
3. Check service logs for detailed error messages
4. Verify all dependencies are installed correctly
