-- Run this in Supabase SQL Editor to create the competitor_intel table
-- Go to: Supabase Dashboard > SQL Editor > New Query

CREATE TABLE competitor_intel (
    id BIGSERIAL PRIMARY KEY,
    competitor TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    category TEXT DEFAULT 'Other',
    summary TEXT,
    shared_by TEXT,
    date_added DATE DEFAULT CURRENT_DATE,
    slack_link TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for faster URL duplicate checks
CREATE INDEX idx_competitor_intel_url ON competitor_intel(url);

-- Create index for faster date-based queries (for reports)
CREATE INDEX idx_competitor_intel_date ON competitor_intel(date_added);

-- Create index for competitor name searches
CREATE INDEX idx_competitor_intel_competitor ON competitor_intel(competitor);

-- Enable Row Level Security (optional but recommended)
ALTER TABLE competitor_intel ENABLE ROW LEVEL SECURITY;

-- Allow all operations for authenticated users (adjust as needed)
CREATE POLICY "Allow all access" ON competitor_intel
    FOR ALL
    USING (true)
    WITH CHECK (true);
