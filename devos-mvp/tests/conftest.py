"""
Pytest configuration and fixtures for DevOS MVP tests
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock

# Test configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        'system': {
            'working_directory': '/tmp/devos-test',
            'logging': {
                'level': 'DEBUG',
                'file': 'test.log'
            }
        },
        'llm': {
            'default_provider': 'mock',
            'bedrock': {
                'region': 'us-east-1',
                'models': {
                    'primary': 'claude-3-sonnet',
                    'fallback': 'claude-3-haiku'
                }
            }
        },
        'security': {
            'approval': {
                'enabled': True,
                'auto_approve_safe': True,
                'approval_timeout': 30
            }
        },
        'api': {
            'host': '127.0.0.1',
            'port': 8080
        }
    }

@pytest.fixture
def mock_bedrock_client():
    """Mock AWS Bedrock client for testing."""
    mock_client = Mock()
    mock_client.invoke_model = AsyncMock()
    mock_client.invoke_model.return_value = {
        'body': Mock(read=Mock(return_value=b'{"content": [{"text": "Test response"}]}')),
        'contentType': 'application/json'
    }
    return mock_client

@pytest.fixture
def mock_approval_manager():
    """Mock approval manager for testing."""
    mock_manager = Mock()
    mock_manager.requires_approval = AsyncMock(return_value=False)
    mock_manager.request_approval = AsyncMock(return_value="approval_123")
    mock_manager.get_approval_status = AsyncMock(return_value={
        'id': 'approval_123',
        'status': 'pending',
        'command': 'test command'
    })
    return mock_manager

@pytest.fixture
def mock_context_engine():
    """Mock context engine for testing."""
    mock_engine = Mock()
    mock_engine.get_context = AsyncMock(return_value={
        'current_directory': '/tmp/test',
        'recent_files': [],
        'git_status': 'clean',
        'running_processes': []
    })
    mock_engine.start = AsyncMock()
    mock_engine.stop = AsyncMock()
    return mock_engine

@pytest.fixture
def mock_executor():
    """Mock command executor for testing."""
    mock_executor = Mock()
    mock_executor.execute_command = AsyncMock(return_value={
        'success': True,
        'output': 'Test output',
        'error': '',
        'exit_code': 0
    })
    return mock_executor

@pytest.fixture
def sample_commands():
    """Sample commands for testing."""
    return {
        'safe': [
            'ls -la',
            'cat file.txt',
            'git status',
            'pwd',
            'whoami'
        ],
        'risky': [
            'rm -rf /',
            'sudo rm -rf /important',
            'dd if=/dev/zero of=/dev/sda',
            'mkfs.ext4 /dev/sda1'
        ],
        'medium': [
            'pip install package',
            'npm install',
            'git push origin main',
            'docker run -d nginx'
        ]
    }

@pytest.fixture
def sample_contexts():
    """Sample contexts for testing."""
    return {
        'basic': {
            'current_directory': '/home/user/project',
            'user': 'user',
            'recent_commands': ['ls', 'cd project']
        },
        'root': {
            'current_directory': '/root',
            'user': 'root',
            'recent_commands': ['sudo su', 'ls']
        },
        'git_repo': {
            'current_directory': '/home/user/project',
            'user': 'user',
            'git_status': 'modified',
            'git_branch': 'feature/test'
        }
    }

@pytest.fixture
def sample_approval_requests():
    """Sample approval requests for testing."""
    return [
        {
            'command': 'rm important_file.txt',
            'user_id': 'user123',
            'context': {'current_directory': '/home/user'}
        },
        {
            'command': 'sudo systemctl restart nginx',
            'user_id': 'admin456',
            'context': {'current_directory': '/etc/nginx'}
        }
    ]

# Test utilities
class AsyncContextManager:
    """Utility class for async context managers in tests."""
    
    def __init__(self, async_obj):
        self.async_obj = async_obj
    
    async def __aenter__(self):
        return self.async_obj
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

def create_mock_async_context(obj):
    """Create a mock async context manager."""
    return AsyncContextManager(obj)

# Test markers
pytest.mark.integration = pytest.mark.integration
pytest.mark.unit = pytest.mark.unit
pytest.mark.slow = pytest.mark.slow