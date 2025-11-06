-- Add chart_image_url column to stocks table
-- Run this in Supabase SQL Editor before running upload_charts_to_supabase.py

ALTER TABLE stocks ADD COLUMN IF NOT EXISTS chart_image_url TEXT;

-- Add comment for documentation
COMMENT ON COLUMN stocks.chart_image_url IS 'Public URL to YTD chart image in Supabase Storage';

-- Optional: Create index if you'll be querying by this column
CREATE INDEX IF NOT EXISTS idx_stocks_chart_image_url ON stocks(chart_image_url) WHERE chart_image_url IS NOT NULL;
