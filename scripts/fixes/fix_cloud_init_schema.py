#!/usr/bin/env python3
"""
Fix cloud-init schema validation issues on deployed VMs
This script will fix the datasource_list issue on already deployed VMs
"""

import sys
import subprocess

def fix_cloud_init_schema(vm_ip):
    """Fix cloud-init schema validation errors on a deployed VM"""
    print(f"🔧 Fixing cloud-init schema issues on {vm_ip}...")
    
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
            return False
        
        print("✅ SSH connection working")
        
        # Check current schema validation status
        print("\n1. Checking current cloud-init schema status:")
        schema_check = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', 'sudo cloud-init schema --system'
        ], capture_output=True, text=True, timeout=15)
        
        print(schema_check.stdout)
        if schema_check.stderr:
            print("Schema errors found:")
            print(schema_check.stderr)
        
        # Find and backup the problematic cloud-config file
        print("\n2. Backing up current cloud-config...")
        backup_cmd = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', 
            'sudo cp /var/lib/cloud/instances/*/cloud-config.txt /var/lib/cloud/instances/*/cloud-config.txt.backup 2>/dev/null || echo "No cloud-config.txt found"'
        ], capture_output=True, text=True, timeout=10)
        
        if backup_cmd.returncode == 0:
            print("✅ Backup created")
        
        # Remove datasource_list from user-data
        print("\n3. Fixing cloud-config user-data...")
        fix_cmd = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', 
            '''sudo find /var/lib/cloud/instances/ -name "cloud-config.txt" -exec sed -i '/^datasource_list:/d' {} \; 2>/dev/null || echo "No changes needed"'''
        ], capture_output=True, text=True, timeout=10)
        
        if fix_cmd.returncode == 0:
            print("✅ Removed datasource_list from user-data")
        
        # Clean and reinitialize cloud-init
        print("\n4. Cleaning and reinitializing cloud-init...")
        clean_cmd = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', 
            'sudo cloud-init clean --logs'
        ], capture_output=True, text=True, timeout=15)
        
        if clean_cmd.returncode == 0:
            print("✅ Cloud-init cleaned")
        
        # Verify schema is now valid
        print("\n5. Verifying fixed schema:")
        final_check = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', 'sudo cloud-init schema --system'
        ], capture_output=True, text=True, timeout=15)
        
        print(final_check.stdout)
        if final_check.returncode == 0 and "Valid schema" in final_check.stdout:
            print("✅ Schema validation successful!")
            
            # Try to complete any pending installations
            print("\n6. Attempting to complete installations...")
            install_cmd = subprocess.run([
                'ssh', 
                '-o', 'ConnectTimeout=3',
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                f'ubuntu@{vm_ip}', 
                'sudo cloud-init modules --mode=config && sudo cloud-init modules --mode=final'
            ], timeout=300)
            
            if install_cmd.returncode == 0:
                print("✅ Cloud-init modules completed")
            else:
                print("⚠️  Cloud-init modules may need manual completion")
                
        else:
            print("❌ Schema validation still failing")
            
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ Operation timed out")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 fix_cloud_init_schema.py <vm-ip>")
        print("")
        print("Examples:")
        print("  python3 fix_cloud_init_schema.py 192.168.1.189")
        sys.exit(1)
    
    vm_ip = sys.argv[1]
    fix_cloud_init_schema(vm_ip)

if __name__ == "__main__":
    main()
