# MCP Delete Functionality Examples

This document shows how to use the delete functionality via MCP tool calls.

## MCP Tool: `manage` with `action: "delete"`

### Example 1: Delete from Local (Project Space Only)

```json
{
  "name": "manage",
  "arguments": {
    "action": "delete",
    "zettel_id": "042-email-deliverability",
    "source": "local",
    "location": "project",
    "confirm": true
  }
}
```

**Response:**
```json
{
  "status": "success",
  "action": "delete",
  "zettel_id": "042-email-deliverability",
  "deleted_from": {
    "local": ["project"],
    "registry": false
  }
}
```

### Example 2: Delete from Local (User Space Only)

```json
{
  "name": "manage",
  "arguments": {
    "action": "delete",
    "zettel_id": "042-email-deliverability",
    "source": "local",
    "location": "user",
    "confirm": true
  }
}
```

### Example 3: Delete from Local (Both Project and User)

When `source: "local"` and no `location` specified, it tries to delete from both:

```json
{
  "name": "manage",
  "arguments": {
    "action": "delete",
    "zettel_id": "042-email-deliverability",
    "source": "local",
    "confirm": true
  }
}
```

**Response:**
```json
{
  "status": "success",
  "action": "delete",
  "zettel_id": "042-email-deliverability",
  "deleted_from": {
    "local": ["project", "user"],
    "registry": false
  }
}
```

### Example 4: Delete from Registry

```json
{
  "name": "manage",
  "arguments": {
    "action": "delete",
    "zettel_id": "042-email-deliverability",
    "source": "registry",
    "confirm": true
  }
}
```

**Response:**
```json
{
  "status": "success",
  "action": "delete",
  "zettel_id": "042-email-deliverability",
  "deleted_from": {
    "local": [],
    "registry": true
  }
}
```

### Example 5: Delete from Registry with Relationships

If the entry has relationships, you need `cascade_relationships: true`:

```json
{
  "name": "manage",
  "arguments": {
    "action": "delete",
    "zettel_id": "042-email-deliverability",
    "source": "registry",
    "cascade_relationships": true,
    "confirm": true
  }
}
```

**Response:**
```json
{
  "status": "success",
  "action": "delete",
  "zettel_id": "042-email-deliverability",
  "deleted_from": {
    "local": [],
    "registry": true
  },
  "relationships_deleted": 3
}
```

### Example 6: Delete from All Three Tiers

```json
{
  "name": "manage",
  "arguments": {
    "action": "delete",
    "zettel_id": "042-email-deliverability",
    "source": ["local", "registry"],
    "confirm": true
  }
}
```

**Response:**
```json
{
  "status": "success",
  "action": "delete",
  "zettel_id": "042-email-deliverability",
  "deleted_from": {
    "local": ["project", "user"],
    "registry": true
  }
}
```

### Example 7: Backward Compatible (No Source)

The old API still works (defaults to `source: "local"`):

```json
{
  "name": "manage",
  "arguments": {
    "action": "delete",
    "zettel_id": "042-email-deliverability",
    "confirm": true
  }
}
```

## Error Responses

### Missing Confirmation

```json
{
  "name": "manage",
  "arguments": {
    "action": "delete",
    "zettel_id": "042-email-deliverability",
    "source": "local",
    "confirm": false
  }
}
```

**Response:**
```json
{
  "error": "confirm: true is required for delete"
}
```

### Relationships Exist (Registry)

```json
{
  "name": "manage",
  "arguments": {
    "action": "delete",
    "zettel_id": "042-email-deliverability",
    "source": "registry",
    "confirm": true
  }
}
```

**Response:**
```json
{
  "status": "error",
  "action": "delete",
  "zettel_id": "042-email-deliverability",
  "errors": {
    "registry": "Cannot delete entry: 3 relationship(s) exist. Set cascade_relationships: true to delete relationships first."
  }
}
```

### Partial Success

If deleting from multiple tiers and one fails:

```json
{
  "status": "partial",
  "action": "delete",
  "zettel_id": "042-email-deliverability",
  "deleted_from": {
    "local": ["project"],
    "registry": false
  },
  "errors": {
    "registry": "Entry '042-email-deliverability' not found in registry"
  }
}
```

## Complete Workflow Example

1. **Create entry:**
```json
{
  "name": "manage",
  "arguments": {
    "action": "create",
    "zettel_id": "042-test-delete",
    "title": "Test Entry",
    "content": "# Test\n\nContent",
    "entry_type": "pattern",
    "location": "project"
  }
}
```

2. **Publish to registry:**
```json
{
  "name": "manage",
  "arguments": {
    "action": "publish",
    "zettel_id": "042-test-delete",
    "location": "project"
  }
}
```

3. **Delete from all tiers:**
```json
{
  "name": "manage",
  "arguments": {
    "action": "delete",
    "zettel_id": "042-test-delete",
    "source": ["local", "registry"],
    "confirm": true
  }
}
```

