"""Configure VM after deployment"""

import subprocess
import os

def configure_vm(config, logger):
    """Configure VM with cloud-init ISO, connect CD-ROM, and power on"""
    logger.info("Configuring VM and attaching cloud-init...")
    
    # Set govc environment
    env = os.environ.copy()
    env['GOVC_URL'] = f"https://{config.esxi_user}:{config.esxi_password}@{config.esxi_host}/sdk"
    env['GOVC_INSECURE'] = '1'
    
    try:
        # Upload cloud-init ISO
        upload_cloud_init_iso(config, logger, env)
        
        # Add and attach CD-ROM
        add_cdrom_device(config, logger, env)
        attach_iso_to_cdrom(config, logger, env)
        
        # CRITICAL FIX: Connect the CD-ROM device
        connect_cdrom_device(config, logger, env)
        
        # Set boot order to CD-ROM first
        set_boot_order(config, logger, env)
        
        # Power on VM
        power_on_vm(config, logger, env)
        
    except Exception as e:
        logger.error(f"VM configuration failed: {e}")
        raise

def upload_cloud_init_iso(config, logger, env):
    """Upload cloud-init ISO to datastore"""
    logger.info("Uploading cloud-init ISO...")
    
    iso_local_path = os.path.join(config.work_dir, "cloud-init.iso")
    iso_datastore_path = f"{config.vm_name}/cloud-init.iso"
    
    cmd = [
        config.govc_bin, 'datastore.upload',
        '-ds', config.datastore,
        iso_local_path, iso_datastore_path
    ]
    
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"ISO upload failed: {result.stderr}")
    
    logger.info("✅ Cloud-init ISO uploaded")

def add_cdrom_device(config, logger, env):
    """Add CD-ROM device to VM"""
    logger.info("Adding CD-ROM device...")
    
    cmd = [
        config.govc_bin, 'device.cdrom.add',
        '-vm', config.vm_name
    ]
    
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"CD-ROM add failed: {result.stderr}")

def attach_iso_to_cdrom(config, logger, env):
    """Attach ISO to CD-ROM device"""
    logger.info("Attaching cloud-init ISO to CD-ROM...")
    
    iso_datastore_path = f"{config.vm_name}/cloud-init.iso"
    
    cmd = [
        config.govc_bin, 'device.cdrom.insert',
        '-vm', config.vm_name,
        '-ds', config.datastore,
        iso_datastore_path
    ]
    
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"ISO attach failed: {result.stderr}")
    
    logger.info("✅ Cloud-init ISO attached")

def power_on_vm(config, logger, env):
    """Power on the VM"""
    logger.info("Powering on VM...")
    
    cmd = [
        config.govc_bin, 'vm.power',
        '-on', config.vm_name
    ]
    
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Power on failed: {result.stderr}")
    
    logger.info("✅ VM powered on successfully")

def connect_cdrom_device(config, logger, env):
    """Connect the CD-ROM device so VM can boot from it"""
    logger.info("Connecting CD-ROM device...")
    
    # First, get the CD-ROM device name
    cmd = [config.govc_bin, 'device.ls', '-vm', config.vm_name]
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    
    cdrom_device = None
    for line in result.stdout.split('\n'):
        if 'cdrom-' in line and 'cloud-init.iso' in line:
            cdrom_device = line.split()[0]
            break
    
    if not cdrom_device:
        raise Exception("Could not find cloud-init CD-ROM device")
    
    # Connect the CD-ROM device
    cmd = [
        config.govc_bin, 'device.connect',
        '-vm', config.vm_name, cdrom_device
    ]
    
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        logger.warn(f"CD-ROM connect warning: {result.stderr}")
    else:
        logger.info(f"✅ CD-ROM device {cdrom_device} connected")

def set_boot_order(config, logger, env):
    """Set boot order to CD-ROM first, then disk"""
    logger.info("Setting boot order to CD-ROM first...")
    
    # Try to set boot order - this may not work on all ESXi versions
    cmd = [
        config.govc_bin, 'device.boot',
        '-vm', config.vm_name,
        '-order', 'cdrom,disk'
    ]
    
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if result.returncode == 0:
        logger.info("✅ Boot order set to CD-ROM first")
    else:
        logger.warn("Could not set boot order automatically")
        logger.info("VM will try CD-ROM since it's connected")
