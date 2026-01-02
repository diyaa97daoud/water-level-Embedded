# SPDX-FileCopyrightText: 2025
# SPDX-License-Identifier: MIT
"""
Smart Water Level Management - Hardware Component
Adafruit Feather nRF52840 with BLE Provisioning
"""

import time
import board
import microcontroller
import json
import digitalio
import displayio
import terminalio
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService
from adafruit_display_text import label
import adafruit_displayio_ssd1306
import adafruit_hcsr04

print("=" * 50)
print("Smart Water Level Management")
print("Adafruit Feather nRF52840")
print("=" * 50)

# Initialize OLED Display
displayio.release_displays()
i2c = board.I2C()

display = None
try:
    from i2cdisplaybus import I2CDisplayBus
    for address in [0x3C, 0x3D]:
        try:
            display_bus = I2CDisplayBus(i2c, device_address=address)
            display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=32)
            print(f"✓ Display initialized at 0x{address:02X}")
            break
        except:
            continue
    if display is None:
        print("⚠ OLED not found - continuing without display")
except:
    print("⚠ Display error - continuing without display")

def show_message(line1="", line2="", line3=""):
    """Display up to 3 lines of text on OLED"""
    if display is None:
        return
    
    splash = displayio.Group()
    display.root_group = splash
    
    if line1:
        text1 = label.Label(terminalio.FONT, text=line1, color=0xFFFFFF, x=0, y=4)
        splash.append(text1)
    if line2:
        text2 = label.Label(terminalio.FONT, text=line2, color=0xFFFFFF, x=0, y=14)
        splash.append(text2)
    if line3:
        text3 = label.Label(terminalio.FONT, text=line3, color=0xFFFFFF, x=0, y=24)
        splash.append(text3)

# Show startup message
show_message("Water Level", "Management", "Starting...")
time.sleep(1)

# Initialize Ultrasonic Sensor (HC-SR04)
try:
    sonar = adafruit_hcsr04.HCSR04(trigger_pin=board.D10, echo_pin=board.D11)
    print("✓ Ultrasonic sensor initialized (D10=TRIG, D11=ECHO)")
    SENSOR_AVAILABLE = True
except Exception as e:
    print(f"⚠ Ultrasonic sensor error: {e}")
    print("  Continuing with simulated data...")
    SENSOR_AVAILABLE = False

# Initialize Relay for Pump Control
try:
    relay_pin = digitalio.DigitalInOut(board.D12)
    relay_pin.direction = digitalio.Direction.OUTPUT
    relay_pin.value = False  # Start with pump OFF
    print("✓ Relay initialized on D12 (Pump OFF)")
    RELAY_AVAILABLE = True
except Exception as e:
    print(f"⚠ Relay initialization error: {e}")
    RELAY_AVAILABLE = False

# Water level calculation constants
TANK_HEIGHT = 100.0  # Total tank height in cm
SENSOR_TO_TOP = 5.0  # Distance from sensor to tank top in cm

# Initialize BLE
ble = BLERadio()
uart = UARTService()
advertisement = ProvideServicesAdvertisement(uart)
ble.name = "WaterLevel-Device"

# Configuration files
CONFIG_FILE = "/config.json"
OLD_CONFIG_FILE = "/config.txt"

# Initialize buttons
import digitalio
button_a = digitalio.DigitalInOut(board.D9)
button_a.direction = digitalio.Direction.INPUT
button_a.pull = digitalio.Pull.UP

def migrate_old_config():
    """Migrate from old txt format to new json format"""
    try:
        with open(OLD_CONFIG_FILE, "r") as f:
            lines = f.readlines()
            if len(lines) >= 2:
                device_id = lines[0].strip()
                device_key = lines[1].strip()
                
                config = {
                    "device_id": device_id,
                    "device_key": device_key
                }
                
                with open(CONFIG_FILE, "w") as f_new:
                    json.dump(config, f_new)
                
                print("✓ Migrated config.txt to config.json")
                
                try:
                    import os
                    os.remove(OLD_CONFIG_FILE)
                    print("✓ Removed old config.txt")
                except:
                    print("⚠ Could not remove config.txt")
                
                return device_id, device_key
    except:
        pass
    return None, None

def load_config():
    """Load Device ID, Key, and Thresholds from flash storage"""
    device_id, device_key = migrate_old_config()
    if device_id and device_key:
        # After migration, create full config dict
        config_dict = {
            "device_id": device_id,
            "device_key": device_key,
            "min_threshold": 20.0,  # Default min distance (max water level)
            "max_threshold": 80.0   # Default max distance (min water level)
        }
        return config_dict
    
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            device_id = config.get("device_id")
            device_key = config.get("device_key")
            
            if device_id and device_key:
                print(f"✓ Config loaded: {device_id}")
                print(f"  Thresholds: min={config.get('min_threshold', 20.0)}cm, max={config.get('max_threshold', 80.0)}cm")
                return config
    except:
        pass
    
    print("⚠ No configuration found")
    return None

def save_config(device_id, device_key):
    """Save Device ID and Key to flash storage"""
    try:
        config = {
            "device_id": device_id,
            "device_key": device_key
        }
        
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)
        
        print(f"✓ Config saved: {device_id}")
        return True
    except Exception as e:
        print(f"✗ Save failed: {e}")
        return False

def read_distance():
    """Read distance from ultrasonic sensor or return simulated value"""
    if not SENSOR_AVAILABLE:
        # Simulate distance reading (10-400 cm range)
        import random
        return round(random.uniform(10.0, 400.0), 2)
    
    try:
        # Read distance from sensor (in cm)
        distance = sonar.distance
        print(f"  Distance: {distance:.2f} cm")
        return round(distance, 2)
        
    except Exception as e:
        print(f"⚠ Sensor read error: {e}")
        # Return default distance
        return 100.0

def ble_provisioning():
    """Handle BLE provisioning"""
    print("\n" + "=" * 50)
    print("BLE PROVISIONING MODE")
    print(f"Device: {ble.name}")
    print("Format: DEVICE_ID,DEVICE_KEY")
    print("=" * 50)
    
    show_message("BLE Provisioning", "Waiting for", "connection...")
    
    ble.start_advertising(advertisement)
    
    while True:
        if ble.connected:
            print("✓ Connected")
            show_message("BLE Connected!", "Waiting for", "credentials...")
            
            while ble.connected:
                if uart.in_waiting:
                    try:
                        data = uart.read(uart.in_waiting)
                        message = data.decode('utf-8').strip()
                        
                        print(f"Received: {message}")
                        show_message("Data received", "Processing...", "")
                        
                        if ',' in message:
                            parts = message.split(',', 1)
                            if len(parts) == 2:
                                device_id = parts[0].strip()
                                device_key = parts[1].strip()
                                
                                if device_id and device_key:
                                    if save_config(device_id, device_key):
                                        uart.write(b"SUCCESS")
                                        print("✓ Provisioning complete")
                                        show_message("SUCCESS!", "Config saved", "Restarting...")
                                        time.sleep(2)
                                        ble.stop_advertising()
                                        microcontroller.reset()
                                    else:
                                        uart.write(b"ERROR: Save failed")
                                        show_message("ERROR!", "Save failed", "Try again")
                                        time.sleep(2)
                                else:
                                    uart.write(b"ERROR: Invalid data")
                                    show_message("ERROR!", "Invalid data", "Try again")
                                    time.sleep(2)
                            else:
                                uart.write(b"ERROR: Invalid format")
                                show_message("ERROR!", "Bad format", "Try again")
                                time.sleep(2)
                        else:
                            uart.write(b"ERROR: Missing comma")
                            show_message("ERROR!", "Missing comma", "Try again")
                            time.sleep(2)
                            
                    except Exception as e:
                        uart.write(f"ERROR: {str(e)}".encode())
                        show_message("ERROR!", str(e)[:16], "Try again")
                        time.sleep(2)
                
                time.sleep(0.1)
            
            print("✗ Disconnected")
            show_message("Disconnected", "Waiting for", "connection...")
            ble.start_advertising(advertisement)
        
        time.sleep(0.1)

def main_operation(config):
    """Main operation mode - BLE gateway communication"""
    device_id = config.get("device_id")
    device_key = config.get("device_key")
    
    print("\n" + "=" * 50)
    print("NORMAL OPERATION - BLE GATEWAY MODE")
    print(f"Device: {device_id}")
    print(f"Key: {device_key}")
    print(f"Thresholds: min={config.get('min_threshold', 20.0)}cm, max={config.get('max_threshold', 80.0)}cm")
    print("Waiting for BLE gateway connection...")
    print("Press Button A to re-provision")
    print("=" * 50)
    
    show_message("Ready", "Waiting for", "Gateway...")
    
    # Start BLE advertising for gateway
    ble.start_advertising(advertisement)
    
    last_sensor_send = time.monotonic()
    sensor_interval = 5  # Send sensor data every 5 seconds
    distance = 100.0  # Default distance
    pump_on = False
    
    while True:
        # Check Button A for re-provisioning
        if not button_a.value:
            print("\n! Button A pressed")
            show_message("Button A", "Provisioning", "mode...")
            time.sleep(0.5)
            while not button_a.value:
                time.sleep(0.1)
            ble.stop_advertising()
            ble_provisioning()
        
        # Handle BLE connection from gateway
        if ble.connected:
            show_message("Connected!", "Sending data", f"D:{distance:.1f}cm P:{'ON' if pump_on else 'OFF'}")
            
            # Send sensor data periodically
            if time.monotonic() - last_sensor_send >= sensor_interval:
                # Read actual distance from sensor
                distance = read_distance()
                
                # AUTO-STOP: Check if pump should stop (water reached HIGH level = min distance)
                if pump_on and config and distance <= config.get('min_threshold', 5.0):
                    pump_on = False
                    if RELAY_AVAILABLE:
                        relay_pin.value = False
                    print(f"🛑 AUTO-STOP: Water reached HIGH level (distance={distance:.1f}cm <= {config.get('min_threshold', 5.0)}cm)")
                    show_message("Pump AUTO-STOP", "High water level", "reached!")
                    time.sleep(1)
                
                # Create sensor data message
                sensor_data = {
                    "device_key": device_key,
                    "water_level": distance,
                    "pump_status": "ON" if pump_on else "OFF",
                    "timestamp": time.monotonic()
                }
                
                message = json.dumps(sensor_data)
                uart.write(message.encode('utf-8'))
                sensor_status = "REAL" if SENSOR_AVAILABLE else "SIM"
                print(f"→ Sent [{sensor_status}]: Distance={distance:.1f}cm, Pump={'ON' if pump_on else 'OFF'}")
                
                last_sensor_send = time.monotonic()
            
            # Check for incoming commands from gateway
            if uart.in_waiting:
                try:
                    data = uart.read(uart.in_waiting)
                    command = data.decode('utf-8').strip()
                    print(f"← Received: {command}")
                    
                    # Handle GET_CONFIG request
                    if command == "GET_CONFIG":
                        config = {
                            "device_key": device_key,
                            "device_id": device_id
                        }
                        uart.write(json.dumps(config).encode('utf-8'))
                        print("→ Sent config")
                    
                    # Handle pump control commands (JSON format)
                    elif command.startswith('{'):
                        try:
                            cmd_data = json.loads(command)
                            
                            # Handle action-based commands (new format)
                            if 'action' in cmd_data:
                                action = cmd_data['action'].upper()
                                if action == 'START_PUMP':
                                    if not pump_on:
                                        pump_on = True
                                        if RELAY_AVAILABLE:
                                            relay_pin.value = True
                                        print("✓ Pump STARTED by command")
                                        show_message("Pump STARTED", "By command", "")
                                        time.sleep(1)
                                elif action == 'STOP_PUMP':
                                    if pump_on:
                                        pump_on = False
                                        if RELAY_AVAILABLE:
                                            relay_pin.value = False
                                        print("✓ Pump STOPPED by command")
                                        show_message("Pump STOPPED", "By command", "")
                                        time.sleep(1)
                            
                            # Handle command-based format (old format)
                            elif cmd_data.get("command") == "START":
                                pump_on = True
                                if RELAY_AVAILABLE:
                                    relay_pin.value = True
                                print("✓ PUMP STARTED")
                                show_message("PUMP START", f"D:{distance:.1f}cm", "Pump: ON")
                            
                            # Handle threshold update
                            elif "minThreshold" in cmd_data or "min_threshold" in cmd_data:
                                min_t = cmd_data.get("minThreshold") or cmd_data.get("min_threshold")
                                max_t = cmd_data.get("maxThreshold") or cmd_data.get("max_threshold")
                                
                                # Update config in memory
                                if min_t is not None:
                                    config['min_threshold'] = min_t
                                if max_t is not None:
                                    config['max_threshold'] = max_t
                                
                                # Save to file with flush to prevent corruption
                                try:
                                    # Read existing config first to preserve all fields
                                    existing_config = {}
                                    try:
                                        with open(CONFIG_FILE, "r") as f:
                                            existing_config = json.load(f)
                                    except:
                                        pass
                                    
                                    # Update thresholds
                                    if min_t is not None:
                                        existing_config['min_threshold'] = min_t
                                    if max_t is not None:
                                        existing_config['max_threshold'] = max_t
                                    
                                    # Write back to file
                                    with open(CONFIG_FILE, "w") as f:
                                        json.dump(existing_config, f)
                                        f.flush()  # Ensure data is written to disk
                                    
                                    print(f"✓ Thresholds updated and saved: min={min_t}cm, max={max_t}cm")
                                    show_message("Thresholds", f"Min:{min_t}cm", f"Max:{max_t}cm")
                                    time.sleep(2)
                                except Exception as e:
                                    print(f"⚠ Failed to save thresholds: {e}")
                                
                        except (ValueError, Exception) as e:
                            print(f"⚠ JSON parse error: {e}")
                            
                except Exception as e:
                    print(f"✗ Error: {e}")
            
            time.sleep(0.1)
        else:
            # Not connected, try advertising
            if not ble.advertising:
                ble.start_advertising(advertisement)
                show_message("Ready", "Waiting for", "Gateway....")
            
            time.sleep(1)

# ============================================
# Main Program
# ============================================

config = load_config()

if config:
    main_operation(config)
else:
    print("\nPress Button A to start provisioning")
    show_message("No Config!", "Press Button A", "to provision")
    
    while True:
        if not button_a.value:
            print("\n! Button A pressed")
            time.sleep(0.5)
            ble_provisioning()
        time.sleep(0.1)
