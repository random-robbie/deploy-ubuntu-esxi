#!/usr/bin/env python3
"""
Force VM Network Fix
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from modules.config import Config
from modules.logger import Logger
import subprocess
import time

def fix_vm_network(vm_name):
    config = Config()
    logger = Logger()
    
    # Set govc environment
    env = os.environ.copy()
    env['GOVC_URL'] = f"https://{config.esxi_user}:{config.esxi_password}@{config.esxi_host}/sdk"
    env['GOVC_INSECURE'] = '1'
    
    logger.info(f"🔧 Fixing network for VM: {vm_name}")
    
    try:
        # Step 1: Ensure network adapter is connected
        logger.info("Step 1: Connecting network adapter...")
        cmd = [config.govc_bin, 'device.connect', '-vm', vm_name, 'ethernet-0']
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        # Step 2: Force power cycle to reset network
        logger.info("Step 2: Power cycling VM...")
        cmd = [config.govc_bin, 'vm.power', '-off', vm_name]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        time.sleep(5)
        
        cmd = [config.govc_bin, 'vm.power', '-on', vm_name]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        # Step 3: Wait for boot and check IP
        logger.info("Step 3: Waiting for VM to boot...")
        for i in range(30):
            time.sleep(10)
            cmd = [config.govc_bin, 'vm.ip', vm_name]
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                ip = result.stdout.strip()
                if ip != "0.0.0.0":
                    logger.info(f"✅ VM IP: {ip}")
                    logger.info(f"Try SSH: ssh ubuntu@{ip} (password: ubuntu)")
                    return
            
            print(".", end="", flush=True)
        
        print()
        logger.warn("VM still has no IP after power cycle")
        
        # Step 4: Check if we need to manually run cloud-init
        logger.info("Step 4: The VM may need manual cloud-init trigger")
        logger.info("Try accessing via ESXi console:")
        logger.info("1. Go to ESXi web interface")
        logger.info(f"2. Open console for VM: {vm_name}")
        logger.info("3. Login may work with default cloud image credentials")
        logger.info("4. Manually run: sudo cloud-init clean && sudo cloud-init init")
        
    except Exception as e:
        logger.error(f"Fix failed: {e}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 fix_network.py <vm-name>")
        sys.exit(1)
    
    vm_name = sys.argv[1]
    fix_vm_network(vm_name)

if __name__ == "__main__":
    main()
