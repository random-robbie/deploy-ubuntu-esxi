# Disk Expansion Fix Guide

## Problem
VM shows only 8.55GB used space but was configured with 500GB disk - the disk is not auto-expanding.

## Root Cause
Cloud images often don't automatically expand to use the full disk space allocated by the hypervisor.

## Manual Fix Steps

### 1. Check Current Status
```bash
# Check current disk usage
df -h /

# Check physical disk size  
lsblk

# Check partition table
sudo fdisk -l /dev/sda
```

### 2. Install Required Tools
```bash
sudo apt-get update
sudo apt-get install -y cloud-guest-utils
```

### 3. Expand the Partition
```bash
# Grow the root partition (usually /dev/sda1)
sudo growpart /dev/sda 1
```

### 4. Resize the Filesystem
```bash
# For ext4 filesystems (most common)
sudo resize2fs /dev/sda1

# OR for XFS filesystems
sudo xfs_growfs /
```

### 5. Verify the Fix
```bash
# Check new disk usage
df -h /

# Should now show ~500GB available space
```

## Automated Script Usage

Once you have SSH access to the VM:

```bash
# Check disk status
python3 scripts/fix_disk.py <vm-ip>

# Fix disk expansion automatically
python3 scripts/fix_disk.py <vm-ip> fix

# Via VM helper menu (option 11)
python3 scripts/vm_helper.py
```

## Prevention for Future VMs

The cloud-init configuration has been updated to include automatic disk expansion:

```yaml
# Added to cloud-init user-data
packages:
  - cloud-guest-utils

growpart:
  mode: auto
  devices: ['/']
```

This ensures new VMs will automatically expand to use the full allocated disk space during first boot.

## Common Issues

### Issue: "NOCHANGE" message from growpart
- **Cause**: Partition is already at maximum size
- **Solution**: Check if the filesystem needs resizing instead

### Issue: Permission denied
- **Cause**: Not running with sudo
- **Solution**: Ensure all commands use `sudo`

### Issue: Different device names
- **Cause**: VM uses /dev/vda instead of /dev/sda
- **Solution**: Replace /dev/sda with /dev/vda in commands

### Issue: XFS filesystem
- **Cause**: Using XFS instead of ext4
- **Solution**: Use `sudo xfs_growfs /` instead of `resize2fs`

## Verification Commands

```bash
# Before fix - should show ~8GB
df -h /

# After fix - should show ~500GB  
df -h /

# Check if growpart worked
sudo growpart /dev/sda 1
# Should say "NOCHANGE" if already expanded
```

The disk expansion should increase your available space from ~8GB to the full 500GB allocated to the VM.
