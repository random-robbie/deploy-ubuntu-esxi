#!/usr/bin/env python3
"""
VM Diagnostic Tool - Check specific VM status and issues
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from modules.config import Config
from modules.logger import Logger
import subprocess

def diagnose_vm(vm_name):
    config = Config()
    logger = Logger()
    
    # Set govc environment
    env = os.environ.copy()
    env['GOVC_URL'] = f"https://{config.esxi_user}:{config.esxi_password}@{config.esxi_host}/sdk"
    env['GOVC_INSECURE'] = '1'
    
    logger.info(f"🔍 Diagnosing VM: {vm_name}")
    
    try:
        # 1. Check VM power state and basic info
        logger.info("=== VM Basic Info ===")
        cmd = [config.govc_bin, 'vm.info', vm_name]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        print(result.stdout)
        
        # 2. Check VM hardware configuration
        logger.info("=== VM Hardware ===")
        cmd = [config.govc_bin, 'vm.info', '-json', vm_name]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if 'numCpu' in result.stdout:
            import json
            vm_data = json.loads(result.stdout)
            vm_info = vm_data['VirtualMachines'][0]
            logger.info(f"CPUs: {vm_info['Config']['Hardware']['NumCPU']}")
            logger.info(f"Memory: {vm_info['Config']['Hardware']['MemoryMB']} MB")
        
        # 3. Check network devices
        logger.info("=== Network Devices ===")
        cmd = [config.govc_bin, 'device.ls', '-vm', vm_name]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        print(result.stdout)
        
        # 4. Check network adapter details
        logger.info("=== Network Adapter Details ===")
        cmd = [config.govc_bin, 'device.info', '-vm', vm_name, 'ethernet-*']
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        print(result.stdout)
        
        # 5. Check VM events for errors
        logger.info("=== Recent VM Events ===")
        cmd = [config.govc_bin, 'events', '-n', '10', vm_name]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        print(result.stdout)
        
        # 6. Check datastore info
        logger.info("=== Datastore Info ===")
        cmd = [config.govc_bin, 'datastore.info', config.datastore]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        print(result.stdout)
        
        # 7. Check if cloud-init ISO is attached
        logger.info("=== CD-ROM Devices ===")
        cmd = [config.govc_bin, 'device.info', '-vm', vm_name, 'cdrom-*']
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        print(result.stdout)
        
        # 8. Try to get VM IP with timeout
        logger.info("=== IP Address Check ===")
        cmd = [config.govc_bin, 'vm.ip', vm_name]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout.strip():
            ip = result.stdout.strip()
            logger.info(f"VM IP: {ip}")
            if ip == "0.0.0.0":
                logger.warn("IP is 0.0.0.0 - VM not getting DHCP")
        else:
            logger.warn("No IP address found")
            
        # 9. Check VM console for boot messages
        logger.info("=== VM Console Check ===")
        logger.info("Attempting to capture console output...")
        cmd = [config.govc_bin, 'vm.console', vm_name]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=5)
        if result.stdout:
            print("Console output:")
            print(result.stdout[-1000:])  # Last 1000 chars
        
    except subprocess.TimeoutExpired:
        logger.warn("Command timed out")
    except Exception as e:
        logger.error(f"Diagnostic error: {e}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 diagnose_vm.py <vm-name>")
        print("Example: python3 diagnose_vm.py ubuntu-pentest-20250704-102906")
        sys.exit(1)
    
    vm_name = sys.argv[1]
    diagnose_vm(vm_name)

if __name__ == "__main__":
    main()
