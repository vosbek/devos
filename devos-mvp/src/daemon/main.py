#!/usr/bin/env python3
"""
DevOS Main Daemon - LLM-powered OS interaction service
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Optional

import uvicorn
from contextlib import asynccontextmanager

from .api import create_app
from .config import Config
from ..context.file_monitor import FileMonitor
from ..context.process_monitor import ProcessMonitor
from ..context.git_monitor import GitMonitor
from ..llm.bedrock_client import BedrockClient
from ..approval.manager import ApprovalManager

class DevOSDaemon:
    """Main daemon service for DevOS"""
    
    def __init__(self, config_path: str = "/etc/devos/daemon.yaml"):
        self.config = Config.load_from_file(config_path)
        self.running = False
        self.services = {}
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, self.config.log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/var/log/devos/daemon.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    async def start_services(self):
        """Initialize and start all daemon services"""
        try:
            # Initialize LLM client
            self.services['bedrock'] = BedrockClient(
                region=self.config.aws_region,
                access_key=self.config.aws_access_key,
                secret_key=self.config.aws_secret_key
            )
            
            # Initialize context monitors
            self.services['file_monitor'] = FileMonitor(
                watch_paths=self.config.watch_paths
            )
            self.services['process_monitor'] = ProcessMonitor(
                update_interval=self.config.process_update_interval
            )
            self.services['git_monitor'] = GitMonitor(
                repo_paths=self.config.git_repo_paths
            )
            
            # Initialize approval manager
            self.services['approval_manager'] = ApprovalManager(
                config=self.config.approval_config
            )
            
            # Start all monitors
            for service_name, service in self.services.items():
                if hasattr(service, 'start'):
                    await service.start()
                    self.logger.info(f"Started {service_name}")
                    
            # Create FastAPI app
            self.app = create_app(self.services, self.config)
            
            self.logger.info("All services started successfully")
            self.running = True
            
        except Exception as e:
            self.logger.error(f"Failed to start services: {e}")
            await self.stop_services()
            raise
            
    async def stop_services(self):
        """Stop all daemon services"""
        self.running = False
        
        for service_name, service in self.services.items():
            try:
                if hasattr(service, 'stop'):
                    await service.stop()
                    self.logger.info(f"Stopped {service_name}")
            except Exception as e:
                self.logger.error(f"Error stopping {service_name}: {e}")
                
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, shutting down...")
            asyncio.create_task(self.stop_services())
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
    async def run(self):
        """Main run loop"""
        await self.start_services()
        
        # Start the web server
        config = uvicorn.Config(
            self.app,
            host=self.config.api_host,
            port=self.config.api_port,
            loop="asyncio"
        )
        server = uvicorn.Server(config)
        
        self.logger.info(f"DevOS daemon running on {self.config.api_host}:{self.config.api_port}")
        
        try:
            await server.serve()
        except Exception as e:
            self.logger.error(f"Server error: {e}")
        finally:
            await self.stop_services()

async def main():
    """Main entry point"""
    daemon = DevOSDaemon()
    daemon.setup_signal_handlers()
    
    try:
        await daemon.run()
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())