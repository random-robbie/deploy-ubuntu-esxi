# Ubuntu VM Deployment to ESXi

🚀 **Automated Ubuntu VM deployment to VMware ESXi with Docker, Go, and pentesting tools**

A modular Python-based tool that deploys Ubuntu cloud images to ESXi with proper configuration, networking, and software installation via cloud-init.

## ✨ Features

- **Automated VM Deployment** - Deploy Ubuntu VMs to ESXi with correct CPU/RAM/disk specs
- **Cloud-Init Integration** - Automatic hostname, networking, and software installation
- **Pre-installed Software** - Docker, Docker Compose, Go, and common pentesting tools
- **Secure Configuration** - Credentials stored in `.env` file (not in code)
- **Real-time Monitoring** - Track cloud-init progress and installation status
- **Comprehensive Logging** - Built-in diagnostics and troubleshooting tools
- **Modular Design** - Small, focused Python modules for easy maintenance

## 🎯 What Gets Installed

- **Ubuntu 24.04 LTS** (Oracular) - Latest cloud image from [cloud-images.ubuntu.com](https://cloud-images.ubuntu.com/)
- **Docker** + Docker Compose - Latest stable versions
- **Go** - Configurable version (default: 1.24.4)
- **Pentesting Tools** - nmap, netcat, tcpdump, python3, git, vim, htop
- **VMware Tools** - For better ESXi integration

## 📋 Requirements

### System Requirements
- **macOS** (tested on M1 Macs)
- **Python 3.7+**
- **VMware ESXi 6.5+**

### Dependencies
- `wget` - Download Ubuntu images
- `mkisofs` or `genisoimage` - Create cloud-init ISOs
- `ovftool` - VMware OVF Tool for VM deployment
- `ssh` - Monitor deployment progress

### Install Dependencies (macOS)
```bash
# Install Homebrew tools
brew install wget cdrtools

# Download VMware OVF Tool from VMware website
# Extract to ~/tools/newubuntu/ovftool/
```

## 🚀 Quick Start

### 1. Clone and Setup
```bash
# Create directory
mkdir -p ~/tools/newubuntu
cd ~/tools/newubuntu

# Download/copy the deployment scripts
# (Copy all Python files and modules/ directory)

# Run interactive setup
python3 setup.py
```

### 2. Configure ESXi Credentials
The setup script will prompt for:
- ESXi host IP address
- ESXi username (usually `root`)
- ESXi password
- VM specifications (CPU, RAM, disk size)
- Datastore name

### 3. Deploy VM
```bash
python3 deploy.py
```

### 4. Monitor Progress
```bash
# Check cloud-init logs
python3 check_cloudinit.py <vm-name>

# Follow logs in real-time
python3 check_cloudinit.py <vm-name> follow
```

## 📁 Project Structure

```
ubuntu-vm-deployment/
├── deploy.py                 # Main deployment script
├── setup.py                  # Interactive configuration setup
├── .env                      # Your credentials (created by setup)
├── .env.example              # Template for configuration
├── modules/                  # Core deployment modules
│   ├── config.py            # Configuration management
│   ├── logger.py            # Logging functionality
│   ├── dependencies.py      # Dependency checking
│   ├── directories.py       # Directory management
│   ├── download.py          # Ubuntu image download
│   ├── cloudinit.py         # Cloud-init ISO creation
│   ├── deploy.py            # VM deployment via ovftool
│   ├── configure.py         # VM configuration via govc
│   ├── monitor.py           # Progress monitoring
│   └── status.py            # Final status display
├── check_cloudinit.py       # Cloud-init log checker
├── diagnose_vm.py           # VM diagnostics
├── network_check.py         # Network troubleshooting
├── fix_network.py           # Network fixes
├── fix_cdrom.py             # CD-ROM connection fixes
├── check_boot.py            # Boot configuration checker
├── quick_status.py          # Quick VM status
└── check_vm.py              # VM status checker
```

## 🔧 Configuration

### Environment Variables (.env)
```bash
# ESXi Server Configuration
ESXI_HOST=your.esxi.server.ip
ESXI_USER=root
ESXI_PASSWORD=your_esxi_password

# VM Configuration
VM_MEMORY=8192              # RAM in MB
VM_CPU=8                    # Number of CPUs
VM_DISK_SIZE=500           # Disk size in GB
DATASTORE=datastore1       # ESXi datastore name
GO_VERSION=1.24.4          # Go version to install

# Optional: SSH Key Path (auto-detected if empty)
SSH_KEY_PATH=~/.ssh/id_rsa.pub
```

### Default VM Specifications
- **8 CPUs**
- **8GB RAM**
- **500GB disk**
- **Ubuntu 24.04 LTS**
- **Unique hostname** (pentest-YYYYMMDD-HHMMSS)

## 🛠 Usage Examples

### Basic Deployment
```bash
python3 deploy.py
```

### Check VM Status
```bash
python3 quick_status.py ubuntu-pentest-20250704-123456
```

### Monitor Cloud-Init Progress
```bash
# Check status
python3 check_cloudinit.py ubuntu-pentest-20250704-123456 progress

# View logs
python3 check_cloudinit.py ubuntu-pentest-20250704-123456

# Follow logs in real-time
python3 check_cloudinit.py ubuntu-pentest-20250704-123456 follow
```

### Troubleshooting
```bash
# Full VM diagnostics
python3 diagnose_vm.py ubuntu-pentest-20250704-123456

# Network troubleshooting
python3 network_check.py ubuntu-pentest-20250704-123456

# Fix common issues
python3 fix_network.py ubuntu-pentest-20250704-123456
python3 fix_cdrom.py ubuntu-pentest-20250704-123456
```

## 🔒 Security

- **No hardcoded credentials** - All sensitive data in `.env` file
- **Secure file permissions** - `.env` file set to 600 (owner read/write only)
- **Git-safe** - Credentials automatically excluded from version control
- **SSH key support** - Automatic SSH key detection and configuration
- **Password authentication** - Default ubuntu/ubuntu login for initial access

## 🐛 Troubleshooting

### Common Issues

**VM doesn't get IP address:**
```bash
python3 fix_network.py <vm-name>
```

**Cloud-init not running:**
```bash
python3 fix_cdrom.py <vm-name>
```

**SSH connection fails:**
- Check if VM has IP: `python3 quick_status.py <vm-name>`
- Try console login via ESXi web interface: ubuntu/ubuntu
- Check cloud-init status: `python3 check_cloudinit.py <vm-name>`

**Boot order issues:**
```bash
python3 check_boot.py <vm-name>
python3 check_boot.py <vm-name> force
```

### Log Locations
- Cloud-init logs: `/var/log/cloud-init.log`
- Cloud-init output: `/var/log/cloud-init-output.log`
- SSH into VM: `ssh ubuntu@<vm-ip>` (password: ubuntu)

## 🎯 Tested Environment

- **macOS** (Apple Silicon M1/M2)
- **VMware ESXi 7.0+**
- **Python 3.9+**
- **Ubuntu 24.04 LTS** cloud images

> **Note**: Currently tested and optimized for macOS (Apple Silicon). Linux and Intel Mac support may require minor adjustments.

## 📝 Default Credentials

**Initial Login:**
- Username: `ubuntu`
- Password: `ubuntu`

**Security Note:** Change the default password immediately after first login:
```bash
sudo passwd ubuntu
```

## 🔄 Workflow

1. **Download** - Fetches Ubuntu cloud image from cloud-images.ubuntu.com
2. **Configure** - Creates cloud-init configuration with your specifications
3. **Deploy** - Uses ovftool to deploy VM with correct CPU/RAM/disk
4. **Attach** - Connects cloud-init ISO to VM
5. **Boot** - Powers on VM, boots from cloud-init CD-ROM
6. **Install** - Cloud-init installs software and configures system
7. **Verify** - Monitors progress and verifies installations

## 🤝 Contributing

This is a modular Python project designed for easy maintenance:

- **Small modules** - Each file has a single responsibility
- **Easy debugging** - Fix individual components without affecting others
- **Clear structure** - Well-organized codebase with comprehensive logging

## 📄 License

MIT License - Feel free to use and modify for your needs.

## ⚠️ Disclaimer

This tool is designed for legitimate system administration and security testing purposes. Always ensure you have proper authorization before deploying VMs in any environment.
