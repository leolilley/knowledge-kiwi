"""
Tests for KnowledgeRegistry API client.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from knowledge_kiwi.api.knowledge_registry import KnowledgeRegistry


class TestKnowledgeRegistry:
    """Tests for KnowledgeRegistry."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_entries_success(self, mock_supabase):
        """Test successful search in registry."""
        registry = KnowledgeRegistry()
        registry.client = mock_supabase
        
        # Setup RPC search
        mock_supabase.setup_rpc_search("test", [
            {
                "zettel_id": "042-entry",
                "title": "Test Entry",
                "entry_type": "pattern",
                "tags": ["test"],
                "relevance_score": 0.9,
                "snippet": "Test snippet"
            }
        ])
        
        results = await registry.search_entries("test", limit=10)
        
        assert len(results) > 0
        assert results[0]["zettel_id"] == "042-entry"
        assert results[0]["source_location"] == "registry"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_entries_no_client(self):
        """Test search when client is not initialized."""
        registry = KnowledgeRegistry()
        registry.client = None
        
        results = await registry.search_entries("test")
        
        assert results == []

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_entry_success(self, mock_supabase):
        """Test successfully getting an entry."""
        registry = KnowledgeRegistry()
        registry.client = mock_supabase
        
        # Setup entry
        mock_supabase.configure_table_data('knowledge_entries', {
            "zettel_id": "042-entry",
            "title": "Test Entry",
            "content": "Content",
            "entry_type": "pattern",
            "tags": ["test"],
            "version": "1.0.0"
        })
        
        result = await registry.get_entry("042-entry")
        
        assert result is not None
        assert result["zettel_id"] == "042-entry"
        assert result["title"] == "Test Entry"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_entry_not_found(self, mock_supabase):
        """Test getting non-existent entry."""
        registry = KnowledgeRegistry()
        registry.client = mock_supabase
        
        # Setup empty table
        mock_supabase.configure_table_data('knowledge_entries', None)
        
        result = await registry.get_entry("999-nonexistent")
        
        assert result is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_publish_entry_new(self, mock_supabase):
        """Test publishing a new entry."""
        registry = KnowledgeRegistry()
        registry.client = mock_supabase
        
        # Setup empty table
        mock_supabase.configure_table_data('knowledge_entries', None)
        
        result = await registry.publish_entry(
            zettel_id="042-new",
            title="New Entry",
            content="Content",
            entry_type="pattern",
            tags=["test"]
        )
        
        assert "status" in result
        assert result["status"] == "success"
        assert result["zettel_id"] == "042-new"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_publish_entry_update(self, mock_supabase):
        """Test updating existing entry."""
        registry = KnowledgeRegistry()
        registry.client = mock_supabase
        
        # Setup existing entry
        mock_supabase.configure_table_data('knowledge_entries', {
            "zettel_id": "042-existing",
            "title": "Old Title",
            "content": "Old Content",
            "entry_type": "pattern",
            "version": "1.0.0"
        })
        
        result = await registry.publish_entry(
            zettel_id="042-existing",
            title="New Title",
            content="New Content",
            entry_type="pattern"
        )
        
        assert result["status"] == "success"
        assert "version" in result

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_relationships_success(self, mock_supabase):
        """Test getting relationships."""
        registry = KnowledgeRegistry()
        registry.client = mock_supabase
        
        # Setup relationships
        mock_supabase.configure_table_data('knowledge_relationships', [
            {
                "from_zettel_id": "042-entry",
                "to_zettel_id": "043-related",
                "relationship_type": "references"
            }
        ])
        
        result = await registry.get_relationships("042-entry")
        
        assert "outgoing" in result
        assert "incoming" in result
        assert len(result["outgoing"]) > 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_relationship_success(self, mock_supabase):
        """Test creating a relationship."""
        registry = KnowledgeRegistry()
        registry.client = mock_supabase
        
        result = await registry.create_relationship(
            from_zettel_id="042-from",
            to_zettel_id="043-to",
            relationship_type="references"
        )
        
        assert result["status"] == "success"
        assert "relationship" in result

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_collection_success(self, mock_supabase):
        """Test creating a collection."""
        registry = KnowledgeRegistry()
        registry.client = mock_supabase
        
        result = await registry.create_collection(
            name="Test Collection",
            description="Description",
            zettel_ids=["042-entry1", "043-entry2"],
            collection_type="topic"
        )
        
        assert result["status"] == "success"
        assert "collection_id" in result

