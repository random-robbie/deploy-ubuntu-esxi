#!/usr/bin/env python3
"""
Comprehensive Cloud-Init Testing Suite
Tests all aspects of cloud-init configuration and deployment
"""

import sys
import os
import subprocess
import tempfile

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

def test_configuration_validation():
    """Test configuration validation"""
    print("🧪 Testing Configuration Validation")
    print("-" * 40)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    validator_path = os.path.join(script_dir, 'validator.py')
    
    try:
        result = subprocess.run([
            'python3', validator_path, 'config'
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Configuration validation test PASSED")
            return True
        else:
            print("❌ Configuration validation test FAILED")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Configuration validation test ERROR: {e}")
        return False

def test_yaml_generation():
    """Test YAML generation and syntax"""
    print("\n🧪 Testing YAML Generation")
    print("-" * 40)
    
    try:
        # Import the module
        sys.path.insert(0, '/Users/rwiggins/tools/newubuntu/modules')
        from cloudinit import create_user_data_forced, create_meta_data, create_network_config
        
        # Create mock config
        class MockConfig:
            def __init__(self):
                self.vm_hostname = "test-validation-vm"
                self.go_version = "1.24.4"
        
        mock_config = MockConfig()
        ssh_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ... test@example.com"
        
        # Test user-data generation
        print("Testing user-data generation...")
        user_data = create_user_data_forced(mock_config, ssh_key)
        
        # Validate YAML syntax
        try:
            yaml_content = yaml.safe_load(user_data)
            print("✅ User-data YAML syntax is valid")
        except yaml.YAMLError as e:
            print(f"❌ User-data YAML syntax error: {e}")
            return False
        
        # Check for problematic elements
        if 'datasource_list' in yaml_content:
            print("❌ Found 'datasource_list' in user-data (will cause schema errors)")
            return False
        else:
            print("✅ No 'datasource_list' found in user-data")
        
        # Test meta-data generation
        print("Testing meta-data generation...")
        meta_data = create_meta_data(mock_config)
        meta_yaml = yaml.safe_load(meta_data)
        print("✅ Meta-data generation successful")
        
        # Test network-config generation
        print("Testing network-config generation...")
        network_config = create_network_config()
        network_yaml = yaml.safe_load(network_config)
        print("✅ Network-config generation successful")
        
        # Validate required sections
        required_sections = ['users', 'hostname', 'packages', 'runcmd']
        missing_sections = []
        for section in required_sections:
            if section not in yaml_content:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"⚠️  Missing recommended sections: {missing_sections}")
        else:
            print("✅ All recommended sections present")
        
        # Check for Docker installation
        runcmd = yaml_content.get('runcmd', [])
        has_docker = any('docker' in str(cmd).lower() for cmd in runcmd)
        if has_docker:
            print("✅ Docker installation found in runcmd")
        else:
            print("❌ No Docker installation found in runcmd")
            return False
        
        # Check for Go installation
        has_go = any('golang' in str(cmd) or '/usr/local/go' in str(cmd) for cmd in runcmd)
        if has_go:
            print("✅ Go installation found in runcmd")
        else:
            print("❌ No Go installation found in runcmd")
            return False
        
        print("✅ YAML generation test PASSED")
        return True
        
    except ImportError as e:
        print(f"❌ Could not import cloudinit module: {e}")
        return False
    except Exception as e:
        print(f"❌ YAML generation test ERROR: {e}")
        return False

def test_schema_validation():
    """Test cloud-init schema validation"""
    print("\n🧪 Testing Schema Validation")
    print("-" * 40)
    
    try:
        # Generate a test cloud-config
        sys.path.insert(0, '/Users/rwiggins/tools/newubuntu/modules')
        from cloudinit import create_user_data_forced
        
        class MockConfig:
            def __init__(self):
                self.vm_hostname = "test-schema-vm"
                self.go_version = "1.24.4"
        
        mock_config = MockConfig()
        ssh_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ... test@example.com"
        user_data = create_user_data_forced(mock_config, ssh_key)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(user_data)
            temp_file = f.name
        
        try:
            # Test with cloud-init schema if available
            result = subprocess.run([
                'cloud-init', 'schema', '--config-file', temp_file
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ Cloud-init schema validation PASSED")
                return True
            else:
                print(f"❌ Cloud-init schema validation FAILED: {result.stderr}")
                return False
                
        except FileNotFoundError:
            print("⚠️  cloud-init command not found - skipping schema validation")
            return True
        finally:
            os.unlink(temp_file)
            
    except Exception as e:
        print(f"❌ Schema validation test ERROR: {e}")
        return False

def test_deployment_if_available():
    """Test deployment validation if a VM IP is provided"""
    print("\n🧪 Testing Deployment Validation")
    print("-" * 40)
    
    if len(sys.argv) > 1:
        vm_ip = sys.argv[1]
        print(f"Testing deployment validation for VM: {vm_ip}")
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        validator_path = os.path.join(script_dir, 'validator.py')
        
        try:
            result = subprocess.run([
                'python3', validator_path, 'deploy', vm_ip
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print("✅ Deployment validation test PASSED")
                return True
            else:
                print("❌ Deployment validation test FAILED")
                print(result.stdout)
                return False
                
        except Exception as e:
            print(f"❌ Deployment validation test ERROR: {e}")
            return False
    else:
        print("⚠️  No VM IP provided - skipping deployment validation test")
        print("   To test deployment validation, run: python3 test_suite.py <vm-ip>")
        return True

def test_file_permissions():
    """Test that all scripts have proper permissions"""
    print("\n🧪 Testing File Permissions")
    print("-" * 40)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    scripts_to_check = [
        'validator.py',
        'pre_deploy_check.py', 
        'post_deploy_check.py',
        'test_suite.py',
        'troubleshoot_installations.py',
        'fixes/fix_cloud_init_schema.py',
        'fixes/complete_fix.py'
    ]
    
    all_good = True
    for script in scripts_to_check:
        script_path = os.path.join(script_dir, script)
        if os.path.exists(script_path):
            if os.access(script_path, os.X_OK):
                print(f"✅ {script} is executable")
            else:
                print(f"❌ {script} is NOT executable")
                all_good = False
        else:
            print(f"⚠️  {script} not found")
    
    return all_good

def test_dependencies():
    """Test required dependencies"""
    print("\n🧪 Testing Dependencies")
    print("-" * 40)
    
    dependencies = [
        ('python3', 'python3 --version'),
        ('yaml', ['python3', '-c', 'import collections.abc; import collections; collections.Hashable = collections.abc.Hashable; import yaml; print(yaml.__version__)']),
        ('ssh', 'ssh -V')
    ]
    
    all_good = True
    for name, cmd in dependencies:
        try:
            if isinstance(cmd, list):
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            else:
                result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ {name} is available")
            else:
                print(f"❌ {name} test failed")
                all_good = False
        except Exception as e:
            print(f"❌ {name} not available: {e}")
            all_good = False
    
    return all_good

def run_comprehensive_test():
    """Run all tests"""
    print("🚀 Cloud-Init Comprehensive Test Suite")
    print("=" * 50)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("File Permissions", test_file_permissions),
        ("Configuration Validation", test_configuration_validation),
        ("YAML Generation", test_yaml_generation),
        ("Schema Validation", test_schema_validation),
        ("Deployment Validation", test_deployment_if_available)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:25} {status}")
        if result:
            passed += 1
    
    print("\n" + "-" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Your cloud-init setup is working correctly!")
        return True
    else:
        print("❌ SOME TESTS FAILED - Please fix the issues above")
        return False

def main():
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        print("Cloud-Init Test Suite")
        print("Usage:")
        print("  python3 test_suite.py           # Run all tests except deployment")
        print("  python3 test_suite.py <vm-ip>   # Run all tests including deployment")
        print("")
        print("Examples:")
        print("  python3 test_suite.py")
        print("  python3 test_suite.py 192.168.1.189")
        sys.exit(0)
    
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
