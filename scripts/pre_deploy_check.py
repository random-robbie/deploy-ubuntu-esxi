#!/usr/bin/env python3
"""
Pre-deployment validation hook
Automatically validates cloud-init configuration before deployment
"""

import sys
import os
import subprocess

def run_validation():
    """Run configuration validation before deployment"""
    print("🔍 Running pre-deployment validation...")
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    validator_path = os.path.join(script_dir, 'validator.py')
    
    try:
        result = subprocess.run([
            'python3', validator_path, 'config'
        ], capture_output=False, timeout=60)
        
        if result.returncode == 0:
            print("\n✅ Pre-deployment validation PASSED - proceeding with deployment")
            return True
        else:
            print("\n❌ Pre-deployment validation FAILED - deployment blocked")
            print("Please fix the configuration issues above before deploying")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Validation timed out")
        return False
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False

if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)
