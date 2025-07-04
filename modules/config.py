"""Configuration settings for VM deployment with .env support"""

import os
from datetime import datetime

class Config:
    def __init__(self):
        # Load environment variables from .env file
        self._load_env_file()
        
        # ESXi settings from environment
        self.esxi_host = os.getenv('ESXI_HOST', '192.168.1.248')
        self.esxi_user = os.getenv('ESXI_USER', 'root')
        self.esxi_password = os.getenv('ESXI_PASSWORD')
        
        if not self.esxi_password:
            raise ValueError("ESXI_PASSWORD not set in .env file")
        
        # VM specifications from environment
        self.vm_memory = os.getenv('VM_MEMORY', '8192')
        self.vm_cpu = os.getenv('VM_CPU', '8')
        self.vm_disk_size = os.getenv('VM_DISK_SIZE', '500')
        self.datastore = os.getenv('DATASTORE', '12TB')
        self.go_version = os.getenv('GO_VERSION', '1.24.4')
        
        # VM naming
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.vm_base_name = "ubuntu-pentest"
        self.vm_name = f"{self.vm_base_name}-{timestamp}"
        self.vm_hostname = f"pentest-{timestamp}"  # Unique hostname
        
        # Directories
        self.tools_dir = os.path.expanduser("~/tools/newubuntu")
        self.work_dir = os.path.join(self.tools_dir, "work")
        self.iso_dir = os.path.join(self.tools_dir, "iso")
        
        # Ubuntu image
        self.ubuntu_base_url = "https://cloud-images.ubuntu.com/oracular/current"
        self.ubuntu_ova = "oracular-server-cloudimg-amd64.ova"
        
        # Tool paths
        self.ovftool_bin = os.path.join(self.tools_dir, "ovftool", "ovftool")
        self.govc_bin = os.path.join(self.tools_dir, "govc", "govc")
        
        # SSH key path
        ssh_key_env = os.getenv('SSH_KEY_PATH')
        if ssh_key_env:
            self.ssh_key_path = os.path.expanduser(ssh_key_env)
        else:
            self.ssh_key_path = self._find_ssh_key()
    
    def _load_env_file(self):
        """Load environment variables from .env file"""
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
        
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
    
    def _find_ssh_key(self):
        """Find SSH public key"""
        keys = [
            os.path.expanduser("~/.ssh/id_rsa.pub"),
            os.path.expanduser("~/.ssh/id_ed25519.pub")
        ]
        for key in keys:
            if os.path.exists(key):
                return key
        return None
