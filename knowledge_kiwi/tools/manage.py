"""Manage tool for Knowledge Kiwi (CRUD + publish operations)."""

import json
from typing import Dict, Any, Optional, List
from pathlib import Path

from ..api.knowledge_registry import KnowledgeRegistry
from ..utils.knowledge_resolver import KnowledgeResolver, parse_knowledge_file, write_knowledge_file


class ManageTool:
    """Unified CRUD operations and publishing."""
    
    def __init__(self):
        self.resolver = KnowledgeResolver()
        self.registry = KnowledgeRegistry()
    
    async def execute(self, arguments: Dict[str, Any]) -> str:
        """
        Manage knowledge entries (create, update, delete, publish).
        
        Args:
            action: "create" | "update" | "delete" | "publish"
            zettel_id: Unique identifier (required for all actions)
            title: Entry title (create/update)
            content: Entry content (create/update)
            entry_type: Type of entry (create)
            category: Optional category path (create, e.g., "email-infrastructure/smtp")
            tags: Tags array (create/update)
            source_type: Source type (create/update)
            source_url: Source URL (create/update)
            location: "project" | "user" (create, default: "project")
            source: "local" | "registry" | ["local", "registry"] (delete, default: "local")
            location: "project" | "user" | ["project", "user"] (delete, optional, for local source)
            cascade_relationships: true (delete from registry, optional)
            confirm: true (delete, required)
            version: Version string (publish, optional)
        
        Returns:
            JSON string with operation result
        """
        try:
            action = arguments.get("action")
            zettel_id = arguments.get("zettel_id")
            
            if not action:
                return json.dumps({
                    "error": "action is required (create, update, delete, or publish)"
                })
            
            if not zettel_id:
                return json.dumps({
                    "error": "zettel_id is required"
                })
            
            if action == "create":
                return await self._create_entry(arguments)
            elif action == "update":
                return await self._update_entry(arguments)
            elif action == "delete":
                return await self._delete_entry(arguments)
            elif action == "publish":
                return await self._publish_entry(arguments)
            else:
                return json.dumps({
                    "error": f"Unknown action: {action}"
                })
                
        except Exception as e:
            return json.dumps({
                "error": str(e)
            })
    
    def _sanitize_category(self, category: str) -> str:
        """
        Sanitize category name for filesystem.
        
        - Lowercase
        - Replace spaces/special chars with hyphens
        - Remove leading/trailing hyphens
        """
        import re
        # Convert to lowercase
        category = category.lower()
        
        # Replace invalid characters with hyphens
        category = re.sub(r'[^a-z0-9_/-]', '-', category)
        
        # Remove multiple consecutive hyphens
        category = re.sub(r'-+', '-', category)
        
        # Remove leading/trailing hyphens
        category = category.strip('-')
        
        return category
    
    def _entry_type_to_category(self, entry_type: str) -> str:
        """
        Derive category from entry_type using pluralization rules.
        
        Used when no explicit category is provided.
        """
        # Special cases
        if entry_type == "api_fact":
            return "apis"
        
        # Simple pluralization
        if entry_type.endswith('y'):
            return entry_type[:-1] + 'ies'  # category -> categories
        elif entry_type.endswith('s') or entry_type.endswith('x') or entry_type.endswith('ch'):
            return entry_type + 'es'  # box -> boxes, match -> matches
        else:
            return entry_type + 's'  # pattern -> patterns
    
    async def _create_entry(self, args: Dict[str, Any]) -> str:
        """Create a new knowledge entry with dynamic category support."""
        zettel_id = args["zettel_id"]
        title = args.get("title", "")
        content = args.get("content", "")
        entry_type = args.get("entry_type", "learning")
        category = args.get("category")
        tags = args.get("tags", [])
        source_type = args.get("source_type")
        source_url = args.get("source_url")
        location = args.get("location", "project")
        
        if not title or not content:
            return json.dumps({
                "error": "title and content are required for create"
            })
        
        # Determine target directory
        if location == "project":
            base_dir = self.resolver.project_knowledge_dir
        elif location == "user":
            base_dir = self.resolver.user_knowledge_dir
        else:
            return json.dumps({
                "error": f"Invalid location: {location}. Use 'project' or 'user'"
            })
        
        # Determine category
        if category:
            category = self._sanitize_category(category)
        else:
            category = self._entry_type_to_category(entry_type)
        
        # Create category directory (supports nested paths like "email/smtp")
        category_dir = base_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = category_dir / f"{zettel_id}.md"
        
        # Check if already exists
        if file_path.exists():
            return json.dumps({
                "error": f"Entry '{zettel_id}' already exists at {file_path}"
            })
        
        # Write file
        write_knowledge_file(
            file_path=file_path,
            zettel_id=zettel_id,
            title=title,
            content=content,
            entry_type=entry_type,
            category=category,  # Store category in frontmatter
            tags=tags,
            source_type=source_type,
            source_url=source_url
        )
        
        return json.dumps({
            "status": "success",
            "action": "create",
            "zettel_id": zettel_id,
            "location": location,
            "category": category,  # Return category used
            "path": str(file_path)
        }, indent=2)
    
    async def _update_entry(self, args: Dict[str, Any]) -> str:
        """Update an existing knowledge entry."""
        zettel_id = args["zettel_id"]
        
        # Find entry location
        resolution = self.resolver.resolve_entry(zettel_id, "local")
        
        if not resolution["location"]:
            return json.dumps({
                "error": f"Entry '{zettel_id}' not found in local storage"
            })
        
        file_path = Path(resolution["path"])
        entry_data = parse_knowledge_file(file_path)
        
        # Update fields
        if "title" in args:
            entry_data["title"] = args["title"]
        if "content" in args:
            entry_data["content"] = args["content"]
        if "tags" in args:
            entry_data["tags"] = args["tags"]
        if "source_type" in args:
            entry_data["source_type"] = args["source_type"]
        if "source_url" in args:
            entry_data["source_url"] = args["source_url"]
        
        # Write updated file
        write_knowledge_file(
            file_path=file_path,
            zettel_id=zettel_id,
            title=entry_data["title"],
            content=entry_data["content"],
            entry_type=entry_data["entry_type"],
            tags=entry_data.get("tags"),
            source_type=entry_data.get("source_type"),
            source_url=entry_data.get("source_url")
        )
        
        return json.dumps({
            "status": "success",
            "action": "update",
            "zettel_id": zettel_id,
            "location": resolution["location"],
            "path": str(file_path)
        }, indent=2)
    
    async def _delete_entry(self, args: Dict[str, Any]) -> str:
        """
        Delete a knowledge entry from specified source(s).
        
        Args:
            zettel_id: Entry to delete
            source: "local" | "registry" | ["local", "registry"] (default: "local" for backward compat)
            location: "project" | "user" | ["project", "user"] (optional, for local source)
            confirm: true (required)
            cascade_relationships: true (optional, for registry source)
        """
        zettel_id = args["zettel_id"]
        confirm = args.get("confirm", False)
        source = args.get("source", "local")  # Default to "local" for backward compatibility
        location = args.get("location")
        cascade_relationships = args.get("cascade_relationships", False)
        
        if not confirm:
            return json.dumps({
                "error": "confirm: true is required for delete"
            })
        
        # Normalize source to list
        sources = [source] if isinstance(source, str) else source
        
        deleted_from = {
            "local": [],
            "registry": False
        }
        errors = {}
        relationships_deleted = 0
        
        # Handle local deletion
        if "local" in sources:
            # Normalize location to list
            if location is None:
                # Default: try both project and user
                locations = ["project", "user"]
            elif isinstance(location, str):
                locations = [location]
            else:
                locations = location
            
            for loc in locations:
                if loc not in ["project", "user"]:
                    errors[f"local_{loc}"] = f"Invalid location: {loc}. Use 'project' or 'user'"
                    continue
                
                # Find entry in specific location
                if loc == "project":
                    project_path = self.resolver._check_project_space(zettel_id)
                    if project_path and project_path.exists():
                        project_path.unlink()
                        deleted_from["local"].append("project")
                elif loc == "user":
                    user_path = self.resolver._check_user_space(zettel_id)
                    if user_path and user_path.exists():
                        user_path.unlink()
                        deleted_from["local"].append("user")
            
            # If no location specified and nothing found, try resolver (backward compat)
            if not deleted_from["local"] and location is None:
                resolution = self.resolver.resolve_entry(zettel_id, "local")
                if resolution["location"]:
                    file_path = Path(resolution["path"])
                    file_path.unlink()
                    deleted_from["local"].append(resolution["location"])
        
        # Handle registry deletion
        if "registry" in sources:
            result = await self.registry.delete_entry(zettel_id, cascade_relationships)
            
            if "error" in result:
                errors["registry"] = result["error"]
            else:
                deleted_from["registry"] = True
                relationships_deleted = result.get("relationships_deleted", 0)
        
        # Determine overall status
        if errors and not deleted_from["local"] and not deleted_from["registry"]:
            status = "error"
        elif errors:
            status = "partial"
        else:
            status = "success"
        
        response = {
            "status": status,
            "action": "delete",
            "zettel_id": zettel_id,
            "deleted_from": deleted_from
        }
        
        if relationships_deleted > 0:
            response["relationships_deleted"] = relationships_deleted
        
        if errors:
            response["errors"] = errors
        
        return json.dumps(response, indent=2)
    
    async def _publish_entry(self, args: Dict[str, Any]) -> str:
        """Publish entry from local to registry."""
        zettel_id = args["zettel_id"]
        version = args.get("version")
        location = args.get("location", "project")
        
        # Find entry in local storage
        resolution = self.resolver.resolve_entry(zettel_id, "local")
        
        if not resolution["location"]:
            return json.dumps({
                "error": f"Entry '{zettel_id}' not found in local storage"
            })
        
        file_path = Path(resolution["path"])
        entry_data = parse_knowledge_file(file_path)
        
        # Publish to registry
        result = await self.registry.publish_entry(
            zettel_id=zettel_id,
            title=entry_data["title"],
            content=entry_data["content"],
            entry_type=entry_data["entry_type"],
            category=entry_data.get("category"),  # Include category from file
            tags=entry_data.get("tags"),
            source_type=entry_data.get("source_type"),
            source_url=entry_data.get("source_url"),
            version=version
        )
        
        if "error" in result:
            return json.dumps(result, indent=2)
        
        return json.dumps({
            "status": "success",
            "action": "publish",
            "zettel_id": zettel_id,
            "version": result.get("version"),
            "published_to": "registry",
            "location": resolution["location"]
        }, indent=2)

