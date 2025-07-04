#!/usr/bin/env python3
"""
Test Disk Expansion on Existing VM
"""

import sys
import os
import subprocess

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from modules.config import Config
from modules.logger import Logger

def test_disk_expansion(vm_name):
    """Test disk expansion on existing VM"""
    config = Config()
    logger = Logger()
    
    # Set govc environment
    env = os.environ.copy()
    env['GOVC_URL'] = f"https://{config.esxi_user}:{config.esxi_password}@{config.esxi_host}/sdk"
    env['GOVC_INSECURE'] = '1'
    
    logger.info(f"Testing disk expansion on: {vm_name}")
    logger.info(f"Target size: {config.vm_disk_size}GB")
    
    try:
        # Power off VM first
        logger.info("Powering off VM...")
        cmd = [config.govc_bin, 'vm.power', '-off', vm_name]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        import time
        time.sleep(5)
        
        # Get current disk info
        logger.info("Getting current disk information...")
        cmd = [config.govc_bin, 'vm.info', '-json', vm_name]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error("Could not get VM info")
            return
        
        import json
        vm_data = json.loads(result.stdout)
        disks = vm_data['VirtualMachines'][0]['Config']['Hardware']['Device']
        
        logger.info("Found devices:")
        for device in disks:
            if 'CapacityInBytes' in device:
                label = device.get('DeviceInfo', {}).get('Label', 'Unknown')
                size_gb = device['CapacityInBytes'] // (1024**3)
                logger.info(f"  {label}: {size_gb}GB")
        
        # Find disk to expand
        disk_device = None
        for device in disks:
            if device.get('DeviceInfo', {}).get('Label', '').startswith('Hard disk'):
                disk_device = device
                break
        
        if not disk_device:
            logger.error("Could not find primary disk device")
            return
        
        current_size_bytes = disk_device['CapacityInBytes']
        current_size_gb = current_size_bytes // (1024**3)
        target_size_gb = int(config.vm_disk_size)
        
        logger.info(f"Current disk size: {current_size_gb}GB")
        logger.info(f"Target disk size: {target_size_gb}GB")
        
        if current_size_gb >= target_size_gb:
            logger.info("Disk is already at or above target size")
            return
        
        # Try to expand the disk
        logger.info("Attempting disk expansion...")
        
        # Method 1: By label
        cmd = [
            config.govc_bin, 'vm.disk.change',
            '-vm', vm_name,
            '-disk.label', 'Hard disk 1',
            '-size', f'{target_size_gb}G'
        ]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"✅ Disk expanded to {target_size_gb}GB")
        else:
            logger.warn(f"Method 1 failed: {result.stderr}")
            
            # Method 2: By key
            logger.info("Trying alternative method...")
            cmd = [
                config.govc_bin, 'vm.disk.change',
                '-vm', vm_name,
                '-disk.key', '2000',
                '-size', f'{target_size_gb}G'
            ]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ Disk expanded to {target_size_gb}GB (method 2)")
            else:
                logger.error(f"Method 2 also failed: {result.stderr}")
                
                # Method 3: List devices and try by device path
                logger.info("Listing all devices...")
                cmd = [config.govc_bin, 'device.ls', '-vm', vm_name]
                result = subprocess.run(cmd, env=env, capture_output=True, text=True)
                print(result.stdout)
        
        # Power back on
        logger.info("Powering VM back on...")
        cmd = [config.govc_bin, 'vm.power', '-on', vm_name]
        subprocess.run(cmd, env=env, capture_output=True, text=True)
        
    except Exception as e:
        logger.error(f"Error: {e}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 test_disk_expansion.py <vm-name>")
        sys.exit(1)
    
    vm_name = sys.argv[1]
    test_disk_expansion(vm_name)

if __name__ == "__main__":
    main()
