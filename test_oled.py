# Test OLED Display
import board
import displayio
import terminalio
from adafruit_display_text import label
from i2cdisplaybus import I2CDisplayBus
import adafruit_displayio_ssd1306

displayio.release_displays()

i2c = board.I2C()

# Scan I2C
print("Scanning I2C bus...")
while not i2c.try_lock():
    pass
try:
    devices = i2c.scan()
    print(f"I2C devices found: {[hex(device) for device in devices]}")
finally:
    i2c.unlock()

# Try to initialize display
try:
    display_bus = I2CDisplayBus(i2c, device_address=0x3C)
    display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=32)
    print("✓ Display initialized at 0x3C")
    
    # Make the display context
    splash = displayio.Group()
    display.root_group = splash
    
    # Draw a label
    text = "Hello OLED!"
    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF, x=10, y=15)
    splash.append(text_area)
    
    print("✓ Text displayed on OLED")
    
except Exception as e:
    print(f"✗ Display error: {e}")

print("Test complete")
