-- =====================================================================
-- InvestMatch User Tracking Schema
-- =====================================================================
-- This schema tracks user interactions with stocks in the InvestMatch app:
-- - user_swipes: Records every left/right swipe on stocks
-- - user_watchlist: Stores stocks users want to monitor
--
-- Run this in Supabase SQL Editor to set up user tracking
-- =====================================================================

-- =====================================================================
-- TABLE: user_swipes
-- =====================================================================
-- Tracks every swipe action (left = pass, right = like) for each user
-- Swipes are permanent - users cannot modify their swipe history
-- =====================================================================

CREATE TABLE IF NOT EXISTS user_swipes (
    id BIGSERIAL PRIMARY KEY,

    -- Foreign key to Supabase Auth user
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Foreign key to stock being swiped
    company_id BIGINT NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,

    -- Direction of swipe: 'left' (pass) or 'right' (like)
    swipe_direction TEXT NOT NULL CHECK (swipe_direction IN ('left', 'right')),

    -- Timestamp of when swipe occurred
    swiped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Prevent duplicate swipes on same stock
    CONSTRAINT unique_user_company_swipe UNIQUE (user_id, company_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_swipes_user_id ON user_swipes(user_id);
CREATE INDEX IF NOT EXISTS idx_user_swipes_company_id ON user_swipes(company_id);
CREATE INDEX IF NOT EXISTS idx_user_swipes_user_company ON user_swipes(user_id, company_id);
CREATE INDEX IF NOT EXISTS idx_user_swipes_swiped_at ON user_swipes(user_id, swiped_at DESC);

-- Add helpful comment
COMMENT ON TABLE user_swipes IS 'Tracks all user swipe actions on stocks (left=pass, right=like)';
COMMENT ON COLUMN user_swipes.swipe_direction IS 'Either ''left'' (pass) or ''right'' (like)';

-- =====================================================================
-- TABLE: user_watchlist
-- =====================================================================
-- Stores stocks that users want to monitor (typically from right swipes)
-- Users can add notes and manage their watchlist
-- =====================================================================

CREATE TABLE IF NOT EXISTS user_watchlist (
    id BIGSERIAL PRIMARY KEY,

    -- Foreign key to Supabase Auth user
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Foreign key to stock in watchlist
    company_id BIGINT NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,

    -- When stock was added to watchlist
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Optional user notes about this stock
    notes TEXT,

    -- Prevent duplicate entries in watchlist
    CONSTRAINT unique_user_company_watchlist UNIQUE (user_id, company_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_watchlist_user_id ON user_watchlist(user_id);
CREATE INDEX IF NOT EXISTS idx_user_watchlist_company_id ON user_watchlist(company_id);
CREATE INDEX IF NOT EXISTS idx_user_watchlist_added_at ON user_watchlist(user_id, added_at DESC);

-- Add helpful comment
COMMENT ON TABLE user_watchlist IS 'Stores stocks users are actively monitoring';
COMMENT ON COLUMN user_watchlist.notes IS 'Optional user notes about why they are watching this stock';

-- =====================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =====================================================================
-- Ensures users can only access their own data
-- =====================================================================

-- Enable RLS on both tables
ALTER TABLE user_swipes ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_watchlist ENABLE ROW LEVEL SECURITY;

-- =====================================================================
-- RLS POLICIES: user_swipes
-- =====================================================================

-- Policy: Users can view their own swipes
CREATE POLICY "Users can view their own swipes"
    ON user_swipes
    FOR SELECT
    USING (auth.uid() = user_id);

-- Policy: Users can insert their own swipes
CREATE POLICY "Users can insert their own swipes"
    ON user_swipes
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Note: No UPDATE or DELETE policies - swipes are permanent

-- =====================================================================
-- RLS POLICIES: user_watchlist
-- =====================================================================

-- Policy: Users can view their own watchlist
CREATE POLICY "Users can view their own watchlist"
    ON user_watchlist
    FOR SELECT
    USING (auth.uid() = user_id);

-- Policy: Users can add to their own watchlist
CREATE POLICY "Users can insert into their own watchlist"
    ON user_watchlist
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Policy: Users can update their own watchlist items (e.g., edit notes)
CREATE POLICY "Users can update their own watchlist"
    ON user_watchlist
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Policy: Users can delete from their own watchlist
CREATE POLICY "Users can delete from their own watchlist"
    ON user_watchlist
    FOR DELETE
    USING (auth.uid() = user_id);

-- =====================================================================
-- HELPER FUNCTIONS
-- =====================================================================

-- =====================================================================
-- FUNCTION: get_user_swipe_stats
-- =====================================================================
-- Returns swipe statistics for a user
-- Usage: SELECT * FROM get_user_swipe_stats('user-uuid-here');
-- =====================================================================

CREATE OR REPLACE FUNCTION get_user_swipe_stats(user_uuid UUID)
RETURNS TABLE (
    total_swipes BIGINT,
    left_swipes BIGINT,
    right_swipes BIGINT,
    swipe_rate NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::BIGINT as total_swipes,
        COUNT(*) FILTER (WHERE swipe_direction = 'left')::BIGINT as left_swipes,
        COUNT(*) FILTER (WHERE swipe_direction = 'right')::BIGINT as right_swipes,
        CASE
            WHEN COUNT(*) > 0 THEN
                ROUND((COUNT(*) FILTER (WHERE swipe_direction = 'right')::NUMERIC / COUNT(*)::NUMERIC) * 100, 2)
            ELSE 0
        END as swipe_rate
    FROM user_swipes
    WHERE user_id = user_uuid;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_user_swipe_stats IS 'Returns swipe statistics for a user (total, left, right, and like rate)';

-- =====================================================================
-- FUNCTION: get_unswiped_stocks
-- =====================================================================
-- Returns stocks that user hasn't swiped on yet
-- Usage: SELECT * FROM get_unswiped_stocks('user-uuid-here') LIMIT 10;
-- =====================================================================

CREATE OR REPLACE FUNCTION get_unswiped_stocks(user_uuid UUID)
RETURNS TABLE (
    id BIGINT,
    ticker TEXT,
    name TEXT,
    sector TEXT,
    market_cap NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.id,
        s.ticker,
        s.name,
        s.sector,
        s.market_cap
    FROM stocks s
    WHERE s.id NOT IN (
        SELECT company_id
        FROM user_swipes
        WHERE user_id = user_uuid
    )
    ORDER BY s.market_cap DESC NULLS LAST;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_unswiped_stocks IS 'Returns all stocks that a user has not swiped on yet';

-- =====================================================================
-- FUNCTION: add_to_watchlist_from_swipe
-- =====================================================================
-- Automatically adds stock to watchlist when user swipes right
-- Usage: SELECT add_to_watchlist_from_swipe('user-uuid', 123);
-- =====================================================================

CREATE OR REPLACE FUNCTION add_to_watchlist_from_swipe(user_uuid UUID, company_bigint BIGINT)
RETURNS BOOLEAN AS $$
BEGIN
    -- Insert into watchlist if not already there
    INSERT INTO user_watchlist (user_id, company_id)
    VALUES (user_uuid, company_bigint)
    ON CONFLICT (user_id, company_id) DO NOTHING;

    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION add_to_watchlist_from_swipe IS 'Adds a stock to user watchlist (called after right swipe)';

-- =====================================================================
-- FUNCTION: remove_from_watchlist
-- =====================================================================
-- Removes a stock from user's watchlist
-- Usage: SELECT remove_from_watchlist('user-uuid', 123);
-- =====================================================================

CREATE OR REPLACE FUNCTION remove_from_watchlist(user_uuid UUID, company_bigint BIGINT)
RETURNS BOOLEAN AS $$
DECLARE
    rows_deleted INTEGER;
BEGIN
    DELETE FROM user_watchlist
    WHERE user_id = user_uuid AND company_id = company_bigint;

    GET DIAGNOSTICS rows_deleted = ROW_COUNT;
    RETURN rows_deleted > 0;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION remove_from_watchlist IS 'Removes a stock from user watchlist';

-- =====================================================================
-- COMPLETE!
-- =====================================================================
-- Tables, indexes, RLS policies, and helper functions created
-- Next steps:
-- 1. Verify tables exist: \dt user_*
-- 2. Test RLS policies with test user
-- 3. Run test_user_tracking.py to validate functionality
-- =====================================================================
