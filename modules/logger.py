"""Simple logging functionality"""

class Logger:
    def __init__(self):
        # ANSI color codes
        self.GREEN = '\033[0;32m'
        self.YELLOW = '\033[1;33m'
        self.RED = '\033[0;31m'
        self.NC = '\033[0m'  # No Color
    
    def info(self, message):
        """Log info message"""
        print(f"{self.GREEN}[INFO]{self.NC} {message}")
    
    def warn(self, message):
        """Log warning message"""
        print(f"{self.YELLOW}[WARN]{self.NC} {message}")
    
    def error(self, message):
        """Log error message"""
        print(f"{self.RED}[ERROR]{self.NC} {message}")
    
    def status(self, message):
        """Log status without prefix"""
        print(message)
