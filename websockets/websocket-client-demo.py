#!/usr/bin/env python3
"""
Stock Data WebSocket Client
Demonstrates real-time stock monitoring with price alerts
"""

import asyncio
import websockets
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockMonitorClient:
    def __init__(self, uri="ws://localhost:8765"):
        self.uri = uri
        self.websocket = None
        self.running = False
        
    async def connect(self):
        """Connect to the WebSocket server"""
        try:
            self.websocket = await websockets.connect(self.uri)
            self.running = True
            logger.info(f"✅ Connected to stock data server at {self.uri}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the WebSocket server"""
        self.running = False
        if self.websocket:
            await self.websocket.close()
            logger.info("Disconnected from server")
    
    async def subscribe_to_tickers(self, tickers):
        """Subscribe to specific stock tickers"""
        if self.websocket:
            message = {
                "type": "subscribe",
                "tickers": tickers
            }
            await self.websocket.send(json.dumps(message))
            logger.info(f"📊 Subscribed to: {', '.join(tickers)}")
    
    async def get_price_history(self, ticker):
        """Request price history for a ticker"""
        if self.websocket:
            message = {
                "type": "get_history",
                "ticker": ticker
            }
            await self.websocket.send(json.dumps(message))
    
    async def listen_for_messages(self):
        """Listen for incoming messages"""
        try:
            while self.running and self.websocket:
                try:
                    # Set a timeout to prevent indefinite waiting
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=30.0)
                    data = json.loads(message)
                    await self.handle_message(data)
                except asyncio.TimeoutError:
                    # Send a ping to keep connection alive
                    if self.websocket:
                        await self.websocket.ping()
                    continue
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")
        except Exception as e:
            logger.error(f"Error listening for messages: {e}")
        finally:
            self.running = False
    
    async def handle_message(self, data):
        """Handle incoming WebSocket messages"""
        message_type = data.get("type")
        timestamp = data.get("timestamp", "")
        
        if message_type == "current_prices":
            print(f"\n📈 Current Stock Prices ({timestamp}):")
            print("-" * 50)
            for ticker, price in data["data"].items():
                print(f"  {ticker:6} : ${price:8.2f}")
                
        elif message_type == "price_update":
            print(f"\n🔄 Price Update ({timestamp}):")
            for ticker, price in data["data"].items():
                print(f"  {ticker:6} : ${price:8.2f}")
                
        elif message_type == "price_alert":
            print(f"\n🚨 {'='*60}")
            print(f"🚨 PRICE ALERT! 🚨")
            print(f"🚨 {'='*60}")
            print(f"📊 Ticker: {data['ticker']}")
            print(f"📈 Change: +{data['change_percent']:.2f}% in 1 minute")
            print(f"💰 Current Price: ${data['current_price']:.2f}")
            print(f"💰 Previous Price: ${data['previous_price']:.2f}")
            print(f"⏰ Time: {data['timestamp']}")
            print(f"📝 {data['message']}")
            print(f"🚨 {'='*60}")
            
        elif message_type == "subscription_confirmed":
            print(f"✅ Subscription confirmed for: {', '.join(data.get('tickers', []))}")
            
        elif message_type == "price_history":
            print(f"\n📊 Price History for {data['ticker']}:")
            print("-" * 60)
            for entry in data["data"][-10:]:  # Show last 10 entries
                change_symbol = "📈" if entry['change_percent'] >= 0 else "📉"
                print(f"  {entry['timestamp'][:19]} | ${entry['price']:8.2f} | {change_symbol} {entry['change_percent']:+6.2f}%")
                
        elif message_type == "error":
            print(f"❌ Error: {data.get('message', 'Unknown error')}")
    
    async def interactive_demo(self):
        """Run an interactive demo of the WebSocket client"""
        # Connect to server
        if not await self.connect():
            return
        
        print("\n🚀 Stock Data Monitor Started!")
        print("=" * 60)
        print("📊 Real-time stock price monitoring")
        print("🚨 Alerts for price increases >2% in 1 minute")
        print("📈 5-minute average calculations")
        print("🛑 Press Ctrl+C to stop monitoring")
        print("=" * 60)
        
        # Subscribe to popular stocks
        popular_tickers = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]
        await self.subscribe_to_tickers(popular_tickers)
        
        # Start listening for messages
        try:
            # Create a task for listening to messages
            listen_task = asyncio.create_task(self.listen_for_messages())
            
            # Wait for the task to complete or be interrupted
            await listen_task
            
        except KeyboardInterrupt:
            print("\n\n👋 Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Demo error: {e}")
        finally:
            await self.disconnect()
    
    async def test_specific_features(self):
        """Test specific WebSocket features"""
        if not await self.connect():
            return
        
        try:
            print("\n🧪 Testing WebSocket Features...")
            
            # Test 1: Get current prices
            print("\n1️⃣ Getting current prices...")
            await asyncio.sleep(2)
            
            # Test 2: Subscribe to specific tickers
            print("\n2️⃣ Subscribing to AAPL and GOOGL...")
            await self.subscribe_to_tickers(["AAPL", "GOOGL"])
            await asyncio.sleep(3)
            
            # Test 3: Get price history
            print("\n3️⃣ Getting price history for AAPL...")
            await self.get_price_history("AAPL")
            await asyncio.sleep(2)
            
            # Test 4: Monitor for alerts
            print("\n4️⃣ Monitoring for price alerts (wait for natural price movements)...")
            print("   This may take a few minutes depending on market simulation...")
            
            # Listen for messages for a while
            await asyncio.sleep(30)  # Monitor for 30 seconds
            
        except KeyboardInterrupt:
            print("\n\n👋 Testing stopped by user")
        except Exception as e:
            logger.error(f"Test error: {e}")
        finally:
            await self.disconnect()

async def main():
    """Main function with menu options"""
    client = StockMonitorClient()
    
    print("🔌 Stock Data WebSocket Client")
    print("=" * 40)
    print("1. Interactive Demo (recommended)")
    print("2. Feature Testing")
    print("3. Exit")
    
    try:
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            await client.interactive_demo()
        elif choice == "2":
            await client.test_specific_features()
        elif choice == "3":
            print("👋 Goodbye!")
        else:
            print("❌ Invalid choice")
            
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"Client error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
