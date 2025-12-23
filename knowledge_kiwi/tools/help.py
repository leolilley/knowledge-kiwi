"""Help tool for Knowledge Kiwi."""

from typing import Dict, Any
import json


class HelpTool:
    """Provide workflow guidance and examples."""
    
    async def execute(self, params: Dict[str, Any]) -> str:
        """
        Get help with knowledge operations.
        
        Args:
            query: What you need help with
            context: Additional context
        
        Returns:
            Helpful guidance and examples
        """
        query = params.get("query", "").lower()
        context = params.get("context", "")
        
        # Pattern matching for common queries
        if "create" in query or "new entry" in query:
            return self._help_create()
        elif "search" in query or "find" in query:
            return self._help_search()
        elif "delete" in query or "remove" in query:
            return self._help_delete()
        elif "link" in query or "relationship" in query:
            return self._help_link()
        elif "publish" in query or "share" in query:
            return self._help_publish()
        elif "source" in query or "local" in query or "registry" in query:
            return self._help_source_selection()
        else:
            return self._help_general()
    
    def _help_create(self) -> str:
        return json.dumps({
            "topic": "Creating Knowledge Entries",
            "workflow": [
                "1. Search first to avoid duplicates: search({'query': 'your topic', 'source': 'local'})",
                "2. Create entry: manage({'action': 'create', 'zettel_id': '042-your-id', 'title': '...', 'content': '...', 'entry_type': 'pattern', 'location': 'project'})",
                "3. Link to related entries: link({'action': 'link', 'from_zettel_id': '042-your-id', 'to_zettel_id': '043-related', 'relationship_type': 'references'})"
            ],
            "examples": [
                {
                    "description": "Create a pattern entry",
                    "code": "manage({'action': 'create', 'zettel_id': '042-email-deliverability', 'title': 'Email Deliverability Best Practices', 'content': '# Email Deliverability...', 'entry_type': 'pattern', 'tags': ['email', 'deliverability'], 'location': 'project'})"
                },
                {
                    "description": "Create a learning entry",
                    "code": "manage({'action': 'create', 'zettel_id': '045-dental-leads', 'title': 'Dental Clinic Lead Generation', 'content': '...', 'entry_type': 'learning', 'source_type': 'experiment', 'location': 'project'})"
                }
            ],
            "entry_types": [
                "api_fact - API documentation snippets",
                "pattern - Reusable patterns",
                "concept - Mental models",
                "learning - Things you've learned",
                "experiment - Experiment results",
                "reference - Quick reference notes",
                "template - Code/content templates",
                "workflow - Process documentation"
            ]
        }, indent=2)
    
    def _help_search(self) -> str:
        return json.dumps({
            "topic": "Searching Knowledge",
            "workflow": [
                "1. Search local (offline): search({'query': 'email', 'source': 'local'})",
                "2. Search registry (shared): search({'query': 'email', 'source': 'registry'})",
                "3. Search both: search({'query': 'email', 'source': ['local', 'registry']})"
            ],
            "examples": [
                {
                    "description": "Search local knowledge only",
                    "code": "search({'query': 'email deliverability', 'source': 'local', 'entry_type': 'pattern', 'limit': 10})"
                },
                {
                    "description": "Search registry for shared knowledge",
                    "code": "search({'query': 'lead generation', 'source': 'registry', 'tags': ['outreach'], 'limit': 5})"
                }
            ],
            "tips": [
                "Use 'local' source for offline work",
                "Use 'registry' source to discover shared knowledge",
                "Combine both sources for comprehensive results",
                "Filter by entry_type or tags for better results"
            ]
        }, indent=2)
    
    def _help_link(self) -> str:
        return json.dumps({
            "topic": "Linking Entries and Collections",
            "workflow": [
                "1. Link two entries: link({'action': 'link', 'from_zettel_id': '042-email', 'to_zettel_id': '043-spf', 'relationship_type': 'references'})",
                "2. Create collection: link({'action': 'create_collection', 'name': 'Email Infrastructure', 'zettel_ids': ['042-email', '043-spf'], 'collection_type': 'topic'})",
                "3. Get relationships: link({'action': 'get_relationships', 'zettel_id': '042-email'})"
            ],
            "relationship_types": [
                "references - A mentions B",
                "contradicts - A disagrees with B",
                "extends - A builds on B",
                "implements - A is implementation of B",
                "supersedes - A replaces B",
                "depends_on - A requires B",
                "related - General relationship",
                "example_of - A is example of B"
            ],
            "collection_types": [
                "topic - Related by topic",
                "project - Project-specific",
                "learning_path - Sequential learning",
                "reference - Quick reference",
                "archive - Archived entries"
            ]
        }, indent=2)
    
    def _help_delete(self) -> str:
        return json.dumps({
            "topic": "Deleting Knowledge Entries",
            "workflow": [
                "1. Delete from local: manage({'action': 'delete', 'zettel_id': '042-email', 'source': 'local', 'confirm': true})",
                "2. Delete from registry: manage({'action': 'delete', 'zettel_id': '042-email', 'source': 'registry', 'confirm': true})",
                "3. Delete from both: manage({'action': 'delete', 'zettel_id': '042-email', 'source': ['local', 'registry'], 'confirm': true})"
            ],
            "examples": [
                {
                    "description": "Delete from project space only",
                    "code": "manage({'action': 'delete', 'zettel_id': '042-email-deliverability', 'source': 'local', 'location': 'project', 'confirm': true})"
                },
                {
                    "description": "Delete from user space only",
                    "code": "manage({'action': 'delete', 'zettel_id': '042-email-deliverability', 'source': 'local', 'location': 'user', 'confirm': true})"
                },
                {
                    "description": "Delete from registry",
                    "code": "manage({'action': 'delete', 'zettel_id': '042-email-deliverability', 'source': 'registry', 'confirm': true})"
                },
                {
                    "description": "Delete from registry with relationships (cascade)",
                    "code": "manage({'action': 'delete', 'zettel_id': '042-email-deliverability', 'source': 'registry', 'cascade_relationships': true, 'confirm': true})"
                },
                {
                    "description": "Delete from all tiers",
                    "code": "manage({'action': 'delete', 'zettel_id': '042-email-deliverability', 'source': ['local', 'registry'], 'confirm': true})"
                }
            ],
            "tips": [
                "Always requires confirm: true for safety",
                "Can delete from project, user, or registry",
                "Can delete from multiple tiers in one operation",
                "Registry deletions with relationships require cascade_relationships: true",
                "Backward compatible: old API (no source) defaults to local"
            ],
            "safety": [
                "confirm: true is always required",
                "Registry deletions check for relationships by default",
                "Set cascade_relationships: true to delete relationships too"
            ]
        }, indent=2)
    
    def _help_publish(self) -> str:
        return json.dumps({
            "topic": "Publishing to Registry",
            "workflow": [
                "1. Create entry locally: manage({'action': 'create', 'location': 'project', ...})",
                "2. Refine and update: manage({'action': 'update', ...})",
                "3. Publish when ready: manage({'action': 'publish', 'zettel_id': '042-email', 'location': 'project'})"
            ],
            "examples": [
                {
                    "description": "Publish from project space",
                    "code": "manage({'action': 'publish', 'zettel_id': '042-email-deliverability', 'location': 'project'})"
                },
                {
                    "description": "Publish with specific version",
                    "code": "manage({'action': 'publish', 'zettel_id': '042-email-deliverability', 'version': '1.1.0', 'location': 'project'})"
                }
            ],
            "tips": [
                "Publish makes your knowledge available to others",
                "Version auto-increments if not specified",
                "Can publish from project or user space"
            ]
        }, indent=2)
    
    def _help_source_selection(self) -> str:
        return json.dumps({
            "topic": "Explicit Source Selection",
            "explanation": "Knowledge Kiwi requires explicit source selection - you choose where to search/read from",
            "source_options": [
                {
                    "source": "local",
                    "description": "Checks project space (.ai/knowledge/) then user space (~/.knowledge-kiwi/)",
                    "use_case": "Offline work, fast access",
                    "example": "search({'query': 'email', 'source': 'local'})"
                },
                {
                    "source": "registry",
                    "description": "Checks Supabase registry only",
                    "use_case": "Shared knowledge, versioned entries",
                    "example": "search({'query': 'email', 'source': 'registry'})"
                },
                {
                    "source": "['local', 'registry']",
                    "description": "Checks both, local results prioritized",
                    "use_case": "Comprehensive search",
                    "example": "search({'query': 'email', 'source': ['local', 'registry']})"
                }
            ],
            "why_explicit": [
                "Prevents unexpected network calls",
                "Clear separation between offline and online",
                "User controls when to hit the network",
                "Transparency - always know where knowledge came from"
            ],
            "tips": [
                "Default to 'local' for offline-first workflows",
                "Use 'registry' to discover shared knowledge",
                "Combine both for comprehensive results"
            ]
        }, indent=2)
    
    def _help_general(self) -> str:
        return json.dumps({
            "topic": "Knowledge Kiwi Overview",
            "description": "Knowledge Kiwi provides a 5-tool interface for managing your knowledge base",
            "tools": [
                {
                    "name": "search",
                    "description": "Search knowledge entries with explicit source selection",
                    "example": "search({'query': 'email', 'source': 'local'})"
                },
                {
                    "name": "get",
                    "description": "Get entry details with relationships",
                    "example": "get({'zettel_id': '042-email', 'source': 'local'})"
                },
                {
                    "name": "manage",
                    "description": "Create, update, delete, and publish entries",
                    "example": "manage({'action': 'create', 'zettel_id': '042-email', 'title': '...', 'content': '...', 'entry_type': 'pattern'})"
                },
                {
                    "name": "link",
                    "description": "Link entries and create collections",
                    "example": "link({'action': 'link', 'from_zettel_id': '042-email', 'to_zettel_id': '043-spf', 'relationship_type': 'references'})"
                },
                {
                    "name": "help",
                    "description": "Get workflow guidance",
                    "example": "help({'query': 'how to create an entry'})"
                }
            ],
            "storage_tiers": [
                "Project Space (.ai/knowledge/) - Project-specific knowledge",
                "User Space (~/.knowledge-kiwi/) - Personal knowledge library",
                "Registry (Supabase) - Shared, versioned knowledge"
            ],
            "workflow_examples": "See v2/Knowledge-Kiwi-Workflow-Examples.md for complete examples"
        }, indent=2)

