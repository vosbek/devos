"""
Risk assessment engine for DevOS commands
"""

import re
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

class RiskAssessment:
    """Assesses risk levels for commands and operations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Risk level definitions
        self.risk_levels = {
            'safe': 0,
            'low': 1,
            'medium': 2,
            'high': 3,
            'critical': 4
        }
        
        # Command risk mappings
        self.command_risks = {
            # Safe read-only commands
            'ls': 'safe', 'cat': 'safe', 'grep': 'safe', 'find': 'safe',
            'head': 'safe', 'tail': 'safe', 'pwd': 'safe', 'whoami': 'safe',
            'date': 'safe', 'uptime': 'safe', 'which': 'safe', 'whereis': 'safe',
            
            # Low risk commands
            'mkdir': 'low', 'touch': 'low', 'cp': 'low', 'mv': 'low',
            'git status': 'low', 'git log': 'low', 'git show': 'low',
            
            # Medium risk commands
            'rm': 'medium', 'rmdir': 'medium', 'chmod': 'medium', 'chown': 'medium',
            'git add': 'medium', 'git commit': 'medium', 'git push': 'medium',
            'pip install': 'medium', 'npm install': 'medium',
            
            # High risk commands
            'sudo': 'high', 'su': 'high', 'passwd': 'high',
            'systemctl': 'high', 'service': 'high',
            'iptables': 'high', 'ufw': 'high',
            
            # Critical risk commands
            'dd': 'critical', 'mkfs': 'critical', 'fdisk': 'critical',
            'cfdisk': 'critical', 'parted': 'critical'
        }
        
        # High-risk patterns
        self.high_risk_patterns = [
            r'rm\s+-rf\s+/',           # Remove root directory
            r'rm\s+-rf\s+\*',          # Remove everything
            r'>\s*/dev/sd[a-z]',       # Write to disk device
            r'chmod\s+777\s+/',        # World writable root
            r'chown\s+.*\s+/',         # Change ownership of root
            r'curl.*\|\s*sh',          # Pipe download to shell
            r'wget.*\|\s*sh',          # Pipe download to shell
            r':\(\)\{\s*:\|:\&\s*\}',  # Fork bomb
        ]
        
        # Critical system paths
        self.critical_paths = [
            '/boot', '/sys', '/proc', '/dev',
            '/etc/passwd', '/etc/shadow', '/etc/sudoers',
            '/var/log', '/etc/ssh', '/root'
        ]
    
    async def assess_command_risk(self, command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the risk level of a command"""
        
        try:
            # Basic command analysis
            base_risk = self._assess_base_command_risk(command)
            
            # Pattern analysis
            pattern_risk = self._assess_pattern_risk(command)
            
            # Context analysis
            context_risk = self._assess_context_risk(command, context)
            
            # Path analysis
            path_risk = self._assess_path_risk(command)
            
            # Calculate overall risk
            overall_risk = max(base_risk, pattern_risk, context_risk, path_risk)
            
            # Generate risk assessment
            assessment = {
                'level': self._risk_level_name(overall_risk),
                'score': overall_risk,
                'factors': {
                    'base_command': self._risk_level_name(base_risk),
                    'patterns': self._risk_level_name(pattern_risk),
                    'context': self._risk_level_name(context_risk),
                    'paths': self._risk_level_name(path_risk)
                },
                'reasons': self._generate_risk_reasons(command, overall_risk),
                'recommendations': self._generate_recommendations(command, overall_risk)
            }
            
            return assessment
            
        except Exception as e:
            self.logger.error(f"Error assessing command risk: {e}")
            return {
                'level': 'medium',
                'score': 2,
                'factors': {'error': 'Assessment failed'},
                'reasons': ['Risk assessment failed, defaulting to medium risk'],
                'recommendations': ['Manual review required']
            }
    
    def _assess_base_command_risk(self, command: str) -> int:
        """Assess risk based on the base command"""
        
        # Extract the main command
        main_command = self._extract_main_command(command)
        
        if not main_command:
            return 1  # Low risk for empty/unknown commands
        
        # Check direct command mappings
        if main_command in self.command_risks:
            return self.risk_levels[self.command_risks[main_command]]
        
        # Check for sudo prefix
        if command.strip().startswith('sudo '):
            return max(3, self._assess_base_command_risk(command[5:]))  # High risk minimum
        
        # Default to medium risk for unknown commands
        return 2
    
    def _assess_pattern_risk(self, command: str) -> int:
        """Assess risk based on dangerous patterns"""
        
        max_risk = 0
        
        for pattern in self.high_risk_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                max_risk = max(max_risk, 4)  # Critical risk
        
        # Additional pattern checks
        if '|' in command and any(shell in command for shell in ['sh', 'bash', 'zsh']):
            max_risk = max(max_risk, 3)  # High risk for piped shell commands
        
        if re.search(r'eval\s*\$\(', command):
            max_risk = max(max_risk, 3)  # High risk for eval
        
        return max_risk
    
    def _assess_context_risk(self, command: str, context: Dict[str, Any]) -> int:
        """Assess risk based on execution context"""
        
        risk = 0
        
        # Check current directory
        current_dir = context.get('current_directory', '')
        if current_dir in ['/boot', '/sys', '/proc', '/dev', '/etc']:
            risk = max(risk, 3)  # High risk in system directories
        
        # Check if running as root
        if context.get('user') == 'root':
            risk = max(risk, 2)  # Medium risk when running as root
        
        # Check recent command history
        recent_commands = context.get('recent_commands', [])
        if any('sudo' in cmd for cmd in recent_commands[-5:]):
            risk = max(risk, 1)  # Low risk if recent sudo usage
        
        return risk
    
    def _assess_path_risk(self, command: str) -> int:
        """Assess risk based on paths mentioned in command"""
        
        max_risk = 0
        
        for critical_path in self.critical_paths:
            if critical_path in command:
                if any(op in command for op in ['rm', 'mv', 'cp', 'chmod', 'chown']):
                    max_risk = max(max_risk, 4)  # Critical risk
                else:
                    max_risk = max(max_risk, 2)  # Medium risk for read access
        
        return max_risk
    
    def _extract_main_command(self, command: str) -> str:
        """Extract the main command from a complex command line"""
        
        # Clean the command
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
        
        # Extract the first word
        parts = command.split()
        if parts:
            return parts[0]
        
        return ''
    
    def _risk_level_name(self, risk_score: int) -> str:
        """Convert risk score to level name"""
        
        for level, score in self.risk_levels.items():
            if score == risk_score:
                return level
        
        return 'unknown'
    
    def _generate_risk_reasons(self, command: str, risk_score: int) -> List[str]:
        """Generate human-readable reasons for the risk assessment"""
        
        reasons = []
        
        if risk_score >= 4:
            reasons.append("Command could cause irreversible system damage")
        elif risk_score >= 3:
            reasons.append("Command requires elevated privileges or system access")
        elif risk_score >= 2:
            reasons.append("Command modifies files or system state")
        elif risk_score >= 1:
            reasons.append("Command has minor side effects")
        else:
            reasons.append("Command appears safe for execution")
        
        # Add specific reasons based on command content
        if 'rm' in command:
            reasons.append("Command deletes files or directories")
        
        if 'sudo' in command:
            reasons.append("Command uses elevated privileges")
        
        if any(path in command for path in self.critical_paths):
            reasons.append("Command accesses critical system paths")
        
        return reasons
    
    def _generate_recommendations(self, command: str, risk_score: int) -> List[str]:
        """Generate recommendations based on risk assessment"""
        
        recommendations = []
        
        if risk_score >= 4:
            recommendations.extend([
                "Consider alternatives to this command",
                "Review command carefully before execution",
                "Ensure you have system backups",
                "Consider running in a test environment first"
            ])
        elif risk_score >= 3:
            recommendations.extend([
                "Review command parameters carefully",
                "Ensure you have necessary permissions",
                "Consider the impact on system stability"
            ])
        elif risk_score >= 2:
            recommendations.extend([
                "Verify target files/directories exist",
                "Consider backing up affected files"
            ])
        elif risk_score >= 1:
            recommendations.append("Command should be safe to execute")
        
        return recommendations
    
    def is_auto_approvable(self, command: str, context: Dict[str, Any]) -> bool:
        """Determine if command can be automatically approved"""
        
        assessment = self.assess_command_risk(command, context)
        return assessment['score'] <= 0  # Only 'safe' commands