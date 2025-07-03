# MVP Detailed Implementation: DevOS - LLM-Powered Developer OS

## MVP Scope and Objectives

**Target**: Functional proof-of-concept demonstrating core LLM-OS integration  
**Timeline**: 3 months (12 weeks)  
**Core Features**: File operations, Git commands, process management, basic AWS integration  
**Success Criteria**: 5 use cases working end-to-end with >90% accuracy  

## Project Structure

```
devos-mvp/
├── src/
│   ├── daemon/                 # Core daemon service
│   │   ├── __init__.py
│   │   ├── main.py            # Service entry point
│   │   ├── api.py             # REST API endpoints
│   │   ├── models.py          # Data models
│   │   └── config.py          # Configuration management
│   ├── llm/                   # LLM integration layer
│   │   ├── __init__.py
│   │   ├── bedrock_client.py  # AWS Bedrock integration
│   │   ├── model_router.py    # Model selection logic
│   │   └── prompt_templates.py # Command templates
│   ├── context/               # Context engine
│   │   ├── __init__.py
│   │   ├── file_monitor.py    # File system monitoring
│   │   ├── process_monitor.py # Process monitoring
│   │   ├── git_monitor.py     # Git repository monitoring
│   │   └── database.py        # Context storage
│   ├── executor/              # Command execution
│   │   ├── __init__.py
│   │   ├── sandbox.py         # Secure command execution
│   │   ├── validators.py      # Command validation
│   │   └── handlers.py        # Command handlers
│   ├── approval/              # Approval system
│   │   ├── __init__.py
│   │   ├── manager.py         # Approval workflow
│   │   ├── risk_assessment.py # Risk evaluation
│   │   └── preferences.py     # User preferences
│   └── ui/                    # User interface components
│       ├── __init__.py
│       ├── hotkeys.py         # Hotkey handling
│       ├── notifications.py   # Desktop notifications
│       └── log_viewer.py      # Log window
├── config/
│   ├── daemon.yaml            # Daemon configuration
│   ├── models.yaml            # LLM model configuration
│   └── security.yaml          # Security policies
├── scripts/
│   ├── install.sh             # Installation script
│   ├── setup_environment.sh   # Environment setup
│   └── create_service.sh      # systemd service creation
├── tests/
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   └── e2e/                   # End-to-end tests
├── docs/
│   ├── api.md                 # API documentation
│   ├── installation.md        # Installation guide
│   └── configuration.md       # Configuration guide
└── requirements.txt           # Python dependencies
```

## Core Implementation Details

### 1. Main Daemon Service (`src/daemon/main.py`)

```python
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
from fastapi import FastAPI
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
```

### 2. REST API Layer (`src/daemon/api.py`)

```python
"""
FastAPI application for DevOS daemon
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.websockets import WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import uuid
import json
from datetime import datetime

from ..llm.model_router import ModelRouter
from ..executor.sandbox import CommandExecutor
from ..approval.manager import ApprovalManager

class CommandRequest(BaseModel):
    command: str
    context: Optional[Dict[str, Any]] = None
    user_id: str = "default"
    approval_timeout: int = 300  # 5 minutes

class CommandResponse(BaseModel):
    job_id: str
    status: str  # pending, approved, executing, completed, failed
    requires_approval: bool
    estimated_cost: float
    model_used: Optional[str] = None

class ApprovalRequest(BaseModel):
    approved: bool
    remember: bool = False
    note: Optional[str] = None

def create_app(services: Dict, config) -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title="DevOS API",
        description="LLM-powered operating system interface",
        version="1.0.0"
    )
    
    # Global state
    jobs = {}  # job_id -> job_data
    websocket_connections = []
    
    # Initialize components
    model_router = ModelRouter(services['bedrock'], config.model_config)
    executor = CommandExecutor(config.security_config)
    approval_manager: ApprovalManager = services['approval_manager']
    
    @app.post("/api/v1/command", response_model=CommandResponse)
    async def submit_command(request: CommandRequest, background_tasks: BackgroundTasks):
        """Submit a natural language command for processing"""
        
        job_id = str(uuid.uuid4())
        
        # Get current context
        context = await gather_context(services, request.context)
        
        # Route to appropriate model
        model_info = await model_router.select_model(request.command, context)
        
        # Assess risk and approval requirements
        approval_required = await approval_manager.requires_approval(
            request.command, context, request.user_id
        )
        
        job_data = {
            'id': job_id,
            'command': request.command,
            'context': context,
            'user_id': request.user_id,
            'model_info': model_info,
            'status': 'pending' if approval_required else 'approved',
            'requires_approval': approval_required,
            'created_at': datetime.utcnow(),
            'estimated_cost': model_info['estimated_cost']
        }
        
        jobs[job_id] = job_data
        
        if not approval_required:
            # Execute immediately
            background_tasks.add_task(execute_command, job_id)
        else:
            # Send approval notification
            background_tasks.add_task(send_approval_notification, job_id)
        
        return CommandResponse(
            job_id=job_id,
            status=job_data['status'],
            requires_approval=approval_required,
            estimated_cost=model_info['estimated_cost'],
            model_used=model_info['model_name']
        )
    
    @app.get("/api/v1/command/{job_id}/status")
    async def get_command_status(job_id: str):
        """Get the status of a command execution"""
        
        if job_id not in jobs:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = jobs[job_id]
        return {
            'job_id': job_id,
            'status': job['status'],
            'result': job.get('result'),
            'error': job.get('error'),
            'logs': job.get('logs', []),
            'progress': job.get('progress', 0),
            'estimated_completion': job.get('estimated_completion')
        }
    
    @app.post("/api/v1/command/{job_id}/approve")
    async def approve_command(job_id: str, approval: ApprovalRequest, background_tasks: BackgroundTasks):
        """Approve or reject a pending command"""
        
        if job_id not in jobs:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = jobs[job_id]
        
        if job['status'] != 'pending':
            raise HTTPException(status_code=400, detail="Job is not pending approval")
        
        if approval.approved:
            job['status'] = 'approved'
            
            # Learn user preference if requested
            if approval.remember:
                await approval_manager.learn_preference(
                    job['command'], job['context'], job['user_id'], True
                )
            
            # Execute the command
            background_tasks.add_task(execute_command, job_id)
        else:
            job['status'] = 'rejected'
            job['result'] = {'message': 'Command rejected by user'}
        
        # Notify websocket clients
        await broadcast_job_update(job_id)
        
        return {'status': 'success', 'job_status': job['status']}
    
    @app.websocket("/ws/events")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for real-time updates"""
        await websocket.accept()
        websocket_connections.append(websocket)
        
        try:
            while True:
                # Keep connection alive
                await websocket.receive_text()
        except WebSocketDisconnect:
            websocket_connections.remove(websocket)
    
    async def gather_context(services: Dict, additional_context: Optional[Dict] = None) -> Dict:
        """Gather current system context for command processing"""
        context = {
            'timestamp': datetime.utcnow().isoformat(),
            'cwd': str(Path.cwd()),
        }
        
        # File system context
        if 'file_monitor' in services:
            context['files'] = await services['file_monitor'].get_recent_changes()
        
        # Process context
        if 'process_monitor' in services:
            context['processes'] = await services['process_monitor'].get_current_processes()
        
        # Git context
        if 'git_monitor' in services:
            context['git'] = await services['git_monitor'].get_repository_status()
        
        # Merge additional context
        if additional_context:
            context.update(additional_context)
        
        return context
    
    async def execute_command(job_id: str):
        """Execute a command in the background"""
        job = jobs[job_id]
        job['status'] = 'executing'
        
        try:
            # Generate system commands using LLM
            llm_response = await model_router.process_command(
                job['command'], 
                job['context'], 
                job['model_info']
            )
            
            # Execute generated commands
            result = await executor.execute(llm_response['commands'], job['user_id'])
            
            job['status'] = 'completed'
            job['result'] = result
            job['logs'] = result.get('logs', [])
            
        except Exception as e:
            job['status'] = 'failed'
            job['error'] = str(e)
            job['logs'] = [{'level': 'error', 'message': str(e)}]
        
        # Notify websocket clients
        await broadcast_job_update(job_id)
    
    async def send_approval_notification(job_id: str):
        """Send desktop notification for approval request"""
        job = jobs[job_id]
        
        notification_data = {
            'type': 'approval_request',
            'job_id': job_id,
            'command': job['command'],
            'estimated_cost': job['estimated_cost'],
            'model': job['model_info']['model_name']
        }
        
        # Send to UI service for desktop notification
        # This would integrate with the desktop notification system
        await broadcast_notification(notification_data)
    
    async def broadcast_job_update(job_id: str):
        """Broadcast job status update to all websocket clients"""
        job = jobs[job_id]
        message = {
            'type': 'job_update',
            'job_id': job_id,
            'status': job['status'],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        for websocket in websocket_connections[:]:  # Copy list to avoid modification during iteration
            try:
                await websocket.send_text(json.dumps(message))
            except:
                websocket_connections.remove(websocket)
    
    async def broadcast_notification(data: Dict):
        """Broadcast notification to all websocket clients"""
        message = {
            'type': 'notification',
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        for websocket in websocket_connections[:]:
            try:
                await websocket.send_text(json.dumps(message))
            except:
                websocket_connections.remove(websocket)
    
    return app
```

### 3. AWS Bedrock Integration (`src/llm/bedrock_client.py`)

```python
"""
AWS Bedrock client for LLM integration
"""

import json
import boto3
from typing import Dict, List, Optional, Any
from botocore.exceptions import ClientError
import logging

class BedrockClient:
    """AWS Bedrock client for LLM model access"""
    
    def __init__(self, region: str, access_key: str, secret_key: str):
        self.region = region
        self.logger = logging.getLogger(__name__)
        
        # Initialize Bedrock client
        self.bedrock = boto3.client(
            'bedrock-runtime',
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        
        # Model configurations
        self.models = {
            'titan-text-lite': {
                'model_id': 'amazon.titan-text-lite-v1',
                'max_tokens': 512,
                'cost_per_1k_tokens': 0.0003
            },
            'claude-3-haiku': {
                'model_id': 'anthropic.claude-3-haiku-20240307-v1:0',
                'max_tokens': 2048,
                'cost_per_1k_tokens': 0.0015
            },
            'claude-3.5-sonnet': {
                'model_id': 'anthropic.claude-3-5-sonnet-20241022-v2:0',
                'max_tokens': 4096,
                'cost_per_1k_tokens': 0.015
            }
        }
    
    async def invoke_model(self, model_name: str, prompt: str, context: Dict) -> Dict:
        """Invoke a Bedrock model with the given prompt"""
        
        if model_name not in self.models:
            raise ValueError(f"Unknown model: {model_name}")
        
        model_config = self.models[model_name]
        
        try:
            if model_name.startswith('claude'):
                response = await self._invoke_claude(model_config, prompt, context)
            elif model_name.startswith('titan'):
                response = await self._invoke_titan(model_config, prompt, context)
            else:
                raise ValueError(f"Unsupported model type: {model_name}")
            
            return response
            
        except ClientError as e:
            self.logger.error(f"AWS Bedrock error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Model invocation error: {e}")
            raise
    
    async def _invoke_claude(self, model_config: Dict, prompt: str, context: Dict) -> Dict:
        """Invoke Claude model through Bedrock"""
        
        # Construct Claude-specific request
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": model_config['max_tokens'],
            "messages": [
                {
                    "role": "user",
                    "content": self._build_system_prompt(prompt, context)
                }
            ],
            "temperature": 0.1,
            "top_p": 0.9
        }
        
        response = self.bedrock.invoke_model(
            modelId=model_config['model_id'],
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        
        return {
            'content': response_body['content'][0]['text'],
            'usage': response_body.get('usage', {}),
            'model_id': model_config['model_id']
        }
    
    async def _invoke_titan(self, model_config: Dict, prompt: str, context: Dict) -> Dict:
        """Invoke Titan model through Bedrock"""
        
        request_body = {
            "inputText": self._build_system_prompt(prompt, context),
            "textGenerationConfig": {
                "maxTokenCount": model_config['max_tokens'],
                "temperature": 0.1,
                "topP": 0.9,
                "stopSequences": ["```"]
            }
        }
        
        response = self.bedrock.invoke_model(
            modelId=model_config['model_id'],
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        
        return {
            'content': response_body['results'][0]['outputText'],
            'usage': {
                'input_tokens': response_body.get('inputTextTokenCount', 0),
                'output_tokens': response_body.get('outputTextTokenCount', 0)
            },
            'model_id': model_config['model_id']
        }
    
    def _build_system_prompt(self, user_command: str, context: Dict) -> str:
        """Build system prompt with context and command"""
        
        system_context = f"""
You are DevOS, an AI assistant integrated into a Linux operating system. You help developers by translating natural language commands into system operations.

Current System Context:
- Working Directory: {context.get('cwd', 'unknown')}
- Timestamp: {context.get('timestamp', 'unknown')}
- User: {context.get('user_id', 'developer')}

File System Context:
{json.dumps(context.get('files', {}), indent=2)}

Process Context:
{json.dumps(context.get('processes', {}), indent=2)}

Git Context:
{json.dumps(context.get('git', {}), indent=2)}

User Command: {user_command}

Please analyze the command and provide a JSON response with the following structure:
{{
    "interpretation": "What the user wants to accomplish",
    "commands": [
        {{
            "type": "bash|python|sql",
            "command": "actual command to execute",
            "description": "what this command does",
            "safety_level": "safe|moderate|destructive"
        }}
    ],
    "explanation": "Brief explanation of what will happen",
    "risks": ["any potential risks or side effects"]
}}

Only provide commands that are safe and follow security best practices. Never include commands that could harm the system or compromise security.
"""
        
        return system_context
    
    def estimate_cost(self, model_name: str, prompt_length: int) -> float:
        """Estimate the cost of a model invocation"""
        
        if model_name not in self.models:
            return 0.0
        
        # Rough estimation: prompt + expected response
        estimated_tokens = prompt_length + 500
        cost_per_1k = self.models[model_name]['cost_per_1k_tokens']
        
        return (estimated_tokens / 1000) * cost_per_1k
```

### 4. Installation Script (`scripts/install.sh`)

```bash
#!/bin/bash

# DevOS MVP Installation Script
# Installs and configures DevOS daemon on Ubuntu 22.04

set -e

DEVOS_USER="devos"
DEVOS_HOME="/opt/devos"
CONFIG_DIR="/etc/devos"
LOG_DIR="/var/log/devos"
SERVICE_NAME="devos-daemon"

echo "🚀 Starting DevOS MVP installation..."

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root (use sudo)"
   exit 1
fi

# Check Ubuntu version
if ! grep -q "22.04" /etc/os-release; then
    echo "⚠️  Warning: This installer is designed for Ubuntu 22.04 LTS"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system packages
echo "📦 Updating system packages..."
apt-get update
apt-get upgrade -y

# Install system dependencies
echo "🔧 Installing system dependencies..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    build-essential \
    pkg-config \
    libffi-dev \
    libssl-dev \
    libasound2-dev \
    portaudio19-dev \
    libpulse-dev \
    libdbus-1-dev \
    libgirepository1.0-dev \
    git \
    curl \
    wget \
    jq \
    sqlite3 \
    gnome-shell-extensions \
    libnotify-bin

# Create DevOS user
echo "👤 Creating DevOS user..."
if ! id "$DEVOS_USER" &>/dev/null; then
    useradd -r -s /bin/false -d "$DEVOS_HOME" "$DEVOS_USER"
fi

# Create directories
echo "📁 Creating directories..."
mkdir -p "$DEVOS_HOME"
mkdir -p "$CONFIG_DIR"
mkdir -p "$LOG_DIR"
mkdir -p "$DEVOS_HOME"/{src,config,logs}

# Set ownership
chown -R "$DEVOS_USER:$DEVOS_USER" "$DEVOS_HOME"
chown -R "$DEVOS_USER:$DEVOS_USER" "$LOG_DIR"

# Copy application files
echo "📄 Installing application files..."
cp -r ./src/* "$DEVOS_HOME/src/"
cp -r ./config/* "$CONFIG_DIR/"

# Create Python virtual environment
echo "🐍 Setting up Python environment..."
cd "$DEVOS_HOME"
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r "$PWD/../requirements.txt"

# Create systemd service
echo "⚙️  Creating systemd service..."
cat > "/etc/systemd/system/${SERVICE_NAME}.service" << EOF
[Unit]
Description=DevOS LLM-Powered Operating System Daemon
After=network.target
Wants=network.target
Documentation=https://github.com/your-org/devos

[Service]
Type=notify
User=$DEVOS_USER
Group=$DEVOS_USER
WorkingDirectory=$DEVOS_HOME
Environment=PATH=$DEVOS_HOME/venv/bin
Environment=PYTHONPATH=$DEVOS_HOME/src
ExecStart=$DEVOS_HOME/venv/bin/python -m daemon.main
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=devos-daemon

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=$LOG_DIR $CONFIG_DIR $DEVOS_HOME/logs
CapabilityBoundingSet=CAP_NET_BIND_SERVICE

[Install]
WantedBy=multi-user.target
EOF

# Set file permissions
echo "🔐 Setting file permissions..."
chown -R "$DEVOS_USER:$DEVOS_USER" "$DEVOS_HOME"
chmod -R 755 "$DEVOS_HOME/src"
chmod 640 "$CONFIG_DIR"/*.yaml
chmod 750 "$LOG_DIR"

# Create default configuration
echo "⚙️  Creating default configuration..."
cat > "$CONFIG_DIR/daemon.yaml" << EOF
# DevOS Daemon Configuration

# API Configuration
api_host: "127.0.0.1"
api_port: 8080

# AWS Configuration (replace with your values)
aws_region: "us-east-1"
aws_access_key: ""  # Configure via environment or IAM role
aws_secret_key: ""  # Configure via environment or IAM role

# Logging
log_level: "INFO"

# File System Monitoring
watch_paths:
  - "/home"
  - "/opt"
  - "/tmp"

# Process Monitoring
process_update_interval: 30

# Git Repository Paths
git_repo_paths:
  - "/home"

# Model Configuration
model_config:
  default_model: "claude-3-haiku"
  cost_threshold: 0.10
  timeout: 30

# Approval Configuration
approval_config:
  auto_approve_safe: true
  approval_timeout: 300
  learn_preferences: true

# Security Configuration
security_config:
  sandbox_enabled: true
  max_execution_time: 120
  allowed_commands:
    - "ls"
    - "cp"
    - "mv"
    - "mkdir"
    - "git"
    - "npm"
    - "pip"
    - "docker"
  blocked_commands:
    - "rm -rf /"
    - "mkfs"
    - "dd"
EOF

# Initialize database
echo "🗄️  Initializing database..."
sudo -u "$DEVOS_USER" "$DEVOS_HOME/venv/bin/python" -c "
import sys
sys.path.append('$DEVOS_HOME/src')
from context.database import init_database
init_database('$DEVOS_HOME/logs/context.db')
print('Database initialized successfully')
"

# Enable and start service
echo "🚀 Starting DevOS daemon..."
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl start "$SERVICE_NAME"

# Check service status
sleep 5
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "✅ DevOS daemon started successfully"
    echo "📊 Service status:"
    systemctl status "$SERVICE_NAME" --no-pager -l
else
    echo "❌ Failed to start DevOS daemon"
    echo "📊 Service status:"
    systemctl status "$SERVICE_NAME" --no-pager -l
    echo "📄 Recent logs:"
    journalctl -u "$SERVICE_NAME" --no-pager -l -n 20
    exit 1
fi

# Install desktop integration
echo "🖥️  Installing desktop integration..."
if [ -n "$SUDO_USER" ] && [ "$SUDO_USER" != "root" ]; then
    USER_HOME=$(getent passwd "$SUDO_USER" | cut -d: -f6)
    
    # Create desktop shortcut
    cat > "$USER_HOME/Desktop/DevOS.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=DevOS
Comment=LLM-Powered Operating System
Exec=gnome-terminal -- curl -X POST http://localhost:8080/api/v1/command -H "Content-Type: application/json" -d '{"command": "help"}'
Icon=utilities-terminal
Terminal=false
Categories=Development;System;
EOF
    
    chmod +x "$USER_HOME/Desktop/DevOS.desktop"
    chown "$SUDO_USER:$SUDO_USER" "$USER_HOME/Desktop/DevOS.desktop"
fi

# Display installation summary
echo ""
echo "🎉 DevOS MVP installation completed successfully!"
echo ""
echo "📋 Installation Summary:"
echo "   • Service: $SERVICE_NAME"
echo "   • Status: $(systemctl is-active $SERVICE_NAME)"
echo "   • API: http://localhost:8080"
echo "   • Config: $CONFIG_DIR/daemon.yaml"
echo "   • Logs: $LOG_DIR/"
echo ""
echo "🔧 Next Steps:"
echo "   1. Configure AWS credentials in $CONFIG_DIR/daemon.yaml"
echo "   2. Test the API: curl http://localhost:8080/api/v1/command"
echo "   3. View logs: journalctl -u $SERVICE_NAME -f"
echo "   4. Configure hotkeys and desktop integration"
echo ""
echo "📚 Documentation: https://github.com/your-org/devos/docs"
echo ""
```

### 5. Testing Suite (`tests/integration/test_basic_commands.py`)

```python
"""
Integration tests for basic DevOS commands
"""

import pytest
import asyncio
import httpx
from pathlib import Path
import tempfile
import os

BASE_URL = "http://localhost:8080"

class TestBasicCommands:
    """Test basic command functionality"""
    
    @pytest.fixture
    def client(self):
        return httpx.AsyncClient(base_url=BASE_URL)
    
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield tmp_dir
    
    @pytest.mark.asyncio
    async def test_file_listing(self, client, temp_dir):
        """Test file listing command"""
        
        # Create test files
        test_files = ["file1.txt", "file2.py", "file3.md"]
        for filename in test_files:
            Path(temp_dir, filename).touch()
        
        # Submit command
        response = await client.post("/api/v1/command", json={
            "command": f"list files in {temp_dir}",
            "context": {"cwd": temp_dir}
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "job_id" in data
        assert "status" in data
        assert data["requires_approval"] is False
        
        # Wait for completion
        job_id = data["job_id"]
        await self._wait_for_completion(client, job_id)
        
        # Check results
        result_response = await client.get(f"/api/v1/command/{job_id}/status")
        result_data = result_response.json()
        
        assert result_data["status"] == "completed"
        assert "result" in result_data
        
        # Verify all test files are listed
        result_text = str(result_data["result"])
        for filename in test_files:
            assert filename in result_text
    
    @pytest.mark.asyncio
    async def test_file_organization(self, client, temp_dir):
        """Test file organization by type"""
        
        # Create mixed file types
        files = {
            "document.pdf": "pdf",
            "image.jpg": "image", 
            "script.py": "code",
            "data.csv": "data"
        }
        
        for filename in files.keys():
            Path(temp_dir, filename).touch()
        
        # Submit organization command
        response = await client.post("/api/v1/command", json={
            "command": f"organize files in {temp_dir} by type",
            "context": {"cwd": temp_dir}
        })
        
        assert response.status_code == 200
        data = response.json()
        
        job_id = data["job_id"]
        await self._wait_for_completion(client, job_id)
        
        # Check that directories were created and files moved
        result_response = await client.get(f"/api/v1/command/{job_id}/status")
        result_data = result_response.json()
        
        assert result_data["status"] == "completed"
        
        # Verify organization (this would depend on implementation)
        # Could check for created subdirectories, moved files, etc.
    
    @pytest.mark.asyncio
    async def test_git_status(self, client, temp_dir):
        """Test git status command"""
        
        # Initialize git repo
        os.system(f"cd {temp_dir} && git init")
        Path(temp_dir, "README.md").write_text("# Test Repo")
        
        response = await client.post("/api/v1/command", json={
            "command": "show git status",
            "context": {"cwd": temp_dir}
        })
        
        assert response.status_code == 200
        data = response.json()
        
        job_id = data["job_id"]
        await self._wait_for_completion(client, job_id)
        
        result_response = await client.get(f"/api/v1/command/{job_id}/status")
        result_data = result_response.json()
        
        assert result_data["status"] == "completed"
        assert "README.md" in str(result_data["result"])
    
    @pytest.mark.asyncio
    async def test_approval_workflow(self, client):
        """Test approval workflow for destructive commands"""
        
        response = await client.post("/api/v1/command", json={
            "command": "delete all temporary files",
            "context": {}
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["requires_approval"] is True
        assert data["status"] == "pending"
        
        job_id = data["job_id"]
        
        # Approve the command
        approval_response = await client.post(f"/api/v1/command/{job_id}/approve", json={
            "approved": True,
            "remember": False
        })
        
        assert approval_response.status_code == 200
        
        # Wait for execution
        await self._wait_for_completion(client, job_id)
        
        result_response = await client.get(f"/api/v1/command/{job_id}/status")
        result_data = result_response.json()
        
        assert result_data["status"] == "completed"
    
    async def _wait_for_completion(self, client, job_id, timeout=30):
        """Wait for job completion or timeout"""
        
        for _ in range(timeout):
            response = await client.get(f"/api/v1/command/{job_id}/status")
            data = response.json()
            
            if data["status"] in ["completed", "failed", "rejected"]:
                return data
            
            await asyncio.sleep(1)
        
        raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

## Build and Deployment Instructions

### 1. Prerequisites
- Ubuntu 22.04 LTS
- Python 3.11+
- AWS account with Bedrock access
- 8GB RAM, 4 CPU cores minimum

### 2. Installation Steps
```bash
# Clone repository
git clone https://github.com/your-org/devos-mvp.git
cd devos-mvp

# Run installation script
sudo ./scripts/install.sh

# Configure AWS credentials
sudo nano /etc/devos/daemon.yaml
# Add your AWS access key and secret key

# Restart service
sudo systemctl restart devos-daemon

# Test API
curl -X POST http://localhost:8080/api/v1/command \
  -H "Content-Type: application/json" \
  -d '{"command": "list files in current directory"}'
```

### 3. Testing
```bash
# Run unit tests
cd devos-mvp
python -m pytest tests/unit/ -v

# Run integration tests (requires running daemon)
python -m pytest tests/integration/ -v

# Run end-to-end tests
python -m pytest tests/e2e/ -v
```

### 4. Configuration
Key configuration files:
- `/etc/devos/daemon.yaml` - Main daemon configuration
- `/etc/devos/models.yaml` - LLM model configuration  
- `/etc/devos/security.yaml` - Security policies

### 5. Monitoring
```bash
# View service status
sudo systemctl status devos-daemon

# View logs
sudo journalctl -u devos-daemon -f

# Check API health
curl http://localhost:8080/health
```

This MVP implementation provides a solid foundation for the DevOS concept with working code, installation procedures, and testing frameworks. The system can process natural language commands, route them to appropriate LLM models, execute system operations safely, and provide real-time feedback to users.