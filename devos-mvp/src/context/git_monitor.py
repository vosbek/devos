"""
Git repository monitoring for DevOS context engine
"""

import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import os

class GitMonitor:
    """Monitor git repositories and provide context"""
    
    def __init__(self, repo_paths: List[str] = None):
        self.repo_paths = repo_paths or ["/home"]
        self.git_repos = {}
        self.running = False
        self.logger = logging.getLogger(__name__)
        
    async def start(self):
        """Start git monitoring"""
        try:
            await self._discover_repositories()
            self.running = True
            self.logger.info(f"Git monitor started, found {len(self.git_repos)} repositories")
            
        except Exception as e:
            self.logger.error(f"Failed to start git monitor: {e}")
            raise
    
    async def stop(self):
        """Stop git monitoring"""
        self.running = False
        self.logger.info("Git monitor stopped")
    
    async def _discover_repositories(self):
        """Discover git repositories in watch paths"""
        discovered_repos = {}
        
        for base_path in self.repo_paths:
            try:
                path = Path(base_path)
                if not path.exists():
                    continue
                
                # Look for .git directories
                for git_dir in path.rglob('.git'):
                    if git_dir.is_dir():
                        repo_path = git_dir.parent
                        discovered_repos[str(repo_path)] = {
                            'path': str(repo_path),
                            'git_dir': str(git_dir),
                            'discovered_at': datetime.utcnow()
                        }
                        
            except Exception as e:
                self.logger.warning(f"Error discovering repos in {base_path}: {e}")
        
        self.git_repos = discovered_repos
    
    async def _run_git_command(self, repo_path: str, command: List[str]) -> Dict[str, Any]:
        """Run a git command in a repository"""
        try:
            full_command = ['git'] + command
            result = subprocess.run(
                full_command,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                'returncode': result.returncode,
                'stdout': result.stdout.strip(),
                'stderr': result.stderr.strip(),
                'command': ' '.join(full_command)
            }
            
        except subprocess.TimeoutExpired:
            return {'error': 'Git command timed out'}
        except Exception as e:
            return {'error': str(e)}
    
    async def get_repository_status(self, repo_path: str = None) -> Dict[str, Any]:
        """Get git status for a repository"""
        try:
            # If no path specified, try current directory
            if repo_path is None:
                repo_path = os.getcwd()
            
            # Check if it's a git repository
            if not await self._is_git_repository(repo_path):
                return {'error': 'Not a git repository'}
            
            status_info = {}
            
            # Get current branch
            branch_result = await self._run_git_command(repo_path, ['branch', '--show-current'])
            if branch_result.get('returncode') == 0:
                status_info['current_branch'] = branch_result['stdout'] or 'detached'
            else:
                status_info['current_branch'] = 'unknown'
            
            # Get status
            status_result = await self._run_git_command(repo_path, ['status', '--porcelain'])
            if status_result.get('returncode') == 0:
                status_lines = status_result['stdout'].split('\n') if status_result['stdout'] else []
                
                staged_files = []
                modified_files = []
                untracked_files = []
                
                for line in status_lines:
                    if len(line) >= 3:
                        status_code = line[:2]
                        file_path = line[3:]
                        
                        if status_code[0] in ['A', 'M', 'D', 'R', 'C']:
                            staged_files.append(file_path)
                        if status_code[1] in ['M', 'D']:
                            modified_files.append(file_path)
                        if status_code == '??':
                            untracked_files.append(file_path)
                
                status_info.update({
                    'staged_files': staged_files,
                    'modified_files': modified_files,
                    'untracked_files': untracked_files,
                    'clean': len(status_lines) == 0
                })
            
            # Get recent commits
            log_result = await self._run_git_command(
                repo_path, 
                ['log', '--oneline', '-10', '--format=%h|%s|%an|%ar']
            )
            if log_result.get('returncode') == 0 and log_result['stdout']:
                commits = []
                for line in log_result['stdout'].split('\n'):
                    if '|' in line:
                        parts = line.split('|', 3)
                        if len(parts) >= 4:
                            commits.append({
                                'hash': parts[0],
                                'message': parts[1],
                                'author': parts[2],
                                'time': parts[3]
                            })
                status_info['recent_commits'] = commits
            
            # Get remote information
            remote_result = await self._run_git_command(repo_path, ['remote', '-v'])
            if remote_result.get('returncode') == 0 and remote_result['stdout']:
                remotes = {}
                for line in remote_result['stdout'].split('\n'):
                    parts = line.split()
                    if len(parts) >= 2:
                        remote_name = parts[0]
                        remote_url = parts[1]
                        if remote_name not in remotes:
                            remotes[remote_name] = remote_url
                status_info['remotes'] = remotes
            
            status_info['repository_path'] = repo_path
            return status_info
            
        except Exception as e:
            self.logger.error(f"Error getting git status: {e}")
            return {'error': str(e)}
    
    async def _is_git_repository(self, path: str) -> bool:
        """Check if a path is a git repository"""
        try:
            result = await self._run_git_command(path, ['rev-parse', '--git-dir'])
            return result.get('returncode') == 0
        except Exception:
            return False
    
    async def get_all_repositories_status(self) -> Dict[str, Any]:
        """Get status for all discovered repositories"""
        try:
            if not self.git_repos:
                await self._discover_repositories()
            
            all_status = {}
            
            for repo_path in self.git_repos.keys():
                try:
                    status = await self.get_repository_status(repo_path)
                    all_status[repo_path] = status
                except Exception as e:
                    all_status[repo_path] = {'error': str(e)}
            
            return {
                'repositories': all_status,
                'total_repositories': len(self.git_repos)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting all repositories status: {e}")
            return {'error': str(e)}
    
    async def get_git_summary(self, repo_path: str = None) -> Dict[str, Any]:
        """Get a concise git summary suitable for LLM context"""
        try:
            status = await self.get_repository_status(repo_path)
            
            if 'error' in status:
                return status
            
            # Create concise summary
            summary = {
                'current_branch': status.get('current_branch', 'unknown'),
                'is_clean': status.get('clean', True),
                'changes_summary': {
                    'staged': len(status.get('staged_files', [])),
                    'modified': len(status.get('modified_files', [])),
                    'untracked': len(status.get('untracked_files', []))
                }
            }
            
            # Add recent commit info
            recent_commits = status.get('recent_commits', [])
            if recent_commits:
                summary['last_commit'] = {
                    'message': recent_commits[0]['message'],
                    'author': recent_commits[0]['author'],
                    'time': recent_commits[0]['time']
                }
            
            # Add remote info
            remotes = status.get('remotes', {})
            if 'origin' in remotes:
                summary['origin'] = remotes['origin']
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting git summary: {e}")
            return {'error': str(e)}
    
    async def execute_git_command(self, command: str, repo_path: str = None) -> Dict[str, Any]:
        """Execute a git command safely"""
        try:
            if repo_path is None:
                repo_path = os.getcwd()
            
            if not await self._is_git_repository(repo_path):
                return {'error': 'Not a git repository'}
            
            # Parse command (remove 'git' if present)
            command_parts = command.strip().split()
            if command_parts[0].lower() == 'git':
                command_parts = command_parts[1:]
            
            # Whitelist of safe git commands
            safe_commands = [
                'status', 'log', 'show', 'diff', 'branch', 'remote',
                'ls-files', 'ls-tree', 'rev-parse', 'describe'
            ]
            
            if not command_parts or command_parts[0] not in safe_commands:
                return {'error': f'Git command not allowed: {command_parts[0] if command_parts else "empty"}'}
            
            result = await self._run_git_command(repo_path, command_parts)
            
            return {
                'command': 'git ' + ' '.join(command_parts),
                'output': result.get('stdout', ''),
                'error': result.get('stderr', ''),
                'success': result.get('returncode') == 0
            }
            
        except Exception as e:
            self.logger.error(f"Error executing git command: {e}")
            return {'error': str(e)}
    
    async def get_repository_info(self, repo_path: str = None) -> Dict[str, Any]:
        """Get general information about a repository"""
        try:
            if repo_path is None:
                repo_path = os.getcwd()
            
            if not await self._is_git_repository(repo_path):
                return {'error': 'Not a git repository'}
            
            info = {'repository_path': repo_path}
            
            # Get repository root
            root_result = await self._run_git_command(repo_path, ['rev-parse', '--show-toplevel'])
            if root_result.get('returncode') == 0:
                info['root_path'] = root_result['stdout']
            
            # Get all branches
            branches_result = await self._run_git_command(repo_path, ['branch', '-a'])
            if branches_result.get('returncode') == 0:
                branches = []
                for line in branches_result['stdout'].split('\n'):
                    branch = line.strip().replace('* ', '').replace('remotes/', '')
                    if branch and not branch.startswith('HEAD'):
                        branches.append(branch)
                info['all_branches'] = list(set(branches))
            
            # Get tags
            tags_result = await self._run_git_command(repo_path, ['tag', '-l'])
            if tags_result.get('returncode') == 0:
                tags = [tag.strip() for tag in tags_result['stdout'].split('\n') if tag.strip()]
                info['tags'] = tags[-10:]  # Last 10 tags
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting repository info: {e}")
            return {'error': str(e)}