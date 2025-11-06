# Stock Analysis Toolkit

A complete Python toolkit for fetching, analyzing, and visualizing TSX stock performance.

## Scripts Overview

### 1. **fetch_stock_prices.py**
Fetches year-to-date (YTD) closing prices for all TSX stocks and stores them in Supabase.

**What it does:**
- Reads all tickers from the `stocks` table
- Fetches daily closing prices from Yahoo Finance (2025 YTD)
- Stores price data in `stock_prices` table
- Uses batch upserts for efficiency

**Usage:**
```bash
python fetch_stock_prices.py
```

**Output:**
```
Fetching stocks from Supabase...
✅ Found 60 stocks in database

[1/60] Fetching SHOP...
  ✅ Fetched 3 price points for SHOP
...
```

---

### 2. **update_stock_metrics.py**
Calculates and updates YTD performance metrics for all stocks.

**What it does:**
- Reads price data from `stock_prices` table
- Calculates YTD return percentage for each stock
- Updates `stocks` table with:
  - `ytd_return`: YTD return percentage
  - `current_price`: Most recent closing price
  - `first_price_2025`: First closing price in 2025
  - `price_updated_at`: Update timestamp
- Shows top 5 and bottom 5 performers

**Usage:**
```bash
python update_stock_metrics.py
```

**Output:**
```
[1/60] SHOP... ✅ YTD: +15.3% | Price: $138.50 (2025-01-02 → 2025-01-05)
...

Top 5 Performers:
Rank   Ticker     YTD Return    Current Price
--------------------------------------------------
1      SHOP       +15.30%       $138.50
2      RY         +8.45%        $142.25
...

Average YTD return: +5.23%
```

---

### 3. **visualize_stock_performance.py**
Generates beautiful YTD performance charts for any stock ticker.

**What it does:**
- Accepts ticker symbol as command-line argument
- Queries stock info and price data from Supabase
- Creates professional line chart with:
  - Green line for positive YTD, red for negative
  - Semi-transparent fill under the curve
  - Reference line at starting price
  - Data point markers every 2 weeks
  - Formatted currency and dates
- Saves chart as PNG in `charts/` directory
- Displays chart in window

**Usage:**
```bash
python visualize_stock_performance.py SHOP
python visualize_stock_performance.py RY
```

**Output:**
```
✅ Generated chart: charts/SHOP_ytd_chart.png
📈 SHOP: $138.50 | YTD Return: +15.3%
```

---

### 4. **visualize_all_stocks.py**
Generates YTD performance charts for ALL stocks in the database at once.

**What it does:**
- Queries all stocks from `stocks` table
- Fetches 2025 price data for each stock
- Creates professional line charts for each (10x5 inches)
- Saves all charts to `charts/` directory
- Skips stocks with insufficient data (< 5 price points)
- Prints summary report with average YTD return

**Usage:**
```bash
python visualize_all_stocks.py
```

**Output:**
```
Generating charts for 59 stocks...

[1/59] SHOP... ✅ +15.3%
[2/59] RY... ✅ +8.5%
[3/59] TD... ✅ -2.1%
[4/59] ABC... ⚠️  Insufficient data (skipped)
...

Summary:
Total stocks: 59
Charts generated: 56
Skipped (insufficient data): 3
Failed (errors): 0

📊 Average YTD return: +5.23%
📁 Charts saved to: C:\Users\j.shaw\apps\charts\
```

---

### 5. **upload_charts_to_supabase.py**
Uploads all generated chart images to Supabase Storage and updates the database with public URLs.

**What it does:**
- Reads all stocks from `stocks` table
- Uploads each chart PNG to Supabase Storage bucket 'stock-charts'
- Gets public URL for each uploaded image
- Updates `stocks` table with `chart_image_url` column
- Creates bucket if it doesn't exist
- Shows progress for each upload

**Usage:**
```bash
# First, run the SQL to add the column
# Then run the upload script
python upload_charts_to_supabase.py
```

**Output:**
```
✅ Bucket 'stock-charts' already exists

Uploading charts...

[1/59] SHOP... ✅ Uploaded
[2/59] RY... ✅ Uploaded
[3/59] TD... ✅ Uploaded
[4/59] ABC... ⚠️  Chart file not found (skipped)
...

Summary:
Total stocks: 59
Charts uploaded: 56
Skipped (no chart file): 3
Failed (upload/update errors): 0

✅ Charts available at: https://your-project.supabase.co/storage/v1/object/public/stock-charts/
```

---

## Setup Instructions

### 1. Database Setup

Run these SQL files in your Supabase SQL Editor:

```sql
-- Create stock_prices table
-- File: create_stock_prices_table.sql
```

```sql
-- Add metrics columns to stocks table
-- File: add_stock_metrics_columns.sql
```

```sql
-- Add chart_image_url column to stocks table
-- File: add_chart_image_url_column.sql
```

### 2. Environment Variables

Ensure your `.env` file contains:
```
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

### 3. Install Dependencies

```bash
pip install yfinance pandas supabase python-dotenv matplotlib seaborn
```

---

## Complete Workflow

Follow these steps to set up and use the complete stock analysis system:

### Step 1: Fetch Stock Prices
```bash
python fetch_stock_prices.py
```
- Fetches YTD prices from Yahoo Finance
- Populates `stock_prices` table
- Run this daily to keep data current

### Step 2: Update Metrics
```bash
python update_stock_metrics.py
```
- Calculates YTD returns
- Updates `stocks` table with metrics
- Shows performance summary
- Run after fetching new prices

### Step 3: Visualize Performance

**Option A: Generate charts for specific stocks**
```bash
python visualize_stock_performance.py SHOP
python visualize_stock_performance.py RY
python visualize_stock_performance.py TD
```
- Creates charts for individual tickers
- Displays chart in window
- Great for quick analysis

**Option B: Generate charts for ALL stocks**
```bash
python visualize_all_stocks.py
```
- Batch generates charts for entire portfolio
- No display windows (faster)
- Perfect for reports or dashboards

### Step 4: Upload Charts to Cloud Storage (Optional)
```bash
python upload_charts_to_supabase.py
```
- Uploads all chart images to Supabase Storage
- Updates database with public image URLs
- Makes charts accessible via URLs in your app
- Run after generating charts

---

## Database Schema

### stocks table
```sql
- id (bigint, primary key)
- ticker (text)
- name (text)
- ytd_return (decimal)
- current_price (decimal)
- first_price_2025 (decimal)
- price_updated_at (timestamp)
- chart_image_url (text) -- Public URL to chart in Supabase Storage
```

### stock_prices table
```sql
- id (bigserial, primary key)
- company_id (bigint, foreign key → stocks.id)
- date (date)
- close_price (decimal)
- UNIQUE constraint on (company_id, date)
```

---

## Error Handling

All scripts include comprehensive error handling:
- ✅ Missing data gracefully skipped
- ✅ Invalid tickers reported
- ✅ Database connection errors caught
- ✅ Helpful error messages printed

---

## Output Examples

### Chart Features
- **Clean, modern design** using seaborn darkgrid style
- **Color-coded performance**: Green (positive), Red (negative)
- **Professional formatting**: Currency symbols, month names
- **Reference lines**: Shows starting price for context
- **Key metrics displayed**: Current price and YTD return
- **High resolution**: 150 DPI for crisp output

### File Structure
```
apps/
├── fetch_stock_prices.py
├── update_stock_metrics.py
├── visualize_stock_performance.py
├── visualize_all_stocks.py
├── upload_charts_to_supabase.py
├── create_stock_prices_table.sql
├── add_stock_metrics_columns.sql
├── add_chart_image_url_column.sql
└── charts/
    ├── SHOP_ytd_chart.png
    ├── RY_ytd_chart.png
    ├── TD_ytd_chart.png
    ├── BNS_ytd_chart.png
    └── ... (all stock charts)
```

---

## Automation Tips

### Daily Updates (Cron Job)
```bash
# Run daily at 6 PM EST (after market close)
0 18 * * 1-5 cd /path/to/apps && python fetch_stock_prices.py && python update_stock_metrics.py
```

### Batch Chart Generation

**Option 1: Generate ALL charts at once**
```bash
# Generate charts for every stock in database
python visualize_all_stocks.py
```

**Option 2: Generate charts for specific tickers**
```bash
# Generate charts for selected stocks
for ticker in SHOP RY TD BNS BMO; do
    python visualize_stock_performance.py $ticker
done
```

**Option 3: Full daily automation with charts**
```bash
# Complete daily update (prices + metrics + charts)
python fetch_stock_prices.py && python update_stock_metrics.py && python visualize_all_stocks.py
```

**Option 4: Full automation with cloud storage**
```bash
# Complete daily update with cloud storage upload
python fetch_stock_prices.py && python update_stock_metrics.py && python visualize_all_stocks.py && python upload_charts_to_supabase.py
```

---

## Troubleshooting

**No price data found:**
- Run `fetch_stock_prices.py` first to populate data

**Ticker not found:**
- Ensure ticker exists in `stocks` table
- Check ticker spelling (case-insensitive)

**Charts not displaying:**
- Install `python-tk`: `sudo apt install python3-tk` (Linux)
- Charts still save to file even if display fails

**Rate limiting errors:**
- Scripts include built-in delays
- Yahoo Finance has rate limits; run during off-peak hours

**Upload to Supabase Storage fails:**
- Ensure bucket 'stock-charts' exists or script will create it
- Verify SUPABASE_SERVICE_ROLE_KEY has storage permissions
- Check Supabase Storage quota hasn't been exceeded
- Run `add_chart_image_url_column.sql` before uploading

**Chart images not accessible:**
- Ensure bucket is set to public in Supabase Storage settings
- Check file permissions in Supabase dashboard
- Verify URLs in database are complete and correct

---

## Next Steps

1. ✅ Set up database tables (run SQL files)
2. ✅ Fetch initial price data
3. ✅ Calculate metrics
4. ✅ Generate your first chart
5. ✅ Upload charts to Supabase Storage
6. 🔄 Set up daily automation
7. 📊 Build a dashboard using the data
8. 📱 Integrate chart URLs into your mobile app
