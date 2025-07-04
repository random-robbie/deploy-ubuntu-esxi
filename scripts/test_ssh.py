#!/usr/bin/env python3
"""
Test SSH connectivity with the new timeout settings
"""

import sys
import subprocess
import time

def test_ssh_connectivity(vm_ip):
    """Test SSH connection with same settings as monitor.py"""
    print(f"Testing SSH to {vm_ip}...")
    
    try:
        # Test SSH connectivity with short timeout
        ssh_test = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'ConnectionAttempts=1',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'BatchMode=yes',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', 'echo "SSH ready"'
        ], capture_output=True, text=True, timeout=5)
        
        if ssh_test.returncode == 0:
            print("✅ SSH connection successful")
            
            # Test cloud-init status
            print("Testing cloud-init status...")
            status_cmd = subprocess.run([
                'ssh',
                '-o', 'ConnectTimeout=3',
                '-o', 'ConnectionAttempts=1', 
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                f'ubuntu@{vm_ip}', 'sudo cloud-init status 2>/dev/null || echo "cloud-init not available"'
            ], capture_output=True, text=True, timeout=10)
            
            if status_cmd.returncode == 0:
                status_output = status_cmd.stdout.strip()
                if "not available" in status_output:
                    print("ℹ️  Cloud-init not installed or not available")
                else:
                    print(f"✅ Cloud-init status: {status_output}")
            else:
                print(f"⚠️  Cloud-init status failed: {status_cmd.stderr.strip()}")
                
            # Test basic system info
            print("Testing basic system access...")
            info_cmd = subprocess.run([
                'ssh',
                '-o', 'ConnectTimeout=3',
                '-o', 'ConnectionAttempts=1', 
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                f'ubuntu@{vm_ip}', 'uname -a && whoami'
            ], capture_output=True, text=True, timeout=10)
            
            if info_cmd.returncode == 0:
                print(f"✅ System info: {info_cmd.stdout.strip()}")
            else:
                print(f"⚠️  System info failed: {info_cmd.stderr.strip()}")
                
        else:
            print(f"❌ SSH connection failed: {ssh_test.stderr.strip()}")
            
    except subprocess.TimeoutExpired:
        print("❌ SSH connection timed out")
    except Exception as e:
        print(f"❌ SSH error: {e}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 test_ssh.py <vm-ip>")
        sys.exit(1)
    
    vm_ip = sys.argv[1]
    test_ssh_connectivity(vm_ip)

if __name__ == "__main__":
    main()
