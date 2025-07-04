#!/usr/bin/env python3
"""
Post-deployment validation script
Automatically validates VM after deployment completes
"""

import sys
import os
import subprocess
import time

def wait_for_vm_ready(vm_ip, max_wait=300):
    """Wait for VM to be ready for validation"""
    print(f"⏳ Waiting for VM {vm_ip} to be ready for validation...")
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            result = subprocess.run([
                'ssh', '-o', 'ConnectTimeout=3',
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                f'ubuntu@{vm_ip}', 'echo "ready"'
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                print(f"✅ VM {vm_ip} is ready for validation")
                return True
                
        except subprocess.TimeoutExpired:
            pass
        except Exception:
            pass
            
        print(".", end="", flush=True)
        time.sleep(10)
    
    print(f"\n❌ VM {vm_ip} did not become ready within {max_wait} seconds")
    return False

def run_post_deployment_validation(vm_ip):
    """Run full deployment validation"""
    print(f"🔍 Running post-deployment validation for {vm_ip}...")
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    validator_path = os.path.join(script_dir, 'validator.py')
    
    try:
        result = subprocess.run([
            'python3', validator_path, 'deploy', vm_ip
        ], capture_output=False, timeout=120)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Post-deployment validation timed out")
        return False
    except Exception as e:
        print(f"❌ Post-deployment validation error: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 post_deploy_check.py <vm-ip> [wait-time]")
        print("Example: python3 post_deploy_check.py 192.168.1.190 600")
        sys.exit(1)
    
    vm_ip = sys.argv[1]
    max_wait = int(sys.argv[2]) if len(sys.argv) > 2 else 300
    
    print(f"🚀 Post-deployment validation for VM: {vm_ip}")
    print("=" * 50)
    
    # Wait for VM to be ready
    if not wait_for_vm_ready(vm_ip, max_wait):
        sys.exit(1)
    
    # Wait a bit more for cloud-init to complete
    print("⏳ Waiting additional 60 seconds for cloud-init to complete...")
    time.sleep(60)
    
    # Run validation
    success = run_post_deployment_validation(vm_ip)
    
    print("\n" + "=" * 50)
    if success:
        print("✅ POST-DEPLOYMENT VALIDATION PASSED")
        print(f"VM {vm_ip} is ready for use!")
    else:
        print("❌ POST-DEPLOYMENT VALIDATION FAILED")
        print(f"VM {vm_ip} may have issues - check the output above")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
