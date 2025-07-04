"""Create cloud-init ISO with FIXED configuration for security testing"""

import os
import subprocess
import shutil

def create_cloud_init_iso(config, logger):
    """Create cloud-init ISO that FORCES hostname and networking with proper error handling"""
    logger.info("Creating cloud-init configuration with FIXED settings...")
    
    # Read SSH key if available
    ssh_key = ""
    if config.ssh_key_path and os.path.exists(config.ssh_key_path):
        with open(config.ssh_key_path, 'r') as f:
            ssh_key = f.read().strip()
        logger.info(f"Found SSH key: {config.ssh_key_path}")
    else:
        logger.warn("No SSH key found - using password authentication only")
    
    # Create user-data with FIXED settings
    user_data_content = create_user_data_forced(config, ssh_key)
    user_data_path = os.path.join(config.work_dir, "user-data")
    with open(user_data_path, 'w') as f:
        f.write(user_data_content)
    
    # Create meta-data
    meta_data_content = create_meta_data(config)
    meta_data_path = os.path.join(config.work_dir, "meta-data")
    with open(meta_data_path, 'w') as f:
        f.write(meta_data_content)
    
    # Create network-config to force DHCP with proper permissions
    network_config_content = create_network_config()
    network_config_path = os.path.join(config.work_dir, "network-config")
    with open(network_config_path, 'w') as f:
        f.write(network_config_content)
    
    # Create ISO with all three files
    iso_path = os.path.join(config.work_dir, "cloud-init.iso")
    create_iso(user_data_path, meta_data_path, network_config_path, iso_path, logger)
    
    logger.info(f"✅ Cloud-init ISO created: {iso_path}")

def create_user_data_forced(config, ssh_key):
    """Generate cloud-init user-data with FIXED execution and proper error handling"""
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

# Force network configuration with proper permissions
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
    permissions: '0600'
    owner: root:root
  - path: /etc/hostname
    content: {config.vm_hostname}
    permissions: '0644'
    owner: root:root
  - path: /home/ubuntu/install-docker.sh
    content: |
      #!/bin/bash
      set -e
      
      echo "Installing Docker with error handling..."
      
      # Check internet connectivity first
      if ! ping -c 1 8.8.8.8 > /dev/null 2>&1; then
          echo "Warning: No internet connectivity, Docker installation may fail"
          exit 1
      fi
      
      # Add Docker's official GPG key and repository
      apt-get update
      apt-get install -y ca-certificates curl gnupg lsb-release
      
      # Create keyring directory
      mkdir -p /etc/apt/keyrings
      
      # Add Docker GPG key
      curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
      chmod a+r /etc/apt/keyrings/docker.gpg
      
      # Add Docker repository
      echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
      
      # Update and install Docker
      apt-get update
      apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
      
      # Start and enable Docker
      systemctl enable docker
      systemctl start docker
      
      # Add ubuntu user to docker group
      usermod -aG docker ubuntu
      
      # Test Docker installation
      docker --version
      systemctl is-active docker
      
      echo "Docker installation completed successfully"
    permissions: '0755'
    owner: root:root

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

# FIXED runcmd with proper error handling
runcmd:
  # Fix netplan permissions first
  - chmod 600 /etc/netplan/50-cloud-init.yaml
  - chown root:root /etc/netplan/50-cloud-init.yaml
  
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
  - systemctl restart ssh || systemctl restart sshd
  
  # Fix network configuration with proper error handling
  - |
    set +e  # Don't exit on errors for network commands
    echo "Configuring network..."
    netplan generate
    netplan apply
    # Try different network restart methods
    systemctl restart systemd-networkd || true
    systemctl restart NetworkManager || true
    # Legacy networking service (may not exist)
    systemctl restart networking || echo "networking.service not found (this is normal on newer systems)"
    echo "Network configuration completed"
  
  # Wait for network to settle
  - sleep 10
  
  # Install Docker with better error handling
  - |
    set -e
    echo "Starting Docker installation..."
    if ping -c 1 8.8.8.8 > /dev/null 2>&1; then
        /home/ubuntu/install-docker.sh
        echo "Docker installation successful"
    else
        echo "ERROR: No internet connectivity - Docker installation skipped"
        echo "Manual installation required after network is fixed"
    fi
  
  # Install Go {config.go_version} with error handling
  - |
    set -e
    echo "Installing Go {config.go_version}..."
    if ping -c 1 golang.org > /dev/null 2>&1; then
        cd /tmp
        wget -q https://golang.org/dl/go{config.go_version}.linux-amd64.tar.gz
        tar -xzf go{config.go_version}.linux-amd64.tar.gz -C /usr/local
        rm go{config.go_version}.linux-amd64.tar.gz
        echo "Go installation successful"
    else
        echo "ERROR: Cannot reach golang.org - Go installation skipped"
    fi
  
  # Set up Go environment
  - echo 'export PATH=$PATH:/usr/local/go/bin' >> /home/ubuntu/.bashrc
  - echo 'export PATH=$PATH:/usr/local/go/bin' >> /etc/profile
  - mkdir -p /home/ubuntu/go/{{bin,src,pkg}}
  - echo 'export GOPATH=/home/ubuntu/go' >> /home/ubuntu/.bashrc
  - echo 'export PATH=$PATH:$GOPATH/bin' >> /home/ubuntu/.bashrc
  - chown -R ubuntu:ubuntu /home/ubuntu/go
  
  # Create improved rootless Docker setup script
  - |
    cat > /home/ubuntu/setup-docker-rootless.sh << 'EOF'
    #!/bin/bash
    set -e
    
    echo "Setting up Docker rootless mode..."
    
    # Ensure we're running as ubuntu user
    if [ "$(whoami)" != "ubuntu" ]; then
        echo "Error: This script must be run as the ubuntu user"
        echo "Usage: sudo -u ubuntu ./setup-docker-rootless.sh"
        exit 1
    fi
    
    # Check if Docker is installed
    if ! command -v docker > /dev/null 2>&1; then
        echo "Error: Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Install prerequisites for rootless mode
    sudo apt-get update
    sudo apt-get install -y uidmap dbus-user-session slirp4netns fuse-overlayfs
    
    # Enable unprivileged user namespaces
    echo 'kernel.unprivileged_userns_clone=1' | sudo tee -a /etc/sysctl.conf
    sudo sysctl -p
    
    # Enable lingering for ubuntu user
    sudo loginctl enable-linger ubuntu
    
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
  
  # Create network troubleshooting script
  - |
    cat > /home/ubuntu/fix-network.sh << 'EOF'
    #!/bin/bash
    echo "Network troubleshooting script"
    echo "Current network configuration:"
    ip addr show
    echo ""
    echo "Fixing netplan permissions..."
    sudo chmod 600 /etc/netplan/50-cloud-init.yaml
    echo "Regenerating network configuration..."
    sudo netplan generate
    sudo netplan apply
    echo "Restarting network services..."
    sudo systemctl restart systemd-networkd
    echo "Network fix attempt completed"
    EOF
  - chmod +x /home/ubuntu/fix-network.sh
  - chown ubuntu:ubuntu /home/ubuntu/fix-network.sh
  
  # Generate SSH host keys if missing
  - |
    if [ ! -f /etc/ssh/ssh_host_rsa_key ]; then
        echo "Generating SSH host keys..."
        ssh-keygen -A
    fi
  
  # Final network restart with proper error handling
  - |
    set +e
    echo "Final network configuration..."
    sleep 5
    systemctl restart systemd-networkd || true
    # Force DHCP renewal
    dhclient -r || true
    sleep 2
    dhclient || true
    echo "Network configuration completed"

# Don't force reboot - let it complete naturally
final_message: |
  VM configured with hostname {config.vm_hostname}!
  Login: ubuntu/ubuntu
  
  Docker installed (if internet was available during setup)
  For rootless Docker mode: ./setup-docker-rootless.sh
  Test Docker: docker ps (after logout/login)
  
  Go {config.go_version} installed (if internet was available)
  Test Go: go version
  
  Network troubleshooting: ./fix-network.sh
  
  Ready for security testing!
"""

def create_meta_data(config):
    """Generate cloud-init meta-data"""
    import time
    return f"""instance-id: pentest-vm-{int(time.time())}
local-hostname: {config.vm_hostname}
"""

def create_network_config():
    """Generate network-config to force DHCP with proper security"""
    return """version: 2
ethernets:
  ens160:
    dhcp4: true
    dhcp4-overrides:
      use-hostname: false
  ens192:
    dhcp4: true
    dhcp4-overrides:
      use-hostname: false
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
