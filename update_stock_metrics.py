"""
Calculate and update YTD performance metrics for stocks.

Reads price data from stock_prices table and updates the stocks table with:
- ytd_return: Year-to-date return percentage
- current_price: Most recent closing price
- first_price_2025: First closing price in 2025
- price_updated_at: Timestamp of update

Requirements:
- stocks table must have columns: id, ticker, ytd_return, current_price,
  first_price_2025, price_updated_at
- stock_prices table must have: company_id, date, close_price
"""

import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal

from supabase import create_client, Client
from dotenv import load_dotenv

# ---------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

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

    print(f"✅ Found {len(stocks)} stocks in database\n")
    return stocks


def get_price_metrics(company_id: int) -> Optional[Tuple[Decimal, Decimal, str, str]]:
    """
    Get first and latest price data for a company from stock_prices table.

    Args:
        company_id: The company ID to query

    Returns:
        Tuple of (first_price, latest_price, first_date, latest_date) or None if no data
    """
    try:
        # Get first price in 2025 (earliest date)
        first_response = (
            supabase.table("stock_prices")
            .select("close_price, date")
            .eq("company_id", company_id)
            .gte("date", "2025-01-01")
            .order("date", desc=False)
            .limit(1)
            .execute()
        )

        # Get most recent price
        latest_response = (
            supabase.table("stock_prices")
            .select("close_price, date")
            .eq("company_id", company_id)
            .order("date", desc=True)
            .limit(1)
            .execute()
        )

        if not first_response.data or not latest_response.data:
            return None

        first_price = Decimal(str(first_response.data[0]["close_price"]))
        first_date = first_response.data[0]["date"]
        latest_price = Decimal(str(latest_response.data[0]["close_price"]))
        latest_date = latest_response.data[0]["date"]

        return (first_price, latest_price, first_date, latest_date)

    except Exception as e:
        print(f"  ❌ Error querying price data: {e}")
        return None


def calculate_ytd_return(first_price: Decimal, current_price: Decimal) -> Decimal:
    """
    Calculate YTD return percentage.

    Formula: ((current - first) / first) * 100

    Args:
        first_price: First closing price in 2025
        current_price: Most recent closing price

    Returns:
        YTD return as a percentage (Decimal)
    """
    if first_price == 0:
        return Decimal("0")

    return ((current_price - first_price) / first_price) * Decimal("100")


def batch_update_stocks(update_records: List[Dict[str, Any]]) -> None:
    """
    Update stock metrics in batches.

    Args:
        update_records: List of dicts with stock updates
    """
    if not update_records:
        return

    print(f"\nUpdating {len(update_records)} stocks in database...")

    # Supabase upsert requires individual updates when using id as key
    # So we'll do them one by one but efficiently
    for record in update_records:
        try:
            supabase.table("stocks").update({
                "ytd_return": float(record["ytd_return"]),
                "current_price": float(record["current_price"]),
                "first_price_2025": float(record["first_price_2025"]),
                "price_updated_at": record["price_updated_at"]
            }).eq("id", record["id"]).execute()

        except Exception as e:
            print(f"  ❌ Error updating {record.get('ticker', 'unknown')}: {e}")
            continue

    print("✅ Database updated successfully\n")


# ---------------------------------------------------------------------
# Main Function
# ---------------------------------------------------------------------

def update_stock_metrics():
    """
    Main function to calculate and update YTD metrics for all stocks.
    """
    print(f"\n{'='*70}")
    print("Calculating YTD Performance Metrics")
    print(f"{'='*70}\n")

    # Get all stocks
    stocks = get_all_stocks()

    if not stocks:
        print("No stocks found in database. Exiting.")
        return

    # Track statistics
    update_records = []
    skipped_count = 0
    current_timestamp = datetime.utcnow().isoformat()

    print("Processing stocks...\n")

    for idx, stock in enumerate(stocks, 1):
        company_id = stock["id"]
        ticker = stock["ticker"]

        print(f"[{idx}/{len(stocks)}] {ticker}...", end=" ")

        # Get price data
        price_data = get_price_metrics(company_id)

        if price_data is None:
            print("⚠️  No price data available (skipped)")
            skipped_count += 1
            continue

        first_price, latest_price, first_date, latest_date = price_data

        # Calculate YTD return
        ytd_return = calculate_ytd_return(first_price, latest_price)

        # Store update record
        update_records.append({
            "id": company_id,
            "ticker": ticker,
            "ytd_return": ytd_return,
            "current_price": latest_price,
            "first_price_2025": first_price,
            "price_updated_at": current_timestamp
        })

        # Print metrics
        ytd_str = f"{ytd_return:+.2f}%"
        price_str = f"${latest_price:.2f}"
        print(f"✅ YTD: {ytd_str:>8} | Price: {price_str:>10} ({first_date} → {latest_date})")

    # Update database
    batch_update_stocks(update_records)

    # Print summary
    print(f"{'='*70}")
    print("Summary Statistics")
    print(f"{'='*70}\n")

    if update_records:
        # Calculate statistics
        total_updated = len(update_records)
        ytd_returns = [float(r["ytd_return"]) for r in update_records]
        avg_ytd = sum(ytd_returns) / len(ytd_returns)

        # Sort by YTD return
        sorted_records = sorted(update_records, key=lambda x: float(x["ytd_return"]), reverse=True)
        top_5 = sorted_records[:5]
        bottom_5 = sorted_records[-5:]

        print(f"Total companies processed: {len(stocks)}")
        print(f"Successfully updated: {total_updated}")
        print(f"Skipped (no data): {skipped_count}")
        print(f"Average YTD return: {avg_ytd:+.2f}%\n")

        print("Top 5 Performers:")
        print(f"{'Rank':<6} {'Ticker':<10} {'YTD Return':<12} {'Current Price':<15}")
        print("-" * 50)
        for i, record in enumerate(top_5, 1):
            ytd = float(record["ytd_return"])
            price = float(record["current_price"])
            print(f"{i:<6} {record['ticker']:<10} {ytd:+.2f}%{' ':<8} ${price:.2f}")

        print(f"\nBottom 5 Performers:")
        print(f"{'Rank':<6} {'Ticker':<10} {'YTD Return':<12} {'Current Price':<15}")
        print("-" * 50)
        for i, record in enumerate(bottom_5, 1):
            ytd = float(record["ytd_return"])
            price = float(record["current_price"])
            print(f"{i:<6} {record['ticker']:<10} {ytd:+.2f}%{' ':<8} ${price:.2f}")

    else:
        print("No stocks were updated.")
        print(f"Skipped (no data): {skipped_count}")

    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    update_stock_metrics()
