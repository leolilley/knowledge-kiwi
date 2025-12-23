"""Get tool for Knowledge Kiwi."""

import json
from typing import Dict, Any, Optional, Union, List
from pathlib import Path

from ..api.knowledge_registry import KnowledgeRegistry
from ..utils.knowledge_resolver import KnowledgeResolver, parse_knowledge_file, write_knowledge_file


class GetTool:
    """Get knowledge entry with explicit source selection."""
    
    def __init__(self):
        self.resolver = KnowledgeResolver()
        self.registry = KnowledgeRegistry()
    
    async def execute(self, arguments: Dict[str, Any]) -> str:
        """
        Get a knowledge entry.
        
        Args:
            zettel_id: Unique identifier
            source: "local" | "registry" | ["local", "registry"]
            include_relationships: Include linked entries (default: false)
            include_backlinks: Include entries that link to this (default: false)
            destination: Download from registry to "user" | "project" | ["user", "project"] (default: None)
        
        Returns:
            JSON string with entry details
        """
        try:
            zettel_id = arguments.get("zettel_id")
            source = arguments.get("source", "local")
            include_relationships = arguments.get("include_relationships", False)
            include_backlinks = arguments.get("include_backlinks", False)
            destination = arguments.get("destination")
            
            # Normalize destination to list
            download_destinations = []
            if destination:
                if isinstance(destination, str):
                    download_destinations = [destination]
                elif isinstance(destination, list):
                    download_destinations = destination
            
            if not zettel_id:
                return json.dumps({
                    "error": "zettel_id is required"
                })
            
            # Normalize source
            sources = [source] if isinstance(source, str) else source
            
            entry_data = None
            source_location = None
            
            # Check local first (if source includes local)
            if "local" in sources:
                resolution = self.resolver.resolve_entry(zettel_id, "local")
                
                if resolution["location"]:
                    file_path = Path(resolution["path"])
                    entry_data = parse_knowledge_file(file_path)
                    source_location = resolution["location"]
            
            # Check registry (if not found locally or source is registry-only)
            if not entry_data and "registry" in sources:
                registry_entry = await self.registry.get_entry(zettel_id)
                
                if registry_entry:
                    entry_data = registry_entry
                    source_location = "registry"
                    
                    # Determine category
                    category = registry_entry.get("category")
                    if not category:
                        entry_type = registry_entry.get("entry_type", "learning")
                        category = entry_type + "s" if not entry_type.endswith("s") else entry_type
                    
                    downloaded_locations = []
                    
                    # Download to requested destinations
                    for destination in download_destinations:
                        if destination == "user":
                            user_dir = Path.home() / ".knowledge-kiwi"
                            category_dir = user_dir / category
                            category_dir.mkdir(parents=True, exist_ok=True)
                            
                            file_path = category_dir / f"{zettel_id}.md"
                            write_knowledge_file(
                                file_path=file_path,
                                zettel_id=zettel_id,
                                title=registry_entry["title"],
                                content=registry_entry["content"],
                                entry_type=registry_entry.get("entry_type", "learning"),
                                category=category,
                                tags=registry_entry.get("tags"),
                                source_type=registry_entry.get("source_type"),
                                source_url=registry_entry.get("source_url")
                            )
                            downloaded_locations.append(f"~/.knowledge-kiwi/{category}/{zettel_id}.md")
                        
                        elif destination == "project":
                            project_dir = self.resolver.project_knowledge_dir
                            category_dir = project_dir / category
                            category_dir.mkdir(parents=True, exist_ok=True)
                            
                            file_path = category_dir / f"{zettel_id}.md"
                            write_knowledge_file(
                                file_path=file_path,
                                zettel_id=zettel_id,
                                title=registry_entry["title"],
                                content=registry_entry["content"],
                                entry_type=registry_entry.get("entry_type", "learning"),
                                category=category,
                                tags=registry_entry.get("tags"),
                                source_type=registry_entry.get("source_type"),
                                source_url=registry_entry.get("source_url")
                            )
                            # Use relative path for display (try relative to project root, fallback to absolute)
                            try:
                                rel_path = file_path.relative_to(self.resolver.project_root)
                                downloaded_locations.append(str(rel_path))
                            except ValueError:
                                # File is not under project_root (e.g., in tests), use absolute path
                                downloaded_locations.append(str(file_path))
            
            if not entry_data:
                return json.dumps({
                    "error": f"Entry '{zettel_id}' not found in specified source(s)"
                })
            
            result = {
                "zettel_id": entry_data.get("zettel_id"),
                "title": entry_data.get("title"),
                "content": entry_data.get("content"),
                "entry_type": entry_data.get("entry_type"),
                "category": entry_data.get("category"),  # Include category
                "tags": entry_data.get("tags", []),
                "source_location": source_location
            }
            
            # Add relationships if requested (requires registry access)
            if include_relationships or include_backlinks:
                if "registry" in sources:
                    relationships = await self.registry.get_relationships(zettel_id)
                    
                    if include_relationships:
                        result["relationships"] = [
                            {
                                "zettel_id": rel["zettel_id"],
                                "relationship_type": rel["relationship_type"],
                                "direction": "outgoing"
                            }
                            for rel in relationships.get("outgoing", [])
                        ]
                    
                    if include_backlinks:
                        result["backlinks"] = [
                            {
                                "zettel_id": rel["zettel_id"],
                                "relationship_type": rel["relationship_type"],
                                "direction": "incoming"
                            }
                            for rel in relationships.get("incoming", [])
                        ]
            
            # Add download information if entry was downloaded
            if source_location == "registry" and downloaded_locations:
                if len(downloaded_locations) == 1:
                    result["downloaded_to"] = downloaded_locations[0]
                else:
                    result["downloaded_to"] = downloaded_locations
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return json.dumps({
                "error": str(e)
            })

