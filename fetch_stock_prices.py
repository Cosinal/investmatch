"""
Fetch YTD stock prices for TSX companies and store in Supabase.

Database Schema Required:
- stocks table: id (bigint), ticker (text)
- stock_prices table:
    - id (bigserial, primary key)
    - company_id (bigint, foreign key to stocks.id)
    - date (date)
    - close_price (decimal/numeric)
    - UNIQUE constraint on (company_id, date)
"""

import os
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import time

import yfinance as yf
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv

# ---------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Constants
YTD_START_DATE = "2025-01-01"
TODAY = date.today().strftime("%Y-%m-%d")
BATCH_SIZE = 100  # Number of price records to upsert at once

# ---------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------

def get_all_stocks() -> List[Dict[str, Any]]:
    """
    Fetch all stocks from Supabase stocks table.
    Returns list of dicts with 'id' and 'ticker' keys.
    """
    print("Fetching stocks from Supabase...")

    response = supabase.table("stocks").select("id, ticker").execute()
    stocks = response.data

    print(f"✅ Found {len(stocks)} stocks in database")
    return stocks


def fetch_price_data(ticker: str, start_date: str, end_date: str) -> Optional[List[Dict[str, Any]]]:
    """
    Fetch historical price data from Yahoo Finance.

    Args:
        ticker: Stock ticker (e.g., 'SHOP')
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        List of dicts with 'date' and 'close' keys, or None if fetch fails
    """
    # Add .TO suffix for TSX tickers
    yahoo_ticker = f"{ticker}.TO"

    try:
        stock = yf.Ticker(yahoo_ticker)
        history = stock.history(start=start_date, end=end_date, interval="1d")

        if history.empty:
            print(f"  ⚠️  No data returned for {yahoo_ticker}")
            return None

        # Convert to list of dicts
        price_data = []
        for timestamp, row in history.iterrows():
            close_price = row.get("Close")
            if close_price is not None and not pd.isna(close_price):
                price_data.append({
                    "date": timestamp.strftime("%Y-%m-%d"),
                    "close": float(close_price)
                })

        return price_data if price_data else None

    except Exception as e:
        print(f"  ❌ Error fetching data for {yahoo_ticker}: {e}")
        return None


def batch_upsert_prices(price_records: List[Dict[str, Any]]) -> None:
    """
    Upsert price records to Supabase in batches.

    Args:
        price_records: List of dicts with 'company_id', 'date', 'close_price' keys
    """
    if not price_records:
        return

    total_records = len(price_records)
    print(f"Upserting {total_records} price records in batches of {BATCH_SIZE}...")

    for i in range(0, total_records, BATCH_SIZE):
        batch = price_records[i:i + BATCH_SIZE]

        try:
            supabase.table("stock_prices").upsert(
                batch,
                on_conflict="company_id,date"
            ).execute()

            print(f"  ✅ Upserted batch {i // BATCH_SIZE + 1} ({len(batch)} records)")

        except Exception as e:
            print(f"  ❌ Error upserting batch {i // BATCH_SIZE + 1}: {e}")
            continue


# ---------------------------------------------------------------------
# Main Function
# ---------------------------------------------------------------------

def fetch_ytd_prices():
    """
    Main function to fetch YTD stock prices and store in Supabase.
    """
    print(f"\n{'='*70}")
    print(f"Fetching YTD Stock Prices ({YTD_START_DATE} to {TODAY})")
    print(f"{'='*70}\n")

    # Get all stocks from database
    stocks = get_all_stocks()

    if not stocks:
        print("No stocks found in database. Exiting.")
        return

    # Track statistics
    successful_count = 0
    failed_count = 0
    total_price_records = 0
    all_price_records = []

    print(f"\nFetching price data for {len(stocks)} stocks...\n")

    for idx, stock in enumerate(stocks, 1):
        company_id = stock["id"]
        ticker = stock["ticker"]

        print(f"[{idx}/{len(stocks)}] Fetching {ticker}...")

        # Fetch price data from Yahoo Finance
        price_data = fetch_price_data(ticker, YTD_START_DATE, TODAY)

        if price_data:
            # Convert to database format
            for price_point in price_data:
                all_price_records.append({
                    "company_id": company_id,
                    "date": price_point["date"],
                    "close_price": price_point["close"]
                })

            print(f"  ✅ Fetched {len(price_data)} price points for {ticker}")
            successful_count += 1
            total_price_records += len(price_data)
        else:
            print(f"  ❌ Failed to fetch data for {ticker}")
            failed_count += 1

        # Rate limiting: wait 0.5 seconds between requests
        time.sleep(0.5)

    # Upsert all collected price records
    print(f"\n{'='*70}")
    print("Uploading price data to Supabase...")
    print(f"{'='*70}\n")

    batch_upsert_prices(all_price_records)

    # Print summary
    print(f"\n{'='*70}")
    print("Summary")
    print(f"{'='*70}")
    print(f"Total stocks processed: {len(stocks)}")
    print(f"Successful: {successful_count}")
    print(f"Failed: {failed_count}")
    print(f"Total price records collected: {total_price_records}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    fetch_ytd_prices()
