"""
Tests for KnowledgeResolver.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
import yaml

from knowledge_kiwi.utils.knowledge_resolver import (
    KnowledgeResolver,
    parse_knowledge_file,
    write_knowledge_file
)


class TestKnowledgeResolver:
    """Tests for KnowledgeResolver."""

    def test_resolve_entry_project_space(self, temp_project_dir, sample_knowledge_file):
        """Test resolving entry from project space."""
        resolver = KnowledgeResolver(project_root=temp_project_dir)
        
        result = resolver.resolve_entry("042-test-entry", "local")
        
        assert result["location"] == "project"
        assert result["path"] is not None
        assert result["path"].exists()

    def test_resolve_entry_user_space(self, temp_user_dir):
        """Test resolving entry from user space."""
        # Create entry in user space
        user_dir = temp_user_dir / ".knowledge-kiwi" / "pattern"
        user_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = user_dir / "042-user-entry.md"
        write_knowledge_file(
            file_path=file_path,
            zettel_id="042-user-entry",
            title="User Entry",
            content="Content",
            entry_type="pattern"
        )
        
        resolver = KnowledgeResolver()
        # Patch user directory
        resolver.user_knowledge_dir = temp_user_dir / ".knowledge-kiwi"
        
        result = resolver.resolve_entry("042-user-entry", "local")
        
        assert result["location"] == "user"
        assert result["path"] == file_path

    def test_resolve_entry_not_found(self, temp_project_dir):
        """Test resolving non-existent entry."""
        resolver = KnowledgeResolver(project_root=temp_project_dir)
        
        result = resolver.resolve_entry("999-nonexistent", "local")
        
        assert result["location"] is None
        assert result["path"] is None

    def test_resolve_entry_registry_source(self):
        """Test resolving entry with registry source."""
        resolver = KnowledgeResolver()
        
        result = resolver.resolve_entry("042-entry", "registry")
        
        assert result["location"] == "registry"
        assert result["path"] is None

    def test_search_local_project_space(self, temp_project_dir, sample_knowledge_file):
        """Test searching local project space."""
        resolver = KnowledgeResolver(project_root=temp_project_dir)
        
        results = resolver.search_local("test", limit=10)
        
        assert len(results) > 0
        assert results[0]["zettel_id"] == "042-test-entry"
        assert results[0]["source_location"] == "project"

    def test_search_local_with_filters(self, temp_project_dir, sample_knowledge_file):
        """Test searching with entry_type and tags filters."""
        resolver = KnowledgeResolver(project_root=temp_project_dir)
        
        results = resolver.search_local(
            "test",
            entry_type="pattern",
            tags=["test"],
            limit=10
        )
        
        assert len(results) > 0
        assert results[0]["entry_type"] == "pattern"

    def test_search_local_no_results(self, temp_project_dir):
        """Test searching with no results."""
        resolver = KnowledgeResolver(project_root=temp_project_dir)
        
        results = resolver.search_local("nonexistent", limit=10)
        
        assert len(results) == 0

    def test_discover_categories(self, temp_project_dir):
        """Test discovering categories dynamically."""
        resolver = KnowledgeResolver(project_root=temp_project_dir)
        
        # Create multiple categories including nested
        base_dir = temp_project_dir / ".ai" / "knowledge"
        (base_dir / "patterns").mkdir(parents=True, exist_ok=True)
        (base_dir / "learnings").mkdir(parents=True, exist_ok=True)
        (base_dir / "email-infrastructure" / "smtp").mkdir(parents=True, exist_ok=True)
        (base_dir / "aws" / "lambda").mkdir(parents=True, exist_ok=True)
        
        categories = resolver.discover_categories(base_dir)
        
        # Should discover all directories (including parent directories)
        assert "patterns" in categories
        assert "learnings" in categories
        assert "email-infrastructure" in categories  # Parent directory
        assert "email-infrastructure/smtp" in categories  # Nested
        assert "aws" in categories  # Parent directory
        assert "aws/lambda" in categories  # Nested
        assert len(categories) >= 6  # At least 6 (may include more if temp dir has others)

    def test_resolve_entry_nested_category(self, temp_project_dir):
        """Test resolving entry in nested category."""
        resolver = KnowledgeResolver(project_root=temp_project_dir)
        
        # Create entry in nested category
        nested_dir = temp_project_dir / ".ai" / "knowledge" / "email-infrastructure" / "smtp"
        nested_dir.mkdir(parents=True, exist_ok=True)
        
        from knowledge_kiwi.utils.knowledge_resolver import write_knowledge_file
        file_path = nested_dir / "001-spf.md"
        write_knowledge_file(
            file_path=file_path,
            zettel_id="001-spf",
            title="SPF Records",
            content="# SPF",
            entry_type="pattern"
        )
        
        result = resolver.resolve_entry("001-spf", "local")
        
        assert result["location"] == "project"
        assert result["path"] == file_path
        assert result["path"].exists()

    def test_search_local_nested_category(self, temp_project_dir):
        """Test searching entries in nested categories."""
        resolver = KnowledgeResolver(project_root=temp_project_dir)
        
        # Create entry in nested category
        nested_dir = temp_project_dir / ".ai" / "knowledge" / "email-infrastructure" / "smtp"
        nested_dir.mkdir(parents=True, exist_ok=True)
        
        from knowledge_kiwi.utils.knowledge_resolver import write_knowledge_file
        write_knowledge_file(
            file_path=nested_dir / "001-spf.md",
            zettel_id="001-spf",
            title="SPF Records",
            content="# SPF Records\n\nSPF configuration",
            entry_type="pattern"
        )
        
        results = resolver.search_local("SPF", limit=10)
        
        assert len(results) > 0
        assert results[0]["zettel_id"] == "001-spf"
        assert "email-infrastructure/smtp" in results[0]["category"]

    def test_search_local_with_category_filter(self, temp_project_dir):
        """Test searching with category filter."""
        resolver = KnowledgeResolver(project_root=temp_project_dir)
        
        # Create entries in different categories
        base_dir = temp_project_dir / ".ai" / "knowledge"
        (base_dir / "patterns").mkdir(parents=True, exist_ok=True)
        (base_dir / "email-infrastructure" / "smtp").mkdir(parents=True, exist_ok=True)
        
        from knowledge_kiwi.utils.knowledge_resolver import write_knowledge_file
        
        # Entry in patterns
        write_knowledge_file(
            file_path=base_dir / "patterns" / "001-pattern.md",
            zettel_id="001-pattern",
            title="Pattern",
            content="Pattern content",
            entry_type="pattern"
        )
        
        # Entry in nested category
        write_knowledge_file(
            file_path=base_dir / "email-infrastructure" / "smtp" / "002-spf.md",
            zettel_id="002-spf",
            title="SPF",
            content="SPF unique content text",
            entry_type="pattern"
        )
        
        # Search with category filter - use unique query
        results = resolver.search_local("SPF unique", category="email-infrastructure/smtp", limit=10)
        
        # Should only find the entry in the specified category
        assert len(results) >= 1
        spf_results = [r for r in results if r["zettel_id"] == "002-spf"]
        assert len(spf_results) == 1
        assert spf_results[0]["category"] == "email-infrastructure/smtp"


class TestParseKnowledgeFile:
    """Tests for parse_knowledge_file function."""

    def test_parse_file_with_frontmatter(self, temp_project_dir):
        """Test parsing file with YAML frontmatter."""
        file_path = temp_project_dir / "test.md"
        content = """---
zettel_id: 042-test
title: Test Entry
entry_type: pattern
tags: [test, example]
---
# Test Entry

Content here.
"""
        file_path.write_text(content)
        
        result = parse_knowledge_file(file_path)
        
        assert result["zettel_id"] == "042-test"
        assert result["title"] == "Test Entry"
        assert result["entry_type"] == "pattern"
        assert result["tags"] == ["test", "example"]
        assert "Content here." in result["content"]

    def test_parse_file_without_frontmatter(self, temp_project_dir):
        """Test parsing file without frontmatter."""
        file_path = temp_project_dir / "test.md"
        content = "# Test Entry\n\nContent here."
        file_path.write_text(content)
        
        result = parse_knowledge_file(file_path)
        
        assert result["zettel_id"] == "test"  # From filename
        assert "Content here." in result["content"]


class TestWriteKnowledgeFile:
    """Tests for write_knowledge_file function."""

    def test_write_file_success(self, temp_project_dir):
        """Test successfully writing a knowledge file."""
        file_path = temp_project_dir / "test.md"
        
        write_knowledge_file(
            file_path=file_path,
            zettel_id="042-test",
            title="Test Entry",
            content="# Test\n\nContent",
            entry_type="pattern",
            tags=["test"]
        )
        
        assert file_path.exists()
        
        # Verify content
        content = file_path.read_text()
        assert "zettel_id: 042-test" in content
        assert "# Test" in content

    def test_write_file_creates_directory(self, temp_project_dir):
        """Test that write creates parent directories."""
        file_path = temp_project_dir / "nested" / "dir" / "test.md"
        
        write_knowledge_file(
            file_path=file_path,
            zettel_id="042-test",
            title="Test",
            content="Content",
            entry_type="pattern"
        )
        
        assert file_path.exists()
        assert file_path.parent.exists()

