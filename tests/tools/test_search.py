"""
Tests for search tool.
"""

import pytest
import json
from unittest.mock import patch, Mock
from pathlib import Path

from knowledge_kiwi.tools.search import SearchTool


class TestSearchTool:
    """Tests for SearchTool."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_local_success(self, temp_project_dir, sample_knowledge_file):
        """Test successful local search."""
        tool = SearchTool()
        
        # Patch resolver to use temp directory
        with patch.object(tool.resolver, 'project_knowledge_dir', temp_project_dir / ".ai" / "knowledge"), \
             patch.object(tool.resolver, 'user_knowledge_dir', Path("/tmp/empty")):
            
            result = await tool.execute({
                "query": "test",
                "source": "local",
                "limit": 10
            })
            
            result_data = json.loads(result)
            assert "results" in result_data
            assert len(result_data["results"]) > 0
            assert result_data["results"][0]["zettel_id"] == "042-test-entry"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_local_no_results(self, temp_project_dir):
        """Test local search with no results."""
        tool = SearchTool()
        
        with patch.object(tool.resolver, 'project_knowledge_dir', temp_project_dir / ".ai" / "knowledge"), \
             patch.object(tool.resolver, 'user_knowledge_dir', Path("/tmp/empty")):
            
            result = await tool.execute({
                "query": "nonexistent",
                "source": "local",
                "limit": 10
            })
            
            result_data = json.loads(result)
            assert result_data["results_count"] == 0
            assert result_data["results"] == []

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_registry_success(self, mock_supabase):
        """Test successful registry search."""
        tool = SearchTool()
        
        # Setup mock registry search
        mock_supabase.setup_rpc_search("test", [
            {
                "zettel_id": "042-registry-entry",
                "title": "Registry Entry",
                "entry_type": "pattern",
                "tags": ["test"],
                "relevance_score": 0.9,
                "snippet": "Test snippet"
            }
        ])
        
        with patch.object(tool.registry, 'client', mock_supabase):
            result = await tool.execute({
                "query": "test",
                "source": "registry",
                "limit": 10
            })
            
            result_data = json.loads(result)
            assert "results" in result_data
            assert len(result_data["results"]) > 0
            assert result_data["results"][0]["zettel_id"] == "042-registry-entry"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_both_sources(self, temp_project_dir, sample_knowledge_file, mock_supabase):
        """Test searching both local and registry sources."""
        tool = SearchTool()
        
        # Setup mock registry search
        mock_supabase.setup_rpc_search("test", [
            {
                "zettel_id": "043-registry-entry",
                "title": "Registry Entry",
                "entry_type": "pattern",
                "tags": ["test"],
                "relevance_score": 0.8,
                "snippet": "Registry snippet"
            }
        ])
        
        with patch.object(tool.resolver, 'project_knowledge_dir', temp_project_dir / ".ai" / "knowledge"), \
             patch.object(tool.resolver, 'user_knowledge_dir', Path("/tmp/empty")), \
             patch.object(tool.registry, 'client', mock_supabase):
            
            result = await tool.execute({
                "query": "test",
                "source": ["local", "registry"],
                "limit": 10
            })
            
            result_data = json.loads(result)
            assert result_data["results_count"] >= 2  # At least one from local and one from registry

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_with_filters(self, temp_project_dir, sample_knowledge_file):
        """Test search with entry_type and tags filters."""
        tool = SearchTool()
        
        with patch.object(tool.resolver, 'project_knowledge_dir', temp_project_dir / ".ai" / "knowledge"), \
             patch.object(tool.resolver, 'user_knowledge_dir', Path("/tmp/empty")):
            
            result = await tool.execute({
                "query": "test",
                "source": "local",
                "entry_type": "pattern",
                "tags": ["test"],
                "limit": 10
            })
            
            result_data = json.loads(result)
            # Should find the entry since it matches filters
            assert result_data["results_count"] > 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_missing_query(self):
        """Test search with missing query parameter."""
        tool = SearchTool()
        
        result = await tool.execute({
            "source": "local"
        })
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "query" in result_data["error"].lower()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_invalid_source(self):
        """Test search with invalid source."""
        tool = SearchTool()
        
        result = await tool.execute({
            "query": "test",
            "source": "invalid"
        })
        
        # Should still work but only search valid sources
        result_data = json.loads(result)
        assert "results" in result_data

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_with_category_filter(self, temp_project_dir):
        """Test search with category filter."""
        tool = SearchTool()
        
        # Create entries in different categories
        base_dir = temp_project_dir / ".ai" / "knowledge"
        (base_dir / "patterns").mkdir(parents=True, exist_ok=True)
        (base_dir / "email-infrastructure" / "smtp").mkdir(parents=True, exist_ok=True)
        
        from knowledge_kiwi.utils.knowledge_resolver import write_knowledge_file
        
        write_knowledge_file(
            file_path=base_dir / "patterns" / "001-pattern.md",
            zettel_id="001-pattern",
            title="Pattern",
            content="Pattern content",
            entry_type="pattern"
        )
        
        write_knowledge_file(
            file_path=base_dir / "email-infrastructure" / "smtp" / "002-spf.md",
            zettel_id="002-spf",
            title="SPF",
            content="SPF content",
            entry_type="pattern"
        )
        
        with patch.object(tool.resolver, 'project_knowledge_dir', base_dir), \
             patch.object(tool.resolver, 'user_knowledge_dir', Path("/tmp/empty")):
            
            result = await tool.execute({
                "query": "content",
                "source": "local",
                "category": "email-infrastructure/smtp",
                "limit": 10
            })
            
            result_data = json.loads(result)
            assert result_data["results_count"] == 1
            assert result_data["results"][0]["zettel_id"] == "002-spf"
            assert result_data["results"][0]["category"] == "email-infrastructure/smtp"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_registry_with_category(self, mock_supabase):
        """Test registry search with category filter."""
        tool = SearchTool()
        
        # Setup mock registry search with category
        mock_supabase.setup_rpc_search("test", [
            {
                "zettel_id": "042-category-entry",
                "title": "Category Entry",
                "entry_type": "pattern",
                "category": "email-infrastructure/smtp",
                "tags": ["test"],
                "relevance_score": 0.9,
                "snippet": "Test snippet"
            }
        ])
        
        with patch.object(tool.registry, 'client', mock_supabase):
            result = await tool.execute({
                "query": "test",
                "source": "registry",
                "category": "email-infrastructure/smtp",
                "limit": 10
            })
            
            result_data = json.loads(result)
            assert "results" in result_data
            if len(result_data["results"]) > 0:
                assert result_data["results"][0]["category"] == "email-infrastructure/smtp"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_multi_term_matching(self, temp_project_dir):
        """Test multi-term search requires all terms to match."""
        tool = SearchTool()
        
        base_dir = temp_project_dir / ".ai" / "knowledge"
        base_dir.mkdir(parents=True, exist_ok=True)
        
        from knowledge_kiwi.utils.knowledge_resolver import write_knowledge_file
        
        # Create entry with both terms
        write_knowledge_file(
            file_path=base_dir / "001-jwt-auth.md",
            zettel_id="001-jwt-auth",
            title="JWT Authentication",
            content="JWT authentication patterns and best practices",
            entry_type="pattern"
        )
        
        # Create entry with only one term
        write_knowledge_file(
            file_path=base_dir / "002-jwt-token.md",
            zettel_id="002-jwt-token",
            title="JWT Token",
            content="JWT token structure and validation",
            entry_type="pattern"
        )
        
        with patch.object(tool.resolver, 'project_knowledge_dir', base_dir), \
             patch.object(tool.resolver, 'user_knowledge_dir', Path("/tmp/empty")):
            
            # Multi-term search should only match entry with both terms
            result = await tool.execute({
                "query": "JWT authentication",
                "source": "local",
                "limit": 10
            })
            
            result_data = json.loads(result)
            assert result_data["results_count"] == 1
            assert result_data["results"][0]["zettel_id"] == "001-jwt-auth"
            
            # Single term should match both
            result = await tool.execute({
                "query": "JWT",
                "source": "local",
                "limit": 10
            })
            
            result_data = json.loads(result)
            assert result_data["results_count"] == 2

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_relevance_scoring(self, temp_project_dir):
        """Test that relevance scoring ranks results correctly."""
        tool = SearchTool()
        
        base_dir = temp_project_dir / ".ai" / "knowledge"
        base_dir.mkdir(parents=True, exist_ok=True)
        
        from knowledge_kiwi.utils.knowledge_resolver import write_knowledge_file
        
        # Create entry with exact title match (should score highest)
        write_knowledge_file(
            file_path=base_dir / "001-email-deliverability.md",
            zettel_id="001-email-deliverability",
            title="Email Deliverability",
            content="Content about email deliverability",
            entry_type="concept"
        )
        
        # Create entry with terms in content only (should score lower)
        write_knowledge_file(
            file_path=base_dir / "002-other-topic.md",
            zettel_id="002-other-topic",
            title="Other Topic",
            content="This is about email deliverability best practices",
            entry_type="concept"
        )
        
        with patch.object(tool.resolver, 'project_knowledge_dir', base_dir), \
             patch.object(tool.resolver, 'user_knowledge_dir', Path("/tmp/empty")):
            
            result = await tool.execute({
                "query": "email deliverability",
                "source": "local",
                "limit": 10
            })
            
            result_data = json.loads(result)
            assert result_data["results_count"] == 2
            
            # First result should have higher relevance score
            scores = [r.get("relevance_score", 0) for r in result_data["results"]]
            assert scores[0] >= scores[1], "Results should be sorted by relevance"
            
            # Exact title match should be first
            assert result_data["results"][0]["zettel_id"] == "001-email-deliverability"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_registry_multi_term(self, mock_supabase):
        """Test registry search with multi-term matching."""
        tool = SearchTool()
        
        # Setup mock registry search with entries
        mock_supabase.setup_rpc_search("JWT authentication", [
            {
                "zettel_id": "042-jwt-auth",
                "title": "JWT Authentication",
                "entry_type": "pattern",
                "category": "auth",
                "tags": ["jwt", "auth"],
                "relevance_score": 0.9,
                "snippet": "JWT authentication patterns"
            },
            {
                "zettel_id": "043-jwt-token",
                "title": "JWT Token",
                "entry_type": "pattern",
                "category": "auth",
                "tags": ["jwt"],
                "relevance_score": 0.8,
                "snippet": "JWT token structure"
            }
        ])
        
        with patch.object(tool.registry, 'client', mock_supabase):
            result = await tool.execute({
                "query": "JWT authentication",
                "source": "registry",
                "limit": 10
            })
            
            result_data = json.loads(result)
            assert "results" in result_data
            # Should only match entry with both terms
            if len(result_data["results"]) > 0:
                assert result_data["results"][0]["zettel_id"] == "042-jwt-auth"

