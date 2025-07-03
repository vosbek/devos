"""
File system monitoring for DevOS context engine
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import watchdog.observers
from watchdog.events import FileSystemEventHandler
import hashlib

class FileEventHandler(FileSystemEventHandler):
    """Handle file system events"""
    
    def __init__(self, file_monitor):
        self.file_monitor = file_monitor
        self.logger = logging.getLogger(__name__)
    
    def on_any_event(self, event):
        """Handle any file system event"""
        if not event.is_directory:
            asyncio.create_task(self.file_monitor.handle_file_event(event))

class FileMonitor:
    """Monitor file system changes and provide context"""
    
    def __init__(self, watch_paths: List[str] = None):
        self.watch_paths = watch_paths or ["/home", "/tmp"]
        self.observer = watchdog.observers.Observer()
        self.event_handler = FileEventHandler(self)
        self.recent_changes = []
        self.running = False
        self.logger = logging.getLogger(__name__)
        
        # Limit tracking to prevent memory issues
        self.max_recent_changes = 100
        self.change_retention_hours = 24
    
    async def start(self):
        """Start file monitoring"""
        try:
            for path in self.watch_paths:
                if Path(path).exists():
                    self.observer.schedule(self.event_handler, path, recursive=True)
                    self.logger.info(f"Started monitoring {path}")
            
            self.observer.start()
            self.running = True
            self.logger.info("File monitor started")
            
        except Exception as e:
            self.logger.error(f"Failed to start file monitor: {e}")
            raise
    
    async def stop(self):
        """Stop file monitoring"""
        self.running = False
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
        self.logger.info("File monitor stopped")
    
    async def handle_file_event(self, event):
        """Handle individual file system event"""
        try:
            event_info = {
                'timestamp': datetime.utcnow(),
                'event_type': event.event_type,
                'src_path': event.src_path,
                'is_directory': event.is_directory
            }
            
            if hasattr(event, 'dest_path'):
                event_info['dest_path'] = event.dest_path
            
            # Add to recent changes
            self.recent_changes.append(event_info)
            
            # Cleanup old events
            await self.cleanup_old_events()
            
        except Exception as e:
            self.logger.error(f"Error handling file event: {e}")
    
    async def cleanup_old_events(self):
        """Remove old events to prevent memory buildup"""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.change_retention_hours)
        
        self.recent_changes = [
            event for event in self.recent_changes 
            if event['timestamp'] > cutoff_time
        ]
        
        # Also limit by count
        if len(self.recent_changes) > self.max_recent_changes:
            self.recent_changes = self.recent_changes[-self.max_recent_changes:]
    
    async def get_recent_changes(self, limit: int = 20) -> Dict[str, Any]:
        """Get recent file system changes"""
        try:
            await self.cleanup_old_events()
            
            recent = self.recent_changes[-limit:] if self.recent_changes else []
            
            # Summarize by type
            change_summary = {}
            for event in recent:
                event_type = event['event_type']
                if event_type not in change_summary:
                    change_summary[event_type] = 0
                change_summary[event_type] += 1
            
            return {
                'recent_changes': [
                    {
                        'timestamp': event['timestamp'].isoformat(),
                        'type': event['event_type'],
                        'path': os.path.basename(event['src_path']),
                        'full_path': event['src_path']
                    }
                    for event in recent
                ],
                'change_summary': change_summary,
                'total_changes': len(self.recent_changes)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting recent changes: {e}")
            return {'error': str(e)}
    
    async def get_directory_info(self, path: str = None) -> Dict[str, Any]:
        """Get information about a directory"""
        try:
            target_path = Path(path) if path else Path.cwd()
            
            if not target_path.exists():
                return {'error': f"Path does not exist: {target_path}"}
            
            if not target_path.is_dir():
                return {'error': f"Path is not a directory: {target_path}"}
            
            # Get directory contents
            files = []
            directories = []
            total_size = 0
            
            try:
                for item in target_path.iterdir():
                    if item.is_file():
                        size = item.stat().st_size
                        files.append({
                            'name': item.name,
                            'size': size,
                            'modified': datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                        })
                        total_size += size
                    elif item.is_dir():
                        directories.append({
                            'name': item.name,
                            'modified': datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                        })
            except PermissionError:
                return {'error': f"Permission denied accessing: {target_path}"}
            
            return {
                'path': str(target_path),
                'files': sorted(files, key=lambda x: x['name']),
                'directories': sorted(directories, key=lambda x: x['name']),
                'file_count': len(files),
                'directory_count': len(directories),
                'total_size': total_size
            }
            
        except Exception as e:
            self.logger.error(f"Error getting directory info: {e}")
            return {'error': str(e)}
    
    async def find_files(self, pattern: str = None, extension: str = None, 
                        path: str = None, limit: int = 50) -> Dict[str, Any]:
        """Find files matching criteria"""
        try:
            search_path = Path(path) if path else Path.cwd()
            
            if not search_path.exists():
                return {'error': f"Search path does not exist: {search_path}"}
            
            matches = []
            
            # Use different search strategies
            if extension:
                # Search by extension
                pattern = f"*.{extension.lstrip('.')}"
                matches = list(search_path.rglob(pattern))
            elif pattern:
                # Search by pattern
                matches = list(search_path.rglob(pattern))
            else:
                # List all files
                matches = [f for f in search_path.rglob("*") if f.is_file()]
            
            # Limit results and add metadata
            result_files = []
            for match in matches[:limit]:
                try:
                    stat = match.stat()
                    result_files.append({
                        'name': match.name,
                        'path': str(match),
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'extension': match.suffix
                    })
                except (OSError, PermissionError):
                    continue
            
            return {
                'matches': result_files,
                'total_found': len(matches),
                'limited_to': limit,
                'search_path': str(search_path)
            }
            
        except Exception as e:
            self.logger.error(f"Error finding files: {e}")
            return {'error': str(e)}
    
    async def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get detailed information about a specific file"""
        try:
            path = Path(file_path)
            
            if not path.exists():
                return {'error': f"File does not exist: {file_path}"}
            
            if not path.is_file():
                return {'error': f"Path is not a file: {file_path}"}
            
            stat = path.stat()
            
            # Basic file info
            info = {
                'name': path.name,
                'path': str(path),
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'accessed': datetime.fromtimestamp(stat.st_atime).isoformat(),
                'extension': path.suffix,
                'permissions': oct(stat.st_mode)[-3:]
            }
            
            # File type detection
            if path.suffix.lower() in ['.py', '.js', '.java', '.cpp', '.c', '.go', '.rs']:
                info['type'] = 'code'
            elif path.suffix.lower() in ['.txt', '.md', '.rst', '.doc', '.docx']:
                info['type'] = 'document'
            elif path.suffix.lower() in ['.jpg', '.png', '.gif', '.svg', '.bmp']:
                info['type'] = 'image'
            else:
                info['type'] = 'other'
            
            # Calculate file hash for change detection
            if stat.st_size < 1024 * 1024:  # Only for files < 1MB
                try:
                    with open(path, 'rb') as f:
                        content = f.read()
                        info['md5_hash'] = hashlib.md5(content).hexdigest()
                except (OSError, PermissionError):
                    pass
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting file info: {e}")
            return {'error': str(e)}