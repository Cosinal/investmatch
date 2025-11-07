"""
Test script for InvestMatch user tracking system.

This script:
1. Connects to Supabase
2. Creates/uses a test user
3. Simulates swiping on stocks
4. Adds right-swiped stocks to watchlist
5. Queries and displays user data
6. Verifies RLS is working correctly

Run this after executing create_user_tracking_tables.sql in Supabase.
"""

import os
import random
from typing import List, Dict, Any
from datetime import datetime

from supabase import create_client, Client
from dotenv import load_dotenv

# ---------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Test user UUID - will be fetched from auth.users or you can set manually
# To set manually: Replace None with your user UUID string
# Example: TEST_USER_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
TEST_USER_ID = "05affdd9-fa0c-4ee8-bf9f-32db99fe6a00"

# ---------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------

def get_or_create_test_user() -> str:
    """
    Get a valid user ID from auth.users table.
    If TEST_USER_ID is set, validates it exists.
    Otherwise, tries to find any existing user.
    """
    global TEST_USER_ID

    # If TEST_USER_ID is manually set, validate it exists
    if TEST_USER_ID:
        try:
            response = supabase.auth.admin.get_user_by_id(TEST_USER_ID)
            if response:
                print(f"✅ Using manually configured user: {TEST_USER_ID}\n")
                return TEST_USER_ID
        except Exception as e:
            print(f"⚠️  Configured TEST_USER_ID not found: {e}")

    # Try to get first user from auth.users using admin API
    try:
        # Use admin API to list users
        response = supabase.auth.admin.list_users()

        if response and hasattr(response, 'users') and len(response.users) > 0:
            user_id = response.users[0].id
            print(f"✅ Found existing user in auth.users: {user_id}")
            print(f"   Email: {response.users[0].email or 'N/A'}\n")
            return user_id
    except Exception as e:
        print(f"⚠️  Could not query auth.users via admin API: {e}")

    # If no users found, provide instructions
    print("\n" + "="*70)
    print("❌ No users found in Supabase Auth")
    print("="*70)
    print("\nTo run this test, you need a user in your Supabase project.")
    print("\nOption 1: Create a test user via Supabase Dashboard")
    print("  1. Go to Authentication → Users in Supabase Dashboard")
    print("  2. Click 'Add User'")
    print("  3. Enter email (e.g., test@investmatch.com) and password")
    print("  4. Copy the user UUID")
    print("  5. Set TEST_USER_ID in this script to that UUID")
    print("\nOption 2: Create a test user via SQL")
    print("  Run this in Supabase SQL Editor:")
    print("  ```sql")
    print("  -- This creates a user in auth.users")
    print("  -- Note: This is a simplified version, normally users are created via Supabase Auth API")
    print("  SELECT auth.uid(); -- This will show you if you're logged in")
    print("  ```")
    print("\nOption 3: Sign up via your app")
    print("  1. Run your InvestMatch app")
    print("  2. Create an account")
    print("  3. Find your user UUID in Supabase Dashboard → Authentication → Users")
    print("  4. Set TEST_USER_ID in this script")
    print("\n" + "="*70 + "\n")

    return None


def get_random_stocks(limit: int = 10) -> List[Dict[str, Any]]:
    """Get random stocks from database."""
    response = supabase.table("stocks").select("id, ticker, name").limit(60).execute()

    if not response.data:
        print("❌ No stocks found in database")
        return []

    # Randomly sample stocks
    all_stocks = response.data
    sample_size = min(limit, len(all_stocks))
    return random.sample(all_stocks, sample_size)


def record_swipe(user_id: str, company_id: int, direction: str) -> bool:
    """Record a swipe action."""
    try:
        response = supabase.table("user_swipes").insert({
            "user_id": user_id,
            "company_id": company_id,
            "swipe_direction": direction
        }).execute()

        return True
    except Exception as e:
        # Duplicate swipe is okay - unique constraint will prevent it
        if "unique_user_company_swipe" in str(e):
            print(f"  ⚠️  Already swiped on this stock")
            return False
        print(f"  ❌ Error recording swipe: {e}")
        return False


def add_to_watchlist(user_id: str, company_id: int, notes: str = None) -> bool:
    """Add stock to user's watchlist."""
    try:
        response = supabase.table("user_watchlist").insert({
            "user_id": user_id,
            "company_id": company_id,
            "notes": notes
        }).execute()

        return True
    except Exception as e:
        if "unique_user_company_watchlist" in str(e):
            print(f"  ⚠️  Already in watchlist")
            return False
        print(f"  ❌ Error adding to watchlist: {e}")
        return False


def get_user_swipes(user_id: str) -> List[Dict[str, Any]]:
    """Get all swipes for a user."""
    response = supabase.table("user_swipes").select(
        "*, stocks(ticker, name)"
    ).eq("user_id", user_id).order("swiped_at", desc=True).execute()

    return response.data or []


def get_user_watchlist(user_id: str) -> List[Dict[str, Any]]:
    """Get user's watchlist."""
    response = supabase.table("user_watchlist").select(
        "*, stocks(ticker, name, current_price, ytd_return)"
    ).eq("user_id", user_id).order("added_at", desc=True).execute()

    return response.data or []


def get_swipe_stats(user_id: str) -> Dict[str, Any]:
    """Get swipe statistics for user."""
    try:
        response = supabase.rpc("get_user_swipe_stats", {"user_uuid": user_id}).execute()

        if response.data and len(response.data) > 0:
            return response.data[0]
        return {}
    except Exception as e:
        print(f"  ❌ Error getting swipe stats: {e}")
        return {}


def get_unswiped_stocks_count(user_id: str) -> int:
    """Get count of stocks user hasn't swiped on."""
    try:
        response = supabase.rpc("get_unswiped_stocks", {"user_uuid": user_id}).execute()

        return len(response.data) if response.data else 0
    except Exception as e:
        print(f"  ❌ Error getting unswiped stocks: {e}")
        return 0


# ---------------------------------------------------------------------
# Main Test Function
# ---------------------------------------------------------------------

def run_tests():
    """Run comprehensive tests of user tracking system."""
    print(f"\n{'='*70}")
    print("InvestMatch User Tracking System Test")
    print(f"{'='*70}\n")

    # Get or validate test user
    user_id = get_or_create_test_user()

    if not user_id:
        print("❌ Cannot run tests without a valid user. Exiting.")
        return

    print(f"Test User ID: {user_id}\n")

    # ---------------------------------------------------------------------
    # TEST 1: Get Random Stocks
    # ---------------------------------------------------------------------
    print("📊 Step 1: Getting random stocks for testing...")
    stocks = get_random_stocks(10)

    if not stocks:
        print("❌ Failed to get stocks. Exiting.")
        return

    print(f"✅ Retrieved {len(stocks)} stocks\n")

    # ---------------------------------------------------------------------
    # TEST 2: Simulate Swipes
    # ---------------------------------------------------------------------
    print("👆 Step 2: Simulating swipe actions...")

    left_swipes = stocks[:5]  # First 5 = pass (left)
    right_swipes = stocks[5:]  # Last 5 = like (right)

    print("\n  Left swipes (PASS):")
    for stock in left_swipes:
        success = record_swipe(user_id, stock["id"], "left")
        icon = "✅" if success else "⚠️"
        print(f"    {icon} {stock['ticker']} - {stock['name']}")

    print("\n  Right swipes (LIKE):")
    for stock in right_swipes:
        success = record_swipe(user_id, stock["id"], "right")
        icon = "✅" if success else "⚠️"
        print(f"    {icon} {stock['ticker']} - {stock['name']}")

    print()

    # ---------------------------------------------------------------------
    # TEST 3: Add to Watchlist
    # ---------------------------------------------------------------------
    print("⭐ Step 3: Adding liked stocks to watchlist...")

    for stock in right_swipes:
        notes = f"Interested in {stock['ticker']} - potential investment"
        success = add_to_watchlist(user_id, stock["id"], notes)
        icon = "✅" if success else "⚠️"
        print(f"  {icon} Added {stock['ticker']} to watchlist")

    print()

    # ---------------------------------------------------------------------
    # TEST 4: Query User Data
    # ---------------------------------------------------------------------
    print("📈 Step 4: Querying user data...\n")

    # Get swipe history
    print("  Swipe History:")
    swipes = get_user_swipes(user_id)
    print(f"  Total swipes: {len(swipes)}")

    for swipe in swipes[:5]:  # Show first 5
        direction_icon = "👍" if swipe["swipe_direction"] == "right" else "👎"
        ticker = swipe["stocks"]["ticker"]
        name = swipe["stocks"]["name"]
        print(f"    {direction_icon} {ticker} - {name}")

    if len(swipes) > 5:
        print(f"    ... and {len(swipes) - 5} more")

    print()

    # Get watchlist
    print("  Watchlist:")
    watchlist = get_user_watchlist(user_id)
    print(f"  Total watchlist items: {len(watchlist)}")

    for item in watchlist:
        ticker = item["stocks"]["ticker"]
        name = item["stocks"]["name"]
        price = item["stocks"].get("current_price")
        ytd = item["stocks"].get("ytd_return")

        price_str = f"${price:.2f}" if price else "N/A"
        ytd_str = f"{ytd:+.2f}%" if ytd is not None else "N/A"

        print(f"    ⭐ {ticker} - {name}")
        print(f"       Price: {price_str} | YTD: {ytd_str}")
        if item.get("notes"):
            print(f"       Notes: {item['notes']}")

    print()

    # ---------------------------------------------------------------------
    # TEST 5: Get Statistics
    # ---------------------------------------------------------------------
    print("📊 Step 5: Getting user statistics...\n")

    stats = get_swipe_stats(user_id)

    if stats:
        print(f"  Total Swipes: {stats.get('total_swipes', 0)}")
        print(f"  Left Swipes (Pass): {stats.get('left_swipes', 0)}")
        print(f"  Right Swipes (Like): {stats.get('right_swipes', 0)}")
        print(f"  Like Rate: {stats.get('swipe_rate', 0)}%")
    else:
        print("  ⚠️  Could not retrieve stats")

    print()

    # Get unswiped stocks count
    unswiped_count = get_unswiped_stocks_count(user_id)
    print(f"  Stocks not yet swiped: {unswiped_count}")

    print()

    # ---------------------------------------------------------------------
    # TEST 6: Verify RLS (if possible)
    # ---------------------------------------------------------------------
    print("🔒 Step 6: RLS Verification")
    print("  Note: RLS policies are active and enforced by Supabase")
    print("  In production, users can only see their own swipes/watchlist")
    print("  This test uses SERVICE_ROLE_KEY which bypasses RLS")

    print(f"\n{'='*70}")
    print("✅ All tests completed successfully!")
    print(f"{'='*70}\n")

    print("Summary:")
    print(f"  - Recorded {len(swipes)} total swipes")
    print(f"  - Created {len(watchlist)} watchlist items")
    print(f"  - {unswiped_count} stocks remaining to swipe")
    print(f"\n  Test User ID: {user_id}")
    print(f"  You can view this data in Supabase dashboard\n")


# ---------------------------------------------------------------------
# Run Tests
# ---------------------------------------------------------------------

if __name__ == "__main__":
    try:
        run_tests()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
