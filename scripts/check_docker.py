#!/usr/bin/env python3
"""
Docker Installation Checker
Verifies Docker installation and provides rootless setup
"""

import sys
import subprocess
import os

def check_docker_installation(vm_ip):
    """Check Docker installation status on VM"""
    print(f"🐳 Checking Docker installation on {vm_ip}...")
    
    try:
        # Test SSH connection first
        ssh_test = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'ConnectionAttempts=1',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', 'echo "SSH OK"'
        ], capture_output=True, text=True, timeout=5)
        
        if ssh_test.returncode != 0:
            print("❌ SSH connection failed")
            return False
        
        print("✅ SSH connection successful")
        
        # Check if Docker is installed
        docker_check = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', 'docker --version'
        ], capture_output=True, text=True, timeout=10)
        
        if docker_check.returncode == 0:
            print(f"✅ Docker installed: {docker_check.stdout.strip()}")
        else:
            print("❌ Docker not installed or not working")
            return False
        
        # Check Docker service status
        service_check = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', 'systemctl is-active docker'
        ], capture_output=True, text=True, timeout=10)
        
        if service_check.returncode == 0:
            print(f"✅ Docker service: {service_check.stdout.strip()}")
        else:
            print("⚠️  Docker service not running")
        
        # Check if user can run Docker
        user_check = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', 'docker ps'
        ], capture_output=True, text=True, timeout=10)
        
        if user_check.returncode == 0:
            print("✅ User can run Docker commands")
        else:
            print("⚠️  User cannot run Docker (may need logout/login or rootless setup)")
        
        # Check if rootless setup script exists
        rootless_check = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', 'ls -la ~/setup-docker-rootless.sh'
        ], capture_output=True, text=True, timeout=10)
        
        if rootless_check.returncode == 0:
            print("✅ Rootless Docker setup script available")
            print("   Run: ssh ubuntu@{} './setup-docker-rootless.sh'".format(vm_ip))
        else:
            print("ℹ️  Rootless setup script not found")
        
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ Connection timeout")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def setup_rootless_docker(vm_ip):
    """Run the rootless Docker setup on the VM"""
    print(f"🔧 Setting up rootless Docker on {vm_ip}...")
    
    try:
        # First, check if the setup script exists
        check_script = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', 'ls -la ~/setup-docker-rootless.sh'
        ], capture_output=True, text=True, timeout=10)
        
        if check_script.returncode != 0:
            print("❌ Rootless setup script not found")
            print("This VM may not have been deployed with the latest configuration")
            return
        
        print("✅ Rootless setup script found")
        print("Running rootless Docker setup (this may take a minute)...")
        
        # Run the rootless setup script
        setup_cmd = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', './setup-docker-rootless.sh'
        ], timeout=120)  # Allow 2 minutes for setup
        
        if setup_cmd.returncode == 0:
            print("✅ Rootless Docker setup completed")
            print("\n🚀 Testing rootless Docker...")
            
            # Test rootless Docker
            test_cmd = subprocess.run([
                'ssh', 
                '-o', 'ConnectTimeout=3',
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                f'ubuntu@{vm_ip}', 'source ~/.bashrc && docker ps'
            ], capture_output=True, text=True, timeout=30)
            
            if test_cmd.returncode == 0:
                print("✅ Rootless Docker is working!")
                print(f"🚀 Connect: ssh ubuntu@{vm_ip}")
                print("Then run: docker ps")
            else:
                print("⚠️  Rootless Docker setup completed but test failed")
                print("Try logging out and back in, then run: docker ps")
        else:
            print("❌ Rootless setup failed")
            print("Check the VM manually for error details")
            
    except subprocess.TimeoutExpired:
        print("❌ Setup timeout (this can happen if setup takes longer than expected)")
        print("Setup may still be running - check manually")
    except Exception as e:
        print(f"❌ Setup error: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 check_docker.py <vm-ip>           - Check Docker installation")
        print("  python3 check_docker.py <vm-ip> setup     - Setup rootless Docker")
        print("")
        print("Examples:")
        print("  python3 check_docker.py 192.168.1.170")
        print("  python3 check_docker.py 192.168.1.170 setup")
        sys.exit(1)
    
    vm_ip = sys.argv[1]
    
    if len(sys.argv) > 2 and sys.argv[2] == 'setup':
        setup_rootless_docker(vm_ip)
    else:
        check_docker_installation(vm_ip)

if __name__ == "__main__":
    main()
