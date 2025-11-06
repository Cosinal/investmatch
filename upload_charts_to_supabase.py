"""
Upload stock chart images to Supabase Storage and update database with URLs.

This script:
- Reads all stocks from Supabase
- Uploads chart PNGs to Supabase Storage bucket 'stock-charts'
- Updates stocks table with public image URLs
- Shows progress and summary
"""

import os
from typing import List, Optional, Tuple

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
CHART_DIR = "charts"
BUCKET_NAME = "stock-charts"

# ---------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------

def get_all_stocks() -> List[dict]:
    """
    Fetch all stocks from Supabase.
    Returns list of dicts with id and ticker.
    """
    response = supabase.table("stocks").select("id, ticker").execute()
    return response.data


def ensure_bucket_exists():
    """
    Ensure the stock-charts bucket exists in Supabase Storage.
    Creates it if it doesn't exist.
    """
    try:
        # Try to get bucket info
        buckets = supabase.storage.list_buckets()
        bucket_names = [bucket['name'] for bucket in buckets]

        if BUCKET_NAME not in bucket_names:
            print(f"Creating bucket '{BUCKET_NAME}'...")
            supabase.storage.create_bucket(
                BUCKET_NAME,
                options={"public": True}  # Make bucket public for easy access
            )
            print(f"✅ Bucket '{BUCKET_NAME}' created successfully")
        else:
            print(f"✅ Bucket '{BUCKET_NAME}' already exists")
    except Exception as e:
        print(f"⚠️  Error checking/creating bucket: {e}")
        print("Continuing with upload attempts...")


def upload_chart_to_storage(ticker: str) -> Optional[str]:
    """
    Upload a chart image to Supabase Storage.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Public URL of uploaded image, or None if upload fails
    """
    # Check if local file exists
    local_path = os.path.join(CHART_DIR, f"{ticker}_ytd_chart.png")

    if not os.path.exists(local_path):
        return None

    # Read file
    with open(local_path, "rb") as f:
        file_data = f.read()

    # Storage path in bucket
    storage_path = f"{ticker}_ytd_chart.png"

    try:
        # Upload to Supabase Storage (upsert to overwrite if exists)
        supabase.storage.from_(BUCKET_NAME).upload(
            storage_path,
            file_data,
            file_options={"content-type": "image/png", "upsert": "true"}
        )

        # Get public URL
        public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(storage_path)

        return public_url

    except Exception as e:
        print(f"  ❌ Upload error: {e}")
        return None


def update_stock_chart_url(stock_id: int, chart_url: str) -> bool:
    """
    Update stocks table with chart image URL.

    Args:
        stock_id: Stock ID
        chart_url: Public URL of chart image

    Returns:
        True if update successful, False otherwise
    """
    try:
        supabase.table("stocks").update(
            {"chart_image_url": chart_url}
        ).eq("id", stock_id).execute()

        return True

    except Exception as e:
        print(f"  ❌ Database update error: {e}")
        return False


# ---------------------------------------------------------------------
# Main Function
# ---------------------------------------------------------------------

def upload_all_charts():
    """
    Main function to upload all charts to Supabase Storage.
    """
    print(f"\n{'='*70}")
    print("Uploading Stock Charts to Supabase Storage")
    print(f"{'='*70}\n")

    # Ensure bucket exists
    ensure_bucket_exists()
    print()

    # Get all stocks
    stocks = get_all_stocks()
    total_stocks = len(stocks)

    if total_stocks == 0:
        print("No stocks found in database. Exiting.")
        return

    print(f"Found {total_stocks} stocks in database.\n")
    print("Uploading charts...\n")

    # Track statistics
    successful_count = 0
    skipped_count = 0
    failed_count = 0

    for idx, stock in enumerate(stocks, 1):
        stock_id = stock["id"]
        ticker = stock["ticker"]

        print(f"[{idx}/{total_stocks}] {ticker}...", end=" ")

        # Upload chart to storage
        public_url = upload_chart_to_storage(ticker)

        if public_url is None:
            print("⚠️  Chart file not found (skipped)")
            skipped_count += 1
            continue

        # Update database with URL
        success = update_stock_chart_url(stock_id, public_url)

        if success:
            print("✅ Uploaded")
            successful_count += 1
        else:
            print("❌ Upload succeeded but database update failed")
            failed_count += 1

    # Print summary
    print(f"\n{'='*70}")
    print("Summary")
    print(f"{'='*70}")
    print(f"Total stocks: {total_stocks}")
    print(f"Charts uploaded: {successful_count}")
    print(f"Skipped (no chart file): {skipped_count}")
    print(f"Failed (upload/update errors): {failed_count}")
    print(f"\n✅ Charts available at: {SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    upload_all_charts()
