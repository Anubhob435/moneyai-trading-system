#!/usr/bin/env python3
"""
Real-Time Stock Data WebSocket Server
Simulates stock price updates and monitors for price changes
"""

import asyncio
import websockets
import json
import random
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Set
import asyncpg
import os
from dotenv import load_dotenv
from collections import defaultdict, deque

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockDataServer:
    def __init__(self):
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.subscriptions: Dict[websockets.WebSocketServerProtocol, Set[str]] = defaultdict(set)
        
        # Stock data storage
        self.current_prices: Dict[str, float] = {}
        self.price_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.minute_price_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=60))
        self.five_minute_history: Dict[str, List[Dict]] = defaultdict(list)
        
        # Monitoring data
        self.last_alert_time: Dict[str, datetime] = {}
        
        # Default stock tickers with realistic starting prices
        self.tickers = {
            "AAPL": 175.50,
            "GOOGL": 2650.00,
            "MSFT": 380.25,
            "TSLA": 845.30,
            "AMZN": 3200.75,
            "META": 485.60,
            "NFLX": 380.90,
            "NVDA": 875.40,
            "AMD": 165.80,
            "INTC": 58.25
        }
        
        # Initialize current prices
        self.current_prices = self.tickers.copy()
        
        # Database configuration
        self.db_config = {
            'host': os.getenv('DB_HOST'),
            'user': os.getenv('DB_USER'),
            'database': os.getenv('DB_NAME'),
            'password': os.getenv('DB_PASSWORD'),
            'port': os.getenv('DB_PORT')
        }
        
        # Running flags
        self.is_running = True
        self.db_available = True  # Track if database is available
        
    async def get_db_connection(self):
        """Get async database connection"""
        try:
            return await asyncpg.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            self.db_available = False
            return None
    async def register_client(self, websocket, path=None):
        """Register a new WebSocket client"""
        self.clients.add(websocket)
        logger.info(f"Client connected. Total clients: {len(self.clients)}")
        
        # Send current prices to new client
        await self.send_current_prices(websocket)
        
        try:
            # Listen for messages from this client
            async for message in websocket:
                await self.handle_client_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client disconnected")
        finally:
            await self.unregister_client(websocket)
    
    async def unregister_client(self, websocket):
        """Unregister a WebSocket client"""
        self.clients.discard(websocket)
        if websocket in self.subscriptions:
            del self.subscriptions[websocket]
        logger.info(f"Client disconnected. Total clients: {len(self.clients)}")
    
    async def handle_client_message(self, websocket, message):
        """Handle incoming messages from clients"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "subscribe":
                tickers = data.get("tickers", [])
                self.subscriptions[websocket].update(tickers)
                await self.send_message(websocket, {
                    "type": "subscription_confirmed",
                    "tickers": list(self.subscriptions[websocket]),
                    "timestamp": datetime.now().isoformat()
                })
                logger.info(f"Client subscribed to: {tickers}")
                
            elif message_type == "unsubscribe":
                tickers = data.get("tickers", [])
                for ticker in tickers:
                    self.subscriptions[websocket].discard(ticker)
                await self.send_message(websocket, {
                    "type": "unsubscription_confirmed",
                    "tickers": tickers,
                    "timestamp": datetime.now().isoformat()
                })
                
            elif message_type == "get_history":
                ticker = data.get("ticker")
                if ticker and ticker in self.price_history:
                    history_data = []
                    for i, price_data in enumerate(list(self.price_history[ticker])):
                        prev_price = list(self.price_history[ticker])[i-1]['price'] if i > 0 else price_data['price']
                        change_percent = ((price_data['price'] - prev_price) / prev_price) * 100
                        history_data.append({
                            "timestamp": price_data['timestamp'],
                            "price": price_data['price'],
                            "change_percent": change_percent
                        })
                    
                    await self.send_message(websocket, {
                        "type": "price_history",
                        "ticker": ticker,
                        "data": history_data[-20:],  # Last 20 entries
                        "timestamp": datetime.now().isoformat()
                    })
                    
        except json.JSONDecodeError:
            await self.send_message(websocket, {
                "type": "error",
                "message": "Invalid JSON format",
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error handling client message: {e}")
    
    async def send_message(self, websocket, message):
        """Send message to a specific client"""
        try:
            await websocket.send(json.dumps(message))
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Attempted to send message to closed connection")
        except Exception as e:
            logger.error(f"Error sending message: {e}")
    
    async def broadcast_message(self, message, target_tickers=None):
        """Broadcast message to all relevant clients"""
        if not self.clients:
            return
            
        # If target_tickers specified, only send to clients subscribed to those tickers
        target_clients = self.clients
        if target_tickers:
            target_clients = set()
            for client, subscribed_tickers in self.subscriptions.items():
                if any(ticker in subscribed_tickers for ticker in target_tickers):
                    target_clients.add(client)
                elif not subscribed_tickers:  # Clients with no specific subscriptions get all updates
                    target_clients.add(client)
        
        # Send to all target clients
        disconnected_clients = set()
        for client in target_clients:
            try:
                await client.send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            await self.unregister_client(client)
    
    async def send_current_prices(self, websocket):
        """Send current prices to a client"""
        message = {
            "type": "current_prices",
            "data": self.current_prices,
            "timestamp": datetime.now().isoformat()
        }
        await self.send_message(websocket, message)
    
    async def generate_price_updates(self):
        """Generate realistic price updates for stocks"""
        while self.is_running:
            try:
                updated_prices = {}
                current_time = datetime.now()
                
                for ticker, current_price in list(self.current_prices.items()):
                    # Generate realistic price movement (±2% typical range)
                    volatility = random.uniform(0.005, 0.02)  # 0.5% to 2% volatility
                    direction = random.choice([-1, 1])
                    change_percent = direction * volatility * random.uniform(0.1, 1.0)
                    
                    # Calculate new price
                    new_price = current_price * (1 + change_percent)
                    new_price = round(new_price, 2)
                    
                    # Store price data
                    price_data = {
                        "price": new_price,
                        "timestamp": current_time.isoformat(),
                        "change_percent": change_percent * 100
                    }
                    
                    self.current_prices[ticker] = new_price
                    self.price_history[ticker].append(price_data)
                    self.minute_price_history[ticker].append(price_data)
                    updated_prices[ticker] = new_price
                    
                    # Check for 2% price increase alerts
                    await self.check_price_alerts(ticker, new_price, current_price)
                
                # Broadcast price updates
                await self.broadcast_message({
                    "type": "price_update",
                    "data": updated_prices,
                    "timestamp": current_time.isoformat()
                })
                
                # Wait for next update (1-3 seconds for realistic feel)
                await asyncio.sleep(random.uniform(1, 3))
                
            except Exception as e:
                logger.error(f"Error generating price updates: {e}")
                await asyncio.sleep(5)
    
    async def check_price_alerts(self, ticker, new_price, previous_price):
        """Check for price increase alerts (>2% in 1 minute)"""
        try:
            current_time = datetime.now()
            
            # Check if we have enough data for 1-minute comparison
            minute_ago = current_time - timedelta(minutes=1)
            
            # Get price from 1 minute ago
            minute_old_price = None
            for price_data in reversed(list(self.minute_price_history[ticker])):
                price_time = datetime.fromisoformat(price_data["timestamp"].replace('Z', '+00:00').replace('+00:00', ''))
                if price_time <= minute_ago:
                    minute_old_price = price_data["price"]
                    break
            
            if minute_old_price is None:
                return  # Not enough data yet
            
            # Calculate percentage change over 1 minute
            change_percent = ((new_price - minute_old_price) / minute_old_price) * 100
            
            # Alert if increase is more than 2%
            if change_percent > 2.0:
                # Check if we already sent an alert recently (avoid spam)
                last_alert = self.last_alert_time.get(ticker)
                if last_alert is None or (current_time - last_alert).seconds > 60:
                    self.last_alert_time[ticker] = current_time
                    
                    alert_message = {
                        "type": "price_alert",
                        "ticker": ticker,
                        "change_percent": round(change_percent, 2),
                        "current_price": new_price,
                        "previous_price": minute_old_price,
                        "message": f"{ticker} increased by {change_percent:.2f}% in the last minute!",
                        "timestamp": current_time.isoformat()
                    }
                    
                    await self.broadcast_message(alert_message, [ticker])
                    logger.info(f"ALERT: {ticker} increased by {change_percent:.2f}% in 1 minute")
        
        except Exception as e:
            logger.error(f"Error checking price alerts for {ticker}: {e}")
    
    async def calculate_five_minute_averages(self):
        """Calculate and store 5-minute average prices"""
        while self.is_running:
            try:
                await asyncio.sleep(300)  # Wait 5 minutes
                
                current_time = datetime.now()
                five_minutes_ago = current_time - timedelta(minutes=5)
                
                # Try to get database connection, but don't fail if it's not available
                conn = None
                try:
                    conn = await self.get_db_connection()
                except Exception as db_error:
                    logger.warning(f"Database connection failed, skipping 5-minute averages: {db_error}")
                    continue
                
                if conn is None:
                    logger.warning("Cannot connect to database for 5-minute averages, skipping...")
                    continue
                
                for ticker in self.tickers.keys():
                    # Calculate average from price history
                    recent_prices = []
                    for price_data in self.price_history[ticker]:
                        price_time = datetime.fromisoformat(price_data["timestamp"].replace('Z', '+00:00').replace('+00:00', ''))
                        if price_time >= five_minutes_ago:
                            recent_prices.append(price_data["price"])
                    
                    if recent_prices:
                        avg_price = sum(recent_prices) / len(recent_prices)
                        
                        # Store in database (using existing table structure)
                        try:
                            # Insert into trading_api_trade as an average calculation record
                            query = """
                                INSERT INTO trading_api_trade 
                                (ticker, side, quantity, price, timestamp, user_id)
                                VALUES ($1, $2, $3, $4, $5, $6)
                            """
                            
                            await conn.execute(
                                query,
                                f"{ticker}_5MIN_AVG",  # Special ticker for averages
                                "average",  # Special side for averages
                                len(recent_prices),  # Number of data points
                                round(avg_price, 2),
                                current_time,
                                None  # No user ID for system calculations
                            )
                            
                            logger.info(f"Stored 5-minute average for {ticker}: ${avg_price:.2f}")
                            
                        except Exception as e:
                            logger.error(f"Error storing 5-minute average for {ticker}: {e}")
                            # Continue with other tickers even if database insert fails
                
                # Clean up database connection
                try:
                    if conn:
                        await conn.close()
                except Exception as close_error:
                    logger.warning(f"Error closing database connection: {close_error}")
                
            except Exception as e:
                logger.error(f"Error calculating 5-minute averages: {e}")
                # Clean up database connection in case of error
                try:
                    if 'conn' in locals() and conn:
                        await conn.close()
                except Exception:
                    pass
    
    async def cleanup_old_data(self):
        """Clean up old price history data periodically"""
        while self.is_running:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                current_time = datetime.now()
                cutoff_time = current_time - timedelta(hours=24)  # Keep 24 hours of data
                
                for ticker in self.price_history.keys():
                    # Remove old entries
                    filtered_history = deque(maxlen=100)
                    for price_data in self.price_history[ticker]:
                        price_time = datetime.fromisoformat(price_data["timestamp"].replace('Z', '+00:00').replace('+00:00', ''))
                        if price_time >= cutoff_time:
                            filtered_history.append(price_data)
                    
                    self.price_history[ticker] = filtered_history
                
                logger.info("Cleaned up old price history data")
                
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
    
    async def start_server(self, host="localhost", port=8765):
        """Start the WebSocket server"""
        logger.info(f"Starting WebSocket server on {host}:{port}")
        
        # Start background tasks
        asyncio.create_task(self.generate_price_updates())
        asyncio.create_task(self.calculate_five_minute_averages())
        asyncio.create_task(self.cleanup_old_data())
        
        # Start WebSocket server
        server = await websockets.serve(self.register_client, host, port)
        
        logger.info("🚀 WebSocket Stock Data Server is running!")
        logger.info(f"🔌 Connect to: ws://{host}:{port}")
        logger.info("📊 Monitoring tickers: " + ", ".join(self.tickers.keys()))
        logger.info("🚨 Alerts: >2% price increase in 1 minute")
        logger.info("📈 5-minute averages: Calculated and stored every 5 minutes")
        logger.info(f"💾 Database available: {self.db_available}")
        
        return server
    
    def stop_server(self):
        """Stop the server"""
        self.is_running = False
        logger.info("WebSocket server stopped")

async def main():
    """Main function to run the WebSocket server"""
    server_instance = StockDataServer()
    
    try:
        server = await server_instance.start_server()
        
        # Keep server running
        await server.wait_closed()
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        server_instance.stop_server()

if __name__ == "__main__":
    asyncio.run(main())
