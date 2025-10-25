# Blue Relay Chat - Laptop Client User Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Getting Started](#getting-started)
4. [User Interface](#user-interface)
5. [Connecting to Devices](#connecting-to-devices)
6. [Sending Messages](#sending-messages)
7. [Managing Channels](#managing-channels)
8. [Settings and Configuration](#settings-and-configuration)
9. [Troubleshooting](#troubleshooting)
10. [Advanced Features](#advanced-features)

## Introduction

Blue Relay Chat (BRC) is a decentralized messaging application that uses Bluetooth mesh networking to enable communication between devices without requiring internet connectivity. The laptop client provides a simple, cross-platform interface for participating in BRC networks from your Windows, macOS, or Linux laptop.

### Key Features

- **Decentralized Communication**: No central server required
- **Bluetooth Mesh**: Automatic message routing through nearby devices
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **End-to-End Encryption**: Secure communication between devices
- **Simple Interface**: Minimal, easy-to-use design
- **Real-Time Chat**: Instant messaging with nearby BRC devices

### System Requirements

#### Minimum Requirements
- **Operating System**: Windows 10, macOS 10.15, or Linux (Ubuntu 20.04+)
- **Bluetooth**: Bluetooth 4.0+ with BLE support
- **Memory**: 512MB RAM minimum
- **Storage**: 50MB free disk space
- **Python**: Python 3.8 or later (included in installer)

#### Recommended Requirements
- **Operating System**: Windows 11, macOS 12+, or Linux (Ubuntu 22.04+)
- **Bluetooth**: Bluetooth 5.0+ for better range and speed
- **Memory**: 2GB RAM or more
- **Storage**: 200MB free disk space

## Installation

### Windows Installation

1. **Download the Installer**
   - Visit the [Blue Relay Chat releases page](https://github.com/blue-relay-chat/blue-relay-chat/releases)
   - Download `BlueRelayChat-Setup-1.0.0.exe`

2. **Run the Installer**
   - Double-click the downloaded installer
   - Follow the installation wizard
   - Choose installation directory (default: `C:\Program Files\Blue Relay Chat`)

3. **Launch the Application**
   - Desktop shortcut: Double-click "Blue Relay Chat"
   - Start Menu: Find "Blue Relay Chat" in your applications
   - Command line: `BlueRelayChat.exe`

4. **Windows Firewall Setup**
   - When prompted, allow Blue Relay Chat through Windows Firewall
   - This enables Bluetooth communication with other devices

### macOS Installation

1. **Download the DMG**
   - Visit the [Blue Relay Chat releases page](https://github.com/blue-relay-chat/blue-relay-chat/releases)
   - Download `BlueRelayChat-1.0.0.dmg`

2. **Install the Application**
   - Double-click the downloaded DMG file
   - Drag "Blue Relay Chat" to your Applications folder
   - Eject the DMG when complete

3. **Launch the Application**
   - Finder: Open Applications folder and double-click "Blue Relay Chat"
   - Launchpad: Click the Blue Relay Chat icon
   - Spotlight: Search for "Blue Relay Chat"

4. **macOS Permissions**
   - On first launch, grant Bluetooth permissions when prompted
   - Allow the app to access Bluetooth in System Preferences > Security & Privacy

### Linux Installation

#### Option 1: AppImage (Recommended)

1. **Download the AppImage**
   - Visit the [Blue Relay Chat releases page](https://github.com/blue-relay-chat/blue-relay-chat/releases)
   - Download `BlueRelayChat-1.0.0-x86_64.AppImage`

2. **Make Executable**
   ```bash
   chmod +x BlueRelayChat-1.0.0-x86_64.AppImage
   ```

3. **Run the Application**
   ```bash
   ./BlueRelayChat-1.0.0-x86_64.AppImage
   ```

#### Option 2: Debian/Ubuntu Package

1. **Download the DEB Package**
   - Download `blue-relay-chat_1.0.0_amd64.deb`

2. **Install the Package**
   ```bash
   sudo dpkg -i blue-relay-chat_1.0.0_amd64.deb
   ```

3. **Launch the Application**
   ```bash
   blue-relay-chat
   ```

#### Option 3: Fedora/RPM Package

1. **Download the RPM Package**
   - Download `blue-relay-chat-1.0.0.x86_64.rpm`

2. **Install the Package**
   ```bash
   sudo rpm -i blue-relay-chat-1.0.0.x86_64.rpm
   ```

3. **Launch the Application**
   ```bash
   blue-relay-chat
   ```

### Linux Bluetooth Setup

#### Ubuntu/Debian
```bash
# Install Bluetooth support
sudo apt update
sudo apt install bluetooth bluez

# Add user to bluetooth group
sudo usermod -a -G bluetooth $USER

# Restart Bluetooth service
sudo systemctl restart bluetooth
```

#### Fedora/CentOS
```bash
# Install Bluetooth support
sudo dnf install bluez

# Add user to bluetooth group
sudo usermod -a -G bluetooth $USER

# Enable and start Bluetooth service
sudo systemctl enable bluetooth
sudo systemctl start bluetooth
```

## Getting Started

### First Launch

When you first launch Blue Relay Chat, you'll see:

1. **Welcome Screen**: Brief introduction to the application
2. **Bluetooth Setup**: Automatic detection of your Bluetooth adapter
3. **Identity Creation**: Generate your unique BRC identity
4. **Main Interface**: The chat window with peer list

### Creating Your Identity

Blue Relay Chat automatically creates a cryptographic identity for you:

1. **Key Generation**: Your private key is generated locally
2. **Public ID**: A unique identifier derived from your public key
3. **Display Name**: Choose a name that other users will see

Your identity is stored securely on your device and never transmitted to central servers.

### Basic Navigation

- **Message Input**: Type your message and press Enter or click Send
- **Peer List**: See connected BRC devices on the left
- **Message History**: Scroll through previous messages
- **Status Bar**: View connection status and current channel

## User Interface

### Main Window Layout

```
┌─ Blue Relay Chat ─────────────────────────────────┐
│ Status: Connected (3 peers) | Channel: #bluetooth │
├─────────────────────────────────────────────────────┤
│ Peer List │ Message Display Area                  │
│ ├─ User1  │ ┌─────────────────────────────────────┐ │
│ ├─ User2  │ │ [12:34] User1: Hello there!       │ │
│ ├─ User3  │ │ [12:35] User2: Hi everyone!        │ │
│ └─ ...    │ │ [12:36] System: User4 joined       │ │
│           │ │                                     │ │
│           │ └─────────────────────────────────────┘ │
├─────────────────────────────────────────────────────┤
│ > [Message input field]              [Send] [Join] │
└─────────────────────────────────────────────────────┘
```

### Interface Components

#### Status Bar
- **Connection Status**: Shows if you're connected to the mesh network
- **Peer Count**: Number of directly connected devices
- **Current Channel**: Active chat channel
- **Transport Status**: Bluetooth connectivity indicator

#### Peer List
- **Online Peers**: ● Green indicator for connected devices
- **Connecting Peers**: ◐ Yellow indicator for connecting devices
- **Offline Peers**: ○ Gray indicator for disconnected devices
- **Peer Names**: Display names of nearby BRC devices

#### Message Display
- **Timestamps**: When messages were sent/received
- **Sender Names**: Who sent each message
- **Message Content**: The actual message text
- **System Messages**: Notifications about connections, channels, etc.

#### Input Area
- **Message Field**: Type your messages here
- **Send Button**: Send your message (or press Enter)
- **Join Button**: Join a different channel
- **Channel Selector**: Choose which channel to chat in

### Keyboard Shortcuts

- **Enter**: Send message
- **Ctrl+L**: Clear message input
- **Ctrl+H**: Show/hide help
- **Ctrl+S**: Open settings
- **Ctrl+Q**: Quit application
- **F5**: Refresh peer list
- **Tab**: Cycle through interface elements

## Connecting to Devices

### Automatic Discovery

Blue Relay Chat automatically discovers nearby BRC devices:

1. **Bluetooth Scanning**: Continuously scans for BRC devices
2. **Device Detection**: Identifies devices running Blue Relay Chat
3. **Connection Attempts**: Automatically tries to connect to discovered devices
4. **Mesh Formation**: Creates a network of connected devices

### Manual Connection

If automatic discovery doesn't work:

1. **Check Bluetooth**: Ensure Bluetooth is enabled on your laptop
2. **Device Visibility**: Make sure your device is discoverable
3. **Refresh Peers**: Click the refresh button or press F5
4. **Check Distance**: Ensure devices are within Bluetooth range (typically 10-100 meters)

### Connection Issues

#### Common Problems

1. **Bluetooth Not Available**
   - **Windows**: Check if Bluetooth is enabled in Settings
   - **macOS**: Check Bluetooth in System Preferences
   - **Linux**: Run `sudo systemctl status bluetooth`

2. **No Devices Found**
   - Move closer to other BRC devices
   - Check if other devices have Blue Relay Chat running
   - Restart Bluetooth on your device

3. **Connection Failures**
   - Restart the Blue Relay Chat application
   - Check if Bluetooth adapter is working
   - Try disabling and re-enabling Bluetooth

#### Troubleshooting Steps

1. **Restart Application**: Close and reopen Blue Relay Chat
2. **Reset Bluetooth**: Turn Bluetooth off and on again
3. **Check Permissions**: Ensure the app has Bluetooth permissions
4. **Update Drivers**: Update Bluetooth drivers (Windows/Linux)
5. **Try Different Adapter**: Use an external USB Bluetooth adapter

## Sending Messages

### Basic Messaging

1. **Type Your Message**: Enter text in the input field
2. **Send Message**: Press Enter or click the Send button
3. **Message Routing**: Message is automatically routed through the mesh
4. **Delivery Confirmation**: Message appears in your chat history

### Message Types

#### Text Messages
- **Regular Chat**: Standard text messages to all peers
- **Private Messages**: Direct messages to specific users
- **System Messages**: Notifications about the network

#### Message Limits
- **Maximum Length**: 4096 characters per message
- **Rate Limiting**: 60 messages per minute to prevent spam
- **Character Encoding**: UTF-8 support for international characters

### Message Formatting

Blue Relay Chat supports basic text formatting:

- **Line Breaks**: Use Shift+Enter for new lines
- **Emojis**: Full Unicode emoji support
- **Special Characters**: Support for international characters

## Managing Channels

### Channel Types

#### Default Channels
- **#bluetooth**: Main channel for all nearby devices
- **#local**: Location-based channel (if enabled)
- **#system**: System notifications and updates

#### Custom Channels
- **Private Channels**: Invite-only channels for specific groups
- **Public Channels**: Open channels anyone can join
- **Temporary Channels**: Channels that exist for a limited time

### Joining Channels

1. **Channel Selection**: Click the channel dropdown or Join button
2. **Channel List**: Browse available channels
3. **Join Channel**: Select a channel and confirm
4. **Channel Switching**: Your messages now go to the new channel

### Creating Channels

1. **Open Channel Menu**: Click Join > Create New Channel
2. **Channel Settings**:
   - **Channel Name**: Unique channel identifier
   - **Channel Type**: Public or private
   - **Description**: Optional channel description
3. **Create Channel**: Confirm to create the channel
4. **Invite Users**: Share the channel name with others

## Settings and Configuration

### Accessing Settings

- **Menu Bar**: Click File > Settings
- **Keyboard Shortcut**: Press Ctrl+S
- **Settings Button**: Click the settings icon (if available)

### General Settings

#### Interface Settings
- **Window Size**: Adjust window dimensions
- **Font Size**: Change text size (8-20pt)
- **Theme**: Choose light or dark theme
- **Language**: Select interface language

#### Chat Settings
- **Timestamps**: Show/hide message timestamps
- **Auto-scroll**: Automatically scroll to new messages
- **Message History**: Set maximum messages to keep
- **Sound Notifications**: Enable/disable notification sounds

### Bluetooth Settings

#### Connection Settings
- **Adapter Selection**: Choose Bluetooth adapter (if multiple)
- **Scan Interval**: How often to scan for devices (10-60 seconds)
- **Max Peers**: Maximum concurrent connections (5-50)
- **Auto-reconnect**: Automatically reconnect to lost devices

#### Performance Settings
- **Power Save Mode**: Reduce Bluetooth power usage
- **Connection Timeout**: How long to wait for connections (5-30 seconds)
- **Discovery Timeout**: How long to scan for devices (10-60 seconds)

### Security Settings

#### Privacy Settings
- **Require Encryption**: Force encryption for all messages
- **Verify Peers**: Validate peer identities
- **Auto-trust Known**: Automatically trust previously connected devices

#### Identity Settings
- **Display Name**: Change how others see you
- **Backup Identity**: Export your identity for backup
- **Reset Identity**: Generate a new cryptographic identity

### Advanced Settings

#### Network Settings
- **Mesh TTL**: How many hops messages can travel (1-10)
- **Retry Attempts**: How many times to retry failed messages
- **Compression**: Enable message compression for faster delivery

#### Debug Settings
- **Log Level**: Change logging verbosity (ERROR, WARNING, INFO, DEBUG)
- **Log File**: Location for debug logs
- **Performance Monitor**: Show resource usage statistics

## Troubleshooting

### Common Issues

#### Application Won't Start

**Windows**:
1. Check if .NET Framework is installed
2. Run as Administrator
3. Check Windows Event Viewer for errors
4. Reinstall the application

**macOS**:
1. Check if the app is from an identified developer
2. Allow the app in Security & Privacy settings
3. Try launching from Terminal: `open /Applications/Blue\ Relay\ Chat.app`

**Linux**:
1. Check if executable has proper permissions: `chmod +x BlueRelayChat.AppImage`
2. Install missing dependencies: `sudo apt install libgtk-3-0 libgdk-pixbuf2.0-0`
3. Check system logs: `journalctl -f | grep blue-relay-chat`

#### Bluetooth Connection Issues

**No Devices Found**:
1. Enable Bluetooth on your device
2. Make device discoverable
3. Check physical distance to other devices
4. Restart Bluetooth service

**Connection Drops**:
1. Check battery level on both devices
2. Move closer to other devices
3. Reduce interference from other wireless devices
4. Update Bluetooth drivers

**Poor Performance**:
1. Close other Bluetooth applications
2. Reduce number of connected devices
3. Enable power save mode
4. Check for hardware issues

#### Message Issues

**Messages Not Sending**:
1. Check if you're connected to the mesh
2. Verify recipient is still connected
3. Check message length (max 4096 characters)
4. Restart the application

**Messages Not Receiving**:
1. Check if you're in the correct channel
2. Verify sender is connected to the mesh
3. Check message filters and settings
4. Clear message history if full

### Getting Help

#### Built-in Help
- **Help Menu**: Click Help > Documentation
- **Keyboard Shortcut**: Press Ctrl+H
- **Context Help**: Right-click on interface elements

#### Online Resources
- **Documentation**: [https://blue-relay-chat.readthedocs.io](https://blue-relay-chat.readthedocs.io)
- **GitHub Issues**: [https://github.com/blue-relay-chat/blue-relay-chat/issues](https://github.com/blue-relay-chat/blue-relay-chat/issues)
- **Community Forum**: [https://community.blue-relay-chat.org](https://community.blue-relay-chat.org)

#### Reporting Bugs

When reporting bugs, please include:
1. **Operating System**: Windows, macOS, or Linux version
2. **Blue Relay Chat Version**: Check Help > About
3. **Bluetooth Adapter**: Make and model if known
4. **Error Message**: Exact text of any error messages
5. **Steps to Reproduce**: What you were doing when the bug occurred

### Diagnostic Information

#### Generate Diagnostic Report
1. **Help Menu**: Click Help > Generate Diagnostic Report
2. **Save Report**: Choose location to save the report
3. **Share Report**: Include the report when asking for help

The diagnostic report includes:
- System information
- Bluetooth adapter details
- Application configuration
- Recent error logs
- Network statistics

## Advanced Features

### Command Line Interface

Blue Relay Chat supports command-line operation:

```bash
# Start with specific configuration
blue-relay-chat --config /path/to/config.ini

# Enable debug mode
blue-relay-chat --debug

# Start minimized
blue-relay-chat --minimized

# Connect to specific channel
blue-relay-chat --channel "#private-chat"

# Show help
blue-relay-chat --help
```

### Scripting and Automation

#### Python API

```python
import asyncio
from bitchat.transports.laptop_bluetooth import LaptopBluetoothTransport
from bitchat.config.manager import ConfigManager

async def send_automated_message():
    config = ConfigManager()
    transport = LaptopBluetoothTransport(config)
    
    await transport.start()
    
    message = {
        "content": "Automated message",
        "type": "text",
        "channel_id": "#bluetooth"
    }
    
    await transport.send_message(message)
    await transport.stop()

asyncio.run(send_automated_message())
```

#### Configuration Files

Advanced users can edit configuration directly:

```ini
# ~/.config/blue-relay-chat/config.ini

[laptop_gui]
window_width = 800
window_height = 600
font_size = 12
theme = dark

[laptop_bluetooth]
max_peers = 30
scan_interval_seconds = 15
auto_reconnect = true
```

### Network Analysis

#### Mesh Statistics
- **Hop Count**: How many devices a message traveled through
- **Delivery Time**: How long messages take to arrive
- **Network Size**: Total number of devices in the mesh
- **Message Routes**: Visual representation of message paths

#### Performance Monitoring
- **CPU Usage**: Application processor usage
- **Memory Usage**: RAM consumption
- **Bluetooth Traffic**: Data sent and received
- **Connection Quality**: Signal strength and error rates

### Security Features

#### End-to-End Encryption
- **Automatic Encryption**: All messages are encrypted by default
- **Key Exchange**: Secure cryptographic key exchange
- **Perfect Forward Secrecy**: Compromised keys don't reveal past messages

#### Identity Verification
- **Cryptographic IDs**: Each user has a unique cryptographic identifier
- **Trust Management**: Choose which peers to trust
- **Replay Protection**: Prevents message replay attacks

#### Emergency Wipe
- **Quick Shutdown**: Immediately clear all sensitive data
- **Secure Deletion**: Cryptographically wipe keys and messages
- **Recovery Options**: Backup and restore your identity

---

## Conclusion

Blue Relay Chat provides a secure, decentralized way to communicate with nearby devices without requiring internet connectivity. The laptop client offers a simple, cross-platform interface that makes it easy to join the BRC network and start chatting.

For more information, updates, and community support, visit:
- **Website**: [https://blue-relay-chat.org](https://blue-relay-chat.org)
- **Documentation**: [https://docs.blue-relay-chat.org](https://docs.blue-relay-chat.org)
- **GitHub**: [https://github.com/blue-relay-chat/blue-relay-chat](https://github.com/blue-relay-chat/blue-relay-chat)

Thank you for using Blue Relay Chat!