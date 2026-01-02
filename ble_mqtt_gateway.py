#!/usr/bin/env python3
"""
BLE to MQTT Gateway
Bridges CircuitPython device (BLE) to MQTT broker
"""

import asyncio
import json
import sys
from bleak import BleakClient, BleakScanner
import paho.mqtt.client as mqtt
from datetime import datetime

# Configuration
DEVICE_NAME = "WaterLevel-Device"
UART_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
UART_TX_CHAR_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"  # Nordic UART TX (device -> gateway)
UART_RX_CHAR_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"  # Nordic UART RX (gateway -> device)

# MQTT Configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_SENSOR = "devices/{device_key}/sensor/data"  # Will be formatted with device_key
MQTT_TOPIC_PUMP_CMD = "devices/{device_key}/pump/start"  # Pump control commands (backend uses /start)
MQTT_TOPIC_CONFIG = "devices/{device_key}/thresholds/update"  # Configuration updates (backend format)

class BLEMQTTGateway:
    def __init__(self):
        self.ble_client = None
        self.mqtt_client = None
        self.device_key = None
        self.running = True
        self.ble_buffer = ""  # Buffer for incomplete BLE messages
        self.command_queue = []  # Queue for MQTT commands to forward to BLE
        
    async def find_device(self):
        """Scan for the water level device"""
        print(f"🔍 Scanning for '{DEVICE_NAME}'...")
        
        devices = await BleakScanner.discover(timeout=10.0)
        
        for device in devices:
            if device.name and DEVICE_NAME in device.name:
                print(f"✓ Found device: {device.name} ({device.address})")
                return device
        
        print(f"✗ Device '{DEVICE_NAME}' not found")
        return None
    
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            print("✓ Connected to MQTT broker")
            # Subscribe to pump command and config topics if device_key is available
            if self.device_key:
                cmd_topic = MQTT_TOPIC_PUMP_CMD.format(device_key=self.device_key)
                config_topic = MQTT_TOPIC_CONFIG.format(device_key=self.device_key)
                client.subscribe(cmd_topic)
                client.subscribe(config_topic)
                print(f"✓ Subscribed to {cmd_topic}")
                print(f"✓ Subscribed to {config_topic}")
        else:
            print(f"✗ MQTT connection failed with code {rc}")
    
    def on_mqtt_message(self, client, userdata, msg):
        """Handle incoming MQTT messages (pump commands from backend)"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            print(f"📨 MQTT [{topic}]: {payload}")
            
            # Queue command/config to be sent to BLE device
            if 'pump/start' in topic or 'thresholds/update' in topic:
                self.command_queue.append(payload)
                print(f"→ Queued for BLE device (queue size: {len(self.command_queue)})")
            else:
                print(f"⚠ Unknown topic: {topic}")
                
        except Exception as e:
            print(f"✗ Error handling MQTT message: {e}")
    
    async def send_to_ble(self, message):
        """Send message to BLE device"""
        try:
            await self.ble_client.write_gatt_char(
                UART_RX_CHAR_UUID,
                message.encode('utf-8')
            )
            print(f"→ BLE: {message}")
        except Exception as e:
            print(f"✗ Error sending to BLE: {e}")
    
    def handle_ble_data(self, sender, data):
        """Handle data received from BLE device"""
        try:
            # Decode and add to buffer
            chunk = data.decode('utf-8')
            self.ble_buffer += chunk
            
            # Process complete messages (ending with })
            while '}' in self.ble_buffer:
                # Find the end of JSON message
                end_idx = self.ble_buffer.index('}') + 1
                message = self.ble_buffer[:end_idx].strip()
                self.ble_buffer = self.ble_buffer[end_idx:]
                
                # Find the start of JSON message
                start_idx = message.rfind('{')
                if start_idx != -1:
                    message = message[start_idx:]
                    
                    print(f"← BLE: {message}")
                    
                    # Parse JSON sensor data
                    try:
                        sensor_data = json.loads(message)
                        
                        # Store device key for future use
                        if 'device_key' in sensor_data:
                            self.device_key = sensor_data['device_key']
                        
                        # Add timestamp if not present
                        if 'timestamp' not in sensor_data:
                            sensor_data['timestamp'] = datetime.now().isoformat()
                        
                        # Publish to MQTT with device-specific topic (as bytes for backend)
                        if self.device_key:
                            topic = MQTT_TOPIC_SENSOR.format(device_key=self.device_key)
                            mqtt_payload = json.dumps(sensor_data)
                            self.mqtt_client.publish(topic, mqtt_payload.encode('utf-8'))
                            print(f"📤 MQTT [{topic}]: {mqtt_payload}")
                        else:
                            print("⚠ No device_key available, cannot publish")
                        
                    except json.JSONDecodeError as e:
                        print(f"⚠ JSON parse error: {e}")
                        
        except Exception as e:
            print(f"✗ Error handling BLE data: {e}")
    
    async def request_config(self):
        """Request device configuration"""
        try:
            await self.send_to_ble("GET_CONFIG")
            await asyncio.sleep(0.5)  # Wait for response
            
            # Subscribe to pump commands and config updates once we have device_key
            if self.device_key and self.mqtt_client:
                cmd_topic = MQTT_TOPIC_PUMP_CMD.format(device_key=self.device_key)
                config_topic = MQTT_TOPIC_CONFIG.format(device_key=self.device_key)
                self.mqtt_client.subscribe(cmd_topic)
                self.mqtt_client.subscribe(config_topic)
                print(f"✓ Subscribed to {cmd_topic}")
                print(f"✓ Subscribed to {config_topic}")
        except Exception as e:
            print(f"⚠ Could not request config: {e}")
        except Exception as e:
            print(f"⚠ Could not request config: {e}")
    
    async def run(self):
        """Main gateway loop"""
        print("=" * 60)
        print("BLE to MQTT Gateway")
        print("=" * 60)
        
        # Setup MQTT
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_message = self.on_mqtt_message
        
        try:
            self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.mqtt_client.loop_start()
        except Exception as e:
            print(f"✗ Failed to connect to MQTT broker: {e}")
            return
        
        # Main BLE connection loop
        while self.running:
            try:
                # Find device
                device = await self.find_device()
                if not device:
                    print("⏳ Retrying in 5 seconds...")
                    await asyncio.sleep(5)
                    continue
                
                # Connect to device
                print(f"🔗 Connecting to {device.address}...")
                
                async with BleakClient(device.address) as client:
                    self.ble_client = client
                    
                    if client.is_connected:
                        print("✓ BLE Connected!")
                        
                        # Wait a moment for services to be discovered
                        await asyncio.sleep(1)
                        
                        # List all services and characteristics for debugging
                        try:
                            for service in client.services:
                                if "6e400001" in service.uuid.lower():
                                    print(f"✓ Found UART Service: {service.uuid}")
                                    for char in service.characteristics:
                                        print(f"  - Characteristic: {char.uuid} (properties: {char.properties})")
                        except Exception as e:
                            print(f"⚠ Service discovery error: {e}")
                        
                        # Subscribe to notifications
                        try:
                            await client.start_notify(
                                UART_TX_CHAR_UUID,
                                self.handle_ble_data
                            )
                            print("✓ Listening for sensor data...")
                        except Exception as e:
                            print(f"✗ Failed to start notifications: {e}")
                            raise
                        
                        # Request device configuration
                        await self.request_config()
                        
                        # Keep connection alive and process commands
                        while client.is_connected and self.running:
                            # Check for queued commands to send to BLE
                            if self.command_queue:
                                command = self.command_queue.pop(0)
                                await self.send_to_ble(command)
                                print(f"✓ Sent command to BLE device")
                            
                            await asyncio.sleep(0.5)
                        
                        print("✗ BLE Disconnected")
                    
            except Exception as e:
                print(f"✗ BLE Error: {e}")
                await asyncio.sleep(5)
        
        # Cleanup
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
        
        print("\n👋 Gateway stopped")

async def main():
    gateway = BLEMQTTGateway()
    
    try:
        await gateway.run()
    except KeyboardInterrupt:
        print("\n⚠ Interrupted by user")
        gateway.running = False

if __name__ == "__main__":
    print("\n💡 Make sure:")
    print("  1. CircuitPython device is powered on")
    print("  2. MQTT broker is running (Mosquitto)")
    print("  3. Backend server is running")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
