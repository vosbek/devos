"""
Command validation for DevOS security
"""

import re
import logging
from typing import Dict, List, Any, Tuple
from pathlib import Path

class CommandValidator:
    """Validates commands for security and safety"""
    
    def __init__(self, security_config: Dict[str, Any]):
        self.security_config = security_config
        self.logger = logging.getLogger(__name__)
        
        # Command allowlists and blocklists
        self.allowed_commands = set(security_config.get('allowed_commands', [
            'ls', 'cp', 'mv', 'mkdir', 'rmdir', 'touch', 'cat', 'grep', 'find',
            'git', 'npm', 'pip', 'python', 'python3', 'node', 'docker',
            'kubectl', 'helm', 'terraform', 'aws'
        ]))
        
        self.blocked_commands = set(security_config.get('blocked_commands', [
            'rm -rf /', 'mkfs', 'dd', 'sudo rm -rf', 'chmod 777 /',
            'chown root /', 'init 0', 'shutdown', 'reboot'
        ]))
        
        # Dangerous patterns
        self.dangerous_patterns = [
            r'rm\s+-rf\s+/',           # rm -rf /
            r':\(\)\{\s*:\|:\&\s*\}',  # Fork bomb
            r'mkfs\.',                 # Format filesystem
            r'dd\s+if=/dev/zero',      # Zero out device
            r'>/dev/sd[a-z]',          # Write to disk device
            r'chmod\s+777\s+/',        # Make root world writable
            r'curl.*\|\s*sh',          # Pipe curl to shell
            r'wget.*\|\s*sh',          # Pipe wget to shell
            r'eval\s*\$\(',            # Eval with command substitution
        ]
        
        # Sensitive paths that should be protected
        self.protected_paths = [
            '/etc/passwd', '/etc/shadow', '/etc/sudoers',
            '/boot', '/sys', '/proc', '/dev',
            '/var/log', '/etc/ssh', '/root'
        ]
    
    async def validate_command(self, command_info: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a command for execution"""
        
        command = command_info.get('command', '')
        command_type = command_info.get('type', 'bash')
        safety_level = command_info.get('safety_level', 'safe')
        
        # Basic validation
        if not command or not command.strip():
            return {
                'valid': False,
                'reason': 'Empty command',
                'severity': 'low'
            }
        
        # Type-specific validation
        if command_type == 'bash':
            return await self._validate_bash_command(command, safety_level)
        elif command_type == 'python':
            return await self._validate_python_command(command, safety_level)
        elif command_type == 'sql':
            return await self._validate_sql_command(command, safety_level)
        else:
            return {
                'valid': False,
                'reason': f'Unsupported command type: {command_type}',
                'severity': 'medium'
            }
    
    async def _validate_bash_command(self, command: str, safety_level: str) -> Dict[str, Any]:
        """Validate a bash command"""
        
        # Check for blocked commands
        for blocked in self.blocked_commands:
            if blocked.lower() in command.lower():
                return {
                    'valid': False,
                    'reason': f'Blocked command pattern: {blocked}',
                    'severity': 'high'
                }
        
        # Check for dangerous patterns
        for pattern in self.dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return {
                    'valid': False,
                    'reason': f'Dangerous command pattern detected',
                    'severity': 'high'
                }
        
        # Extract and validate the main command
        main_command = self._extract_main_command(command)
        
        if main_command and main_command not in self.allowed_commands:
            return {
                'valid': False,
                'reason': f'Command not in allowlist: {main_command}',
                'severity': 'medium'
            }
        
        # Check for protected path access
        protected_path_risk = self._check_protected_paths(command)
        if protected_path_risk['risk']:
            if safety_level != 'destructive':
                return {
                    'valid': False,
                    'reason': f'Access to protected path: {protected_path_risk["path"]}',
                    'severity': 'high'
                }
        
        # Additional safety checks based on safety level
        if safety_level == 'destructive':
            # Destructive commands need extra validation
            destructive_risk = self._assess_destructive_risk(command)
            if destructive_risk['risk_level'] == 'extreme':
                return {
                    'valid': False,
                    'reason': f'Extremely destructive command: {destructive_risk["reason"]}',
                    'severity': 'critical'
                }
        
        # Command appears safe
        return {
            'valid': True,
            'reason': 'Command passed security validation',
            'severity': 'none',
            'warnings': self._generate_warnings(command, safety_level)
        }
    
    async def _validate_python_command(self, command: str, safety_level: str) -> Dict[str, Any]:
        """Validate a Python command"""
        
        # Check for dangerous Python operations
        dangerous_python = [
            'import os', 'import subprocess', 'import sys',
            'eval(', 'exec(', '__import__',
            'open(', 'file(', 'input(',
            'raw_input(', 'compile('
        ]
        
        for dangerous in dangerous_python:
            if dangerous in command:
                if safety_level != 'destructive':
                    return {
                        'valid': False,
                        'reason': f'Potentially dangerous Python operation: {dangerous}',
                        'severity': 'medium'
                    }
        
        return {
            'valid': True,
            'reason': 'Python command passed validation',
            'severity': 'none'
        }
    
    async def _validate_sql_command(self, command: str, safety_level: str) -> Dict[str, Any]:
        """Validate a SQL command"""
        
        # Check for dangerous SQL operations
        dangerous_sql = [
            'DROP TABLE', 'DROP DATABASE', 'DELETE FROM',
            'TRUNCATE', 'ALTER TABLE', 'UPDATE ',
            'INSERT INTO', 'CREATE USER', 'GRANT ALL'
        ]
        
        command_upper = command.upper()
        
        for dangerous in dangerous_sql:
            if dangerous in command_upper:
                if safety_level != 'destructive':
                    return {
                        'valid': False,
                        'reason': f'Potentially destructive SQL operation: {dangerous}',
                        'severity': 'high'
                    }
        
        return {
            'valid': True,
            'reason': 'SQL command passed validation',
            'severity': 'none'
        }
    
    def _extract_main_command(self, command: str) -> str:
        """Extract the main command from a complex command line"""
        
        # Handle command pipes, redirections, etc.
        command = command.strip()
        
        # Remove sudo if present
        if command.startswith('sudo '):
            command = command[5:].strip()
        
        # Split on pipes and take the first part
        if '|' in command:
            command = command.split('|')[0].strip()
        
        # Split on redirections
        for redirect in ['>', '>>', '<']:
            if redirect in command:
                command = command.split(redirect)[0].strip()
        
        # Extract the first word (the actual command)
        parts = command.split()
        if parts:
            return parts[0]
        
        return ''
    
    def _check_protected_paths(self, command: str) -> Dict[str, Any]:
        """Check if command accesses protected paths"""
        
        for protected_path in self.protected_paths:
            if protected_path in command:
                return {
                    'risk': True,
                    'path': protected_path,
                    'severity': 'high'
                }
        
        return {'risk': False}
    
    def _assess_destructive_risk(self, command: str) -> Dict[str, Any]:
        """Assess the destructive risk level of a command"""
        
        extreme_risk_patterns = [
            r'rm\s+-rf\s+/',
            r'rm\s+-rf\s+\*',
            r'rm\s+-rf\s+~',
            r'mkfs',
            r'dd\s+if=/dev/zero\s+of=/',
            r'chmod\s+000\s+/',
            r'chown\s+root:root\s+/'
        ]
        
        high_risk_patterns = [
            r'rm\s+-rf',
            r'rm\s+-r\s+\*',
            r'chmod\s+777',
            r'chown\s+.*\s+/'
        ]
        
        for pattern in extreme_risk_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return {
                    'risk_level': 'extreme',
                    'reason': 'Command could destroy system or critical data'
                }
        
        for pattern in high_risk_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return {
                    'risk_level': 'high',
                    'reason': 'Command could cause significant damage'
                }
        
        return {
            'risk_level': 'moderate',
            'reason': 'Command marked as destructive but appears manageable'
        }
    
    def _generate_warnings(self, command: str, safety_level: str) -> List[str]:
        """Generate warnings for potentially risky but allowed commands"""
        
        warnings = []
        
        # Check for commands that modify files
        if any(cmd in command for cmd in ['rm ', 'mv ', 'cp ']):
            warnings.append('Command modifies files')
        
        # Check for network operations
        if any(cmd in command for cmd in ['curl', 'wget', 'ssh', 'scp']):
            warnings.append('Command involves network operations')
        
        # Check for package management
        if any(cmd in command for cmd in ['pip install', 'npm install', 'apt install']):
            warnings.append('Command installs software packages')
        
        # Check for sudo usage
        if 'sudo' in command:
            warnings.append('Command uses elevated privileges')
        
        return warnings
    
    def is_safe_for_auto_approval(self, command_info: Dict[str, Any]) -> bool:
        """Determine if a command is safe for automatic approval"""
        
        command = command_info.get('command', '')
        safety_level = command_info.get('safety_level', 'safe')
        
        # Only safe commands can be auto-approved
        if safety_level != 'safe':
            return False
        
        # Check against known safe read-only operations
        safe_readonly_commands = [
            'ls', 'cat', 'grep', 'find', 'head', 'tail',
            'git status', 'git log', 'git show', 'git diff',
            'ps', 'top', 'df', 'du', 'free', 'uptime',
            'pwd', 'whoami', 'date', 'which', 'whereis'
        ]
        
        main_command = self._extract_main_command(command)
        
        # Check if it's a known safe command
        for safe_cmd in safe_readonly_commands:
            if command.strip().startswith(safe_cmd):
                return True
        
        # Default to requiring approval
        return False