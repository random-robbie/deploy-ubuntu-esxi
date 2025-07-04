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
        # Expand disk to configured size
        expand_vm_disk(config, logger, env)
        
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

def expand_vm_disk(config, logger, env):
    """Expand VM disk to configured size"""
    logger.info(f"Expanding VM disk to {config.vm_disk_size}GB...")
    
    try:
        # Method 1: Try direct disk expansion by device name
        cmd = [
            config.govc_bin, 'vm.disk.change',
            '-vm', config.vm_name,
            '-size', f'{config.vm_disk_size}G'
        ]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"✅ Disk expanded to {config.vm_disk_size}GB")
            return
        else:
            logger.warn(f"Method 1 failed: {result.stderr}")
        
        # Method 2: Try with disk label
        cmd = [
            config.govc_bin, 'vm.disk.change',
            '-vm', config.vm_name,
            '-disk.label', 'Hard disk 1',
            '-size', f'{config.vm_disk_size}G'
        ]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"✅ Disk expanded to {config.vm_disk_size}GB (method 2)")
            return
        else:
            logger.warn(f"Method 2 failed: {result.stderr}")
        
        # Method 3: Try with common disk key
        cmd = [
            config.govc_bin, 'vm.disk.change',
            '-vm', config.vm_name,
            '-disk.key', '2000',
            '-size', f'{config.vm_disk_size}G'
        ]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"✅ Disk expanded to {config.vm_disk_size}GB (method 3)")
            return
        else:
            logger.warn(f"Method 3 failed: {result.stderr}")
        
        # Method 4: List devices and try to find disk
        logger.info("Listing VM devices to find disk...")
        cmd = [config.govc_bin, 'device.ls', '-vm', config.vm_name]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("VM devices:")
            logger.info(result.stdout)
            
            # Look for disk device in the output
            for line in result.stdout.split('\n'):
                if 'disk-' in line.lower() or 'harddisk' in line.lower():
                    device_name = line.split()[0]
                    logger.info(f"Trying to expand device: {device_name}")
                    
                    cmd = [
                        config.govc_bin, 'vm.disk.change',
                        '-vm', config.vm_name,
                        '-disk.name', device_name,
                        '-size', f'{config.vm_disk_size}G'
                    ]
                    
                    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        logger.info(f"✅ Disk expanded to {config.vm_disk_size}GB (device: {device_name})")
                        return
        
        # If all methods fail, log error but continue
        logger.error("All disk expansion methods failed")
        logger.info("VM will be deployed with original disk size")
        logger.info("Use 'python3 scripts/test_disk_expansion.py <vm-name>' to expand manually")
        
    except Exception as e:
        logger.error(f"Error during disk expansion: {e}")
        logger.info("VM will be deployed with original disk size")

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
