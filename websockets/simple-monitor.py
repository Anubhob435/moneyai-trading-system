#!/usr/bin/env python3
"""
Simple WebSocket Client for Monitoring Price Alerts
"""

import asyncio
import websockets
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def monitor_alerts():
    """Monitor for price alerts continuously"""
    uri = "ws://localhost:8765"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🔌 Connected to stock data server")
            print("🚨 Monitoring for price alerts...")
            print("📊 Press Ctrl+C to stop\n")
            
            # Subscribe to all tickers for alerts
            subscribe_msg = {
                "type": "subscribe",
                "tickers": ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "META", "NFLX", "NVDA", "AMD", "INTC"]
            }
            await websocket.send(json.dumps(subscribe_msg))
            
            # Listen for messages
            async for message in websocket:
                data = json.loads(message)
                
                if data.get("type") == "price_alert":
                    print(f"🚨 ALERT! {data['ticker']} increased {data['change_percent']:.2f}% to ${data['current_price']:.2f}")
                elif data.get("type") == "subscription_confirmed":
                    print(f"✅ Subscribed to: {', '.join(data.get('tickers', []))}")
                elif data.get("type") == "current_prices":
                    print("📈 Received current prices")
                elif data.get("type") == "price_update":
                    # Show a simple progress indicator
                    print(".", end="", flush=True)
                    
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(monitor_alerts())
