"""
Tests for the approval system components
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from approval.manager import ApprovalManager, ApprovalStatus
from approval.risk_assessment import RiskAssessment
from approval.preferences import UserPreferences


class TestApprovalManager:
    """Test the approval manager."""
    
    @pytest.fixture
    def approval_config(self):
        """Configuration for approval manager."""
        return {
            'auto_approve_safe': True,
            'approval_timeout': 30,
            'learn_preferences': True
        }
    
    @pytest.fixture
    def approval_manager(self, approval_config):
        """Create approval manager instance."""
        return ApprovalManager(approval_config)
    
    @pytest.mark.asyncio
    async def test_approval_manager_initialization(self, approval_manager):
        """Test approval manager initialization."""
        await approval_manager.start()
        
        assert approval_manager.auto_approve_safe is True
        assert approval_manager.approval_timeout == 30
        assert approval_manager.learn_preferences is True
        
        await approval_manager.stop()
    
    @pytest.mark.asyncio
    async def test_requires_approval_safe_command(self, approval_manager):
        """Test approval requirement for safe commands."""
        await approval_manager.start()
        
        with patch.object(approval_manager.risk_assessment, 'assess_command_risk') as mock_assess:
            mock_assess.return_value = {'level': 'safe'}
            
            requires = await approval_manager.requires_approval(
                'ls -la', {'current_directory': '/home/user'}, 'user123'
            )
            
            assert requires is False
        
        await approval_manager.stop()
    
    @pytest.mark.asyncio
    async def test_requires_approval_risky_command(self, approval_manager):
        """Test approval requirement for risky commands."""
        await approval_manager.start()
        
        with patch.object(approval_manager.risk_assessment, 'assess_command_risk') as mock_assess:
            mock_assess.return_value = {'level': 'high'}
            
            requires = await approval_manager.requires_approval(
                'rm -rf /important', {'current_directory': '/home/user'}, 'user123'
            )
            
            assert requires is True
        
        await approval_manager.stop()
    
    @pytest.mark.asyncio
    async def test_request_approval(self, approval_manager):
        """Test approval request creation."""
        await approval_manager.start()
        
        with patch.object(approval_manager.risk_assessment, 'assess_command_risk') as mock_assess:
            mock_assess.return_value = {
                'level': 'medium',
                'reasons': ['File modification'],
                'score': 2
            }
            
            approval_request = {
                'command': 'rm file.txt',
                'user_id': 'user123',
                'context': {'current_directory': '/home/user'}
            }
            
            approval_id = await approval_manager.request_approval(approval_request)
            
            assert approval_id is not None
            assert approval_id in approval_manager.pending_approvals
            
            approval_data = approval_manager.pending_approvals[approval_id]
            assert approval_data['command'] == 'rm file.txt'
            assert approval_data['user_id'] == 'user123'
            assert approval_data['status'] == ApprovalStatus.PENDING
        
        await approval_manager.stop()
    
    @pytest.mark.asyncio
    async def test_process_approval_response_approve(self, approval_manager):
        """Test processing approval response (approve)."""
        await approval_manager.start()
        
        # Create a pending approval
        with patch.object(approval_manager.risk_assessment, 'assess_command_risk') as mock_assess:
            mock_assess.return_value = {'level': 'medium', 'reasons': [], 'score': 2}
            
            approval_id = await approval_manager.request_approval({
                'command': 'rm file.txt',
                'user_id': 'user123'
            })
            
            # Process approval
            response = await approval_manager.process_approval_response(approval_id, {
                'approved': True,
                'remember': False,
                'note': 'Safe to delete'
            })
            
            assert response['success'] is True
            assert response['approved'] is True
            assert approval_id not in approval_manager.pending_approvals
        
        await approval_manager.stop()
    
    @pytest.mark.asyncio
    async def test_process_approval_response_reject(self, approval_manager):
        """Test processing approval response (reject)."""
        await approval_manager.start()
        
        # Create a pending approval
        with patch.object(approval_manager.risk_assessment, 'assess_command_risk') as mock_assess:
            mock_assess.return_value = {'level': 'high', 'reasons': [], 'score': 3}
            
            approval_id = await approval_manager.request_approval({
                'command': 'rm -rf /important',
                'user_id': 'user123'
            })
            
            # Process rejection
            response = await approval_manager.process_approval_response(approval_id, {
                'approved': False,
                'remember': True,
                'note': 'Too dangerous'
            })
            
            assert response['success'] is True
            assert response['approved'] is False
            assert approval_id not in approval_manager.pending_approvals
        
        await approval_manager.stop()
    
    @pytest.mark.asyncio
    async def test_get_pending_approvals(self, approval_manager):
        """Test getting pending approvals."""
        await approval_manager.start()
        
        with patch.object(approval_manager.risk_assessment, 'assess_command_risk') as mock_assess:
            mock_assess.return_value = {'level': 'medium', 'reasons': [], 'score': 2}
            
            # Create multiple pending approvals
            approval_id1 = await approval_manager.request_approval({
                'command': 'rm file1.txt',
                'user_id': 'user123'
            })
            
            approval_id2 = await approval_manager.request_approval({
                'command': 'rm file2.txt',
                'user_id': 'user456'
            })
            
            # Get all pending approvals
            pending = await approval_manager.get_pending_approvals()
            assert len(pending) == 2
            
            # Get user-specific pending approvals
            user_pending = await approval_manager.get_pending_approvals('user123')
            assert len(user_pending) == 1
            assert user_pending[0]['command'] == 'rm file1.txt'
        
        await approval_manager.stop()


class TestRiskAssessment:
    """Test the risk assessment engine."""
    
    @pytest.fixture
    def risk_assessment(self):
        """Create risk assessment instance."""
        return RiskAssessment()
    
    @pytest.mark.asyncio
    async def test_assess_safe_command(self, risk_assessment):
        """Test assessment of safe commands."""
        assessment = await risk_assessment.assess_command_risk('ls -la', {})
        
        assert assessment['level'] == 'safe'
        assert assessment['score'] == 0
        assert 'safe' in assessment['reasons'][0].lower()
    
    @pytest.mark.asyncio
    async def test_assess_risky_command(self, risk_assessment):
        """Test assessment of risky commands."""
        assessment = await risk_assessment.assess_command_risk('rm -rf /', {})
        
        assert assessment['level'] == 'critical'
        assert assessment['score'] == 4
        assert len(assessment['reasons']) > 0
    
    @pytest.mark.asyncio
    async def test_assess_medium_risk_command(self, risk_assessment):
        """Test assessment of medium risk commands."""
        assessment = await risk_assessment.assess_command_risk('pip install package', {})
        
        assert assessment['level'] in ['medium', 'low']
        assert assessment['score'] >= 1
    
    @pytest.mark.asyncio
    async def test_context_risk_assessment(self, risk_assessment):
        """Test risk assessment with context."""
        # Test in root directory
        assessment = await risk_assessment.assess_command_risk(
            'rm file.txt', 
            {'current_directory': '/root', 'user': 'root'}
        )
        
        assert assessment['score'] >= 2  # Should be higher risk
        
        # Test in user directory
        assessment = await risk_assessment.assess_command_risk(
            'rm file.txt',
            {'current_directory': '/home/user', 'user': 'user'}
        )
        
        # Should be lower risk than root
        assert assessment['score'] <= 3
    
    def test_extract_main_command(self, risk_assessment):
        """Test command extraction."""
        # Simple command
        assert risk_assessment._extract_main_command('ls -la') == 'ls'
        
        # Command with sudo
        assert risk_assessment._extract_main_command('sudo rm file.txt') == 'rm'
        
        # Command with pipes
        assert risk_assessment._extract_main_command('cat file.txt | grep pattern') == 'cat'
        
        # Command with redirection
        assert risk_assessment._extract_main_command('echo "test" > file.txt') == 'echo'
    
    def test_is_auto_approvable(self, risk_assessment):
        """Test auto-approval determination."""
        # Safe commands should be auto-approvable
        assert risk_assessment.is_auto_approvable('ls -la', {}) is True
        
        # Risky commands should not be auto-approvable
        assert risk_assessment.is_auto_approvable('rm -rf /', {}) is False


class TestUserPreferences:
    """Test the user preferences system."""
    
    @pytest.fixture
    def temp_config_dir(self, temp_dir):
        """Create temporary config directory."""
        return temp_dir / "config"
    
    @pytest.fixture
    def user_preferences(self, temp_config_dir):
        """Create user preferences instance."""
        return UserPreferences(str(temp_config_dir))
    
    @pytest.mark.asyncio
    async def test_preferences_initialization(self, user_preferences):
        """Test preferences initialization."""
        await user_preferences.load()
        
        assert user_preferences.preferences == {}
        assert user_preferences.command_patterns == {}
        assert user_preferences.approval_history == []
    
    @pytest.mark.asyncio
    async def test_learn_preference(self, user_preferences):
        """Test learning user preferences."""
        await user_preferences.load()
        
        await user_preferences.learn_preference(
            'user123', 'ls -la', {}, approved=True, note='Always approve ls'
        )
        
        # Check that preference was learned
        assert 'user123' in user_preferences.preferences
        user_prefs = user_preferences.preferences['user123']
        assert len(user_prefs) == 1
        
        # Check approval history
        assert len(user_preferences.approval_history) == 1
        assert user_preferences.approval_history[0]['approved'] is True
    
    @pytest.mark.asyncio
    async def test_get_command_preference(self, user_preferences):
        """Test getting command preferences."""
        await user_preferences.load()
        
        # Learn a preference
        await user_preferences.learn_preference(
            'user123', 'ls -la', {}, approved=True
        )
        
        # Get preference
        preference = await user_preferences.get_command_preference(
            'user123', 'ls -la', {}
        )
        
        assert preference is not None
        assert preference['approved'] is True
    
    @pytest.mark.asyncio
    async def test_save_and_load_preferences(self, user_preferences):
        """Test saving and loading preferences."""
        await user_preferences.load()
        
        # Add some preferences
        await user_preferences.learn_preference(
            'user123', 'ls -la', {}, approved=True
        )
        await user_preferences.learn_preference(
            'user456', 'rm file.txt', {}, approved=False
        )
        
        # Save preferences
        await user_preferences.save()
        
        # Create new instance and load
        new_preferences = UserPreferences(user_preferences.config_dir)
        await new_preferences.load()
        
        # Verify data was loaded
        assert 'user123' in new_preferences.preferences
        assert 'user456' in new_preferences.preferences
        assert len(new_preferences.approval_history) == 2
    
    @pytest.mark.asyncio
    async def test_user_statistics(self, user_preferences):
        """Test user statistics generation."""
        await user_preferences.load()
        
        # Add some preferences
        await user_preferences.learn_preference('user123', 'ls -la', {}, approved=True)
        await user_preferences.learn_preference('user123', 'cat file.txt', {}, approved=True)
        await user_preferences.learn_preference('user123', 'rm file.txt', {}, approved=False)
        
        stats = await user_preferences.get_user_statistics('user123')
        
        assert stats['total_preferences'] == 3
        assert stats['approved_count'] == 2
        assert stats['rejected_count'] == 1
        assert stats['approval_rate'] == 2/3
    
    @pytest.mark.asyncio
    async def test_clear_user_preferences(self, user_preferences):
        """Test clearing user preferences."""
        await user_preferences.load()
        
        # Add preferences
        await user_preferences.learn_preference('user123', 'ls -la', {}, approved=True)
        await user_preferences.learn_preference('user456', 'cat file.txt', {}, approved=True)
        
        # Clear one user's preferences
        await user_preferences.clear_user_preferences('user123')
        
        assert 'user123' not in user_preferences.preferences
        assert 'user456' in user_preferences.preferences
        
        # Check approval history is cleaned
        remaining_history = [h for h in user_preferences.approval_history if h['user_id'] != 'user123']
        assert len(remaining_history) == 1