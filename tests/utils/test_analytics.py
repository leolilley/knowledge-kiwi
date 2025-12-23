"""
Tests for analytics and logging utilities.
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch

from knowledge_kiwi.utils.analytics import (
    log_tool_execution,
    get_execution_history,
    tool_stats,
    recent_failures,
    _get_history_file,
    _ensure_dir
)


class TestLogToolExecution:
    """Tests for log_tool_execution function."""
    
    def test_log_tool_execution_creates_file(self, temp_user_dir):
        """Test that log_tool_execution creates the history file."""
        with patch('knowledge_kiwi.utils.analytics._get_history_file') as mock_get_file:
            history_file = temp_user_dir / ".runs" / "history.jsonl"
            mock_get_file.return_value = history_file
            
            log_tool_execution(
                tool_name="search",
                status="success",
                duration_sec=0.5,
                inputs={"query": "test", "source": "local"}
            )
            
            assert history_file.exists()
            assert history_file.parent.exists()
    
    def test_log_tool_execution_writes_entry(self, temp_user_dir):
        """Test that log_tool_execution writes a valid entry."""
        with patch('knowledge_kiwi.utils.analytics._get_history_file') as mock_get_file:
            history_file = temp_user_dir / ".runs" / "history.jsonl"
            mock_get_file.return_value = history_file
            
            log_tool_execution(
                tool_name="search",
                status="success",
                duration_sec=0.5,
                inputs={"query": "test", "source": "local"},
                project="/test/project",
                outputs={"result_count": 10},
                metadata={"zettel_id": "042-test"}
            )
            
            # Read and verify entry
            with open(history_file, 'r') as f:
                line = f.readline().strip()
                entry = json.loads(line)
            
            assert entry["tool"] == "search"
            assert entry["status"] == "success"
            assert entry["duration_sec"] == 0.5
            assert entry["project"] == "/test/project"
            assert entry["inputs"]["query"] == "test"
            assert entry["outputs"]["result_count"] == 10
            assert entry["metadata"]["zettel_id"] == "042-test"
            assert "timestamp" in entry
    
    def test_log_tool_execution_with_error(self, temp_user_dir):
        """Test logging an execution with an error."""
        with patch('knowledge_kiwi.utils.analytics._get_history_file') as mock_get_file:
            history_file = temp_user_dir / ".runs" / "history.jsonl"
            mock_get_file.return_value = history_file
            
            log_tool_execution(
                tool_name="manage",
                status="error",
                duration_sec=0.1,
                inputs={"action": "create"},
                error="Validation failed"
            )
            
            with open(history_file, 'r') as f:
                entry = json.loads(f.readline().strip())
            
            assert entry["status"] == "error"
            assert entry["error"] == "Validation failed"
    
    def test_log_tool_execution_summarizes_large_inputs(self, temp_user_dir):
        """Test that large inputs are summarized."""
        with patch('knowledge_kiwi.utils.analytics._get_history_file') as mock_get_file:
            history_file = temp_user_dir / ".runs" / "history.jsonl"
            mock_get_file.return_value = history_file
            
            # Create large input
            large_content = "x" * 200  # Exceeds max_value_length (100)
            log_tool_execution(
                tool_name="manage",
                status="success",
                duration_sec=0.5,
                inputs={"content": large_content, "query": "test"}
            )
            
            with open(history_file, 'r') as f:
                entry = json.loads(f.readline().strip())
            
            # Content should be truncated
            assert len(entry["inputs"]["content"]) < len(large_content)
            assert entry["inputs"]["content"].endswith("...")
    
    def test_log_tool_execution_removes_none_values(self, temp_user_dir):
        """Test that None values are removed from entries."""
        with patch('knowledge_kiwi.utils.analytics._get_history_file') as mock_get_file:
            history_file = temp_user_dir / ".runs" / "history.jsonl"
            mock_get_file.return_value = history_file
            
            log_tool_execution(
                tool_name="search",
                status="success",
                duration_sec=0.5,
                inputs={"query": "test"},
                project=None,
                outputs=None,
                error=None,
                metadata=None
            )
            
            with open(history_file, 'r') as f:
                entry = json.loads(f.readline().strip())
            
            # None values should not be in the entry
            assert "project" not in entry or entry["project"] is not None
            assert "outputs" not in entry or entry["outputs"] is not None
            assert "error" not in entry or entry["error"] is not None
            assert "metadata" not in entry or entry["metadata"] is not None


class TestGetExecutionHistory:
    """Tests for get_execution_history function."""
    
    def test_get_execution_history_empty_file(self, temp_user_dir):
        """Test getting history from non-existent file."""
        with patch('knowledge_kiwi.utils.analytics._get_history_file') as mock_get_file:
            history_file = temp_user_dir / ".runs" / "history.jsonl"
            mock_get_file.return_value = history_file
            
            history = get_execution_history(days=30)
            
            assert history == []
    
    def test_get_execution_history_returns_recent_entries(self, temp_user_dir):
        """Test that get_execution_history returns recent entries."""
        with patch('knowledge_kiwi.utils.analytics._get_history_file') as mock_get_file:
            history_file = temp_user_dir / ".runs" / "history.jsonl"
            mock_get_file.return_value = history_file
            history_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write some entries
            now = datetime.now()
            entries = [
                {"timestamp": (now - timedelta(days=1)).isoformat(), "tool": "search", "status": "success"},
                {"timestamp": (now - timedelta(days=2)).isoformat(), "tool": "get", "status": "success"},
                {"timestamp": (now - timedelta(days=35)).isoformat(), "tool": "manage", "status": "success"},  # Too old
            ]
            
            with open(history_file, 'w') as f:
                for entry in entries:
                    f.write(json.dumps(entry) + '\n')
            
            history = get_execution_history(days=30)
            
            # Should only return entries from last 30 days
            assert len(history) == 2
            assert all(h["tool"] in ["search", "get"] for h in history)
    
    def test_get_execution_history_filters_by_tool(self, temp_user_dir):
        """Test filtering history by tool name."""
        with patch('knowledge_kiwi.utils.analytics._get_history_file') as mock_get_file:
            history_file = temp_user_dir / ".runs" / "history.jsonl"
            mock_get_file.return_value = history_file
            history_file.parent.mkdir(parents=True, exist_ok=True)
            
            now = datetime.now()
            entries = [
                {"timestamp": now.isoformat(), "tool": "search", "status": "success"},
                {"timestamp": now.isoformat(), "tool": "get", "status": "success"},
                {"timestamp": now.isoformat(), "tool": "search", "status": "error"},
            ]
            
            with open(history_file, 'w') as f:
                for entry in entries:
                    f.write(json.dumps(entry) + '\n')
            
            history = get_execution_history(days=30, tool_name="search")
            
            assert len(history) == 2
            assert all(h["tool"] == "search" for h in history)
    
    def test_get_execution_history_filters_by_project(self, temp_user_dir):
        """Test filtering history by project."""
        with patch('knowledge_kiwi.utils.analytics._get_history_file') as mock_get_file:
            history_file = temp_user_dir / ".runs" / "history.jsonl"
            mock_get_file.return_value = history_file
            history_file.parent.mkdir(parents=True, exist_ok=True)
            
            now = datetime.now()
            entries = [
                {"timestamp": now.isoformat(), "tool": "search", "project": "/project/a"},
                {"timestamp": now.isoformat(), "tool": "get", "project": "/project/b"},
                {"timestamp": now.isoformat(), "tool": "manage", "project": "/project/a"},
            ]
            
            with open(history_file, 'w') as f:
                for entry in entries:
                    f.write(json.dumps(entry) + '\n')
            
            history = get_execution_history(days=30, project="/project/a")
            
            assert len(history) == 2
            assert all(h["project"] == "/project/a" for h in history)
    
    def test_get_execution_history_sorted_recent_first(self, temp_user_dir):
        """Test that history is sorted with most recent first."""
        with patch('knowledge_kiwi.utils.analytics._get_history_file') as mock_get_file:
            history_file = temp_user_dir / ".runs" / "history.jsonl"
            mock_get_file.return_value = history_file
            history_file.parent.mkdir(parents=True, exist_ok=True)
            
            now = datetime.now()
            entries = [
                {"timestamp": (now - timedelta(hours=3)).isoformat(), "tool": "search"},
                {"timestamp": (now - timedelta(hours=1)).isoformat(), "tool": "get"},
                {"timestamp": (now - timedelta(hours=2)).isoformat(), "tool": "manage"},
            ]
            
            with open(history_file, 'w') as f:
                for entry in entries:
                    f.write(json.dumps(entry) + '\n')
            
            history = get_execution_history(days=30)
            
            # Should be sorted by timestamp descending
            timestamps = [datetime.fromisoformat(h["timestamp"]) for h in history]
            assert timestamps == sorted(timestamps, reverse=True)


class TestToolStats:
    """Tests for tool_stats function."""
    
    def test_tool_stats_calculates_success_rate(self, temp_user_dir):
        """Test that tool_stats calculates success rates correctly."""
        with patch('knowledge_kiwi.utils.analytics._get_history_file') as mock_get_file:
            history_file = temp_user_dir / ".runs" / "history.jsonl"
            mock_get_file.return_value = history_file
            history_file.parent.mkdir(parents=True, exist_ok=True)
            
            now = datetime.now()
            entries = [
                {"timestamp": now.isoformat(), "tool": "search", "status": "success", "duration_sec": 0.1},
                {"timestamp": now.isoformat(), "tool": "search", "status": "success", "duration_sec": 0.2},
                {"timestamp": now.isoformat(), "tool": "search", "status": "error", "duration_sec": 0.05},
                {"timestamp": now.isoformat(), "tool": "get", "status": "success", "duration_sec": 0.3},
            ]
            
            with open(history_file, 'w') as f:
                for entry in entries:
                    f.write(json.dumps(entry) + '\n')
            
            stats = tool_stats(days=30)
            
            assert "search" in stats
            assert "get" in stats
            
            search_stats = stats["search"]
            assert search_stats["total_executions"] == 3
            assert search_stats["success_rate"] == pytest.approx(2/3, 0.01)
            assert search_stats["error_rate"] == pytest.approx(1/3, 0.01)
            assert search_stats["avg_duration_sec"] == pytest.approx(0.116, 0.01)
            
            get_stats = stats["get"]
            assert get_stats["total_executions"] == 1
            assert get_stats["success_rate"] == 1.0
    
    def test_tool_stats_collects_common_errors(self, temp_user_dir):
        """Test that tool_stats collects common errors."""
        with patch('knowledge_kiwi.utils.analytics._get_history_file') as mock_get_file:
            history_file = temp_user_dir / ".runs" / "history.jsonl"
            mock_get_file.return_value = history_file
            history_file.parent.mkdir(parents=True, exist_ok=True)
            
            now = datetime.now()
            entries = [
                {"timestamp": now.isoformat(), "tool": "manage", "status": "error", "error": "Validation failed"},
                {"timestamp": now.isoformat(), "tool": "manage", "status": "error", "error": "Validation failed"},
                {"timestamp": now.isoformat(), "tool": "manage", "status": "error", "error": "Network error"},
            ]
            
            with open(history_file, 'w') as f:
                for entry in entries:
                    f.write(json.dumps(entry) + '\n')
            
            stats = tool_stats(days=30)
            
            assert "manage" in stats
            manage_stats = stats["manage"]
            assert "Validation failed" in manage_stats["common_errors"]
            assert "Network error" in manage_stats["common_errors"]
    
    def test_tool_stats_empty_history(self, temp_user_dir):
        """Test tool_stats with no history."""
        with patch('knowledge_kiwi.utils.analytics._get_history_file') as mock_get_file:
            history_file = temp_user_dir / ".runs" / "history.jsonl"
            mock_get_file.return_value = history_file
            
            stats = tool_stats(days=30)
            
            assert stats == {}


class TestRecentFailures:
    """Tests for recent_failures function."""
    
    def test_recent_failures_returns_only_errors(self, temp_user_dir):
        """Test that recent_failures only returns failed executions."""
        with patch('knowledge_kiwi.utils.analytics._get_history_file') as mock_get_file:
            history_file = temp_user_dir / ".runs" / "history.jsonl"
            mock_get_file.return_value = history_file
            history_file.parent.mkdir(parents=True, exist_ok=True)
            
            now = datetime.now()
            entries = [
                {"timestamp": now.isoformat(), "tool": "search", "status": "success"},
                {"timestamp": now.isoformat(), "tool": "get", "status": "error", "error": "Failed"},
                {"timestamp": now.isoformat(), "tool": "manage", "status": "error", "error": "Validation failed"},
            ]
            
            with open(history_file, 'w') as f:
                for entry in entries:
                    f.write(json.dumps(entry) + '\n')
            
            failures = recent_failures(count=10)
            
            assert len(failures) == 2
            assert all(f["status"] == "error" for f in failures)
    
    def test_recent_failures_respects_count_limit(self, temp_user_dir):
        """Test that recent_failures respects the count limit."""
        with patch('knowledge_kiwi.utils.analytics._get_history_file') as mock_get_file:
            history_file = temp_user_dir / ".runs" / "history.jsonl"
            mock_get_file.return_value = history_file
            history_file.parent.mkdir(parents=True, exist_ok=True)
            
            now = datetime.now()
            entries = [
                {"timestamp": now.isoformat(), "tool": "search", "status": "error", "error": "Error 1"},
                {"timestamp": now.isoformat(), "tool": "get", "status": "error", "error": "Error 2"},
                {"timestamp": now.isoformat(), "tool": "manage", "status": "error", "error": "Error 3"},
            ]
            
            with open(history_file, 'w') as f:
                for entry in entries:
                    f.write(json.dumps(entry) + '\n')
            
            failures = recent_failures(count=2)
            
            assert len(failures) == 2
    
    def test_recent_failures_filters_by_project(self, temp_user_dir):
        """Test that recent_failures can filter by project."""
        with patch('knowledge_kiwi.utils.analytics._get_history_file') as mock_get_file:
            history_file = temp_user_dir / ".runs" / "history.jsonl"
            mock_get_file.return_value = history_file
            history_file.parent.mkdir(parents=True, exist_ok=True)
            
            now = datetime.now()
            entries = [
                {"timestamp": now.isoformat(), "tool": "search", "status": "error", "project": "/project/a"},
                {"timestamp": now.isoformat(), "tool": "get", "status": "error", "project": "/project/b"},
            ]
            
            with open(history_file, 'w') as f:
                for entry in entries:
                    f.write(json.dumps(entry) + '\n')
            
            failures = recent_failures(count=10, project="/project/a")
            
            assert len(failures) == 1
            assert failures[0]["project"] == "/project/a"
    
    def test_recent_failures_empty_history(self, temp_user_dir):
        """Test recent_failures with no history."""
        with patch('knowledge_kiwi.utils.analytics._get_history_file') as mock_get_file:
            history_file = temp_user_dir / ".runs" / "history.jsonl"
            mock_get_file.return_value = history_file
            
            failures = recent_failures(count=10)
            
            assert failures == []


class TestHelperFunctions:
    """Tests for helper functions."""
    
    def test_get_history_file_returns_correct_path(self):
        """Test that _get_history_file returns the correct path."""
        history_file = _get_history_file()
        
        assert history_file.name == "history.jsonl"
        assert ".runs" in str(history_file)
        assert ".knowledge-kiwi" in str(history_file)
    
    def test_ensure_dir_creates_directory(self, temp_user_dir):
        """Test that _ensure_dir creates the directory if it doesn't exist."""
        test_file = temp_user_dir / "subdir" / "file.txt"
        
        assert not test_file.parent.exists()
        
        _ensure_dir(test_file)
        
        assert test_file.parent.exists()

