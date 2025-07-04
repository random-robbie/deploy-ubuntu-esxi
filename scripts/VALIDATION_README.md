# Cloud-Init Validation System

This comprehensive validation system ensures your cloud-init configurations work correctly before and after deployment, preventing the types of schema validation errors that can break VM deployments.

## 🎯 Overview

The validation system consists of several components:

### Core Validation Scripts

1. **`validator.py`** - Main validation engine
2. **`test_suite.py`** - Comprehensive testing suite
3. **`pre_deploy_check.py`** - Pre-deployment validation hook
4. **`post_deploy_check.py`** - Post-deployment validation

### Integration Scripts

1. **`fixes/fix_cloud_init_schema.py`** - Fix schema issues on deployed VMs
2. **`fixes/complete_fix.py`** - Complete workflow for fixing and redeploying

## 🚀 Quick Start

### 1. Test Your Current Configuration

```bash
cd /Users/rwiggins/tools/newubuntu
python3 scripts/validator.py config
```

### 2. Run Comprehensive Tests

```bash
python3 scripts/test_suite.py
```

### 3. Test a Deployed VM

```bash
python3 scripts/validator.py deploy 192.168.1.189
```

### 4. Full Validation (Config + Deployment)

```bash
python3 scripts/validator.py both 192.168.1.189
```

## 📋 Validation Categories

### Configuration Validation

Tests performed **before** deployment:

- ✅ **Cloud-init script syntax** - Validates Python code
- ✅ **User-data generation** - Tests YAML generation 
- ✅ **Schema compliance** - Checks for problematic properties
- ✅ **Required sections** - Validates essential cloud-init sections
- ✅ **Installation commands** - Verifies Docker/Go installation steps
- ✅ **YAML syntax** - Ensures valid YAML structure

### Deployment Validation

Tests performed **after** deployment:

- ✅ **SSH connectivity** - Tests VM accessibility
- ✅ **Cloud-init status** - Checks execution status
- ✅ **Schema compliance** - Validates deployed configuration
- ✅ **Installation verification** - Tests Docker/Go functionality
- ✅ **Network configuration** - Validates hostname/networking
- ✅ **Service status** - Checks running services

## 🛠️ Usage Examples

### Pre-Deployment Validation

```bash
# Validate configuration before deployment
python3 scripts/validator.py config

# Run comprehensive test suite
python3 scripts/test_suite.py

# Test with specific script path
python3 scripts/validator.py config /path/to/cloudinit.py
```

### Post-Deployment Validation

```bash
# Validate deployed VM
python3 scripts/validator.py deploy 192.168.1.190

# Post-deployment check with custom wait time
python3 scripts/post_deploy_check.py 192.168.1.190 600

# Test suite including deployment validation
python3 scripts/test_suite.py 192.168.1.190
```

### Fixing Issues

```bash
# Fix schema issues on broken VM
python3 scripts/fixes/fix_cloud_init_schema.py 192.168.1.189

# Complete workflow: cleanup + redeploy + test
python3 scripts/fixes/complete_fix.py full 192.168.1.189
```

## 🔧 Integration with Deployment

The validation system is automatically integrated into your deployment process:

### Automatic Pre-Deployment Validation

The `deploy.py` script now automatically runs validation before deployment:

```python
# Step 0: Validate configuration
if not validate_configuration(logger):
    logger.error("Deployment aborted due to validation failures")
    sys.exit(1)
```

### Manual Post-Deployment Validation

After deployment, run:

```bash
python3 scripts/post_deploy_check.py <new-vm-ip>
```

## 📊 Understanding Results

### Success Indicators

```
✅ VALIDATION PASSED - Configuration looks good!
✅ Pre-deployment validation PASSED
✅ Cloud-init completed successfully
✅ Docker is installed and running
✅ Go is installed: go version go1.24.4 linux/amd64
```

### Common Issues and Fixes

#### ❌ Schema Validation Error

```
❌ ERROR: Found 'datasource_list' in user-data template
```

**Fix:** The datasource_list property was removed from the cloudinit.py template.

#### ❌ Cloud-init Not Started

```
❌ ERROR: Cloud-init has not started - likely configuration error
```

**Fix:** This indicates a schema validation error prevented cloud-init from running.

#### ❌ Installation Not Found

```
❌ ERROR: Docker is not properly installed or running
```

**Fix:** Cloud-init may have failed during the installation phase.

## 🔍 Troubleshooting

### Debug Configuration Issues

1. **Run comprehensive tests:**
   ```bash
   python3 scripts/test_suite.py
   ```

2. **Check specific components:**
   ```bash
   python3 scripts/validator.py config
   ```

3. **Validate YAML generation:**
   ```bash
   python3 -c "
   import sys; sys.path.insert(0, 'modules')
   from cloudinit import create_user_data_forced
   # Test YAML generation
   "
   ```

### Debug Deployment Issues

1. **Check VM status:**
   ```bash
   python3 scripts/validator.py deploy <vm-ip>
   ```

2. **Check cloud-init logs:**
   ```bash
   ssh ubuntu@<vm-ip> 'sudo cloud-init status --long'
   ```

3. **Manual installation check:**
   ```bash
   python3 scripts/troubleshoot_installations.py <vm-ip>
   ```

## 🚨 Common Validation Failures

### 1. Datasource List in User-Data

**Problem:** `datasource_list` property in user-data causes schema errors.

**Solution:** Already fixed in the updated cloudinit.py

### 2. YAML Syntax Errors

**Problem:** Invalid YAML structure in generated user-data.

**Solution:** 
```bash
python3 scripts/validator.py config
# Fix any syntax issues in modules/cloudinit.py
```

### 3. Missing Installation Commands

**Problem:** Docker or Go installation commands missing from runcmd.

**Solution:** Verify the runcmd section in cloudinit.py contains proper installation scripts.

### 4. SSH Connection Issues

**Problem:** Cannot connect to VM for validation.

**Solution:**
- Verify VM IP address
- Check network connectivity
- Ensure SSH service is running
- Verify ubuntu user credentials

### 5. Cloud-init Timeout

**Problem:** Cloud-init taking too long to complete.

**Solution:**
```bash
# Wait longer for completion
python3 scripts/post_deploy_check.py <vm-ip> 900
```

## 📈 Best Practices

### Before Every Deployment

1. **Always run pre-deployment validation:**
   ```bash
   python3 scripts/validator.py config
   ```

2. **Run comprehensive tests after changes:**
   ```bash
   python3 scripts/test_suite.py
   ```

### After Every Deployment

1. **Run post-deployment validation:**
   ```bash
   python3 scripts/post_deploy_check.py <vm-ip>
   ```

2. **Verify installations manually:**
   ```bash
   ssh ubuntu@<vm-ip> 'docker --version && /usr/local/go/bin/go version'
   ```

## 📚 Script Reference

| Task | Command |
|------|---------|
| Validate config | `python3 scripts/validator.py config` |
| Test deployment | `python3 scripts/validator.py deploy <ip>` |
| Full validation | `python3 scripts/validator.py both <ip>` |
| Run all tests | `python3 scripts/test_suite.py` |
| Pre-deploy check | `python3 scripts/pre_deploy_check.py` |
| Post-deploy check | `python3 scripts/post_deploy_check.py <ip>` |
| Fix broken VM | `python3 scripts/fixes/fix_cloud_init_schema.py <ip>` |
| Complete fix workflow | `python3 scripts/fixes/complete_fix.py full <ip>` |

---

**🎯 Remember:** Always validate before deploying! This validation system will catch issues early and save you from broken VM deployments.
