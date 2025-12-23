#!/usr/bin/env python3
"""
Knowledge Kiwi MCP Server

Knowledge base MCP server with Zettelkasten support.
Provides 5 core tools: search, get, manage, link, help.
"""

import asyncio
import time
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .tools.search import SearchTool
from .tools.get import GetTool
from .tools.manage import ManageTool
from .tools.link import LinkTool
from .tools.help import HelpTool
from .utils.analytics import log_tool_execution


class KnowledgeKiwiMCP:
    """Knowledge base MCP server with Zettelkasten support"""
    
    def __init__(self):
        self.server = Server("knowledge-kiwi-mcp")
        self.setup_tools()
    
    def setup_tools(self):
        """Register knowledge management tools"""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="search",
                    description="Search knowledge entries using natural language search. Supports multi-term matching where all terms must appear. Use when: finding entries by keywords, filtering by category/type/tags, or searching both local and remote sources.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query - natural language search supporting multiple terms. Examples: 'email deliverability', 'JWT authentication', 'React patterns'. All terms must match for best results."
                            },
                            "source": {
                                "type": ["string", "array"],
                                "description": "Where to search. 'local' = project + user space (offline), 'registry' = Supabase (online), ['local', 'registry'] = both. Default: 'local'",
                                "enum": ["local", "registry"],
                                "default": "local"
                            },
                            "category": {
                                "type": "string",
                                "description": "Filter by category path. Example: 'email-infrastructure/smtp' or 'patterns'. Optional."
                            },
                            "entry_type": {
                                "type": "string",
                                "enum": ["api_fact", "pattern", "concept", "learning", "experiment", "reference", "template", "workflow"],
                                "description": "Filter by entry type. Optional."
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Filter by tags. Must match all tags. Example: ['email', 'smtp']. Optional."
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Max results to return. Default: 10",
                                "default": 10
                            }
                        },
                        "required": ["query", "source"]
                    }
                ),
                Tool(
                    name="get",
                    description="Retrieve a specific knowledge entry by zettel_id. Use when: you know the exact entry ID, need full content/details, or want to download from registry to local. Returns: title, content, metadata, optional relationships.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "zettel_id": {
                                "type": "string",
                                "description": "Entry identifier (format: '042-email-deliverability' or similar). Required."
                            },
                            "source": {
                                "type": ["string", "array"],
                                "description": "Where to get from. 'local' = project/user space, 'registry' = Supabase, ['local', 'registry'] = try local first, then registry. Default: 'local'",
                                "enum": ["local", "registry"],
                                "default": "local"
                            },
                            "include_relationships": {
                                "type": "boolean",
                                "description": "Include linked entries (outgoing relationships). Default: false",
                                "default": False
                            },
                            "include_backlinks": {
                                "type": "boolean",
                                "description": "Include entries that link to this one (incoming relationships). Default: false",
                                "default": False
                            },
                            "destination": {
                                "type": ["string", "array"],
                                "description": "ONLY when source='registry': Download to 'user' (~/.knowledge-kiwi), 'project' (.ai/knowledge), or both. Ignored for local source.",
                                "enum": ["user", "project"]
                            }
                        },
                        "required": ["zettel_id", "source"]
                    }
                ),
                Tool(
                    name="manage",
                    description="Create, update, delete, or publish knowledge entries. Use: create=new entry, update=modify existing, delete=remove entry, publish=upload local entry to registry. Each action has different required parameters.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": ["create", "update", "delete", "publish"],
                                "description": "Operation: 'create'=new entry, 'update'=modify, 'delete'=remove, 'publish'=upload to registry. Required."
                            },
                            "zettel_id": {
                                "type": "string",
                                "description": "Entry identifier (format: '042-email-deliverability'). Required for all actions."
                            },
                            "title": {
                                "type": "string",
                                "description": "Entry title. Required for 'create', optional for 'update'. Ignored for 'delete'/'publish'."
                            },
                            "content": {
                                "type": "string",
                                "description": "Markdown content. Required for 'create', optional for 'update'. Ignored for 'delete'/'publish'."
                            },
                            "entry_type": {
                                "type": "string",
                                "enum": ["api_fact", "pattern", "concept", "learning", "experiment", "reference", "template", "workflow"],
                                "description": "Entry type. Required for 'create' only. Ignored for other actions."
                            },
                            "category": {
                                "type": "string",
                                "description": "Category path for organization (e.g., 'email-infrastructure/smtp' or 'patterns'). Optional for 'create'/'update'. Creates nested folders. Ignored for 'delete'/'publish'."
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Tags array. Optional for 'create'/'update'. Example: ['email', 'smtp']. Ignored for 'delete'/'publish'."
                            },
                            "source_type": {
                                "type": "string",
                                "description": "Source origin: 'youtube', 'docs', 'experiment', 'manual', 'chat', 'book', 'article', 'course'. Optional for 'create'/'update'."
                            },
                            "source_url": {
                                "type": "string",
                                "description": "URL of source material. Optional for 'create'/'update'."
                            },
                            "location": {
                                "type": ["string", "array"],
                                "description": "For 'create': 'project' (.ai/knowledge) or 'user' (~/.knowledge-kiwi). Default: 'project'. For 'delete': 'project' | 'user' | ['project', 'user']. Ignored for 'update'/'publish'.",
                                "enum": ["project", "user"]
                            },
                            "source": {
                                "type": ["string", "array"],
                                "description": "ONLY for 'delete': 'local' (project+user), 'registry' (Supabase), or ['local', 'registry'] (both). Default: 'local'. Ignored for other actions.",
                                "enum": ["local", "registry"]
                            },
                            "cascade_relationships": {
                                "type": "boolean",
                                "description": "ONLY for 'delete' with source='registry': If true, deletes relationships first. Default: false. Ignored for other actions.",
                                "default": False
                            },
                            "confirm": {
                                "type": "boolean",
                                "description": "ONLY for 'delete': Must be true to confirm deletion. Required for safety. Ignored for other actions.",
                                "default": False
                            },
                            "version": {
                                "type": "string",
                                "description": "ONLY for 'publish': Version string (e.g., '1.0.0'). Optional, auto-increments if omitted. Ignored for other actions."
                            }
                        },
                        "required": ["action", "zettel_id"]
                    }
                ),
                Tool(
                    name="link",
                    description="Link entries together or create collections. Use: 'link'=connect two entries, 'create_collection'=group entries, 'get_relationships'=view links. Relationships stored in registry only.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": ["link", "create_collection", "get_relationships"],
                                "description": "Operation: 'link'=connect entries, 'create_collection'=group entries, 'get_relationships'=view links. Required."
                            },
                            "from_zettel_id": {
                                "type": "string",
                                "description": "ONLY for 'link': Source entry ID. Required for 'link', ignored otherwise."
                            },
                            "to_zettel_id": {
                                "type": "string",
                                "description": "ONLY for 'link': Target entry ID. Required for 'link', ignored otherwise."
                            },
                            "relationship_type": {
                                "type": "string",
                                "enum": ["references", "contradicts", "extends", "implements", "supersedes", "depends_on", "related", "example_of"],
                                "description": "ONLY for 'link': Relationship type. 'references'=most common. Required for 'link', ignored otherwise."
                            },
                            "name": {
                                "type": "string",
                                "description": "ONLY for 'create_collection': Collection name. Required for 'create_collection', ignored otherwise."
                            },
                            "description": {
                                "type": "string",
                                "description": "ONLY for 'create_collection': Collection description. Optional, ignored otherwise."
                            },
                            "zettel_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "ONLY for 'create_collection': Array of entry IDs to include. Required for 'create_collection', ignored otherwise."
                            },
                            "collection_type": {
                                "type": "string",
                                "enum": ["topic", "project", "learning_path", "reference", "archive"],
                                "description": "ONLY for 'create_collection': Collection type. Default: 'topic'. Ignored otherwise.",
                                "default": "topic"
                            },
                            "zettel_id": {
                                "type": "string",
                                "description": "ONLY for 'get_relationships': Entry ID to query. Required for 'get_relationships', ignored otherwise."
                            }
                        },
                        "required": ["action"]
                    }
                ),
                Tool(
                    name="help",
                    description="Get usage guidance, examples, and best practices. Use when: unsure how to use a tool, need examples, or want workflow guidance. Query examples: 'create entry', 'search', 'delete', 'link entries'.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "What you need help with. Examples: 'how to create an entry', 'searching knowledge', 'delete entries', 'link relationships'. Required."
                            },
                            "context": {
                                "type": "string",
                                "description": "Additional context about your situation. Optional."
                            }
                        },
                        "required": ["query"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            """Handle tool execution."""
            start_time = time.time()
            status = "success"
            error = None
            result = None
            project_path = None
            
            try:
                try:
                    project_path = str(Path.cwd())
                except:
                    pass
                
                if name == "search":
                    tool = SearchTool()
                    result = await tool.execute(arguments)
                elif name == "get":
                    tool = GetTool()
                    result = await tool.execute(arguments)
                elif name == "manage":
                    tool = ManageTool()
                    result = await tool.execute(arguments)
                elif name == "link":
                    tool = LinkTool()
                    result = await tool.execute(arguments)
                elif name == "help":
                    tool = HelpTool()
                    result = await tool.execute(arguments)
                else:
                    error = f"Unknown tool: {name}"
                    status = "error"
                    return [TextContent(
                        type="text",
                        text=f'{{"error": "{error}"}}'
                    )]
                
                metadata = {}
                try:
                    result_data = json.loads(result)
                    if isinstance(result_data, dict):
                        metadata = {
                            "zettel_id": result_data.get("zettel_id"),
                            "action": result_data.get("action"),
                            "source": arguments.get("source"),
                            "category": arguments.get("category") or result_data.get("category"),
                        }
                        metadata = {k: v for k, v in metadata.items() if v is not None}
                except:
                    pass
                
                return [TextContent(type="text", text=result)]
                
            except Exception as e:
                import traceback
                status = "error"
                error = str(e)
                error_msg = {
                    "error": error,
                    "traceback": traceback.format_exc()
                }
                result = json.dumps(error_msg, indent=2)
                return [TextContent(
                    type="text",
                    text=result
                )]
            finally:
                duration_sec = time.time() - start_time
                try:
                    outputs = None
                    try:
                        if result:
                            outputs = json.loads(result)
                    except:
                        outputs = {"result_length": len(result) if result else 0}
                    
                    log_tool_execution(
                        tool_name=name,
                        status=status,
                        duration_sec=duration_sec,
                        inputs=arguments,
                        project=project_path,
                        outputs=outputs,
                        error=error,
                        metadata=metadata
                    )
                except Exception:
                    pass
    
    async def run(self):
        """Start the MCP server"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


def main():
    """Entry point for the MCP server"""
    server = KnowledgeKiwiMCP()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
