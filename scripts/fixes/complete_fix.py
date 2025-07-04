#!/usr/bin/env python3
"""
Complete fix for cloud-init datasource_list schema issue
This script will:
1. Verify the fix has been applied to your deployment scripts
2. Help you deploy a new VM with corrected configuration
3. Optionally help cleanup the broken VM
"""

import sys
import subprocess
import os

def check_fixed_cloudinit_script():
    """Check if the cloud-init script has been fixed"""
    print("🔍 Checking if cloud-init script has been fixed...")
    
    script_path = "/Users/rwiggins/tools/newubuntu/modules/cloudinit.py"
    
    if not os.path.exists(script_path):
        print(f"❌ Could not find {script_path}")
        return False
    
    with open(script_path, 'r') as f:
        content = f.read()
    
    if 'datasource_list: ["NoCloud", "None"]' in content:
        print("❌ The problematic datasource_list is still in the cloud-init script!")
        print("   Run this command to fix it:")
        print("   sed -i '' '/datasource_list:/d' /Users/rwiggins/tools/newubuntu/modules/cloudinit.py")
        return False
    else:
        print("✅ Cloud-init script has been fixed - no datasource_list in user-data")
        return True

def deploy_new_vm():
    """Deploy a new VM with corrected configuration"""
    print("\n🚀 Deploying new VM with corrected cloud-init configuration...")
    
    # Change to the newubuntu directory
    os.chdir("/Users/rwiggins/tools/newubuntu")
    
    try:
        # Run the deployment script
        result = subprocess.run([
            'python3', 'deploy.py'
        ], capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            print("✅ New VM deployment initiated successfully!")
            print("Output:")
            print(result.stdout)
            
            # Extract VM IP if possible
            lines = result.stdout.split('\n')
            for line in lines:
                if 'IP:' in line or '192.168.' in line:
                    print(f"🎯 VM Details: {line}")
        else:
            print("❌ VM deployment failed!")
            print("Error:")
            print(result.stderr)
            print("Output:")
            print(result.stdout)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ VM deployment timed out")
        return False
    except Exception as e:
        print(f"❌ VM deployment error: {e}")
        return False

def cleanup_broken_vm(vm_ip):
    """Optionally cleanup the broken VM"""
    print(f"\n🗑️  Cleaning up broken VM at {vm_ip}...")
    
    try:
        # Use the destroy script if available
        result = subprocess.run([
            'python3', 'scripts/destroy_vm.py', vm_ip
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ Broken VM cleaned up successfully")
        else:
            print("⚠️  VM cleanup may have failed - check manually")
            print(result.stderr)
        
    except Exception as e:
        print(f"⚠️  Could not cleanup VM automatically: {e}")
        print("You may need to cleanup manually through your hypervisor")

def test_new_vm(vm_ip):
    """Test the new VM installation"""
    print(f"\n🧪 Testing new VM at {vm_ip}...")
    
    try:
        # Wait a bit for the VM to fully boot
        print("Waiting 30 seconds for VM to complete setup...")
        subprocess.run(['sleep', '30'])
        
        # Test with the troubleshooting script
        result = subprocess.run([
            'python3', 'scripts/troubleshoot_installations.py', vm_ip
        ], capture_output=True, text=True, timeout=60)
        
        print("Test results:")
        print(result.stdout)
        
        if "Docker not found" not in result.stdout and "Go not found" not in result.stdout:
            print("✅ New VM appears to be working correctly!")
            return True
        else:
            print("⚠️  New VM may still have issues - check the output above")
            return False
        
    except Exception as e:
        print(f"⚠️  Could not test new VM: {e}")
        return False

def main():
    print("🔧 Cloud-Init Complete Fix Script")
    print("=" * 50)
    
    # Check if script is fixed
    if not check_fixed_cloudinit_script():
        print("\n❌ Please fix the cloud-init script first and run this again")
        sys.exit(1)
    
    if len(sys.argv) >= 2:
        action = sys.argv[1].lower()
        
        if action == "deploy":
            # Deploy new VM
            if deploy_new_vm():
                print("\n✅ Deployment completed! Check the output above for VM details.")
                print("Wait a few minutes, then test with:")
                print("python3 scripts/troubleshoot_installations.py <new-vm-ip>")
            
        elif action == "cleanup" and len(sys.argv) >= 3:
            # Cleanup broken VM
            broken_vm_ip = sys.argv[2]
            cleanup_broken_vm(broken_vm_ip)
            
        elif action == "test" and len(sys.argv) >= 3:
            # Test VM
            vm_ip = sys.argv[2]
            test_new_vm(vm_ip)
            
        elif action == "full" and len(sys.argv) >= 3:
            # Full workflow: cleanup broken, deploy new, test
            broken_vm_ip = sys.argv[2]
            print(f"🔄 Full workflow: cleanup {broken_vm_ip}, deploy new, test")
            
            cleanup_broken_vm(broken_vm_ip)
            
            if deploy_new_vm():
                print("\n⏳ Waiting for new VM to be ready...")
                # You'll need to manually get the new VM IP and test
                print("📝 Please note the new VM IP from the deployment output above")
                print("    Then test with: python3 complete_fix.py test <new-vm-ip>")
            
        else:
            print("❌ Invalid action or missing parameters")
            print_usage()
    else:
        print_usage()

def print_usage():
    print("\nUsage:")
    print("  python3 complete_fix.py deploy                     # Deploy new VM")
    print("  python3 complete_fix.py cleanup <broken-vm-ip>     # Cleanup broken VM")
    print("  python3 complete_fix.py test <vm-ip>               # Test VM")
    print("  python3 complete_fix.py full <broken-vm-ip>        # Full workflow")
    print("")
    print("Examples:")
    print("  python3 complete_fix.py deploy")
    print("  python3 complete_fix.py cleanup 192.168.1.189")
    print("  python3 complete_fix.py test 192.168.1.190")
    print("  python3 complete_fix.py full 192.168.1.189")

if __name__ == "__main__":
    main()
