"""
Tests for help tool.
"""

import pytest
import json

from knowledge_kiwi.tools.help import HelpTool


class TestHelpTool:
    """Tests for HelpTool."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_help_create(self):
        """Test help for creating entries."""
        tool = HelpTool()
        
        result = await tool.execute({
            "query": "how to create a knowledge entry"
        })
        
        result_data = json.loads(result)
        assert "topic" in result_data
        assert "workflow" in result_data
        assert "examples" in result_data
        assert "Creating" in result_data["topic"] or "create" in result_data["topic"].lower()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_help_search(self):
        """Test help for searching."""
        tool = HelpTool()
        
        result = await tool.execute({
            "query": "how to search"
        })
        
        result_data = json.loads(result)
        assert "topic" in result_data
        assert "Searching" in result_data["topic"] or "search" in result_data["topic"].lower()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_help_link(self):
        """Test help for linking."""
        tool = HelpTool()
        
        result = await tool.execute({
            "query": "how to link entries"
        })
        
        result_data = json.loads(result)
        assert "topic" in result_data
        assert "Linking" in result_data["topic"] or "link" in result_data["topic"].lower()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_help_publish(self):
        """Test help for publishing."""
        tool = HelpTool()
        
        result = await tool.execute({
            "query": "how to publish"
        })
        
        result_data = json.loads(result)
        assert "topic" in result_data
        assert "Publishing" in result_data["topic"] or "publish" in result_data["topic"].lower()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_help_general(self):
        """Test general help."""
        tool = HelpTool()
        
        result = await tool.execute({
            "query": "what is knowledge kiwi"
        })
        
        result_data = json.loads(result)
        assert "topic" in result_data
        assert "tools" in result_data or "overview" in result_data.get("topic", "").lower()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_help_source_selection(self):
        """Test help for source selection."""
        tool = HelpTool()
        
        result = await tool.execute({
            "query": "what is source selection"
        })
        
        result_data = json.loads(result)
        assert "topic" in result_data
        assert "source" in result_data["topic"].lower() or "source_options" in result_data

