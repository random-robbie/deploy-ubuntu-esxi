#!/usr/bin/env python3
"""
Cloud-Init Installation Troubleshooter
Debug Docker and Go installation issues
"""

import sys
import subprocess

def check_cloud_init_status(vm_ip):
    """Check cloud-init status and installation issues"""
    print(f"🔍 Troubleshooting cloud-init installations on {vm_ip}...")
    
    try:
        # Test SSH connection first
        ssh_test = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', 'echo "SSH OK"'
        ], capture_output=True, text=True, timeout=5)
        
        if ssh_test.returncode != 0:
            print("❌ SSH connection failed")
            print("Check VM IP and network connectivity")
            return False
        
        print("✅ SSH connection working")
        
        # Check cloud-init status
        print("\n1. Cloud-init status:")
        status_cmd = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', 'sudo cloud-init status --long'
        ], capture_output=True, text=True, timeout=10)
        
        if status_cmd.returncode == 0:
            print(status_cmd.stdout)
        else:
            print("Could not get cloud-init status")
        
        # Check cloud-init logs
        print("\n2. Cloud-init output log (last 50 lines):")
        log_cmd = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', 'sudo tail -50 /var/log/cloud-init-output.log'
        ], capture_output=True, text=True, timeout=15)
        
        if log_cmd.returncode == 0:
            print(log_cmd.stdout)
        else:
            print("Could not read cloud-init logs")
        
        # Check if Docker is installed
        print("\n3. Docker installation check:")
        docker_cmd = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', 'which docker && docker --version || echo "Docker not found"'
        ], capture_output=True, text=True, timeout=10)
        
        if docker_cmd.returncode == 0:
            print(docker_cmd.stdout)
        
        # Check if Go is installed
        print("\n4. Go installation check:")
        go_cmd = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', 'ls -la /usr/local/go/bin/go && /usr/local/go/bin/go version || echo "Go not found"'
        ], capture_output=True, text=True, timeout=10)
        
        if go_cmd.returncode == 0:
            print(go_cmd.stdout)
        
        # Check for any installation errors in logs
        print("\n5. Looking for installation errors:")
        error_cmd = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', 'sudo grep -i -A5 -B5 "error\\|fail" /var/log/cloud-init-output.log | tail -20'
        ], capture_output=True, text=True, timeout=10)
        
        if error_cmd.returncode == 0 and error_cmd.stdout.strip():
            print("Errors found in cloud-init logs:")
            print(error_cmd.stdout)
        else:
            print("No obvious errors found in logs")
        
        # Check if installations are still running
        print("\n6. Checking for running installations:")
        process_cmd = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', 'ps aux | grep -E "(apt|docker|wget|curl)" | grep -v grep || echo "No installation processes running"'
        ], capture_output=True, text=True, timeout=10)
        
        if process_cmd.returncode == 0:
            print(process_cmd.stdout)
        
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ Connection timeout")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def manual_install_missing(vm_ip):
    """Manually install missing Docker and Go"""
    print(f"\n🔧 Attempting manual installation on {vm_ip}...")
    
    try:
        # Install Docker
        print("Installing Docker...")
        docker_install = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', 'curl -fsSL https://get.docker.com | sudo bash && sudo usermod -aG docker ubuntu'
        ], timeout=300)
        
        if docker_install.returncode == 0:
            print("✅ Docker installation completed")
        else:
            print("❌ Docker installation failed")
        
        # Install Go
        print("Installing Go...")
        go_install_cmd = '''
            sudo wget -c https://golang.org/dl/go1.24.4.linux-amd64.tar.gz -O - | sudo tar -xz -C /usr/local &&
            echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc &&
            sudo mkdir -p /home/ubuntu/go/{bin,src,pkg} &&
            sudo chown -R ubuntu:ubuntu /home/ubuntu/go &&
            echo 'export GOPATH=/home/ubuntu/go' >> ~/.bashrc &&
            echo 'export PATH=$PATH:$GOPATH/bin' >> ~/.bashrc
        '''
        
        go_install = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', go_install_cmd
        ], timeout=180)
        
        if go_install.returncode == 0:
            print("✅ Go installation completed")
        else:
            print("❌ Go installation failed")
        
        print("Manual installation completed. Logout and login to refresh environment.")
        
    except subprocess.TimeoutExpired:
        print("❌ Manual installation timed out")
    except Exception as e:
        print(f"❌ Manual installation error: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 troubleshoot_installations.py <vm-ip>           - Check installations")
        print("  python3 troubleshoot_installations.py <vm-ip> fix       - Manual install missing")
        print("")
        print("Examples:")
        print("  python3 troubleshoot_installations.py 192.168.1.189")
        print("  python3 troubleshoot_installations.py 192.168.1.189 fix")
        sys.exit(1)
    
    vm_ip = sys.argv[1]
    
    if len(sys.argv) > 2 and sys.argv[2] == 'fix':
        # Check first, then fix
        if check_cloud_init_status(vm_ip):
            manual_install_missing(vm_ip)
    else:
        check_cloud_init_status(vm_ip)

if __name__ == "__main__":
    main()
