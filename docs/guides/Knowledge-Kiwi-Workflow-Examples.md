# Knowledge Kiwi Workflow Examples

## Overview

This document shows practical workflows for using Knowledge Kiwi tools in real scenarios. These examples demonstrate how the 5 core tools (`search`, `get`, `manage`, `link`, `help`) work together to build and maintain a knowledge base.

## Workflow 1: Creating Your First Knowledge Entry

**Scenario**: You just learned something new about email deliverability and want to save it.

### Step-by-Step

1. **Check if similar knowledge exists** (avoid duplicates):
```json
{
  "tool": "search",
  "params": {
    "query": "email deliverability SPF",
    "source": "local",
    "limit": 5
  }
}
```

**Response:**
```json
{
  "query": "email deliverability SPF",
  "source": "local",
  "results_count": 0,
  "results": []
}
```

2. **Create the entry** (stored locally in project):
```json
{
  "tool": "manage",
  "params": {
    "action": "create",
    "zettel_id": "042-email-deliverability",
    "title": "Email Deliverability Best Practices",
    "content": "# Email Deliverability Best Practices\n\nSPF records must include all sending IPs...",
    "entry_type": "pattern",
    "tags": ["email", "deliverability", "infrastructure"],
    "source_type": "experiment",
    "source_url": "https://example.com/test",
    "location": "project"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "action": "create",
  "zettel_id": "042-email-deliverability",
  "location": "project",
  "path": ".ai/knowledge/patterns/042-email-deliverability.md"
}
```

**Result**: Entry created at `.ai/knowledge/patterns/042-email-deliverability.md`

---

## Workflow 2: Searching Local Knowledge (Offline)

**Scenario**: You're working offline and need to find information about email setup.

### Step-by-Step

1. **Search local knowledge only** (fast, no network):
```json
{
  "tool": "search",
  "params": {
    "query": "email setup",
    "source": "local",
    "entry_type": "pattern",
    "limit": 10
  }
}
```

**Response:**
```json
{
  "query": "email setup",
  "source": "local",
  "results_count": 3,
  "results": [
    {
      "zettel_id": "042-email-deliverability",
      "title": "Email Deliverability Best Practices",
      "entry_type": "pattern",
      "tags": ["email", "deliverability"],
      "source_location": "project",
      "relevance_score": 0.92,
      "snippet": "SPF records must include all sending IPs..."
    },
    {
      "zettel_id": "043-spf-records",
      "title": "SPF Record Configuration",
      "entry_type": "pattern",
      "tags": ["email", "spf", "dns"],
      "source_location": "user",
      "relevance_score": 0.85,
      "snippet": "SPF records use TXT records in DNS..."
    }
  ]
}
```

**Key Points:**
- `source: "local"` searches both project and user space
- `source_location` shows where each entry was found
- No network calls - works offline

---

## Workflow 3: Finding Knowledge in Registry (Shared Knowledge)

**Scenario**: You want to see what others have learned about a topic.

### Step-by-Step

1. **Search registry for shared knowledge**:
```json
{
  "tool": "search",
  "params": {
    "query": "lead generation strategies",
    "source": "registry",
    "entry_type": "pattern",
    "limit": 10
  }
}
```

**Response:**
```json
{
  "query": "lead generation strategies",
  "source": "registry",
  "results_count": 5,
  "results": [
    {
      "zettel_id": "101-cold-outreach",
      "title": "Cold Outreach Best Practices",
      "entry_type": "pattern",
      "tags": ["lead-generation", "outreach"],
      "source_location": "registry",
      "relevance_score": 0.88,
      "snippet": "Personalization increases response rates by 3x..."
    }
  ]
}
```

2. **Download interesting entry to user space** (for offline access):
```json
{
  "tool": "get",
  "params": {
    "zettel_id": "101-cold-outreach",
    "source": "registry",
    "destination": "user"
  }
}
```

**Response:**
```json
{
  "zettel_id": "101-cold-outreach",
  "title": "Cold Outreach Best Practices",
  "content": "# Cold Outreach Best Practices\n\n...",
  "entry_type": "pattern",
  "tags": ["lead-generation", "outreach"],
  "source_location": "registry",
  "downloaded_to": "~/.knowledge-kiwi/patterns/101-cold-outreach.md"
}
```

**Result**: Entry now available locally in user space for future offline access.

---

## Workflow 4: Searching Both Local and Registry

**Scenario**: You want comprehensive results from both your local knowledge and shared registry.

### Step-by-Step

1. **Search both sources**:
```json
{
  "tool": "search",
  "params": {
    "query": "email authentication",
    "source": ["local", "registry"],
    "limit": 15
  }
}
```

**Response:**
```json
{
  "query": "email authentication",
  "source": ["local", "registry"],
  "results_count": 8,
  "results": [
    {
      "zettel_id": "042-email-deliverability",
      "title": "Email Deliverability Best Practices",
      "source_location": "project",  // Local result (prioritized)
      "relevance_score": 0.95
    },
    {
      "zettel_id": "043-spf-records",
      "title": "SPF Record Configuration",
      "source_location": "user",  // Local result
      "relevance_score": 0.90
    },
    {
      "zettel_id": "201-dkim-setup",
      "title": "DKIM Setup Guide",
      "source_location": "registry",  // Remote result
      "relevance_score": 0.88
    }
  ]
}
```

**Key Points:**
- Local results appear first (prioritized)
- Registry results follow
- `source_location` clearly indicates origin

---

## Workflow 5: Linking Related Knowledge

**Scenario**: You want to connect related entries to build a knowledge graph.

### Step-by-Step

1. **Get an entry with its relationships**:
```json
{
  "tool": "get",
  "params": {
    "zettel_id": "042-email-deliverability",
    "source": "local",
    "include_relationships": true,
    "include_backlinks": true
  }
}
```

**Response:**
```json
{
  "zettel_id": "042-email-deliverability",
  "title": "Email Deliverability Best Practices",
  "content": "...",
  "source_location": "project",
  "relationships": [
    {
      "zettel_id": "043-spf-records",
      "relationship_type": "references",
      "direction": "outgoing"
    }
  ],
  "backlinks": []
}
```

2. **Link to a related entry** (creates relationship):
```json
{
  "tool": "link",
  "params": {
    "action": "link",
    "from_zettel_id": "042-email-deliverability",
    "to_zettel_id": "044-dkim-setup",
    "relationship_type": "references"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "action": "link",
  "relationship": {
    "from_zettel_id": "042-email-deliverability",
    "to_zettel_id": "044-dkim-setup",
    "relationship_type": "references"
  }
}
```

3. **Create a collection** (group related entries):
```json
{
  "tool": "link",
  "params": {
    "action": "create_collection",
    "name": "Email Infrastructure",
    "description": "All entries about email setup and authentication",
    "zettel_ids": [
      "042-email-deliverability",
      "043-spf-records",
      "044-dkim-setup"
    ],
    "collection_type": "topic"
  }
}
```

**Result**: Related entries are now linked and grouped in a collection.

---

## Workflow 6: Updating Existing Knowledge

**Scenario**: You learned something new that updates an existing entry.

### Step-by-Step

1. **Get the current entry**:
```json
{
  "tool": "get",
  "params": {
    "zettel_id": "042-email-deliverability",
    "source": "local"
  }
}
```

2. **Update the entry** (adds new information):
```json
{
  "tool": "manage",
  "params": {
    "action": "update",
    "zettel_id": "042-email-deliverability",
    "content": "# Email Deliverability Best Practices\n\n## Original content...\n\n## New Learning (2025-01-20)\n\nDMARC policies should be set to 'quarantine' initially...",
    "tags": ["email", "deliverability", "infrastructure", "dmarc"]
  }
}
```

**Response:**
```json
{
  "status": "success",
  "action": "update",
  "zettel_id": "042-email-deliverability",
  "location": "project",
  "path": ".ai/knowledge/patterns/042-email-deliverability.md"
}
```

**Result**: Entry updated in place (resolver finds it automatically).

---

## Workflow 7: Publishing to Registry (Sharing Knowledge)

**Scenario**: You've refined a knowledge entry and want to share it with others.

### Step-by-Step

1. **Publish from project space to registry**:
```json
{
  "tool": "manage",
  "params": {
    "action": "publish",
    "zettel_id": "042-email-deliverability",
    "version": "1.1.0",
    "location": "project"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "action": "publish",
  "zettel_id": "042-email-deliverability",
  "version": "1.1.0",
  "published_to": "registry",
  "location": "project"
}
```

**Result**: Entry now available in registry for others to discover and download.

---

## Workflow 8: Integration with Script Kiwi (Complete Workflow)

**Scenario**: You're running a scraping workflow and want to store learnings.

### Context Kiwi Directive Example

```xml
<step name="scrape_leads">
  <tool_call>
    <mcp>script-kiwi</mcp>
    <tool>run</tool>
    <params>
      <script_name>google_maps_leads</script_name>
      <params>
        <search_term>dental clinic</search_term>
        <location>Texas</location>
      </params>
    </params>
  </tool_call>
</step>

<step name="check_knowledge">
  <tool_call>
    <mcp>knowledge-kiwi</mcp>
    <tool>search</tool>
    <params>
      <query>dental clinic lead generation</query>
      <source>local</source>
      <limit>5</limit>
    </params>
  </tool_call>
</step>

<step name="store_learning">
  <tool_call>
    <mcp>knowledge-kiwi</mcp>
    <tool>manage</tool>
    <params>
      <action>create</action>
      <zettel_id>045-dental-leads-texas</zettel_id>
      <title>Dental Clinic Lead Generation - Texas</title>
      <content># Dental Clinic Lead Generation - Texas\n\nScraped {step_1_output.count} leads...",
      <entry_type>learning</entry_type>
      <tags>["dental", "leads", "texas", "scraping"]</tags>
      <source_type>experiment</source_type>
      <location>project</location>
    </params>
  </tool_call>
</step>

<step name="link_to_pattern">
  <tool_call>
    <mcp>knowledge-kiwi</mcp>
    <tool>link</tool>
    <params>
      <action>link</action>
      <from_zettel_id>045-dental-leads-texas</from_zettel_id>
      <to_zettel_id>042-email-deliverability</to_zettel_id>
      <relationship_type>implements</relationship_type>
    </params>
  </tool_call>
</step>
```

**Flow:**
1. Script Kiwi scrapes leads
2. Knowledge Kiwi checks for existing knowledge
3. Knowledge Kiwi stores new learning
4. Knowledge Kiwi links to related pattern

---

## Workflow 9: Offline-First Development

**Scenario**: You're on a plane, working offline, building up local knowledge.

### Step-by-Step

1. **Create entries locally** (no network needed):
```json
{
  "tool": "manage",
  "params": {
    "action": "create",
    "zettel_id": "046-offline-pattern",
    "title": "Offline Development Pattern",
    "content": "...",
    "entry_type": "pattern",
    "location": "project"
  }
}
```

2. **Search local knowledge** (works offline):
```json
{
  "tool": "search",
  "params": {
    "query": "offline",
    "source": "local"
  }
}
```

3. **Link entries** (stored locally):
```json
{
  "tool": "link",
  "params": {
    "action": "link",
    "from_zettel_id": "046-offline-pattern",
    "to_zettel_id": "042-email-deliverability",
    "relationship_type": "related"
  }
}
```

**When back online:**
4. **Publish to registry** (share with team):
```json
{
  "tool": "manage",
  "params": {
    "action": "publish",
    "zettel_id": "046-offline-pattern",
    "location": "project"
  }
}
```

---

## Workflow 10: Getting Help

**Scenario**: You're new to Knowledge Kiwi and need guidance.

### Step-by-Step

1. **Get help on workflows**:
```json
{
  "tool": "help",
  "params": {
    "query": "how to create a knowledge entry",
    "context": "I'm new to Zettelkasten"
  }
}
```

**Response:**
```json
{
  "topic": "Creating Knowledge Entries",
  "workflow": [
    "1. Use search() to check for similar entries",
    "2. Use manage({'action': 'create', ...}) to create new entry",
    "3. Use link() to connect related entries",
    "4. Use manage({'action': 'publish', ...}) to share with team"
  ],
  "examples": [
    {
      "description": "Create a pattern entry",
      "code": "manage({'action': 'create', 'zettel_id': '042-email-deliverability', 'title': 'Email Deliverability', 'content': '# ...', 'entry_type': 'pattern'})"
    }
  ],
  "related_topics": ["searching", "linking", "publishing"]
}
```

---

## Common Patterns

### Pattern 1: Research Before Creating
```json
// 1. Search first
search({"query": "topic", "source": ["local", "registry"]})

// 2. If not found, create
manage({"action": "create", ...})

// 3. Link to related
link({"action": "link", ...})
```

### Pattern 2: Local Development → Publish
```json
// 1. Create locally
manage({"action": "create", "location": "project", ...})

// 2. Refine and update
manage({"action": "update", ...})

// 3. Publish when ready
manage({"action": "publish", ...})
```

### Pattern 3: Discover → Download → Use
```json
// 1. Search registry
search({"query": "topic", "source": "registry"})

// 2. Get and download
get({"zettel_id": "...", "source": "registry", "destination": "user"})

// 3. Now available locally
get({"zettel_id": "...", "source": "local"})
```

---

## Key Takeaways

1. **Explicit Source Selection**: Always specify `source: "local"`, `source: "registry"`, or `source: ["local", "registry"]`
2. **Offline-First**: `source: "local"` works offline, no network needed
3. **Transparency**: `source_location` always shows where knowledge came from
4. **Workflow Integration**: Knowledge Kiwi tools work seamlessly with Script Kiwi in directives
5. **Progressive Enhancement**: Start local, publish when ready, download what you need

