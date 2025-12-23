# Setup Guide - Script Kiwi & Knowledge Kiwi

## Step 1: Create Supabase Projects

### Manual Steps (via supabase.com)

1. **Script Kiwi Project**
   - Go to https://supabase.com/dashboard
   - Click "New Project"
   - Name: `script-kiwi`
   - Region: Choose closest to you
   - Database Password: Generate and save securely
   - Wait for project to initialize (~2 minutes)
   - **Save these values:**
     - Project URL: `https://xxxxx.supabase.co`
     - Anon Key: `eyJhbGc...`

2. **Knowledge Kiwi Project**
   - Same process as above
   - Name: `knowledge-kiwi`
   - **Save these values:**
     - Project URL: `https://xxxxx.supabase.co`
     - Anon Key: `eyJhbGc...`

### After Creation

Update `.env` files in each project with:
```bash
SCRIPT_KIWI_SUPABASE_URL=https://xxxxx.supabase.co
SCRIPT_KIWI_SUPABASE_KEY=your-anon-key

SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SECRET_KEY=your-secret-key  # For write/publish access
SUPABASE_ANON_KEY=your-anon-key      # For read-only access (fallback)
```

## Step 2: Run Database Schemas

### Script Kiwi Schema

1. Go to Script Kiwi project → SQL Editor
2. Copy contents from `v2/schemas/script-kiwi-schema.sql`
3. Run the SQL script
4. Verify tables created: `scripts`, `script_versions`, `executions`, `lockfiles`, `script_feedback`

### Knowledge Kiwi Schema

1. Go to Knowledge Kiwi project → SQL Editor
2. Copy contents from `docs/knowledge-kiwi-schema-redesigned.sql`
3. Run the SQL script
4. Verify tables created: `knowledge_entries`, `knowledge_relationships`, `knowledge_collections`
5. Verify function created: `search_knowledge_fulltext`

## Step 3: Verify Setup

Test the MCP server:
```bash
# Knowledge Kiwi
cd ~/projects/knowledge-kiwi-v2
source .venv/bin/activate
python -m knowledge_kiwi.server
# Should start without errors (will wait for stdio input)
```

### Execution Logging

All tool executions are automatically logged to `~/.knowledge-kiwi/.runs/history.jsonl`. This includes:
- Tool name, status, duration
- Input parameters (summarized)
- Output summaries
- Error messages (if any)
- Metadata (zettel_id, action, source, category)

Query execution history:
```python
from knowledge_kiwi.utils.analytics import get_execution_history, tool_stats

# Get recent executions
history = get_execution_history(days=7)

# Get tool performance stats
stats = tool_stats(days=30)
```

## Step 4: Connect to MCP Client

### For Cursor
Add to `~/.config/cursor/mcp.json`:
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

**Note**: Update the path to match your actual project location!

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

### For Claude Desktop
Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%/Claude/claude_desktop_config.json` (Windows)

Restart Cursor/Claude Desktop after adding the configuration.

## Next Steps

After setup is complete:
- ✅ Database schema deployed
- ✅ Environment variables configured
- ✅ MCP server tested
- 🔲 Connect to MCP client (Cursor/Claude Desktop)
- 🔲 Create your first knowledge entry
