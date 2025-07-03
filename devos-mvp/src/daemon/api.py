"""
FastAPI application for DevOS daemon
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.websockets import WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import uuid
import json
from datetime import datetime

from .models import (
    CommandRequest, CommandResponse, ApprovalRequest, 
    Job, JobStatus, CommandResult, SystemContext
)
from ..llm.model_router import ModelRouter
from ..executor.sandbox import CommandExecutor
from ..approval.manager import ApprovalManager

class CommandRequestModel(BaseModel):
    """Pydantic model for command requests"""
    command: str
    context: Optional[Dict[str, Any]] = None
    user_id: str = "default"
    approval_timeout: int = 300

class ApprovalRequestModel(BaseModel):
    """Pydantic model for approval requests"""
    approved: bool
    remember: bool = False
    note: Optional[str] = None

def create_app(services: Dict, config) -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title="DevOS API",
        description="LLM-powered operating system interface",
        version="1.0.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Global state
    jobs: Dict[str, Job] = {}
    websocket_connections: List[WebSocket] = []
    
    # Initialize components
    model_router = ModelRouter(services['bedrock'], config.model_config)
    executor = CommandExecutor(config.security_config)
    approval_manager: ApprovalManager = services['approval_manager']
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                name: "running" for name in services.keys()
            }
        }
    
    @app.post("/api/v1/command", response_model=CommandResponse)
    async def submit_command(request: CommandRequestModel, background_tasks: BackgroundTasks):
        """Submit a natural language command for processing"""
        
        job_id = str(uuid.uuid4())
        
        # Get current context
        context = await gather_context(services, request.context)
        
        # Create job
        job = Job(
            id=job_id,
            command=request.command,
            user_id=request.user_id,
            context=context.__dict__
        )
        
        # Route to appropriate model
        model_info = await model_router.select_model(request.command, context.__dict__)
        job.model_used = model_info['model_name']
        job.cost_usd = model_info['estimated_cost']
        
        # Assess risk and approval requirements
        approval_required = await approval_manager.requires_approval(
            request.command, context.__dict__, request.user_id
        )
        job.requires_approval = approval_required
        
        if not approval_required:
            job.set_status(JobStatus.APPROVED, "Auto-approved based on safety assessment")
            background_tasks.add_task(execute_command, job_id)
        else:
            job.set_status(JobStatus.PENDING, "Waiting for user approval")
            background_tasks.add_task(send_approval_notification, job_id)
        
        jobs[job_id] = job
        
        return CommandResponse(
            job_id=job_id,
            status=job.status,
            requires_approval=approval_required,
            estimated_cost=model_info['estimated_cost'],
            model_used=model_info['model_name']
        )
    
    @app.get("/api/v1/command/{job_id}/status")
    async def get_command_status(job_id: str):
        """Get the status of a command execution"""
        
        if job_id not in jobs:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = jobs[job_id]
        return {
            'job_id': job_id,
            'status': job.status.value,
            'result': job.result,
            'error': job.error,
            'logs': job.logs,
            'progress': job.progress,
            'estimated_completion': job.estimated_completion.isoformat() if job.estimated_completion else None,
            'tokens_consumed': job.tokens_consumed,
            'cost_usd': job.cost_usd
        }
    
    @app.post("/api/v1/command/{job_id}/approve")
    async def approve_command(job_id: str, approval: ApprovalRequestModel, background_tasks: BackgroundTasks):
        """Approve or reject a pending command"""
        
        if job_id not in jobs:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = jobs[job_id]
        
        if job.status != JobStatus.PENDING:
            raise HTTPException(status_code=400, detail="Job is not pending approval")
        
        if approval.approved:
            job.set_status(JobStatus.APPROVED, f"Approved by user")
            job.approved_by = job.user_id  # In production, get from auth
            job.approved_at = datetime.utcnow()
            
            # Learn user preference if requested
            if approval.remember:
                await approval_manager.learn_preference(
                    job.command, job.context, job.user_id, True
                )
            
            # Execute the command
            background_tasks.add_task(execute_command, job_id)
        else:
            job.set_status(JobStatus.REJECTED, f"Rejected by user: {approval.note or 'No reason provided'}")
            job.result = {'message': 'Command rejected by user', 'note': approval.note}
        
        # Notify websocket clients
        await broadcast_job_update(job_id)
        
        return {'status': 'success', 'job_status': job.status.value}
    
    @app.get("/api/v1/jobs")
    async def list_jobs(user_id: Optional[str] = None, limit: int = 50):
        """List recent jobs"""
        
        job_list = list(jobs.values())
        
        # Filter by user if specified
        if user_id:
            job_list = [job for job in job_list if job.user_id == user_id]
        
        # Sort by creation time (newest first)
        job_list.sort(key=lambda x: x.created_at, reverse=True)
        
        # Limit results
        job_list = job_list[:limit]
        
        return {
            'jobs': [
                {
                    'id': job.id,
                    'command': job.command,
                    'status': job.status.value,
                    'created_at': job.created_at.isoformat(),
                    'progress': job.progress
                }
                for job in job_list
            ],
            'total': len(job_list)
        }
    
    @app.websocket("/ws/events")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for real-time updates"""
        await websocket.accept()
        websocket_connections.append(websocket)
        
        try:
            while True:
                # Keep connection alive
                await websocket.receive_text()
        except WebSocketDisconnect:
            websocket_connections.remove(websocket)
    
    async def gather_context(services: Dict, additional_context: Optional[Dict] = None) -> SystemContext:
        """Gather current system context for command processing"""
        
        import os
        
        context = SystemContext(
            cwd=os.getcwd(),
            user_id="system"  # In production, get from auth
        )
        
        # File system context
        if 'file_monitor' in services:
            try:
                context.files = await services['file_monitor'].get_recent_changes()
            except Exception as e:
                context.files = {"error": str(e)}
        
        # Process context
        if 'process_monitor' in services:
            try:
                context.processes = await services['process_monitor'].get_current_processes()
            except Exception as e:
                context.processes = {"error": str(e)}
        
        # Git context
        if 'git_monitor' in services:
            try:
                context.git = await services['git_monitor'].get_repository_status()
            except Exception as e:
                context.git = {"error": str(e)}
        
        # Environment variables
        context.environment = dict(os.environ)
        
        # Merge additional context
        if additional_context:
            for key, value in additional_context.items():
                if hasattr(context, key):
                    setattr(context, key, value)
        
        return context
    
    async def execute_command(job_id: str):
        """Execute a command in the background"""
        job = jobs[job_id]
        job.set_status(JobStatus.EXECUTING, "Starting command execution")
        
        try:
            # Generate system commands using LLM
            job.update_progress(10, "Analyzing command with LLM")
            
            llm_response = await model_router.process_command(
                job.command, 
                job.context, 
                {
                    'model_name': job.model_used,
                    'estimated_cost': job.cost_usd
                }
            )
            
            job.tokens_consumed = llm_response.get('usage', {}).get('total_tokens', 0)
            job.update_progress(30, "Generated execution plan")
            
            # Execute generated commands
            job.update_progress(40, "Executing commands")
            result = await executor.execute(llm_response['commands'], job.user_id)
            
            job.update_progress(90, "Processing results")
            job.set_status(JobStatus.COMPLETED, "Command executed successfully")
            job.result = result.__dict__ if hasattr(result, '__dict__') else result
            job.update_progress(100, "Complete")
            
        except Exception as e:
            job.set_status(JobStatus.FAILED, f"Execution failed: {str(e)}")
            job.error = str(e)
            job.add_log("ERROR", f"Command execution failed: {str(e)}")
        
        # Notify websocket clients
        await broadcast_job_update(job_id)
    
    async def send_approval_notification(job_id: str):
        """Send desktop notification for approval request"""
        job = jobs[job_id]
        
        notification_data = {
            'type': 'approval_request',
            'job_id': job_id,
            'command': job.command,
            'estimated_cost': job.cost_usd,
            'model': job.model_used
        }
        
        # Send to UI service for desktop notification
        await broadcast_notification(notification_data)
    
    async def broadcast_job_update(job_id: str):
        """Broadcast job status update to all websocket clients"""
        if job_id not in jobs:
            return
            
        job = jobs[job_id]
        message = {
            'type': 'job_update',
            'job_id': job_id,
            'status': job.status.value,
            'progress': job.progress,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        for websocket in websocket_connections[:]:  # Copy to avoid modification during iteration
            try:
                await websocket.send_text(json.dumps(message))
            except:
                websocket_connections.remove(websocket)
    
    async def broadcast_notification(data: Dict):
        """Broadcast notification to all websocket clients"""
        message = {
            'type': 'notification',
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        for websocket in websocket_connections[:]:
            try:
                await websocket.send_text(json.dumps(message))
            except:
                websocket_connections.remove(websocket)
    
    return app