#!/usr/bin/env python3
"""
Setup script for Ubuntu VM deployment
Creates .env file and checks dependencies
"""

import os
import sys
import shutil

def main():
    print("🚀 Ubuntu VM Deployment Setup")
    print("=" * 40)
    
    # Check if .env exists
    env_file = '.env'
    env_example = '.env.example'
    
    if os.path.exists(env_file):
        print("✅ .env file already exists")
        
        # Ask if user wants to reconfigure
        response = input("Do you want to reconfigure? (y/N): ").lower()
        if response != 'y':
            print("Setup complete. Run: python3 deploy.py")
            return
    
    print("\n📝 Creating .env configuration file...")
    
    # Get ESXi settings
    print("\nESXi Server Configuration:")
    esxi_host = input("ESXi Host IP [192.168.1.248]: ").strip() or "192.168.1.248"
    esxi_user = input("ESXi Username [root]: ").strip() or "root"
    esxi_password = input("ESXi Password: ").strip()
    
    if not esxi_password:
        print("❌ ESXi password is required!")
        sys.exit(1)
    
    # Get VM settings
    print("\nVM Configuration:")
    vm_memory = input("VM Memory (MB) [8192]: ").strip() or "8192"
    vm_cpu = input("VM CPUs [8]: ").strip() or "8"
    vm_disk_size = input("VM Disk Size (GB) [500]: ").strip() or "500"
    datastore = input("ESXi Datastore [12TB]: ").strip() or "12TB"
    go_version = input("Go Version [1.24.4]: ").strip() or "1.24.4"
    
    # SSH key
    ssh_key_path = input("SSH Key Path (leave empty for auto-detect): ").strip()
    
    # Create .env file
    env_content = f"""# ESXi Server Configuration
ESXI_HOST={esxi_host}
ESXI_USER={esxi_user}
ESXI_PASSWORD={esxi_password}

# VM Configuration  
VM_MEMORY={vm_memory}
VM_CPU={vm_cpu}
VM_DISK_SIZE={vm_disk_size}
DATASTORE={datastore}
GO_VERSION={go_version}

# Optional: SSH Key Path (leave empty to auto-detect)
SSH_KEY_PATH={ssh_key_path}
"""
    
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print(f"\n✅ Created {env_file}")
    
    # Set proper permissions
    os.chmod(env_file, 0o600)
    print("🔒 Set secure permissions (600)")
    
    # Check dependencies
    print("\n🔍 Checking dependencies...")
    
    missing = []
    
    # Check Python modules
    try:
        import subprocess
        import urllib.request
        print("✅ Python modules: OK")
    except ImportError as e:
        missing.append(f"Python module: {e}")
    
    # Check system tools
    tools = ['wget', 'curl']
    for tool in tools:
        if shutil.which(tool):
            print(f"✅ {tool}: Found")
        else:
            missing.append(f"{tool}: Install with 'brew install {tool}'")
    
    # Check ISO creation tools
    if shutil.which('mkisofs'):
        print("✅ mkisofs: Found")
    elif shutil.which('genisoimage'):
        print("✅ genisoimage: Found")
    else:
        missing.append("mkisofs/genisoimage: Install with 'brew install cdrtools'")
    
    # Check ovftool
    ovftool_path = os.path.expanduser("~/tools/newubuntu/ovftool/ovftool")
    if os.path.exists(ovftool_path):
        print("✅ ovftool: Found")
    else:
        missing.append("ovftool: Download from VMware and install to ~/tools/newubuntu/ovftool/")
    
    if missing:
        print("\n❌ Missing dependencies:")
        for item in missing:
            print(f"   - {item}")
        print("\nInstall missing dependencies and run setup again.")
    else:
        print("\n🎉 All dependencies satisfied!")
        print("\n🚀 Ready to deploy! Run:")
        print("   python3 deploy.py")
        
        # Show current config
        print(f"\n📋 Current configuration:")
        print(f"   ESXi: {esxi_user}@{esxi_host}")
        print(f"   VM: {vm_cpu} CPUs, {vm_memory} MB RAM, {vm_disk_size} GB disk")
        print(f"   Datastore: {datastore}")
        print(f"   Go: {go_version}")

if __name__ == "__main__":
    main()
