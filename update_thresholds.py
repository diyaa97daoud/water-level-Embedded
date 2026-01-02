#!/usr/bin/env python3
"""
Update device thresholds via backend API
Usage: python update_thresholds.py <min_threshold> <max_threshold>
Example: python update_thresholds.py 5.0 20.0

This updates the database AND publishes to the device via MQTT automatically.
"""

import sys
import json
import requests

# Configuration
BACKEND_URL = "http://localhost:8080/api"
USERNAME = "admin"
PASSWORD = "admin123"
CONFIG_FILE = "e:\\config.json"

def get_device_info():
    """Read device_key from config.json"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            device_key = config.get("device_key")
            if not device_key:
                print("✗ Error: device_key not found in config.json")
                return None
            return device_key
    except FileNotFoundError:
        print(f"✗ Error: {CONFIG_FILE} not found")
        return None
    except json.JSONDecodeError:
        print(f"✗ Error: Invalid JSON in {CONFIG_FILE}")
        return None

def find_device_id(token, device_key):
    """Find device ID by device_key from backend"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BACKEND_URL}/devices", headers=headers)
        
        if response.status_code == 200:
            devices = response.json()
            # Handle paginated response
            if 'content' in devices:
                for device in devices['content']:
                    if device.get('deviceKey') == device_key:
                        return device.get('id')
            else:
                # Handle non-paginated response
                for device in devices:
                    if device.get('deviceKey') == device_key:
                        return device.get('id')
        
        print(f"✗ Device with key {device_key} not found in backend")
        return None
    except Exception as e:
        print(f"✗ Error finding device: {e}")
        return None

def update_thresholds(min_threshold, max_threshold):
    """Update device thresholds via backend API"""
    
    try:
        # Step 0: Get device_key from config.json
        print("📁 Reading device configuration...")
        device_key = get_device_info()
        if not device_key:
            return False
        print(f"✓ Device key: {device_key}")
        
        # Step 1: Login
        print(f"\n🔐 Logging in as {USERNAME}...")
        login_response = requests.post(
            f"{BACKEND_URL}/auth/login",
            json={"username": USERNAME, "password": PASSWORD},
            headers={"Content-Type": "application/json"}
        )
        
        if login_response.status_code != 200:
            print(f"✗ Login failed: {login_response.text}")
            return False
        
        token = login_response.json()["token"]
        print("✓ Login successful")
        
        # Step 2: Find device ID
        print(f"\n🔍 Finding device in database...")
        device_id = find_device_id(token, device_key)
        if not device_id:
            return False
        print(f"✓ Found device ID: {device_id}")
        
        # Step 3: Update thresholds
        print(f"\n📝 Updating thresholds for device {device_id}...")
        print(f"   Min threshold: {min_threshold}cm (high water level, pump auto-stops)")
        print(f"   Max threshold: {max_threshold}cm (low water level, admin can start pump)")
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        update_response = requests.put(
            f"{BACKEND_URL}/devices/{device_id}/thresholds",
            json={"minThreshold": min_threshold, "maxThreshold": max_threshold},
            headers=headers
        )
        
        if update_response.status_code != 200:
            print(f"✗ Update failed: {update_response.text}")
            return False
        
        result = update_response.json()
        print("\n✓ Thresholds updated successfully!")
        print(f"   Database: min={result['minThreshold']}, max={result['maxThreshold']}")
        print(f"   MQTT published to device automatically")
        print(f"   Device will save to config.json")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"✗ Could not connect to backend at {BACKEND_URL}")
        print("  Make sure the backend is running on http://localhost:8080")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python update_thresholds.py <min_threshold> <max_threshold>")
        print("Example: python update_thresholds.py 5.0 20.0")
        print()
        print("Threshold meanings:")
        print("  - min_threshold: High water level (pump auto-stops when reached)")
        print("  - max_threshold: Low water level (admin can start pump)")
        sys.exit(1)
    
    try:
        min_val = float(sys.argv[1])
        max_val = float(sys.argv[2])
        
        if min_val >= max_val:
            print("Error: min_threshold must be less than max_threshold")
            sys.exit(1)
        
        success = update_thresholds(min_val, max_val)
        sys.exit(0 if success else 1)
        
    except ValueError:
        print("Error: Thresholds must be numeric values")
        sys.exit(1)