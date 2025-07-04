"""Download Ubuntu cloud image"""

import os
import urllib.request
import urllib.error

def download_ubuntu_image(config, logger):
    """Download Ubuntu OVA if not already present"""
    logger.info("Checking Ubuntu cloud image...")
    
    ova_path = os.path.join(config.work_dir, config.ubuntu_ova)
    
    if os.path.exists(ova_path):
        logger.info("Ubuntu image already downloaded")
        return
    
    logger.info("Downloading Ubuntu cloud image...")
    url = f"{config.ubuntu_base_url}/{config.ubuntu_ova}"
    
    try:
        # Download with progress
        def progress_hook(block_num, block_size, total_size):
            if total_size > 0:
                percent = min(100, (block_num * block_size * 100) // total_size)
                print(f"\rDownloading: {percent}%", end='', flush=True)
        
        urllib.request.urlretrieve(url, ova_path, progress_hook)
        print()  # New line after progress
        logger.info(f"✅ Downloaded: {ova_path}")
        
    except urllib.error.URLError as e:
        logger.error(f"Failed to download Ubuntu image: {e}")
        raise
