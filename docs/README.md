# Knowledge Kiwi Documentation

This folder contains all documentation for Knowledge Kiwi.

## Structure

- `guides/` - Detailed guides and specifications
- `examples/` - Example knowledge entries and usage patterns
- `*.sql` - Database schemas

## Key Documents

### Getting Started
- **Setup-Guide.md** - Initial setup instructions (Supabase, environment, dependencies)

### Core Concepts
- **Knowledge-Kiwi-Redesign-Plan.md** - Complete redesign plan (5 tools, 3-tier storage, explicit source selection)
- **Knowledge-Kiwi-Workflow-Examples.md** - 10 practical workflow examples

### Integration
- **Directive-Orchestration-Pattern.md** - How Context Kiwi directives use Knowledge Kiwi
- **Sample-Directive-Example.md** - Example directive XML

### Database
- **knowledge-kiwi-schema-redesigned.sql** - Complete database schema for Supabase

## Quick Links

- [Redesign Plan](guides/Knowledge-Kiwi-Redesign-Plan.md)
- [Workflow Examples](guides/Knowledge-Kiwi-Workflow-Examples.md)
- [Setup Guide](guides/Setup-Guide.md)

## Key Features

- **5 Core Tools**: `search`, `get`, `manage`, `link`, `help`
- **3-Tier Storage**: Project (`.ai/knowledge/`) → User (`~/.knowledge-kiwi/`) → Registry (Supabase)
- **Explicit Source Selection**: Tools require `source` parameter (`"local"` | `"registry"` | `["local", "registry"]`)
- **Plain Markdown Files**: Knowledge entries are markdown with YAML frontmatter (no SQL sync complexity)
- **Execution Logging**: All tool executions logged to `~/.knowledge-kiwi/.runs/history.jsonl` with analytics support

