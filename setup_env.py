#!/usr/bin/env python3
"""
Setup script for Water Level Monitoring System
- Creates admin user
- Registers device in database

Usage: python setup_system.py
"""

import requests
import json

# Configuration
BACKEND_URL = "http://localhost:8080/api"

# User credentials
ADMIN_USERNAME = "admin"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"

# Device configuration
DEVICE_NAME = "Water Tank Sensor"
DEVICE_KEY = "12345678-1234-1234-1234-123456789abc"  # UUID format required
MIN_THRESHOLD = 5.0  # cm - high water level (pump auto-stops)
MAX_THRESHOLD = 20.0  # cm - low water level (can start pump)

def register_admin():
    """Register admin user"""
    print("=" * 60)
    print("STEP 1: Registering Admin User")
    print("=" * 60)
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/auth/register",
            json={
                "username": ADMIN_USERNAME,
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            # Registration returns full auth response with user nested inside
            user = data.get('user', data)
            print(f"✓ Admin user created successfully!")
            print(f"   User ID: {user['id']}")
            print(f"   Username: {user['username']}")
            print(f"   Email: {user.get('email', 'N/A')}")
            print(f"   Role: {user['role']}")
            
            # Check if role is correct
            if user['role'] != 'ADMIN':
                print(f"   ⚠ WARNING: User role is '{user['role']}' instead of 'ADMIN'")
                print(f"   You may need to manually update the role in the database")
            
            return True
        elif response.status_code == 409 or "already exists" in response.text.lower():
            print(f"⚠ Admin user already exists")
            return True
        else:
            print(f"✗ Failed to register admin: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"✗ Could not connect to backend at {BACKEND_URL}")
        print("  Make sure the backend is running on http://localhost:8080")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def login_admin():
    """Login as admin and get token"""
    print("\n" + "=" * 60)
    print("STEP 2: Logging in as Admin")
    print("=" * 60)
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/auth/login",
            json={
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            token = response.json()["token"]
            print(f"✓ Login successful")
            return token
        else:
            print(f"✗ Login failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

def register_device(token):
    """Register device in database"""
    print("\n" + "=" * 60)
    print("STEP 3: Registering Device")
    print("=" * 60)
    
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/devices/register",
            json={
                "name": DEVICE_NAME,
                "minThreshold": MIN_THRESHOLD,
                "maxThreshold": MAX_THRESHOLD
            },
            headers=headers
        )
        
        if response.status_code == 200 or response.status_code == 201:
            device = response.json()
            print(f"✓ Device registered successfully!")
            print(f"   Device ID: {device['id']}")
            print(f"   Device Name: {device['name']}")
            print(f"   Device Key: {device['deviceKey']}")
            print(f"   Min Threshold: {device['minThreshold']}cm (high water, pump stops)")
            print(f"   Max Threshold: {device['maxThreshold']}cm (low water, can start pump)")
            print(f"\n⚠ IMPORTANT: Update e:\\config.json with this device_key:")
            print(f'   {{"device_id": "device1345", "device_key": "{device["deviceKey"]}", "min_threshold": {MIN_THRESHOLD}, "max_threshold": {MAX_THRESHOLD}}}')
            return device['id']
        elif response.status_code == 409 or "already exists" in response.text.lower():
            print(f"⚠ Device with this key already exists")
            # Try to get existing device
            try:
                devices_response = requests.get(f"{BACKEND_URL}/devices", headers=headers)
                if devices_response.status_code == 200:
                    devices = devices_response.json()
                    if 'content' in devices:
                        for dev in devices['content']:
                            if dev['deviceKey'] == DEVICE_KEY:
                                print(f"   Found existing device:")
                                print(f"   Device ID: {dev['id']}")
                                print(f"   Device Name: {dev['name']}")
                                return dev['id']
            except:
                pass
            return None
        else:
            print(f"✗ Failed to register device: {response.text}")
            return None
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

def main():
    print("\n🚀 Water Level Monitoring System Setup")
    print()
    
    # Step 1: Register admin user
    if not register_admin():
        print("\n❌ Setup failed at user registration")
        return False
    
    # Step 2: Login
    token = login_admin()
    if not token:
        print("\n❌ Setup failed at login")
        return False
    
    # Step 3: Register device
    device_id = register_device(token)
    if device_id is None:
        print("\n⚠ Device registration had issues (may already exist)")
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ SETUP COMPLETE")
    print("=" * 60)
    print("\nSystem is ready!")
    print("\n📋 Quick reference:")
    print(f"   Admin username: {ADMIN_USERNAME}")
    print(f"   Admin password: {ADMIN_PASSWORD}")
    print(f"   Device ID: {device_id if device_id else '(check database)'}")
    print(f"   (See device_key above in the registration output)")
    print("\n📝 Next steps:")
    print("   1. Make sure Mosquitto MQTT broker is running")
    print("   2. Start the gateway: python e:\\ble_mqtt_gateway.py")
    print("   3. Power on the CircuitPython device")
    print("   4. Data should start flowing automatically")
    print("\n🔧 Test commands:")
    print(f"   Update thresholds: python e:\\update_thresholds.py 5.0 20.0")
    print(f"   Start pump: python e:\\send_pump_command.py START_PUMP")
    print(f"   Stop pump: python e:\\send_pump_command.py STOP_PUMP")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠ Setup interrupted by user")
        exit(1)