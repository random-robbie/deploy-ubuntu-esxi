#!/usr/bin/env python3
"""
VM Status Checker and Fixer
Check current VM status and manually fix hostname/network issues
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from modules.config import Config
from modules.logger import Logger
import subprocess

def main():
    config = Config()
    logger = Logger()
    
    # Set govc environment
    env = os.environ.copy()
    env['GOVC_URL'] = f"https://{config.esxi_user}:{config.esxi_password}@{config.esxi_host}/sdk"
    env['GOVC_INSECURE'] = '1'
    
    logger.info("Checking VM status...")
    
    # Find the latest VM
    try:
        cmd = [config.govc_bin, 'ls', '/*/vm/']
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        vms = [line for line in result.stdout.split('\n') if 'ubuntu-pentest' in line]
        
        if not vms:
            logger.error("No ubuntu-pentest VMs found")
            return
            
        latest_vm = vms[-1].split('/')[-1]
        logger.info(f"Found VM: {latest_vm}")
        
        # Check power state
        cmd = [config.govc_bin, 'vm.info', '-json', latest_vm]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if 'poweredOn' in result.stdout:
            logger.info("✅ VM is powered on")
        else:
            logger.warn("❌ VM is not powered on")
            
        # Check IP
        cmd = [config.govc_bin, 'vm.ip', latest_vm]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout.strip():
            ip = result.stdout.strip()
            if ip != "0.0.0.0":
                logger.info(f"✅ VM IP: {ip}")
            else:
                logger.warn("❌ VM has no IP (0.0.0.0)")
        else:
            logger.warn("❌ Could not get VM IP")
            
        # Show VM info
        cmd = [config.govc_bin, 'vm.info', latest_vm]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        logger.status("\nVM Details:")
        print(result.stdout)
        
    except Exception as e:
        logger.error(f"Error checking VM: {e}")

if __name__ == "__main__":
    main()
