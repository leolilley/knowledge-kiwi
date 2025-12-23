"""
Knowledge Registry API Client

Handles all interactions with Supabase knowledge_entries table (registry tier).
"""

import os
from typing import Dict, List, Optional, Any
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()


class KnowledgeRegistry:
    """Client for Knowledge Kiwi Supabase registry."""
    
    def __init__(self):
        self._client = None
    
    @property
    def client(self):
        """Lazily initialize Supabase client."""
        if self._client is None:
            # Read from os.environ directly (set by MCP server or .env file)
            url = os.getenv("SUPABASE_URL")
            # Use SUPABASE_SECRET_KEY for write access
            key = os.getenv("SUPABASE_SECRET_KEY")
            
            if not url or not key:
                return None
            
            # Trim whitespace from key (common issue with .env files)
            url = url.strip() if url else None
            key = key.strip() if key else None
            
            if not url or not key:
                return None
            
            try:
                self._client = create_client(url, key)
            except Exception as e:
                # If client creation fails, return None
                print(f"Error creating Supabase client: {e}")
                return None
        return self._client
    
    @property
    def is_configured(self) -> bool:
        """Check if Supabase is configured."""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SECRET_KEY")
        return bool(url and key)
    
    def _parse_search_query(self, query: str) -> List[str]:
        """
        Parse search query into normalized terms.
        
        Handles:
        - Multiple words (split by whitespace)
        - Normalization (lowercase, strip)
        - Filters out single characters
        
        Future: Add support for quoted phrases and operators (| for OR, - for NOT)
        """
        if not query or not query.strip():
            return []
        
        terms = []
        for word in query.split():
            word = word.strip().lower()
            if word and len(word) >= 2:  # Ignore single characters
                terms.append(word)
        
        return terms
    
    def _calculate_relevance_score(
        self,
        query_terms: List[str],
        title: str,
        description: Optional[str] = None
    ) -> float:
        """
        Calculate relevance score based on term matches.
        
        Scoring:
        - Exact title match: 100
        - Title contains all terms: 80
        - Title contains some terms: 60 * (matches/terms)
        - Description contains all terms: 40
        - Description contains some terms: 20 * (matches/terms)
        """
        title_lower = title.lower()
        desc_lower = (description or "").lower()
        
        # Check exact title match
        title_normalized = title_lower.replace("_", " ").replace("-", " ")
        query_normalized = " ".join(query_terms)
        if title_normalized == query_normalized or title_lower == query_normalized.replace(" ", "_"):
            return 100.0
        
        # Count term matches in title
        title_matches = sum(1 for term in query_terms if term in title_lower)
        desc_matches = sum(1 for term in query_terms if term in desc_lower)
        
        # Calculate score
        score = 0.0
        
        if title_matches == len(query_terms):
            score = 80.0  # All terms in title
        elif title_matches > 0:
            score = 60.0 * (title_matches / len(query_terms))  # Some terms in title
        
        if desc_matches == len(query_terms):
            score = max(score, 40.0)  # All terms in description
        elif desc_matches > 0:
            score = max(score, 20.0 * (desc_matches / len(query_terms)))  # Some terms in description
        
        return score
    
    async def search_entries(
        self,
        query: str,
        category: Optional[str] = None,
        entry_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search entries in registry using full-text search with multi-term matching.
        
        Returns list of entries with relevance scores.
        """
        if not self.client:
            return []
        
        # Parse query into normalized terms
        query_terms = self._parse_search_query(query)
        if not query_terms:
            return []
        
        try:
            # Use the search function - get more results to filter client-side
            result = self.client.rpc(
                "search_knowledge_fulltext",
                {
                    "search_query": query,
                    "match_count": limit * 3,  # Get more results for client-side filtering
                    "filter_entry_type": entry_type,
                    "filter_tags": tags,
                    "filter_category": category
                }
            ).execute()
            
            entries = []
            for row in result.data:
                title = row.get("title", "")
                snippet = row.get("snippet", "")
                
                # CRITICAL: Multi-term matching - ensure ALL terms appear
                title_snippet = f"{title} {snippet}".lower()
                if not all(term in title_snippet for term in query_terms):
                    continue  # Skip if not all terms match
                
                # Calculate relevance score
                relevance_score = self._calculate_relevance_score(
                    query_terms,
                    title,
                    snippet
                )
                
                entries.append({
                    "zettel_id": row["zettel_id"],
                    "title": title,
                    "entry_type": row["entry_type"],
                    "category": row.get("category"),  # Include category
                    "tags": row.get("tags", []),
                    "source_location": "registry",
                    "relevance_score": relevance_score / 100.0,  # Normalize to 0-1 range
                    "snippet": snippet
                })
            
            # Sort by relevance score (highest first)
            entries.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
            
            return entries[:limit]
        except Exception as e:
            print(f"Error searching registry: {e}")
            return []
    
    async def get_entry(self, zettel_id: str) -> Optional[Dict[str, Any]]:
        """Get entry from registry."""
        if not self.client:
            return None
        
        try:
            result = self.client.table("knowledge_entries").select("*").eq("zettel_id", zettel_id).single().execute()
            
            if result.data:
                return {
                    "zettel_id": result.data["zettel_id"],
                    "title": result.data["title"],
                    "content": result.data["content"],
                    "entry_type": result.data["entry_type"],
                    "category": result.data.get("category"),  # Include category
                    "tags": result.data.get("tags", []),
                    "source_type": result.data.get("source_type"),
                    "source_url": result.data.get("source_url"),
                    "version": result.data.get("version", "1.0.0"),
                    "created_at": result.data.get("created_at"),
                    "updated_at": result.data.get("updated_at")
                }
            return None
        except Exception as e:
            print(f"Error getting entry from registry: {e}")
            return None
    
    async def publish_entry(
        self,
        zettel_id: str,
        title: str,
        content: str,
        entry_type: str,
        tags: Optional[List[str]] = None,
        category: Optional[str] = None,
        source_type: Optional[str] = None,
        source_url: Optional[str] = None,
        version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Publish entry to registry.
        
        If entry exists, updates it. Otherwise creates new entry.
        """
        if not self.client:
            return {"error": "Supabase client not initialized"}
        
        try:
            # Check if entry exists
            existing = await self.get_entry(zettel_id)
            
            entry_data = {
                "zettel_id": zettel_id,
                "title": title,
                "content": content,
                "entry_type": entry_type,
                "tags": tags or [],
                "category": category,  # Include category
                "source_type": source_type,
                "source_url": source_url,
            }
            
            if version:
                entry_data["version"] = version
            elif existing:
                # Auto-increment version
                current_version = existing.get("version", "1.0.0")
                try:
                    parts = current_version.split(".")
                    patch = int(parts[-1]) + 1
                    entry_data["version"] = ".".join(parts[:-1] + [str(patch)])
                except:
                    entry_data["version"] = "1.0.1"
            
            if existing:
                # Update existing entry
                result = self.client.table("knowledge_entries").update(entry_data).eq("zettel_id", zettel_id).execute()
            else:
                # Create new entry
                if "version" not in entry_data:
                    entry_data["version"] = "1.0.0"
                result = self.client.table("knowledge_entries").insert(entry_data).execute()
            
            return {
                "status": "success",
                "zettel_id": zettel_id,
                "version": entry_data.get("version", "1.0.0")
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def get_relationships(
        self,
        zettel_id: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get relationships for an entry.
        
        Returns:
            {
                "outgoing": [...],  # Relationships from this entry
                "incoming": [...]   # Relationships to this entry
            }
        """
        if not self.client:
            return {"outgoing": [], "incoming": []}
        
        try:
            # Get outgoing relationships
            outgoing_result = self.client.table("knowledge_relationships").select("*").eq("from_zettel_id", zettel_id).execute()
            
            # Get incoming relationships
            incoming_result = self.client.table("knowledge_relationships").select("*").eq("to_zettel_id", zettel_id).execute()
            
            return {
                "outgoing": [
                    {
                        "zettel_id": rel["to_zettel_id"],
                        "relationship_type": rel["relationship_type"]
                    }
                    for rel in outgoing_result.data
                ],
                "incoming": [
                    {
                        "zettel_id": rel["from_zettel_id"],
                        "relationship_type": rel["relationship_type"]
                    }
                    for rel in incoming_result.data
                ]
            }
        except Exception as e:
            print(f"Error getting relationships: {e}")
            return {"outgoing": [], "incoming": []}
    
    async def create_relationship(
        self,
        from_zettel_id: str,
        to_zettel_id: str,
        relationship_type: str
    ) -> Dict[str, Any]:
        """Create a relationship between two entries."""
        if not self.client:
            return {"error": "Supabase client not initialized"}
        
        try:
            result = self.client.table("knowledge_relationships").insert({
                "from_zettel_id": from_zettel_id,
                "to_zettel_id": to_zettel_id,
                "relationship_type": relationship_type
            }).execute()
            
            return {
                "status": "success",
                "relationship": {
                    "from_zettel_id": from_zettel_id,
                    "to_zettel_id": to_zettel_id,
                    "relationship_type": relationship_type
                }
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def create_collection(
        self,
        name: str,
        description: Optional[str],
        zettel_ids: List[str],
        collection_type: str
    ) -> Dict[str, Any]:
        """Create a collection of entries."""
        if not self.client:
            return {"error": "Supabase client not initialized"}
        
        try:
            result = self.client.table("knowledge_collections").insert({
                "name": name,
                "description": description,
                "zettel_ids": zettel_ids,
                "collection_type": collection_type
            }).execute()
            
            return {
                "status": "success",
                "collection_id": result.data[0]["id"] if result.data else None
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def delete_entry(
        self,
        zettel_id: str,
        cascade_relationships: bool = False
    ) -> Dict[str, Any]:
        """
        Delete entry from registry.
        
        Args:
            zettel_id: Entry to delete
            cascade_relationships: If True, delete related relationships first.
                                   If False, prevent deletion if relationships exist.
        
        Returns:
            {"status": "success"} or {"error": "..."}
        """
        if not self.client:
            return {"error": "Supabase client not initialized"}
        
        try:
            # Check if entry exists
            existing = await self.get_entry(zettel_id)
            if not existing:
                return {"error": f"Entry '{zettel_id}' not found in registry"}
            
            # Check for relationships
            relationships = await self.get_relationships(zettel_id)
            total_relationships = len(relationships.get("outgoing", [])) + len(relationships.get("incoming", []))
            
            if total_relationships > 0 and not cascade_relationships:
                return {
                    "error": f"Cannot delete entry: {total_relationships} relationship(s) exist. Set cascade_relationships: true to delete relationships first."
                }
            
            # Delete relationships if cascade is enabled
            if cascade_relationships and total_relationships > 0:
                # Delete outgoing relationships
                self.client.table("knowledge_relationships").delete().eq("from_zettel_id", zettel_id).execute()
                # Delete incoming relationships
                self.client.table("knowledge_relationships").delete().eq("to_zettel_id", zettel_id).execute()
            
            # Delete the entry
            self.client.table("knowledge_entries").delete().eq("zettel_id", zettel_id).execute()
            
            return {
                "status": "success",
                "zettel_id": zettel_id,
                "relationships_deleted": total_relationships if cascade_relationships else 0
            }
        except Exception as e:
            return {"error": str(e)}

