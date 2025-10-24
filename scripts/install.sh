#!/bin/bash

# Blue Relay Chat RPi 4 Installation Script
# This script installs Blue Relay Chat on a Raspberry Pi 4

set -e  # Exit on any error

# Configuration
INSTALL_DIR="/opt/blue-relay-chat"
SERVICE_USER="pi"
PYTHON_VERSION="3.9"
VENV_DIR="$INSTALL_DIR/venv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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
check_rpi() {
    if [[ ! -f /proc/device-tree/model ]] || ! grep -q "Raspberry Pi" /proc/device-tree/model; then
        error "This script is designed for Raspberry Pi. Detected system is not a Raspberry Pi."
    fi
    
    local MODEL=$(tr -d '\0' < /proc/device-tree/model)
    log "Detected Raspberry Pi model: $MODEL"
}

# Check system requirements
check_requirements() {
    log "Checking system requirements..."
    
    # Check for sufficient disk space (at least 1GB)
    local AVAILABLE_SPACE=$(df / | awk 'NR==2 {print $4}')
    if [[ $AVAILABLE_SPACE -lt 1048576 ]]; then
        error "Insufficient disk space. At least 1GB required."
    fi
    
    # Check for sufficient memory (at least 1GB)
    local AVAILABLE_MEMORY=$(free -m | awk 'NR==2{print $7}')
    if [[ $AVAILABLE_MEMORY -lt 1024 ]]; then
        warn "Low available memory. At least 1GB recommended."
    fi
    
    # Check for internet connection
    if ! ping -c 1 google.com &> /dev/null; then
        error "No internet connection. Please check your network settings."
    fi
    
    log "System requirements check passed."
}

# Install system dependencies
install_system_deps() {
    log "Installing system dependencies..."
    
    # Update package lists
    sudo apt-get update
    
    # Install required packages
    sudo apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        git \
        libbluetooth-dev \
        libglib2.0-dev \
        bluez \
        systemd \
        sqlite3 \
        libsqlite3-dev \
        curl \
        wget
    
    # Install optional packages for better performance
    sudo apt-get install -y \
        libbz2-dev \
        liblzma-dev \
        libreadline-dev \
        libssl-dev \
        libffi-dev
    
    log "System dependencies installed."
}

# Create installation directory
create_install_dir() {
    log "Creating installation directory..."
    
    # Create directory if it doesn't exist
    sudo mkdir -p $INSTALL_DIR
    
    # Set ownership
    sudo chown $SERVICE_USER:$SERVICE_USER $INSTALL_DIR
    
    log "Installation directory created."
}

# Clone or update the repository
setup_source() {
    log "Setting up source code..."
    
    # Check if the directory is a git repository
    if [[ -d "$INSTALL_DIR/.git" ]]; then
        log "Repository already exists, updating..."
        cd $INSTALL_DIR
        git pull origin main
    else
        log "Cloning repository..."
        git clone https://github.com/blue-relay-chat/blue-relay-chat-rpi4.git $INSTALL_DIR
        cd $INSTALL_DIR
    fi
    
    log "Source code setup complete."
}

# Create Python virtual environment
setup_python_env() {
    log "Setting up Python virtual environment..."
    
    # Create virtual environment
    python3 -m venv $VENV_DIR
    
    # Activate virtual environment
    source $VENV_DIR/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    pip install -r requirements.txt
    
    log "Python environment setup complete."
}

# Setup configuration
setup_config() {
    log "Setting up configuration..."
    
    # Create config directory
    mkdir -p /home/$SERVICE_USER/.config/blue-relay-chat
    
    # Create data directory
    mkdir -p /home/$SERVICE_USER/.local/share/blue-relay-chat
    
    # Create log directory
    sudo mkdir -p /var/log/blue-relay-chat
    sudo chown $SERVICE_USER:$SERVICE_USER /var/log/blue-relay-chat
    
    # Copy default config if it doesn't exist
    if [[ ! -f /home/$SERVICE_USER/.config/blue-relay-chat/config.ini ]]; then
        cp config.ini /home/$SERVICE_USER/.config/blue-relay-chat/config.ini
        chown $SERVICE_USER:$SERVICE_USER /home/$SERVICE_USER/.config/blue-relay-chat/config.ini
    fi
    
    log "Configuration setup complete."
}

# Install systemd service
install_service() {
    log "Installing systemd service..."
    
    # Copy service file
    sudo cp systemd/blue-relay-chat.service /etc/systemd/system/
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    # Enable service
    sudo systemctl enable blue-relay-chat.service
    
    log "Systemd service installed."
}

# Install user service (optional)
install_user_service() {
    log "Installing user service..."
    
    # Create user service directory
    mkdir -p /home/$SERVICE_USER/.config/systemd/user
    
    # Copy user service file
    cp systemd/blue-relay-chat-user.service /home/$SERVICE_USER/.config/systemd/user/
    
    # Reload user systemd
    systemctl --user daemon-reload
    
    # Enable user service
    systemctl --user enable blue-relay-chat-user.service
    
    log "User service installed."
}

# Create command-line shortcut
create_cli_shortcut() {
    log "Creating command-line shortcut..."
    
    # Create a symlink to the main script
    sudo ln -sf $INSTALL_DIR/main.py /usr/local/bin/blue-relay-chat
    sudo chmod +x /usr/local/bin/blue-relay-chat
    
    log "Command-line shortcut created."
}

# Setup Bluetooth permissions
setup_bluetooth() {
    log "Setting up Bluetooth permissions..."
    
    # Add user to bluetooth group
    sudo usermod -a -G bluetooth $SERVICE_USER
    
    # Enable and start Bluetooth service
    sudo systemctl enable bluetooth
    sudo systemctl start bluetooth
    
    log "Bluetooth permissions setup complete."
}

# Create desktop shortcut (optional)
create_desktop_shortcut() {
    log "Creating desktop shortcut..."
    
    # Create desktop entry
    cat > /home/$SERVICE_USER/Desktop/BlueRelayChat.desktop << EOF
[Desktop Entry]
Name=Blue Relay Chat
Comment=Decentralized messaging client
Exec=python3 $INSTALL_DIR/main.py
Icon=$INSTALL_DIR/assets/icon.png
Terminal=true
Type=Application
Categories=Network;
EOF
    
    # Make it executable
    chmod +x /home/$SERVICE_USER/Desktop/BlueRelayChat.desktop
    
    log "Desktop shortcut created."
}

# Run post-installation checks
post_install_checks() {
    log "Running post-installation checks..."
    
    # Check if virtual environment exists
    if [[ ! -d "$VENV_DIR" ]]; then
        error "Virtual environment not found."
    fi
    
    # Check if main script exists
    if [[ ! -f "$INSTALL_DIR/main.py" ]]; then
        error "Main script not found."
    fi
    
    # Check if config file exists
    if [[ ! -f "/home/$SERVICE_USER/.config/blue-relay-chat/config.ini" ]]; then
        error "Configuration file not found."
    fi
    
    # Check if service file exists
    if [[ ! -f "/etc/systemd/system/blue-relay-chat.service" ]]; then
        error "Service file not found."
    fi
    
    log "Post-installation checks passed."
}

# Display installation summary
display_summary() {
    log "Installation complete!"
    echo
    echo "Blue Relay Chat has been installed to: $INSTALL_DIR"
    echo
    echo "To start the service:"
    echo "  sudo systemctl start blue-relay-chat"
    echo
    echo "To check the service status:"
    echo "  sudo systemctl status blue-relay-chat"
    echo
    echo "To view logs:"
    echo "  sudo journalctl -u blue-relay-chat -f"
    echo
    echo "To run the application directly:"
    echo "  blue-relay-chat"
    echo
    echo "Configuration file location:"
    echo "  /home/$SERVICE_USER/.config/blue-relay-chat/config.ini"
    echo
    echo "Data directory:"
    echo "  /home/$SERVICE_USER/.local/share/blue-relay-chat"
    echo
    echo "For more information, see the documentation at:"
    echo "  https://github.com/blue-relay-chat/blue-relay-chat-rpi4"
    echo
}

# Main installation function
main() {
    log "Starting Blue Relay Chat installation..."
    
    # Run checks
    check_root
    check_rpi
    check_requirements
    
    # Install dependencies
    install_system_deps
    
    # Setup application
    create_install_dir
    setup_source
    setup_python_env
    setup_config
    install_service
    install_user_service
    create_cli_shortcut
    setup_bluetooth
    
    # Optional components
    if [[ "$1" == "--with-desktop" ]]; then
        create_desktop_shortcut
    fi
    
    # Final checks
    post_install_checks
    display_summary
    
    log "Installation completed successfully!"
}

# Parse command line arguments
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo "Blue Relay Chat Installation Script"
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  --help, -h              Show this help message"
    echo "  --with-desktop          Create desktop shortcut"
    echo
    exit 0
fi

# Run main function
main "$@"