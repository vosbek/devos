#!/bin/bash

# DevOS MVP Installation Script
# This script sets up the DevOS MVP environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PYTHON_MIN_VERSION="3.9"
INSTALL_DIR="${HOME}/.devos"
CONFIG_DIR="${INSTALL_DIR}/config"
LOG_DIR="${INSTALL_DIR}/logs"
DATA_DIR="${INSTALL_DIR}/data"

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

check_python_version() {
    log "Checking Python version..."
    
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is not installed. Please install Python 3.9 or higher."
    fi
    
    python_version=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
    
    if [ "$(printf '%s\n' "$PYTHON_MIN_VERSION" "$python_version" | sort -V | head -n1)" = "$PYTHON_MIN_VERSION" ]; then
        success "Python $python_version is compatible"
    else
        error "Python $python_version is not compatible. Please install Python $PYTHON_MIN_VERSION or higher."
    fi
}

check_dependencies() {
    log "Checking system dependencies..."
    
    # Check for required system packages
    missing_deps=()
    
    if ! command -v git &> /dev/null; then
        missing_deps+=("git")
    fi
    
    if ! command -v curl &> /dev/null; then
        missing_deps+=("curl")
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        error "Missing required dependencies: ${missing_deps[*]}. Please install them first."
    fi
    
    success "All system dependencies are available"
}

setup_directories() {
    log "Setting up directories..."
    
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "$DATA_DIR"
    
    success "Directories created successfully"
}

setup_virtual_environment() {
    log "Setting up Python virtual environment..."
    
    if [ ! -d "$INSTALL_DIR/venv" ]; then
        python3 -m venv "$INSTALL_DIR/venv"
        success "Virtual environment created"
    else
        log "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source "$INSTALL_DIR/venv/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip
    
    success "Virtual environment ready"
}

install_devos() {
    log "Installing DevOS MVP..."
    
    # Activate virtual environment
    source "$INSTALL_DIR/venv/bin/activate"
    
    # Install DevOS package
    pip install -e .
    
    success "DevOS MVP installed successfully"
}

copy_configuration() {
    log "Setting up configuration..."
    
    # Copy default configuration
    if [ ! -f "$CONFIG_DIR/config.yaml" ]; then
        cp "config/config.yaml" "$CONFIG_DIR/config.yaml"
        success "Default configuration copied"
    else
        log "Configuration file already exists"
    fi
    
    # Create .env file template
    if [ ! -f "$CONFIG_DIR/.env" ]; then
        cat > "$CONFIG_DIR/.env" << EOF
# DevOS Environment Variables
# Copy this file and set your values

# AWS Configuration (for Bedrock)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_DEFAULT_REGION=us-east-1

# OpenAI Configuration (optional)
OPENAI_API_KEY=your_openai_api_key

# Enterprise Integrations (optional)
RANCHER_URL=https://your-rancher-instance.com
RANCHER_TOKEN=your_rancher_token
RANCHER_CLUSTER_ID=your_cluster_id

JIRA_URL=https://your-company.atlassian.net
JIRA_USERNAME=your_email@company.com
JIRA_API_TOKEN=your_jira_api_token

SERVICENOW_INSTANCE=your-company.service-now.com
SERVICENOW_USERNAME=your_username
SERVICENOW_PASSWORD=your_password

NEWRELIC_API_KEY=your_newrelic_api_key
NEWRELIC_ACCOUNT_ID=your_account_id

SPLUNK_URL=https://your-splunk-instance.com
SPLUNK_TOKEN=your_splunk_token
EOF
        success "Environment template created"
    fi
}

setup_systemd_service() {
    log "Setting up systemd service..."
    
    # Create systemd service file
    cat > "$INSTALL_DIR/devos.service" << EOF
[Unit]
Description=DevOS - LLM-powered Developer Operating System
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
ExecStart=$INSTALL_DIR/venv/bin/python -m daemon.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # Create activation script
    cat > "$INSTALL_DIR/activate.sh" << EOF
#!/bin/bash
# DevOS Activation Script
source "$INSTALL_DIR/venv/bin/activate"
export DEVOS_CONFIG_DIR="$CONFIG_DIR"
export DEVOS_DATA_DIR="$DATA_DIR"
export DEVOS_LOG_DIR="$LOG_DIR"
EOF
    
    chmod +x "$INSTALL_DIR/activate.sh"
    
    success "Service files created"
}

create_cli_wrapper() {
    log "Creating CLI wrapper..."
    
    cat > "$INSTALL_DIR/devos-cli" << EOF
#!/bin/bash
# DevOS CLI Wrapper
source "$INSTALL_DIR/venv/bin/activate"
export DEVOS_CONFIG_DIR="$CONFIG_DIR"
export DEVOS_DATA_DIR="$DATA_DIR"
export DEVOS_LOG_DIR="$LOG_DIR"
python -m cli.main "\$@"
EOF
    
    chmod +x "$INSTALL_DIR/devos-cli"
    
    # Create symlink in user's bin directory
    if [ -d "$HOME/.local/bin" ]; then
        ln -sf "$INSTALL_DIR/devos-cli" "$HOME/.local/bin/devos"
        success "CLI wrapper created and linked"
    else
        success "CLI wrapper created at $INSTALL_DIR/devos-cli"
        warning "Add $INSTALL_DIR to your PATH to use 'devos-cli' command"
    fi
}

run_initial_setup() {
    log "Running initial setup..."
    
    # Activate virtual environment
    source "$INSTALL_DIR/venv/bin/activate"
    
    # Initialize database
    export DEVOS_CONFIG_DIR="$CONFIG_DIR"
    export DEVOS_DATA_DIR="$DATA_DIR"
    export DEVOS_LOG_DIR="$LOG_DIR"
    
    python -c "
import sys
sys.path.insert(0, 'src')
from daemon.database import init_database
import asyncio
asyncio.run(init_database())
print('Database initialized successfully')
"
    
    success "Initial setup completed"
}

display_next_steps() {
    echo
    echo "=================================="
    echo "DevOS MVP Installation Complete!"
    echo "=================================="
    echo
    echo "Next steps:"
    echo "1. Configure your environment variables in: $CONFIG_DIR/.env"
    echo "2. Review and adjust configuration in: $CONFIG_DIR/config.yaml"
    echo "3. Start DevOS daemon:"
    echo "   source $INSTALL_DIR/activate.sh"
    echo "   python -m daemon.main"
    echo
    echo "4. Or install as a system service:"
    echo "   sudo cp $INSTALL_DIR/devos.service /etc/systemd/system/"
    echo "   sudo systemctl enable devos"
    echo "   sudo systemctl start devos"
    echo
    echo "5. Use the CLI:"
    echo "   devos --help"
    echo
    echo "Configuration directory: $CONFIG_DIR"
    echo "Data directory: $DATA_DIR"
    echo "Log directory: $LOG_DIR"
    echo
    echo "For more information, see the README.md file."
}

# Main installation flow
main() {
    log "Starting DevOS MVP installation..."
    
    check_python_version
    check_dependencies
    setup_directories
    setup_virtual_environment
    install_devos
    copy_configuration
    setup_systemd_service
    create_cli_wrapper
    run_initial_setup
    
    display_next_steps
    
    success "Installation completed successfully!"
}

# Run main function
main "$@"