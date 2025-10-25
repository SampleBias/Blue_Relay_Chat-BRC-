# Blue Relay Chat - Small Screen GUI

This document describes the small screen GUI implementation for Blue Relay Chat, optimized for 1.44-inch LCD displays with toggle/button input.

## Overview

The small screen GUI provides a complete chat interface for compact displays, perfect for Raspberry Pi Zero 2 W deployments with limited screen real estate. It uses a custom display driver and button-based input system to create an efficient messaging interface.

## Features

### Display Capabilities
- **128x128 pixel resolution** for 1.44-inch LCD displays
- **Monochrome rendering** with optimized font
- **Text wrapping** for long messages
- **Multiple UI modes**: Chat, Menu, Status
- **Real-time updates** with configurable refresh rates

### Input System
- **Toggle-based navigation** with 6-button layout
- **Text input mode** with character grid selection
- **Mode switching** between navigation and text input
- **Configurable GPIO pins** for custom hardware
- **Debounced input** to prevent false triggers

### User Interface
- **Chat Mode**: Send/receive messages with compact display
- **Menu System**: Navigate settings and options
- **Status Pages**: View system information and network status
- **Input Indicators**: Visual feedback for current mode

## Hardware Requirements

### Display
- **1.44-inch LCD** with 128x128 resolution
- **Framebuffer interface** (/dev/fb1 or compatible)
- **Monochrome or color** display support
- **SPI or I2C** communication (depending on display)

### Input
- **6 GPIO pins** minimum for basic operation:
  - Toggle/Enter button (GPIO 17)
  - Up navigation (GPIO 22)
  - Down navigation (GPIO 23)
  - Left navigation (GPIO 24)
  - Right navigation (GPIO 25)
  - Select/Confirm (GPIO 27)
- **Additional pins** for extended functionality:
  - Back/Cancel (GPIO 5)
  - Mode switch (GPIO 6)

### Recommended Hardware
- **Raspberry Pi Zero 2 W** with GPIO header
- **1.44-inch LCD display** (ST7735, ST7789, or compatible)
- **Push buttons** or tactile switches
- **Breadboard** for custom button layouts
- **Power supply**: Stable 2.5A+ for reliable operation

## Installation

### Hardware Setup

1. **Connect Display**:
   ```bash
   # Enable SPI interface if needed
   sudo raspi-config nonint do_spi
   ```

2. **Connect Buttons**:
   ```
   GPIO 17 -> Toggle/Enter
   GPIO 22 -> Up
   GPIO 23 -> Down
   GPIO 24 -> Left
   GPIO 25 -> Right
   GPIO 27 -> Select
   GPIO 5  -> Back
   GPIO 6  -> Mode Switch
   ```

3. **Install Dependencies**:
   ```bash
   sudo apt-get update
   sudo apt-get install -y python3-rpi.gpio
   ```

### Software Setup

1. **Clone Repository**:
   ```bash
   git clone https://github.com/blue-relay-chat/blue-relay-chat-rpi4.git
   cd blue-relay-chat-rpi4
   ```

2. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install RPi.GPIO
   ```

3. **Configure for Small Screen**:
   ```bash
   # Copy small screen configuration
   cp config_small_screen.ini ~/.config/blue-relay-chat/config.ini
   
   # Edit display settings if needed
   nano ~/.config/blue-relay-chat/config.ini
   ```

4. **Run Small Screen GUI**:
   ```bash
   python3 -m bitchat.gui.small_screen_gui
   ```

## Configuration

### Display Settings
```ini
[gui]
screen_width = 128
screen_height = 128
font_width = 6
font_height = 8
max_display_messages = 10
auto_refresh_interval_ms = 500
show_cursor = true
```

### Input Settings
```ini
[input]
input_type = gpio
gpio_config = default
enable_button_input = true
button_debounce_ms = 50
text_input_timeout_seconds = 60
```

### Performance Settings
```ini
[performance]
max_cpu_usage_percent = 70
max_memory_mb = 100
message_queue_size = 100
gui_update_interval_ms = 100
```

## Usage

### Basic Navigation

1. **Chat Mode** (default):
   - **Toggle/Enter**: Switch to text input mode
   - **Up/Down**: Navigate message history
   - **Left/Right**: Navigate menu (in menu mode)
   - **Select**: Send message (in text input mode)
   - **Back**: Return to menu

2. **Menu Mode**:
   - **Up/Down**: Navigate menu options
   - **Select**: Choose menu option
   - **Back**: Return to chat

3. **Text Input Mode**:
   - **Up/Down/Left/Right**: Navigate character grid
   - **Select**: Choose character
   - **Back**: Delete last character
   - **Toggle**: Switch back to navigation mode

### Message Composition

1. **Press Toggle/Enter** to enter text input mode
2. **Navigate** to character grid using arrow keys
3. **Select** characters to compose message
4. **Press Select** again to send message
5. **Press Back** to delete characters or exit text mode

### Status Monitoring

The GUI provides real-time status information:
- **Connected peers**: Number of active connections
- **Transport status**: Mesh and Nostr connectivity
- **Current channel**: Active chat channel
- **System information**: Hardware and performance metrics

## Customization

### Button Layout

Customize GPIO pin configuration:

```python
# In your config file
[input]
gpio_config = {
    "toggle_pin": 17,
    "up_pin": 22,
    "down_pin": 23,
    "left_pin": 24,
    "right_pin": 25,
    "select_pin": 27,
    "back_pin": 5,
    "mode_pin": 6
}
```

### Display Settings

Adjust display parameters for your specific hardware:

```ini
[display]
device_path = /dev/fb1
color_mode = monochrome
rotation = 0
backlight_level = 80
```

### UI Behavior

Configure interface behavior:

```ini
[gui]
minimal_ui = true
hide_timestamps = false
abbreviate_usernames = true
compact_messages = true
scroll_speed_ms = 100
```

## Troubleshooting

### Display Issues

1. **Blank Screen**:
   - Check framebuffer device path
   - Verify SPI is enabled: `raspi-config get spi`
   - Check display power and connections

2. **Garbled Display**:
   - Verify display resolution settings
   - Check framebuffer format compatibility
   - Test with different rotation values

3. **Slow Refresh**:
   - Increase `gui_update_interval_ms`
   - Reduce `max_display_messages`
   - Check CPU usage with `top`

### Input Issues

1. **Unresponsive Buttons**:
   - Verify GPIO pin connections
   - Check for short circuits
   - Increase `button_debounce_ms` value
   - Test with `python3 -c "import RPi.GPIO; print(RPi.GPIO.VERSION)"`

2. **Multiple Triggers**:
   - Increase debounce timing
   - Check button quality
   - Add pull-up resistors if not present

3. **Mode Switching Problems**:
   - Verify mode pin connection
   - Check GPIO configuration
   - Review input handler logs

### Performance Issues

1. **High CPU Usage**:
   - Reduce refresh rate
   - Lower message queue size
   - Enable power save mode
   - Check for memory leaks

2. **Memory Issues**:
   - Reduce `max_memory_mb`
   - Lower message history limits
   - Enable compression
   - Monitor with `free -h`

## Development

### Adding New Features

1. **Display Driver**:
   ```python
   from bitchat.gui.display_driver import DisplayDriver
   
   display = DisplayDriver("/dev/fb1")
   display.connect()
   display.draw_text(10, 10, "Hello", DisplayColor.WHITE)
   display.refresh()
   ```

2. **Input Handler**:
   ```python
   from bitchat.gui.input_handler import InputHandler
   
   input_handler = InputHandler()
   input_handler.register_callback(InputEvent.BUTTON_PRESS, my_callback)
   input_handler.start()
   ```

3. **GUI Integration**:
   ```python
   from bitchat.gui.small_screen_gui import SmallScreenGUI
   from bitchat.config.manager import ConfigManager
   from bitchat.core.events import EventBus
   
   config = ConfigManager()
   event_bus = EventBus()
   gui = SmallScreenGUI(config, event_bus)
   await gui.initialize()
   await gui.start()
   ```

### Testing Without Hardware

Use mock mode for development:

```python
# Set environment variable
export BITCHAT_MOCK_INPUT=true

# Run with mock input
python3 -m bitchat.gui.small_screen_gui
```

## Hardware Compatibility

### Tested Displays

- **ST7735**: 1.44-inch TFT LCD (128x128)
- **ST7789**: Small TFT displays (128x128)
- **SSD1306**: OLED displays (128x64, scaled)
- **Custom framebuffer**: Linux framebuffer devices

### Tested Platforms

- **Raspberry Pi Zero 2 W**: Full support
- **Raspberry Pi 3/4**: Compatible with GPIO adapter
- **Orange Pi Zero 2W**: GPIO compatible
- **Custom ARM boards**: With Linux and GPIO access

## Performance Optimization

### Memory Usage

- **Screen Buffer**: ~16KB for 128x128 monochrome
- **Message History**: 50 messages maximum
- **Font Data**: ~2KB for character set
- **Total GUI**: ~50KB typical usage

### CPU Usage

- **Display Refresh**: 100-500ms intervals
- **Input Polling**: 10ms debounce cycle
- **Message Processing**: Asynchronous event handling
- **Background Tasks**: Minimal impact design

## Future Enhancements

### Planned Features

1. **Touch Screen Support**: Capacitive touch input
2. **Color Displays**: RGB and TFT color support
3. **Larger Screens**: 1.8-inch and 2.4-inch support
4. **Wireless Input**: Bluetooth remote control
5. **Voice Input**: Text-to-speech integration
6. **Emoji Support**: Unicode character set expansion

### Performance Improvements

1. **Hardware Acceleration**: DMA-based display updates
2. **Double Buffering**: Flicker-free refresh
3. **Partial Updates**: Only changed regions
4. **Compression**: Display data compression
5. **Caching**: Font and UI element caching

## Conclusion

The small screen GUI provides a complete, optimized chat interface for compact displays while maintaining full Blue Relay Chat functionality. Its modular design allows for easy customization and extension to support various hardware configurations.

For deployment on Raspberry Pi Zero 2 W with 1.44-inch displays, this implementation offers an excellent balance of functionality, performance, and resource efficiency.