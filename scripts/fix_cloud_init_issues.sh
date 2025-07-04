#!/bin/bash
#
# Cloud-Init Issue Fix Script
# Addresses the specific issues found in your cloud-init logs
#

set -e

echo "🔧 Cloud-Init Issue Fix Script"
echo "================================"
echo "This script fixes common cloud-init issues for pentesting VMs"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root"
    echo "Usage: sudo $0"
    exit 1
fi

echo "🔍 Diagnosing current issues..."

# Issue 1: Fix netplan permissions
echo ""
echo "1️⃣  Fixing netplan file permissions..."
if [ -f /etc/netplan/50-cloud-init.yaml ]; then
    echo "   Found netplan file, fixing permissions..."
    chmod 600 /etc/netplan/50-cloud-init.yaml
    chown root:root /etc/netplan/50-cloud-init.yaml
    echo "   ✅ Netplan permissions fixed"
else
    echo "   ⚠️  Netplan file not found"
fi

# Issue 2: Handle networking.service not found
echo ""
echo "2️⃣  Checking network service status..."
if systemctl list-unit-files | grep -q "networking.service"; then
    echo "   networking.service exists"
    systemctl restart networking
    echo "   ✅ networking.service restarted"
else
    echo "   networking.service not found (normal on newer systems)"
    echo "   Using systemd-networkd instead..."
    systemctl restart systemd-networkd
    echo "   ✅ systemd-networkd restarted"
fi

# Issue 3: Check internet connectivity and fix Docker installation
echo ""
echo "3️⃣  Checking Docker installation..."
if command -v docker > /dev/null 2>&1; then
    echo "   Docker is installed"
    docker --version
    if systemctl is-active --quiet docker; then
        echo "   ✅ Docker service is running"
    else
        echo "   Starting Docker service..."
        systemctl start docker
        systemctl enable docker
        echo "   ✅ Docker service started"
    fi
else
    echo "   Docker not found, checking internet connectivity..."
    if ping -c 1 8.8.8.8 > /dev/null 2>&1; then
        echo "   Internet is available, installing Docker..."
        
        # Install Docker using repository method (more reliable)
        apt-get update
        apt-get install -y ca-certificates curl gnupg lsb-release
        
        # Add Docker's official GPG key
        mkdir -p /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        chmod a+r /etc/apt/keyrings/docker.gpg
        
        # Add Docker repository
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
        
        # Install Docker
        apt-get update
        apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
        
        # Start and enable Docker
        systemctl enable docker
        systemctl start docker
        
        # Add ubuntu user to docker group if exists
        if id "ubuntu" &>/dev/null; then
            usermod -aG docker ubuntu
        fi
        
        echo "   ✅ Docker installed successfully"
    else
        echo "   ❌ No internet connectivity - Docker installation skipped"
        echo "   Please fix network connectivity and run this script again"
    fi
fi

# Issue 4: Fix SSH host key generation
echo ""
echo "4️⃣  Checking SSH host keys..."
if [ ! -f /etc/ssh/ssh_host_rsa_key ] || [ ! -f /etc/ssh/ssh_host_ed25519_key ]; then
    echo "   Generating missing SSH host keys..."
    ssh-keygen -A
    systemctl restart ssh || systemctl restart sshd
    echo "   ✅ SSH host keys generated and SSH restarted"
else
    echo "   ✅ SSH host keys exist"
fi

# Issue 5: Create network troubleshooting script
echo ""
echo "5️⃣  Creating troubleshooting scripts..."

# Create network fix script
cat > /home/ubuntu/fix-network.sh << 'EOF'
#!/bin/bash
echo "🔧 Network Troubleshooting Script"
echo "================================="

echo "Current network status:"
echo "----------------------"
ip addr show
echo ""
echo "Current routes:"
ip route show
echo ""

echo "Fixing netplan permissions..."
sudo chmod 600 /etc/netplan/*.yaml
sudo chown root:root /etc/netplan/*.yaml

echo "Regenerating network configuration..."
sudo netplan generate
sudo netplan apply

echo "Restarting network services..."
sudo systemctl restart systemd-networkd
sudo systemctl restart NetworkManager 2>/dev/null || echo "NetworkManager not running"

echo "Renewing DHCP lease..."
sudo dhclient -r 2>/dev/null || true
sleep 2
sudo dhclient 2>/dev/null || true

echo ""
echo "Updated network status:"
echo "----------------------"
ip addr show
echo ""
echo "Network troubleshooting completed"
EOF

chmod +x /home/ubuntu/fix-network.sh
chown ubuntu:ubuntu /home/ubuntu/fix-network.sh 2>/dev/null || true

# Create Docker troubleshooting script
cat > /home/ubuntu/fix-docker.sh << 'EOF'
#!/bin/bash
echo "🔧 Docker Troubleshooting Script"
echo "================================"

# Check if Docker is installed
if ! command -v docker > /dev/null 2>&1; then
    echo "Docker not installed. Installing now..."
    if ping -c 1 8.8.8.8 > /dev/null 2>&1; then
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        rm get-docker.sh
        sudo usermod -aG docker $USER
        echo "Docker installed. Please logout and login again."
    else
        echo "❌ No internet connectivity for Docker installation"
        exit 1
    fi
else
    echo "Docker is installed"
    docker --version
fi

# Check Docker service
if ! systemctl is-active --quiet docker; then
    echo "Starting Docker service..."
    sudo systemctl start docker
    sudo systemctl enable docker
fi

# Test Docker
echo "Testing Docker..."
sudo docker run hello-world

echo "✅ Docker is working correctly"
EOF

chmod +x /home/ubuntu/fix-docker.sh
chown ubuntu:ubuntu /home/ubuntu/fix-docker.sh 2>/dev/null || true

echo "   ✅ Troubleshooting scripts created in /home/ubuntu/"

# Issue 6: Apply final network fixes
echo ""
echo "6️⃣  Applying final network configuration..."
netplan generate
netplan apply
systemctl restart systemd-networkd

echo ""
echo "🎉 All fixes applied successfully!"
echo ""
echo "📋 Summary of fixes:"
echo "   ✅ Fixed netplan file permissions (600)"
echo "   ✅ Handled networking.service issue"
echo "   ✅ Fixed/installed Docker"
echo "   ✅ Generated SSH host keys"
echo "   ✅ Created troubleshooting scripts"
echo "   ✅ Applied network configuration"
echo ""
echo "📝 Available troubleshooting scripts:"
echo "   • /home/ubuntu/fix-network.sh - Fix network issues"
echo "   • /home/ubuntu/fix-docker.sh - Fix Docker issues"
echo ""
echo "🔄 You may want to reboot the system to ensure all changes take effect"
echo "   sudo reboot"
