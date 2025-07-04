#!/usr/bin/env python3
"""
Simple Network Diagnostic for VM
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from modules.config import Config
from modules.logger import Logger
import subprocess

def check_network(vm_name):
    config = Config()
    logger = Logger()
    
    # Set govc environment
    env = os.environ.copy()
    env['GOVC_URL'] = f"https://{config.esxi_user}:{config.esxi_password}@{config.esxi_host}/sdk"
    env['GOVC_INSECURE'] = '1'
    
    logger.info(f"🔍 Network Diagnostic for: {vm_name}")
    
    try:
        # Check network devices
        logger.info("=== Network Devices ===")
        cmd = [config.govc_bin, 'device.ls', '-vm', vm_name]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        print(result.stdout)
        
        # Check if network is connected
        logger.info("=== Network Connection Status ===")
        cmd = [config.govc_bin, 'device.info', '-vm', vm_name, 'ethernet-0']
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        print(result.stdout)
        
        # Check VM tools status
        logger.info("=== VMware Tools Status ===")
        cmd = [config.govc_bin, 'vm.info', vm_name]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if 'Tools' in line or 'Guest' in line:
                print(line)
        
        # Try to get guest info
        logger.info("=== Guest OS Info ===")
        cmd = [config.govc_bin, 'vm.info', '-json', vm_name]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if 'guestFullName' in result.stdout:
            print("Guest OS detected")
        else:
            print("Guest OS not detected - VMware Tools may not be running")
            
        # Check if we can connect the network
        logger.info("=== Attempting to Connect Network ===")
        cmd = [config.govc_bin, 'device.connect', '-vm', vm_name, 'ethernet-0']
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("✅ Network connected successfully")
        else:
            logger.warn(f"Network connect failed: {result.stderr}")
            
        # Wait and check IP again
        logger.info("=== Checking IP After Network Connect ===")
        import time
        time.sleep(10)
        cmd = [config.govc_bin, 'vm.ip', vm_name]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            ip = result.stdout.strip()
            if ip != "0.0.0.0":
                logger.info(f"✅ VM IP: {ip}")
            else:
                logger.warn("Still no IP - checking cloud-init")
                
        # Check if cloud-init ISO is properly attached
        logger.info("=== Cloud-Init ISO Status ===")
        cmd = [config.govc_bin, 'device.ls', '-vm', vm_name]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if 'cdrom' in result.stdout.lower():
            logger.info("CD-ROM device found")
            # Check what's in the CD-ROM
            cmd = [config.govc_bin, 'device.info', '-vm', vm_name, 'cdrom-3000']
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            print(result.stdout)
        else:
            logger.warn("No CD-ROM device found")
            
    except Exception as e:
        logger.error(f"Error: {e}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 network_check.py <vm-name>")
        sys.exit(1)
    
    vm_name = sys.argv[1]
    check_network(vm_name)

if __name__ == "__main__":
    main()
