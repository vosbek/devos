"""
Approval manager for DevOS command execution
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum

from .risk_assessment import RiskAssessment
from .preferences import UserPreferences

class ApprovalStatus(Enum):
    """Approval status enumeration"""
    AUTO_APPROVED = "auto_approved"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"

class ApprovalManager:
    """Manages approval workflows for command execution"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.risk_assessment = RiskAssessment()
        self.user_preferences = UserPreferences()
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.auto_approve_safe = config.get('auto_approve_safe', True)
        self.approval_timeout = config.get('approval_timeout', 300)  # 5 minutes
        self.learn_preferences = config.get('learn_preferences', True)
        
        # Pending approvals
        self.pending_approvals = {}
        
    async def start(self):
        """Start the approval manager"""
        await self.user_preferences.load()
        self.logger.info("Approval manager started")
    
    async def stop(self):
        """Stop the approval manager"""
        await self.user_preferences.save()
        self.logger.info("Approval manager stopped")
    
    async def requires_approval(self, command: str, context: Dict[str, Any], user_id: str) -> bool:
        """Determine if a command requires user approval"""
        
        try:
            # Assess risk level
            risk_level = await self.risk_assessment.assess_command_risk(command, context)
            
            # Check user preferences
            user_pref = await self.user_preferences.get_command_preference(
                user_id, command, context
            )
            
            # Auto-approval logic
            if self.auto_approve_safe and risk_level['level'] == 'safe':
                # Check if user has explicitly denied this type of command
                if user_pref and user_pref.get('always_deny', False):
                    return True
                return False
            
            # Check if user has given blanket approval
            if user_pref and user_pref.get('always_approve', False):
                # But still require approval for high-risk commands
                if risk_level['level'] in ['high', 'critical']:
                    return True
                return False
            
            # Default: require approval for non-safe commands
            return risk_level['level'] != 'safe'
            
        except Exception as e:
            self.logger.error(f"Error assessing approval requirement: {e}")
            # Fail safe: require approval on error
            return True
    
    async def request_approval(self, approval_request: Dict[str, Any]) -> str:
        """Request approval for a command"""
        
        approval_id = f"approval_{datetime.utcnow().timestamp()}_{hash(approval_request['command']) % 1000}"
        
        approval_data = {
            'id': approval_id,
            'command': approval_request['command'],
            'user_id': approval_request['user_id'],
            'context': approval_request.get('context', {}),
            'risk_assessment': await self.risk_assessment.assess_command_risk(
                approval_request['command'], 
                approval_request.get('context', {})
            ),
            'status': ApprovalStatus.PENDING,
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(seconds=self.approval_timeout)
        }
        
        self.pending_approvals[approval_id] = approval_data
        
        # Schedule cleanup after timeout
        asyncio.create_task(self._cleanup_expired_approval(approval_id))
        
        self.logger.info(f"Approval requested for command: {approval_request['command'][:50]}...")
        
        return approval_id
    
    async def process_approval_response(self, approval_id: str, response: Dict[str, Any]) -> Dict[str, Any]:
        """Process user's approval response"""
        
        if approval_id not in self.pending_approvals:
            return {
                'success': False,
                'error': 'Approval request not found or expired'
            }
        
        approval_data = self.pending_approvals[approval_id]
        
        # Check if expired
        if datetime.utcnow() > approval_data['expires_at']:
            approval_data['status'] = ApprovalStatus.TIMEOUT
            del self.pending_approvals[approval_id]
            return {
                'success': False,
                'error': 'Approval request has expired'
            }
        
        # Process the response
        approved = response.get('approved', False)
        remember = response.get('remember', False)
        note = response.get('note', '')
        
        if approved:
            approval_data['status'] = ApprovalStatus.APPROVED
            
            # Learn user preference if requested
            if remember and self.learn_preferences:
                await self.user_preferences.learn_preference(
                    approval_data['user_id'],
                    approval_data['command'],
                    approval_data['context'],
                    approved=True,
                    note=note
                )
        else:
            approval_data['status'] = ApprovalStatus.REJECTED
            
            # Learn rejection preference
            if remember and self.learn_preferences:
                await self.user_preferences.learn_preference(
                    approval_data['user_id'],
                    approval_data['command'],
                    approval_data['context'],
                    approved=False,
                    note=note
                )
        
        approval_data['response'] = response
        approval_data['responded_at'] = datetime.utcnow()
        
        # Remove from pending
        del self.pending_approvals[approval_id]
        
        result = {
            'success': True,
            'approved': approved,
            'status': approval_data['status'].value,
            'note': note
        }
        
        self.logger.info(f"Approval {approval_id} {'approved' if approved else 'rejected'}")
        
        return result
    
    async def get_approval_status(self, approval_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of an approval request"""
        
        if approval_id not in self.pending_approvals:
            return None
        
        approval_data = self.pending_approvals[approval_id]
        
        # Check if expired
        if datetime.utcnow() > approval_data['expires_at']:
            approval_data['status'] = ApprovalStatus.TIMEOUT
            del self.pending_approvals[approval_id]
            return {
                'id': approval_id,
                'status': ApprovalStatus.TIMEOUT.value,
                'expired': True
            }
        
        return {
            'id': approval_id,
            'status': approval_data['status'].value,
            'command': approval_data['command'],
            'risk_level': approval_data['risk_assessment']['level'],
            'created_at': approval_data['created_at'].isoformat(),
            'expires_at': approval_data['expires_at'].isoformat(),
            'time_remaining': (approval_data['expires_at'] - datetime.utcnow()).total_seconds()
        }
    
    async def learn_preference(self, user_id: str, command: str, context: Dict[str, Any], approved: bool) -> bool:
        """Learn user preference for future similar commands"""
        
        if not self.learn_preferences:
            return False
        
        try:
            await self.user_preferences.learn_preference(
                user_id, command, context, approved
            )
            return True
        except Exception as e:
            self.logger.error(f"Error learning preference: {e}")
            return False
    
    async def get_pending_approvals(self, user_id: str = None) -> List[Dict[str, Any]]:
        """Get list of pending approvals"""
        
        pending = []
        
        for approval_id, approval_data in self.pending_approvals.items():
            # Filter by user if specified
            if user_id and approval_data['user_id'] != user_id:
                continue
            
            # Check if expired
            if datetime.utcnow() > approval_data['expires_at']:
                approval_data['status'] = ApprovalStatus.TIMEOUT
                continue
            
            pending.append({
                'id': approval_id,
                'command': approval_data['command'],
                'user_id': approval_data['user_id'],
                'risk_level': approval_data['risk_assessment']['level'],
                'created_at': approval_data['created_at'].isoformat(),
                'expires_at': approval_data['expires_at'].isoformat(),
                'time_remaining': (approval_data['expires_at'] - datetime.utcnow()).total_seconds()
            })
        
        # Clean up expired approvals
        expired_ids = [
            approval_id for approval_id, approval_data in self.pending_approvals.items()
            if approval_data['status'] == ApprovalStatus.TIMEOUT
        ]
        
        for approval_id in expired_ids:
            del self.pending_approvals[approval_id]
        
        return pending
    
    async def _cleanup_expired_approval(self, approval_id: str):
        """Clean up expired approval after timeout"""
        
        await asyncio.sleep(self.approval_timeout)
        
        if approval_id in self.pending_approvals:
            approval_data = self.pending_approvals[approval_id]
            
            if approval_data['status'] == ApprovalStatus.PENDING:
                approval_data['status'] = ApprovalStatus.TIMEOUT
                self.logger.info(f"Approval {approval_id} expired")
                
                # Clean up
                del self.pending_approvals[approval_id]
    
    async def get_approval_statistics(self, user_id: str = None, days: int = 30) -> Dict[str, Any]:
        """Get approval statistics"""
        
        # This would be more sophisticated with persistent storage
        # For MVP, return basic stats from current session
        
        stats = {
            'pending_count': len(self.pending_approvals),
            'auto_approve_enabled': self.auto_approve_safe,
            'approval_timeout_seconds': self.approval_timeout,
            'learn_preferences_enabled': self.learn_preferences
        }
        
        if user_id:
            user_pending = [
                a for a in self.pending_approvals.values() 
                if a['user_id'] == user_id
            ]
            stats['user_pending_count'] = len(user_pending)
        
        return stats
    
    async def update_approval_config(self, new_config: Dict[str, Any]) -> bool:
        """Update approval configuration"""
        
        try:
            if 'auto_approve_safe' in new_config:
                self.auto_approve_safe = new_config['auto_approve_safe']
            
            if 'approval_timeout' in new_config:
                self.approval_timeout = new_config['approval_timeout']
            
            if 'learn_preferences' in new_config:
                self.learn_preferences = new_config['learn_preferences']
            
            self.config.update(new_config)
            
            self.logger.info("Approval configuration updated")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating approval config: {e}")
            return False