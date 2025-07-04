# Scripts Directory

This directory contains organized scripts for VM management and troubleshooting.

## Directory Structure

```
scripts/
├── diagnostics/     # VM diagnostic and status checking scripts
│   ├── check_boot.py       # Check boot order and CD-ROM status
│   ├── check_cloudinit.py  # Monitor cloud-init progress
│   ├── check_vm.py         # General VM status checker
│   ├── diagnose_vm.py      # Comprehensive VM diagnostics
│   ├── network_check.py    # Network connectivity diagnostics
│   └── quick_status.py     # Fast VM status check
├── fixes/          # VM repair and fix scripts
│   ├── fix_cdrom.py        # Fix CD-ROM connection and boot
│   └── fix_network.py      # Force network reset and repair
├── check_docker.py     # Check Docker installation status
├── destroy_vm.py       # DESTROY VMs and clean up resources
├── test_destroy.py     # Create test VM for destruction testing
└── README.md           # This file
```

## Usage Examples

### Diagnostic Scripts

```bash
# Quick VM status
python3 scripts/diagnostics/quick_status.py ubuntu-pentest-20250704-102906

# Full VM diagnostics
python3 scripts/diagnostics/diagnose_vm.py ubuntu-pentest-20250704-102906

# Check cloud-init progress
python3 scripts/diagnostics/check_cloudinit.py ubuntu-pentest-20250704-102906

# Follow cloud-init logs in real-time
python3 scripts/diagnostics/check_cloudinit.py ubuntu-pentest-20250704-102906 follow

# Check boot configuration
python3 scripts/diagnostics/check_boot.py ubuntu-pentest-20250704-102906

# Network diagnostics
python3 scripts/diagnostics/network_check.py ubuntu-pentest-20250704-102906
```

### Fix Scripts

```bash
# Fix network issues
python3 scripts/fixes/fix_network.py ubuntu-pentest-20250704-102906

# Fix CD-ROM and force boot
python3 scripts/fixes/fix_cdrom.py ubuntu-pentest-20250704-102906

# Force CD-ROM boot order
python3 scripts/diagnostics/check_boot.py ubuntu-pentest-20250704-102906 force

# Check Docker installation
python3 scripts/check_docker.py 192.168.1.170

# Setup rootless Docker
python3 scripts/check_docker.py 192.168.1.170 setup
```

### Destruction Scripts (⚠️  DANGEROUS)

```bash
# List all VMs available for deletion
python3 scripts/destroy_vm.py --list

# Destroy specific VM (with confirmation)
python3 scripts/destroy_vm.py ubuntu-pentest-20250704-102906

# Destroy all VMs matching pattern
python3 scripts/destroy_vm.py --pattern ubuntu-pentest

# Interactive destruction menu
python3 scripts/destroy_vm.py

# Create test VM for destruction testing
python3 scripts/test_destroy.py
```

## Script Categories

### Diagnostics (`diagnostics/`)
- **Non-destructive** operations only
- Gather information and status
- Safe to run multiple times
- No configuration changes

### Fixes (`fixes/`)
- **Potentially destructive** operations
- Modify VM configuration
- Power cycle VMs
- Use with caution in production

### Destruction (`destroy_vm.py`)
- **EXTREMELY DESTRUCTIVE** operations
- Permanently deletes VMs and all data
- Multiple safety confirmations required
- Cannot be undone - use with extreme caution

## Security Notes

- All scripts use credentials from `.env` file
- No hardcoded passwords or sensitive data
- SSH operations use key-based auth when possible
- Fallback to documented default credentials for cloud images

## Adding New Scripts

When adding new scripts:

1. Place diagnostic scripts in `diagnostics/`
2. Place fix/repair scripts in `fixes/`
3. Follow the naming convention: `action_target.py`
4. Include proper documentation and usage examples
5. Use the existing config and logger modules
6. Test thoroughly before adding to version control
