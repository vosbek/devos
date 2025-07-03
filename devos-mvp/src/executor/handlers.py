"""
Command handlers for specific operations in DevOS
"""

import logging
import os
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path

from ..daemon.models import CommandResult

class CommandHandler:
    """Handles specific types of commands with specialized logic"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Handler mapping
        self.handlers = {
            'file_operation': self.handle_file_operation,
            'git_operation': self.handle_git_operation,
            'process_management': self.handle_process_management,
            'system_query': self.handle_system_query
        }
    
    async def handle_command(self, command_info: Dict[str, Any]) -> CommandResult:
        """Route command to appropriate handler"""
        
        command_type = self._classify_command(command_info.get('command', ''))
        handler = self.handlers.get(command_type, self.handle_generic_command)
        
        try:
            return await handler(command_info)
        except Exception as e:
            self.logger.error(f"Error in command handler {command_type}: {e}")
            return CommandResult(
                success=False,
                error=f"Handler error: {str(e)}"
            )
    
    def _classify_command(self, command: str) -> str:
        """Classify command type based on content"""
        
        command_lower = command.lower().strip()
        
        # File operations
        file_ops = ['ls', 'cp', 'mv', 'mkdir', 'rmdir', 'touch', 'find', 'grep']
        if any(op in command_lower for op in file_ops):
            return 'file_operation'
        
        # Git operations
        if command_lower.startswith('git '):
            return 'git_operation'
        
        # Process management
        process_ops = ['ps', 'kill', 'killall', 'top', 'htop', 'jobs']
        if any(op in command_lower for op in process_ops):
            return 'process_management'
        
        # System queries
        query_ops = ['whoami', 'pwd', 'date', 'uptime', 'free', 'df', 'uname']
        if any(op in command_lower for op in query_ops):
            return 'system_query'
        
        return 'generic'
    
    async def handle_file_operation(self, command_info: Dict[str, Any]) -> CommandResult:
        """Handle file operations with enhanced feedback"""
        
        command = command_info.get('command', '')
        
        try:
            # Parse file operation
            operation_type = self._parse_file_operation(command)
            
            # Execute the command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            stdout, stderr = await process.communicate()
            
            output = stdout.decode('utf-8', errors='replace').strip()
            error = stderr.decode('utf-8', errors='replace').strip()
            
            # Enhanced output formatting for file operations
            if operation_type == 'list':
                output = self._format_list_output(output, command)
            elif operation_type == 'find':
                output = self._format_find_output(output, command)
            
            # Detect affected files
            affected_files = self._detect_file_changes(command, operation_type)
            
            return CommandResult(
                success=process.returncode == 0,
                output=output,
                error=error,
                exit_code=process.returncode,
                commands_executed=[command],
                files_affected=affected_files
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"File operation failed: {str(e)}"
            )
    
    async def handle_git_operation(self, command_info: Dict[str, Any]) -> CommandResult:
        """Handle git operations with enhanced context"""
        
        command = command_info.get('command', '')
        
        try:
            # Check if we're in a git repository
            git_check = await asyncio.create_subprocess_shell(
                'git rev-parse --git-dir',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await git_check.communicate()
            
            if git_check.returncode != 0:
                return CommandResult(
                    success=False,
                    error="Not in a git repository"
                )
            
            # Execute git command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            stdout, stderr = await process.communicate()
            
            output = stdout.decode('utf-8', errors='replace').strip()
            error = stderr.decode('utf-8', errors='replace').strip()
            
            # Enhance git output
            if 'git status' in command:
                output = self._format_git_status(output)
            elif 'git log' in command:
                output = self._format_git_log(output)
            
            return CommandResult(
                success=process.returncode == 0,
                output=output,
                error=error,
                exit_code=process.returncode,
                commands_executed=[command]
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Git operation failed: {str(e)}"
            )
    
    async def handle_process_management(self, command_info: Dict[str, Any]) -> CommandResult:
        """Handle process management operations"""
        
        command = command_info.get('command', '')
        
        try:
            # Add safety checks for process operations
            if 'kill' in command and '-9' in command:
                # Warn about force killing
                command_info['warning'] = "Force killing processes (kill -9)"
            
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            output = stdout.decode('utf-8', errors='replace').strip()
            error = stderr.decode('utf-8', errors='replace').strip()
            
            # Format process output
            if command.startswith('ps '):
                output = self._format_process_output(output)
            
            return CommandResult(
                success=process.returncode == 0,
                output=output,
                error=error,
                exit_code=process.returncode,
                commands_executed=[command]
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Process operation failed: {str(e)}"
            )
    
    async def handle_system_query(self, command_info: Dict[str, Any]) -> CommandResult:
        """Handle system information queries"""
        
        command = command_info.get('command', '')
        
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            output = stdout.decode('utf-8', errors='replace').strip()
            error = stderr.decode('utf-8', errors='replace').strip()
            
            # Add helpful context to system queries
            if command == 'pwd':
                current_dir = Path.cwd()
                output += f"\nCurrent directory: {current_dir.name}"
                if current_dir.parent != current_dir:
                    output += f"\nParent directory: {current_dir.parent}"
            
            elif command in ['df', 'df -h']:
                output += "\nDisk usage summary for current system"
            
            return CommandResult(
                success=process.returncode == 0,
                output=output,
                error=error,
                exit_code=process.returncode,
                commands_executed=[command]
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"System query failed: {str(e)}"
            )
    
    async def handle_generic_command(self, command_info: Dict[str, Any]) -> CommandResult:
        """Handle generic commands that don't fit other categories"""
        
        command = command_info.get('command', '')
        
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            stdout, stderr = await process.communicate()
            
            output = stdout.decode('utf-8', errors='replace').strip()
            error = stderr.decode('utf-8', errors='replace').strip()
            
            return CommandResult(
                success=process.returncode == 0,
                output=output,
                error=error,
                exit_code=process.returncode,
                commands_executed=[command]
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Command execution failed: {str(e)}"
            )
    
    def _parse_file_operation(self, command: str) -> str:
        """Parse the type of file operation"""
        
        if command.startswith('ls'):
            return 'list'
        elif command.startswith('find'):
            return 'find'
        elif command.startswith('cp'):
            return 'copy'
        elif command.startswith('mv'):
            return 'move'
        elif command.startswith('rm'):
            return 'remove'
        elif command.startswith('mkdir'):
            return 'create_dir'
        elif command.startswith('touch'):
            return 'create_file'
        else:
            return 'other'
    
    def _format_list_output(self, output: str, command: str) -> str:
        """Format ls command output with helpful information"""
        
        if not output:
            return "Directory is empty"
        
        lines = output.strip().split('\n')
        
        # Add summary for long listings
        if '-l' in command:
            file_count = len([line for line in lines if not line.startswith('total')])
            header = f"Found {file_count} items:\n"
            return header + output
        else:
            # Simple listing - add count
            items = [item for line in lines for item in line.split() if item]
            return f"Found {len(items)} items:\n{output}"
    
    def _format_find_output(self, output: str, command: str) -> str:
        """Format find command output"""
        
        if not output:
            return "No files found matching criteria"
        
        lines = output.strip().split('\n')
        return f"Found {len(lines)} matching files:\n{output}"
    
    def _format_git_status(self, output: str) -> str:
        """Format git status output with helpful summary"""
        
        if 'nothing to commit' in output:
            return "✓ Git repository is clean (no changes)\n\n" + output
        else:
            return "⚠ Git repository has changes:\n\n" + output
    
    def _format_git_log(self, output: str) -> str:
        """Format git log output"""
        
        if not output:
            return "No commits found"
        
        lines = output.strip().split('\n')
        commit_count = len([line for line in lines if line.startswith('commit')])
        
        return f"Showing {commit_count} recent commits:\n\n{output}"
    
    def _format_process_output(self, output: str) -> str:
        """Format process listing output"""
        
        if not output:
            return "No processes found"
        
        lines = output.strip().split('\n')
        if len(lines) > 1:  # Has header
            process_count = len(lines) - 1
            return f"Found {process_count} processes:\n{output}"
        
        return output
    
    def _detect_file_changes(self, command: str, operation_type: str) -> List[str]:
        """Detect which files were affected by the operation"""
        
        affected_files = []
        
        if operation_type in ['copy', 'move']:
            # Extract source and destination from cp/mv commands
            parts = command.split()
            if len(parts) >= 3:
                affected_files.extend(parts[-2:])  # Last two arguments
        
        elif operation_type == 'remove':
            # Extract files being removed
            parts = command.split()
            for part in parts[1:]:  # Skip 'rm'
                if not part.startswith('-'):  # Skip flags
                    affected_files.append(part)
        
        elif operation_type in ['create_file', 'create_dir']:
            # Extract files/dirs being created
            parts = command.split()
            affected_files.extend(parts[1:])  # All arguments after command
        
        return affected_files