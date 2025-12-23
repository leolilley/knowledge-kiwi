# Knowledge Kiwi Redesign Plan

## Purpose

Redesign Knowledge Kiwi to follow the same 3-tier storage pattern as Script Kiwi and Context Kiwi, using plain markdown files (not SQL) and removing RAG/embeddings complexity. This creates a consistent, scalable architecture across all Kiwi projects.

## Outcomes

- Knowledge Kiwi uses 3-tier storage: **Project → User → Registry** (same tiers as Script Kiwi)
- **Explicit source selection**: Tools require `source` parameter (`"local"` | `"registry"` | `["local", "registry"]`) - no automatic fallback
- Knowledge entries stored as plain markdown files (like directives, not SQL)
- 5 core tools aligned with Script Kiwi pattern: `search`, `get`, `manage`, `link`, `help`
- No RAG/embeddings complexity (removed from scope)
- Clear separation: Local knowledge (fast, offline) vs. Remote registry (shared, versioned)
- Supabase registry for remote knowledge base (searchable, shareable)

## Current State vs. Target State

### Current State (Problematic)
- 9 individual tools (create_entry, get_entry, update_entry, delete_entry, search_knowledge, link_entries, create_collection, sync_to_database, sync_from_database)
- Bidirectional sync between local files and database (confusing)
- Database as source of truth (SQL-based)
- RAG/embeddings complexity (feature-flagged but adds complexity)
- Inconsistent with Script Kiwi pattern

### Target State (Clean)
- 5 core tools aligned with Script Kiwi
- 3-tier storage: Project (`.ai/knowledge/`) → User (`~/.knowledge-kiwi/`) → Registry (Supabase)
- **Explicit source selection**: `source: "local"` (project + user) or `source: "registry"` (remote registry) - no automatic fallback
- Plain markdown files (like directives)
- No RAG/embeddings (removed from scope)
- Clear separation between local and remote knowledge

## Storage Tiers

### 1. Project Space (`.ai/knowledge/`)
- **Purpose**: Project-specific knowledge entries
- **Priority**: Highest (checked first)
- **Location**: `{project_root}/.ai/knowledge/{category}/`
- **Example**: `.ai/knowledge/patterns/042-email-deliverability.md`
- **Use case**: Project-specific learnings, not shared
- **Format**: Plain markdown files with frontmatter

### 2. User Space (`~/.knowledge-kiwi/`)
- **Purpose**: Personal knowledge library, downloaded from registry
- **Priority**: Second (checked if not in project)
- **Location**: `~/.knowledge-kiwi/{category}/`
- **Example**: `~/.knowledge-kiwi/apis/001-apify-basics.md`
- **Use case**: Personal knowledge, available across all projects
- **Format**: Plain markdown files with frontmatter

### 3. Registry (Supabase `knowledge_entries` table)
- **Purpose**: Remote knowledge base (searchable, shareable)
- **Location**: Remote Supabase database
- **Use case**: Shared knowledge, versioned entries
- **Format**: Stored in database, can be downloaded as markdown files

### Resolution Logic

**Explicit Source Selection** (different from Script Kiwi's automatic fallback):

Tools accept a `source` parameter to explicitly choose where to search:
- `source: "local"` - Checks project space first, then user space (reports which one)
- `source: "registry"` - Only checks registry (Supabase)
- `source: ["local", "registry"]` - Checks both, with local results prioritized

**Local Resolution Order** (when `source: "local"`):
1. **Project space** (`.ai/knowledge/`) - checked first
2. **User space** (`~/.knowledge-kiwi/`) - checked if not in project
3. Response includes `source_location: "project" | "user"` to indicate where it was found

**Why explicit?** Allows clear separation between local knowledge (fast, offline) and remote registry (shared, versioned). No automatic fallback to avoid unexpected network calls.

## File Format

Knowledge entries are plain markdown files with YAML frontmatter (like directives):

```markdown
---
zettel_id: 042-email-deliverability
title: Email Deliverability Best Practices
entry_type: pattern
tags: [email, deliverability, infrastructure]
source_type: experiment
source_url: https://example.com
created_at: 2025-01-15T10:00:00Z
updated_at: 2025-01-15T10:00:00Z
---

# Email Deliverability Best Practices

Content here...

## Key Points

- Point 1
- Point 2

## Related Entries

- [[043-spf-records]] - SPF record setup
- [[044-dkim-setup]] - DKIM configuration
```

### Frontmatter Fields

- `zettel_id` (required): Unique identifier (e.g., "042-email-deliverability")
- `title` (required): Entry title
- `entry_type` (required): One of `api_fact`, `pattern`, `concept`, `learning`, `experiment`, `reference`, `template`, `workflow`
- `tags` (optional): Array of tags
- `source_type` (optional): One of `youtube`, `docs`, `experiment`, `manual`, `chat`, `book`, `article`, `course`
- `source_url` (optional): URL to source
- `created_at` (optional): ISO 8601 timestamp
- `updated_at` (optional): ISO 8601 timestamp

## 5 Core Tools

### 1. `search` - Search Knowledge Entries

**Purpose**: Search knowledge entries with explicit source selection

**Input**:
```json
{
  "query": "email deliverability",
  "source": "local",  // Required: "local" | "registry" | ["local", "registry"]
  "category": "patterns",  // Optional: filter by category
  "entry_type": "pattern",  // Optional: filter by entry type
  "tags": ["email"],  // Optional: filter by tags
  "limit": 10
}
```

**Behavior**:
- **If `source: "local"`**:
  1. Search project space: `.ai/knowledge/` (file system glob)
  2. Search user space: `~/.knowledge-kiwi/` (file system glob)
  3. Merge results (project results prioritized)
  4. Return with `source_location: "project" | "user"` for each result

- **If `source: "registry"`**:
  1. Search registry: Supabase full-text search (tsvector)
  2. Return results with `source_location: "registry"`

- **If `source: ["local", "registry"]`**:
  1. Search both local and db
  2. Merge results (local results prioritized)
  3. Return with `source_location` for each result

**Output**:
```json
{
  "query": "email deliverability",
  "source": "local",
  "results_count": 5,
  "results": [
    {
      "zettel_id": "042-email-deliverability",
      "title": "Email Deliverability Best Practices",
      "entry_type": "pattern",
      "tags": ["email", "deliverability"],
      "source_location": "project",  // "project" | "user" | "registry"
      "relevance_score": 0.85,
      "snippet": "..."
    }
  ]
}
```

### 2. `get` - Get Entry Details

**Purpose**: Get a specific entry with relationships and context

**Input**:
```json
{
  "zettel_id": "042-email-deliverability",
  "source": "local",  // Required: "local" | "registry" | ["local", "registry"]
  "include_relationships": true,  // Optional: include linked entries
  "include_backlinks": true,  // Optional: include entries that link to this
  "destination": "user"  // Optional: download from registry to "user" | "project" | ["user", "project"] (only if source includes "registry")
}
```

**Behavior**:
- **If `source: "local"`**:
  1. Check project space first: `.ai/knowledge/`
  2. If not found, check user space: `~/.knowledge-kiwi/`
  3. Read markdown file directly
  4. Parse frontmatter and content
  5. Return with `source_location: "project" | "user"`

- **If `source: "registry"`**:
  1. Fetch from Supabase registry
  2. Optionally download to user/project space if `destination` is specified
  3. Return with `source_location: "registry"`

- **If `source: ["local", "registry"]`**:
  1. Check local first (project → user)
  2. If not found locally, check registry
  3. Optionally download from registry to user/project space if `destination` is specified
  4. Return with `source_location` indicating where it was found

- **Relationships/backlinks**: Fetched from registry (requires `source` to include "registry" or relationships stored locally)

**Output**:
```json
{
  "zettel_id": "042-email-deliverability",
  "title": "Email Deliverability Best Practices",
  "content": "# Email Deliverability...",
  "entry_type": "pattern",
  "tags": ["email", "deliverability"],
  "source_location": "project",  // "project" | "user" | "registry"
  "relationships": [
    {
      "zettel_id": "043-spf-records",
      "relationship_type": "references",
      "direction": "outgoing"
    }
  ],
  "backlinks": [
    {
      "zettel_id": "044-email-campaigns",
      "relationship_type": "references",
      "direction": "incoming"
    }
  ]
}
```

### 3. `manage` - Unified CRUD Operations

**Purpose**: Create, update, delete, and publish knowledge entries

**Input** (Create):
```json
{
  "action": "create",
  "zettel_id": "042-email-deliverability",
  "title": "Email Deliverability Best Practices",
  "content": "# Email Deliverability...",
  "entry_type": "pattern",
  "tags": ["email", "deliverability"],
  "source_type": "experiment",
  "source_url": "https://example.com",
  "location": "project"  // Optional: "project" | "user" | "registry" (default: project)
}
```

**Input** (Update):
```json
{
  "action": "update",
  "zettel_id": "042-email-deliverability",
  "title": "Updated Title",  // Only include fields to update
  "content": "Updated content...",
  "tags": ["email", "deliverability", "infrastructure"]
}
```

**Input** (Delete):
```json
{
  "action": "delete",
  "zettel_id": "042-email-deliverability",
  "confirm": true  // Safety check
}
```

**Input** (Publish):
```json
{
  "action": "publish",
  "zettel_id": "042-email-deliverability",
  "version": "1.0.0",  // Optional semver (default: auto-increment)
  "location": "project"  // Optional: publish from project or user space
}
```

**Behavior**:
- **Create**: Creates markdown file in specified location (default: project)
- **Update**: Updates entry in its current location (resolves location first)
- **Delete**: Deletes entry from its current location
- **Publish**: Uploads entry from project/user space to registry

**Output**:
```json
{
  "status": "success",
  "action": "create",
  "zettel_id": "042-email-deliverability",
  "location": "project",
  "path": ".ai/knowledge/patterns/042-email-deliverability.md"
}
```

### 4. `link` - Manage Relationships & Collections

**Purpose**: Link entries, create collections, manage relationships

**Input** (Link entries):
```json
{
  "action": "link",
  "from_zettel_id": "042-email-deliverability",
  "to_zettel_id": "043-spf-records",
  "relationship_type": "references"  // "references" | "contradicts" | "extends" | "implements" | "supersedes" | "depends_on" | "related" | "example_of"
}
```

**Input** (Create collection):
```json
{
  "action": "create_collection",
  "name": "Email Infrastructure",
  "description": "All entries about email setup",
  "zettel_ids": ["042-email-deliverability", "043-spf-records"],
  "collection_type": "topic"  // "topic" | "project" | "learning_path" | "reference" | "archive"
}
```

**Input** (Get relationships):
```json
{
  "action": "get_relationships",
  "zettel_id": "042-email-deliverability"
}
```

**Behavior**:
- **Link**: Creates relationship between two entries (can be across tiers)
- **Create collection**: Groups related entries
- **Get relationships**: Returns all relationships for an entry

**Output**:
```json
{
  "status": "success",
  "action": "link",
  "relationship": {
    "from_zettel_id": "042-email-deliverability",
    "to_zettel_id": "043-spf-records",
    "relationship_type": "references"
  }
}
```

### 5. `help` - Help and Guidance

**Purpose**: Get workflow guidance and examples

**Input**:
```json
{
  "query": "how to create a knowledge entry",
  "context": "I'm new to Zettelkasten"  // Optional
}
```

**Output**:
```json
{
  "topic": "Creating Knowledge Entries",
  "workflow": [
    "1. Use search() to find similar entries",
    "2. Use manage({'action': 'create', ...}) to create new entry",
    "3. Use link() to connect related entries"
  ],
  "examples": [
    {
      "description": "Create a pattern entry",
      "code": "manage({'action': 'create', 'zettel_id': '042-email-deliverability', 'title': '...', 'content': '...', 'entry_type': 'pattern'})"
    }
  ]
}
```

## Project Structure

```
~/projects/knowledge-kiwi/
├── knowledge_kiwi/
│   ├── api/
│   │   └── knowledge_registry.py      # Supabase client for registry
│   ├── tools/
│   │   ├── search.py                   # Search tool
│   │   ├── get.py                      # Get tool
│   │   ├── manage.py                   # CRUD + publish tool
│   │   ├── link.py                     # Relationships tool
│   │   └── help.py                     # Help tool
│   ├── utils/
│   │   └── knowledge_resolver.py      # 3-tier resolution logic
│   ├── server.py                       # MCP server
│   └── config.py                       # Configuration
├── tests/
│   ├── api/
│   ├── tools/
│   └── utils/
├── docs/
├── .ai/                                # Project space
│   └── knowledge/
│       ├── apis/
│       ├── patterns/
│       ├── concepts/
│       ├── learnings/
│       ├── experiments/
│       ├── references/
│       ├── templates/
│       └── workflows/
├── pyproject.toml
├── .venv/
└── .env.example
```

**User space** (created at runtime):
```
~/.knowledge-kiwi/
├── apis/
├── patterns/
├── concepts/
├── learnings/
├── experiments/
├── references/
├── templates/
└── workflows/
```

## Database Schema (Registry Only)

Supabase `knowledge_entries` table stores entries for the registry tier:

```sql
CREATE TABLE knowledge_entries (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    zettel_id text UNIQUE NOT NULL,
    title text NOT NULL,
    content text NOT NULL,
    entry_type text NOT NULL,
    tags text[] DEFAULT '{}',
    source_type text,
    source_url text,
    version text DEFAULT '1.0.0',  -- Semver versioning
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),
    -- Full-text search
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english', title || ' ' || content)
    ) STORED
);

CREATE INDEX idx_knowledge_search ON knowledge_entries USING GIN(search_vector);
CREATE INDEX idx_knowledge_tags ON knowledge_entries USING GIN(tags);
CREATE INDEX idx_knowledge_zettel_id ON knowledge_entries(zettel_id);
```

**Note**: No embeddings, no RAG complexity. Just full-text search (tsvector).

## Implementation Details

### Knowledge Resolver (Explicit Source Selection)

Different from Script Kiwi's automatic fallback - uses explicit source parameter:

```python
class KnowledgeResolver:
    """Resolve knowledge entries with explicit source selection."""
    
    def resolve_entry(
        self,
        zettel_id: str,
        source: Union[str, List[str]],  # "local" | "registry" | ["local", "registry"]
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Resolve entry with explicit source selection.
        
        Args:
            source: "local" (project + user), "registry" (remote registry), or ["local", "registry"]
        
        Returns:
            {
                "location": "project" | "user" | "registry" | None,
                "path": Path | None,
                "version": str | None
            }
        """
        # Normalize source to list
        sources = [source] if isinstance(source, str) else source
        
        # Check local sources (project → user)
        if "local" in sources:
            # 1. Check project space first
            project_path = self._check_project_space(zettel_id, category)
            if project_path and project_path.exists():
                return {"location": "project", "path": project_path, "version": None}
            
            # 2. Check user space
            user_path = self._check_user_space(zettel_id, category)
            if user_path and user_path.exists():
                return {"location": "user", "path": user_path, "version": None}
        
        # Check registry (only if "registry" in sources and not found locally)
        if "registry" in sources:
            registry_entry = await self._check_registry(zettel_id)
            if registry_entry:
                return {
                    "location": "registry",
                    "path": None,
                    "version": registry_entry.get("version")
                }
        
        return {"location": None, "path": None, "version": None}
    
    def search_entries(
        self,
        query: str,
        source: Union[str, List[str]],
        category: Optional[str] = None,
        entry_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search entries with explicit source selection.
        
        Returns results with source_location for each entry.
        """
        sources = [source] if isinstance(source, str) else source
        results = []
        
        # Search local (project + user)
        if "local" in sources:
            project_results = self._search_project_space(query, category, entry_type, tags, limit)
            user_results = self._search_user_space(query, category, entry_type, tags, limit)
            # Merge and deduplicate (project prioritized)
            results.extend(project_results)
            results.extend([r for r in user_results if r["zettel_id"] not in [p["zettel_id"] for p in project_results]])
        
        # Search registry
        if "registry" in sources:
            registry_results = await self._search_registry(query, category, entry_type, tags, limit)
            results.extend(registry_results)
        
        # Sort by relevance and limit
        results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        return results[:limit]
```

### File Parsing

Parse markdown files with frontmatter:

```python
def parse_knowledge_file(file_path: Path) -> Dict[str, Any]:
    """Parse markdown file with YAML frontmatter."""
    content = file_path.read_text()
    
    # Split frontmatter and content
    if content.startswith("---"):
        parts = content.split("---", 2)
        frontmatter = yaml.safe_load(parts[1])
        body = parts[2].strip()
    else:
        frontmatter = {}
        body = content
    
    return {
        **frontmatter,
        "content": body,
        "path": str(file_path)
    }
```

### Registry API Client

```python
class KnowledgeRegistry:
    """Client for Knowledge Kiwi Supabase registry."""
    
    async def search_entries(
        self,
        query: str,
        category: Optional[str] = None,
        entry_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search entries in registry using full-text search."""
        # Use tsvector search
        pass
    
    async def get_entry(self, zettel_id: str) -> Optional[Dict[str, Any]]:
        """Get entry from registry."""
        pass
    
    async def publish_entry(
        self,
        zettel_id: str,
        entry_data: Dict[str, Any],
        version: Optional[str] = None
    ) -> Dict[str, Any]:
        """Publish entry to registry."""
        pass
```

## Workstreams

1. **Schema & Infrastructure**
   - Create Supabase schema (knowledge_entries table)
   - Full-text search indexes (tsvector)
   - No embeddings/RAG (removed from scope)

2. **Knowledge Resolver**
   - Implement explicit source selection logic (`source: "local"` | `"registry"` | `["local", "registry"]`)
   - File system scanning (project + user space for local)
   - Registry integration (for db source)
   - Source location reporting in responses

3. **File Format & Parsing**
   - Markdown with YAML frontmatter parser
   - File writer (create/update entries)
   - Category-based file organization

4. **MCP Tools Implementation**
   - `search`: Multi-tier search with ranking
   - `get`: Entry retrieval with relationships
   - `manage`: CRUD + publish operations
   - `link`: Relationship management
   - `help`: Workflow guidance

5. **Registry API Client**
   - Supabase client for knowledge_entries
   - Full-text search queries
   - Publish/download operations

6. **Testing**
   - Unit tests for resolver logic
   - Integration tests for 3-tier resolution
   - File parsing tests
   - Registry API tests

7. **Documentation**
   - README with usage examples
   - Tool documentation
   - Migration guide from old structure

## Migration from Current State

### Current Structure
- `knowledge/base/` with SQL-based sync
- 9 individual tools
- Bidirectional sync complexity

### Migration Steps

1. **Create new structure**
   - Set up `.ai/knowledge/` directories
   - Create `~/.knowledge-kiwi/` structure

2. **Migrate existing entries**
   - Convert existing `knowledge/base/` files to new format
   - Preserve zettel_id, metadata
   - Organize by category

3. **Update tools**
   - Replace 9 tools with 5 core tools
   - Implement 3-tier resolution
   - Remove sync complexity

4. **Update directives**
   - Update Context Kiwi directives to use new tools
   - Update tool references in workflows

## Dependencies

- **Supabase**: Registry storage and search
- **Context Kiwi**: Directives reference Knowledge Kiwi tools
- **No RAG dependencies**: Removed embeddings/vector search complexity

## Benefits

1. **Explicit Control**: Explicit `source` parameter prevents unexpected network calls - user chooses local vs. remote
2. **Clear Separation**: Local knowledge (fast, offline) vs. remote registry (shared, versioned) are distinct
3. **Transparency**: Always know where knowledge came from (`source_location` in responses)
4. **Simplicity**: Plain files, no SQL sync complexity
5. **Scalability**: Easy to add new categories/types
6. **Portability**: Knowledge entries are just markdown files
7. **Version Control**: Git-friendly (project space tracked)
8. **No RAG Complexity**: Removed embeddings/vector search
9. **Offline-First**: Can work entirely with local knowledge without registry access

## Risks & Mitigations

- **File format migration**: Provide migration script
- **Tool API changes**: Update directives in Context Kiwi
- **Registry search quality**: Full-text search may be less accurate than embeddings (acceptable trade-off for simplicity)
- **Explicit source requirement**: Users must specify `source` parameter (unlike Script Kiwi's automatic fallback) - **Mitigation**: Clear error messages, help tool guidance, default to `"local"` in examples
- **Design difference from Script Kiwi**: Knowledge Kiwi uses explicit source selection vs. Script Kiwi's automatic fallback - **This is intentional**: Knowledge entries are often large, and users should control when to hit the network

## Acceptance Criteria

- [ ] Explicit source selection works: `source: "local"` checks project → user, `source: "registry"` checks registry
- [ ] `search` with `source: "local"` finds entries in project and user space, reports `source_location`
- [ ] `search` with `source: "registry"` searches registry only
- [ ] `search` with `source: ["local", "registry"]` searches both, prioritizes local results
- [ ] `get` with `source: "local"` resolves project → user, reports where found
- [ ] `get` with `source: "registry"` fetches from registry only
- [ ] `get` with `source: ["local", "registry"]` checks local first, falls back to registry if not found
- [ ] `manage` creates/updates/deletes in appropriate tier
- [ ] `publish` uploads entries from local to registry
- [ ] `link` creates relationships (can reference entries across tiers)
- [ ] File format is plain markdown with frontmatter
- [ ] No RAG/embeddings complexity
- [ ] No automatic fallback to registry (explicit `source` parameter required)

## Next Steps

1. Review and approve this plan
2. Create Supabase schema (simplified, no embeddings)
3. Implement knowledge resolver
4. Implement 5 core tools
5. Test 3-tier resolution
6. Migrate existing knowledge entries
7. Update Context Kiwi directives

