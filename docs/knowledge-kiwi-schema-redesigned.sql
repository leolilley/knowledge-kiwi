-- ============================================
-- KNOWLEDGE KIWI DATABASE SCHEMA (REDESIGNED)
-- Registry tier only - no sync, no embeddings
-- ============================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- Fuzzy text search

-- ==========================================
-- KNOWLEDGE ENTRIES (Registry)
-- ==========================================
CREATE TABLE knowledge_entries (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Zettelkasten ID
    zettel_id text UNIQUE NOT NULL,  -- e.g., "042-email-deliverability"
    
    -- Content
    title text NOT NULL,
    content text NOT NULL,
    
    -- Categorization
    entry_type text NOT NULL CHECK (entry_type IN (
        'api_fact',      -- API documentation snippets
        'pattern',       -- Reusable patterns
        'concept',       -- Mental models
        'learning',      -- Things you've learned
        'experiment',    -- Experiment results
        'reference',     -- Quick reference notes
        'template',      -- Code/content templates
        'workflow'       -- Process documentation
    )),
    category text,  -- Dynamic category path (e.g., "email-infrastructure/smtp")
    
    -- Source tracking
    source_type text CHECK (source_type IN (
        'youtube',
        'docs',
        'experiment',
        'manual',
        'chat',
        'book',
        'article',
        'course'
    )),
    source_url text,
    
    -- Tags
    tags text[] DEFAULT '{}',
    
    -- Versioning
    version text DEFAULT '1.0.0',  -- Semver versioning
    
    -- Full-text search
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english', title || ' ' || content)
    ) STORED,
    
    -- Metadata
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

-- Indexes
CREATE INDEX idx_knowledge_search ON knowledge_entries USING GIN(search_vector);
CREATE INDEX idx_knowledge_tags ON knowledge_entries USING GIN(tags);
CREATE INDEX idx_knowledge_zettel_id ON knowledge_entries(zettel_id);
CREATE INDEX idx_knowledge_entry_type ON knowledge_entries(entry_type);
CREATE INDEX idx_knowledge_category ON knowledge_entries(category);
CREATE INDEX idx_knowledge_updated_at ON knowledge_entries(updated_at DESC);

-- ==========================================
-- KNOWLEDGE RELATIONSHIPS
-- ==========================================
CREATE TABLE knowledge_relationships (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    from_zettel_id text NOT NULL REFERENCES knowledge_entries(zettel_id) ON DELETE CASCADE,
    to_zettel_id text NOT NULL REFERENCES knowledge_entries(zettel_id) ON DELETE CASCADE,
    
    relationship_type text NOT NULL CHECK (relationship_type IN (
        'references',    -- A → B: A mentions B
        'contradicts',   -- A ⊗ B: A disagrees with B
        'extends',       -- A ⊃ B: A builds on B
        'implements',    -- A ⇒ B: A is implementation of B concept
        'supersedes',    -- A ↦ B: A replaces B
        'depends_on',    -- A → B: A requires B
        'related',       -- A ↔ B: General relationship
        'example_of'     -- A is example of B
    )),
    
    created_at timestamptz DEFAULT now(),
    
    -- Prevent duplicate relationships
    UNIQUE(from_zettel_id, to_zettel_id, relationship_type)
);

CREATE INDEX idx_relationships_from ON knowledge_relationships(from_zettel_id);
CREATE INDEX idx_relationships_to ON knowledge_relationships(to_zettel_id);

-- ==========================================
-- KNOWLEDGE COLLECTIONS
-- ==========================================
CREATE TABLE knowledge_collections (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    name text NOT NULL,
    description text,
    collection_type text NOT NULL CHECK (collection_type IN (
        'topic',         -- Related by topic
        'project',       -- Project-specific
        'learning_path', -- Sequential learning
        'reference',     -- Quick reference
        'archive'        -- Archived entries
    )),
    zettel_ids text[] DEFAULT '{}',  -- Array of zettel_ids
    
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

CREATE INDEX idx_collections_type ON knowledge_collections(collection_type);
CREATE INDEX idx_collections_zettel_ids ON knowledge_collections USING GIN(zettel_ids);

-- ==========================================
-- FULL-TEXT SEARCH FUNCTION
-- ==========================================
CREATE OR REPLACE FUNCTION search_knowledge_fulltext(
    search_query text,
    match_count integer DEFAULT 10,
    filter_entry_type text DEFAULT NULL,
    filter_tags text[] DEFAULT NULL
)
RETURNS TABLE (
    zettel_id text,
    title text,
    content text,
    entry_type text,
    tags text[],
    relevance_score numeric,
    snippet text
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ke.zettel_id,
        ke.title,
        ke.content,
        ke.entry_type,
        ke.tags,
        ts_rank(ke.search_vector, plainto_tsquery('english', search_query))::numeric AS relevance_score,
        ts_headline('english', ke.content, plainto_tsquery('english', search_query), 'MaxWords=50') AS snippet
    FROM knowledge_entries ke
    WHERE ke.search_vector @@ plainto_tsquery('english', search_query)
        AND (filter_entry_type IS NULL OR ke.entry_type = filter_entry_type)
        AND (filter_tags IS NULL OR ke.tags && filter_tags)
    ORDER BY relevance_score DESC
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- ROW LEVEL SECURITY (RLS)
-- ==========================================
ALTER TABLE knowledge_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_relationships ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_collections ENABLE ROW LEVEL SECURITY;

-- Public read access (for registry entries)
CREATE POLICY "Public read access" ON knowledge_entries
    FOR SELECT
    USING (true);

-- Authenticated users can create/update/delete their own entries
CREATE POLICY "Users can manage entries" ON knowledge_entries
    FOR ALL
    USING (true);  -- Simplified for now - can add user_id checks later

CREATE POLICY "Public read relationships" ON knowledge_relationships
    FOR SELECT
    USING (true);

CREATE POLICY "Users can manage relationships" ON knowledge_relationships
    FOR ALL
    USING (true);

CREATE POLICY "Public read collections" ON knowledge_collections
    FOR SELECT
    USING (true);

CREATE POLICY "Users can manage collections" ON knowledge_collections
    FOR ALL
    USING (true);

