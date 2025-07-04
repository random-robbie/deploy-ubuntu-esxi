"""Directory setup and management"""

import os

def setup_directories(config, logger):
    """Create necessary directories"""
    logger.info("Setting up directories...")
    
    directories = [
        config.tools_dir,
        config.work_dir,
        config.iso_dir
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"  Created: {directory}")
    
    # Change to tools directory
    os.chdir(config.tools_dir)
    logger.info(f"Working directory: {config.tools_dir}")
