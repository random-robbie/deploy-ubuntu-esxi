#!/usr/bin/env python3
"""
VM Destruction Script
Safely removes VMs and cleans up associated resources
"""

import sys
import os
import subprocess
import time

# Add project root to path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from modules.config import Config
from modules.logger import Logger

def list_vms_for_deletion(config, logger, env):
    """List all VMs that can be deleted"""
    logger.info("📋 Available VMs for deletion:")
    
    try:
        # List all VMs
        cmd = [config.govc_bin, 'ls', '/*/vm/']
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        all_vms = [line.strip() for line in result.stdout.split('\n') if line.strip()]
        
        if not all_vms:
            logger.warn("No VMs found")
            return []
        
        # Show all VMs with numbers
        vm_list = []
        for i, vm_path in enumerate(all_vms, 1):
            vm_name = vm_path.split('/')[-1]
            
            # Get power state
            try:
                power_cmd = [config.govc_bin, 'vm.info', vm_name]
                power_result = subprocess.run(power_cmd, env=env, capture_output=True, text=True)
                power_state = "unknown"
                for line in power_result.stdout.split('\n'):
                    if 'Power state:' in line:
                        power_state = line.split(':')[1].strip()
                        break
                
                print(f"  {i}. {vm_name} ({power_state})")
                vm_list.append(vm_name)
                
            except Exception as e:
                print(f"  {i}. {vm_name} (error getting state)")
                vm_list.append(vm_name)
        
        return vm_list
        
    except Exception as e:
        logger.error(f"Error listing VMs: {e}")
        return []

def get_vm_info(config, logger, env, vm_name):
    """Get detailed VM information before deletion"""
    logger.info(f"📊 VM Information: {vm_name}")
    
    try:
        # Get VM details
        cmd = [config.govc_bin, 'vm.info', vm_name]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(result.stdout)
            
            # Check for snapshots
            snap_cmd = [config.govc_bin, 'snapshot.tree', '-vm', vm_name]
            snap_result = subprocess.run(snap_cmd, env=env, capture_output=True, text=True)
            
            if snap_result.returncode == 0 and snap_result.stdout.strip():
                logger.warn("⚠️  VM has snapshots:")
                print(snap_result.stdout)
            
            return True
        else:
            logger.error(f"Could not get VM info: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error getting VM info: {e}")
        return False

def confirm_deletion(vm_name):
    """Get user confirmation for deletion"""
    print(f"\n🚨 WARNING: This will PERMANENTLY DELETE VM: {vm_name}")
    print("This action cannot be undone!")
    print("\nThe following will be deleted:")
    print("  - VM configuration")
    print("  - All virtual disks")
    print("  - All snapshots")
    print("  - VM from inventory")
    
    confirmation = input(f"\nType 'DELETE {vm_name}' to confirm: ").strip()
    
    return confirmation == f"DELETE {vm_name}"

def destroy_vm(config, logger, env, vm_name, force=False):
    """Safely destroy a VM and clean up resources"""
    logger.info(f"💥 Destroying VM: {vm_name}")
    
    try:
        # Step 1: Power off VM if running
        logger.info("Step 1: Powering off VM...")
        power_cmd = [config.govc_bin, 'vm.power', '-off', vm_name]
        power_result = subprocess.run(power_cmd, env=env, capture_output=True, text=True)
        
        if power_result.returncode == 0:
            logger.info("✅ VM powered off")
        else:
            logger.info("ℹ️  VM was already powered off or not found")
        
        # Wait a moment for clean shutdown
        time.sleep(3)
        
        # Step 2: Remove all snapshots
        logger.info("Step 2: Removing snapshots...")
        snap_cmd = [config.govc_bin, 'snapshot.remove', '-vm', vm_name, '*']
        snap_result = subprocess.run(snap_cmd, env=env, capture_output=True, text=True)
        
        if snap_result.returncode == 0:
            logger.info("✅ Snapshots removed")
        else:
            logger.info("ℹ️  No snapshots to remove")
        
        # Step 3: Destroy VM
        logger.info("Step 3: Destroying VM...")
        destroy_cmd = [config.govc_bin, 'vm.destroy', vm_name]
        destroy_result = subprocess.run(destroy_cmd, env=env, capture_output=True, text=True)
        
        if destroy_result.returncode == 0:
            logger.info("✅ VM destroyed successfully")
            
            # Step 4: Clean up any remaining files
            logger.info("Step 4: Cleaning up...")
            
            # Try to clean up any cloud-init ISOs with the VM name
            work_dir = config.work_dir
            if os.path.exists(work_dir):
                for file in os.listdir(work_dir):
                    if vm_name in file and file.endswith('.iso'):
                        try:
                            os.remove(os.path.join(work_dir, file))
                            logger.info(f"🗑️  Removed: {file}")
                        except Exception as e:
                            logger.warn(f"Could not remove {file}: {e}")
            
            logger.info(f"🎉 VM '{vm_name}' completely destroyed!")
            return True
            
        else:
            logger.error(f"Failed to destroy VM: {destroy_result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error destroying VM: {e}")
        return False

def destroy_multiple_vms(config, logger, env, pattern=None):
    """Destroy multiple VMs matching a pattern"""
    logger.info(f"🔍 Finding VMs to destroy{f' matching pattern: {pattern}' if pattern else ''}...")
    
    try:
        cmd = [config.govc_bin, 'ls', '/*/vm/']
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        all_vms = [line.strip().split('/')[-1] for line in result.stdout.split('\n') if line.strip()]
        
        if pattern:
            matching_vms = [vm for vm in all_vms if pattern in vm]
        else:
            matching_vms = all_vms
        
        if not matching_vms:
            logger.info("No matching VMs found")
            return
        
        logger.info(f"Found {len(matching_vms)} VMs to destroy:")
        for vm in matching_vms:
            print(f"  - {vm}")
        
        confirm = input(f"\nDestroy all {len(matching_vms)} VMs? (yes/no): ").strip().lower()
        
        if confirm == 'yes':
            destroyed = 0
            for vm in matching_vms:
                logger.info(f"\n--- Destroying {vm} ---")
                if destroy_vm(config, logger, env, vm, force=True):
                    destroyed += 1
                else:
                    logger.error(f"Failed to destroy {vm}")
            
            logger.info(f"\n✅ Destroyed {destroyed}/{len(matching_vms)} VMs")
        else:
            logger.info("Operation cancelled")
            
    except Exception as e:
        logger.error(f"Error in bulk destruction: {e}")

def main():
    config = Config()
    logger = Logger()
    
    # Set up environment
    env = os.environ.copy()
    env['GOVC_URL'] = f"https://{config.esxi_user}:{config.esxi_password}@{config.esxi_host}/sdk"
    env['GOVC_INSECURE'] = '1'
    
    if len(sys.argv) == 1:
        # Interactive mode
        logger.info("🗑️  VM Destruction Tool")
        print("=" * 50)
        
        vm_list = list_vms_for_deletion(config, logger, env)
        
        if not vm_list:
            return
        
        print("\nOptions:")
        print("0. Exit")
        print("Enter VM number to destroy specific VM")
        print("Type 'pattern:<text>' to destroy VMs matching pattern")
        print("Type 'all' to destroy ALL VMs (dangerous!)")
        
        choice = input("\nSelect option: ").strip()
        
        if choice == '0':
            logger.info("Exiting...")
            return
        elif choice == 'all':
            logger.warn("⚠️  WARNING: This will destroy ALL VMs!")
            final_confirm = input("Type 'DESTROY ALL VMs' to confirm: ").strip()
            if final_confirm == "DESTROY ALL VMs":
                destroy_multiple_vms(config, logger, env)
            else:
                logger.info("Cancelled")
        elif choice.startswith('pattern:'):
            pattern = choice[8:].strip()
            if pattern:
                destroy_multiple_vms(config, logger, env, pattern)
            else:
                logger.error("No pattern specified")
        else:
            try:
                vm_idx = int(choice) - 1
                if 0 <= vm_idx < len(vm_list):
                    vm_name = vm_list[vm_idx]
                    
                    # Show VM info
                    get_vm_info(config, logger, env, vm_name)
                    
                    # Confirm deletion
                    if confirm_deletion(vm_name):
                        destroy_vm(config, logger, env, vm_name)
                    else:
                        logger.info("Deletion cancelled")
                else:
                    logger.error("Invalid VM number")
            except ValueError:
                logger.error("Invalid choice")
    
    else:
        # Command line mode
        if len(sys.argv) < 2:
            print("Usage:")
            print("  python3 destroy_vm.py                    # Interactive mode")
            print("  python3 destroy_vm.py <vm-name>          # Destroy specific VM")
            print("  python3 destroy_vm.py --pattern <text>   # Destroy VMs matching pattern")
            print("  python3 destroy_vm.py --list             # List VMs only")
            print("")
            print("Examples:")
            print("  python3 destroy_vm.py ubuntu-pentest-20250704-102906")
            print("  python3 destroy_vm.py --pattern ubuntu-pentest")
            print("  python3 destroy_vm.py --list")
            sys.exit(1)
        
        if sys.argv[1] == '--list':
            list_vms_for_deletion(config, logger, env)
        elif sys.argv[1] == '--pattern':
            if len(sys.argv) > 2:
                pattern = sys.argv[2]
                destroy_multiple_vms(config, logger, env, pattern)
            else:
                logger.error("Pattern not specified")
        else:
            vm_name = sys.argv[1]
            
            # Show VM info
            if get_vm_info(config, logger, env, vm_name):
                # Confirm deletion
                if confirm_deletion(vm_name):
                    destroy_vm(config, logger, env, vm_name)
                else:
                    logger.info("Deletion cancelled")

if __name__ == "__main__":
    main()
