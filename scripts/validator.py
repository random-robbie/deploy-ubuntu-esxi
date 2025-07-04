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
import importlib.util
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

            # Regex check for datasource_list
            if re.search(r'datasource_list\s*:\s*\[\s*["\']NoCloud["\']\s*,\s*["\']None["\']\s*\]', content):
                self.add_error("Found 'datasource_list' in user-data template - this will cause schema validation errors")
                self.add_error("Remove datasource_list from user-data - it belongs in system config only")

            # Check for required function definitions
            required_functions = ['create_user_data_forced', 'create_meta_data', 'create_network_config']
            for func in required_functions:
                if f"def {func}" not in content:
                    self.add_error(f"Missing required function: {func}")

            if '#cloud-config' not in content:
                self.add_warning("Cloud-config header not found in template")

            open_brace = content.count('{')
            close_brace = content.count('}')
            if open_brace != close_brace:
                self.add_warning("Unmatched braces detected - this might indicate f-string formatting issues")

            self.add_info("Cloud-init script syntax check passed")
            return True

        except Exception as e:
            self.add_error(f"Failed to read cloud-init script: {e}")
            return False

    def validate_generated_userdata(self, config) -> bool:
        """Generate and validate user-data content"""
        print("🔍 Validating generated user-data content...")

        try:
            script_path = config.get('script_path', '')
            if not os.path.exists(script_path):
                self.add_error(f"Script path not found: {script_path}")
                return False

            module_name = "user_cloudinit_module"
            spec = importlib.util.spec_from_file_location(module_name, script_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if not hasattr(module, 'create_user_data_forced'):
                self.add_error("Missing required function: create_user_data_forced")
                return False

            class MockConfig:
                def __init__(self):
                    self.vm_hostname = "test-validation"
                    self.go_version = "1.24.4"

            mock_config = MockConfig()
            ssh_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ... test@example.com"
            user_data = module.create_user_data_forced(mock_config, ssh_key)

            try:
                yaml_content = yaml.safe_load(user_data)
                self.add_info("Generated user-data has valid YAML syntax")
            except yaml.YAMLError as e:
                self.add_error(f"Generated user-data has invalid YAML syntax: {e}")
                return False

            if 'datasource_list' in yaml_content:
                self.add_error("Generated user-data contains 'datasource_list' - this will cause validation errors")
                return False

            required_sections = ['users', 'hostname', 'packages', 'runcmd']
            for section in required_sections:
                if section not in yaml_content:
                    self.add_warning(f"Missing recommended section: {section}")

            runcmd = yaml_content.get('runcmd', [])
            if not any('docker' in str(cmd).lower() for cmd in runcmd):
                self.add_warning("No Docker installation commands found in runcmd")

            if not any('golang' in str(cmd) or '/usr/local/go' in str(cmd) for cmd in runcmd):
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
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                f.write(user_data_content)
                temp_file = f.name

            result = subprocess.run([
                'cloud-init', 'schema', '--config-file', temp_file
            ], capture_output=True, text=True, timeout=30)

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

    def _run_ssh_command(self, command: str) -> subprocess.CompletedProcess:
        ssh_command = [
            'ssh', '-o', 'ConnectTimeout=5',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'ubuntu@{self.vm_ip}', command
        ]
        return subprocess.run(
            ssh_command, capture_output=True, text=True, timeout=15
        )

    def test_ssh_connection(self) -> bool:
        print(f"🔍 Testing SSH connection to {self.vm_ip}...")

        try:
            result = self._run_ssh_command('echo "SSH OK"')
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
        print(f"🔍 Checking cloud-init status on {self.vm_ip}...")

        try:
            result = self._run_ssh_command('sudo cloud-init status --long')
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
                    log_result = self._run_ssh_command('sudo cat /var/log/cloud-init.log')
                    if log_result.returncode == 0:
                        log_content = log_result.stdout
                        self.add_info(f"Full cloud-init.log content:\n{log_content}")
                        if "apt-get update failed" in log_content or "Failed to fetch" in log_content:
                            self.add_error("Cloud-init log indicates apt-get update failed. Check network or repository configuration.")
                            self.add_info("Attempting network connectivity check on VM...")
                            ping_result = self._run_ssh_command('ping -c 4 google.com')
                            if ping_result.returncode == 0:
                                self.add_info("VM can ping google.com. Network connectivity seems okay.")
                            else:
                                self.add_error(f"VM cannot ping google.com. Network connectivity issue: {ping_result.stderr}")
                            dig_result = self._run_ssh_command('dig +short google.com')
                            if dig_result.returncode == 0 and dig_result.stdout.strip():
                                self.add_info(f"VM can resolve google.com. DNS resolution seems okay. IP: {dig_result.stdout.strip()}")
                            else:
                                self.add_error(f"VM cannot resolve google.com. DNS resolution issue: {dig_result.stderr}")
                        if "Error running command" in log_content:
                            self.add_error("Cloud-init log indicates an error running a command. Check user-data scripts.")
                        if "eatmydata" in log_content:
                            self.add_error("Cloud-init log indicates 'eatmydata' command failed. This might be related to apt issues.")
                    else:
                        self.add_warning(f"Could not read cloud-init.log: {log_result.stderr}")
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
