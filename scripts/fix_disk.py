#!/usr/bin/env python3
"""
Disk Expansion Checker and Fixer
Diagnoses and fixes disk expansion issues on VMs
"""

import sys
import subprocess

def check_disk_usage(vm_ip):
    """Check current disk usage and partition layout"""
    print(f"💾 Checking disk usage on {vm_ip}...")
    
    try:
        # Test SSH connection
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
        
        # Check disk usage
        print("\n1. Current disk usage:")
        df_cmd = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', 'df -h /'
        ], capture_output=True, text=True, timeout=10)
        
        if df_cmd.returncode == 0:
            print(df_cmd.stdout)
        else:
            print("❌ Could not get disk usage")
            return False
        
        # Check physical disk size
        print("\n2. Physical disk information:")
        lsblk_cmd = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', 'lsblk'
        ], capture_output=True, text=True, timeout=10)
        
        if lsblk_cmd.returncode == 0:
            print(lsblk_cmd.stdout)
        else:
            print("❌ Could not get block device info")
        
        # Check partition table
        print("\n3. Partition information:")
        fdisk_cmd = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', 'sudo fdisk -l /dev/sda'
        ], capture_output=True, text=True, timeout=10)
        
        if fdisk_cmd.returncode == 0:
            print(fdisk_cmd.stdout)
        else:
            print("⚠️  Could not get partition info (may not be /dev/sda)")
        
        # Check if cloud-init disk resize is enabled
        print("\n4. Cloud-init growpart status:")
        growpart_cmd = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', 'sudo cloud-init status --long 2>/dev/null || echo "cloud-init not available"'
        ], capture_output=True, text=True, timeout=10)
        
        if growpart_cmd.returncode == 0:
            print(growpart_cmd.stdout.strip())
        
        # Check filesystem type
        print("\n5. Filesystem information:")
        mount_cmd = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', 'mount | grep "on / "'
        ], capture_output=True, text=True, timeout=10)
        
        if mount_cmd.returncode == 0:
            print(mount_cmd.stdout.strip())
        
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ Connection timeout")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def fix_disk_expansion(vm_ip):
    """Attempt to fix disk expansion"""
    print(f"\n🔧 Attempting to fix disk expansion on {vm_ip}...")
    
    try:
        # Step 1: Check if growpart is available
        print("Step 1: Checking for growpart utility...")
        growpart_check = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', 'which growpart'
        ], capture_output=True, text=True, timeout=10)
        
        if growpart_check.returncode != 0:
            print("   Installing cloud-guest-utils...")
            install_cmd = subprocess.run([
                'ssh', 
                '-o', 'ConnectTimeout=3',
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                f'ubuntu@{vm_ip}', 'sudo apt-get update && sudo apt-get install -y cloud-guest-utils'
            ], timeout=120)
            
            if install_cmd.returncode == 0:
                print("   ✅ cloud-guest-utils installed")
            else:
                print("   ❌ Failed to install cloud-guest-utils")
                return False
        else:
            print("   ✅ growpart is available")
        
        # Step 2: Identify the root partition
        print("\nStep 2: Identifying root partition...")
        root_partition_cmd = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', 'df / | tail -1 | awk \'{print $1}\''
        ], capture_output=True, text=True, timeout=10)
        
        if root_partition_cmd.returncode == 0:
            root_partition = root_partition_cmd.stdout.strip()
            print(f"   Root partition: {root_partition}")
            
            # Extract disk and partition number
            if '/dev/sda' in root_partition:
                disk = '/dev/sda'
                partition_num = root_partition.replace('/dev/sda', '')
            elif '/dev/vda' in root_partition:
                disk = '/dev/vda'
                partition_num = root_partition.replace('/dev/vda', '')
            else:
                print(f"   ⚠️  Unexpected partition format: {root_partition}")
                disk = '/dev/sda'  # Assume sda
                partition_num = '1'  # Assume partition 1
            
            print(f"   Disk: {disk}, Partition: {partition_num}")
        else:
            print("   ⚠️  Could not identify root partition, assuming /dev/sda1")
            disk = '/dev/sda'
            partition_num = '1'
        
        # Step 3: Grow the partition
        print(f"\nStep 3: Growing partition {disk}{partition_num}...")
        growpart_cmd = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', f'sudo growpart {disk} {partition_num}'
        ], capture_output=True, text=True, timeout=30)
        
        if growpart_cmd.returncode == 0:
            print("   ✅ Partition grown successfully")
        else:
            print(f"   ⚠️  Growpart result: {growpart_cmd.stderr.strip()}")
            if "NOCHANGE" in growpart_cmd.stderr:
                print("   ℹ️  Partition is already at maximum size")
        
        # Step 4: Resize the filesystem
        print("\nStep 4: Resizing filesystem...")
        resize_cmd = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', 'sudo resize2fs /dev/sda1 2>/dev/null || sudo xfs_growfs / 2>/dev/null || echo "Filesystem resize may have failed"'
        ], capture_output=True, text=True, timeout=60)
        
        if resize_cmd.returncode == 0:
            print("   ✅ Filesystem resized")
        else:
            print(f"   ⚠️  Filesystem resize result: {resize_cmd.stdout.strip()}")
        
        # Step 5: Check result
        print("\nStep 5: Checking final disk usage...")
        final_check = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', 'df -h /'
        ], capture_output=True, text=True, timeout=10)
        
        if final_check.returncode == 0:
            print(final_check.stdout)
            print("🎉 Disk expansion process completed!")
        else:
            print("❌ Could not verify final disk usage")
        
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ Operation timed out")
        return False
    except Exception as e:
        print(f"❌ Error during fix: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 fix_disk.py <vm-ip>           - Check disk usage")
        print("  python3 fix_disk.py <vm-ip> fix       - Fix disk expansion")
        print("")
        print("Examples:")
        print("  python3 fix_disk.py 192.168.1.170")
        print("  python3 fix_disk.py 192.168.1.170 fix")
        sys.exit(1)
    
    vm_ip = sys.argv[1]
    
    if len(sys.argv) > 2 and sys.argv[2] == 'fix':
        # Check first, then fix
        if check_disk_usage(vm_ip):
            fix_disk_expansion(vm_ip)
    else:
        check_disk_usage(vm_ip)

if __name__ == "__main__":
    main()
