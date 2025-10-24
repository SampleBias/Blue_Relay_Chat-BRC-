#!/bin/bash

# Blue Relay Chat RPi 4 Uninstallation Script
# This script removes Blue Relay Chat from a Raspberry Pi 4

set -e  # Exit on any error

# Configuration
INSTALL_DIR="/opt/blue-relay-chat"
SERVICE_USER="pi"

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

# Ask for confirmation
confirm_uninstall() {
    echo -e "${RED}WARNING: This will completely remove Blue Relay Chat from your system.${NC}"
    echo -e "${RED}All data, including messages and identity, will be permanently deleted.${NC}"
    echo
    read -p "Are you sure you want to continue? (type 'yes' to confirm): " -r
    
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log "Uninstallation cancelled."
        exit 0
    fi
    
    # Second confirmation
    echo
    read -p "This is your last chance. Are you absolutely sure? (type 'yes' to confirm): " -r
    
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log "Uninstallation cancelled."
        exit 0
    fi
}

# Stop and disable services
stop_services() {
    log "Stopping and disabling services..."
    
    # Stop and disable systemd service
    if systemctl is-active --quiet blue-relay-chat.service; then
        sudo systemctl stop blue-relay-chat.service
        log "Stopped blue-relay-chat.service"
    fi
    
    if systemctl is-enabled --quiet blue-relay-chat.service; then
        sudo systemctl disable blue-relay-chat.service
        log "Disabled blue-relay-chat.service"
    fi
    
    # Stop and disable user service
    if systemctl --user is-active --quiet blue-relay-chat-user.service; then
        systemctl --user stop blue-relay-chat-user.service
        log "Stopped blue-relay-chat-user.service"
    fi
    
    if systemctl --user is-enabled --quiet blue-relay-chat-user.service; then
        systemctl --user disable blue-relay-chat-user.service
        log "Disabled blue-relay-chat-user.service"
    fi
    
    log "Services stopped and disabled."
}

# Remove service files
remove_service_files() {
    log "Removing service files..."
    
    # Remove systemd service file
    if [[ -f /etc/systemd/system/blue-relay-chat.service ]]; then
        sudo rm /etc/systemd/system/blue-relay-chat.service
        sudo systemctl daemon-reload
        log "Removed blue-relay-chat.service"
    fi
    
    # Remove user service file
    if [[ -f /home/$SERVICE_USER/.config/systemd/user/blue-relay-chat-user.service ]]; then
        rm /home/$SERVICE_USER/.config/systemd/user/blue-relay-chat-user.service
        systemctl --user daemon-reload
        log "Removed blue-relay-chat-user.service"
    fi
    
    log "Service files removed."
}

# Remove application files
remove_app_files() {
    log "Removing application files..."
    
    # Remove installation directory
    if [[ -d $INSTALL_DIR ]]; then
        sudo rm -rf $INSTALL_DIR
        log "Removed installation directory: $INSTALL_DIR"
    fi
    
    # Remove CLI shortcut
    if [[ -L /usr/local/bin/blue-relay-chat ]]; then
        sudo rm /usr/local/bin/blue-relay-chat
        log "Removed CLI shortcut"
    fi
    
    # Remove desktop shortcut
    if [[ -f /home/$SERVICE_USER/Desktop/BlueRelayChat.desktop ]]; then
        rm /home/$SERVICE_USER/Desktop/BlueRelayChat.desktop
        log "Removed desktop shortcut"
    fi
    
    log "Application files removed."
}

# Remove data and configuration
remove_data_config() {
    log "Removing data and configuration..."
    
    # Remove config directory
    if [[ -d /home/$SERVICE_USER/.config/blue-relay-chat ]]; then
        rm -rf /home/$SERVICE_USER/.config/blue-relay-chat
        log "Removed configuration directory"
    fi
    
    # Remove data directory
    if [[ -d /home/$SERVICE_USER/.local/share/blue-relay-chat ]]; then
        rm -rf /home/$SERVICE_USER/.local/share/blue-relay-chat
        log "Removed data directory"
    fi
    
    # Remove log directory
    if [[ -d /var/log/blue-relay-chat ]]; then
        sudo rm -rf /var/log/blue-relay-chat
        log "Removed log directory"
    fi
    
    log "Data and configuration removed."
}

# Clean up system
cleanup_system() {
    log "Cleaning up system..."
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    # Reset user systemd
    systemctl --user daemon-reload
    
    # Remove user from bluetooth group (optional)
    # Uncomment the following line if you want to remove the user from the bluetooth group
    # sudo gpasswd -d $SERVICE_USER bluetooth
    
    log "System cleanup complete."
}

# Display uninstallation summary
display_summary() {
    log "Uninstallation complete!"
    echo
    echo "Blue Relay Chat has been completely removed from your system."
    echo "All data, including messages and identity, has been permanently deleted."
    echo
    echo "If you want to reinstall Blue Relay Chat in the future, you can"
    echo "download the installation script from:"
    echo "  https://github.com/blue-relay-chat/blue-relay-chat-rpi4"
    echo
}

# Main uninstallation function
main() {
    log "Starting Blue Relay Chat uninstallation..."
    
    # Run checks
    check_root
    confirm_uninstall
    
    # Stop and disable services
    stop_services
    
    # Remove service files
    remove_service_files
    
    # Remove application files
    remove_app_files
    
    # Remove data and configuration
    remove_data_config
    
    # Clean up system
    cleanup_system
    
    # Display summary
    display_summary
    
    log "Uninstallation completed successfully!"
}

# Parse command line arguments
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo "Blue Relay Chat Uninstallation Script"
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  --help, -h              Show this help message"
    echo "  --keep-data             Keep data and configuration files"
    echo
    exit 0
fi

# Check for --keep-data option
if [[ "$1" == "--keep-data" ]]; then
    # Override the remove_data_config function
    remove_data_config() {
        log "Keeping data and configuration files..."
        echo
        echo "Data and configuration files have been preserved:"
        echo "  Configuration: /home/$SERVICE_USER/.config/blue-relay-chat"
        echo "  Data: /home/$SERVICE_USER/.local/share/blue-relay-chat"
        echo "  Logs: /var/log/blue-relay-chat"
        echo
    }
fi

# Run main function
main "$@"