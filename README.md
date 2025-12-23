# Knowledge Kiwi MCP

Knowledge base MCP server with Zettelkasten support and 3-tier storage.

## Overview

Knowledge Kiwi provides a personal knowledge base system using plain markdown files stored across three tiers: **Project Space** (`.ai/knowledge/`), **User Space** (`~/.knowledge-kiwi/`), and **Registry** (Supabase). Supports explicit source selection for offline-first workflows.

## Features

- **5 Core Tools**: `search`, `get`, `manage`, `link`, `help`
- **3-Tier Storage**: Project → User → Registry (explicit source selection)
- **Plain Markdown Files**: No SQL sync complexity, Git-friendly
- **Offline-First**: Work entirely with local knowledge when offline
- **Explicit Source Selection**: Choose `source: "local"` or `source: "registry"` explicitly
- **Zettelkasten Support**: Unique zettel_id system with relationships
- **Full-Text Search**: tsvector-based search (no RAG/embeddings complexity)
- **Execution Logging**: All tool executions logged to `~/.knowledge-kiwi/.runs/history.jsonl`

## Setup

1. **Create Supabase Project**
   - Create new project at supabase.com
   - Save project URL and API keys

2. **Run Database Schema**
   ```bash
   # Copy SQL from docs/knowledge-kiwi-schema-redesigned.sql
   # Run in Supabase SQL Editor
   # Note: No embeddings/RAG - just full-text search (tsvector)
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Fill in your Supabase credentials
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_SECRET_KEY=your-secret-key  # For write/publish access
   SUPABASE_ANON_KEY=your-anon-key      # For read-only access (fallback)
   ```

4. **Install Dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```

5. **Test MCP Server**
   ```bash
   python -m knowledge_kiwi.server
   ```

6. **Connect to Cursor/Claude Desktop**
   
   Add to your MCP configuration file (`~/.config/cursor/mcp.json`):
   
   ```json
   {
     "mcpServers": {
       "knowledge-kiwi": {
         "command": "/home/leo/projects/knowledge-kiwi-v2/.venv/bin/knowledge-kiwi",
         "cwd": "/home/leo/projects/knowledge-kiwi-v2",
         "env": {
          "SUPABASE_URL": "https://your-project.supabase.co",
          "SUPABASE_SECRET_KEY": "your-secret-key",
          "SUPABASE_ANON_KEY": "your-anon-key"
         }
       }
     }
   }
   ```
   
   **Important**: Update the path to match your actual project location!
   
   Alternative (using python module):
   ```json
   {
     "mcpServers": {
       "knowledge-kiwi": {
         "command": "python3",
         "args": ["-m", "knowledge_kiwi.server"],
         "cwd": "/home/leo/projects/knowledge-kiwi-v2",
         "env": {
          "SUPABASE_URL": "https://your-project.supabase.co",
          "SUPABASE_SECRET_KEY": "your-secret-key",
          "SUPABASE_ANON_KEY": "your-anon-key"
         }
       }
     }
   }
   ```
   
   Or use the provided `example.mcp.json` as a template.

## Project Structure

```
knowledge-kiwi-v2/
├── knowledge_kiwi/
│   ├── api/                # Supabase API client for registry
│   ├── tools/              # MCP tools (search, get, manage, link, help)
│   ├── utils/              # Knowledge resolver, logger, analytics
│   └── server.py           # MCP server
├── .ai/knowledge/          # Project space (created at runtime)
│   ├── apis/
│   ├── patterns/
│   ├── concepts/
│   ├── learnings/
│   ├── experiments/
│   ├── references/
│   ├── templates/
│   └── workflows/
├── ~/.knowledge-kiwi/      # User space (created at runtime)
│   ├── [same structure as .ai/knowledge/]
│   └── .runs/history.jsonl  # Tool execution logs
├── tests/
└── docs/
```

## 5 Core Tools

### 1. `search` - Search Knowledge Entries

Search across local (project + user) or registry with explicit source selection.

**Example:**
```json
{
  "query": "email deliverability",
  "source": "local",  // "local" | "registry" | ["local", "registry"]
  "category": "email-infrastructure",  // Optional: filter by category
  "limit": 10
}
```

### 2. `get` - Get Entry Details

Get a specific entry with relationships and context. Explicit source selection required.

**Example:**
```json
{
  "zettel_id": "042-email-deliverability",
  "source": "local",  // "local" | "registry" | ["local", "registry"]
  "destination": "user"  // Optional: download from registry to "user" | "project" | ["user", "project"]
}
```

### 3. `manage` - Unified CRUD Operations

Create, update, delete, and publish knowledge entries.

**Create:**
```json
{
  "action": "create",
  "zettel_id": "042-email-deliverability",
  "title": "Email Deliverability Best Practices",
  "content": "# ...",
  "entry_type": "pattern",
  "category": "email-infrastructure/smtp",  // Optional: custom category path
  "location": "project"  // "project" | "user"
}
```

**Update:**
```json
{
  "action": "update",
  "zettel_id": "042-email-deliverability",
  "content": "Updated content..."
}
```

**Delete:**
```json
{
  "action": "delete",
  "zettel_id": "042-email-deliverability",
  "source": "local",  // "local" | "registry" | ["local", "registry"]
  "location": "project",  // Optional: "project" | "user" | ["project", "user"] (for local)
  "cascade_relationships": false,  // Optional: delete relationships too (for registry)
  "confirm": true  // Required
}
```

**Publish:**
```json
{
  "action": "publish",
  "zettel_id": "042-email-deliverability",
  "location": "project"
}
```

### 4. `link` - Manage Relationships & Collections

Link entries and create collections.

**Link entries:**
```json
{
  "action": "link",
  "from_zettel_id": "042-email-deliverability",
  "to_zettel_id": "043-spf-records",
  "relationship_type": "references"
}
```

**Create collection:**
```json
{
  "action": "create_collection",
  "name": "Email Infrastructure",
  "zettel_ids": ["042-email-deliverability", "043-spf-records"]
}
```

### 5. `help` - Help and Guidance

Get workflow guidance and examples.

**Example:**
```json
{
  "query": "how to create a knowledge entry"
}
```

## Storage Tiers

### 1. Project Space (`.ai/knowledge/`)
- **Purpose**: Project-specific knowledge entries
- **Priority**: Highest (checked first when `source: "local"`)
- **Use case**: Project-specific learnings, not shared
- **Format**: Plain markdown files with YAML frontmatter

### 2. User Space (`~/.knowledge-kiwi/`)
- **Purpose**: Personal knowledge library, downloaded from registry
- **Priority**: Second (checked if not in project)
- **Use case**: Personal knowledge, available across all projects
- **Format**: Plain markdown files with YAML frontmatter
- **Execution Logging**: All tool executions are automatically logged to `~/.knowledge-kiwi/.runs/history.jsonl`

**Logging Details:**
- Tool name (search, get, manage, link, help)
- Execution status (success, error)
- Duration
- Input parameters (summarized)
- Output summary
- Error messages (if any)
- Metadata (zettel_id, action, source, category, etc.)

**Query Logs:**
```python
from knowledge_kiwi.utils.analytics import get_execution_history, tool_stats

# Get recent executions
history = get_execution_history(days=7)

# Get tool performance stats
stats = tool_stats(days=30)
```

### 3. Registry (Supabase `knowledge_entries` table)
- **Purpose**: Remote knowledge base (searchable, shareable)
- **Use case**: Shared knowledge, versioned entries
- **Format**: Stored in database, can be downloaded as markdown files

## Explicit Source Selection

Unlike Script Kiwi's automatic fallback, Knowledge Kiwi requires explicit source selection:

- `source: "local"` - Checks project → user space (works offline)
- `source: "registry"` - Checks registry only (requires network)
- `source: ["local", "registry"]` - Checks both, local prioritized

**Why explicit?** Prevents unexpected network calls and makes it clear where knowledge comes from.

## File Format

Knowledge entries are plain markdown files with YAML frontmatter:

```markdown
---
zettel_id: 042-email-deliverability
title: Email Deliverability Best Practices
entry_type: pattern
category: email-infrastructure/smtp  # Optional: custom category path
tags: [email, deliverability, infrastructure]
source_type: experiment
source_url: https://example.com
created_at: 2025-01-15T10:00:00Z
updated_at: 2025-01-15T10:00:00Z
---

# Email Deliverability Best Practices

Content here...
```

## Workflow Examples

See `v2/Knowledge-Kiwi-Workflow-Examples.md` for complete workflow examples showing:
- Creating knowledge entries
- Searching local vs registry
- Linking related entries
- Publishing to registry
- Offline-first workflows
- Integration with Script Kiwi

## Design Notes

- **No Bidirectional Sync**: Removed sync complexity - entries are plain files
- **No RAG/Embeddings**: Removed from scope for simplicity (full-text search only)
- **Explicit Source Selection**: User chooses local vs registry explicitly
- **Offline-First**: Can work entirely with local knowledge
- **Dynamic Categories**: Support for custom category paths (e.g., `email-infrastructure/smtp`)
- **Execution Logging**: All tool executions logged for analytics and debugging

## Status

✅ **Ready for Use** - All 5 core tools implemented and tested. Database schema deployed. Ready to connect to Cursor/Claude Desktop.

## Quick Start

1. ✅ Database schema deployed (Agent Kiwi Supabase project)
2. ✅ Environment configured (`.env` file)
3. ✅ Dependencies installed
4. ✅ Tests passing
5. 🔲 **Connect to MCP client** - Add to your MCP config (see Setup step 6)
6. 🔲 **Create your first entry** - Use `manage` tool with `action: "create"`
