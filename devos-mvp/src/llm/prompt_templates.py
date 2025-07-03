"""
Prompt templates for DevOS LLM interactions
"""

import json
from typing import Dict, Any
from datetime import datetime

class PromptTemplates:
    """Templates for LLM prompts with system context"""
    
    def __init__(self):
        self.system_template = """You are DevOS, an AI assistant integrated into a Linux operating system. You help developers by translating natural language commands into system operations.

Current System Context:
- Working Directory: {cwd}
- Timestamp: {timestamp}
- User: {user_id}

File System Context:
{file_context}

Process Context:
{process_context}

Git Context:
{git_context}

Environment Context:
{env_context}

User Command: {user_command}

Please analyze the command and provide a JSON response with the following structure:
{{
    "interpretation": "What the user wants to accomplish",
    "commands": [
        {{
            "type": "bash|python|sql",
            "command": "actual command to execute",
            "description": "what this command does",
            "safety_level": "safe|moderate|destructive"
        }}
    ],
    "explanation": "Brief explanation of what will happen",
    "risks": ["any potential risks or side effects"]
}}

Guidelines:
- Only provide commands that are safe and follow security best practices
- Never include commands that could harm the system or compromise security
- For destructive operations, clearly mark safety_level as "destructive"
- Prefer relative paths over absolute paths when possible
- Always explain what each command does
- If the request is unclear, ask for clarification"""

        self.code_analysis_template = """You are DevOS, analyzing code for a developer. 

Code Context:
{code_context}

User Request: {user_command}

Provide analysis in JSON format:
{{
    "analysis": "Your code analysis",
    "suggestions": ["improvement suggestions"],
    "issues": ["potential issues found"],
    "commands": [
        {{
            "type": "bash",
            "command": "command to run",
            "description": "what this does",
            "safety_level": "safe"
        }}
    ]
}}"""

        self.git_template = """You are DevOS, helping with git operations.

Git Repository Context:
{git_context}

Current Branch: {current_branch}
Status: {git_status}
Recent Commits: {recent_commits}

User Command: {user_command}

Provide git commands in JSON format:
{{
    "interpretation": "What git operation to perform",
    "commands": [
        {{
            "type": "bash",
            "command": "git command",
            "description": "what this git command does",
            "safety_level": "safe|moderate|destructive"
        }}
    ],
    "explanation": "What will happen with these git operations",
    "risks": ["any risks like data loss"]
}}"""

        self.file_operation_template = """You are DevOS, performing file operations.

File System Context:
- Current Directory: {cwd}
- Files in directory: {current_files}
- Recent changes: {recent_changes}

User Command: {user_command}

Provide file operation commands in JSON format:
{{
    "interpretation": "What file operation to perform",
    "commands": [
        {{
            "type": "bash",
            "command": "file command",
            "description": "what this file operation does",
            "safety_level": "safe|moderate|destructive"
        }}
    ],
    "explanation": "What will happen to the files",
    "risks": ["any risks like data loss or overwriting"]
}}"""

    def build_system_prompt(self, user_command: str, context: Dict[str, Any]) -> str:
        """Build system prompt with context and command"""
        
        # Extract context information safely
        cwd = context.get('cwd', 'unknown')
        user_id = context.get('user_id', 'developer')
        timestamp = context.get('timestamp', datetime.utcnow().isoformat())
        
        # Format context sections
        file_context = self._format_file_context(context.get('files', {}))
        process_context = self._format_process_context(context.get('processes', {}))
        git_context = self._format_git_context(context.get('git', {}))
        env_context = self._format_env_context(context.get('environment', {}))
        
        return self.system_template.format(
            cwd=cwd,
            timestamp=timestamp,
            user_id=user_id,
            file_context=file_context,
            process_context=process_context,
            git_context=git_context,
            env_context=env_context,
            user_command=user_command
        )
    
    def build_specialized_prompt(self, template_type: str, user_command: str, context: Dict[str, Any]) -> str:
        """Build specialized prompt for specific command types"""
        
        if template_type == "code_analysis":
            return self.code_analysis_template.format(
                code_context=json.dumps(context.get('code', {}), indent=2),
                user_command=user_command
            )
        
        elif template_type == "git":
            git_ctx = context.get('git', {})
            return self.git_template.format(
                git_context=json.dumps(git_ctx, indent=2),
                current_branch=git_ctx.get('current_branch', 'unknown'),
                git_status=git_ctx.get('status', 'unknown'),
                recent_commits=git_ctx.get('recent_commits', []),
                user_command=user_command
            )
        
        elif template_type == "file_operation":
            return self.file_operation_template.format(
                cwd=context.get('cwd', 'unknown'),
                current_files=context.get('files', {}).get('current_files', []),
                recent_changes=context.get('files', {}).get('recent_changes', []),
                user_command=user_command
            )
        
        else:
            # Fall back to general template
            return self.build_system_prompt(user_command, context)
    
    def _format_file_context(self, files_dict: Dict) -> str:
        """Format file system context for prompt"""
        
        if not files_dict or 'error' in files_dict:
            return "File system context unavailable"
        
        output = []
        
        if 'current_files' in files_dict:
            current_files = files_dict['current_files'][:10]  # Limit to first 10
            output.append(f"Current directory files: {', '.join(current_files)}")
        
        if 'recent_changes' in files_dict:
            recent = files_dict['recent_changes'][:5]  # Limit to 5 recent
            if recent:
                output.append(f"Recent changes: {', '.join(recent)}")
        
        return '\n'.join(output) if output else "No file context available"
    
    def _format_process_context(self, processes_dict: Dict) -> str:
        """Format process context for prompt"""
        
        if not processes_dict or 'error' in processes_dict:
            return "Process context unavailable"
        
        if 'running_processes' in processes_dict:
            procs = processes_dict['running_processes'][:5]  # Limit to top 5
            if procs:
                return f"Top processes: {', '.join(procs)}"
        
        return "No significant processes"
    
    def _format_git_context(self, git_dict: Dict) -> str:
        """Format git context for prompt"""
        
        if not git_dict or 'error' in git_dict:
            return "Git context unavailable (not in git repository)"
        
        output = []
        
        if 'current_branch' in git_dict:
            output.append(f"Current branch: {git_dict['current_branch']}")
        
        if 'status' in git_dict:
            output.append(f"Git status: {git_dict['status']}")
        
        if 'uncommitted_changes' in git_dict:
            changes = git_dict['uncommitted_changes']
            if changes:
                output.append(f"Uncommitted changes: {len(changes)} files")
        
        return '\n'.join(output) if output else "Clean git repository"
    
    def _format_env_context(self, env_dict: Dict) -> str:
        """Format environment context for prompt (filtered for security)"""
        
        # Only include safe environment variables
        safe_vars = ['PATH', 'HOME', 'USER', 'SHELL', 'LANG', 'PWD']
        
        safe_env = {k: v for k, v in env_dict.items() if k in safe_vars}
        
        if safe_env:
            env_lines = [f"{k}={v}" for k, v in list(safe_env.items())[:5]]
            return '\n'.join(env_lines)
        
        return "Environment variables filtered for security"
    
    def get_error_response_template(self) -> Dict:
        """Get template for error responses"""
        
        return {
            "interpretation": "Unable to process command",
            "commands": [],
            "explanation": "Command could not be processed due to an error",
            "risks": ["Command execution aborted for safety"]
        }