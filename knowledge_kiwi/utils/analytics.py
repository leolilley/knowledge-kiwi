"""
Tool execution analytics and logging.

Provides:
- Logging tool executions to history
- Analyzing tool performance
- Identifying patterns in usage

Logs are stored in ~/.knowledge-kiwi/.runs/history.jsonl
"""

import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _get_history_file() -> Path:
    """Get path to history file in user space."""
    return Path.home() / ".knowledge-kiwi" / ".runs" / "history.jsonl"


def _ensure_dir(history_file: Path):
    """Ensure runs directory exists."""
    history_file.parent.mkdir(parents=True, exist_ok=True)


def log_tool_execution(
    tool_name: str,
    status: str,
    duration_sec: float,
    inputs: Dict,
    project: Optional[str] = None,
    outputs: Optional[Dict] = None,
    error: Optional[str] = None,
    metadata: Optional[Dict] = None
) -> Dict:
    """
    Log a tool execution to ~/.knowledge-kiwi/.runs/history.jsonl.
    
    Args:
        tool_name: Name of the tool (search, get, manage, link, help)
        status: "success", "error", "validation_failed"
        duration_sec: How long the execution took
        inputs: Input parameters (will be summarized)
        project: Project path this was run in
        outputs: Output data (will be summarized)
        error: Error message if failed
        metadata: Additional metadata (zettel_id, source, action, etc.)
        
    Returns:
        The logged execution entry
    """
    history_file = _get_history_file()
    _ensure_dir(history_file)
    
    def summarize(data, max_items=5, max_value_length=100):
        if not data:
            return None
        if isinstance(data, dict):
            summarized = {}
            for i, (k, v) in enumerate(data.items()):
                if i >= max_items:
                    break
                if isinstance(v, str) and len(v) > max_value_length:
                    summarized[k] = v[:max_value_length] + "..."
                elif isinstance(v, (dict, list)):
                    summarized[k] = f"<{type(v).__name__}>"
                else:
                    summarized[k] = v
            return summarized
        if isinstance(data, str) and len(data) > max_value_length:
            return data[:max_value_length] + "..."
        return data
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "tool": tool_name,
        "status": status,
        "duration_sec": round(duration_sec, 2),
        "project": project,
        "inputs": summarize(inputs),
        "outputs": summarize(outputs),
        "error": error,
        "metadata": metadata
    }
    
    entry = {k: v for k, v in entry.items() if v is not None}
    
    with open(history_file, 'a') as f:
        f.write(json.dumps(entry) + '\n')
    
    logger.info(f"Logged execution: {tool_name} -> {status} ({duration_sec:.1f}s)")
    return entry


def get_execution_history(
    days: int = 30, 
    tool_name: Optional[str] = None,
    project: Optional[str] = None
) -> List[Dict]:
    """
    Load execution history from the last N days.
    
    Args:
        days: Number of days of history to load
        tool_name: Optional filter by tool name
        project: Optional filter by project
        
    Returns:
        List of execution entries, most recent first
    """
    history_file = _get_history_file()
    if not history_file.exists():
        return []
    
    cutoff = datetime.now() - timedelta(days=days)
    executions = []
    
    with open(history_file, 'r') as f:
        for line in f:
            if line.strip():
                execution = json.loads(line)
                exec_time = datetime.fromisoformat(execution['timestamp'])
                
                if exec_time > cutoff:
                    if tool_name and execution.get('tool') != tool_name:
                        continue
                    if project and execution.get('project') != project:
                        continue
                    executions.append(execution)
    
    return sorted(executions, key=lambda x: x['timestamp'], reverse=True)


def _make_stats_entry() -> Dict[str, Any]:
    """Create a fresh stats entry for defaultdict."""
    return {
        'success': 0, 
        'error': 0, 
        'total_duration': 0.0,
        'errors': []
    }


def tool_stats(
    days: int = 30,
    project: Optional[str] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Calculate success rate and performance stats per tool.
    
    Args:
        days: Number of days to analyze
        project: Optional filter by project
        
    Returns:
        Dictionary of tool stats
    """
    executions = get_execution_history(days=days, project=project)
    stats: Dict[str, Dict[str, Any]] = defaultdict(_make_stats_entry)
    
    for execution in executions:
        tool = execution.get('tool', 'unknown')
        stats[tool]['total_duration'] += execution.get('duration_sec', 0)
        
        if execution.get('status') == 'success':
            stats[tool]['success'] += 1
        else:
            stats[tool]['error'] += 1
            if execution.get('error'):
                stats[tool]['errors'].append(execution.get('error'))
    
    result = {}
    for tool, s in stats.items():
        total = s['success'] + s['error']
        result[tool] = {
            'total_executions': total,
            'success_rate': s['success'] / total if total > 0 else 0,
            'error_rate': s['error'] / total if total > 0 else 0,
            'avg_duration_sec': s['total_duration'] / total if total > 0 else 0,
            'common_errors': list(set(s['errors']))[:3]
        }
    
    return result


def recent_failures(
    count: int = 10,
    project: Optional[str] = None
) -> List[Dict]:
    """
    Get recent failures for debugging.
    
    Args:
        count: Number of recent failures to return
        project: Optional filter by project
        
    Returns:
        List of failed executions with details
    """
    executions = get_execution_history(days=7, project=project)
    failures = [e for e in executions if e.get('status') == 'error']
    return failures[:count]


