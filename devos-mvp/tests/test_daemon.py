"""
Tests for the DevOS daemon components
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

from daemon.main import DevOSDaemon
from daemon.api import create_app
from daemon.models import CommandRequest, CommandResult


class TestDevOSDaemon:
    """Test the main DevOS daemon."""
    
    @pytest.mark.asyncio
    async def test_daemon_startup(self, mock_config, mock_bedrock_client, 
                                 mock_approval_manager, mock_context_engine):
        """Test daemon startup process."""
        with patch('daemon.main.BedrockClient', return_value=mock_bedrock_client), \
             patch('daemon.main.ApprovalManager', return_value=mock_approval_manager), \
             patch('daemon.main.ContextEngine', return_value=mock_context_engine):
            
            daemon = DevOSDaemon(mock_config)
            await daemon.start()
            
            # Verify all components are initialized
            assert daemon.llm_client is not None
            assert daemon.approval_manager is not None
            assert daemon.context_engine is not None
            
            # Verify start methods are called
            mock_approval_manager.start.assert_called_once()
            mock_context_engine.start.assert_called_once()
            
            await daemon.stop()
    
    @pytest.mark.asyncio
    async def test_daemon_command_processing(self, mock_config, mock_bedrock_client,
                                           mock_approval_manager, mock_context_engine):
        """Test command processing workflow."""
        with patch('daemon.main.BedrockClient', return_value=mock_bedrock_client), \
             patch('daemon.main.ApprovalManager', return_value=mock_approval_manager), \
             patch('daemon.main.ContextEngine', return_value=mock_context_engine):
            
            daemon = DevOSDaemon(mock_config)
            await daemon.start()
            
            # Mock LLM response
            mock_bedrock_client.process_command.return_value = {
                'command': 'ls -la',
                'explanation': 'List files in current directory'
            }
            
            # Process a command
            result = await daemon.process_command("list all files", "user123")
            
            # Verify processing
            assert result is not None
            mock_bedrock_client.process_command.assert_called_once()
            
            await daemon.stop()
    
    @pytest.mark.asyncio
    async def test_daemon_shutdown(self, mock_config, mock_bedrock_client,
                                  mock_approval_manager, mock_context_engine):
        """Test daemon shutdown process."""
        with patch('daemon.main.BedrockClient', return_value=mock_bedrock_client), \
             patch('daemon.main.ApprovalManager', return_value=mock_approval_manager), \
             patch('daemon.main.ContextEngine', return_value=mock_context_engine):
            
            daemon = DevOSDaemon(mock_config)
            await daemon.start()
            await daemon.stop()
            
            # Verify stop methods are called
            mock_approval_manager.stop.assert_called_once()
            mock_context_engine.stop.assert_called_once()


class TestDevOSAPI:
    """Test the DevOS API endpoints."""
    
    @pytest.fixture
    def app(self, mock_config):
        """Create test app instance."""
        return create_app(mock_config)
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, app):
        """Test health check endpoint."""
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_command_submission(self, app, mock_config):
        """Test command submission endpoint."""
        from fastapi.testclient import TestClient
        
        with patch('daemon.api.daemon') as mock_daemon:
            mock_daemon.process_command = AsyncMock(return_value={
                'command_id': 'cmd_123',
                'status': 'processing',
                'command': 'ls -la'
            })
            
            client = TestClient(app)
            response = client.post("/api/v1/commands", json={
                'command': 'list all files',
                'user_id': 'user123'
            })
            
            assert response.status_code == 200
            data = response.json()
            assert 'command_id' in data
            assert data['status'] == 'processing'
    
    @pytest.mark.asyncio
    async def test_command_status(self, app):
        """Test command status endpoint."""
        from fastapi.testclient import TestClient
        
        with patch('daemon.api.daemon') as mock_daemon:
            mock_daemon.get_command_status = AsyncMock(return_value={
                'command_id': 'cmd_123',
                'status': 'completed',
                'result': 'Command executed successfully'
            })
            
            client = TestClient(app)
            response = client.get("/api/v1/commands/cmd_123")
            
            assert response.status_code == 200
            data = response.json()
            assert data['command_id'] == 'cmd_123'
            assert data['status'] == 'completed'
    
    @pytest.mark.asyncio
    async def test_approval_endpoints(self, app):
        """Test approval-related endpoints."""
        from fastapi.testclient import TestClient
        
        with patch('daemon.api.daemon') as mock_daemon:
            # Mock pending approvals
            mock_daemon.approval_manager.get_pending_approvals = AsyncMock(return_value=[
                {
                    'id': 'approval_123',
                    'command': 'rm file.txt',
                    'risk_level': 'medium'
                }
            ])
            
            client = TestClient(app)
            response = client.get("/api/v1/approvals")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]['id'] == 'approval_123'
    
    @pytest.mark.asyncio
    async def test_approval_response(self, app):
        """Test approval response endpoint."""
        from fastapi.testclient import TestClient
        
        with patch('daemon.api.daemon') as mock_daemon:
            mock_daemon.approval_manager.process_approval_response = AsyncMock(return_value={
                'success': True,
                'approved': True
            })
            
            client = TestClient(app)
            response = client.post("/api/v1/approvals/approval_123/respond", json={
                'approved': True,
                'remember': False
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert data['approved'] is True


class TestCommandModels:
    """Test command request and result models."""
    
    def test_command_request_validation(self):
        """Test CommandRequest model validation."""
        # Valid request
        request = CommandRequest(
            command="ls -la",
            user_id="user123"
        )
        assert request.command == "ls -la"
        assert request.user_id == "user123"
        
        # Invalid request (missing required fields)
        with pytest.raises(ValueError):
            CommandRequest(command="")
    
    def test_command_result_creation(self):
        """Test CommandResult model creation."""
        result = CommandResult(
            success=True,
            output="file1.txt\nfile2.txt",
            error="",
            exit_code=0
        )
        
        assert result.success is True
        assert result.output == "file1.txt\nfile2.txt"
        assert result.exit_code == 0
        
        # Test with error
        error_result = CommandResult(
            success=False,
            output="",
            error="Command not found",
            exit_code=127
        )
        
        assert error_result.success is False
        assert error_result.error == "Command not found"
        assert error_result.exit_code == 127