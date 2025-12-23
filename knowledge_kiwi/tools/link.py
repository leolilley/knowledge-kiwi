"""Link tool for Knowledge Kiwi (relationships and collections)."""

import json
from typing import Dict, Any, Optional, List

from ..api.knowledge_registry import KnowledgeRegistry


class LinkTool:
    """Manage relationships and collections."""
    
    def __init__(self):
        self.registry = KnowledgeRegistry()
    
    async def execute(self, arguments: Dict[str, Any]) -> str:
        """
        Manage relationships and collections.
        
        Args:
            action: "link" | "create_collection" | "get_relationships"
            from_zettel_id: Source entry ID (link)
            to_zettel_id: Target entry ID (link)
            relationship_type: Type of relationship (link)
            name: Collection name (create_collection)
            description: Collection description (create_collection)
            zettel_ids: Array of zettel IDs (create_collection)
            collection_type: Type of collection (create_collection)
            zettel_id: Entry ID (get_relationships)
        
        Returns:
            JSON string with operation result
        """
        try:
            action = arguments.get("action")
            
            if not action:
                return json.dumps({
                    "error": "action is required (link, create_collection, or get_relationships)"
                })
            
            if action == "link":
                return await self._link_entries(arguments)
            elif action == "create_collection":
                return await self._create_collection(arguments)
            elif action == "get_relationships":
                return await self._get_relationships(arguments)
            else:
                return json.dumps({
                    "error": f"Unknown action: {action}"
                })
                
        except Exception as e:
            return json.dumps({
                "error": str(e)
            })
    
    async def _link_entries(self, args: Dict[str, Any]) -> str:
        """Link two entries with a relationship."""
        from_zettel_id = args.get("from_zettel_id")
        to_zettel_id = args.get("to_zettel_id")
        relationship_type = args.get("relationship_type", "references")
        
        if not from_zettel_id or not to_zettel_id:
            return json.dumps({
                "error": "from_zettel_id and to_zettel_id are required"
            })
        
        valid_types = [
            "references", "contradicts", "extends", "implements",
            "supersedes", "depends_on", "related", "example_of"
        ]
        
        if relationship_type not in valid_types:
            return json.dumps({
                "error": f"Invalid relationship_type. Must be one of: {valid_types}"
            })
        
        result = await self.registry.create_relationship(
            from_zettel_id=from_zettel_id,
            to_zettel_id=to_zettel_id,
            relationship_type=relationship_type
        )
        
        if "error" in result:
            return json.dumps(result, indent=2)
        
        return json.dumps({
            "status": "success",
            "action": "link",
            "relationship": result.get("relationship")
        }, indent=2)
    
    async def _create_collection(self, args: Dict[str, Any]) -> str:
        """Create a collection of entries."""
        name = args.get("name")
        description = args.get("description")
        zettel_ids = args.get("zettel_ids", [])
        collection_type = args.get("collection_type", "topic")
        
        if not name:
            return json.dumps({
                "error": "name is required for create_collection"
            })
        
        valid_types = ["topic", "project", "learning_path", "reference", "archive"]
        
        if collection_type not in valid_types:
            return json.dumps({
                "error": f"Invalid collection_type. Must be one of: {valid_types}"
            })
        
        result = await self.registry.create_collection(
            name=name,
            description=description,
            zettel_ids=zettel_ids,
            collection_type=collection_type
        )
        
        if "error" in result:
            return json.dumps(result, indent=2)
        
        return json.dumps({
            "status": "success",
            "action": "create_collection",
            "collection_id": result.get("collection_id")
        }, indent=2)
    
    async def _get_relationships(self, args: Dict[str, Any]) -> str:
        """Get relationships for an entry."""
        zettel_id = args.get("zettel_id")
        
        if not zettel_id:
            return json.dumps({
                "error": "zettel_id is required for get_relationships"
            })
        
        relationships = await self.registry.get_relationships(zettel_id)
        
        return json.dumps({
            "zettel_id": zettel_id,
            "relationships": {
                "outgoing": [
                    {
                        "zettel_id": rel["zettel_id"],
                        "relationship_type": rel["relationship_type"],
                        "direction": "outgoing"
                    }
                    for rel in relationships.get("outgoing", [])
                ],
                "incoming": [
                    {
                        "zettel_id": rel["zettel_id"],
                        "relationship_type": rel["relationship_type"],
                        "direction": "incoming"
                    }
                    for rel in relationships.get("incoming", [])
                ]
            }
        }, indent=2)

