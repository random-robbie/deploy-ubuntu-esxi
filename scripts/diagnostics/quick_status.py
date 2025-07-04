#!/usr/bin/env python3
"""
Quick VM Status Check - Non-blocking
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from modules.config import Config
from modules.logger import Logger
import subprocess

def quick_status(vm_name):
    config = Config()
    logger = Logger()
    
    # Set govc environment
    env = os.environ.copy()
    env['GOVC_URL'] = f"https://{config.esxi_user}:{config.esxi_password}@{config.esxi_host}/sdk"
    env['GOVC_INSECURE'] = '1'
    
    logger.info(f"📊 Quick Status: {vm_name}")
    
    try:
        # Quick power state check
        cmd = [config.govc_bin, 'vm.info', vm_name]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=10)
        
        for line in result.stdout.split('\n'):
            if 'Power state:' in line:
                logger.info(line.strip())
            elif 'IP address:' in line:
                logger.info(line.strip())
        
        # Quick IP check
        cmd = [config.govc_bin, 'vm.ip', vm_name]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0 and result.stdout.strip():
            ip = result.stdout.strip()
            if ip and ip != "0.0.0.0":
                logger.info(f"✅ Current IP: {ip}")
                logger.info(f"🚀 Try SSH: ssh ubuntu@{ip}")
            else:
                logger.warn("❌ No IP or 0.0.0.0")
        else:
            logger.warn("❌ Could not get IP")
            
    except subprocess.TimeoutExpired:
        logger.warn("⏰ Command timed out - ESXi may be busy")
    except Exception as e:
        logger.error(f"Error: {e}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 quick_status.py <vm-name>")
        sys.exit(1)
    
    vm_name = sys.argv[1]
    quick_status(vm_name)

if __name__ == "__main__":
    main()
