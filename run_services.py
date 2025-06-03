#!/usr/bin/env python
"""
TradeOps Service Manager
Manages all TradeOps services: API, WebSocket, Celery, and Analytics
"""

import subprocess
import sys
import time
import signal
import os
from pathlib import Path
import threading
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ServiceManager:
    def __init__(self):
        self.processes = {}
        self.running = True
        self.base_dir = Path(__file__).parent
        
    def start_service(self, name, command, cwd=None):
        """Start a service with the given command"""
        try:
            if cwd is None:
                cwd = self.base_dir
                
            logger.info(f"Starting {name}...")
            
            # Use PowerShell for Windows
            if sys.platform == "win32":
                # Activate virtual environment and run command
                full_command = f"cd '{cwd}'; .\\venv\\Scripts\\Activate.ps1; {command}"
                process = subprocess.Popen(
                    ["powershell", "-Command", full_command],
                    cwd=cwd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                # Unix-like systems
                full_command = f"source venv/bin/activate && {command}"
                process = subprocess.Popen(
                    ["bash", "-c", full_command],
                    cwd=cwd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            
            self.processes[name] = process
            logger.info(f"✅ {name} started (PID: {process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start {name}: {e}")
            return False
    
    def stop_service(self, name):
        """Stop a specific service"""
        if name in self.processes:
            process = self.processes[name]
            try:
                if sys.platform == "win32":
                    process.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    process.terminate()
                
                process.wait(timeout=10)
                logger.info(f"✅ {name} stopped")
                del self.processes[name]
                
            except subprocess.TimeoutExpired:
                logger.warning(f"Force killing {name}...")
                process.kill()
                del self.processes[name]
            except Exception as e:
                logger.error(f"Error stopping {name}: {e}")
    
    def stop_all_services(self):
        """Stop all running services"""
        logger.info("Stopping all services...")
        for name in list(self.processes.keys()):
            self.stop_service(name)
        logger.info("All services stopped")
    
    def check_service_status(self, name):
        """Check if a service is running"""
        if name in self.processes:
            process = self.processes[name]
            return process.poll() is None
        return False
    
    def monitor_services(self):
        """Monitor services and restart if they crash"""
        while self.running:
            for name, process in list(self.processes.items()):
                if process.poll() is not None:
                    logger.warning(f"⚠️ {name} has stopped unexpectedly")
                    del self.processes[name]
            
            time.sleep(5)
    
    def start_all_services(self):
        """Start all TradeOps services"""
        logger.info("🚀 Starting TradeOps System...")
        
        services = [
            {
                "name": "FastAPI Server",
                "command": "python api-app.py",
                "wait": 2
            },
            {
                "name": "WebSocket Server", 
                "command": "python websocket-server.py",
                "wait": 2
            },
            {
                "name": "Celery Worker",
                "command": "celery -A celery_tasks worker --loglevel=info --pool=solo",
                "wait": 3
            },
            {
                "name": "Celery Beat",
                "command": "celery -A celery_tasks beat --loglevel=info",
                "wait": 2
            }
        ]
        
        for service in services:
            success = self.start_service(service["name"], service["command"])
            if not success:
                logger.error(f"Failed to start {service['name']}")
                self.stop_all_services()
                return False
            
            # Wait before starting next service
            time.sleep(service["wait"])
        
        logger.info("✅ All services started successfully!")
        
        # Print service URLs
        print("\n" + "=" * 60)
        print("🎉 TradeOps System is Running!")
        print("=" * 60)
        print("📡 FastAPI Server:     http://localhost:8000")
        print("📡 API Documentation:  http://localhost:8000/docs")
        print("🔌 WebSocket Server:   ws://localhost:8765")
        print("⚙️  Celery Worker:     Running background tasks")
        print("⏰ Celery Beat:       Running scheduled tasks")
        print("=" * 60)
        print("\nPress Ctrl+C to stop all services")
        print("\nQuick Commands:")
        print("  - Test API: curl http://localhost:8000/health")
        print("  - Monitor: python realtime_monitor.py")
        print("  - Analytics: python s3_analytics.py")
        print("=" * 60)
        
        return True

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    logger.info("Received shutdown signal...")
    manager.running = False
    manager.stop_all_services()
    sys.exit(0)

def check_dependencies():
    """Check if required dependencies are available"""
    logger.info("Checking dependencies...")
    
    required_files = [
        "api-app.py",
        "websocket-server.py", 
        "celery_tasks.py",
        ".env"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        logger.error(f"Missing required files: {missing_files}")
        return False
    
    # Check if virtual environment exists
    venv_path = Path("venv")
    if not venv_path.exists():
        logger.error("Virtual environment not found. Please create it first.")
        return False
    
    logger.info("✅ All dependencies found")
    return True

def main():
    """Main function"""
    global manager
    
    print("🔧 TradeOps Service Manager")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        logger.error("❌ Dependency check failed")
        sys.exit(1)
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)
    
    # Create service manager
    manager = ServiceManager()
    
    # Start monitoring thread
    monitor_thread = threading.Thread(target=manager.monitor_services, daemon=True)
    monitor_thread.start()
    
    try:
        # Start all services
        if manager.start_all_services():
            # Keep running until interrupted
            while manager.running:
                time.sleep(1)
        else:
            logger.error("❌ Failed to start services")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        manager.stop_all_services()

if __name__ == "__main__":
    main()
