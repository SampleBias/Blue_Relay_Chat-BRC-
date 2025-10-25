"""
Display driver for 1.44-inch LCD screen.

This module provides a display driver for small LCD screens
commonly used with Raspberry Pi Zero projects.
"""

import time
import threading
from typing import Optional, Tuple, List
from enum import Enum

from ..utils.logging import get_logger


class DisplayColor(Enum):
    """Display colors for monochrome LCD."""
    BLACK = 0
    WHITE = 1


class DisplayDriver:
    """Display driver for 1.44-inch LCD screen."""
    
    # Screen dimensions for 1.44-inch LCD
    SCREEN_WIDTH = 128
    SCREEN_HEIGHT = 128
    PIXEL_COUNT = SCREEN_WIDTH * SCREEN_HEIGHT
    
    # Font settings
    FONT_WIDTH = 6
    FONT_HEIGHT = 8
    CHAR_PER_LINE = SCREEN_WIDTH // FONT_WIDTH
    MAX_LINES = SCREEN_HEIGHT // FONT_HEIGHT
    
    def __init__(self, device_path: str = "/dev/fb1") -> None:
        """
        Initialize display driver.
        
        Args:
            device_path: Path to framebuffer device
        """
        self.logger = get_logger("display_driver")
        self.device_path = device_path
        self.framebuffer: Optional[int] = None
        self.screen_buffer: List[List[int]] = []
        self._lock = threading.Lock()
        
        # Initialize screen buffer
        self._clear_buffer()
        
        self.logger.info(f"Display driver initialized for {self.SCREEN_WIDTH}x{self.SCREEN_HEIGHT} screen")
    
    def _clear_buffer(self) -> None:
        """Clear the internal screen buffer."""
        self.screen_buffer = [
            [DisplayColor.BLACK.value for _ in range(self.SCREEN_WIDTH)]
            for _ in range(self.SCREEN_HEIGHT)
        ]
    
    def connect(self) -> bool:
        """
        Connect to the display device.
        
        Returns:
            True if connection successful, False otherwise
        """
        # Check for mock environment variable
        import os
        if os.environ.get("BITCHAT_MOCK_DISPLAY") == "true":
            self.logger.info("Using mock display mode")
            self.framebuffer = None  # Mock framebuffer
            return True
        
        try:
            # Try to open framebuffer device
            self.framebuffer = open(self.device_path, "wb+")
            self.logger.info(f"Connected to display at {self.device_path}")
            return True
        except (OSError, IOError) as e:
            self.logger.error(f"Failed to connect to display: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the display device."""
        if self.framebuffer:
            try:
                self.framebuffer.close()
                self.framebuffer = None
                self.logger.info("Disconnected from display")
            except (OSError, IOError) as e:
                self.logger.error(f"Error disconnecting from display: {e}")
    
    def clear(self) -> None:
        """Clear the entire screen."""
        with self._lock:
            self._clear_buffer()
    
    def set_pixel(self, x: int, y: int, color: DisplayColor) -> None:
        """
        Set a single pixel.
        
        Args:
            x: X coordinate
            y: Y coordinate
            color: Color to set
        """
        if 0 <= x < self.SCREEN_WIDTH and 0 <= y < self.SCREEN_HEIGHT:
            with self._lock:
                self.screen_buffer[y][x] = color.value
    
    def get_pixel(self, x: int, y: int) -> DisplayColor:
        """
        Get the color of a single pixel.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Color at the specified position
        """
        if 0 <= x < self.SCREEN_WIDTH and 0 <= y < self.SCREEN_HEIGHT:
            with self._lock:
                return DisplayColor(self.screen_buffer[y][x])
        return DisplayColor.BLACK
    
    def draw_line(self, x1: int, y1: int, x2: int, y2: int, color: DisplayColor) -> None:
        """
        Draw a line between two points.
        
        Args:
            x1, y1: Start coordinates
            x2, y2: End coordinates
            color: Line color
        """
        # Bresenham's line algorithm
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        x, y = x1, y1
        
        while True:
            self.set_pixel(x, y, color)
            
            if x == x2 and y == y2:
                break
            
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
    
    def draw_rectangle(self, x: int, y: int, width: int, height: int, color: DisplayColor, fill: bool = False) -> None:
        """
        Draw a rectangle.
        
        Args:
            x, y: Top-left corner coordinates
            width, height: Rectangle dimensions
            color: Rectangle color
            fill: Whether to fill the rectangle
        """
        x2 = min(x + width - 1, self.SCREEN_WIDTH - 1)
        y2 = min(y + height - 1, self.SCREEN_HEIGHT - 1)
        
        if fill:
            for py in range(y, y2 + 1):
                for px in range(x, x2 + 1):
                    self.set_pixel(px, py, color)
        else:
            # Draw outline only
            for px in range(x, x2 + 1):
                self.set_pixel(px, y, color)
                self.set_pixel(px, y2, color)
            for py in range(y + 1, y2):
                self.set_pixel(x, py, color)
                self.set_pixel(x2, py, color)
    
    def draw_char(self, x: int, y: int, char: str, color: DisplayColor) -> None:
        """
        Draw a single character using a simple 6x8 font.
        
        Args:
            x, y: Character position
            char: Character to draw
            color: Character color
        """
        if len(char) != 1:
            return
        
        # Simple 6x8 font for basic ASCII characters
        font = {
            ' ': [0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
            '!': [0x00, 0x00, 0x5F, 0x5F, 0x00],
            '"': [0x00, 0x07, 0x05, 0x07, 0x00],
            '#': [0x14, 0x7F, 0x14, 0x7F, 0x14],
            '$': [0x24, 0x2A, 0x7F, 0x2A, 0x12],
            '%': [0x23, 0x13, 0x08, 0x64, 0x62],
            '&': [0x36, 0x49, 0x55, 0x22, 0x50],
            "'": [0x00, 0x05, 0x03, 0x00, 0x00],
            '(': [0x00, 0x1C, 0x22, 0x41, 0x00],
            ')': [0x00, 0x41, 0x22, 0x1C, 0x00],
            '*': [0x08, 0x2A, 0x1C, 0x2A, 0x08],
            '+': [0x08, 0x08, 0x3E, 0x08, 0x08],
            ',': [0x00, 0x50, 0x30, 0x00, 0x00],
            '-': [0x08, 0x08, 0x08, 0x08, 0x00],
            '.': [0x00, 0x60, 0x60, 0x00, 0x00],
            '/': [0x20, 0x10, 0x08, 0x04, 0x02],
            '0': [0x3E, 0x51, 0x49, 0x45, 0x3E],
            '1': [0x00, 0x42, 0x7F, 0x40, 0x00],
            '2': [0x42, 0x61, 0x51, 0x49, 0x46],
            '3': [0x21, 0x41, 0x45, 0x4B, 0x31],
            '4': [0x18, 0x14, 0x12, 0x7F, 0x10],
            '5': [0x27, 0x45, 0x45, 0x45, 0x39],
            '6': [0x3C, 0x4A, 0x49, 0x49, 0x30],
            '7': [0x01, 0x71, 0x09, 0x05, 0x03],
            '8': [0x36, 0x49, 0x49, 0x49, 0x36],
            '9': [0x06, 0x49, 0x49, 0x29, 0x1E],
            ':': [0x00, 0x36, 0x36, 0x00, 0x00],
            ';': [0x00, 0x56, 0x36, 0x00, 0x00],
            '<': [0x08, 0x14, 0x22, 0x41, 0x00],
            '=': [0x14, 0x14, 0x14, 0x14, 0x14],
            '>': [0x00, 0x41, 0x22, 0x14, 0x08],
            '?': [0x02, 0x01, 0x51, 0x09, 0x06],
            '@': [0x32, 0x49, 0x79, 0x41, 0x3E],
            'A': [0x7E, 0x11, 0x11, 0x11, 0x7E],
            'B': [0x7F, 0x49, 0x49, 0x49, 0x36],
            'C': [0x3E, 0x41, 0x41, 0x41, 0x22],
            'D': [0x7F, 0x41, 0x41, 0x22, 0x1C],
            'E': [0x7F, 0x49, 0x49, 0x49, 0x41],
            'F': [0x7F, 0x09, 0x09, 0x09, 0x01],
            'G': [0x3E, 0x41, 0x49, 0x49, 0x7A],
            'H': [0x7F, 0x08, 0x08, 0x08, 0x7F],
            'I': [0x00, 0x41, 0x7F, 0x41, 0x00],
            'J': [0x20, 0x40, 0x40, 0x3F, 0x01],
            'K': [0x7F, 0x08, 0x14, 0x22, 0x41],
            'L': [0x7F, 0x40, 0x40, 0x40, 0x40],
            'M': [0x7F, 0x02, 0x0C, 0x02, 0x7F],
            'N': [0x7F, 0x04, 0x08, 0x10, 0x7F],
            'O': [0x3E, 0x41, 0x41, 0x41, 0x3E],
            'P': [0x7F, 0x09, 0x09, 0x09, 0x06],
            'Q': [0x3E, 0x41, 0x51, 0x21, 0x5E],
            'R': [0x7F, 0x09, 0x19, 0x29, 0x46],
            'S': [0x46, 0x49, 0x49, 0x49, 0x31],
            'T': [0x01, 0x01, 0x7F, 0x01, 0x01],
            'U': [0x3F, 0x40, 0x40, 0x40, 0x3F],
            'V': [0x1F, 0x20, 0x40, 0x20, 0x1F],
            'W': [0x3F, 0x40, 0x38, 0x40, 0x3F],
            'X': [0x63, 0x14, 0x08, 0x14, 0x63],
            'Y': [0x07, 0x08, 0x70, 0x08, 0x07],
            'Z': [0x61, 0x51, 0x49, 0x45, 0x43],
            '[': [0x00, 0x00, 0x7F, 0x41, 0x41],
            '\\': [0x02, 0x04, 0x08, 0x10, 0x20],
            ']': [0x41, 0x41, 0x7F, 0x00, 0x00],
            '^': [0x04, 0x02, 0x01, 0x02, 0x04],
            '_': [0x40, 0x40, 0x40, 0x40, 0x40],
            '`': [0x00, 0x01, 0x02, 0x04, 0x00],
            'a': [0x20, 0x54, 0x54, 0x54, 0x78],
            'b': [0x7F, 0x48, 0x44, 0x44, 0x38],
            'c': [0x38, 0x44, 0x44, 0x44, 0x20],
            'd': [0x38, 0x44, 0x44, 0x48, 0x7F],
            'e': [0x38, 0x54, 0x54, 0x54, 0x18],
            'f': [0x08, 0x7E, 0x09, 0x01, 0x02],
            'g': [0x18, 0xA4, 0xA4, 0xA4, 0x7C],
            'h': [0x7F, 0x08, 0x04, 0x04, 0x78],
            'i': [0x00, 0x44, 0x7D, 0x40, 0x00],
            'j': [0x20, 0x40, 0x44, 0x3D, 0x00],
            'k': [0x7F, 0x08, 0x10, 0x20, 0x40],
            'l': [0x00, 0x41, 0x7F, 0x40, 0x00],
            'm': [0x7C, 0x04, 0x18, 0x04, 0x78],
            'n': [0x7C, 0x08, 0x04, 0x04, 0x78],
            'o': [0x38, 0x44, 0x44, 0x44, 0x38],
            'p': [0x7C, 0x14, 0x14, 0x14, 0x08],
            'q': [0x08, 0x14, 0x14, 0x18, 0x7C],
            'r': [0x7C, 0x08, 0x04, 0x04, 0x08],
            's': [0x48, 0x54, 0x54, 0x54, 0x20],
            't': [0x04, 0x3E, 0x44, 0x20, 0x00],
            'u': [0x3C, 0x40, 0x40, 0x20, 0x7C],
            'v': [0x1C, 0x20, 0x40, 0x20, 0x1C],
            'w': [0x6C, 0x50, 0x50, 0x50, 0x6C],
            'x': [0x44, 0x28, 0x10, 0x28, 0x44],
            'y': [0x0C, 0x50, 0x50, 0x20, 0x1C],
            'z': [0x44, 0x64, 0x54, 0x4C, 0x44],
        }
        
        # Default to empty box for unknown characters
        char_data = font.get(char, [0x7E, 0x81, 0x81, 0x81, 0x7E])
        
        # Draw character pixels
        for row in range(self.FONT_HEIGHT):
            row_data = char_data[row] if row < len(char_data) else 0
            for col in range(self.FONT_WIDTH):
                if row_data & (0x80 >> col):
                    pixel_x = x + col
                    pixel_y = y + row
                    if pixel_x < self.SCREEN_WIDTH and pixel_y < self.SCREEN_HEIGHT:
                        self.set_pixel(pixel_x, pixel_y, color)
    
    def draw_text(self, x: int, y: int, text: str, color: DisplayColor) -> None:
        """
        Draw text string.
        
        Args:
            x, y: Starting position
            text: Text to draw
            color: Text color
        """
        for i, char in enumerate(text):
            char_x = x + (i * self.FONT_WIDTH)
            if char_x < self.SCREEN_WIDTH - self.FONT_WIDTH:
                self.draw_char(char_x, y, char, color)
    
    def draw_text_wrapped(self, x: int, y: int, text: str, color: DisplayColor, max_width: int = None) -> int:
        """
        Draw text with word wrapping.
        
        Args:
            x, y: Starting position
            text: Text to draw
            color: Text color
            max_width: Maximum width for text (None for screen width)
            
        Returns:
            Number of lines used
        """
        if max_width is None:
            max_width = self.SCREEN_WIDTH
        
        lines_used = 0
        current_y = y
        words = text.split(' ')
        
        for word in words:
            word_width = len(word) * self.FONT_WIDTH
            
            # Check if word fits on current line
            if x + word_width <= max_width:
                self.draw_text(x, current_y, word + ' ', color)
                x += word_width + self.FONT_WIDTH
            else:
                # Move to next line
                current_y += self.FONT_HEIGHT + 1
                lines_used += 1
                if current_y >= self.SCREEN_HEIGHT - self.FONT_HEIGHT:
                    break
                x = 0
                self.draw_text(x, current_y, word + ' ', color)
                x += word_width + self.FONT_WIDTH
        
        return lines_used + 1
    
    def refresh(self) -> None:
        """Refresh the display with current buffer content."""
        if not self.framebuffer:
            return
        
        with self._lock:
            try:
                # Convert buffer to bytes and write to framebuffer
                for y in range(self.SCREEN_HEIGHT):
                    row_data = bytearray()
                    for x in range(0, self.SCREEN_WIDTH, 8):  # Process 8 pixels at a time
                        byte_val = 0
                        for bit in range(8):
                            if x + bit < self.SCREEN_WIDTH:
                                if self.screen_buffer[y][x + bit]:
                                    byte_val |= (1 << (7 - bit))
                        row_data.append(byte_val)
                    
                    # Write row to framebuffer
                    self.framebuffer.write(row_data)
                
                self.framebuffer.flush()
                
            except (OSError, IOError) as e:
                self.logger.error(f"Failed to refresh display: {e}")
    
    def get_dimensions(self) -> Tuple[int, int]:
        """
        Get screen dimensions.
        
        Returns:
            Tuple of (width, height)
        """
        return (self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
    
    def get_text_dimensions(self, text: str) -> Tuple[int, int]:
        """
        Get the dimensions of text if rendered.
        
        Returns:
            Tuple of (width, height)
        """
        lines = text.split('\n')
        max_width = 0
        for line in lines:
            max_width = max(max_width, len(line) * self.FONT_WIDTH)
        
        return (max_width, len(lines) * self.FONT_HEIGHT)