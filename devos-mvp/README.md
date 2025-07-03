# DevOS MVP - LLM-powered Developer Operating System

DevOS is an intelligent developer operating system that provides LLM-powered automation, context-aware assistance, and seamless integration with enterprise tools.

## Features

- **LLM-powered Command Processing**: Natural language command interpretation and execution
- **Context-aware System**: Monitors files, processes, and Git repositories for intelligent assistance
- **Security-first Approach**: Risk assessment and approval workflows for command execution
- **Enterprise Integrations**: Native support for Rancher, Jira, ServiceNow, New Relic, and Splunk
- **Extensible Architecture**: Plugin-based system for custom integrations
- **Local Vector Database**: Persistent memory for learning and context retention

## Quick Start

### Prerequisites

- Python 3.9 or higher
- Git
- curl
- AWS CLI (for Bedrock integration)
- Docker (optional, for sandboxing)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/devos-team/devos.git
cd devos
```

2. Run the installation script:
```bash
chmod +x install.sh
./install.sh
```

3. Configure your environment:
```bash
# Edit environment variables
nano ~/.devos/config/.env

# Edit configuration
nano ~/.devos/config/config.yaml
```

4. Start DevOS:
```bash
# Method 1: Direct execution
source ~/.devos/activate.sh
python -m daemon.main

# Method 2: System service
sudo cp ~/.devos/devos.service /etc/systemd/system/
sudo systemctl enable devos
sudo systemctl start devos
```

## Configuration

### Environment Variables

Configure your environment variables in `~/.devos/config/.env`:

```bash
# AWS Configuration (for Bedrock)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_DEFAULT_REGION=us-east-1

# OpenAI Configuration (optional)
OPENAI_API_KEY=your_openai_api_key

# Enterprise Integrations
RANCHER_URL=https://your-rancher-instance.com
RANCHER_TOKEN=your_rancher_token
JIRA_URL=https://your-company.atlassian.net
JIRA_USERNAME=your_email@company.com
JIRA_API_TOKEN=your_jira_api_token
```

### System Configuration

Edit `~/.devos/config/config.yaml` to customize:

- LLM providers and models
- Security and approval settings
- Enterprise integrations
- Monitoring and logging

## Usage

### Command Line Interface

```bash
# Basic usage
devos "list all Python files in the current directory"
devos "create a new Git branch for feature development"
devos "check the status of our Kubernetes pods"

# With approval workflow
devos "delete old log files older than 30 days"  # Will request approval

# System commands
devos --status           # Check system status
devos --config           # Show configuration
devos --logs             # View logs
devos --approve <id>     # Approve pending command
devos --reject <id>      # Reject pending command
```

### Web Interface

Access the web interface at `http://localhost:8080` when the daemon is running.

### API Usage

```python
import requests

# Submit a command
response = requests.post('http://localhost:8080/api/v1/commands', json={
    'command': 'list all Python files',
    'user_id': 'your-user-id'
})

# Check command status
command_id = response.json()['command_id']
status = requests.get(f'http://localhost:8080/api/v1/commands/{command_id}')
```

## Architecture

### Core Components

- **Daemon**: Main service that orchestrates all components
- **LLM Integration**: Interface with various LLM providers (AWS Bedrock, OpenAI, local models)
- **Context Engine**: Monitors system state and provides intelligent context
- **Approval System**: Risk assessment and user approval workflows
- **Executor**: Secure command execution with sandboxing
- **Enterprise Integrations**: Connectors for enterprise tools

### Security Model

DevOS implements a multi-layered security approach:

1. **Command Validation**: Syntax and safety checks
2. **Risk Assessment**: ML-based risk scoring
3. **Approval Workflows**: User confirmation for risky operations
4. **Sandboxing**: Isolated execution environment
5. **Audit Logging**: Comprehensive operation logging

## Enterprise Integrations

### Rancher/Kubernetes

```yaml
integrations:
  rancher:
    enabled: true
    url: "${RANCHER_URL}"
    token: "${RANCHER_TOKEN}"
    cluster_id: "${RANCHER_CLUSTER_ID}"
```

### Jira

```yaml
integrations:
  jira:
    enabled: true
    url: "${JIRA_URL}"
    username: "${JIRA_USERNAME}"
    api_token: "${JIRA_API_TOKEN}"
```

### ServiceNow

```yaml
integrations:
  servicenow:
    enabled: true
    instance: "${SERVICENOW_INSTANCE}"
    username: "${SERVICENOW_USERNAME}"
    password: "${SERVICENOW_PASSWORD}"
```

### Monitoring Tools

```yaml
integrations:
  newrelic:
    enabled: true
    api_key: "${NEWRELIC_API_KEY}"
    account_id: "${NEWRELIC_ACCOUNT_ID}"
  
  splunk:
    enabled: true
    url: "${SPLUNK_URL}"
    token: "${SPLUNK_TOKEN}"
    index: "devos"
```

## Development

### Project Structure

```
devos-mvp/
├── src/
│   ├── daemon/           # Main daemon service
│   ├── llm/             # LLM integration layer
│   ├── context/         # Context engine
│   ├── executor/        # Command execution
│   ├── approval/        # Approval system
│   └── cli/             # Command line interface
├── config/              # Configuration files
├── tests/              # Test suite
├── docs/               # Documentation
└── scripts/            # Utility scripts
```

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run specific test
pytest tests/test_daemon.py::test_startup
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## Troubleshooting

### Common Issues

1. **Permission Denied**: Ensure the installation script has execute permissions
2. **Python Version**: Verify Python 3.9+ is installed
3. **AWS Credentials**: Check AWS CLI configuration and credentials
4. **Port Conflicts**: Ensure ports 8080-8082 are available

### Logs

View logs for debugging:

```bash
# Real-time logs
tail -f ~/.devos/logs/devos.log

# Application logs
devos --logs

# System service logs
sudo journalctl -u devos -f
```

### Support

- **GitHub Issues**: [Report bugs and request features](https://github.com/devos-team/devos/issues)
- **Documentation**: [Full documentation](https://devos.readthedocs.io)
- **Community**: [Join our Discord](https://discord.gg/devos)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- AWS Bedrock for LLM capabilities
- FastAPI for the web framework
- The open-source community for various dependencies

## Roadmap

- [ ] Web-based dashboard
- [ ] Plugin marketplace
- [ ] Mobile app
- [ ] Multi-tenant support
- [ ] Advanced analytics
- [ ] CI/CD pipeline integration
- [ ] Infrastructure as Code templates
- [ ] Enhanced security features