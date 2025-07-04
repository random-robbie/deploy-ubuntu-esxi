"""Deploy VM to ESXi using ovftool"""

import subprocess
import os

def deploy_vm_to_esxi(config, logger):
    """Deploy VM using ovftool with correct syntax"""
    logger.info(f"Deploying VM: {config.vm_name}")
    logger.info(f"Specs: {config.vm_cpu} CPUs, {config.vm_memory} MB RAM, {config.vm_disk_size} GB disk")
    
    ova_path = os.path.join(config.work_dir, config.ubuntu_ova)
    
    # Build ovftool command with CORRECT syntax
    cmd = [
        config.ovftool_bin,
        '--acceptAllEulas',
        '--allowExtraConfig',
        '--diskMode=thin',
        f'--datastore={config.datastore}',
        f'--numberOfCpus:*={config.vm_cpu}',
        f'--memorySize:*={config.vm_memory}',
        f'--name={config.vm_name}',
        '--net:VM Network=VM Network',
        ova_path,
        f'vi://{config.esxi_user}:{config.esxi_password}@{config.esxi_host}/'
    ]
    
    logger.info("Executing ovftool deployment...")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"✅ VM deployed successfully: {config.vm_name}")
            return config.vm_name
        else:
            logger.error(f"ovftool failed: {result.stderr}")
            raise Exception(f"VM deployment failed: {result.stderr}")
            
    except FileNotFoundError:
        raise Exception(f"ovftool not found at {config.ovftool_bin}")
    except Exception as e:
        raise Exception(f"Deployment error: {e}")
