"""
Integration tests for server logging functionality.
"""

import pytest
import json
from unittest.mock import patch

from knowledge_kiwi.utils.analytics import log_tool_execution


class TestServerLogging:
    """Tests for server-level tool execution logging."""
    
    def test_server_logs_tool_execution(self, temp_user_dir):
        """Test that the server logs tool executions automatically."""
        with patch('knowledge_kiwi.utils.analytics._get_history_file') as mock_get_file:
            history_file = temp_user_dir / ".runs" / "history.jsonl"
            mock_get_file.return_value = history_file
            
            log_tool_execution(
                tool_name="search",
                status="success",
                duration_sec=0.1,
                inputs={"query": "test", "source": "local"}
            )
            
            assert history_file.exists()
            
            with open(history_file, 'r') as f:
                lines = f.readlines()
                assert len(lines) >= 1
                entry = json.loads(lines[-1].strip())
            
            assert entry["tool"] == "search"
            assert entry["status"] == "success"
            assert entry["inputs"]["query"] == "test"
            assert "duration_sec" in entry
            assert "timestamp" in entry
    
    def test_server_logs_tool_errors(self, temp_user_dir):
        """Test that the server logs tool execution errors."""
        with patch('knowledge_kiwi.utils.analytics._get_history_file') as mock_get_file:
            history_file = temp_user_dir / ".runs" / "history.jsonl"
            mock_get_file.return_value = history_file
            
            log_tool_execution(
                tool_name="search",
                status="error",
                duration_sec=0.1,
                inputs={"query": "test", "source": "local"},
                error="Test error"
            )
            
            assert history_file.exists()
            
            with open(history_file, 'r') as f:
                lines = f.readlines()
                assert len(lines) >= 1
                entry = json.loads(lines[-1].strip())
            
            assert entry["tool"] == "search"
            assert entry["status"] == "error"
            assert "error" in entry
            assert "Test error" in entry["error"]
    
    def test_server_logs_metadata(self, temp_user_dir):
        """Test that the server extracts and logs metadata from results."""
        with patch('knowledge_kiwi.utils.analytics._get_history_file') as mock_get_file:
            history_file = temp_user_dir / ".runs" / "history.jsonl"
            mock_get_file.return_value = history_file
            
            log_tool_execution(
                tool_name="manage",
                status="success",
                duration_sec=0.1,
                inputs={
                    "action": "create",
                    "zettel_id": "042-test",
                    "entry_type": "pattern"
                },
                outputs={
                    "status": "success",
                    "action": "create",
                    "zettel_id": "042-test",
                    "category": "patterns"
                },
                metadata={
                    "zettel_id": "042-test",
                    "action": "create",
                    "category": "patterns"
                }
            )
            
            with open(history_file, 'r') as f:
                entry = json.loads(f.readlines()[-1].strip())
            
            assert "metadata" in entry
            assert entry["metadata"]["zettel_id"] == "042-test"
            assert entry["metadata"]["action"] == "create"
            assert entry["metadata"]["category"] == "patterns"
    
    def test_server_logs_project_path(self, temp_user_dir, temp_project_dir):
        """Test that the server logs the project path."""
        with patch('knowledge_kiwi.utils.analytics._get_history_file') as mock_get_file:
            history_file = temp_user_dir / ".runs" / "history.jsonl"
            mock_get_file.return_value = history_file
            
            log_tool_execution(
                tool_name="search",
                status="success",
                duration_sec=0.1,
                inputs={"query": "test", "source": "local"},
                project=str(temp_project_dir)
            )
            
            with open(history_file, 'r') as f:
                entry = json.loads(f.readlines()[-1].strip())
            
            assert "project" in entry
            assert str(temp_project_dir) in entry["project"]

