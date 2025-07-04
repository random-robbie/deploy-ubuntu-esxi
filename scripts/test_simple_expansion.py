#!/usr/bin/env python3
"""
Simple Disk Expansion Test
Test different govc disk expansion methods
"""

import sys
import os
import subprocess

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from modules.config import Config
from modules.logger import Logger

def test_expansion_methods(vm_name, target_size):
    """Test different disk expansion methods"""
    config = Config()
    logger = Logger()
    
    # Set govc environment
    env = os.environ.copy()
    env['GOVC_URL'] = f"https://{config.esxi_user}:{config.esxi_password}@{config.esxi_host}/sdk"
    env['GOVC_INSECURE'] = '1'
    
    logger.info(f"Testing disk expansion methods on: {vm_name}")
    logger.info(f"Target size: {target_size}GB")
    
    # Power off VM first
    logger.info("Powering off VM...")
    cmd = [config.govc_bin, 'vm.power', '-off', vm_name]
    subprocess.run(cmd, env=env, capture_output=True, text=True)
    
    import time
    time.sleep(5)
    
    try:
        # List devices first
        logger.info("Current VM devices:")
        cmd = [config.govc_bin, 'device.ls', '-vm', vm_name]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(result.stdout)
            print("-" * 50)
        
        # Method 1: Simple size change
        logger.info("Method 1: Simple vm.disk.change -size")
        cmd = [
            config.govc_bin, 'vm.disk.change',
            '-vm', vm_name,
            '-size', f'{target_size}G'
        ]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        logger.info(f"Result: {result.returncode}")
        logger.info(f"Stdout: {result.stdout}")
        logger.info(f"Stderr: {result.stderr}")
        print("-" * 50)
        
        if result.returncode == 0:
            logger.info("✅ Method 1 worked!")
            return
        
        # Method 2: With disk label
        logger.info("Method 2: With -disk.label")
        cmd = [
            config.govc_bin, 'vm.disk.change',
            '-vm', vm_name,
            '-disk.label', 'Hard disk 1',
            '-size', f'{target_size}G'
        ]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        logger.info(f"Result: {result.returncode}")
        logger.info(f"Stdout: {result.stdout}")
        logger.info(f"Stderr: {result.stderr}")
        print("-" * 50)
        
        if result.returncode == 0:
            logger.info("✅ Method 2 worked!")
            return
        
        # Method 3: With disk key
        logger.info("Method 3: With -disk.key 2000")
        cmd = [
            config.govc_bin, 'vm.disk.change',
            '-vm', vm_name,
            '-disk.key', '2000',
            '-size', f'{target_size}G'
        ]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        logger.info(f"Result: {result.returncode}")
        logger.info(f"Stdout: {result.stdout}")
        logger.info(f"Stderr: {result.stderr}")
        print("-" * 50)
        
        if result.returncode == 0:
            logger.info("✅ Method 3 worked!")
            return
        
        # Check what disks exist
        logger.info("Method 4: Finding specific disk device")
        cmd = [config.govc_bin, 'device.info', '-vm', vm_name, 'disk-*']
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("Disk device info:")
            print(result.stdout)
        
        logger.info("❌ All methods failed")
        
    finally:
        # Power back on
        logger.info("Powering VM back on...")
        cmd = [config.govc_bin, 'vm.power', '-on', vm_name]
        subprocess.run(cmd, env=env, capture_output=True, text=True)

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 test_simple_expansion.py <vm-name> <target-size-gb>")
        print("Example: python3 test_simple_expansion.py ubuntu-pentest-20250704-112954 500")
        sys.exit(1)
    
    vm_name = sys.argv[1]
    target_size = sys.argv[2]
    
    test_expansion_methods(vm_name, target_size)

if __name__ == "__main__":
    main()
