"""Search tool for Knowledge Kiwi."""

import json
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from ..api.knowledge_registry import KnowledgeRegistry
from ..utils.knowledge_resolver import KnowledgeResolver


class SearchTool:
    """Search knowledge entries with explicit source selection."""
    
    def __init__(self):
        self.resolver = KnowledgeResolver()
        self.registry = KnowledgeRegistry()
    
    async def execute(self, arguments: Dict[str, Any]) -> str:
        """
        Search knowledge entries.
        
        Args:
            query: Search query string
            source: "local" | "registry" | ["local", "registry"]
            category: Optional category filter
            entry_type: Optional entry type filter
            tags: Optional tags filter
            limit: Maximum results (default: 10)
        
        Returns:
            JSON string with search results
        """
        try:
            query = arguments.get("query", "")
            source = arguments.get("source", "local")
            category = arguments.get("category")
            entry_type = arguments.get("entry_type")
            tags = arguments.get("tags")
            limit = arguments.get("limit", 10)
            
            if not query:
                return json.dumps({
                    "error": "query is required"
                })
            
            # Normalize source
            sources = [source] if isinstance(source, str) else source
            
            results = []
            
            # Search local (project + user space)
            if "local" in sources:
                local_results = self.resolver.search_local(
                    query=query,
                    category=category,
                    entry_type=entry_type,
                    tags=tags,
                    limit=limit
                )
                results.extend(local_results)
            
            # Search registry
            if "registry" in sources:
                registry_results = await self.registry.search_entries(
                    query=query,
                    category=category,
                    entry_type=entry_type,
                    tags=tags,
                    limit=limit
                )
                results.extend(registry_results)
            
            # Sort by relevance (local results already prioritized by resolver)
            results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
            results = results[:limit]
            
            return json.dumps({
                "query": query,
                "source": source,
                "results_count": len(results),
                "results": results
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                "error": str(e)
            })

