# DevOS MVP Quick Start Guide

## 🚀 Get DevOS Running in 30 Minutes

This guide will get you from zero to a working DevOS MVP with LLM-powered natural language system interaction.

## Prerequisites

### System Requirements
- **OS**: Ubuntu 22.04 LTS (AWS Workspace or EC2)
- **CPU**: 4+ cores, 2.5+ GHz
- **Memory**: 8+ GB RAM (16 GB recommended)
- **Storage**: 50+ GB available space
- **Network**: High-speed internet for AWS Bedrock

### AWS Setup Required
- AWS Account with Bedrock access
- AWS CLI configured with credentials
- IAM role with Bedrock permissions

## Quick Installation (5 commands)

### 1. Clone and Setup
```bash
# Clone the repository (or create the structure from MVP-Detailed-Implementation.md)
git clone https://github.com/your-org/devos-mvp.git
cd devos-mvp

# Make installation script executable
chmod +x scripts/install.sh
```

### 2. Run Installation
```bash
# Install DevOS with all dependencies
sudo ./scripts/install.sh
```

### 3. Configure AWS Credentials
```bash
# Edit configuration with your AWS credentials
sudo nano /etc/devos/daemon.yaml

# Add your AWS credentials:
# aws_region: "us-east-1"
# aws_access_key: "your-access-key"
# aws_secret_key: "your-secret-key"
```

### 4. Start DevOS
```bash
# Start the service
sudo systemctl start devos-daemon

# Check status
sudo systemctl status devos-daemon
```

### 5. Test Installation
```bash
# Test the API
curl -X POST http://localhost:8080/api/v1/command \
  -H "Content-Type: application/json" \
  -d '{"command": "list files in current directory", "user_id": "testuser"}'
```

## Quick Demo (Try These Commands)

Once DevOS is running, try these commands via the API or build a simple CLI:

### File Operations
```bash
# Organize files by type
curl -X POST http://localhost:8080/api/v1/command \
  -H "Content-Type: application/json" \
  -d '{"command": "organize my Downloads folder by file type", "user_id": "demo"}'

# Find files
curl -X POST http://localhost:8080/api/v1/command \
  -H "Content-Type: application/json" \
  -d '{"command": "find all Python files in this project", "user_id": "demo"}'
```

### Git Operations
```bash
# Check git status
curl -X POST http://localhost:8080/api/v1/command \
  -H "Content-Type: application/json" \
  -d '{"command": "show me git status", "user_id": "demo"}'

# Create and switch branch
curl -X POST http://localhost:8080/api/v1/command \
  -H "Content-Type: application/json" \
  -d '{"command": "create a new branch called feature-test", "user_id": "demo"}'
```

### System Commands
```bash
# Check running processes
curl -X POST http://localhost:8080/api/v1/command \
  -H "Content-Type: application/json" \
  -d '{"command": "show me what processes are using the most CPU", "user_id": "demo"}'

# Environment info
curl -X POST http://localhost:8080/api/v1/command \
  -H "Content-Type: application/json" \
  -d '{"command": "what version of Python am I running", "user_id": "demo"}'
```

## Simple CLI Client (Optional)

Create a simple command-line interface:

```python
#!/usr/bin/env python3
# save as devos-cli.py

import requests
import json
import sys

def send_command(command, user_id="demo"):
    response = requests.post(
        "http://localhost:8080/api/v1/command",
        headers={"Content-Type": "application/json"},
        json={"command": command, "user_id": user_id}
    )
    
    result = response.json()
    print(f"Job ID: {result['job_id']}")
    print(f"Status: {result['status']}")
    print(f"Requires Approval: {result['requires_approval']}")
    
    if result['requires_approval']:
        approve = input("Approve this command? (y/n): ")
        if approve.lower() == 'y':
            requests.post(
                f"http://localhost:8080/api/v1/command/{result['job_id']}/approve",
                json={"approved": True}
            )
            print("Command approved and executing...")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 devos-cli.py 'your command here'")
        sys.exit(1)
    
    command = " ".join(sys.argv[1:])
    send_command(command)
```

Make it executable and use:
```bash
chmod +x devos-cli.py
python3 devos-cli.py "organize my files by date"
```

## Troubleshooting

### Common Issues

#### 1. Service Won't Start
```bash
# Check logs
sudo journalctl -u devos-daemon -f

# Common fixes:
sudo systemctl restart devos-daemon
```

#### 2. AWS Bedrock Access Denied
```bash
# Check IAM permissions
aws sts get-caller-identity

# Verify Bedrock access
aws bedrock list-foundation-models --region us-east-1
```

#### 3. Python Dependencies Missing
```bash
# Reinstall dependencies
cd /opt/devos
source venv/bin/activate
pip install -r /path/to/requirements.txt
```

#### 4. Port 8080 Already in Use
```bash
# Check what's using the port
sudo lsof -i :8080

# Change port in config
sudo nano /etc/devos/daemon.yaml
# Change api_port: 8081
sudo systemctl restart devos-daemon
```

### Check Health
```bash
# Service status
sudo systemctl status devos-daemon

# API health
curl http://localhost:8080/health

# Check logs
sudo tail -f /var/log/devos/daemon.log
```

## What's Included in MVP

### ✅ Core Features Working
- **Natural Language Processing**: Converts commands to system operations
- **File Operations**: List, organize, search, copy files
- **Git Integration**: Status, branch, commit operations
- **Process Management**: View, manage system processes
- **Basic Security**: Command approval workflow
- **AWS Bedrock**: LLM integration with cost tracking

### ✅ Basic Architecture
- **REST API**: HTTP endpoints for command submission
- **Approval System**: Safety checks for destructive operations
- **Context Engine**: Basic file and process awareness
- **Command Executor**: Secure command execution sandbox
- **Logging**: Basic operation logging

### 🚧 Not Yet Included (Full Version)
- Memory Agent with vector database
- Enterprise integrations (Jira, ServiceNow, etc.)
- Advanced security and compliance
- Desktop UI and hotkeys
- Voice commands
- Comprehensive monitoring

## Next Steps

### Extend the MVP
1. **Add Memory Agent**: Follow Memory-Agent-Architecture.md
2. **Add Enterprise Tools**: Follow Enterprise-Integration-Addendum.md  
3. **Add Security**: Follow Security-Compliance-Framework.md
4. **Add Monitoring**: Follow Operational-Monitoring-Architecture.md

### Production Deployment
1. **Create AMI**: Use the custom AMI creation process
2. **Scale**: Deploy across multiple AWS Workspaces
3. **Monitor**: Set up CloudWatch and New Relic
4. **Secure**: Implement full security framework

## Cost Estimation

### MVP Running Costs (Monthly)
- **AWS EC2 (t3.large)**: ~$60
- **AWS Bedrock Usage**: ~$20-50 (depends on usage)
- **Storage (50GB EBS)**: ~$5
- **Data Transfer**: ~$5
- **Total**: ~$90-120/month per workspace

### Usage Patterns
- **Light Usage**: 100 commands/day = ~$0.50/day in LLM costs
- **Medium Usage**: 500 commands/day = ~$2.50/day in LLM costs  
- **Heavy Usage**: 1000+ commands/day = ~$5+/day in LLM costs

## Support and Resources

### Documentation
- **Full Technical Architecture**: `Technical-Architecture.md`
- **Complete Implementation**: `MVP-Detailed-Implementation.md`
- **Use Cases**: `Developer-Use-Cases.md`
- **Enterprise Features**: `Enterprise-Developer-Use-Cases.md`

### Getting Help
- Check logs: `/var/log/devos/daemon.log`
- Service status: `systemctl status devos-daemon`
- API health: `curl http://localhost:8080/health`

This MVP gives you a working foundation to experience DevOS capabilities and can be extended with the full enterprise features as needed.