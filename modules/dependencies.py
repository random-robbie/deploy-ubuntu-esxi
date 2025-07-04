"""Check system dependencies"""

import os
import shutil
import subprocess
import sys

def check_dependencies(config, logger):
    """Check all required dependencies"""
    logger.info("Checking dependencies...")
    
    missing = []
    
    # Check ovftool
    if not os.path.exists(config.ovftool_bin):
        missing.append(f"ovftool (expected at {config.ovftool_bin})")
    elif not os.access(config.ovftool_bin, os.X_OK):
        missing.append(f"ovftool (not executable at {config.ovftool_bin})")
    
    # Check or install govc
    if not os.path.exists(config.govc_bin):
        logger.info("Installing govc...")
        try:
            install_govc(config)
        except Exception as e:
            missing.append(f"govc (failed to install: {e})")
    
    # Check system tools
    required_tools = ['wget', 'curl']
    for tool in required_tools:
        if not shutil.which(tool):
            missing.append(f"{tool} (install with: brew install {tool})")
    
    # Check ISO creation tool
    if not shutil.which('mkisofs') and not shutil.which('genisoimage'):
        missing.append("mkisofs or genisoimage (install with: brew install cdrtools)")
    
    if missing:
        logger.error("Missing dependencies:")
        for item in missing:
            logger.error(f"  - {item}")
        sys.exit(1)
    
    logger.info("✅ All dependencies satisfied")

def install_govc(config):
    """Install govc CLI tool"""
    import urllib.request
    import tarfile
    import platform
    
    # Create govc directory
    govc_dir = os.path.dirname(config.govc_bin)
    os.makedirs(govc_dir, exist_ok=True)
    
    # Download URL
    system = platform.system()
    machine = platform.machine()
    if machine == 'x86_64':
        machine = 'amd64'
    
    url = f"https://github.com/vmware/govmomi/releases/latest/download/govc_{system}_{machine}.tar.gz"
    
    # Download and extract
    with urllib.request.urlopen(url) as response:
        with tarfile.open(fileobj=response, mode='r|gz') as tar:
            for member in tar:
                if member.name == 'govc':
                    member.name = os.path.basename(config.govc_bin)
                    tar.extract(member, govc_dir)
                    break
    
    # Make executable
    os.chmod(config.govc_bin, 0o755)
