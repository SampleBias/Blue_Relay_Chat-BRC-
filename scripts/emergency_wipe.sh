#!/bin/bash

# Blue Relay Chat Emergency Wipe Script
# This script performs an emergency wipe of all Blue Relay Chat data

set -e  # Exit on any error

# Configuration
SERVICE_USER="pi"
DATA_DIR="/home/$SERVICE_USER/.local/share/blue-relay-chat"
CONFIG_DIR="/home/$SERVICE_USER/.config/blue-relay-chat"
LOG_DIR="/var/log/blue-relay-chat"

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
confirm_wipe() {
    echo -e "${RED}EMERGENCY WIPE: This will permanently delete all Blue Relay Chat data.${NC}"
    echo -e "${RED}This includes messages, identity, configuration, and logs.${NC}"
    echo -e "${RED}This action cannot be undone!${NC}"
    echo
    read -p "Are you absolutely sure you want to continue? (type 'EMERGENCY WIPE' to confirm): " -r
    
    if [[ ! $REPLY =~ ^[Ee][Mm][Ee][Rr][Gg][Ee][Nn][Cc][Yy][[:space:]]*[Ww][Ii][Pp][Ee]$ ]]; then
        log "Emergency wipe cancelled."
        exit 0
    fi
    
    # Second confirmation
    echo
    echo -e "${RED}This is your final warning. All data will be permanently lost.${NC}"
    read -p "Type 'FINAL CONFIRMATION' to proceed: " -r
    
    if [[ ! $REPLY =~ ^[Ff][Ii][Nn][Aa][Ll][[:space:]]*[Cc][Oo][Nn][Ff][Ii][Rr][Mm][Aa][Tt][Ii][Oo][Nn]$ ]]; then
        log "Emergency wipe cancelled."
        exit 0
    fi
}

# Stop services
stop_services() {
    log "Stopping Blue Relay Chat services..."
    
    # Stop systemd service
    if systemctl is-active --quiet blue-relay-chat.service; then
        sudo systemctl stop blue-relay-chat.service
        log "Stopped blue-relay-chat.service"
    fi
    
    # Stop user service
    if systemctl --user is-active --quiet blue-relay-chat-user.service; then
        systemctl --user stop blue-relay-chat-user.service
        log "Stopped blue-relay-chat-user.service"
    fi
    
    log "Services stopped."
}

# Wipe data directory
wipe_data() {
    log "Wiping data directory..."
    
    if [[ -d $DATA_DIR ]]; then
        # Securely delete files
        find $DATA_DIR -type f -exec shred -vfz -n 3 {} \;
        
        # Remove directory
        rm -rf $DATA_DIR
        log "Data directory wiped: $DATA_DIR"
    else
        log "Data directory not found: $DATA_DIR"
    fi
}

# Wipe configuration directory
wipe_config() {
    log "Wiping configuration directory..."
    
    if [[ -d $CONFIG_DIR ]]; then
        # Securely delete files
        find $CONFIG_DIR -type f -exec shred -vfz -n 3 {} \;
        
        # Remove directory
        rm -rf $CONFIG_DIR
        log "Configuration directory wiped: $CONFIG_DIR"
    else
        log "Configuration directory not found: $CONFIG_DIR"
    fi
}

# Wipe log directory
wipe_logs() {
    log "Wiping log directory..."
    
    if [[ -d $LOG_DIR ]]; then
        # Securely delete files
        sudo find $LOG_DIR -type f -exec shred -vfz -n 3 {} \;
        
        # Remove directory
        sudo rm -rf $LOG_DIR
        log "Log directory wiped: $LOG_DIR"
    else
        log "Log directory not found: $LOG_DIR"
    fi
}

# Wipe temporary files
wipe_temp() {
    log "Wiping temporary files..."
    
    # Find and wipe temporary files
    find /tmp -name "*blue-relay-chat*" -type f -exec shred -vfz -n 3 {} \; 2>/dev/null || true
    find /var/tmp -name "*blue-relay-chat*" -type f -exec shred -vfz -n 3 {} \; 2>/dev/null || true
    
    # Find and wipe cache files
    find /home/$SERVICE_USER/.cache -name "*blue-relay-chat*" -type f -exec shred -vfz -n 3 {} \; 2>/dev/null || true
    
    log "Temporary files wiped."
}

# Clear free space
clear_free_space() {
    log "Clearing free space..."
    
    # Create a large temporary file to fill free space
    TEMP_FILE="/tmp/blue-relay-chat-wipe-$$"
    
    # Fill free space with random data
    dd if=/dev/urandom of=$TEMP_FILE bs=1M 2>/dev/null || true
    
    # Remove the file
    shred -vfz -n 3 $TEMP_FILE
    rm -f $TEMP_FILE
    
    log "Free space cleared."
}

# Display wipe summary
display_summary() {
    log "Emergency wipe complete!"
    echo
    echo -e "${RED}All Blue Relay Chat data has been permanently deleted.${NC}"
    echo
    echo "The following has been wiped:"
    echo "  - Data directory: $DATA_DIR"
    echo "  - Configuration directory: $CONFIG_DIR"
    echo "  - Log directory: $LOG_DIR"
    echo "  - Temporary files"
    echo "  - Free space"
    echo
    echo "Blue Relay Chat is now completely removed from your system."
    echo
}

# Main wipe function
main() {
    log "Starting emergency wipe of Blue Relay Chat data..."
    
    # Run checks
    check_root
    confirm_wipe
    
    # Stop services
    stop_services
    
    # Wipe data
    wipe_data
    wipe_config
    wipe_logs
    wipe_temp
    
    # Clear free space
    clear_free_space
    
    # Display summary
    display_summary
    
    log "Emergency wipe completed successfully!"
}

# Parse command line arguments
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo "Blue Relay Chat Emergency Wipe Script"
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  --help, -h              Show this help message"
    echo "  --quick                 Quick wipe (less secure, faster)"
    echo
    exit 0
fi

# Check for --quick option
if [[ "$1" == "--quick" ]]; then
    # Override the wipe functions for quick wipe
    wipe_data() {
        log "Quick wiping data directory..."
        
        if [[ -d $DATA_DIR ]]; then
            # Just remove the directory
            rm -rf $DATA_DIR
            log "Data directory quickly wiped: $DATA_DIR"
        else
            log "Data directory not found: $DATA_DIR"
        fi
    }
    
    wipe_config() {
        log "Quick wiping configuration directory..."
        
        if [[ -d $CONFIG_DIR ]]; then
            # Just remove the directory
            rm -rf $CONFIG_DIR
            log "Configuration directory quickly wiped: $CONFIG_DIR"
        else
            log "Configuration directory not found: $CONFIG_DIR"
        fi
    }
    
    wipe_logs() {
        log "Quick wiping log directory..."
        
        if [[ -d $LOG_DIR ]]; then
            # Just remove the directory
            sudo rm -rf $LOG_DIR
            log "Log directory quickly wiped: $LOG_DIR"
        else
            log "Log directory not found: $LOG_DIR"
        fi
    }
    
    wipe_temp() {
        log "Quick wiping temporary files..."
        
        # Just remove temporary files
        find /tmp -name "*blue-relay-chat*" -type f -delete 2>/dev/null || true
        find /var/tmp -name "*blue-relay-chat*" -type f -delete 2>/dev/null || true
        find /home/$SERVICE_USER/.cache -name "*blue-relay-chat*" -type f -delete 2>/dev/null || true
        
        log "Temporary files quickly wiped."
    }
    
    # Skip free space clearing for quick wipe
    clear_free_space() {
        log "Skipping free space clearing for quick wipe."
    }
fi

# Run main function
main "$@"