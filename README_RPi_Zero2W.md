# Blue Relay Chat - Raspberry Pi Zero 2 W Support

This document provides specific information about running Blue Relay Chat on the Raspberry Pi Zero 2 W.

## Overview

The Raspberry Pi Zero 2 W is fully supported by Blue Relay Chat with optimized settings for its hardware constraints (512MB RAM, quad-core ARM Cortex-A53 @ 1.0GHz).

## Hardware Specifications

- **CPU**: Broadcom BCM2710A1, Quad-core Cortex-A53 (ARMv8) @ 1.0GHz
- **RAM**: 512MB LPDDR2 SDRAM
- **Connectivity**: 2.4GHz WiFi, Bluetooth 5.0, BLE
- **GPIO**: 40-pin GPIO header
- **Storage**: MicroSD card slot
- **Form Factor**: 65mm x 30mm compact board

## Installation

### Quick Install

```bash
# Download and run the Pi Zero 2 W installer
curl -fsSL https://raw.githubusercontent.com/blue-relay-chat/blue-relay-chat-rpi4/main/scripts/install_rpi_zero2w.sh | bash

# Or clone and run manually
git clone https://github.com/blue-relay-chat/blue-relay-chat-rpi4.git
cd blue-relay-chat-rpi4
chmod +x scripts/install_rpi_zero2w.sh
./scripts/install_rpi_zero2w.sh
```

### Manual Installation

1. Install system dependencies:
   ```bash
   sudo apt-get update
   sudo apt-get install -y python3 python3-pip python3-venv python3-dev git libbluetooth-dev libglib2.0-dev bluez systemd sqlite3 libsqlite3-dev curl wget wireless-tools rfkill pi-bluetooth raspberrypi-bootloader raspberrypi-kernel
   ```

2. Clone repository and setup Python environment:
   ```bash
   git clone https://github.com/blue-relay-chat/blue-relay-chat-rpi4.git /opt/blue-relay-chat
   cd /opt/blue-relay-chat
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Copy optimized configuration:
   ```bash
   cp config_rpi_zero2w.ini ~/.config/blue-relay-chat/config.ini
   ```

4. Install and enable systemd service:
   ```bash
   sudo cp systemd/blue-relay-chat-rpi-zero2w.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable blue-relay-chat.service
   ```

## Configuration Optimizations

The Pi Zero 2 W configuration includes these optimizations:

### Performance Settings
- **Memory Limit**: 150MB (with 1GB swap file)
- **CPU Usage**: 60% maximum
- **Message Queue**: 300 messages (reduced from 1000)
- **Compression Threshold**: 200 bytes (increased to reduce CPU usage)

### Bluetooth Settings
- **Max Peers**: 15 (reduced from 50)
- **Scan Interval**: 15 seconds (increased to reduce CPU usage)
- **Mesh TTL**: 5 hops (reduced for smaller networks)
- **Discovery Timeout**: 45 seconds (increased for reliability)

### Nostr Settings
- **Max Relay Connections**: 2 (reduced from 5)
- **Subscription Limit**: 5 (reduced from 10)
- **Event Batch Size**: 20 (reduced from 50)
- **Connection Timeout**: 30 seconds (increased for stability)

### System Optimizations
- **1GB Swap File**: Automatically created for memory management
- **GPU Memory**: 16MB minimum (frees RAM for applications)
- **Bluetooth Overlay**: Added to boot configuration
- **CPU Quota**: 80% in systemd service

## Usage

### Starting the Service

```bash
# Start the service
sudo systemctl start blue-relay-chat

# Check status
sudo systemctl status blue-relay-chat

# View logs
sudo journalctl -u blue-relay-chat -f
```

### Running Manually

```bash
# Activate virtual environment
source /opt/blue-relay-chat/venv/bin/activate

# Run the application
cd /opt/blue-relay-chat
python main.py
```

## GPIO Configuration

The emergency wipe function uses GPIO pin 18 by default. This can be changed in the configuration file:

```ini
[security]
emergency_wipe_gpio = 18
```

## Performance Tips

1. **Disable GUI**: For better performance, disable the desktop environment:
   ```bash
   sudo systemctl disable lightdm
   ```

2. **Use Headless Mode**: Run without connected display for best performance

3. **Monitor Resources**: Use `htop` to monitor memory and CPU usage

4. **Optimize Storage**: Use high-quality microSD cards (Class 10 or higher)

5. **Power Supply**: Use a stable 2.5A power supply for reliable operation

## Troubleshooting

### Common Issues

1. **Out of Memory Errors**:
   - Check swap file: `swapon --show`
   - Monitor memory: `free -h`
   - Reduce max_peers in configuration

2. **Bluetooth Issues**:
   - Check service: `sudo systemctl status bluetooth`
   - Unblock if needed: `sudo rfkill unblock bluetooth`
   - Verify adapter: `hciconfig`

3. **Slow Performance**:
   - Check CPU temperature: `vcgencmd measure_temp`
   - Monitor CPU usage: `top`
   - Consider overclocking (with cooling)

4. **Service Won't Start**:
   - Check logs: `sudo journalctl -u blue-relay-chat -n 50`
   - Verify configuration: `python -c "import bitchat.config.manager; print(bitchat.config.manager.ConfigManager())"`
   - Check permissions: `ls -la /opt/blue-relay-chat`

### Getting Help

- **GitHub Issues**: https://github.com/blue-relay-chat/blue-relay-chat-rpi4/issues
- **Documentation**: https://github.com/blue-relay-chat/blue-relay-chat-rpi4/wiki
- **Community**: Check discussions on GitHub repository

## Hardware Comparison

| Feature | Pi Zero 2 W | Pi 4 | Orange Pi Zero 2W |
|---------|---------------|-------|-------------------|
| CPU | 4x Cortex-A53 @ 1.0GHz | 4x Cortex-A72 @ 1.5GHz | 4x Cortex-A53 @ 1.5GHz |
| RAM | 512MB LPDDR2 | 1-8GB LPDDR4 | 512MB-1GB LPDDR4 |
| WiFi | 2.4GHz only | 2.4/5GHz | 2.4/5GHz |
| Bluetooth | 5.0 | 5.0 | 5.0 |
| GPIO | 40-pin | 40-pin | 26-pin |
| Size | 65x30mm | 85x56mm | 60x45mm |
| Power | Low | Medium | Low |

## Development

For developers wanting to optimize for Pi Zero 2 W:

1. **Hardware Detection**: Use the built-in hardware detection:
   ```python
   from bitchat.utils.hardware_detection import get_hardware_info
   
   info = get_hardware_info()
   if info["detected_hardware"] == "rpi-zero2w":
       # Apply Pi Zero 2 W specific optimizations
   ```

2. **Configuration**: Access hardware-specific settings:
   ```python
   from bitchat.config.manager import ConfigManager
   
   config = ConfigManager()
   if config.get_hardware_profile_name() == "Raspberry Pi Zero 2 W":
       # Use optimized settings
   ```

3. **Testing**: Test with memory constraints:
   ```bash
   # Simulate low memory conditions
   sudo systemctl set-property blue-relay-chat MemoryLimit=100M
   ```

## Conclusion

The Raspberry Pi Zero 2 W provides an excellent balance of performance, size, and power efficiency for Blue Relay Chat. With the optimizations included in this implementation, it can effectively serve as a mesh networking node while maintaining low power consumption and a small physical footprint.