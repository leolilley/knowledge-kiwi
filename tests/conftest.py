"""
Shared pytest fixtures for Knowledge Kiwi MCP tests

Centralized mocking infrastructure to eliminate duplication across test files.
Provides reusable fixtures and helper classes for mocking Supabase and file system operations.
"""

import sys
from pathlib import Path
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, Optional, List
import tempfile
import shutil

# Add project root to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


# ============================================================================
# Mock Helper Classes
# ============================================================================

class SupabaseQueryBuilder:
    """
    Builder pattern for creating Supabase query mocks.
    
    Creates a fluent query chain that supports methods like:
    .select().eq().in_().limit().execute().data
    """
    
    def __init__(self, data: Any = None):
        """Initialize query builder with optional default data."""
        self.data = data if data is not None else []
        self._count = None
        self._query = Mock()
        self._setup_chain()
    
    def _setup_chain(self):
        """Setup the fluent query chain - all methods return self to allow chaining."""
        self._is_single = False
        self._is_maybe_single = False
        
        # All query builder methods return self to allow chaining
        self._query.eq = Mock(return_value=self._query)
        self._query.in_ = Mock(return_value=self._query)
        self._query.limit = Mock(return_value=self._query)
        self._query.offset = Mock(return_value=self._query)
        self._query.order = Mock(return_value=self._query)
        
        # Track single() calls
        def single_side_effect():
            self._is_single = True
            return self._query
        self._query.single = Mock(side_effect=single_side_effect)
        
        def maybe_single_side_effect():
            self._is_maybe_single = True
            return self._query
        self._query.maybe_single = Mock(side_effect=maybe_single_side_effect)
        
        # select() is handled by select_side_effect
        def select_side_effect(*args, **kwargs):
            if 'count' in kwargs:
                self._count = kwargs['count']
            return self._query
        self._query.select = Mock(side_effect=select_side_effect)
        
        self._query.insert = Mock(return_value=self._query)
        self._query.update = Mock(return_value=self._query)
        self._query.delete = Mock(return_value=self._query)
        
        # Execute returns a response object with data attribute
        def execute_side_effect():
            mock_response = Mock()
            if self._is_single or self._is_maybe_single:
                if isinstance(self.data, list) and len(self.data) > 0:
                    mock_response.data = self.data[0]
                elif isinstance(self.data, dict):
                    mock_response.data = self.data
                else:
                    mock_response.data = self.data
            else:
                if isinstance(self.data, dict):
                    mock_response.data = [self.data]
                else:
                    mock_response.data = self.data if self.data is not None else []
            
            if self._count == 'exact':
                if isinstance(mock_response.data, list):
                    count_value = len(mock_response.data)
                else:
                    count_value = 1 if mock_response.data else 0
                mock_response.count = count_value
            
            return mock_response
        
        self._query.execute = Mock(side_effect=execute_side_effect)
    
    def build(self):
        """Return the configured query mock."""
        return self._query


class SupabaseTableMock:
    """Mock for a Supabase table with query builder support."""
    
    def __init__(self, default_data: Any = None):
        """Initialize table mock with optional default data."""
        self.default_data = default_data if default_data is not None else []
    
    def select(self, *args, **kwargs):
        """Mock select() - returns a query builder with current default_data."""
        builder = SupabaseQueryBuilder(self.default_data)
        if 'count' in kwargs:
            builder._count = kwargs['count']
        return builder.build()
    
    def insert(self, *args, **kwargs):
        """Mock insert() - returns a query builder."""
        return SupabaseQueryBuilder().build()
    
    def update(self, *args, **kwargs):
        """Mock update() - returns a query builder."""
        builder = SupabaseQueryBuilder()
        query = builder.build()
        query.execute = Mock(return_value=Mock(data=[]))
        return query
    
    def delete(self, *args, **kwargs):
        """Mock delete() - returns a query builder."""
        return SupabaseQueryBuilder().build()


class MockSupabaseClient:
    """
    Centralized Supabase client mock for Knowledge Kiwi.
    
    Provides a complete mock of SupabaseClient with:
    - knowledge_entries table
    - knowledge_relationships table
    - knowledge_collections table
    - RPC support for search_knowledge_fulltext
    """
    
    def __init__(self):
        """Initialize mock Supabase client with knowledge tables."""
        self._tables = {
            'knowledge_entries': SupabaseTableMock(),
            'knowledge_relationships': SupabaseTableMock(),
            'knowledge_collections': SupabaseTableMock(),
        }
        
        # Setup table() method for direct table access
        def table_side_effect(table_name: str):
            """Return table mock for given table name."""
            if table_name in self._tables:
                return self._tables[table_name]
            new_table = SupabaseTableMock()
            self._tables[table_name] = new_table
            return new_table
        
        self.table = Mock(side_effect=table_side_effect)
        
        # Setup RPC for search_knowledge_fulltext
        self.rpc = Mock()
    
    def configure_table_data(self, table_name: str, data: Any):
        """Configure default data for a table."""
        if table_name in self._tables:
            self._tables[table_name].default_data = data
        else:
            self._tables[table_name] = SupabaseTableMock(data)
    
    def setup_rpc_search(self, query: str, return_data: List[Dict[str, Any]]):
        """Setup RPC search_knowledge_fulltext to return specific data."""
        mock_response = Mock()
        mock_response.data = return_data
        mock_response.execute = Mock(return_value=mock_response)
        
        # RPC returns a query builder that has execute()
        mock_rpc_query = Mock()
        mock_rpc_query.execute = Mock(return_value=mock_response)
        
        def rpc_side_effect(function_name, *args, **kwargs):
            if function_name == 'search_knowledge_fulltext':
                return mock_rpc_query
            return Mock(execute=Mock(return_value=Mock(data=[])))
        
        self.rpc = Mock(side_effect=rpc_side_effect)


# ============================================================================
# Base Fixtures
# ============================================================================

@pytest.fixture
def mock_supabase():
    """
    Standard Supabase client mock.
    
    Returns a MockSupabaseClient instance with knowledge tables pre-configured.
    """
    return MockSupabaseClient()


@pytest.fixture
def temp_project_dir():
    """
    Create a temporary directory for testing project knowledge storage.
    
    Yields a Path to the temp directory and cleans up after.
    """
    temp_dir = Path(tempfile.mkdtemp())
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_user_dir():
    """
    Create a temporary directory for testing user knowledge storage.
    
    Yields a Path to the temp directory and cleans up after.
    """
    temp_dir = Path(tempfile.mkdtemp())
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_knowledge_entry():
    """Sample knowledge entry data for testing."""
    return {
        "zettel_id": "042-test-entry",
        "title": "Test Knowledge Entry",
        "content": "# Test Entry\n\nThis is test content for knowledge entries.",
        "entry_type": "pattern",
        "tags": ["test", "example"],
        "source_type": "manual",
        "source_url": None,
        "version": "1.0.0"
    }


@pytest.fixture
def sample_knowledge_file(temp_project_dir, sample_knowledge_entry):
    """
    Create a sample knowledge entry file in temp directory.
    
    Returns the path to the created file.
    """
    import yaml
    from pathlib import Path
    
    entry_type = sample_knowledge_entry["entry_type"]
    zettel_id = sample_knowledge_entry["zettel_id"]
    
    # Create directory structure (pluralize entry_type for category)
    category = entry_type + "s" if not entry_type.endswith("s") else entry_type
    knowledge_dir = temp_project_dir / ".ai" / "knowledge" / category
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    
    # Create file
    file_path = knowledge_dir / f"{zettel_id}.md"
    
    # Build frontmatter
    frontmatter = {
        "zettel_id": zettel_id,
        "title": sample_knowledge_entry["title"],
        "entry_type": entry_type,
        "tags": sample_knowledge_entry["tags"],
    }
    
    if sample_knowledge_entry.get("source_type"):
        frontmatter["source_type"] = sample_knowledge_entry["source_type"]
    
    if sample_knowledge_entry.get("source_url"):
        frontmatter["source_url"] = sample_knowledge_entry["source_url"]
    
    # Write file
    frontmatter_yaml = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
    file_content = f"---\n{frontmatter_yaml}---\n\n{sample_knowledge_entry['content']}\n"
    
    file_path.write_text(file_content, encoding="utf-8")
    
    return file_path

