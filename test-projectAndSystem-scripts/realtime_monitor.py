import asyncio
import websockets
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TradingMonitorClient:
    def __init__(self, uri="ws://localhost:8765"):
        self.uri = uri
        self.websocket = None
        self.is_running = False
        
    async def connect(self):
        """Connect to WebSocket server"""
        try:
            self.websocket = await websockets.connect(self.uri)
            self.is_running = True
            logger.info(f"Connected to WebSocket server at {self.uri}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket server: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from WebSocket server"""
        self.is_running = False
        if self.websocket:
            await self.websocket.close()
            logger.info("Disconnected from WebSocket server")
    
    async def subscribe_to_tickers(self, tickers):
        """Subscribe to specific stock tickers"""
        if self.websocket:
            message = {
                "type": "subscribe",
                "tickers": tickers
            }
            await self.websocket.send(json.dumps(message))
            logger.info(f"Subscribed to tickers: {tickers}")
    
    async def get_price_history(self, ticker):
        """Request price history for a ticker"""
        if self.websocket:
            message = {
                "type": "get_history",
                "ticker": ticker
            }
            await self.websocket.send(json.dumps(message))
    
    async def listen_for_messages(self):
        """Listen for incoming messages from WebSocket server"""
        try:
            while self.is_running and self.websocket:
                message = await self.websocket.recv()
                data = json.loads(message)
                await self.handle_message(data)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")
        except json.JSONDecodeError:
            logger.error("Received invalid JSON message")
        except Exception as e:
            logger.error(f"Error listening for messages: {e}")
    
    async def handle_message(self, data):
        """Handle incoming WebSocket messages"""
        message_type = data.get("type")
        
        if message_type == "current_prices":
            logger.info("Received current prices:")
            for ticker, price in data["data"].items():
                print(f"  {ticker}: ${price:.2f}")
                
        elif message_type == "price_update":
            print(f"\n📈 Price Update - {data['timestamp']}")
            for ticker, price in data["data"].items():
                print(f"  {ticker}: ${price:.2f}")
                
        elif message_type == "price_alert":
            print(f"\n🚨 PRICE ALERT! 🚨")
            print(f"  {data['message']}")
            print(f"  Ticker: {data['ticker']}")
            print(f"  Change: {data['change_percent']:.2f}%")
            print(f"  Current Price: ${data['current_price']:.2f}")
            print(f"  Previous Price: ${data['previous_price']:.2f}")
            print(f"  Time: {data['timestamp']}")
            
        elif message_type == "subscription_confirmed":
            logger.info(f"Subscription confirmed for: {data.get('tickers', [])}")
            
        elif message_type == "price_history":
            print(f"\n📊 Price History for {data['ticker']}:")
            for entry in data["data"]:
                print(f"  {entry['timestamp']}: ${entry['price']:.2f} ({entry['change_percent']:+.2f}%)")
    
    async def run_monitor(self, tickers=None):
        """Run the monitoring client"""
        if not await self.connect():
            return
        
        # Subscribe to specific tickers if provided
        if tickers:
            await self.subscribe_to_tickers(tickers)
        
        # Start listening for messages
        await self.listen_for_messages()

async def main():
    """Main function"""
    print("🚀 TradeOps Real-Time Stock Monitor")
    print("=" * 50)
    
    # Default tickers to monitor
    default_tickers = ["AAPL", "GOOGL", "MSFT", "TSLA"]
    
    client = TradingMonitorClient()
    
    try:
        await client.run_monitor(default_tickers)
    except KeyboardInterrupt:
        print("\n\n👋 Monitoring stopped by user")
    except Exception as e:
        logger.error(f"Monitor error: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
