"""
Tests for get tool.
"""

import pytest
import json
from unittest.mock import patch, Mock
from pathlib import Path

from knowledge_kiwi.tools.get import GetTool


class TestGetTool:
    """Tests for GetTool."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_local_entry_success(self, temp_project_dir, sample_knowledge_file):
        """Test successfully getting a local entry."""
        tool = GetTool()
        
        with patch.object(tool.resolver, 'project_knowledge_dir', temp_project_dir / ".ai" / "knowledge"), \
             patch.object(tool.resolver, 'user_knowledge_dir', Path("/tmp/empty")):
            
            result = await tool.execute({
                "zettel_id": "042-test-entry",
                "source": "local"
            })
            
            result_data = json.loads(result)
            assert result_data["zettel_id"] == "042-test-entry"
            assert result_data["title"] == "Test Knowledge Entry"
            assert result_data["source_location"] == "project"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_registry_entry_success(self, mock_supabase):
        """Test successfully getting a registry entry."""
        tool = GetTool()
        
        # Setup mock registry entry
        mock_supabase.configure_table_data('knowledge_entries', {
            "zettel_id": "042-registry-entry",
            "title": "Registry Entry",
            "content": "Registry content",
            "entry_type": "pattern",
            "tags": ["test"],
            "version": "1.0.0"
        })
        
        with patch.object(tool.registry, 'client', mock_supabase):
            result = await tool.execute({
                "zettel_id": "042-registry-entry",
                "source": "registry"
            })
            
            result_data = json.loads(result)
            assert result_data["zettel_id"] == "042-registry-entry"
            assert result_data["source_location"] == "registry"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_entry_not_found(self, temp_project_dir):
        """Test getting a non-existent entry."""
        tool = GetTool()
        
        with patch.object(tool.resolver, 'project_knowledge_dir', temp_project_dir / ".ai" / "knowledge"), \
             patch.object(tool.resolver, 'user_knowledge_dir', Path("/tmp/empty")):
            
            result = await tool.execute({
                "zettel_id": "999-nonexistent",
                "source": "local"
            })
            
            result_data = json.loads(result)
            assert "error" in result_data
            assert "not found" in result_data["error"].lower()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_with_relationships(self, mock_supabase):
        """Test getting entry with relationships."""
        tool = GetTool()
        
        # Setup mock registry entry
        mock_supabase.configure_table_data('knowledge_entries', {
            "zettel_id": "042-entry",
            "title": "Test Entry",
            "content": "Content",
            "entry_type": "pattern"
        })
        
        # Setup relationships
        mock_supabase.configure_table_data('knowledge_relationships', [
            {
                "from_zettel_id": "042-entry",
                "to_zettel_id": "043-related",
                "relationship_type": "references"
            }
        ])
        
        with patch.object(tool.registry, 'client', mock_supabase):
            result = await tool.execute({
                "zettel_id": "042-entry",
                "source": "registry",
                "include_relationships": True
            })
            
            result_data = json.loads(result)
            assert "relationships" in result_data
            assert len(result_data["relationships"]) > 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_destination_user(self, mock_supabase, temp_user_dir):
        """Test downloading entry from registry to user space using destination parameter."""
        tool = GetTool()
        
        # Setup mock registry entry
        mock_supabase.configure_table_data('knowledge_entries', {
            "zettel_id": "042-download-user",
            "title": "Download Entry",
            "content": "Content to download",
            "entry_type": "pattern",
            "category": "patterns",
            "tags": ["test"]
        })
        
        with patch.object(tool.registry, 'client', mock_supabase), \
             patch('pathlib.Path.home', return_value=temp_user_dir):
            
            result = await tool.execute({
                "zettel_id": "042-download-user",
                "source": "registry",
                "destination": "user"
            })
            
            result_data = json.loads(result)
            assert "downloaded_to" in result_data
            assert "~/.knowledge-kiwi" in result_data["downloaded_to"]
            
            # Verify file was created
            user_file = temp_user_dir / ".knowledge-kiwi" / "patterns" / "042-download-user.md"
            assert user_file.exists()
            
            # Verify file content
            from knowledge_kiwi.utils.knowledge_resolver import parse_knowledge_file
            file_data = parse_knowledge_file(user_file)
            assert file_data["zettel_id"] == "042-download-user"
            assert file_data["title"] == "Download Entry"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_destination_project(self, mock_supabase, temp_project_dir):
        """Test downloading entry from registry to project space using destination parameter."""
        tool = GetTool()
        
        # Setup mock registry entry
        mock_supabase.configure_table_data('knowledge_entries', {
            "zettel_id": "042-download-project",
            "title": "Project Entry",
            "content": "Content for project",
            "entry_type": "pattern",
            "category": "patterns",
            "tags": ["test"]
        })
        
        with patch.object(tool.registry, 'client', mock_supabase), \
             patch.object(tool.resolver, 'project_knowledge_dir', temp_project_dir / ".ai" / "knowledge"):
            
            result = await tool.execute({
                "zettel_id": "042-download-project",
                "source": "registry",
                "destination": "project"
            })
            
            result_data = json.loads(result)
            assert "downloaded_to" in result_data
            assert ".ai/knowledge" in result_data["downloaded_to"]
            
            # Verify file was created
            project_file = temp_project_dir / ".ai" / "knowledge" / "patterns" / "042-download-project.md"
            assert project_file.exists()
            
            # Verify file content
            from knowledge_kiwi.utils.knowledge_resolver import parse_knowledge_file
            file_data = parse_knowledge_file(project_file)
            assert file_data["zettel_id"] == "042-download-project"
            assert file_data["title"] == "Project Entry"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_destination_both(self, mock_supabase, temp_project_dir, temp_user_dir):
        """Test downloading entry from registry to both user and project space."""
        tool = GetTool()
        
        # Setup mock registry entry
        mock_supabase.configure_table_data('knowledge_entries', {
            "zettel_id": "042-download-both",
            "title": "Both Entry",
            "content": "Content for both",
            "entry_type": "pattern",
            "category": "patterns",
            "tags": ["test"]
        })
        
        with patch.object(tool.registry, 'client', mock_supabase), \
             patch.object(tool.resolver, 'project_knowledge_dir', temp_project_dir / ".ai" / "knowledge"), \
             patch.object(tool.resolver, 'project_root', temp_project_dir), \
             patch('pathlib.Path.home', return_value=temp_user_dir):
            
            result = await tool.execute({
                "zettel_id": "042-download-both",
                "source": "registry",
                "destination": ["user", "project"]
            })
            
            result_data = json.loads(result)
            assert "downloaded_to" in result_data
            assert isinstance(result_data["downloaded_to"], list)
            assert len(result_data["downloaded_to"]) == 2
            
            # Verify both files were created
            user_file = temp_user_dir / ".knowledge-kiwi" / "patterns" / "042-download-both.md"
            project_file = temp_project_dir / ".ai" / "knowledge" / "patterns" / "042-download-both.md"
            
            assert user_file.exists()
            assert project_file.exists()
            
            # Verify both files have same content
            from knowledge_kiwi.utils.knowledge_resolver import parse_knowledge_file
            user_data = parse_knowledge_file(user_file)
            project_data = parse_knowledge_file(project_file)
            
            assert user_data["zettel_id"] == project_data["zettel_id"]
            assert user_data["title"] == project_data["title"]

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_destination_with_category(self, mock_supabase, temp_project_dir):
        """Test downloading entry with nested category path."""
        tool = GetTool()
        
        # Setup mock registry entry with nested category
        mock_supabase.configure_table_data('knowledge_entries', {
            "zettel_id": "042-nested-category",
            "title": "Nested Entry",
            "content": "Content with nested category",
            "entry_type": "pattern",
            "category": "sources/youtube",
            "tags": ["test"]
        })
        
        with patch.object(tool.registry, 'client', mock_supabase), \
             patch.object(tool.resolver, 'project_knowledge_dir', temp_project_dir / ".ai" / "knowledge"), \
             patch.object(tool.resolver, 'project_root', temp_project_dir):
            
            result = await tool.execute({
                "zettel_id": "042-nested-category",
                "source": "registry",
                "destination": "project"
            })
            
            result_data = json.loads(result)
            assert "downloaded_to" in result_data
            assert "sources/youtube" in result_data["downloaded_to"] or "youtube" in result_data["downloaded_to"]
            
            # Verify file was created in nested directory
            project_file = temp_project_dir / ".ai" / "knowledge" / "sources" / "youtube" / "042-nested-category.md"
            assert project_file.exists()
            
            # Verify category is preserved in file
            from knowledge_kiwi.utils.knowledge_resolver import parse_knowledge_file
            file_data = parse_knowledge_file(project_file)
            assert file_data["category"] == "sources/youtube"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_destination_fallback_category(self, mock_supabase, temp_project_dir):
        """Test downloading entry without category falls back to pluralized entry_type."""
        tool = GetTool()
        
        # Setup mock registry entry without category
        mock_supabase.configure_table_data('knowledge_entries', {
            "zettel_id": "042-no-category",
            "title": "No Category Entry",
            "content": "Content without category",
            "entry_type": "pattern",
            "tags": ["test"]
        })
        
        with patch.object(tool.registry, 'client', mock_supabase), \
             patch.object(tool.resolver, 'project_knowledge_dir', temp_project_dir / ".ai" / "knowledge"), \
             patch.object(tool.resolver, 'project_root', temp_project_dir):
            
            result = await tool.execute({
                "zettel_id": "042-no-category",
                "source": "registry",
                "destination": "project"
            })
            
            result_data = json.loads(result)
            assert "downloaded_to" in result_data
            
            # Verify file was created in pluralized entry_type directory
            project_file = temp_project_dir / ".ai" / "knowledge" / "patterns" / "042-no-category.md"
            assert project_file.exists()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_destination_invalid_value(self, mock_supabase):
        """Test that invalid destination values are ignored."""
        tool = GetTool()
        
        # Setup mock registry entry
        mock_supabase.configure_table_data('knowledge_entries', {
            "zettel_id": "042-invalid-dest",
            "title": "Invalid Dest Entry",
            "content": "Content",
            "entry_type": "pattern",
            "tags": ["test"]
        })
        
        with patch.object(tool.registry, 'client', mock_supabase):
            result = await tool.execute({
                "zettel_id": "042-invalid-dest",
                "source": "registry",
                "destination": "invalid"
            })
            
            result_data = json.loads(result)
            # Should still return entry data, but no download
            assert result_data["zettel_id"] == "042-invalid-dest"
            assert "downloaded_to" not in result_data

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_destination_not_registry(self, temp_project_dir, sample_knowledge_file):
        """Test that destination parameter is ignored when getting from local source."""
        tool = GetTool()
        
        with patch.object(tool.resolver, 'project_knowledge_dir', temp_project_dir / ".ai" / "knowledge"), \
             patch.object(tool.resolver, 'user_knowledge_dir', Path("/tmp/empty")):
            
            result = await tool.execute({
                "zettel_id": "042-test-entry",
                "source": "local",
                "destination": "project"  # Should be ignored
            })
            
            result_data = json.loads(result)
            assert result_data["zettel_id"] == "042-test-entry"
            assert result_data["source_location"] == "project"
            assert "downloaded_to" not in result_data

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_missing_zettel_id(self):
        """Test get with missing zettel_id."""
        tool = GetTool()
        
        result = await tool.execute({
            "source": "local"
        })
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "zettel_id" in result_data["error"].lower()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_entry_with_category(self, temp_project_dir):
        """Test getting entry with category from nested location."""
        tool = GetTool()
        
        # Create entry in nested category
        nested_dir = temp_project_dir / ".ai" / "knowledge" / "email-infrastructure" / "smtp"
        nested_dir.mkdir(parents=True, exist_ok=True)
        
        from knowledge_kiwi.utils.knowledge_resolver import write_knowledge_file
        write_knowledge_file(
            file_path=nested_dir / "048-nested.md",
            zettel_id="048-nested",
            title="Nested Entry",
            content="# Nested\n\nContent",
            entry_type="pattern",
            category="email-infrastructure/smtp"
        )
        
        with patch.object(tool.resolver, 'project_knowledge_dir', temp_project_dir / ".ai" / "knowledge"), \
             patch.object(tool.resolver, 'user_knowledge_dir', Path("/tmp/empty")):
            
            result = await tool.execute({
                "zettel_id": "048-nested",
                "source": "local"
            })
            
            result_data = json.loads(result)
            assert result_data["zettel_id"] == "048-nested"
            assert result_data.get("category") == "email-infrastructure/smtp"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_registry_entry_with_category(self, mock_supabase):
        """Test getting entry from registry with category."""
        tool = GetTool()
        
        # Setup mock registry
        mock_entry = {
            "zettel_id": "049-registry-category",
            "title": "Registry Category Entry",
            "content": "# Test\n\nContent",
            "entry_type": "pattern",
            "category": "email-infrastructure/smtp",
            "tags": ["test"],
            "version": "1.0.0"
        }
        
        mock_supabase.configure_table_data('knowledge_entries', [mock_entry])
        
        with patch.object(tool.registry, 'client', mock_supabase):
            result = await tool.execute({
                "zettel_id": "049-registry-category",
                "source": "registry"
            })
            
            result_data = json.loads(result)
            assert result_data["zettel_id"] == "049-registry-category"
            assert result_data.get("category") == "email-infrastructure/smtp"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_download_preserves_category(self, temp_user_dir, mock_supabase):
        """Test that downloading from registry preserves category."""
        tool = GetTool()
        
        # Setup mock registry entry with category
        mock_entry = {
            "zettel_id": "050-download-category",
            "title": "Download Category",
            "content": "# Test\n\nContent",
            "entry_type": "pattern",
            "category": "email-infrastructure/smtp",
            "tags": [],
            "version": "1.0.0"
        }
        
        mock_supabase.configure_table_data('knowledge_entries', mock_entry)
        
        user_dir = temp_user_dir / ".knowledge-kiwi"
        
        with patch.object(tool.resolver, 'user_knowledge_dir', user_dir), \
             patch.object(tool.registry, 'client', mock_supabase), \
             patch('pathlib.Path.home', return_value=temp_user_dir):
            
            result = await tool.execute({
                "zettel_id": "050-download-category",
                "source": "registry",
                "destination": "user"
            })
            
            result_data = json.loads(result)
            assert result_data["zettel_id"] == "050-download-category"
            
            # Verify file was created in correct nested category
            file_path = user_dir / "email-infrastructure" / "smtp" / "050-download-category.md"
            assert file_path.exists(), f"File not found at {file_path}. User dir contents: {list(user_dir.rglob('*'))}"
            
            # Verify category is in frontmatter
            from knowledge_kiwi.utils.knowledge_resolver import parse_knowledge_file
            file_data = parse_knowledge_file(file_path)
            assert file_data.get("category") == "email-infrastructure/smtp"

