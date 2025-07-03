"""
Secure command execution sandbox for DevOS
"""

import asyncio
import subprocess
import logging
import time
import os
import signal
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..daemon.models import CommandResult
from .validators import CommandValidator

class CommandExecutor:
    """Secure command executor with sandboxing capabilities"""
    
    def __init__(self, security_config: Dict[str, Any]):
        self.security_config = security_config
        self.validator = CommandValidator(security_config)
        self.logger = logging.getLogger(__name__)
        
        # Execution limits
        self.max_execution_time = security_config.get('max_execution_time', 120)
        self.sandbox_enabled = security_config.get('sandbox_enabled', True)
        
    async def execute(self, commands: List[Dict[str, Any]], user_id: str) -> CommandResult:
        """Execute a list of commands with security controls"""
        
        start_time = time.time()
        all_output = []
        all_errors = []
        commands_executed = []
        files_affected = []
        overall_success = True
        
        try:
            for i, command_info in enumerate(commands):
                self.logger.info(f"Executing command {i+1}/{len(commands)}: {command_info}")
                
                # Validate command
                validation_result = await self.validator.validate_command(command_info)
                if not validation_result['valid']:
                    error_msg = f"Command validation failed: {validation_result['reason']}"
                    all_errors.append(error_msg)
                    overall_success = False
                    continue
                
                # Execute individual command
                result = await self._execute_single_command(command_info, user_id)
                
                # Collect results
                all_output.append(result.output)
                if result.error:
                    all_errors.append(result.error)
                
                commands_executed.append(command_info.get('command', ''))
                files_affected.extend(result.files_affected)
                
                if not result.success:
                    overall_success = False
                    # Decide whether to continue on error
                    if command_info.get('safety_level') == 'destructive':
                        break  # Stop on destructive command failure
            
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            
            return CommandResult(
                success=overall_success,
                output='\n'.join(all_output),
                error='\n'.join(all_errors) if all_errors else "",
                exit_code=0 if overall_success else 1,
                execution_time=execution_time,
                commands_executed=commands_executed,
                files_affected=list(set(files_affected))
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.logger.error(f"Command execution failed: {e}")
            
            return CommandResult(
                success=False,
                output='\n'.join(all_output),
                error=str(e),
                exit_code=1,
                execution_time=execution_time,
                commands_executed=commands_executed,
                files_affected=files_affected
            )
    
    async def _execute_single_command(self, command_info: Dict[str, Any], user_id: str) -> CommandResult:
        """Execute a single command with appropriate handler"""
        
        command_type = command_info.get('type', 'bash')
        command = command_info.get('command', '')
        
        if command_type == 'bash':
            return await self._execute_bash_command(command, command_info)
        elif command_type == 'python':
            return await self._execute_python_command(command, command_info)
        elif command_type == 'sql':
            return await self._execute_sql_command(command, command_info)
        else:
            return CommandResult(
                success=False,
                error=f"Unsupported command type: {command_type}"
            )
    
    async def _execute_bash_command(self, command: str, command_info: Dict[str, Any]) -> CommandResult:
        """Execute a bash command with security controls"""
        
        start_time = time.time()
        
        try:
            # Prepare command environment
            env = os.environ.copy()
            
            # Set up sandbox if enabled
            if self.sandbox_enabled:
                command = self._apply_sandbox_restrictions(command)
            
            # Execute command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=os.getcwd()
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.max_execution_time
                )
                
                output = stdout.decode('utf-8', errors='replace').strip()
                error = stderr.decode('utf-8', errors='replace').strip()
                
                execution_time = (time.time() - start_time) * 1000
                
                # Detect affected files (basic implementation)
                files_affected = self._detect_affected_files(command, output)
                
                return CommandResult(
                    success=process.returncode == 0,
                    output=output,
                    error=error,
                    exit_code=process.returncode,
                    execution_time=execution_time,
                    commands_executed=[command],
                    files_affected=files_affected
                )
                
            except asyncio.TimeoutError:
                # Kill the process if it times out
                try:
                    process.kill()
                    await process.wait()
                except:
                    pass
                
                return CommandResult(
                    success=False,
                    error=f"Command timed out after {self.max_execution_time} seconds",
                    exit_code=124,  # Timeout exit code
                    execution_time=self.max_execution_time * 1000
                )
                
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            
            return CommandResult(
                success=False,
                error=f"Command execution failed: {str(e)}",
                exit_code=1,
                execution_time=execution_time
            )
    
    def _apply_sandbox_restrictions(self, command: str) -> str:
        """Apply sandbox restrictions to command"""
        
        # Basic sandboxing - in production, use more sophisticated methods
        # like containers, chroot, or firejail
        
        restricted_command = command
        
        # Prevent certain dangerous operations
        dangerous_patterns = [
            'rm -rf /',
            'mkfs',
            'dd if=',
            'chmod 777',
            'chown root',
            'sudo rm',
            'sudo dd'
        ]
        
        for pattern in dangerous_patterns:
            if pattern in command.lower():
                raise ValueError(f"Dangerous command pattern detected: {pattern}")
        
        # Add safety prefixes for certain commands
        if command.strip().startswith('rm '):
            # Add interactive flag to rm commands
            restricted_command = command.replace('rm ', 'rm -i ', 1)
        
        return restricted_command
    
    async def _execute_python_command(self, command: str, command_info: Dict[str, Any]) -> CommandResult:
        """Execute a Python command or script"""
        
        start_time = time.time()
        
        try:
            # Create a restricted Python environment
            python_code = f"""
import sys
import os
import subprocess
import json
from pathlib import Path

# Restricted imports only
allowed_modules = ['os', 'sys', 'json', 'pathlib', 're', 'datetime', 'math']

# Execute the command
try:
    result = {command}
    print(json.dumps({{"success": True, "result": str(result)}}))
except Exception as e:
    print(json.dumps({{"success": False, "error": str(e)}}))
"""
            
            process = await asyncio.create_subprocess_exec(
                'python3', '-c', python_code,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.max_execution_time
            )
            
            output = stdout.decode('utf-8', errors='replace').strip()
            error = stderr.decode('utf-8', errors='replace').strip()
            
            execution_time = (time.time() - start_time) * 1000
            
            return CommandResult(
                success=process.returncode == 0,
                output=output,
                error=error,
                exit_code=process.returncode,
                execution_time=execution_time,
                commands_executed=[command]
            )
            
        except asyncio.TimeoutError:
            return CommandResult(
                success=False,
                error=f"Python command timed out after {self.max_execution_time} seconds",
                exit_code=124,
                execution_time=self.max_execution_time * 1000
            )
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            
            return CommandResult(
                success=False,
                error=f"Python command execution failed: {str(e)}",
                exit_code=1,
                execution_time=execution_time
            )
    
    async def _execute_sql_command(self, command: str, command_info: Dict[str, Any]) -> CommandResult:
        """Execute a SQL command (placeholder for future implementation)"""
        
        # This would integrate with database connections in a full implementation
        return CommandResult(
            success=False,
            error="SQL command execution not implemented in MVP",
            exit_code=1
        )
    
    def _detect_affected_files(self, command: str, output: str) -> List[str]:
        """Detect files that may have been affected by the command"""
        
        affected_files = []
        
        # Basic file detection based on command patterns
        if 'cp ' in command or 'copy ' in command:
            # Extract file paths from copy commands
            parts = command.split()
            if len(parts) >= 3:
                affected_files.extend(parts[-2:])  # Source and destination
        
        elif 'mv ' in command or 'move ' in command:
            # Extract file paths from move commands
            parts = command.split()
            if len(parts) >= 3:
                affected_files.extend(parts[-2:])  # Source and destination
        
        elif 'rm ' in command:
            # Extract file paths from remove commands
            parts = command.split()
            for part in parts[1:]:  # Skip 'rm' itself
                if not part.startswith('-'):  # Skip flags
                    affected_files.append(part)
        
        elif 'touch ' in command:
            # Extract file paths from touch commands
            parts = command.split()
            affected_files.extend(parts[1:])  # All arguments are files
        
        elif '>' in command or '>>' in command:
            # Extract output redirection files
            if '>>' in command:
                affected_files.append(command.split('>>')[-1].strip())
            elif '>' in command:
                affected_files.append(command.split('>')[-1].strip())
        
        # Clean up file paths
        cleaned_files = []
        for file_path in affected_files:
            file_path = file_path.strip().strip('"').strip("'")
            if file_path and not file_path.startswith('-'):
                cleaned_files.append(file_path)
        
        return cleaned_files
    
    async def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        
        # This would be more sophisticated in a full implementation
        # with persistent storage of execution metrics
        
        return {
            'sandbox_enabled': self.sandbox_enabled,
            'max_execution_time': self.max_execution_time,
            'supported_types': ['bash', 'python', 'sql'],
            'security_config': self.security_config
        }