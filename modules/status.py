"""Show final deployment status and instructions"""

def show_final_status(config, logger):
    """Display final deployment status and next steps"""
    
    logger.status("")
    logger.status("🎉 VM Deployment Complete!")
    logger.status("")
    logger.status(f"VM Name: {config.vm_name}")
    logger.status(f"VM Specs: {config.vm_cpu} CPUs, {config.vm_memory} MB RAM, {config.vm_disk_size} GB disk")
    
    if hasattr(config, 'vm_ip') and config.vm_ip:
        logger.status(f"VM IP: {config.vm_ip}")
    else:
        logger.status("VM IP: <check ESXi console>")
    
    logger.status("")
    logger.status("Login Methods:")
    logger.status("1. ESXi Console: ubuntu/ubuntu")
    
    if hasattr(config, 'vm_ip') and config.vm_ip:
        logger.status(f"2. SSH: ssh ubuntu@{config.vm_ip} (password: ubuntu)")
    else:
        logger.status("2. SSH: ssh ubuntu@<vm-ip> (password: ubuntu)")
    
    logger.status("")
    logger.status("What's Installed:")
    logger.status("- Docker + Docker Compose")
    logger.status(f"- Go {config.go_version}")
    logger.status("- Pentesting tools (nmap, netcat, tcpdump, etc.)")
    
    logger.status("")
    logger.status("Next Steps:")
    logger.status("1. Login via console or SSH")
    logger.status("2. Change password: sudo passwd ubuntu")
    logger.status("3. Test installations:")
    logger.status("   docker --version")
    logger.status("   go version")
    logger.status("4. Update system: sudo apt update && sudo apt upgrade -y")
    
    logger.status("")
    if hasattr(config, 'vm_ip') and config.vm_ip:
        logger.info(f"Try SSH now: ssh ubuntu@{config.vm_ip}")
    else:
        logger.info("Check ESXi web interface for VM IP address")
