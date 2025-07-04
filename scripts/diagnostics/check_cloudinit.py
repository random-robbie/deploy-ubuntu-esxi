#!/usr/bin/env python3
"""
Cloud-Init Log Checker
Monitor cloud-init progress and troubleshoot issues
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from modules.config import Config
from modules.logger import Logger
import subprocess
import time

def check_cloud_init_logs(vm_name, follow=False):
    """Check cloud-init logs via SSH or guest tools"""
    config = Config()
    logger = Logger()
    
    # Set govc environment
    env = os.environ.copy()
    env['GOVC_URL'] = f"https://{config.esxi_user}:{config.esxi_password}@{config.esxi_host}/sdk"
    env['GOVC_INSECURE'] = '1'
    
    logger.info(f"📋 Checking cloud-init logs for: {vm_name}")
    
    try:
        # First, get VM IP
        vm_ip = get_vm_ip(config, logger, env, vm_name)
        
        if vm_ip:
            check_logs_via_ssh(config, logger, vm_ip, follow)
        else:
            logger.warn("No IP address - cannot check logs via SSH")
            logger.info("Try checking manually via ESXi console")
            
    except Exception as e:
        logger.error(f"Error checking logs: {e}")

def get_vm_ip(config, logger, env, vm_name):
    """Get VM IP address"""
    logger.info("Getting VM IP address...")
    
    cmd = [config.govc_bin, 'vm.ip', vm_name]
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    
    if result.returncode == 0 and result.stdout.strip():
        ip = result.stdout.strip()
        if ip and ip != "0.0.0.0":
            logger.info(f"✅ VM IP: {ip}")
            return ip
    
    return None

def check_logs_via_ssh(config, logger, vm_ip, follow):
    """Check cloud-init logs via SSH"""
    logger.info(f"Connecting to ubuntu@{vm_ip} to check cloud-init...")
    
    # Test SSH connectivity first
    ssh_cmd = [
        'ssh', '-o', 'ConnectTimeout=5', 
        '-o', 'StrictHostKeyChecking=no',
        '-o', 'BatchMode=yes',
        f'ubuntu@{vm_ip}', 'echo "SSH OK"'
    ]
    
    result = subprocess.run(ssh_cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        logger.warn("SSH connection failed - trying with password...")
        check_logs_with_password(config, logger, vm_ip, follow)
        return
    
    logger.info("✅ SSH connection successful")
    
    # Check cloud-init status
    logger.info("=== Cloud-Init Status ===")
    ssh_cmd = [
        'ssh', '-o', 'ConnectTimeout=5', 
        '-o', 'StrictHostKeyChecking=no',
        f'ubuntu@{vm_ip}', 'sudo cloud-init status --long'
    ]
    result = subprocess.run(ssh_cmd, capture_output=True, text=True)
    print(result.stdout)
    
    # Check cloud-init logs
    logger.info("=== Cloud-Init Log (last 50 lines) ===")
    ssh_cmd = [
        'ssh', '-o', 'ConnectTimeout=5', 
        '-o', 'StrictHostKeyChecking=no',
        f'ubuntu@{vm_ip}', 'sudo tail -50 /var/log/cloud-init.log'
    ]
    result = subprocess.run(ssh_cmd, capture_output=True, text=True)
    print(result.stdout)
    
    # Check cloud-init output log
    logger.info("=== Cloud-Init Output Log (last 30 lines) ===")
    ssh_cmd = [
        'ssh', '-o', 'ConnectTimeout=5', 
        '-o', 'StrictHostKeyChecking=no',
        f'ubuntu@{vm_ip}', 'sudo tail -30 /var/log/cloud-init-output.log'
    ]
    result = subprocess.run(ssh_cmd, capture_output=True, text=True)
    print(result.stdout)
    
    if follow:
        logger.info("=== Following Cloud-Init Log (Ctrl+C to stop) ===")
        try:
            ssh_cmd = [
                'ssh', '-o', 'ConnectTimeout=5', 
                '-o', 'StrictHostKeyChecking=no',
                f'ubuntu@{vm_ip}', 'sudo tail -f /var/log/cloud-init-output.log'
            ]
            subprocess.run(ssh_cmd)
        except KeyboardInterrupt:
            logger.info("Stopped following log")

def check_logs_with_password(config, logger, vm_ip, follow):
    """Try to check logs using password authentication"""
    
    if not check_sshpass():
        logger.warn("sshpass not available - install with: brew install hudochenkov/sshpass/sshpass")
        logger.info("Manual check:")
        logger.info(f"ssh ubuntu@{vm_ip}")
        logger.info("Password: ubuntu")
        logger.info("Then run: sudo cloud-init status --long")
        logger.info("And: sudo tail -f /var/log/cloud-init-output.log")
        return
    
    logger.info("Trying SSH with password...")
    
    # Check cloud-init status with password
    logger.info("=== Cloud-Init Status ===")
    ssh_cmd = [
        'sshpass', '-p', 'ubuntu', 'ssh', 
        '-o', 'ConnectTimeout=5', 
        '-o', 'StrictHostKeyChecking=no',
        f'ubuntu@{vm_ip}', 'sudo cloud-init status --long'
    ]
    result = subprocess.run(ssh_cmd, capture_output=True, text=True)
    print(result.stdout)
    
    # Check cloud-init logs with password
    logger.info("=== Cloud-Init Log (last 50 lines) ===")
    ssh_cmd = [
        'sshpass', '-p', 'ubuntu', 'ssh', 
        '-o', 'ConnectTimeout=5', 
        '-o', 'StrictHostKeyChecking=no',
        f'ubuntu@{vm_ip}', 'sudo tail -50 /var/log/cloud-init.log'
    ]
    result = subprocess.run(ssh_cmd, capture_output=True, text=True)
    print(result.stdout)

def check_sshpass():
    """Check if sshpass is available"""
    try:
        subprocess.run(['sshpass'], capture_output=True)
        return True
    except FileNotFoundError:
        return False

def check_cloud_init_progress(vm_name):
    """Quick check of cloud-init progress"""
    config = Config()
    logger = Logger()
    
    env = os.environ.copy()
    env['GOVC_URL'] = f"https://{config.esxi_user}:{config.esxi_password}@{config.esxi_host}/sdk"
    env['GOVC_INSECURE'] = '1'
    
    logger.info(f"🔍 Quick cloud-init progress check: {vm_name}")
    
    vm_ip = get_vm_ip(config, logger, env, vm_name)
    
    if not vm_ip:
        logger.warn("No IP - cloud-init may still be running or failed")
        return
    
    # Quick status check
    if check_sshpass():
        ssh_cmd = [
            'sshpass', '-p', 'ubuntu', 'ssh', 
            '-o', 'ConnectTimeout=5', 
            '-o', 'StrictHostKeyChecking=no',
            f'ubuntu@{vm_ip}', 'sudo cloud-init status'
        ]
    else:
        ssh_cmd = [
            'ssh', '-o', 'ConnectTimeout=5', 
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'BatchMode=yes',
            f'ubuntu@{vm_ip}', 'sudo cloud-init status'
        ]
    
    result = subprocess.run(ssh_cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        status = result.stdout.strip()
        if 'done' in status:
            logger.info("✅ Cloud-init completed successfully")
        elif 'running' in status:
            logger.info("🔄 Cloud-init is still running...")
        elif 'error' in status:
            logger.warn("❌ Cloud-init encountered errors")
        else:
            logger.info(f"Status: {status}")
    else:
        logger.warn("Could not check cloud-init status")

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 check_cloudinit.py <vm-name>           - Check cloud-init logs")
        print("  python3 check_cloudinit.py <vm-name> follow    - Follow cloud-init logs")
        print("  python3 check_cloudinit.py <vm-name> progress  - Quick progress check")
        print("")
        print("Examples:")
        print("  python3 check_cloudinit.py ubuntu-pentest-20250704-102906")
        print("  python3 check_cloudinit.py ubuntu-pentest-20250704-102906 follow")
        sys.exit(1)
    
    vm_name = sys.argv[1]
    
    if len(sys.argv) > 2:
        if sys.argv[2] == 'follow':
            check_cloud_init_logs(vm_name, follow=True)
        elif sys.argv[2] == 'progress':
            check_cloud_init_progress(vm_name)
        else:
            check_cloud_init_logs(vm_name, follow=False)
    else:
        check_cloud_init_logs(vm_name, follow=False)

if __name__ == "__main__":
    main()
