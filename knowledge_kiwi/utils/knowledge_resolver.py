"""Knowledge resolver for 3-tier storage system with explicit source selection."""

from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import yaml
import re


class KnowledgeResolver:
    """Resolve knowledge entries from 3-tier storage system with dynamic categories."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize resolver.
        
        Args:
            project_root: Project root directory (defaults to current working directory)
        """
        self.project_root = project_root or Path.cwd()
        self.project_knowledge_dir = self.project_root / ".ai" / "knowledge"
        self.user_knowledge_dir = Path.home() / ".knowledge-kiwi"
    
    def discover_categories(self, base_dir: Path) -> List[str]:
        """
        Discover all categories by scanning directories recursively.
        
        Returns list of category paths (e.g., ["patterns", "email-infrastructure/smtp"]).
        """
        if not base_dir.exists():
            return []
        
        categories = set()
        for item in base_dir.rglob("*"):
            if item.is_dir() and not item.name.startswith('.'):
                # Get relative path from base_dir
                rel_path = item.relative_to(base_dir)
                category_path = str(rel_path).replace('\\', '/')
                categories.add(category_path)
        
        return sorted(categories)
    
    def resolve_entry(
        self,
        zettel_id: str,
        source: Union[str, List[str]],
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Resolve entry with explicit source selection.
        
        Args:
            zettel_id: Unique identifier (e.g., "042-email-deliverability")
            source: "local" | "registry" | ["local", "registry"]
            category: Optional category to narrow search
        
        Returns:
            {
                "location": "project" | "user" | "registry" | None,
                "path": Path | None,
                "version": str | None
            }
        """
        # Normalize source to list
        sources = [source] if isinstance(source, str) else source
        
        # Check local sources (project → user)
        if "local" in sources:
            # 1. Check project space first
            project_path = self._check_project_space(zettel_id, category)
            if project_path and project_path.exists():
                return {
                    "location": "project",
                    "path": project_path,
                    "version": None
                }
            
            # 2. Check user space
            user_path = self._check_user_space(zettel_id, category)
            if user_path and user_path.exists():
                return {
                    "location": "user",
                    "path": user_path,
                    "version": None
                }
        
        # Check registry (only if "registry" in sources and not found locally)
        if "registry" in sources:
            # Registry check will be done by API client
            return {
                "location": "registry",
                "path": None,
                "version": None
            }
        
        return {"location": None, "path": None, "version": None}
    
    def _check_project_space(
        self,
        zettel_id: str,
        category: Optional[str] = None
    ) -> Optional[Path]:
        """Check project space for entry."""
        if category:
            candidate = self.project_knowledge_dir / category / f"{zettel_id}.md"
            if candidate.exists():
                return candidate
        
        for md_file in self.project_knowledge_dir.rglob(f"{zettel_id}.md"):
            return md_file
        
        return None
    
    def _check_user_space(
        self,
        zettel_id: str,
        category: Optional[str] = None
    ) -> Optional[Path]:
        """Check user space for entry."""
        if category:
            candidate = self.user_knowledge_dir / category / f"{zettel_id}.md"
            if candidate.exists():
                return candidate
        
        for md_file in self.user_knowledge_dir.rglob(f"{zettel_id}.md"):
            return md_file
        
        return None
    
    def search_local(
        self,
        query: str,
        category: Optional[str] = None,
        entry_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search local knowledge (project + user space).
        
        Returns results with source_location for each entry.
        """
        results = []
        
        # Search project space
        project_results = self._search_directory(
            self.project_knowledge_dir,
            query,
            category,
            entry_type,
            tags,
            limit,
            "project"
        )
        results.extend(project_results)
        
        # Search user space (avoid duplicates)
        existing_zettel_ids = {r["zettel_id"] for r in project_results}
        user_results = self._search_directory(
            self.user_knowledge_dir,
            query,
            category,
            entry_type,
            tags,
            limit,
            "user"
        )
        results.extend([
            r for r in user_results
            if r["zettel_id"] not in existing_zettel_ids
        ])
        
        # Sort by relevance and limit
        results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        return results[:limit]
    
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
        content: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> float:
        """
        Calculate relevance score based on term matches.
        
        Scoring:
        - Exact title match: 100
        - Title contains all terms: 80
        - Title contains some terms: 60 * (matches/terms)
        - Content contains all terms: 40
        - Content contains some terms: 20 * (matches/terms)
        - Category match: +15
        - Tags match: +10
        """
        title_lower = title.lower()
        content_lower = (content or "").lower()
        category_lower = (category or "").lower() if category else ""
        tags_str = " ".join(tags or []).lower()
        
        # Check exact title match
        title_normalized = title_lower.replace("_", " ").replace("-", " ")
        query_normalized = " ".join(query_terms)
        if title_normalized == query_normalized or title_lower == query_normalized.replace(" ", "_"):
            return 100.0
        
        # Count term matches in title
        title_matches = sum(1 for term in query_terms if term in title_lower)
        content_matches = sum(1 for term in query_terms if term in content_lower)
        
        # Calculate score
        score = 0.0
        
        if title_matches == len(query_terms):
            score = 80.0  # All terms in title
        elif title_matches > 0:
            score = 60.0 * (title_matches / len(query_terms))  # Some terms in title
        
        if content_matches == len(query_terms):
            score = max(score, 40.0)  # All terms in content
        elif content_matches > 0:
            score = max(score, 20.0 * (content_matches / len(query_terms)))  # Some terms in content
        
        # Category match (bonus)
        if category_lower:
            category_matches = sum(1 for term in query_terms if term in category_lower)
            if category_matches > 0:
                score += 15.0 * (category_matches / len(query_terms))
        
        # Tags match (bonus)
        if tags_str:
            tag_matches = sum(1 for term in query_terms if term in tags_str)
            if tag_matches > 0:
                score += 10.0 * min(tag_matches / len(query_terms), 1.0)
        
        return min(score, 100.0)  # Cap at 100
    
    def _search_directory(
        self,
        base_dir: Path,
        query: str,
        category: Optional[str] = None,
        entry_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10,
        source_location: str = "project"
    ) -> List[Dict[str, Any]]:
        """Search a directory for matching entries with improved multi-term search."""
        results = []
        
        if not base_dir.exists():
            return results
        
        # Parse query into normalized terms
        query_terms = self._parse_search_query(query)
        if not query_terms:
            return results
        
        # Determine search scope
        if category:
            cat_dir = base_dir / category
            if cat_dir.exists():
                search_paths = list(cat_dir.rglob("*.md"))
            else:
                search_paths = []
        else:
            search_paths = list(base_dir.rglob("*.md"))
            
        for file_path in search_paths:
            try:
                entry_data = parse_knowledge_file(file_path)
                
                # Filter by entry_type
                if entry_type and entry_data.get("entry_type") != entry_type:
                    continue
                
                # Filter by tags
                if tags:
                    entry_tags = entry_data.get("tags", [])
                    if not any(tag in entry_tags for tag in tags):
                        continue
                
                title = entry_data.get("title", "")
                content = entry_data.get("content", "")
                entry_category = entry_data.get("category")
                entry_tags = entry_data.get("tags", [])
                
                # CRITICAL: Multi-term matching - ensure ALL terms appear
                title_content = f"{title} {content}".lower()
                if not all(term in title_content for term in query_terms):
                    continue  # Skip if not all terms match
                
                # Calculate relevance score
                relevance_score = self._calculate_relevance_score(
                    query_terms,
                    title,
                    content,
                    entry_category,
                    entry_tags
                )
                
                if relevance_score > 0:
                    # Extract snippet
                    snippet = self._extract_snippet(content, query_terms)
                    
                    # Get category path relative to base_dir
                    rel_path = file_path.parent.relative_to(base_dir)
                    category_path = str(rel_path).replace('\\', '/')
                    
                    results.append({
                        "zettel_id": entry_data.get("zettel_id"),
                        "title": title,
                        "entry_type": entry_data.get("entry_type"),
                        "category": category_path,  # Include category path
                        "tags": entry_tags,
                        "source_location": source_location,
                        "relevance_score": relevance_score / 100.0,  # Normalize to 0-1 range
                        "snippet": snippet
                    })
            except Exception:
                # Skip files that can't be parsed
                continue
        
        return results
    
    def _extract_snippet(self, content: str, query_terms: List[str], max_length: int = 150) -> str:
        """Extract a snippet around query terms."""
        content_lower = content.lower()
        
        # Find first occurrence of any query term
        for term in query_terms:
            idx = content_lower.find(term)
            if idx != -1:
                start = max(0, idx - 50)
                end = min(len(content), idx + len(term) + 100)
                snippet = content[start:end]
                if start > 0:
                    snippet = "..." + snippet
                if end < len(content):
                    snippet = snippet + "..."
                return snippet.strip()
        
        # Fallback: first max_length characters
        return content[:max_length] + "..." if len(content) > max_length else content


def parse_knowledge_file(file_path: Path) -> Dict[str, Any]:
    """
    Parse markdown file with YAML frontmatter.
    
    Returns:
        Dictionary with frontmatter fields + "content" key
    """
    content = file_path.read_text(encoding="utf-8")
    
    # Split frontmatter and content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter_str = parts[1].strip()
            body = parts[2].strip()
            
            try:
                frontmatter = yaml.safe_load(frontmatter_str) or {}
            except yaml.YAMLError:
                frontmatter = {}
        else:
            frontmatter = {}
            body = content
    else:
        frontmatter = {}
        body = content
    
    # Extract zettel_id from filename if not in frontmatter
    if "zettel_id" not in frontmatter:
        frontmatter["zettel_id"] = file_path.stem
    
    return {
        **frontmatter,
        "content": body,
        "path": str(file_path)
    }


def write_knowledge_file(
    file_path: Path,
    zettel_id: str,
    title: str,
    content: str,
    entry_type: str,
    tags: Optional[List[str]] = None,
    source_type: Optional[str] = None,
    source_url: Optional[str] = None,
    category: Optional[str] = None,
    **kwargs
) -> None:
    """
    Write knowledge entry to markdown file with YAML frontmatter.
    
    Args:
        file_path: Path to write file
        zettel_id: Unique identifier
        title: Entry title
        content: Entry content (markdown)
        entry_type: Type of entry
        tags: Optional tags
        source_type: Optional source type
        source_url: Optional source URL
        **kwargs: Additional frontmatter fields
    """
    # Ensure directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Build frontmatter
    frontmatter = {
        "zettel_id": zettel_id,
        "title": title,
        "entry_type": entry_type,
    }
    
    if category:
        frontmatter["category"] = category
    
    if tags:
        frontmatter["tags"] = tags
    
    if source_type:
        frontmatter["source_type"] = source_type
    
    if source_url:
        frontmatter["source_url"] = source_url
    
    # Add any additional fields
    frontmatter.update(kwargs)
    
    # Write file
    frontmatter_yaml = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
    file_content = f"---\n{frontmatter_yaml}---\n\n{content}\n"
    
    file_path.write_text(file_content, encoding="utf-8")

