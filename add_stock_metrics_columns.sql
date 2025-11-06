-- Add YTD metrics columns to stocks table
-- Run this in Supabase SQL Editor before running update_stock_metrics.py

-- Add YTD return percentage column
ALTER TABLE stocks
ADD COLUMN IF NOT EXISTS ytd_return DECIMAL(10, 4);

-- Add current price column (most recent closing price)
ALTER TABLE stocks
ADD COLUMN IF NOT EXISTS current_price DECIMAL(12, 4);

-- Add first price in 2025 column
ALTER TABLE stocks
ADD COLUMN IF NOT EXISTS first_price_2025 DECIMAL(12, 4);

-- Add timestamp for when prices were last updated
ALTER TABLE stocks
ADD COLUMN IF NOT EXISTS price_updated_at TIMESTAMP WITH TIME ZONE;

-- Create index for faster queries on ytd_return (for sorting by performance)
CREATE INDEX IF NOT EXISTS idx_stocks_ytd_return ON stocks(ytd_return DESC);

-- Add comments for documentation
COMMENT ON COLUMN stocks.ytd_return IS 'Year-to-date return percentage';
COMMENT ON COLUMN stocks.current_price IS 'Most recent closing price in CAD';
COMMENT ON COLUMN stocks.first_price_2025 IS 'First closing price in 2025';
COMMENT ON COLUMN stocks.price_updated_at IS 'Timestamp of last price update';
