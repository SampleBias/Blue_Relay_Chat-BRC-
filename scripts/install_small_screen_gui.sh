#!/bin/bash

# Blue Relay Chat Small Screen GUI Installation Script
# This script installs Blue Relay Chat with small screen GUI support

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/blue-relay-chat"
SERVICE_USER="pi"
PYTHON_VERSION="3.9"

# Functions
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root. Run as a regular user with sudo."
    fi
}

# Check if running on Raspberry Pi
check_raspberry_pi() {
    if [[ ! -f /proc/device-tree/model ]]; then
        error "This script is designed for Raspberry Pi. Could not detect hardware."
        exit 1
    fi
    
    MODEL=$(tr -d '\0' < /proc/device-tree/model)
    if [[ ! "$MODEL" =~ "Raspberry Pi" ]]; then
        warn "This script is optimized for Raspberry Pi, but detected: $MODEL"
        read -p "Continue anyway? (y/n): " -n -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    log "Detected Raspberry Pi model: $MODEL"
}

# Check system requirements
check_requirements() {
    log "Checking system requirements..."
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is required but not installed. Please install Python 3."
        exit 1
    fi
    
    PYTHON_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    REQUIRED_VER="3.7"
    
    if [[ "$(printf '%s\n' "$PYTHON_VER" "$REQUIRED_VER")" -lt "0" ]]; then
        error "Python 3.7+ is required. Found version: $PYTHON_VER"
        exit 1
    fi
    
    # Check for required packages
    REQUIRED_PACKAGES="python3-pip python3-venv git"
    for package in $REQUIRED_PACKAGES; do
        if ! dpkg -l | grep -q "^ii  $package "; then
            error "Required package not installed: $package"
            exit 1
        fi
    done
    
    # Check for optional packages
    OPTIONAL_PACKAGES="python3-rpi.gpio"
    MISSING_OPTIONAL=""
    for package in $OPTIONAL_PACKAGES; do
        if ! dpkg -l | grep -q "^ii  $package "; then
            MISSING_OPTIONAL="$MISSING_OPTIONAL $package "
        fi
    done
    
    if [[ -n "$MISSING_OPTIONAL" ]]; then
        warn "Optional packages not installed: $MISSING_OPTIONAL"
        warn "These will be needed for button input functionality."
    fi
    
    # Check for sufficient disk space
    AVAILABLE_SPACE=$(df / | awk 'NR==2 {print $4}')
    if [[ $AVAILABLE_SPACE -lt 1048576 ]]; then  # 1GB in KB
        error "Insufficient disk space. At least 1GB required. Available: $((AVAILABLE_SPACE/1024/1024))GB"
        exit 1
    fi
    
    log "System requirements check passed."
}

# Install system dependencies
install_system_deps() {
    log "Installing system dependencies..."
    
    # Update package lists
    sudo apt-get update
    
    # Install required packages
    sudo apt-get install -y python3-pip python3-venv git
    
    # Install optional packages for button input
    if [[ -n "$MISSING_OPTIONAL" ]]; then
        sudo apt-get install -y python3-rpi.gpio
    fi
    
    log "System dependencies installed."
}

# Create installation directory
create_install_dir() {
    log "Creating installation directory..."
    
    # Create installation directory if it doesn't exist
    if [[ ! -d "$INSTALL_DIR" ]]; then
        sudo mkdir -p "$INSTALL_DIR"
    fi
    
    # Set ownership
    sudo chown -R $SERVICE_USER:$SERVICE_USER "$INSTALL_DIR"
    sudo chgrp -R $SERVICE_USER:$SERVICE_USER "$INSTALL_DIR"
    
    log "Installation directory created: $INSTALL_DIR"
}

# Clone or update repository
setup_source() {
    log "Setting up source code..."
    
    # Clone repository if directory doesn't exist or is empty
    if [[ ! -d "$INSTALL_DIR/.git" ]] || [[ -z "$(ls -A "$INSTALL_DIR")" ]]; then
        sudo rm -rf "$INSTALL_DIR"
        git clone https://github.com/blue-relay-chat/blue-relay-chat-rpi4.git "$INSTALL_DIR"
    else
        # Update existing repository
        cd "$INSTALL_DIR"
        git pull origin main
    fi
    
    log "Source code setup complete."
}

# Create Python virtual environment
setup_python_env() {
    log "Setting up Python virtual environment..."
    
    cd "$INSTALL_DIR"
    
    # Create virtual environment
    python3 -m venv venv
    
    # Activate and install dependencies
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    log "Python environment setup complete."
}

# Setup configuration for small screen
setup_config() {
    log "Setting up configuration for small screen..."
    
    # Create config directory
    mkdir -p "/home/$SERVICE_USER/.config/blue-relay-chat"
    
    # Copy small screen configuration
    cp config_small_screen.ini "/home/$SERVICE_USER/.config/blue-relay-chat/config.ini"
    
    # Set ownership
    chown $SERVICE_USER:$SERVICE_USER "/home/$SERVICE_USER/.config/blue-relay-chat/config.ini"
    
    log "Small screen configuration setup complete."
}

# Create systemd service
install_service() {
    log "Installing systemd service..."
    
    # Copy service file
    sudo cp systemd/blue-relay-chat-rpi-zero2w.service /etc/systemd/system/
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    # Enable service
    sudo systemctl enable blue-relay-chat.service
    
    log "Systemd service installed and enabled."
}

# Create command-line shortcut
create_cli_shortcut() {
    log "Creating command-line shortcut..."
    
    # Create symlink to main script
    sudo ln -sf "$INSTALL_DIR/main_small_screen.py" /usr/local/bin/blue-relay-chat-gui
    sudo chmod +x /usr/local/bin/blue-relay-chat-gui
    
    log "Command-line shortcut created."
}

# Run post-installation checks
post_install_checks() {
    log "Running post-installation checks..."
    
    # Check if virtual environment exists
    if [[ ! -d "$INSTALL_DIR/venv" ]]; then
        error "Virtual environment not found"
        exit 1
    fi
    
    # Check if main script exists
    if [[ ! -f "$INSTALL_DIR/main_small_screen.py" ]]; then
        error "Main script not found"
        exit 1
    fi
    
    # Check if config file exists
    if [[ ! -f "/home/$SERVICE_USER/.config/blue-relay-chat/config.ini" ]]; then
        error "Configuration file not found"
        exit 1
    fi
    
    # Check if service file exists
    if [[ ! -f "/etc/systemd/system/blue-relay-chat.service" ]]; then
        error "Service file not found"
        exit 1
    fi
    
    log "Post-installation checks passed."
}

# Display installation summary
display_summary() {
    log ""
    log "${GREEN}Blue Relay Chat Small Screen GUI installation complete!${NC}"
    log ""
    log "To start the GUI:"
    log "  blue-relay-chat-gui"
    log ""
    log "To start the service:"
    log "  sudo systemctl start blue-relay-chat"
    log ""
    log "To check the service status:"
    log "  sudo systemctl status blue-relay-chat"
    log ""
    log "To view logs:"
    log "  sudo journalctl -u blue-relay-chat -f"
    log ""
    log "Configuration file:"
    log "  /home/$SERVICE_USER/.config/blue-relay-chat/config.ini"
    log ""
    log "For more information, see:"
    log "  README_Small_Screen_GUI.md"
    log "  TESTING_Small_Screen_GUI.md"
}

# Main installation function
main() {
    log "Starting Blue Relay Chat Small Screen GUI installation..."
    
    # Run checks
    check_root
    check_raspberry_pi
    check_requirements
    
    # Install components
    create_install_dir
    setup_source
    setup_python_env
    setup_config
    install_service
    create_cli_shortcut
    post_install_checks
    
    # Display summary
    display_summary
}

# Parse command line arguments
case "$1" in
    --help|-h)
        echo "Blue Relay Chat Small Screen GUI Installation Script"
        echo ""
        echo "This script installs Blue Relay Chat with small screen GUI support"
        echo ""
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --help, -h              Show this help message"
        echo ""
        exit 0
        ;;
    *)
        # Default behavior
        main
        ;;
esac