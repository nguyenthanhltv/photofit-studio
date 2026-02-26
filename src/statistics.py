"""Statistics tracking for PhotoFit Studio.

Tracks processing statistics for two main menus:
1. Tiếp nhận (Import): Statistics for image import/renaming
2. Xử lý (Processing): Statistics for batch image processing
"""

import json
import os
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict


class ImportStats:
    """Statistics tracker for Tiếp nhận (Import) menu operations."""
    
    def __init__(self, stats_file: str = None):
        self.stats_file = stats_file or self._default_import_stats_file()
        self.stats = self._load_stats()
    
    @staticmethod
    def _default_import_stats_file() -> str:
        base = Path(__file__).parent.parent
        return str(base / "logs" / "import_statistics.json")
    
    def _load_stats(self) -> dict:
        """Load statistics from file."""
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "total_processed": 0,
            "total_success": 0,
            "total_errors": 0,
            "total_time_seconds": 0.0,
            "sessions": [],
            "daily_stats": {},
            "last_updated": datetime.now().isoformat()
        }
    
    def _save_stats(self):
        """Save statistics to file."""
        os.makedirs(os.path.dirname(self.stats_file), exist_ok=True)
        self.stats["last_updated"] = datetime.now().isoformat()
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)
    
    def record_import(self, renamed: bool = True, duration: float = 0.0):
        """Record an import operation.
        
        Args:
            renamed: Whether the file was successfully renamed
            duration: Processing duration in seconds
        """
        self.stats["total_processed"] += 1
        self.stats["total_time_seconds"] += duration
        
        if renamed:
            self.stats["total_success"] += 1
        
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in self.stats["daily_stats"]:
            self.stats["daily_stats"][today] = {
                "processed": 0,
                "success": 0,
                "errors": 0,
                "time_seconds": 0.0
            }
        
        self.stats["daily_stats"][today]["processed"] += 1
        self.stats["daily_stats"][today]["time_seconds"] += duration
        if renamed:
            self.stats["daily_stats"][today]["success"] += 1
        else:
            self.stats["daily_stats"][today]["errors"] += 1
        
        self._save_stats()
    
    def record_error(self):
        """Record an import error."""
        self.stats["total_processed"] += 1
        self.stats["total_errors"] += 1
        
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in self.stats["daily_stats"]:
            self.stats["daily_stats"][today] = {
                "processed": 0,
                "success": 0,
                "errors": 0,
                "time_seconds": 0.0
            }
        
        self.stats["daily_stats"][today]["processed"] += 1
        self.stats["daily_stats"][today]["errors"] += 1
        
        self._save_stats()
    
    def get_summary(self) -> dict:
        """Get import statistics summary."""
        total = self.stats["total_processed"]
        success = self.stats["total_success"]
        errors = self.stats["total_errors"]
        
        avg_time = 0.0
        if total > 0:
            avg_time = self.stats["total_time_seconds"] / total
        
        return {
            "total_processed": total,
            "total_success": success,
            "total_errors": errors,
            "success_rate": (success / total * 100) if total > 0 else 0,
            "average_time_seconds": avg_time,
            "total_time_formatted": self._format_time(self.stats["total_time_seconds"]),
            "last_updated": self.stats.get("last_updated", "N/A")
        }
    
    def get_daily_stats(self, days: int = 7) -> List[dict]:
        """Get daily import statistics."""
        result = []
        today = datetime.now()
        
        for i in range(days):
            date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            stats = self.stats["daily_stats"].get(date, {
                "processed": 0,
                "success": 0,
                "errors": 0,
                "time_seconds": 0.0
            })
            
            result.append({
                "date": date,
                "processed": stats["processed"],
                "success": stats["success"],
                "errors": stats["errors"],
                "success_rate": (stats["success"] / stats["processed"] * 100) 
                    if stats["processed"] > 0 else 0,
                "time_seconds": stats["time_seconds"]
            })
        
        return result
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds to human readable string."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            mins = int(seconds / 60)
            secs = int(seconds % 60)
            return f"{mins}m {secs}s"
        else:
            hours = int(seconds / 3600)
            mins = int((seconds % 3600) / 60)
            return f"{hours}h {mins}m"
    
    def reset_stats(self):
        """Reset all import statistics."""
        self.stats = {
            "total_processed": 0,
            "total_success": 0,
            "total_errors": 0,
            "total_time_seconds": 0.0,
            "sessions": [],
            "daily_stats": {},
            "last_updated": datetime.now().isoformat()
        }
        self._save_stats()


class ProcessingStats:
    """Statistics tracker for Xử lý (Processing) menu operations."""
    
    def __init__(self, stats_file: str = None):
        self.stats_file = stats_file or self._default_stats_file()
        self.stats = self._load_stats()
    
    @staticmethod
    def _default_stats_file() -> str:
        base = Path(__file__).parent.parent
        return str(base / "logs" / "statistics.json")
    
    def _load_stats(self) -> dict:
        """Load statistics from file."""
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        # Default stats structure
        return {
            "total_processed": 0,
            "total_success": 0,
            "total_errors": 0,
            "total_time_seconds": 0.0,
            "sessions": [],
            "daily_stats": {},
            "template_usage": {},
            "last_updated": datetime.now().isoformat()
        }
    
    def _save_stats(self):
        """Save statistics to file."""
        os.makedirs(os.path.dirname(self.stats_file), exist_ok=True)
        self.stats["last_updated"] = datetime.now().isoformat()
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)
    
    def record_success(self, duration: float, template: str = None):
        """Record a successful processing.
        
        Args:
            duration: Processing duration in seconds
            template: Template used (optional)
        """
        self.stats["total_processed"] += 1
        self.stats["total_success"] += 1
        self.stats["total_time_seconds"] += duration
        
        # Update daily stats
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in self.stats["daily_stats"]:
            self.stats["daily_stats"][today] = {
                "processed": 0,
                "success": 0,
                "errors": 0,
                "time_seconds": 0.0
            }
        
        self.stats["daily_stats"][today]["processed"] += 1
        self.stats["daily_stats"][today]["success"] += 1
        self.stats["daily_stats"][today]["time_seconds"] += duration
        
        # Track template usage
        if template:
            if template not in self.stats["template_usage"]:
                self.stats["template_usage"][template] = 0
            self.stats["template_usage"][template] += 1
        
        self._save_stats()
    
    def record_error(self):
        """Record a processing error."""
        self.stats["total_processed"] += 1
        self.stats["total_errors"] += 1
        
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in self.stats["daily_stats"]:
            self.stats["daily_stats"][today] = {
                "processed": 0,
                "success": 0,
                "errors": 0,
                "time_seconds": 0.0
            }
        
        self.stats["daily_stats"][today]["processed"] += 1
        self.stats["daily_stats"][today]["errors"] += 1
        
        self._save_stats()
    
    def start_session(self) -> str:
        """Start a new processing session.
        
        Returns:
            Session ID
        """
        session_id = f"session_{int(time.time())}"
        session = {
            "id": session_id,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "processed": 0,
            "success": 0,
            "errors": 0,
            "duration_seconds": 0.0
        }
        self.stats["sessions"].append(session)
        return session_id
    
    def end_session(self, session_id: str):
        """End a processing session."""
        for session in self.stats["sessions"]:
            if session["id"] == session_id:
                session["end_time"] = datetime.now().isoformat()
                try:
                    start = datetime.fromisoformat(session["start_time"])
                    end = datetime.fromisoformat(session["end_time"])
                    session["duration_seconds"] = (end - start).total_seconds()
                except:
                    pass
                break
        self._save_stats()
    
    def update_session(self, session_id: str, success: bool = True):
        """Update session statistics."""
        for session in self.stats["sessions"]:
            if session["id"] == session_id:
                session["processed"] += 1
                if success:
                    session["success"] += 1
                else:
                    session["errors"] += 1
                break
        self._save_stats()
    
    def get_summary(self) -> dict:
        """Get statistics summary.
        
        Returns:
            Summary dict with key metrics
        """
        total = self.stats["total_processed"]
        success = self.stats["total_success"]
        errors = self.stats["total_errors"]
        
        avg_time = 0.0
        if total > 0:
            avg_time = self.stats["total_time_seconds"] / total
        
        return {
            "total_processed": total,
            "total_success": success,
            "total_errors": errors,
            "success_rate": (success / total * 100) if total > 0 else 0,
            "average_time_seconds": avg_time,
            "total_time_formatted": self._format_time(self.stats["total_time_seconds"]),
            "last_updated": self.stats.get("last_updated", "N/A")
        }
    
    def get_daily_stats(self, days: int = 7) -> List[dict]:
        """Get daily statistics for the last N days.
        
        Args:
            days: Number of days to include
            
        Returns:
            List of daily stat dicts
        """
        result = []
        today = datetime.now()
        
        for i in range(days):
            date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            stats = self.stats["daily_stats"].get(date, {
                "processed": 0,
                "success": 0,
                "errors": 0,
                "time_seconds": 0.0
            })
            
            result.append({
                "date": date,
                "processed": stats["processed"],
                "success": stats["success"],
                "errors": stats["errors"],
                "success_rate": (stats["success"] / stats["processed"] * 100) 
                    if stats["processed"] > 0 else 0,
                "time_seconds": stats["time_seconds"]
            })
        
        return result
    
    def get_template_usage(self) -> Dict[str, int]:
        """Get template usage statistics."""
        return self.stats.get("template_usage", {})
    
    def get_recent_sessions(self, limit: int = 10) -> List[dict]:
        """Get recent processing sessions."""
        sessions = self.stats.get("sessions", [])
        sessions.sort(key=lambda x: x.get("start_time", ""), reverse=True)
        return sessions[:limit]
    
    def reset_stats(self):
        """Reset all statistics."""
        self.stats = {
            "total_processed": 0,
            "total_success": 0,
            "total_errors": 0,
            "total_time_seconds": 0.0,
            "sessions": [],
            "daily_stats": {},
            "template_usage": {},
            "last_updated": datetime.now().isoformat()
        }
        self._save_stats()
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds to human readable string."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            mins = int(seconds / 60)
            secs = int(seconds % 60)
            return f"{mins}m {secs}s"
        else:
            hours = int(seconds / 3600)
            mins = int((seconds % 3600) / 60)
            return f"{hours}h {mins}m"


class SessionStats:
    """Context manager for tracking a single processing session."""
    
    def __init__(self, stats: ProcessingStats, template: str = None):
        self.stats = stats
        self.template = template
        self.session_id = None
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.session_id = self.stats.start_session()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session_id:
            self.stats.end_session(self.session_id)
    
    def record(self, success: bool = True):
        """Record a result."""
        if self.start_time:
            duration = time.time() - self.start_time
            if success:
                self.stats.record_success(duration, self.template)
            else:
                self.stats.record_error()
            self.stats.update_session(self.session_id, success)


# Global stats instances
_global_stats: Optional[ProcessingStats] = None
_global_import_stats: Optional[ImportStats] = None


def get_stats() -> ProcessingStats:
    """Get global processing stats instance (for Xử lý menu)."""
    global _global_stats
    if _global_stats is None:
        _global_stats = ProcessingStats()
    return _global_stats


def get_import_stats() -> ImportStats:
    """Get global import stats instance (for Tiếp nhận menu)."""
    global _global_import_stats
    if _global_import_stats is None:
        _global_import_stats = ImportStats()
    return _global_import_stats


def record_success(duration: float, template: str = None):
    """Quick helper to record processing success (Xử lý menu)."""
    get_stats().record_success(duration, template)


def record_error():
    """Quick helper to record processing error (Xử lý menu)."""
    get_stats().record_error()


def record_import(renamed: bool = True, duration: float = 0.0):
    """Quick helper to record import success (Tiếp nhận menu)."""
    get_import_stats().record_import(renamed, duration)


def record_import_error():
    """Quick helper to record import error (Tiếp nhận menu)."""
    get_import_stats().record_error()
