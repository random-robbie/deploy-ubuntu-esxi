#!/usr/bin/env python3
"""
Fix CD-ROM Connection and Force Boot
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from modules.config import Config
from modules.logger import Logger
import subprocess
import time

def fix_cdrom_and_boot(vm_name):
    config = Config()
    logger = Logger()
    
    env = os.environ.copy()
    env['GOVC_URL'] = f"https://{config.esxi_user}:{config.esxi_password}@{config.esxi_host}/sdk"
    env['GOVC_INSECURE'] = '1'
    
    logger.info(f"🔧 Fixing CD-ROM connection for: {vm_name}")
    
    try:
        # Step 1: Power off VM
        logger.info("Step 1: Powering off VM...")
        cmd = [config.govc_bin, 'vm.power', '-off', vm_name]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        time.sleep(5)
        
        # Step 2: Connect the CD-ROM device
        logger.info("Step 2: Connecting cloud-init CD-ROM...")
        cmd = [config.govc_bin, 'device.connect', '-vm', vm_name, 'cdrom-3002']
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ CD-ROM connected successfully")
        else:
            logger.warn(f"CD-ROM connect warning: {result.stderr}")
        
        # Step 3: Try to set boot order to CD-ROM first
        logger.info("Step 3: Setting boot order to CD-ROM first...")
        
        # Method 1: Try device.boot
        cmd = [config.govc_bin, 'device.boot', '-vm', vm_name, '-order', 'cdrom-3002,disk-1000-0']
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ Boot order set via device.boot")
        else:
            # Method 2: Try generic boot order
            logger.info("Trying alternative boot order method...")
            cmd = [config.govc_bin, 'device.boot', '-vm', vm_name, '-order', 'cdrom,disk']
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ Boot order set via generic method")
            else:
                logger.warn("❌ Could not set boot order automatically")
                logger.info("You may need to set boot order manually in ESXi")
        
        # Step 4: Power on VM
        logger.info("Step 4: Powering on VM...")
        cmd = [config.govc_bin, 'vm.power', '-on', vm_name]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ VM powered on")
        else:
            logger.error(f"Power on failed: {result.stderr}")
            return
        
        # Step 5: Monitor boot and IP
        logger.info("Step 5: Monitoring VM boot...")
        logger.info("VM should now boot from CD-ROM and run cloud-init")
        
        for i in range(60):  # Wait up to 10 minutes
            time.sleep(10)
            
            # Check IP
            cmd = [config.govc_bin, 'vm.ip', vm_name]
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and result.stdout.strip():
                ip = result.stdout.strip()
                if ip and ip != "0.0.0.0":
                    logger.info(f"✅ VM got IP: {ip}")
                    logger.info(f"🚀 Try SSH: ssh ubuntu@{ip} (password: ubuntu)")
                    logger.info("Or try console login: ubuntu/ubuntu")
                    return
            
            if i % 6 == 0:  # Every minute
                logger.info(f"Still waiting... ({i//6 + 1}/10 minutes)")
            else:
                print(".", end="", flush=True)
        
        print()
        logger.warn("VM booted but no IP yet. Check ESXi console for progress.")
        logger.info("Try console login in ESXi web interface")
        
    except subprocess.TimeoutExpired:
        logger.warn("Command timed out")
    except Exception as e:
        logger.error(f"Fix failed: {e}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 fix_cdrom.py <vm-name>")
        sys.exit(1)
    
    vm_name = sys.argv[1]
    fix_cdrom_and_boot(vm_name)

if __name__ == "__main__":
    main()
