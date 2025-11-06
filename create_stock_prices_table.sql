-- Create stock_prices table for storing historical price data
-- Run this in Supabase SQL Editor before running fetch_stock_prices.py

CREATE TABLE IF NOT EXISTS stock_prices (
    id BIGSERIAL PRIMARY KEY,
    company_id BIGINT NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    close_price DECIMAL(12, 4) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Ensure one price per company per day
    CONSTRAINT unique_company_date UNIQUE (company_id, date)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_stock_prices_company_id ON stock_prices(company_id);
CREATE INDEX IF NOT EXISTS idx_stock_prices_date ON stock_prices(date);
CREATE INDEX IF NOT EXISTS idx_stock_prices_company_date ON stock_prices(company_id, date);

-- Add comment for documentation
COMMENT ON TABLE stock_prices IS 'Historical daily closing prices for stocks';
COMMENT ON COLUMN stock_prices.company_id IS 'Foreign key to stocks table';
COMMENT ON COLUMN stock_prices.date IS 'Trading date';
COMMENT ON COLUMN stock_prices.close_price IS 'Closing price in CAD';
