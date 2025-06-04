# 📈 TradeOps: Real-Time Stock Trading API and Analytics System

A comprehensive Python-based stock trading system featuring REST APIs, real-time WebSocket monitoring, algorithmic trading strategies, background processing, and AWS cloud analytics integration.

---

## 📌 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
- [API Endpoints](#api-endpoints)
- [Trading Algorithm](#trading-algorithm)
- [Real-Time Monitoring](#real-time-monitoring)
- [AWS Integration](#aws-integration)
- [Demo Instructions](#demo-instructions)
- [License](#license)

---

## 🚀 Features

### 1. FastAPI REST API
- ✅ Comprehensive trade management with CRUD operations
- ✅ Real-time stock price updates via WebSocket endpoints
- ✅ Trading algorithm integration with JSON responses
- ✅ AWS Lambda proxy endpoints for serverless analytics
- ✅ Interactive API documentation with Swagger UI
- ✅ CORS support for frontend integration

### 2. Algorithmic Trading System
- ✅ **Moving Average Crossover Strategy** (50-day vs 200-day MA)
- ✅ Multi-ticker portfolio simulation
- ✅ Comprehensive trade logging and P&L calculation
- ✅ Performance analytics with win rates and returns
- ✅ Interactive plotting with buy/sell signal visualization
- ✅ CSV data import/export functionality

### 3. Real-Time Stock Monitoring
- ✅ WebSocket server simulating live market data for 10+ tickers
- ✅ Price alerts when stocks increase >2% in 1 minute
- ✅ 5-minute average price calculations
- ✅ Multi-client WebSocket support with broadcasting
- ✅ Realistic price simulation with volatility modeling

### 4. AWS Cloud Integration
- ✅ S3 integration for trade data storage and retrieval
- ✅ Lambda function proxy for serverless analytics
- ✅ Automated data processing pipelines
- ✅ Environment-based configuration management

### 5. Background Processing
- ✅ Celery + Redis task queue implementation
- ✅ Asynchronous data processing
- ✅ Scheduled tasks for price calculations
- ✅ Error handling and retry mechanisms

---

## 🧰 Tech Stack

| Component | Technology Stack |
|-----------|------------------|
| **Backend API** | FastAPI, Pydantic, SQLAlchemy |
| **Database** | PostgreSQL with async support |
| **Real-Time** | WebSockets, asyncio |
| **Task Queue** | Celery + Redis |
| **Cloud Services** | AWS S3, Lambda, API Gateway |
| **Trading Engine** | pandas, numpy, matplotlib |
| **Environment** | Python 3.12+, dotenv configuration |

---

## 🏗️ Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                    TradeOps System Architecture             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐    ┌──────────────────┐                │
│  │   Frontend      │◄──►│   FastAPI        │                │
│  │   (Web/Mobile)  │    │   REST API       │                │
│  └─────────────────┘    └──────┬───────────┘                │
│                                │                            │
│  ┌─────────────────┐           │   ┌──────────────────┐     │
│  │   WebSocket     │◄──────────┼──►│   PostgreSQL     │     │
│  │   Real-time     │           │   │   Database       │     │
│  │   Monitor       │           │   └──────────────────┘     │
│  └─────────────────┘           │                            │
│                                │                            │
│  ┌─────────────────┐           │   ┌──────────────────┐     │
│  │   Trading       │◄──────────┼──►│   Celery +       │     │
│  │   Algorithm     │           │   │   Redis Queue    │     │
│  │   Engine        │           │   └──────────────────┘     │
│  └─────────────────┘           │                            │
│                                │                            │
│  ┌─────────────────┐           │   ┌──────────────────┐     │
│  │   AWS Lambda    │◄──────────┴──►│   AWS S3         │     │
│  │   Analytics     │               │   Data Storage   │     │
│  └─────────────────┘               └──────────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
moneyai-trading-system/
├── api-app.py                    # Main FastAPI application
├── realtime-monitor.py           # WebSocket stock monitoring
├── test-system.py               # System integration tests
├── trading-algorithim/          # Trading strategy implementation
│   ├── algorithim.py            # Moving average crossover strategy
│   ├── strategy_plot.py         # Trading visualization
│   └── sample-generator.py      # Sample data generation
├── .env                         # Environment configuration
├── requirements.txt             # Python dependencies
└── README.md                    # Project documentation
```

---

## 🛠️ Setup Instructions

### 1. Clone Repository
```bash
git clone <your-repository-url>
cd moneyai-trading-system
```

### 2. Create Virtual Environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create a `.env` file with your configurations:
```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=tradeops
DB_USER=your_username
DB_PASSWORD=your_password

# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=your_region
S3_BUCKET_NAME=your_bucket

# Lambda API
LAMBDA_API_URL=https://your-lambda-url.amazonaws.com/default/moneyai
```

### 5. Database Setup
```bash
# Install PostgreSQL and create database
createdb tradeops
```

### 6. Start Services
```bash
# Start Redis (for Celery)
redis-server

# Start FastAPI server
uvicorn api-app:app --reload --host 0.0.0.0 --port 8000

# Start WebSocket monitor (separate terminal)
python realtime-monitor.py

# Start Celery worker (separate terminal)
celery -A api-app.celery_app worker --loglevel=info
```

---

## 📡 API Endpoints

### Core Trading Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | System overview and available endpoints |
| `GET` | `/health` | Health check endpoint |
| `POST` | `/trades/` | Create new trade entry |
| `GET` | `/trades/` | Retrieve trades with filtering |
| `GET` | `/trades/stats` | Trading statistics and analytics |

### Algorithm Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/algorithm/run` | Execute trading algorithm with custom CSV |
| `GET` | `/algorithm/sample` | Run algorithm with sample data |
| `GET` | `/algorithm/help` | Algorithm documentation and usage |

### Analytics & Integration
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/analytics/process` | Trigger analytics processing |
| `GET` | `/tickers/{ticker}/average` | Get ticker price averages |
| `POST` | `/moneyai` | AWS Lambda proxy endpoint |
| `WebSocket` | `/ws` | Real-time data streaming |

### Example API Usage
```bash
# Get system overview
curl -X GET "http://localhost:8000/"

# Run trading algorithm
curl -X GET "http://localhost:8000/algorithm/sample"

# Create a trade
curl -X POST "http://localhost:8000/trades/" \
     -H "Content-Type: application/json" \
     -d '{"ticker": "AAPL", "quantity": 100, "price": 150.25, "trade_type": "BUY"}'
```

---

## 🤖 Trading Algorithm

### Moving Average Crossover Strategy
- **Strategy**: 50-day MA crosses above/below 200-day MA
- **Buy Signal**: 50-day MA crosses above 200-day MA
- **Sell Signal**: 50-day MA crosses below 200-day MA
- **Multi-Ticker**: Supports portfolio-wide analysis

### Sample Results
```json
{
  "status": "success",
  "total_initial_investment": 90000.0,
  "overall_profit_loss": 5358.20,
  "overall_return_percentage": 5.95,
  "summary": {
    "profitable_tickers": 3,
    "losing_tickers": 1,
    "win_rate_percentage": 75.0
  }
}
```

### Usage
```bash
# Generate sample data
python trading-algorithim/sample-generator.py

# Run algorithm with plotting
python trading-algorithim/strategy_plot.py

# Execute via API
curl -X GET "http://localhost:8000/algorithm/sample"
```

---

## 🔄 Real-Time Monitoring

### WebSocket Features
- **Live Price Updates**: 10 major stocks (AAPL, GOOGL, MSFT, etc.)
- **Price Alerts**: Notifications for >2% price increases
- **Multi-Client Support**: Broadcasting to multiple connections
- **Error Handling**: Robust connection management

### Start Monitoring
```bash
python realtime-monitor.py
```

### Sample Output
```
🚀 WebSocket server started on ws://localhost:8765
📊 Broadcasting to 2 clients: AAPL: $155.23 (+1.85%)
🚨 PRICE ALERT: TSLA increased by 2.15% in the last minute!
💰 5-min average for MSFT: $284.56
```

---

## ☁️ AWS Integration

### S3 Data Structure
```
your-s3-bucket/
├── trades/
│   └── 2025/01/15/trades_2025-01-15.csv
└── analytics/
    └── 2025/01/15/analysis_2025-01-15.csv
```

### Lambda Function Features
- **Automated Processing**: Triggered via API Gateway
- **Data Analysis**: Volume and price calculations
- **S3 Integration**: Read/write CSV files
- **Error Handling**: Comprehensive logging

---

## 🎬 Demo Instructions

### Quick Start Demo
```bash
# 1. Start all services
python realtime-monitor.py &
uvicorn api-app:app --reload &

# 2. Test system health
python test-system.py

# 3. Run trading algorithm
curl -X GET "http://localhost:8000/algorithm/sample"

# 4. View API documentation
# Open: http://localhost:8000/docs
```

### Demo Highlights
- ✅ Interactive API documentation
- ✅ Real-time WebSocket price updates
- ✅ Trading algorithm execution with results
- ✅ AWS cloud integration
- ✅ Comprehensive error handling

---

## 🧪 Testing

### Run System Tests
```bash
python test-system.py
```

### Test Coverage
- ✅ API endpoint functionality
- ✅ WebSocket connectivity
- ✅ Database operations
- ✅ Trading algorithm accuracy
- ✅ AWS service integration

---

