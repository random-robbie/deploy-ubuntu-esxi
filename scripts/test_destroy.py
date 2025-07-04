#!/usr/bin/env python3
"""
Safe VM Destruction Test
Creates a test VM just to verify destruction works
"""

import sys
import os
import subprocess

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from modules.config import Config
from modules.logger import Logger

def create_test_vm(config, logger, env):
    """Create a minimal test VM for destruction testing"""
    logger.info("Creating test VM for destruction testing...")
    
    test_vm_name = "test-destroy-me"
    
    try:
        # Create a minimal VM
        cmd = [
            config.govc_bin, 'vm.create',
            '-m', '512',      # 512MB RAM
            '-c', '1',        # 1 CPU
            '-disk', '1GB',   # 1GB disk
            '-on', 'false',   # Don't power on
            test_vm_name
        ]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"✅ Test VM created: {test_vm_name}")
            return test_vm_name
        else:
            logger.error(f"Failed to create test VM: {result.stderr}")
            return None
            
    except Exception as e:
        logger.error(f"Error creating test VM: {e}")
        return None

def main():
    config = Config()
    logger = Logger()
    
    # Set up environment
    env = os.environ.copy()
    env['GOVC_URL'] = f"https://{config.esxi_user}:{config.esxi_password}@{config.esxi_host}/sdk"
    env['GOVC_INSECURE'] = '1'
    
    print("🧪 VM Destruction Test")
    print("=" * 30)
    print("This will create a test VM and then destroy it to verify the destruction script works.")
    
    confirm = input("Create test VM for destruction? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("Test cancelled")
        return
    
    # Create test VM
    test_vm = create_test_vm(config, logger, env)
    
    if test_vm:
        print(f"\n✅ Test VM '{test_vm}' created")
        print(f"\nNow run the destruction script:")
        print(f"python3 scripts/destroy_vm.py {test_vm}")
        print("\nOr use the interactive helper:")
        print("python3 scripts/vm_helper.py")
    else:
        print("❌ Failed to create test VM")

if __name__ == "__main__":
    main()
