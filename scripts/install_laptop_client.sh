#!/bin/bash
# Installation script for Blue Relay Chat laptop client.

# This script installs all necessary dependencies and sets up
# the environment for running the laptop client.

set -e  # Exit on any error

echo "Blue Relay Chat - Laptop Client Installation"
echo "=============================================="

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)

if [ "$PYTHON_MAJOR" -lt "3" ]; then
    echo "Error: Python 3.8 or higher is required"
    echo "Current version: $PYTHON_VERSION"
    exit 1
fi

echo "Python version: $PYTHON_VERSION ✓"

# Check operating system
echo "Checking operating system..."
OS=$(uname -s)
echo "Operating system: $OS ✓"

# Install system dependencies
echo "Installing system dependencies..."
if [ "$OS" = "Linux" ]; then
    # Linux dependencies
    echo "Installing Linux packages..."
    
    # Update package list
    sudo apt update
    
    # Install basic dependencies
    sudo apt install -y python3-pip python3-dev python3-setuptools
    
    # Install Bluetooth dependencies
    sudo apt install -y bluetooth bluez libbluetooth-dev libudev-dev
    
    # Install GUI dependencies
    sudo apt install -y python3-tk python3-dev
    
    # Install crypto dependencies
    sudo apt install -y libssl-dev libffi-dev
    
    echo "Linux dependencies installed ✓"
    
elif [ "$OS" = "Darwin" ]; then
    # macOS dependencies
    echo "Installing macOS packages..."
    
    # Install Homebrew if not available
    if ! command -v brew &> /dev/null; then
        echo "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        eval "$(/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)")"
    fi
    
    # Install Python dependencies
    brew install python-tk
    
    # Install Bluetooth dependencies
    # macOS typically includes Bluetooth support out of the box
    
    echo "macOS dependencies installed ✓"
    
elif [ "$OS" = "MINGW64_NT-10.0" ] || [ "$OS" = "MSYS_NT-10.0" ] || [ "$OS" = "CYGWIN_NT-10.0" ]; then
    # Windows dependencies
    echo "Installing Windows packages..."
    
    # Windows typically includes Bluetooth support out of the box
    # Python packages will be installed via pip
    
    echo "Windows dependencies will be installed via pip ✓"
    
else
    echo "Warning: Unsupported operating system: $OS"
    echo "Please check the documentation for manual installation instructions"
    exit 1
fi

# Create virtual environment
echo "Setting up Python virtual environment..."
VENV_DIR="$HOME/.local/share/blue-relay-chat/venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    mkdir -p "$VENV_DIR"
    python3 -m venv "$VENV_DIR"
fi

echo "Virtual environment: $VENV_DIR ✓"

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip install bleak>=0.20.0
pip install cryptography>=41.0.0
pip install aiofiles>=23.0.0
pip install aiosqlite>=0.19.0
pip install sqlalchemy[asyncio]>=2.0.0
pip install lz4>=4.0.0
pip install pygeohash>=1.3.0
pip install structlog>=23.0.0

# Install development dependencies
echo "Installing development dependencies..."
pip install pytest>=7.4.0
pip install pytest-asyncio>=0.21.0
pip install pytest-cov>=4.1.0
pip install pytest-mock>=3.11.0
pip install black>=23.0.0
pip install flake8>=6.0.0
pip install mypy>=1.5.0
pip install pre-commit>=3.3.0

# Create desktop entry
echo "Creating desktop entry..."
DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"

cat > "$DESKTOP_DIR/blue-relay-chat.desktop" << EOF
[Desktop Entry]
Name=Blue Relay Chat
Comment=Decentralized Bluetooth Messaging
Exec=$VENV_DIR/bin/python3 $(pwd)/main_laptop.py
Icon=$(pwd)/assets/icons/blue_relay_chat.png
Terminal=false
Type=Application
Categories=Network;Chat;
EOF

echo "Desktop entry created: $DESKTOP_DIR/blue-relay-chat.desktop ✓"

# Create launcher script
echo "Creating launcher script..."
LAUNCHER_DIR="$HOME/.local/bin"
mkdir -p "$LAUNCHER_DIR"

cat > "$LAUNCHER_DIR/blue-relay-chat" << EOF
#!/bin/bash
# Blue Relay Chat launcher script

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Run the application
cd "$(pwd)"
python3 main_laptop.py
EOF

chmod +x "$LAUNCHER_DIR/blue-relay-chat"

echo "Launcher script created: $LAUNCHER_DIR/blue-relay-chat ✓"

# Create configuration directory
echo "Setting up configuration directory..."
CONFIG_DIR="$HOME/.config/blue-relay-chat"
mkdir -p "$CONFIG_DIR"

# Copy default configuration
if [ -f "config_laptop.ini" ]; then
    cp config_laptop.ini "$CONFIG_DIR/config.ini"
    echo "Configuration file copied to: $CONFIG_DIR/config.ini ✓"
fi

echo ""
echo "Installation completed successfully!"
echo ""
echo "To run Blue Relay Chat:"
echo "1. Using the launcher: $LAUNCHER_DIR/blue-relay-chat"
echo "2. From the command line: $VENV_DIR/bin/python3 $(pwd)/main_laptop.py"
echo ""
echo "To uninstall:"
echo "1. Remove the virtual environment: rm -rf $VENV_DIR"
echo "2. Remove the desktop entry: rm $DESKTOP_DIR/blue-relay-chat.desktop"
echo "3. Remove the launcher: rm $LAUNCHER_DIR/blue-relay-chat"
echo ""
echo "Enjoy using Blue Relay Chat!"