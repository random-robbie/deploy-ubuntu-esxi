#!/usr/bin/env python3
"""
Docker Installation Troubleshooter
Diagnoses and fixes Docker installation issues
"""

import sys
import subprocess
import time

def troubleshoot_docker(vm_ip):
    """Troubleshoot Docker installation on VM"""
    print(f"🔧 Troubleshooting Docker on {vm_ip}...")
    
    issues_found = []
    fixes_applied = []
    
    try:
        # Test SSH first
        ssh_test = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', 'echo "SSH OK"'
        ], capture_output=True, text=True, timeout=5)
        
        if ssh_test.returncode != 0:
            print("❌ SSH connection failed")
            return
        
        print("✅ SSH connection working")
        
        # Check if Docker is installed
        print("\n1. Checking Docker installation...")
        docker_check = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', 'which docker'
        ], capture_output=True, text=True, timeout=10)
        
        if docker_check.returncode != 0:
            print("❌ Docker not installed")
            issues_found.append("Docker not installed")
            
            # Try to install Docker
            print("   Attempting to install Docker...")
            install_cmd = subprocess.run([
                'ssh', 
                '-o', 'ConnectTimeout=3',
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                f'ubuntu@{vm_ip}', 'curl -fsSL https://get.docker.com | sudo bash'
            ], timeout=300)  # 5 minutes for installation
            
            if install_cmd.returncode == 0:
                print("✅ Docker installation completed")
                fixes_applied.append("Installed Docker")
            else:
                print("❌ Docker installation failed")
                return
        else:
            print("✅ Docker is installed")
        
        # Check Docker version
        print("\n2. Checking Docker version...")
        version_cmd = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', 'docker --version'
        ], capture_output=True, text=True, timeout=10)
        
        if version_cmd.returncode == 0:
            print(f"✅ Docker version: {version_cmd.stdout.strip()}")
        else:
            print("⚠️  Could not get Docker version")
        
        # Check Docker service
        print("\n3. Checking Docker service...")
        service_cmd = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',\n            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', 'sudo systemctl is-active docker'
        ], capture_output=True, text=True, timeout=10)
        
        if service_cmd.returncode == 0:
            print(f"✅ Docker service: {service_cmd.stdout.strip()}")
        else:
            print("❌ Docker service not running")
            issues_found.append("Docker service not running")
            
            # Try to start Docker
            print("   Starting Docker service...")
            start_cmd = subprocess.run([
                'ssh', 
                '-o', 'ConnectTimeout=3',
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                f'ubuntu@{vm_ip}', 'sudo systemctl start docker && sudo systemctl enable docker'
            ], timeout=30)
            
            if start_cmd.returncode == 0:
                print("✅ Docker service started")
                fixes_applied.append("Started Docker service")
            else:
                print("❌ Failed to start Docker service")
        
        # Check user permissions
        print("\n4. Checking user permissions...")
        groups_cmd = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', 'groups ubuntu'
        ], capture_output=True, text=True, timeout=10)
        
        if 'docker' in groups_cmd.stdout:
            print("✅ User is in docker group")
        else:
            print("❌ User not in docker group")
            issues_found.append("User not in docker group")
            
            # Add user to docker group
            print("   Adding user to docker group...")
            usermod_cmd = subprocess.run([
                'ssh', 
                '-o', 'ConnectTimeout=3',
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                f'ubuntu@{vm_ip}', 'sudo usermod -aG docker ubuntu'
            ], timeout=10)
            
            if usermod_cmd.returncode == 0:
                print("✅ User added to docker group")
                fixes_applied.append("Added user to docker group")
                print("⚠️  User needs to logout/login for group changes to take effect")
            else:
                print("❌ Failed to add user to docker group")
        
        # Test Docker functionality
        print("\n5. Testing Docker functionality...")
        docker_test = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', 'sudo docker ps'
        ], capture_output=True, text=True, timeout=15)
        
        if docker_test.returncode == 0:
            print("✅ Docker is working with sudo")
        else:
            print("❌ Docker not working even with sudo")
            issues_found.append("Docker not functional")
        
        # Check for rootless setup script
        print("\n6. Checking rootless setup...")
        rootless_check = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', 'ls -la ~/setup-docker-rootless.sh'
        ], capture_output=True, text=True, timeout=10)
        
        if rootless_check.returncode == 0:
            print("✅ Rootless setup script available")
        else:
            print("⚠️  Rootless setup script not found")
            print("   This VM may need to be redeployed with latest configuration")
        
        # Summary
        print(f"\n📊 Troubleshooting Summary:")
        print(f"   Issues found: {len(issues_found)}")
        print(f"   Fixes applied: {len(fixes_applied)}")
        
        if issues_found:
            print("\n❌ Issues found:")
            for issue in issues_found:
                print(f"   - {issue}")
        
        if fixes_applied:
            print("\n✅ Fixes applied:")
            for fix in fixes_applied:
                print(f"   - {fix}")
        
        if not issues_found:
            print("\n🎉 No issues found - Docker appears to be working!")
        elif fixes_applied:
            print("\n🔧 Some issues were fixed. Try running Docker again.")
            print(f"   ssh ubuntu@{vm_ip}")
            print("   docker ps")
        
    except subprocess.TimeoutExpired:
        print("❌ Operation timed out")
    except Exception as e:
        print(f"❌ Error during troubleshooting: {e}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 troubleshoot_docker.py <vm-ip>")
        print("Example: python3 troubleshoot_docker.py 192.168.1.170")
        sys.exit(1)
    
    vm_ip = sys.argv[1]
    troubleshoot_docker(vm_ip)

if __name__ == "__main__":
    main()
