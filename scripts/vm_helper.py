#!/usr/bin/env python3
"""
VM Management Helper Script
Provides easy access to diagnostic and fix scripts
"""

import os
import sys
import subprocess
from pathlib import Path

class VMManager:
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.project_root = self.script_dir.parent
        
    def list_vms(self):
        """List available VMs"""
        print("🔍 Listing VMs...")
        
        # Check if we can run the config module
        try:
            sys.path.append(str(self.project_root))
            from modules.config import Config
            config = Config()
            
            # Set up environment
            env = os.environ.copy()
            env['GOVC_URL'] = f"https://{config.esxi_user}:{config.esxi_password}@{config.esxi_host}/sdk"
            env['GOVC_INSECURE'] = '1'
            
            # List VMs
            cmd = [config.govc_bin, 'ls', '/*/vm/']
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            vms = [line for line in result.stdout.split('\n') if 'ubuntu-pentest' in line]
            
            if vms:
                print("Available VMs:")
                for i, vm in enumerate(vms, 1):
                    vm_name = vm.split('/')[-1]
                    print(f"  {i}. {vm_name}")
                return [vm.split('/')[-1] for vm in vms]
            else:
                print("No ubuntu-pentest VMs found")
                return []
                
        except Exception as e:
            print(f"Error listing VMs: {e}")
            return []
    
    def run_script(self, script_path, vm_name, *args):
        """Run a diagnostic or fix script"""
        script_full_path = self.script_dir / script_path
        
        if not script_full_path.exists():
            print(f"❌ Script not found: {script_path}")
            return False
        
        print(f"🚀 Running: {script_path} {vm_name} {' '.join(args)}")
        
        cmd = ['python3', str(script_full_path), vm_name] + list(args)
        
        try:
            result = subprocess.run(cmd, cwd=str(self.project_root))
            return result.returncode == 0
        except KeyboardInterrupt:
            print("\n⏹️ Script interrupted by user")
            return False
        except Exception as e:
            print(f"❌ Error running script: {e}")
            return False
    
    def show_menu(self):
        """Show interactive menu"""
        while True:
            print("\n" + "="*50)
            print("🛠️  VM MANAGEMENT HELPER")
            print("="*50)
            print("1. List VMs")
            print("2. Quick Status Check")
            print("3. Full VM Diagnostics")
            print("4. Check Cloud-Init Logs")
            print("5. Check Boot Configuration")
            print("6. Network Diagnostics")
            print("7. Fix Network Issues")
            print("8. Fix CD-ROM Issues")
            print("9. Check Docker Installation")
            print("10. Destroy VM")
            print("0. Exit")
            print("-"*50)
            
            choice = input("Select option: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self.list_vms()
            elif choice in ['2', '3', '4', '5', '6', '7', '8', '9', '10']:
                self.handle_vm_operation(choice)
            else:
                print("❌ Invalid choice")
    
    def handle_vm_operation(self, choice):
        """Handle VM operations that require VM selection"""
        # Get VM name
        vms = self.list_vms()
        if not vms:
            return
        
        if len(vms) == 1:
            vm_name = vms[0]
            print(f"Using VM: {vm_name}")
        else:
            print("\nSelect VM:")
            try:
                vm_idx = int(input("Enter VM number: ")) - 1
                if 0 <= vm_idx < len(vms):
                    vm_name = vms[vm_idx]
                else:
                    print("❌ Invalid VM number")
                    return
            except ValueError:
                print("❌ Invalid input")
                return
        
        # Run appropriate script
        scripts = {
            '2': 'diagnostics/quick_status.py',
            '3': 'diagnostics/diagnose_vm.py', 
            '4': 'diagnostics/check_cloudinit.py',
            '5': 'diagnostics/check_boot.py',
            '6': 'diagnostics/network_check.py',
            '7': 'fixes/fix_network.py',
            '8': 'fixes/fix_cdrom.py',
            '9': 'check_docker.py',
            '10': 'destroy_vm.py'
        }
        
        script_path = scripts.get(choice)
        if script_path:
            # Special handling for Docker checker
            if choice == '9':
                # Need to get VM IP first
                try:
                    sys.path.append(str(self.project_root))
                    from modules.config import Config
                    config = Config()
                    
                    env = os.environ.copy()
                    env['GOVC_URL'] = f"https://{config.esxi_user}:{config.esxi_password}@{config.esxi_host}/sdk"
                    env['GOVC_INSECURE'] = '1'
                    
                    # Get VM IP
                    cmd = [config.govc_bin, 'vm.ip', vm_name]
                    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
                    
                    if result.returncode == 0 and result.stdout.strip():
                        vm_ip = result.stdout.strip()
                        if vm_ip != "0.0.0.0":
                            print(f"Using VM IP: {vm_ip}")
                            
                            print("\nDocker options:")
                            print("1. Check installation")
                            print("2. Setup rootless Docker")
                            
                            sub_choice = input("Select option: ").strip()
                            if sub_choice == '2':
                                self.run_script(script_path, vm_ip, 'setup')
                            else:
                                self.run_script(script_path, vm_ip)
                        else:
                            print("❌ VM has no IP address")
                    else:
                        print("❌ Could not get VM IP")
                except Exception as e:
                    print(f"❌ Error getting VM IP: {e}")
            # Special handling for VM destruction
            elif choice == '10':
                print(f"\n🚨 WARNING: This will destroy VM: {vm_name}")
                print("This is a DESTRUCTIVE operation!")
                
                confirm = input("Are you sure you want to continue? (yes/no): ").strip().lower()
                if confirm == 'yes':
                    self.run_script(script_path, vm_name)
                else:
                    print("❌ Destruction cancelled")
            # Special handling for cloud-init checker
            elif choice == '4':
                print("\nCloud-init options:")
                print("1. Check logs")
                print("2. Follow logs (real-time)")
                print("3. Quick progress check")
                
                sub_choice = input("Select option: ").strip()
                if sub_choice == '2':
                    self.run_script(script_path, vm_name, 'follow')
                elif sub_choice == '3':
                    self.run_script(script_path, vm_name, 'progress')
                else:
                    self.run_script(script_path, vm_name)
            else:
                self.run_script(script_path, vm_name)

def main():
    if len(sys.argv) == 1:
        # Interactive mode
        manager = VMManager()
        manager.show_menu()
    else:
        # Command line mode
        if len(sys.argv) < 3:
            print("Usage:")
            print("  python3 vm_helper.py                    # Interactive mode")
            print("  python3 vm_helper.py <script> <vm-name> [args]")
            print("")
            print("Available scripts:")
            print("  quick_status     - Quick VM status")
            print("  diagnose        - Full diagnostics")
            print("  check_cloudinit - Cloud-init logs")
            print("  check_boot      - Boot configuration")
            print("  network_check   - Network diagnostics")
            print("  fix_network     - Fix network issues")
            print("  fix_cdrom       - Fix CD-ROM issues")
            print("  destroy         - Destroy VM (DANGEROUS!)")
            sys.exit(1)
        
        script_name = sys.argv[1]
        
        # Map command names to script paths
        script_map = {
            'quick_status': 'diagnostics/quick_status.py',
            'diagnose': 'diagnostics/diagnose_vm.py',
            'check_cloudinit': 'diagnostics/check_cloudinit.py',
            'check_boot': 'diagnostics/check_boot.py',
            'network_check': 'diagnostics/network_check.py',
            'fix_network': 'fixes/fix_network.py',
            'fix_cdrom': 'fixes/fix_cdrom.py',
            'destroy': 'destroy_vm.py',
        }
        
        if script_name in script_map:
            vm_name = sys.argv[2]
            args = sys.argv[3:] if len(sys.argv) > 3 else []
            
            manager = VMManager()
            success = manager.run_script(script_map[script_name], vm_name, *args)
            sys.exit(0 if success else 1)
        else:
            print(f"❌ Unknown script: {script_name}")
            sys.exit(1)

if __name__ == "__main__":
    main()
