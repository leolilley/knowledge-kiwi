"""
Tests for link tool (relationships and collections).
"""

import pytest
import json
from unittest.mock import patch, Mock

from knowledge_kiwi.tools.link import LinkTool


class TestLinkTool:
    """Tests for LinkTool."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_link_entries_success(self, mock_supabase):
        """Test successfully linking two entries."""
        tool = LinkTool()
        
        # Setup mock entries
        mock_supabase.configure_table_data('knowledge_entries', [
            {"zettel_id": "042-from"},
            {"zettel_id": "043-to"}
        ])
        
        with patch.object(tool.registry, 'client', mock_supabase):
            result = await tool.execute({
                "action": "link",
                "from_zettel_id": "042-from",
                "to_zettel_id": "043-to",
                "relationship_type": "references"
            })
            
            result_data = json.loads(result)
            assert result_data["status"] == "success"
            assert result_data["action"] == "link"
            assert "relationship" in result_data

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_link_entries_missing_ids(self):
        """Test link with missing zettel IDs."""
        tool = LinkTool()
        
        result = await tool.execute({
            "action": "link",
            "from_zettel_id": "042-from"
            # Missing to_zettel_id
        })
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "required" in result_data["error"].lower()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_collection_success(self, mock_supabase):
        """Test successfully creating a collection."""
        tool = LinkTool()
        
        with patch.object(tool.registry, 'client', mock_supabase):
            result = await tool.execute({
                "action": "create_collection",
                "name": "Test Collection",
                "description": "A test collection",
                "zettel_ids": ["042-entry1", "043-entry2"],
                "collection_type": "topic"
            })
            
            result_data = json.loads(result)
            assert result_data["status"] == "success"
            assert result_data["action"] == "create_collection"
            assert "collection_id" in result_data

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_collection_missing_name(self):
        """Test create collection with missing name."""
        tool = LinkTool()
        
        result = await tool.execute({
            "action": "create_collection",
            "zettel_ids": ["042-entry1"]
        })
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "name" in result_data["error"].lower()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_relationships_success(self, mock_supabase):
        """Test successfully getting relationships for an entry."""
        tool = LinkTool()
        
        # Setup relationships
        mock_supabase.configure_table_data('knowledge_relationships', [
            {
                "from_zettel_id": "042-entry",
                "to_zettel_id": "043-related",
                "relationship_type": "references"
            },
            {
                "from_zettel_id": "044-backlink",
                "to_zettel_id": "042-entry",
                "relationship_type": "extends"
            }
        ])
        
        with patch.object(tool.registry, 'client', mock_supabase):
            result = await tool.execute({
                "action": "get_relationships",
                "zettel_id": "042-entry"
            })
            
            result_data = json.loads(result)
            assert "relationships" in result_data
            assert "outgoing" in result_data["relationships"]
            assert "incoming" in result_data["relationships"]

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_relationships_missing_id(self):
        """Test get relationships with missing zettel_id."""
        tool = LinkTool()
        
        result = await tool.execute({
            "action": "get_relationships"
        })
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "zettel_id" in result_data["error"].lower()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_invalid_action(self):
        """Test with invalid action."""
        tool = LinkTool()
        
        result = await tool.execute({
            "action": "invalid"
        })
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "unknown action" in result_data["error"].lower()

