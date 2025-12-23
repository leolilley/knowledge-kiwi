"""
Tests for manage tool (CRUD operations).
"""

import pytest
import json
from unittest.mock import patch, Mock
from pathlib import Path

from knowledge_kiwi.tools.manage import ManageTool


class TestManageTool:
    """Tests for ManageTool."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_entry_success(self, temp_project_dir):
        """Test successfully creating a new entry."""
        tool = ManageTool()
        
        with patch.object(tool.resolver, 'project_knowledge_dir', temp_project_dir / ".ai" / "knowledge"), \
             patch.object(tool.resolver, 'user_knowledge_dir', Path("/tmp/empty")):
            
            result = await tool.execute({
                "action": "create",
                "zettel_id": "043-new-entry",
                "title": "New Entry",
                "content": "# New Entry\n\nContent here.",
                "entry_type": "pattern",
                "tags": ["new", "test"],
                "location": "project"
            })
            
            result_data = json.loads(result)
            assert result_data["status"] == "success"
            assert result_data["action"] == "create"
            assert result_data["zettel_id"] == "043-new-entry"
            
            # Verify file was created (category is pluralized from entry_type)
            file_path = temp_project_dir / ".ai" / "knowledge" / "patterns" / "043-new-entry.md"
            assert file_path.exists()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_entry_duplicate(self, temp_project_dir, sample_knowledge_file):
        """Test creating duplicate entry fails."""
        tool = ManageTool()
        
        with patch.object(tool.resolver, 'project_knowledge_dir', temp_project_dir / ".ai" / "knowledge"), \
             patch.object(tool.resolver, 'user_knowledge_dir', Path("/tmp/empty")):
            
            result = await tool.execute({
                "action": "create",
                "zettel_id": "042-test-entry",  # Already exists
                "title": "Duplicate",
                "content": "Content",
                "entry_type": "pattern",
                "location": "project"
            })
            
            result_data = json.loads(result)
            assert "error" in result_data
            assert "already exists" in result_data["error"].lower()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_update_entry_success(self, temp_project_dir, sample_knowledge_file):
        """Test successfully updating an entry."""
        tool = ManageTool()
        
        with patch.object(tool.resolver, 'project_knowledge_dir', temp_project_dir / ".ai" / "knowledge"), \
             patch.object(tool.resolver, 'user_knowledge_dir', Path("/tmp/empty")):
            
            result = await tool.execute({
                "action": "update",
                "zettel_id": "042-test-entry",
                "content": "# Updated Content\n\nNew content here."
            })
            
            result_data = json.loads(result)
            assert result_data["status"] == "success"
            assert result_data["action"] == "update"
            
            # Verify content was updated (category is pluralized from entry_type)
            file_path = temp_project_dir / ".ai" / "knowledge" / "patterns" / "042-test-entry.md"
            content = file_path.read_text()
            assert "Updated Content" in content

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_delete_entry_success(self, temp_project_dir, sample_knowledge_file):
        """Test successfully deleting an entry."""
        tool = ManageTool()
        
        with patch.object(tool.resolver, 'project_knowledge_dir', temp_project_dir / ".ai" / "knowledge"), \
             patch.object(tool.resolver, 'user_knowledge_dir', Path("/tmp/empty")):
            
            result = await tool.execute({
                "action": "delete",
                "zettel_id": "042-test-entry",
                "confirm": True
            })
            
            result_data = json.loads(result)
            assert result_data["status"] == "success"
            assert result_data["action"] == "delete"
            
            # Verify file was deleted (category is pluralized from entry_type)
            file_path = temp_project_dir / ".ai" / "knowledge" / "patterns" / "042-test-entry.md"
            assert not file_path.exists()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_delete_entry_no_confirm(self):
        """Test delete without confirmation fails."""
        tool = ManageTool()
        
        result = await tool.execute({
            "action": "delete",
            "zettel_id": "042-test-entry",
            "confirm": False
        })
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "confirm" in result_data["error"].lower()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_delete_entry_from_project_only(self, temp_project_dir, sample_knowledge_file):
        """Test deleting entry from project space only."""
        tool = ManageTool()
        
        with patch.object(tool.resolver, 'project_knowledge_dir', temp_project_dir / ".ai" / "knowledge"), \
             patch.object(tool.resolver, 'user_knowledge_dir', Path("/tmp/empty")):
            
            result = await tool.execute({
                "action": "delete",
                "zettel_id": "042-test-entry",
                "source": "local",
                "location": "project",
                "confirm": True
            })
            
            result_data = json.loads(result)
            assert result_data["status"] == "success"
            assert result_data["deleted_from"]["local"] == ["project"]
            assert result_data["deleted_from"]["registry"] is False

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_delete_entry_from_user_only(self, temp_user_dir):
        """Test deleting entry from user space only."""
        tool = ManageTool()
        
        # Create entry in user space
        user_dir = temp_user_dir / ".knowledge-kiwi" / "patterns"
        user_dir.mkdir(parents=True, exist_ok=True)
        from knowledge_kiwi.utils.knowledge_resolver import write_knowledge_file
        write_knowledge_file(
            file_path=user_dir / "042-user-entry.md",
            zettel_id="042-user-entry",
            title="User Entry",
            content="# User Entry\n\nContent",
            entry_type="pattern"
        )
        
        with patch.object(tool.resolver, 'user_knowledge_dir', temp_user_dir / ".knowledge-kiwi"), \
             patch('pathlib.Path.home', return_value=temp_user_dir):
            
            result = await tool.execute({
                "action": "delete",
                "zettel_id": "042-user-entry",
                "source": "local",
                "location": "user",
                "confirm": True
            })
            
            result_data = json.loads(result)
            assert result_data["status"] == "success"
            assert result_data["deleted_from"]["local"] == ["user"]
            
            # Verify file was deleted
            assert not (user_dir / "042-user-entry.md").exists()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_delete_entry_from_registry(self, mock_supabase):
        """Test deleting entry from registry."""
        tool = ManageTool()
        
        # Setup mock registry entry
        mock_supabase.configure_table_data('knowledge_entries', {
            "zettel_id": "042-registry-delete",
            "title": "Registry Entry",
            "content": "Content",
            "entry_type": "pattern",
            "tags": []
        })
        
        with patch.object(tool.registry, 'client', mock_supabase):
            result = await tool.execute({
                "action": "delete",
                "zettel_id": "042-registry-delete",
                "source": "registry",
                "confirm": True
            })
            
            result_data = json.loads(result)
            assert result_data["status"] == "success"
            assert result_data["deleted_from"]["registry"] is True
            assert result_data["deleted_from"]["local"] == []

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_delete_entry_from_both_tiers(self, temp_project_dir, sample_knowledge_file, mock_supabase):
        """Test deleting entry from both local and registry."""
        tool = ManageTool()
        
        # Setup mock registry entry
        mock_supabase.configure_table_data('knowledge_entries', {
            "zettel_id": "042-test-entry",
            "title": "Test Entry",
            "content": "Content",
            "entry_type": "pattern",
            "tags": []
        })
        
        with patch.object(tool.resolver, 'project_knowledge_dir', temp_project_dir / ".ai" / "knowledge"), \
             patch.object(tool.resolver, 'user_knowledge_dir', Path("/tmp/empty")), \
             patch.object(tool.registry, 'client', mock_supabase):
            
            result = await tool.execute({
                "action": "delete",
                "zettel_id": "042-test-entry",
                "source": ["local", "registry"],
                "confirm": True
            })
            
            result_data = json.loads(result)
            assert result_data["status"] == "success"
            assert "project" in result_data["deleted_from"]["local"]
            assert result_data["deleted_from"]["registry"] is True
            
            # Verify local file was deleted
            file_path = temp_project_dir / ".ai" / "knowledge" / "patterns" / "042-test-entry.md"
            assert not file_path.exists()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_delete_entry_registry_with_relationships(self, mock_supabase):
        """Test deleting entry from registry when relationships exist."""
        tool = ManageTool()
        
        # Setup mock registry entry
        mock_supabase.configure_table_data('knowledge_entries', {
            "zettel_id": "042-with-rels",
            "title": "Entry with Relationships",
            "content": "Content",
            "entry_type": "pattern",
            "tags": []
        })
        
        # Setup relationships
        mock_supabase.configure_table_data('knowledge_relationships', [
            {
                "from_zettel_id": "042-with-rels",
                "to_zettel_id": "043-related",
                "relationship_type": "references"
            }
        ])
        
        with patch.object(tool.registry, 'client', mock_supabase):
            # Try to delete without cascade - should fail
            result = await tool.execute({
                "action": "delete",
                "zettel_id": "042-with-rels",
                "source": "registry",
                "confirm": True
            })
            
            result_data = json.loads(result)
            assert result_data["status"] == "error"
            assert "relationship" in result_data.get("errors", {}).get("registry", "").lower()
            
            # Delete with cascade - should succeed
            result = await tool.execute({
                "action": "delete",
                "zettel_id": "042-with-rels",
                "source": "registry",
                "cascade_relationships": True,
                "confirm": True
            })
            
            result_data = json.loads(result)
            assert result_data["status"] == "success"
            assert result_data.get("relationships_deleted", 0) > 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_delete_entry_partial_success(self, temp_project_dir, sample_knowledge_file, mock_supabase):
        """Test partial success when deleting from multiple tiers."""
        tool = ManageTool()
        
        # Don't setup registry entry (so it won't be found there)
        
        with patch.object(tool.resolver, 'project_knowledge_dir', temp_project_dir / ".ai" / "knowledge"), \
             patch.object(tool.resolver, 'user_knowledge_dir', Path("/tmp/empty")), \
             patch.object(tool.registry, 'client', mock_supabase):
            
            result = await tool.execute({
                "action": "delete",
                "zettel_id": "042-test-entry",
                "source": ["local", "registry"],
                "confirm": True
            })
            
            result_data = json.loads(result)
            # Should succeed locally, fail in registry
            assert result_data["status"] in ["success", "partial"]
            assert "project" in result_data["deleted_from"]["local"]
            assert result_data["deleted_from"]["registry"] is False

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_publish_entry_success(self, temp_project_dir, sample_knowledge_file, mock_supabase):
        """Test successfully publishing an entry to registry."""
        tool = ManageTool()
        
        # Setup mock registry
        mock_supabase.configure_table_data('knowledge_entries', None)
        
        with patch.object(tool.resolver, 'project_knowledge_dir', temp_project_dir / ".ai" / "knowledge"), \
             patch.object(tool.resolver, 'user_knowledge_dir', Path("/tmp/empty")), \
             patch.object(tool.registry, 'client', mock_supabase):
            
            result = await tool.execute({
                "action": "publish",
                "zettel_id": "042-test-entry",
                "location": "project"
            })
            
            result_data = json.loads(result)
            assert result_data["status"] == "success"
            assert result_data["action"] == "publish"
            assert "version" in result_data

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_entry_missing_fields(self):
        """Test create with missing required fields."""
        tool = ManageTool()
        
        result = await tool.execute({
            "action": "create",
            "zettel_id": "043-test",
            # Missing title and content
        })
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "required" in result_data["error"].lower()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_invalid_action(self):
        """Test with invalid action."""
        tool = ManageTool()
        
        result = await tool.execute({
            "action": "invalid",
            "zettel_id": "042-test"
        })
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "unknown action" in result_data["error"].lower() or "invalid" in result_data["error"].lower()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_entry_with_custom_category(self, temp_project_dir):
        """Test creating entry with custom category."""
        tool = ManageTool()
        
        with patch.object(tool.resolver, 'project_knowledge_dir', temp_project_dir / ".ai" / "knowledge"), \
             patch.object(tool.resolver, 'user_knowledge_dir', Path("/tmp/empty")):
            
            result = await tool.execute({
                "action": "create",
                "zettel_id": "044-custom-category",
                "title": "Custom Category Entry",
                "content": "# Custom\n\nContent",
                "entry_type": "pattern",
                "category": "email-infrastructure/smtp",  # Custom nested category
                "location": "project"
            })
            
            result_data = json.loads(result)
            assert result_data["status"] == "success"
            assert result_data["category"] == "email-infrastructure/smtp"
            
            # Verify file was created in nested directory
            file_path = temp_project_dir / ".ai" / "knowledge" / "email-infrastructure" / "smtp" / "044-custom-category.md"
            assert file_path.exists()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_entry_category_fallback(self, temp_project_dir):
        """Test that entry_type fallback works when category not provided."""
        tool = ManageTool()
        
        with patch.object(tool.resolver, 'project_knowledge_dir', temp_project_dir / ".ai" / "knowledge"), \
             patch.object(tool.resolver, 'user_knowledge_dir', Path("/tmp/empty")):
            
            result = await tool.execute({
                "action": "create",
                "zettel_id": "045-fallback",
                "title": "Fallback Test",
                "content": "# Test\n\nContent",
                "entry_type": "learning",  # No category - should use fallback
                "location": "project"
            })
            
            result_data = json.loads(result)
            assert result_data["status"] == "success"
            assert result_data["category"] == "learnings"  # Pluralized from entry_type
            
            # Verify file was created in fallback category
            file_path = temp_project_dir / ".ai" / "knowledge" / "learnings" / "045-fallback.md"
            assert file_path.exists()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_entry_category_sanitization(self, temp_project_dir):
        """Test that category names are sanitized for filesystem."""
        tool = ManageTool()
        
        with patch.object(tool.resolver, 'project_knowledge_dir', temp_project_dir / ".ai" / "knowledge"), \
             patch.object(tool.resolver, 'user_knowledge_dir', Path("/tmp/empty")):
            
            result = await tool.execute({
                "action": "create",
                "zettel_id": "046-sanitized",
                "title": "Sanitized",
                "content": "# Test\n\nContent",
                "entry_type": "pattern",
                "category": "Email Infrastructure/SMTP",  # Should be sanitized
                "location": "project"
            })
            
            result_data = json.loads(result)
            assert result_data["status"] == "success"
            # Should be lowercase with hyphens
            assert "email-infrastructure/smtp" in result_data["category"].lower()
            
            # Verify file was created
            file_path = temp_project_dir / ".ai" / "knowledge" / result_data["category"] / "046-sanitized.md"
            assert file_path.exists()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_publish_entry_with_category(self, temp_project_dir, mock_supabase):
        """Test publishing entry with category to registry."""
        tool = ManageTool()
        
        # Create entry with category
        nested_dir = temp_project_dir / ".ai" / "knowledge" / "email-infrastructure" / "smtp"
        nested_dir.mkdir(parents=True, exist_ok=True)
        
        from knowledge_kiwi.utils.knowledge_resolver import write_knowledge_file
        write_knowledge_file(
            file_path=nested_dir / "047-publish-category.md",
            zettel_id="047-publish-category",
            title="Publish with Category",
            content="# Test\n\nContent",
            entry_type="pattern",
            category="email-infrastructure/smtp"
        )
        
        mock_supabase.configure_table_data('knowledge_entries', None)
        
        with patch.object(tool.resolver, 'project_knowledge_dir', temp_project_dir / ".ai" / "knowledge"), \
             patch.object(tool.resolver, 'user_knowledge_dir', Path("/tmp/empty")), \
             patch.object(tool.registry, 'client', mock_supabase):
            
            result = await tool.execute({
                "action": "publish",
                "zettel_id": "047-publish-category",
                "location": "project"
            })
            
            result_data = json.loads(result)
            assert result_data["status"] == "success"
            
            # Verify category was passed to registry
            # (Would need to check mock calls, but at least verify no error)

