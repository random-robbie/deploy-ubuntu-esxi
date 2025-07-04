#!/usr/bin/env python3
"""
Check Boot Order and CD-ROM Status
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from modules.config import Config
from modules.logger import Logger
import subprocess

def check_boot_order(vm_name):
    config = Config()
    logger = Logger()
    
    # Set govc environment
    env = os.environ.copy()
    env['GOVC_URL'] = f"https://{config.esxi_user}:{config.esxi_password}@{config.esxi_host}/sdk"
    env['GOVC_INSECURE'] = '1'
    
    logger.info(f"🔍 Checking boot configuration for: {vm_name}")
    
    try:
        # Check all devices
        logger.info("=== All VM Devices ===")
        cmd = [config.govc_bin, 'device.ls', '-vm', vm_name]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        print(result.stdout)
        
        # Check CD-ROM specifically
        logger.info("=== CD-ROM Device Info ===")
        cmd = [config.govc_bin, 'device.info', '-vm', vm_name, 'cdrom-*']
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if result.stdout.strip():
            print(result.stdout)
        else:
            logger.warn("No CD-ROM device found!")
            
        # Check if ISO is actually attached
        devices_output = subprocess.run([config.govc_bin, 'device.ls', '-vm', vm_name], 
                                      env=env, capture_output=True, text=True).stdout
        
        if 'cdrom' in devices_output.lower():
            logger.info("✅ CD-ROM device exists")
            # Check if it has our ISO
            if 'cloud-init.iso' in devices_output:
                logger.info("✅ Cloud-init ISO is attached")
            else:
                logger.warn("❌ Cloud-init ISO not attached or different file")
        else:
            logger.error("❌ No CD-ROM device found")
            
        # Try to check boot order (may not work with govc)
        logger.info("=== Attempting Boot Order Check ===")
        cmd = [config.govc_bin, 'device.boot', '-vm', vm_name]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if result.returncode == 0:
            print("Boot order:")
            print(result.stdout)
        else:
            logger.warn("Cannot check boot order with govc")
            
    except Exception as e:
        logger.error(f"Error: {e}")

def force_cdrom_boot(vm_name):
    config = Config()
    logger = Logger()
    
    env = os.environ.copy()
    env['GOVC_URL'] = f"https://{config.esxi_user}:{config.esxi_password}@{config.esxi_host}/sdk"
    env['GOVC_INSECURE'] = '1'
    
    logger.info("🔧 Attempting to force CD-ROM boot...")
    
    try:
        # Power off VM
        logger.info("Powering off VM...")
        cmd = [config.govc_bin, 'vm.power', '-off', vm_name]
        subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        import time
        time.sleep(5)
        
        # Try to set boot order via device.boot
        logger.info("Attempting to set boot order...")
        cmd = [config.govc_bin, 'device.boot', '-vm', vm_name, '-order', 'cdrom,disk']
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ Boot order set to CD-ROM first")
        else:
            logger.warn("❌ Could not set boot order via govc")
            logger.info("You'll need to set boot order manually in ESXi web interface")
            
        # Power back on
        logger.info("Powering on VM...")
        cmd = [config.govc_bin, 'vm.power', '-on', vm_name]
        subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        logger.info("✅ VM powered on - should boot from CD-ROM now")
        
    except Exception as e:
        logger.error(f"Error: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 check_boot.py <vm-name> [force]")
        print("  check_boot.py vm-name        - Check boot configuration")
        print("  check_boot.py vm-name force  - Force CD-ROM boot order")
        sys.exit(1)
    
    vm_name = sys.argv[1]
    
    if len(sys.argv) > 2 and sys.argv[2] == 'force':
        force_cdrom_boot(vm_name)
    else:
        check_boot_order(vm_name)

if __name__ == "__main__":
    main()
