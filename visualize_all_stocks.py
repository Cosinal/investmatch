"""
Generate YTD performance charts for ALL stocks in the database.

This script:
- Queries all stocks from Supabase
- Fetches 2025 YTD price data for each
- Generates professional line charts
- Saves to charts/{ticker}_ytd_chart.png
- Prints summary report
"""

import os
from typing import Optional, Tuple, List
from decimal import Decimal

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
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
MIN_DATA_POINTS = 5  # Skip stocks with fewer data points
POSITIVE_COLOR = "#10b981"  # Green
NEGATIVE_COLOR = "#ef4444"  # Red

# Ensure charts directory exists
os.makedirs(CHART_DIR, exist_ok=True)

# ---------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------

def get_all_stocks() -> List[dict]:
    """
    Fetch all stocks from Supabase.
    Returns list of dicts with id, ticker, name.
    """
    response = supabase.table("stocks").select("id, ticker, name").execute()
    return response.data


def get_stock_price_data(company_id: int) -> Optional[pd.DataFrame]:
    """
    Fetch all 2025 price data for a stock.
    Returns DataFrame with date and close_price columns, or None if insufficient data.
    """
    response = (
        supabase.table("stock_prices")
        .select("date, close_price")
        .eq("company_id", company_id)
        .gte("date", "2025-01-01")
        .order("date", desc=False)
        .execute()
    )

    if not response.data or len(response.data) < MIN_DATA_POINTS:
        return None

    df = pd.DataFrame(response.data)
    df["date"] = pd.to_datetime(df["date"])
    df["close_price"] = df["close_price"].astype(float)

    return df


def calculate_ytd_return(df: pd.DataFrame) -> Optional[float]:
    """
    Calculate YTD return percentage.
    Returns ((current - first) / first) * 100
    """
    if df.empty or len(df) < 2:
        return None

    first_price = df.iloc[0]["close_price"]
    latest_price = df.iloc[-1]["close_price"]

    if first_price == 0:
        return None

    return ((latest_price - first_price) / first_price) * 100


def create_chart(
    ticker: str,
    name: str,
    df: pd.DataFrame,
    ytd_return: Optional[float],
    current_price: float,
    first_price: float
) -> str:
    """
    Create a professional YTD performance chart.
    Returns the output file path.
    """
    sns.set_style("darkgrid")
    fig, ax = plt.subplots(figsize=(10, 5))

    # Determine color based on performance
    is_positive = ytd_return is None or ytd_return >= 0
    line_color = POSITIVE_COLOR if is_positive else NEGATIVE_COLOR

    # Plot the main line
    ax.plot(
        df["date"],
        df["close_price"],
        color=line_color,
        linewidth=2.5,
        label=f"{ticker} Price",
        zorder=3
    )

    # Fill area under the curve
    ax.fill_between(
        df["date"],
        df["close_price"],
        alpha=0.3,
        color=line_color,
        zorder=2
    )

    # Add horizontal reference line at starting price
    ax.axhline(
        y=first_price,
        color='gray',
        linestyle='--',
        linewidth=1,
        alpha=0.5,
        label='Starting Price',
        zorder=1
    )

    # Format y-axis as currency
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'${y:.2f}'))

    # Format x-axis as month names
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    ax.xaxis.set_major_locator(mdates.MonthLocator())

    # Labels and title
    ax.set_xlabel('Date', fontsize=11, fontweight='bold')
    ax.set_ylabel('Price (CAD)', fontsize=11, fontweight='bold')

    # Title with subtitle
    ytd_str = f"{ytd_return:+.1f}%" if ytd_return is not None else "N/A"
    title_text = f"{ticker} - YTD Performance"
    subtitle_text = f"Current: ${current_price:.2f} | YTD: {ytd_str}"

    ax.set_title(
        f"{title_text}\n{subtitle_text}",
        fontsize=14,
        fontweight='bold',
        pad=20
    )

    # Grid and legend
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper left', framealpha=0.9)

    # Tight layout
    plt.tight_layout()

    # Save chart
    output_path = os.path.join(CHART_DIR, f"{ticker}_ytd_chart.png")
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    return output_path


# ---------------------------------------------------------------------
# Main Function
# ---------------------------------------------------------------------

def visualize_all_stocks():
    """
    Main function to generate charts for all stocks.
    """
    print(f"\n{'='*70}")
    print("Generating YTD Charts for All Stocks")
    print(f"{'='*70}\n")

    # Get all stocks
    stocks = get_all_stocks()
    total_stocks = len(stocks)

    if total_stocks == 0:
        print("No stocks found in database. Exiting.")
        return

    print(f"Found {total_stocks} stocks in database.\n")
    print("Generating charts...\n")

    # Track statistics
    successful_count = 0
    skipped_count = 0
    failed_count = 0
    ytd_returns = []

    for idx, stock in enumerate(stocks, 1):
        company_id = stock["id"]
        ticker = stock["ticker"]
        name = stock["name"]

        print(f"[{idx}/{total_stocks}] {ticker}...", end=" ")

        try:
            # Fetch price data
            df = get_stock_price_data(company_id)

            if df is None:
                print("⚠️  Insufficient data (skipped)")
                skipped_count += 1
                continue

            # Calculate metrics
            ytd_return = calculate_ytd_return(df)
            current_price = df.iloc[-1]["close_price"]
            first_price = df.iloc[0]["close_price"]

            # Generate chart
            output_path = create_chart(
                ticker=ticker,
                name=name,
                df=df,
                ytd_return=ytd_return,
                current_price=current_price,
                first_price=first_price
            )

            # Track YTD return for summary
            if ytd_return is not None:
                ytd_returns.append(ytd_return)

            ytd_str = f"{ytd_return:+.1f}%" if ytd_return is not None else "N/A"
            print(f"✅ {ytd_str}")
            successful_count += 1

        except Exception as e:
            print(f"❌ Error: {e}")
            failed_count += 1
            continue

    # Print summary
    print(f"\n{'='*70}")
    print("Summary")
    print(f"{'='*70}")
    print(f"Total stocks: {total_stocks}")
    print(f"Charts generated: {successful_count}")
    print(f"Skipped (insufficient data): {skipped_count}")
    print(f"Failed (errors): {failed_count}")

    if ytd_returns:
        avg_ytd = sum(ytd_returns) / len(ytd_returns)
        print(f"\n📊 Average YTD return: {avg_ytd:+.2f}%")

    charts_path = os.path.abspath(CHART_DIR)
    print(f"📁 Charts saved to: {charts_path}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    visualize_all_stocks()
