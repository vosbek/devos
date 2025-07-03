"""
User preferences and learning system for DevOS
"""

import json
import logging
import hashlib
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

class UserPreferences:
    """Manages user preferences and learns from approval decisions"""
    
    def __init__(self, config_dir: str = "~/.devos"):
        self.config_dir = Path(config_dir).expanduser()
        self.preferences_file = self.config_dir / "preferences.json"
        self.logger = logging.getLogger(__name__)
        
        # In-memory preferences cache
        self.preferences = {}
        self.command_patterns = {}
        self.approval_history = []
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    async def load(self):
        """Load preferences from disk"""
        
        try:
            if self.preferences_file.exists():
                with open(self.preferences_file, 'r') as f:
                    data = json.load(f)
                    self.preferences = data.get('preferences', {})
                    self.command_patterns = data.get('command_patterns', {})
                    self.approval_history = data.get('approval_history', [])
                
                self.logger.info(f"Loaded preferences for {len(self.preferences)} users")
            else:
                self.logger.info("No existing preferences file found")
                
        except Exception as e:
            self.logger.error(f"Error loading preferences: {e}")
            # Initialize with empty preferences
            self.preferences = {}
            self.command_patterns = {}
            self.approval_history = []
    
    async def save(self):
        """Save preferences to disk"""
        
        try:
            data = {
                'preferences': self.preferences,
                'command_patterns': self.command_patterns,
                'approval_history': self.approval_history[-1000:],  # Keep last 1000 entries
                'last_updated': datetime.utcnow().isoformat()
            }
            
            with open(self.preferences_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info("Preferences saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving preferences: {e}")
    
    async def get_command_preference(self, user_id: str, command: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get user's preference for a specific command"""
        
        try:
            # Check for exact command match
            user_prefs = self.preferences.get(user_id, {})
            command_hash = self._hash_command(command)
            
            if command_hash in user_prefs:
                return user_prefs[command_hash]
            
            # Check for pattern matches
            pattern_match = self._find_pattern_match(user_id, command, context)
            if pattern_match:
                return pattern_match
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting command preference: {e}")
            return None
    
    async def learn_preference(self, user_id: str, command: str, context: Dict[str, Any], 
                             approved: bool, note: str = ""):
        """Learn from user's approval decision"""
        
        try:
            # Ensure user preferences exist
            if user_id not in self.preferences:
                self.preferences[user_id] = {}
            
            # Store specific command preference
            command_hash = self._hash_command(command)
            self.preferences[user_id][command_hash] = {
                'command': command,
                'approved': approved,
                'note': note,
                'learned_at': datetime.utcnow().isoformat(),
                'usage_count': self.preferences[user_id].get(command_hash, {}).get('usage_count', 0) + 1
            }
            
            # Learn command patterns
            await self._learn_command_pattern(user_id, command, context, approved)
            
            # Add to approval history
            self.approval_history.append({
                'user_id': user_id,
                'command': command,
                'approved': approved,
                'note': note,
                'timestamp': datetime.utcnow().isoformat(),
                'context': context
            })
            
            self.logger.info(f"Learned preference for user {user_id}: {command[:50]}... = {approved}")
            
        except Exception as e:
            self.logger.error(f"Error learning preference: {e}")
    
    async def _learn_command_pattern(self, user_id: str, command: str, context: Dict[str, Any], approved: bool):
        """Learn patterns from commands for better matching"""
        
        # Extract command components
        main_command = self._extract_main_command(command)
        command_args = self._extract_command_args(command)
        
        # Ensure user patterns exist
        if user_id not in self.command_patterns:
            self.command_patterns[user_id] = {}
        
        user_patterns = self.command_patterns[user_id]
        
        # Learn main command preference
        if main_command not in user_patterns:
            user_patterns[main_command] = {'approved': 0, 'rejected': 0, 'total': 0}
        
        if approved:
            user_patterns[main_command]['approved'] += 1
        else:
            user_patterns[main_command]['rejected'] += 1
        
        user_patterns[main_command]['total'] += 1
        
        # Learn argument patterns
        for arg in command_args:
            if arg.startswith('-'):  # Command flags
                flag_key = f"{main_command}_flag_{arg}"
                if flag_key not in user_patterns:
                    user_patterns[flag_key] = {'approved': 0, 'rejected': 0, 'total': 0}
                
                if approved:
                    user_patterns[flag_key]['approved'] += 1
                else:
                    user_patterns[flag_key]['rejected'] += 1
                
                user_patterns[flag_key]['total'] += 1
    
    def _find_pattern_match(self, user_id: str, command: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find matching patterns for a command"""
        
        if user_id not in self.command_patterns:
            return None
        
        user_patterns = self.command_patterns[user_id]
        main_command = self._extract_main_command(command)
        
        # Check main command pattern
        if main_command in user_patterns:
            pattern_data = user_patterns[main_command]
            
            # Calculate approval probability
            if pattern_data['total'] >= 3:  # Need at least 3 examples
                approval_rate = pattern_data['approved'] / pattern_data['total']
                
                if approval_rate >= 0.8:  # 80% approval rate
                    return {
                        'always_approve': True,
                        'confidence': approval_rate,
                        'based_on': f"Pattern match for '{main_command}' ({pattern_data['total']} examples)"
                    }
                elif approval_rate <= 0.2:  # 20% approval rate
                    return {
                        'always_deny': True,
                        'confidence': 1 - approval_rate,
                        'based_on': f"Pattern match for '{main_command}' ({pattern_data['total']} examples)"
                    }
        
        return None
    
    async def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get user's approval statistics"""
        
        user_prefs = self.preferences.get(user_id, {})
        user_patterns = self.command_patterns.get(user_id, {})
        
        # Count approvals and rejections
        approved_count = sum(1 for pref in user_prefs.values() if pref.get('approved', False))
        rejected_count = len(user_prefs) - approved_count
        
        # Get most common commands
        command_counts = {}
        for pref in user_prefs.values():
            cmd = self._extract_main_command(pref.get('command', ''))
            command_counts[cmd] = command_counts.get(cmd, 0) + 1
        
        most_common = sorted(command_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'total_preferences': len(user_prefs),
            'approved_count': approved_count,
            'rejected_count': rejected_count,
            'approval_rate': approved_count / len(user_prefs) if user_prefs else 0,
            'most_common_commands': most_common,
            'learned_patterns': len(user_patterns),
            'last_activity': max([pref.get('learned_at', '') for pref in user_prefs.values()]) if user_prefs else None
        }
    
    async def export_preferences(self, user_id: str, file_path: str):
        """Export user preferences to a file"""
        
        try:
            user_data = {
                'user_id': user_id,
                'preferences': self.preferences.get(user_id, {}),
                'patterns': self.command_patterns.get(user_id, {}),
                'statistics': await self.get_user_statistics(user_id),
                'exported_at': datetime.utcnow().isoformat()
            }
            
            with open(file_path, 'w') as f:
                json.dump(user_data, f, indent=2)
            
            self.logger.info(f"Exported preferences for {user_id} to {file_path}")
            
        except Exception as e:
            self.logger.error(f"Error exporting preferences: {e}")
            raise
    
    async def import_preferences(self, file_path: str):
        """Import user preferences from a file"""
        
        try:
            with open(file_path, 'r') as f:
                user_data = json.load(f)
            
            user_id = user_data['user_id']
            
            # Merge preferences
            if user_id not in self.preferences:
                self.preferences[user_id] = {}
            
            self.preferences[user_id].update(user_data.get('preferences', {}))
            
            # Merge patterns
            if user_id not in self.command_patterns:
                self.command_patterns[user_id] = {}
            
            self.command_patterns[user_id].update(user_data.get('patterns', {}))
            
            self.logger.info(f"Imported preferences for {user_id} from {file_path}")
            
        except Exception as e:
            self.logger.error(f"Error importing preferences: {e}")
            raise
    
    def _hash_command(self, command: str) -> str:
        """Create a hash for a command for consistent storage"""
        
        # Normalize command (remove extra whitespace, etc.)
        normalized = ' '.join(command.split())
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]
    
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
    
    def _extract_command_args(self, command: str) -> List[str]:
        """Extract command arguments"""
        
        # Clean the command
        command = command.strip()
        
        # Remove sudo if present
        if command.startswith('sudo '):
            command = command[5:].strip()
        
        # Split and return arguments (skip the command itself)
        parts = command.split()
        return parts[1:] if len(parts) > 1 else []
    
    async def clear_user_preferences(self, user_id: str):
        """Clear all preferences for a user"""
        
        if user_id in self.preferences:
            del self.preferences[user_id]
        
        if user_id in self.command_patterns:
            del self.command_patterns[user_id]
        
        # Remove from approval history
        self.approval_history = [
            entry for entry in self.approval_history 
            if entry.get('user_id') != user_id
        ]
        
        self.logger.info(f"Cleared all preferences for user {user_id}")
    
    async def get_global_statistics(self) -> Dict[str, Any]:
        """Get global statistics across all users"""
        
        total_users = len(self.preferences)
        total_preferences = sum(len(user_prefs) for user_prefs in self.preferences.values())
        
        # Most common commands across all users
        all_commands = {}
        for user_prefs in self.preferences.values():
            for pref in user_prefs.values():
                cmd = self._extract_main_command(pref.get('command', ''))
                all_commands[cmd] = all_commands.get(cmd, 0) + 1
        
        most_common_global = sorted(all_commands.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'total_users': total_users,
            'total_preferences': total_preferences,
            'total_patterns': sum(len(patterns) for patterns in self.command_patterns.values()),
            'total_approval_history': len(self.approval_history),
            'most_common_commands_global': most_common_global,
            'average_preferences_per_user': total_preferences / total_users if total_users > 0 else 0
        }