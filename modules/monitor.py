"""Monitor VM deployment progress"""

import subprocess
import time
import os

def wait_for_completion(config, logger):
    """Wait for VM to complete setup and get IP"""
    logger.info("Waiting for VM to complete setup...")
    
    env = os.environ.copy()
    env['GOVC_URL'] = f"https://{config.esxi_user}:{config.esxi_password}@{config.esxi_host}/sdk"
    env['GOVC_INSECURE'] = '1'
    
    # Wait for IP address
    vm_ip = wait_for_ip(config, logger, env)
    config.vm_ip = vm_ip
    
    if vm_ip:
        logger.info(f"VM ready at {vm_ip}")
        logger.info("Choose monitoring method:")
        logger.info("1. Monitor via SSH (recommended)")
        logger.info("2. Wait without SSH monitoring")
        logger.info("3. Skip monitoring (manual check)")
        
        choice = input("Select option (1-3) [1]: ").strip() or "1"
        
        if choice == "1":
            # Wait for cloud-init to complete via SSH
            wait_for_cloud_init_completion(config, logger, vm_ip)
        elif choice == "2":
            # Wait for cloud-init without SSH monitoring
            wait_for_cloud_init(config, logger)
        else:
            logger.info("Skipping monitoring - check manually")
            logger.info(f"SSH: ssh ubuntu@{vm_ip}")
            logger.info(f"Check cloud-init: python3 scripts/diagnostics/check_cloudinit.py {config.vm_name}")
    else:
        # Wait for cloud-init without IP monitoring
        logger.info("No IP address yet - using time-based wait")
        wait_for_cloud_init(config, logger)

def wait_for_ip(config, logger, env, max_attempts=60):
    """Wait for VM to get IP address"""
    logger.info("Waiting for VM IP address...")
    
    for attempt in range(max_attempts):
        try:
            cmd = [config.govc_bin, 'vm.ip', config.vm_name]
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                ip = result.stdout.strip()
                if ip and ip != "0.0.0.0":
                    logger.info(f"✅ VM IP: {ip}")
                    return ip
            
            print(".", end="", flush=True)
            time.sleep(10)
            
        except Exception as e:
            logger.warn(f"Error getting IP: {e}")
            time.sleep(10)
    
    print()  # New line after dots
    logger.warn("VM didn't get IP address yet - may need more time")
    return None

def wait_for_cloud_init(config, logger, wait_minutes=10):
    """Wait for cloud-init to complete installation"""
    logger.info(f"Waiting {wait_minutes} minutes for cloud-init to complete...")
    logger.info("This includes Docker and Go installation...")
    
    for minute in range(wait_minutes):
        logger.info(f"  Progress: {minute + 1}/{wait_minutes} minutes")
        time.sleep(60)
    
    logger.info("✅ Cloud-init should be complete")

def wait_for_cloud_init_completion(config, logger, vm_ip):
    """Monitor cloud-init completion via SSH"""
    logger.info("Monitoring cloud-init progress via SSH...")
    
    # Wait a bit for SSH to be ready
    time.sleep(30)
    
    max_attempts = 20  # 20 attempts * 30 seconds = 10 minutes
    ssh_ready = False
    
    for attempt in range(max_attempts):
        try:
            # Test SSH connectivity with short timeout
            ssh_test = subprocess.run([
                'ssh', 
                '-o', 'ConnectTimeout=3',
                '-o', 'ConnectionAttempts=1',
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'BatchMode=yes',
                '-o', 'UserKnownHostsFile=/dev/null',
                f'ubuntu@{vm_ip}', 'echo "SSH ready"'
            ], capture_output=True, text=True, timeout=5)
            
            if ssh_test.returncode == 0:
                if not ssh_ready:
                    logger.info("✅ SSH connection established")
                    ssh_ready = True
                
                # Check cloud-init status
                status_cmd = subprocess.run([
                    'ssh',
                    '-o', 'ConnectTimeout=3',
                    '-o', 'ConnectionAttempts=1', 
                    '-o', 'StrictHostKeyChecking=no',
                    '-o', 'UserKnownHostsFile=/dev/null',
                    f'ubuntu@{vm_ip}', 'sudo cloud-init status --wait 2>/dev/null || echo "cloud-init not available"'
                ], capture_output=True, text=True, timeout=10)
                
                if status_cmd.returncode == 0:
                    status = status_cmd.stdout.strip()
                    
                    if "not available" in status:
                        logger.info("ℹ️  Cloud-init not available on this VM")
                        logger.info("VM appears to be ready - skipping cloud-init monitoring")
                        verify_installations(vm_ip, logger)
                        return
                    elif 'done' in status:
                        logger.info("✅ Cloud-init completed successfully!")
                        
                        # Show final installations
                        logger.info("Verifying installations...")
                        verify_installations(vm_ip, logger)
                        return
                    elif 'running' in status:
                        logger.info(f"🔄 Cloud-init running... (attempt {attempt + 1}/{max_attempts})")
                    elif 'error' in status:
                        logger.warn("❌ Cloud-init reported errors")
                        logger.info("Check logs with: python3 scripts/diagnostics/check_cloudinit.py " + config.vm_name)
                        return
                    else:
                        logger.info(f"Cloud-init status: {status}")
                else:
                    logger.info(f"Waiting for cloud-init status... (attempt {attempt + 1}/{max_attempts})")
            else:
                # SSH not ready yet
                if attempt % 4 == 0:  # Every 2 minutes
                    logger.info(f"Waiting for SSH access to {vm_ip}... (attempt {attempt + 1}/{max_attempts})")
                print(".", end="", flush=True)
                        
        except subprocess.TimeoutExpired:
            logger.info(f"SSH timeout (attempt {attempt + 1}/{max_attempts})")
        except Exception as e:
            if attempt % 4 == 0:  # Don't spam errors
                logger.info(f"SSH not ready yet: {str(e)[:50]}...")
            print(".", end="", flush=True)
        
        time.sleep(30)  # Wait 30 seconds between checks
    
    print()  # New line after dots
    logger.warn("Cloud-init monitoring timed out - VM may still be setting up")
    logger.info("Check status manually with: python3 scripts/diagnostics/check_cloudinit.py " + config.vm_name)
    logger.info(f"Or try SSH directly: ssh ubuntu@{vm_ip}")

def verify_installations(vm_ip, logger):
    """Verify Docker and Go installations"""
    try:
        # Check Docker
        docker_cmd = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'ConnectionAttempts=1',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', 'docker --version'
        ], capture_output=True, text=True, timeout=10)
        
        if docker_cmd.returncode == 0:
            logger.info(f"✅ Docker: {docker_cmd.stdout.strip()}")
        else:
            logger.info("⚠️  Docker not ready yet")
        
        # Check Go
        go_cmd = subprocess.run([
            'ssh', 
            '-o', 'ConnectTimeout=3',
            '-o', 'ConnectionAttempts=1',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{vm_ip}', '/usr/local/go/bin/go version'
        ], capture_output=True, text=True, timeout=10)
        
        if go_cmd.returncode == 0:
            logger.info(f"✅ Go: {go_cmd.stdout.strip()}")
        else:
            logger.info("⚠️  Go not ready yet")
            
    except subprocess.TimeoutExpired:
        logger.info("⚠️  Verification timed out - installations may still be in progress")
    except Exception as e:
        logger.info("Could not verify installations - check manually")
