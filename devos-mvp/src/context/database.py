"""
Context database for storing system state and history
"""

import sqlite3
import asyncio
import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import threading

class ContextDatabase:
    """SQLite database for storing context information"""
    
    def __init__(self, db_path: str = "/var/lib/devos/context.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()
        self._ensure_db_directory()
        
    def _ensure_db_directory(self):
        """Ensure database directory exists"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self):
        """Initialize database schema"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                await self._create_tables(conn)
            self.logger.info("Context database initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def _create_tables(self, conn: sqlite3.Connection):
        """Create database tables"""
        
        # File context table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS file_context (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL,
                last_modified TIMESTAMP,
                file_type TEXT,
                project_root TEXT,
                git_status TEXT,
                size INTEGER,
                hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(path, last_modified)
            )
        """)
        
        # Process context table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS process_context (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pid INTEGER NOT NULL,
                name TEXT NOT NULL,
                command_line TEXT,
                start_time TIMESTAMP,
                cpu_percent REAL,
                memory_mb REAL,
                status TEXT,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Command history table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS command_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command TEXT NOT NULL,
                user_id TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN,
                execution_time_ms INTEGER,
                context_snapshot TEXT,
                result_summary TEXT,
                model_used TEXT,
                tokens_consumed INTEGER,
                cost_usd REAL
            )
        """)
        
        # Git context table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS git_context (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repo_path TEXT NOT NULL,
                current_branch TEXT,
                commit_hash TEXT,
                status_summary TEXT,
                uncommitted_changes INTEGER,
                last_commit_message TEXT,
                last_commit_author TEXT,
                last_commit_time TIMESTAMP,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # System events table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS system_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                event_data TEXT,
                severity TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed BOOLEAN DEFAULT FALSE
            )
        """)
        
        # Create indexes for better performance
        conn.execute("CREATE INDEX IF NOT EXISTS idx_file_context_path ON file_context(path)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_command_history_timestamp ON command_history(timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_git_context_repo ON git_context(repo_path)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_system_events_timestamp ON system_events(timestamp)")
        
        conn.commit()
    
    async def store_file_context(self, file_info: Dict[str, Any]):
        """Store file context information"""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO file_context 
                        (path, last_modified, file_type, project_root, git_status, size, hash)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        file_info.get('path'),
                        file_info.get('modified'),
                        file_info.get('type'),
                        file_info.get('project_root'),
                        file_info.get('git_status'),
                        file_info.get('size'),
                        file_info.get('hash')
                    ))
                    conn.commit()
        except Exception as e:
            self.logger.error(f"Error storing file context: {e}")
    
    async def store_command_history(self, command_info: Dict[str, Any]):
        """Store command execution history"""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT INTO command_history 
                        (command, user_id, success, execution_time_ms, context_snapshot, 
                         result_summary, model_used, tokens_consumed, cost_usd)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        command_info.get('command'),
                        command_info.get('user_id'),
                        command_info.get('success'),
                        command_info.get('execution_time_ms'),
                        json.dumps(command_info.get('context', {})),
                        command_info.get('result_summary'),
                        command_info.get('model_used'),
                        command_info.get('tokens_consumed'),
                        command_info.get('cost_usd')
                    ))
                    conn.commit()
        except Exception as e:
            self.logger.error(f"Error storing command history: {e}")
    
    async def store_git_context(self, git_info: Dict[str, Any]):
        """Store git repository context"""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO git_context 
                        (repo_path, current_branch, commit_hash, status_summary, 
                         uncommitted_changes, last_commit_message, last_commit_author, last_commit_time)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        git_info.get('repository_path'),
                        git_info.get('current_branch'),
                        git_info.get('current_commit'),
                        json.dumps(git_info.get('changes_summary', {})),
                        git_info.get('uncommitted_count', 0),
                        git_info.get('last_commit', {}).get('message'),
                        git_info.get('last_commit', {}).get('author'),
                        git_info.get('last_commit', {}).get('time')
                    ))
                    conn.commit()
        except Exception as e:
            self.logger.error(f"Error storing git context: {e}")
    
    async def get_recent_commands(self, user_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent command history"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                if user_id:
                    cursor = conn.execute("""
                        SELECT * FROM command_history 
                        WHERE user_id = ? 
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    """, (user_id, limit))
                else:
                    cursor = conn.execute("""
                        SELECT * FROM command_history 
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    """, (limit,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Error getting recent commands: {e}")
            return []
    
    async def get_file_history(self, file_path: str) -> List[Dict[str, Any]]:
        """Get history for a specific file"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                cursor = conn.execute("""
                    SELECT * FROM file_context 
                    WHERE path = ? 
                    ORDER BY created_at DESC
                """, (file_path,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Error getting file history: {e}")
            return []
    
    async def search_commands(self, search_term: str, user_id: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Search command history"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                if user_id:
                    cursor = conn.execute("""
                        SELECT * FROM command_history 
                        WHERE command LIKE ? AND user_id = ?
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    """, (f"%{search_term}%", user_id, limit))
                else:
                    cursor = conn.execute("""
                        SELECT * FROM command_history 
                        WHERE command LIKE ?
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    """, (f"%{search_term}%", limit))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Error searching commands: {e}")
            return []
    
    async def get_usage_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get usage statistics for the specified period"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Total commands
                cursor = conn.execute("""
                    SELECT COUNT(*) as total_commands, 
                           AVG(execution_time_ms) as avg_execution_time,
                           SUM(tokens_consumed) as total_tokens,
                           SUM(cost_usd) as total_cost
                    FROM command_history 
                    WHERE timestamp > ?
                """, (cutoff_date,))
                
                stats = dict(cursor.fetchone())
                
                # Success rate
                cursor = conn.execute("""
                    SELECT 
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate
                    FROM command_history 
                    WHERE timestamp > ?
                """, (cutoff_date,))
                
                success_rate = cursor.fetchone()[0] or 0
                stats['success_rate'] = success_rate
                
                # Most used models
                cursor = conn.execute("""
                    SELECT model_used, COUNT(*) as usage_count
                    FROM command_history 
                    WHERE timestamp > ? AND model_used IS NOT NULL
                    GROUP BY model_used
                    ORDER BY usage_count DESC
                    LIMIT 5
                """, (cutoff_date,))
                
                model_usage = [dict(row) for row in cursor.fetchall()]
                stats['model_usage'] = model_usage
                
                # Daily command counts
                cursor = conn.execute("""
                    SELECT DATE(timestamp) as date, COUNT(*) as commands
                    FROM command_history 
                    WHERE timestamp > ?
                    GROUP BY DATE(timestamp)
                    ORDER BY date DESC
                    LIMIT 30
                """, (cutoff_date,))
                
                daily_stats = [dict(row) for row in cursor.fetchall()]
                stats['daily_commands'] = daily_stats
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Error getting usage statistics: {e}")
            return {}
    
    async def cleanup_old_data(self, retention_days: int = 90):
        """Clean up old data beyond retention period"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    # Clean up old command history
                    cursor = conn.execute("""
                        DELETE FROM command_history 
                        WHERE timestamp < ?
                    """, (cutoff_date,))
                    
                    commands_deleted = cursor.rowcount
                    
                    # Clean up old file context
                    cursor = conn.execute("""
                        DELETE FROM file_context 
                        WHERE created_at < ?
                    """, (cutoff_date,))
                    
                    files_deleted = cursor.rowcount
                    
                    # Clean up old git context
                    cursor = conn.execute("""
                        DELETE FROM git_context 
                        WHERE recorded_at < ?
                    """, (cutoff_date,))
                    
                    git_deleted = cursor.rowcount
                    
                    conn.commit()
                    
                    self.logger.info(f"Cleaned up old data: {commands_deleted} commands, "
                                   f"{files_deleted} file records, {git_deleted} git records")
                    
        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {e}")
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                stats = {}
                
                # Table sizes
                for table in ['command_history', 'file_context', 'git_context', 'system_events']:
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                    stats[f"{table}_count"] = cursor.fetchone()[0]
                
                # Database file size
                db_size = Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0
                stats['database_size_mb'] = db_size / (1024 * 1024)
                
                # Oldest and newest records
                cursor = conn.execute("SELECT MIN(timestamp), MAX(timestamp) FROM command_history")
                oldest, newest = cursor.fetchone()
                stats['oldest_command'] = oldest
                stats['newest_command'] = newest
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Error getting database stats: {e}")
            return {}