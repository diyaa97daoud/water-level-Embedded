#!/usr/bin/env python3
"""
Simple BLE Scanner - Test to see all available BLE devices
"""

import asyncio
from bleak import BleakScanner

async def scan():
    print("Scanning for ALL BLE devices (10 seconds)...")
    print("=" * 60)
    
    devices = await BleakScanner.discover(timeout=10.0)
    
    if len(devices) == 0:
        print("⚠ No BLE devices found!")
        print("\nTroubleshooting:")
        print("1. Make sure Bluetooth is ON in Windows Settings")
        print("2. Check if the nRF device is powered on")
        print("3. Try moving the device closer to your PC")
    else:
        print(f"Found {len(devices)} device(s):\n")
        for device in devices:
            print(f"  Name: {device.name or '(Unknown)'}")
            print(f"  Address: {device.address}")

if __name__ == "__main__":
    asyncio.run(scan())
