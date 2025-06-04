import requests
import asyncio
import websockets
import json
import time
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TradeOpsTests:
    def __init__(self):
        self.api_base = "http://localhost:8000"
        self.ws_uri = "ws://localhost:8765"
        
    def test_api_health(self):
        """Test API health endpoint"""
        try:
            response = requests.get(f"{self.api_base}/health", timeout=5)
            if response.status_code == 200:
                logger.info("✅ API health check passed")
                return True
            else:
                logger.error(f"❌ API health check failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ API health check failed: {e}")
            return False
    
    def test_api_root(self):
        """Test API root endpoint"""
        try:
            response = requests.get(f"{self.api_base}/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ API root endpoint working")
                logger.info(f"   Version: {data.get('version')}")
                return True
            else:
                logger.error(f"❌ API root endpoint failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ API root endpoint failed: {e}")
            return False
    
    def test_create_trade(self):
        """Test creating a trade"""
        try:
            trade_data = {
                "ticker": "AAPL",
                "side": "buy",
                "quantity": 100,
                "price": 150.50,
                "user_id": 1
            }
            
            response = requests.post(
                f"{self.api_base}/trades/",
                json=trade_data,
                timeout=10
            )
            
            if response.status_code == 200:
                trade = response.json()
                logger.info("✅ Trade creation successful")
                logger.info(f"   Trade ID: {trade.get('id')}")
                logger.info(f"   Ticker: {trade.get('ticker')}")
                return True
            else:
                logger.error(f"❌ Trade creation failed: {response.status_code}")
                logger.error(f"   Response: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Trade creation failed: {e}")
            return False
    
    def test_get_trades(self):
        """Test retrieving trades"""
        try:
            response = requests.get(f"{self.api_base}/trades/", timeout=5)
            if response.status_code == 200:
                trades = response.json()
                logger.info(f"✅ Trade retrieval successful ({len(trades)} trades)")
                return True
            else:
                logger.error(f"❌ Trade retrieval failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Trade retrieval failed: {e}")
            return False
    
    def test_trade_stats(self):
        """Test trade statistics"""
        try:
            response = requests.get(f"{self.api_base}/trades/stats", timeout=5)
            if response.status_code == 200:
                stats = response.json()
                logger.info("✅ Trade statistics working")
                logger.info(f"   Total trades: {stats.get('total_trades')}")
                logger.info(f"   Unique tickers: {stats.get('unique_tickers')}")
                return True
            else:
                logger.error(f"❌ Trade statistics failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Trade statistics failed: {e}")
            return False
    
    async def test_websocket_connection(self):
        """Test WebSocket connection"""
        try:
            async with websockets.connect(self.ws_uri) as websocket:
                # Wait for initial message
                message = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(message)
                
                if data.get("type") == "current_prices":
                    logger.info("✅ WebSocket connection successful")
                    logger.info(f"   Received prices for {len(data.get('data', {}))} tickers")
                    return True
                else:
                    logger.error("❌ WebSocket: unexpected initial message")
                    return False
                    
        except asyncio.TimeoutError:
            logger.error("❌ WebSocket connection timeout")
            return False
        except Exception as e:
            logger.error(f"❌ WebSocket connection failed: {e}")
            return False
    
    async def test_websocket_subscription(self):
        """Test WebSocket subscription functionality"""
        try:
            async with websockets.connect(self.ws_uri) as websocket:
                # Subscribe to specific tickers
                subscribe_msg = {
                    "type": "subscribe",
                    "tickers": ["AAPL", "GOOGL"]
                }
                await websocket.send(json.dumps(subscribe_msg))
                
                # Wait for confirmation
                message = await asyncio.wait_for(websocket.recv(), timeout=5)
                # Skip current_prices message
                if json.loads(message).get("type") == "current_prices":
                    message = await asyncio.wait_for(websocket.recv(), timeout=5)
                
                data = json.loads(message)
                if data.get("type") == "subscription_confirmed":
                    logger.info("✅ WebSocket subscription working")
                    return True
                else:
                    logger.error("❌ WebSocket subscription failed")
                    return False
                    
        except asyncio.TimeoutError:
            logger.error("❌ WebSocket subscription timeout")
            return False
        except Exception as e:
            logger.error(f"❌ WebSocket subscription failed: {e}")
            return False
    
    def test_s3_analytics(self):
        """Test S3 analytics functionality"""
        try:
            # Test with today's date
            today = datetime.now().strftime("%Y-%m-%d")
            analytics_data = {"date": today}
            
            response = requests.post(
                f"{self.api_base}/analytics/process",
                json=analytics_data,
                timeout=30  # Analytics might take longer
            )
            
            if response.status_code in [200, 404]:  # 404 is OK if no data exists
                if response.status_code == 200:
                    logger.info("✅ S3 analytics processing successful")
                else:
                    logger.info("✅ S3 analytics endpoint working (no data for today)")
                return True
            else:
                logger.error(f"❌ S3 analytics failed: {response.status_code}")
                logger.error(f"   Response: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ S3 analytics failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("🧪 TradeOps System Tests")
        print("=" * 50)
        
        tests = [
            ("API Health Check", self.test_api_health),
            ("API Root Endpoint", self.test_api_root),
            ("Create Trade", self.test_create_trade),
            ("Get Trades", self.test_get_trades),
            ("Trade Statistics", self.test_trade_stats),
            ("S3 Analytics", self.test_s3_analytics),
        ]
        
        # Async tests
        async_tests = [
            ("WebSocket Connection", self.test_websocket_connection),
            ("WebSocket Subscription", self.test_websocket_subscription),
        ]
        
        passed = 0
        total = len(tests) + len(async_tests)
        
        # Run sync tests
        for test_name, test_func in tests:
            print(f"\n🔍 Testing {test_name}...")
            try:
                if test_func():
                    passed += 1
            except Exception as e:
                logger.error(f"❌ {test_name} threw exception: {e}")
        
        # Run async tests
        async def run_async_tests():
            nonlocal passed
            for test_name, test_func in async_tests:
                print(f"\n🔍 Testing {test_name}...")
                try:
                    if await test_func():
                        passed += 1
                except Exception as e:
                    logger.error(f"❌ {test_name} threw exception: {e}")
        
        asyncio.run(run_async_tests())
        
        # Summary
        print(f"\n" + "=" * 50)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        print("=" * 50)
        
        if passed == total:
            print("🎉 All tests passed! TradeOps system is working correctly.")
            return True
        else:
            print(f"⚠️  {total - passed} tests failed. Please check the logs above.")
            return False

def main():
    """Main function"""
    tester = TradeOpsTests()
    
    print("⏳ Waiting for services to start up...")
    time.sleep(5)  # Give services time to start
    
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ System is ready for use!")
        print("\nNext steps:")
        print("1. Open http://localhost:8000/docs for API documentation")
        print("2. Run 'python realtime_monitor.py' for live monitoring")
        print("3. Run 'python s3_analytics.py' for analytics processing")
    else:
        print("\n❌ Some tests failed. Please check service logs.")

if __name__ == "__main__":
    main()
