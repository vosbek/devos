"""
Process monitoring for DevOS context engine
"""

import asyncio
import logging
import psutil
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

class ProcessMonitor:
    """Monitor system processes and provide context"""
    
    def __init__(self, update_interval: int = 30):
        self.update_interval = update_interval
        self.running = False
        self.process_cache = {}
        self.logger = logging.getLogger(__name__)
        self.monitor_task = None
        
    async def start(self):
        """Start process monitoring"""
        try:
            self.running = True
            self.monitor_task = asyncio.create_task(self._monitor_loop())
            self.logger.info("Process monitor started")
            
        except Exception as e:
            self.logger.error(f"Failed to start process monitor: {e}")
            raise
    
    async def stop(self):
        """Stop process monitoring"""
        self.running = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Process monitor stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                await self._update_process_cache()
                await asyncio.sleep(self.update_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in process monitor loop: {e}")
                await asyncio.sleep(5)  # Short delay before retry
    
    async def _update_process_cache(self):
        """Update cached process information"""
        try:
            current_processes = {}
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'create_time']):
                try:
                    pinfo = proc.info
                    current_processes[pinfo['pid']] = {
                        'name': pinfo['name'],
                        'cpu_percent': pinfo['cpu_percent'],
                        'memory_percent': pinfo['memory_percent'],
                        'create_time': pinfo['create_time'],
                        'status': proc.status(),
                        'last_seen': datetime.utcnow()
                    }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            self.process_cache = current_processes
            
        except Exception as e:
            self.logger.error(f"Error updating process cache: {e}")
    
    async def get_current_processes(self, limit: int = 20) -> Dict[str, Any]:
        """Get current running processes"""
        try:
            if not self.process_cache:
                await self._update_process_cache()
            
            # Sort by CPU usage
            sorted_processes = sorted(
                self.process_cache.items(),
                key=lambda x: x[1]['cpu_percent'] or 0,
                reverse=True
            )
            
            top_processes = []
            for pid, proc_info in sorted_processes[:limit]:
                top_processes.append({
                    'pid': pid,
                    'name': proc_info['name'],
                    'cpu_percent': proc_info['cpu_percent'] or 0,
                    'memory_percent': proc_info['memory_percent'] or 0,
                    'status': proc_info['status']
                })
            
            # System summary
            cpu_count = psutil.cpu_count()
            memory = psutil.virtual_memory()
            
            return {
                'top_processes': top_processes,
                'total_processes': len(self.process_cache),
                'system_summary': {
                    'cpu_count': cpu_count,
                    'cpu_percent': psutil.cpu_percent(interval=1),
                    'memory_total': memory.total,
                    'memory_used': memory.used,
                    'memory_percent': memory.percent
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting current processes: {e}")
            return {'error': str(e)}
    
    async def find_processes(self, name_pattern: str) -> Dict[str, Any]:
        """Find processes matching name pattern"""
        try:
            if not self.process_cache:
                await self._update_process_cache()
            
            matching_processes = []
            
            for pid, proc_info in self.process_cache.items():
                if name_pattern.lower() in proc_info['name'].lower():
                    matching_processes.append({
                        'pid': pid,
                        'name': proc_info['name'],
                        'cpu_percent': proc_info['cpu_percent'] or 0,
                        'memory_percent': proc_info['memory_percent'] or 0,
                        'status': proc_info['status'],
                        'create_time': proc_info['create_time']
                    })
            
            return {
                'matching_processes': matching_processes,
                'count': len(matching_processes),
                'pattern': name_pattern
            }
            
        except Exception as e:
            self.logger.error(f"Error finding processes: {e}")
            return {'error': str(e)}
    
    async def get_process_details(self, pid: int) -> Dict[str, Any]:
        """Get detailed information about a specific process"""
        try:
            proc = psutil.Process(pid)
            
            # Basic process info
            proc_info = {
                'pid': pid,
                'name': proc.name(),
                'status': proc.status(),
                'create_time': proc.create_time(),
                'cpu_percent': proc.cpu_percent(),
                'memory_percent': proc.memory_percent()
            }
            
            # Additional details (may fail for some processes)
            try:
                proc_info.update({
                    'ppid': proc.ppid(),
                    'username': proc.username(),
                    'cmdline': ' '.join(proc.cmdline()),
                    'cwd': proc.cwd(),
                    'num_threads': proc.num_threads()
                })
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                proc_info['access_limited'] = True
            
            # Memory details
            try:
                memory_info = proc.memory_info()
                proc_info['memory'] = {
                    'rss': memory_info.rss,
                    'vms': memory_info.vms
                }
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass
            
            # CPU times
            try:
                cpu_times = proc.cpu_times()
                proc_info['cpu_times'] = {
                    'user': cpu_times.user,
                    'system': cpu_times.system
                }
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass
            
            return proc_info
            
        except psutil.NoSuchProcess:
            return {'error': f"Process {pid} not found"}
        except Exception as e:
            self.logger.error(f"Error getting process details: {e}")
            return {'error': str(e)}
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get overall system statistics"""
        try:
            # CPU information
            cpu_stats = {
                'count': psutil.cpu_count(),
                'percent': psutil.cpu_percent(interval=1),
                'freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
            }
            
            # Memory information
            memory = psutil.virtual_memory()
            memory_stats = {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'percent': memory.percent
            }
            
            # Disk information
            disk_usage = psutil.disk_usage('/')
            disk_stats = {
                'total': disk_usage.total,
                'used': disk_usage.used,
                'free': disk_usage.free,
                'percent': (disk_usage.used / disk_usage.total) * 100
            }
            
            # Network information
            network_stats = {}
            try:
                net_io = psutil.net_io_counters()
                network_stats = {
                    'bytes_sent': net_io.bytes_sent,
                    'bytes_recv': net_io.bytes_recv,
                    'packets_sent': net_io.packets_sent,
                    'packets_recv': net_io.packets_recv
                }
            except Exception:
                network_stats = {'error': 'Network stats unavailable'}
            
            # Boot time
            boot_time = psutil.boot_time()
            uptime = datetime.utcnow() - datetime.fromtimestamp(boot_time)
            
            return {
                'cpu': cpu_stats,
                'memory': memory_stats,
                'disk': disk_stats,
                'network': network_stats,
                'boot_time': boot_time,
                'uptime_seconds': uptime.total_seconds(),
                'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None,
                'process_count': len(psutil.pids())
            }
            
        except Exception as e:
            self.logger.error(f"Error getting system stats: {e}")
            return {'error': str(e)}
    
    async def get_resource_usage_summary(self) -> Dict[str, Any]:
        """Get a summary of resource usage suitable for LLM context"""
        try:
            system_stats = await self.get_system_stats()
            top_processes = await self.get_current_processes(5)
            
            # Create a concise summary
            summary = {
                'system_load': {
                    'cpu_percent': system_stats.get('cpu', {}).get('percent', 0),
                    'memory_percent': system_stats.get('memory', {}).get('percent', 0),
                    'disk_percent': system_stats.get('disk', {}).get('percent', 0)
                },
                'top_cpu_processes': [
                    f"{p['name']} ({p['cpu_percent']:.1f}%)"
                    for p in top_processes.get('top_processes', [])[:3]
                    if p['cpu_percent'] > 1.0
                ],
                'high_memory_processes': [
                    f"{p['name']} ({p['memory_percent']:.1f}%)"
                    for p in top_processes.get('top_processes', [])
                    if p['memory_percent'] > 5.0
                ][:3],
                'total_processes': top_processes.get('total_processes', 0)
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting resource usage summary: {e}")
            return {'error': str(e)}