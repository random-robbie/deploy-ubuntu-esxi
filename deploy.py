#!/usr/bin/env python3
"""
Ubuntu VM Deployment to ESXi - Main Script
Modular Python version with small, fixable components
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.config import Config
from modules.logger import Logger
from modules.dependencies import check_dependencies
from modules.directories import setup_directories
from modules.download import download_ubuntu_image
from modules.cloudinit import create_cloud_init_iso
from modules.deploy import deploy_vm_to_esxi
from modules.configure import configure_vm
from modules.monitor import wait_for_completion
from modules.status import show_final_status

def main():
    """Main deployment function"""
    logger = Logger()
    config = Config()
    
    try:
        logger.info("🚀 Starting Ubuntu VM deployment to ESXi...")
        
        # Step 1: Check dependencies
        check_dependencies(config, logger)
        
        # Step 2: Setup directories
        setup_directories(config, logger)
        
        # Step 3: Download Ubuntu image
        download_ubuntu_image(config, logger)
        
        # Step 4: Create cloud-init ISO
        create_cloud_init_iso(config, logger)
        
        # Step 5: Deploy VM
        vm_name = deploy_vm_to_esxi(config, logger)
        config.vm_name = vm_name
        
        # Step 6: Configure VM
        configure_vm(config, logger)
        
        # Step 7: Wait for completion
        wait_for_completion(config, logger)
        
        # Step 8: Show final status
        show_final_status(config, logger)
        
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
