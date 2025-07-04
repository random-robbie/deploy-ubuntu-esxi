"""Create cloud-init ISO with FORCED configuration"""

import os
import subprocess
import shutil

def create_cloud_init_iso(config, logger):
    """Create cloud-init ISO that FORCES hostname and networking"""
    logger.info("Creating cloud-init configuration with FORCED settings...")
    
    # Read SSH key if available
    ssh_key = ""
    if config.ssh_key_path and os.path.exists(config.ssh_key_path):
        with open(config.ssh_key_path, 'r') as f:
            ssh_key = f.read().strip()
        logger.info(f"Found SSH key: {config.ssh_key_path}")
    else:
        logger.warn("No SSH key found - using password authentication only")
    
    # Create user-data with FORCED settings
    user_data_content = create_user_data_forced(config, ssh_key)
    user_data_path = os.path.join(config.work_dir, "user-data")
    with open(user_data_path, 'w') as f:
        f.write(user_data_content)
    
    # Create meta-data
    meta_data_content = create_meta_data(config)
    meta_data_path = os.path.join(config.work_dir, "meta-data")
    with open(meta_data_path, 'w') as f:
        f.write(meta_data_content)
    
    # Create network-config to force DHCP
    network_config_content = create_network_config()
    network_config_path = os.path.join(config.work_dir, "network-config")
    with open(network_config_path, 'w') as f:
        f.write(network_config_content)
    
    # Create ISO with all three files
    iso_path = os.path.join(config.work_dir, "cloud-init.iso")
    create_iso(user_data_path, meta_data_path, network_config_path, iso_path, logger)
    
    logger.info(f"✅ Cloud-init ISO created: {iso_path}")

def create_user_data_forced(config, ssh_key):
    """Generate cloud-init user-data with FORCED execution"""
    ssh_keys_section = ""
    if ssh_key:
        ssh_keys_section = f"""    ssh_authorized_keys:
      - {ssh_key}"""
    
    return f"""#cloud-config

# User configuration
users:
  - name: ubuntu
    sudo: ALL=(ALL) NOPASSWD:ALL
    shell: /bin/bash
    lock_passwd: false
    plain_text_passwd: ubuntu
{ssh_keys_section}

# Force password authentication
ssh_pwauth: true
disable_root: false
chpasswd:
  expire: false
  users:
    - name: ubuntu
      password: ubuntu
      type: text

# FORCE hostname change - multiple methods
hostname: {config.vm_hostname}
fqdn: {config.vm_hostname}.local
preserve_hostname: false
manage_etc_hosts: true

# Force network configuration
write_files:
  - path: /etc/netplan/50-cloud-init.yaml
    content: |
      network:
        version: 2
        ethernets:
          ens160:
            dhcp4: true
            dhcp4-overrides:
              use-hostname: false
          ens192:
            dhcp4: true
            dhcp4-overrides:
              use-hostname: false
    permissions: '0644'
  - path: /etc/hostname
    content: {config.vm_hostname}
    permissions: '0644'

# Install packages
packages:
  - curl
  - wget
  - git
  - vim
  - htop
  - nmap
  - netcat-traditional
  - tcpdump
  - python3
  - python3-pip
  - net-tools
  - dnsutils
  - apt-transport-https
  - ca-certificates
  - gnupg
  - lsb-release
  - software-properties-common
  - cloud-guest-utils

# Enable disk expansion
growpart:
  mode: auto
  devices: ['/']

# FORCE everything to run
runcmd:
  # FORCE hostname change immediately
  - hostnamectl set-hostname {config.vm_hostname}
  - echo "{config.vm_hostname}" > /etc/hostname
  - sed -i 's/127.0.1.1.*/127.0.1.1 {config.vm_hostname}.local {config.vm_hostname}/' /etc/hosts
  
  # FORCE password reset
  - echo "ubuntu:ubuntu" | chpasswd
  - usermod -aG sudo ubuntu
  
  # FORCE SSH configuration
  - sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config
  - sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
  - systemctl restart ssh
  
  # FORCE network restart
  - netplan generate
  - netplan apply
  - systemctl restart systemd-networkd
  - systemctl restart networking
  
  # Install Docker using official script with error handling
  - |
    set -e
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
    sh /tmp/get-docker.sh
    rm /tmp/get-docker.sh
  - usermod -aG docker ubuntu
  - systemctl enable docker
  - systemctl start docker
  - sleep 5
  
  # Verify Docker installation
  - docker --version
  - systemctl is-active docker
  
  # Prepare for Docker rootless mode
  - apt-get update
  - apt-get install -y uidmap dbus-user-session slirp4netns fuse-overlayfs
  - echo 'kernel.unprivileged_userns_clone=1' >> /etc/sysctl.conf
  - sysctl -p
  
  # Enable lingering for ubuntu user (required for rootless)
  - loginctl enable-linger ubuntu
  
  # Create improved rootless setup script
  - |
    cat > /home/ubuntu/setup-docker-rootless.sh << 'EOF'
    #!/bin/bash
    set -e
    
    echo "Setting up Docker rootless mode..."
    
    # Ensure we're running as ubuntu user
    if [ "$(whoami)" != "ubuntu" ]; then
        echo "Error: This script must be run as the ubuntu user"
        exit 1
    fi
    
    # Stop system Docker for this user
    sudo systemctl disable --now docker.service docker.socket 2>/dev/null || true
    
    # Set up environment
    export XDG_RUNTIME_DIR="/run/user/$(id -u)"
    export DOCKER_HOST="unix://$XDG_RUNTIME_DIR/docker.sock"
    
    # Ensure XDG_RUNTIME_DIR exists
    mkdir -p "$XDG_RUNTIME_DIR"
    
    # Install rootless Docker
    echo "Installing rootless Docker..."
    dockerd-rootless-setuptool.sh install
    
    # Enable and start user systemd service
    systemctl --user enable docker.service
    systemctl --user start docker.service
    
    # Add environment variables to bashrc
    echo "# Docker rootless environment" >> ~/.bashrc
    echo 'export XDG_RUNTIME_DIR="/run/user/$(id -u)"' >> ~/.bashrc
    echo 'export DOCKER_HOST="unix://$XDG_RUNTIME_DIR/docker.sock"' >> ~/.bashrc
    echo 'export PATH="/usr/bin:$PATH"' >> ~/.bashrc
    
    echo "Docker rootless setup complete!"
    echo "Please logout and login again, or run: source ~/.bashrc"
    echo "Then test with: docker ps"
    EOF
  - chmod +x /home/ubuntu/setup-docker-rootless.sh
  - chown ubuntu:ubuntu /home/ubuntu/setup-docker-rootless.sh
  
  # Install Go {config.go_version}
  - wget -c https://golang.org/dl/go{config.go_version}.linux-amd64.tar.gz -O - | tar -xz -C /usr/local
  - echo 'export PATH=$PATH:/usr/local/go/bin' >> /home/ubuntu/.bashrc
  - echo 'export PATH=$PATH:/usr/local/go/bin' >> /etc/profile
  - mkdir -p /home/ubuntu/go/{{bin,src,pkg}}
  - echo 'export GOPATH=/home/ubuntu/go' >> /home/ubuntu/.bashrc
  - echo 'export PATH=$PATH:$GOPATH/bin' >> /home/ubuntu/.bashrc
  - chown -R ubuntu:ubuntu /home/ubuntu/go
  
  # FORCE final network restart
  - sleep 10
  - systemctl restart systemd-networkd
  - dhclient -r && dhclient

# Force reboot to apply all changes
power_state:
  delay: now
  mode: reboot
  message: "Rebooting to apply hostname and network changes"
  timeout: 30
  condition: true

final_message: "VM configured with hostname {config.vm_hostname}! Login: ubuntu/ubuntu\nDocker installed and verified. For rootless mode: ./setup-docker-rootless.sh\nTest standard Docker: docker ps (after logout/login)"
"""

def create_meta_data(config):
    """Generate cloud-init meta-data"""
    import time
    return f"""instance-id: pentest-vm-{int(time.time())}
local-hostname: {config.vm_hostname}
"""

def create_network_config():
    """Generate network-config to force DHCP"""
    return """version: 2
ethernets:
  ens160:
    dhcp4: true
  ens192:
    dhcp4: true
"""

def create_iso(user_data_path, meta_data_path, network_config_path, iso_path, logger):
    """Create ISO using available tool with network-config"""
    
    if shutil.which('mkisofs'):
        cmd = [
            'mkisofs', '-o', iso_path, '-V', 'cidata', '-J', '-R',
            user_data_path, meta_data_path, network_config_path
        ]
        logger.info("Creating ISO with mkisofs...")
    elif shutil.which('genisoimage'):
        cmd = [
            'genisoimage', '-output', iso_path, '-volid', 'cidata',
            '-joliet', '-rock', user_data_path, meta_data_path, network_config_path
        ]
        logger.info("Creating ISO with genisoimage...")
    else:
        raise Exception("No ISO creation tool found (mkisofs or genisoimage)")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"ISO creation failed: {result.stderr}")
