#!/usr/bin/env python3
"""
Cloud-Init Configuration Validator
Validates cloud-init configurations before deployment and running VMs
"""

import sys
import os
import json
import subprocess
import tempfile
import re
from typing import Dict, List, Tuple, Optional

try:
    import yaml
    # Fix for collections.Hashable deprecation in newer Python versions
    try:
        import collections.abc
        if not hasattr(collections, 'Hashable'):
            import collections
            collections.Hashable = collections.abc.Hashable
    except (ImportError, AttributeError):
        pass
except ImportError:
    print("❌ PyYAML not installed. Install with: pip install PyYAML")
    sys.exit(1)

class CloudInitValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []
        
    def add_error(self, message: str):
        self.errors.append(f"❌ ERROR: {message}")
        
    def add_warning(self, message: str):
        self.warnings.append(f"⚠️  WARNING: {message}")
        
    def add_info(self, message: str):
        self.info.append(f"ℹ️  INFO: {message}")
        
    def print_results(self):
        """Print validation results"""
        print("\n" + "="*60)
        print("CLOUD-INIT VALIDATION RESULTS")
        print("="*60)
        
        if self.errors:
            print("\n🚨 ERRORS FOUND:")
            for error in self.errors:
                print(f"  {error}")
                
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  {warning}")
                
        if self.info:
            print("\n📋 INFORMATION:")
            for info in self.info:
                print(f"  {info}")
                
        print("\n" + "="*60)
        
        if self.errors:
            print("❌ VALIDATION FAILED - Please fix errors before deployment")
            return False
        elif self.warnings:
            print("⚠️  VALIDATION PASSED WITH WARNINGS")
            return True
        else:
            print("✅ VALIDATION PASSED - Configuration looks good!")
            return True

class ConfigurationValidator(CloudInitValidator):
    """Validates cloud-init configuration files and scripts"""
    
    def validate_cloudinit_script(self, script_path: str) -> bool:
        """Validate the cloud-init Python script"""
        print(f"🔍 Validating cloud-init script: {script_path}")
        
        if not os.path.exists(script_path):
            self.add_error(f"Cloud-init script not found: {script_path}")
            return False
            
        try:
            with open(script_path, 'r') as f:
                content = f.read()
                
            # Check for problematic datasource_list in user-data
            if 'datasource_list: ["NoCloud", "None"]' in content or "datasource_list: ['NoCloud', 'None']" in content:
                self.add_error("Found 'datasource_list' in user-data template - this will cause schema validation errors")
                self.add_error("Remove datasource_list from user-data - it belongs in system config only")
                
            # Check for required functions
            required_functions = ['create_user_data_forced', 'create_meta_data', 'create_network_config']
            for func in required_functions:
                if f"def {func}" not in content:
                    self.add_error(f"Missing required function: {func}")
                    
            # Check for proper YAML structure in template
            if '#cloud-config' not in content:
                self.add_warning("Cloud-config header not found in template")
                
            # Check for potential YAML syntax issues
            if content.count('{') != content.count('}'):
                self.add_warning("Unmatched braces in template - check f-string formatting")
                
            self.add_info("Cloud-init script syntax check passed")
            return True
            
        except Exception as e:
            self.add_error(f"Failed to read cloud-init script: {e}")
            return False
    
    def validate_generated_userdata(self, config) -> bool:
        """Generate and validate user-data content"""
        print("🔍 Validating generated user-data content...")
        
        try:
            # Import the module to test generation
            sys.path.insert(0, os.path.dirname(config.get('script_path', '')))
            from cloudinit import create_user_data_forced
            
            # Create a mock config object
            class MockConfig:
                def __init__(self):
                    self.vm_hostname = "test-validation"
                    self.go_version = "1.24.4"
                    
            mock_config = MockConfig()
            ssh_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ... test@example.com"
            
            # Generate user-data
            user_data = create_user_data_forced(mock_config, ssh_key)
            
            # Validate YAML syntax
            try:
                # Handle collections.Hashable deprecation issue
                import collections.abc
                if not hasattr(collections, 'Hashable'):
                    collections.Hashable = collections.abc.Hashable
                    
                yaml_content = yaml.safe_load(user_data)
                self.add_info("Generated user-data has valid YAML syntax")
            except (yaml.YAMLError, AttributeError) as e:
                # Try alternative validation method
                try:
                    import json
                    # Convert YAML to JSON as basic validation
                    yaml_content = yaml.safe_load(user_data)
                    self.add_info("Generated user-data has valid YAML syntax (alternative validation)")
                except Exception as e2:
                    self.add_error(f"Generated user-data has invalid YAML syntax: {e}")
                    return False
                
            # Check for problematic properties
            if 'datasource_list' in yaml_content:
                self.add_error("Generated user-data contains 'datasource_list' - this will cause validation errors")
                return False
                
            # Validate required sections
            required_sections = ['users', 'hostname', 'packages', 'runcmd']
            for section in required_sections:
                if section not in yaml_content:
                    self.add_warning(f"Missing recommended section: {section}")
                    
            # Check Docker installation
            runcmd = yaml_content.get('runcmd', [])
            has_docker_install = any('docker' in str(cmd).lower() for cmd in runcmd)
            if not has_docker_install:
                self.add_warning("No Docker installation commands found in runcmd")
                
            # Check Go installation  
            has_go_install = any('golang' in str(cmd) or '/usr/local/go' in str(cmd) for cmd in runcmd)
            if not has_go_install:
                self.add_warning("No Go installation commands found in runcmd")
                
            self.add_info("Generated user-data validation passed")
            return True
            
        except ImportError as e:
            self.add_error(f"Could not import cloud-init module: {e}")
            return False
        except Exception as e:
            self.add_error(f"Error validating generated user-data: {e}")
            return False
    
    def validate_with_cloudinit_schema(self, user_data_content: str) -> bool:
        """Validate using cloud-init's built-in schema validation"""
        print("🔍 Validating with cloud-init schema...")
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                f.write(user_data_content)
                temp_file = f.name
                
            # Run cloud-init schema validation
            result = subprocess.run([
                'cloud-init', 'schema', '--config-file', temp_file
            ], capture_output=True, text=True, timeout=30)
            
            # Cleanup
            os.unlink(temp_file)
            
            if result.returncode == 0:
                self.add_info("Cloud-init schema validation passed")
                return True
            else:
                self.add_error(f"Cloud-init schema validation failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.add_error("Cloud-init schema validation timed out")
            return False
        except FileNotFoundError:
            self.add_warning("cloud-init command not found - skipping schema validation")
            return True
        except Exception as e:
            self.add_error(f"Error running cloud-init schema validation: {e}")
            return False

class DeploymentValidator(CloudInitValidator):
    """Validates cloud-init on deployed VMs"""
    
    def __init__(self, vm_ip: str):
        super().__init__()
        self.vm_ip = vm_ip
        
    def test_ssh_connection(self) -> bool:
        """Test SSH connectivity to VM"""
        print(f"🔍 Testing SSH connection to {self.vm_ip}...")
        
        try:
            result = subprocess.run([
                'ssh', '-o', 'ConnectTimeout=5',
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                f'ubuntu@{self.vm_ip}', 'echo "SSH OK"'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.add_info("SSH connection successful")
                return True
            else:
                self.add_error(f"SSH connection failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.add_error("SSH connection timed out")
            return False
        except Exception as e:
            self.add_error(f"SSH connection error: {e}")
            return False
    
    def validate_cloudinit_status(self) -> bool:
        """Check cloud-init execution status"""
        print(f"🔍 Checking cloud-init status on {self.vm_ip}...")
        
        try:
            # Check cloud-init status
            result = subprocess.run([
                'ssh', '-o', 'ConnectTimeout=5',
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                f'ubuntu@{self.vm_ip}', 'cloud-init status --long'
            ], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                status_output = result.stdout.strip()
                
                if 'status: done' in status_output:
                    self.add_info("Cloud-init completed successfully")
                    return True
                elif 'status: running' in status_output:
                    self.add_warning("Cloud-init is still running")
                    return True
                elif 'status: not started' in status_output:
                    self.add_error("Cloud-init has not started - likely configuration error")
                    return False
                elif 'status: error' in status_output:
                    self.add_error("Cloud-init completed with errors")
                    return False
                else:
                    self.add_warning(f"Unknown cloud-init status: {status_output}")
                    return True
            else:
                self.add_error(f"Could not check cloud-init status: {result.stderr}")
                return False
                
        except Exception as e:
            self.add_error(f"Error checking cloud-init status: {e}")
            return False
    
    def validate_schema_compliance(self) -> bool:
        """Check for schema validation errors"""
        print(f"🔍 Checking schema compliance on {self.vm_ip}...")
        
        try:
            result = subprocess.run([
                'ssh', '-o', 'ConnectTimeout=5',
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                f'ubuntu@{self.vm_ip}', 'cloud-init schema --system'
            ], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                if 'Valid schema' in result.stdout:
                    self.add_info("Cloud-init schema validation passed")
                    return True
                else:
                    self.add_warning("Unexpected schema validation output")
                    return True
            else:
                error_output = result.stderr
                if 'datasource_list' in error_output:
                    self.add_error("Schema validation failed: datasource_list not allowed in user-data")
                    self.add_error("This VM was deployed with incorrect configuration")
                elif 'Invalid schema' in error_output:
                    self.add_error(f"Schema validation failed: {error_output}")
                else:
                    self.add_error(f"Schema validation error: {error_output}")
                return False
                
        except Exception as e:
            self.add_error(f"Error checking schema compliance: {e}")
            return False
    
    def validate_installations(self) -> bool:
        """Validate Docker and Go installations"""
        print(f"🔍 Validating installations on {self.vm_ip}...")
        
        success = True
        
        # Check Docker
        try:
            result = subprocess.run([
                'ssh', '-o', 'ConnectTimeout=5',
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                f'ubuntu@{self.vm_ip}', 'docker --version && systemctl is-active docker'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.add_info("Docker is installed and running")
            else:
                self.add_error("Docker is not properly installed or running")
                success = False
                
        except Exception as e:
            self.add_error(f"Error checking Docker: {e}")
            success = False
        
        # Check Go
        try:
            result = subprocess.run([
                'ssh', '-o', 'ConnectTimeout=5',
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                f'ubuntu@{self.vm_ip}', '/usr/local/go/bin/go version'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.add_info(f"Go is installed: {result.stdout.strip()}")
            else:
                self.add_error("Go is not properly installed")
                success = False
                
        except Exception as e:
            self.add_error(f"Error checking Go: {e}")
            success = False
            
        return success
    
    def validate_network_config(self) -> bool:
        """Validate network configuration"""
        print(f"🔍 Validating network configuration on {self.vm_ip}...")
        
        try:
            # Check hostname
            result = subprocess.run([
                'ssh', '-o', 'ConnectTimeout=5',
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                f'ubuntu@{self.vm_ip}', 'hostname'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                hostname = result.stdout.strip()
                if hostname.startswith('pentest-'):
                    self.add_info(f"Hostname correctly set: {hostname}")
                else:
                    self.add_warning(f"Unexpected hostname: {hostname}")
            else:
                self.add_warning("Could not check hostname")
                
            # Check network interfaces
            result = subprocess.run([
                'ssh', '-o', 'ConnectTimeout=5',
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                f'ubuntu@{self.vm_ip}', 'ip addr show | grep inet'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.add_info("Network interfaces configured")
            else:
                self.add_warning("Could not check network interfaces")
                
            return True
            
        except Exception as e:
            self.add_error(f"Error validating network config: {e}")
            return False

def validate_configuration(config_path: str = None) -> bool:
    """Validate cloud-init configuration before deployment"""
    validator = ConfigurationValidator()
    
    # Default paths
    if not config_path:
        config_path = "/Users/rwiggins/tools/newubuntu/modules/cloudinit.py"
    
    config = {
        'script_path': config_path
    }
    
    success = True
    
    # Validate main script
    if not validator.validate_cloudinit_script(config_path):
        success = False
    
    # Validate generated content
    if not validator.validate_generated_userdata(config):
        success = False
    
    return validator.print_results()

def validate_deployment(vm_ip: str) -> bool:
    """Validate cloud-init on a deployed VM"""
    validator = DeploymentValidator(vm_ip)
    
    success = True
    
    # Test SSH first
    if not validator.test_ssh_connection():
        return validator.print_results()
    
    # Validate cloud-init status
    if not validator.validate_cloudinit_status():
        success = False
    
    # Validate schema compliance
    if not validator.validate_schema_compliance():
        success = False
    
    # Validate installations
    if not validator.validate_installations():
        success = False
    
    # Validate network config
    if not validator.validate_network_config():
        success = False
    
    return validator.print_results()

def main():
    if len(sys.argv) < 2:
        print("Cloud-Init Configuration Validator")
        print("=" * 40)
        print()
        print("Usage:")
        print("  python3 validator.py config [script-path]     # Validate configuration")
        print("  python3 validator.py deploy <vm-ip>           # Validate deployment")
        print("  python3 validator.py both <vm-ip> [script]    # Validate both")
        print()
        print("Examples:")
        print("  python3 validator.py config")
        print("  python3 validator.py deploy 192.168.1.189")
        print("  python3 validator.py both 192.168.1.189")
        sys.exit(1)
    
    action = sys.argv[1].lower()
    
    if action == "config":
        script_path = sys.argv[2] if len(sys.argv) > 2 else None
        success = validate_configuration(script_path)
        sys.exit(0 if success else 1)
        
    elif action == "deploy":
        if len(sys.argv) < 3:
            print("❌ VM IP required for deployment validation")
            sys.exit(1)
        vm_ip = sys.argv[2]
        success = validate_deployment(vm_ip)
        sys.exit(0 if success else 1)
        
    elif action == "both":
        if len(sys.argv) < 3:
            print("❌ VM IP required for full validation")
            sys.exit(1)
        vm_ip = sys.argv[2]
        script_path = sys.argv[3] if len(sys.argv) > 3 else None
        
        print("🔍 Running full validation (configuration + deployment)...")
        config_success = validate_configuration(script_path)
        deploy_success = validate_deployment(vm_ip)
        
        print("\n" + "="*60)
        print("FULL VALIDATION SUMMARY")
        print("="*60)
        print(f"Configuration validation: {'✅ PASSED' if config_success else '❌ FAILED'}")
        print(f"Deployment validation:   {'✅ PASSED' if deploy_success else '❌ FAILED'}")
        
        success = config_success and deploy_success
        sys.exit(0 if success else 1)
        
    else:
        print(f"❌ Unknown action: {action}")
        sys.exit(1)

if __name__ == "__main__":
    main()
