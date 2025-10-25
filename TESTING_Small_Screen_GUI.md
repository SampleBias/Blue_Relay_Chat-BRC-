# Testing Small Screen GUI

This guide provides step-by-step instructions for testing the small screen GUI implementation for Blue Relay Chat on a 1.44-inch display.

## Prerequisites

### Hardware Setup
1. **Raspberry Pi Zero 2 W** with GPIO header
2. **1.44-inch LCD display** (128x128 resolution) with one of:
   - ST7735 TFT display
   - ST7789 TFT display
   - SSD1306 OLED display (will be scaled)
   - Custom framebuffer display
3. **6 push buttons** or tactile switches
4. **Breadboard** for easy prototyping
5. **Jumper wires** for GPIO connections
6. **Power supply** (2.5A+ recommended)

### Software Setup
1. **Updated Blue Relay Chat repository** with GUI components
2. **Python 3.7+** installed
3. **RPi.GPIO library** for button input
4. **Framebuffer access** permissions for display

## Testing Methods

### Method 1: Mock Testing (No Hardware)

This method allows testing the GUI without physical hardware.

#### Steps:
1. **Set up mock environment**:
   ```bash
   export BITCHAT_MOCK_INPUT=true
   export BITCHAT_MOCK_DISPLAY=true
   ```

2. **Run with mock configuration**:
   ```bash
   python3 -m bitchat.gui.small_screen_gui
   ```

3. **Expected behavior**:
   - GUI starts with welcome screen
   - Mock button presses simulate user input
   - Display updates show simulated content
   - Input mode switching works (navigation ↔ text input)

#### Verification:
- Welcome screen appears correctly
- Menu navigation works with up/down arrows
- Text input mode allows character selection
- Status pages show simulated information
- Exit functionality works properly

### Method 2: Hardware Testing

This method tests with actual display and buttons.

#### Steps:
1. **Hardware connections**:
   ```
   Display:
   - VCC → 3.3V
   - GND → GND
   - SCL/SDA → GPIO 2/3 (I2C) or SPI pins
   - CS/DC → GPIO 8 (SPI) or DC pin
   - RST → GPIO 9 (SPI) or Reset pin
   
   Buttons:
   - Toggle/Enter → GPIO 17
   - Up → GPIO 22
   - Down → GPIO 23
   - Left → GPIO 24
   - Right → GPIO 25
   - Select → GPIO 27
   - Back → GPIO 5
   - Mode Switch → GPIO 6
   ```

2. **Enable SPI interface** (if using SPI display):
   ```bash
   sudo raspi-config nonint do_spi
   ```

3. **Configure display**:
   ```bash
   # Edit config if needed
   nano ~/.config/blue-relay-chat/config.ini
   
   # Add display settings
   [display]
   device_path = /dev/fb1
   color_mode = monochrome
   ```

4. **Run with hardware**:
   ```bash
   python3 -m bitchat.gui.small_screen_gui
   ```

#### Expected behavior:
- Display initializes and shows welcome screen
- Button presses navigate menus and control interface
- Text input mode allows message composition
- Real-time status updates
- Message sending and receiving works

#### Troubleshooting:
- **Blank screen**: Check display connections and power
- **Unresponsive buttons**: Verify GPIO wiring and pull-up resistors
- **Garbled display**: Check SPI configuration and cable quality
- **GPIO errors**: Run `sudo usermod -a -G gpio -p $USER`

### Method 3: Integration Testing

This method tests the GUI with the full Blue Relay Chat system.

#### Steps:
1. **Install with small screen config**:
   ```bash
   # Use small screen configuration
   cp config_small_screen.ini ~/.config/blue-relay-chat/config.ini
   
   # Install with Pi Zero 2 W script
   ./scripts/install_rpi_zero2w.sh
   ```

2. **Start the service**:
   ```bash
   sudo systemctl start blue-relay-chat
   ```

3. **Monitor system behavior**:
   ```bash
   # Check logs
   sudo journalctl -u blue-relay-chat -f
   
   # Check resource usage
   top -p $(pgrep -f blue-relay-chat)
   
   # Check display
   sudo cat /dev/fb1 | hexdump -C | head -20
   ```

#### Expected behavior:
- Service starts automatically on boot
- GUI displays on connected 1.44-inch screen
- Button input controls interface
- Messages route through mesh network
- Status indicators show connection state

## Performance Testing

### Memory Usage
Monitor memory consumption:
```bash
# Check memory usage
free -h

# Monitor process memory
ps aux | grep blue-relay-chat
```

Expected: ~50MB total usage for GUI with display and input

### CPU Usage
Monitor CPU consumption:
```bash
# Check CPU usage
top -p $(pgrep -f blue-relay-chat)

# Check CPU temperature
vcgencmd measure_temp
```

Expected: <30% CPU usage, <60°C temperature

### Display Performance
Test display refresh rates:
```bash
# Test different refresh intervals
# Edit config: gui_update_interval_ms = 100, 200, 500
```

Expected: Smooth scrolling at 100-200ms, readable at 500ms

## Input Testing

### Button Response
Test button responsiveness:
```bash
# Test with different debounce settings
# Edit config: button_debounce_ms = 25, 50, 100
```

Expected: Reliable response at 50ms debounce

### Mode Switching
Test input mode transitions:
1. Start in navigation mode
2. Press Mode Switch button to enter text input mode
3. Type message using character grid
4. Press Mode Switch button to return to navigation mode
5. Press Select to send message

## Automated Testing

### Unit Tests
Run unit tests for GUI components:
```bash
# Test display driver
python3 -m pytest tests/unit/test_display_driver.py

# Test input handler
python3 -m pytest tests/unit/test_input_handler.py

# Test GUI logic
python3 -m pytest tests/unit/test_small_screen_gui.py
```

### Integration Tests
Test full system integration:
```bash
# Run integration tests
python3 -m pytest tests/integration/test_gui_integration.py
```

## Validation Checklist

### Display Validation
- [ ] Welcome screen displays correctly
- [ ] Menu items are readable
- [ ] Text wraps properly at screen edges
- [ ] Cursor blinks in text input mode
- [ ] Status indicators update correctly
- [ ] Screen refresh is smooth (no flicker)

### Input Validation
- [ ] All buttons respond to presses
- [ ] Button debouncing prevents false triggers
- [ ] Mode switching works reliably
- [ ] Character grid navigation works correctly
- [ ] Text input accepts all characters

### Performance Validation
- [ ] Memory usage stays within limits
- [ ] CPU usage remains reasonable
- [ ] Display refresh is responsive
- [ ] No memory leaks during extended operation

### Integration Validation
- [ ] GUI starts with system service
- [ ] Messages route correctly through transports
- [ ] Status updates reflect actual system state
- [ ] Configuration changes apply correctly

## Debugging

### Enable Debug Logging
Add to configuration:
```ini
[application]
debug = true
log_level = DEBUG
```

### Common Issues and Solutions

1. **Permission denied on /dev/fb1**:
   - Add user to video group: `sudo usermod -a -G video $USER`
   - Check framebuffer permissions: `ls -l /dev/fb*`

2. **GPIO access denied**:
   - Add user to gpio group: `sudo usermod -a -G gpio $USER`
   - Check GPIO permissions: `ls -l /dev/gpiomem`

3. **Display shows garbage**:
   - Check framebuffer format compatibility
   - Verify display resolution matches configuration
   - Test with different color_mode settings

4. **Buttons not responding**:
   - Verify GPIO pin connections with multimeter
   - Check for short circuits
   - Test with simple GPIO read script

5. **High CPU usage**:
   - Reduce refresh rate in configuration
   - Enable power save mode
   - Close unnecessary applications

## Expected Results

When properly configured and tested, the small screen GUI should:
- Start automatically on system boot
- Display clear, readable text on 1.44-inch screen
- Respond immediately to button input
- Maintain smooth performance on Raspberry Pi Zero 2 W
- Provide full chat functionality with minimal resource usage
- Integrate seamlessly with Blue Relay Chat networking features

## Support

For issues during testing:
1. **Check logs**: `sudo journalctl -u blue-relay-chat -n 50`
2. **Verify configuration**: `python3 -c "from bitchat.config.manager import ConfigManager; print(ConfigManager())"`
3. **Test hardware**: `python3 -c "from bitchat.utils.hardware_detection import get_hardware_info; print(get_hardware_info())"`
4. **Report issues**: Create detailed bug reports with hardware specs and configuration

The small screen GUI has been designed to be robust and testable, allowing for thorough validation before deployment.