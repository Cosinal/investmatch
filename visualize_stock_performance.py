"""
Generate beautiful YTD performance charts for TSX stocks.

Usage:
    python visualize_stock_performance.py SHOP
    python visualize_stock_performance.py RY

Requirements:
    - matplotlib
    - seaborn
    - pandas
    - python-dotenv
    - supabase
"""

import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
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

# Chart styling constants
POSITIVE_COLOR = "#10b981"  # Green
NEGATIVE_COLOR = "#ef4444"  # Red
CHART_DIR = "charts"

# ---------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------

def get_stock_info(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Get stock information from stocks table.

    Args:
        ticker: Stock ticker symbol (e.g., 'SHOP')

    Returns:
        Dict with stock info or None if not found
    """
    try:
        response = (
            supabase.table("stocks")
            .select("id, ticker, name, ytd_return, current_price, first_price_2025")
            .eq("ticker", ticker.upper())
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]

    except Exception as e:
        print(f"❌ Error fetching stock info: {e}")
        return None


def get_price_data(company_id: int) -> Optional[pd.DataFrame]:
    """
    Get all 2025 price data for a company.

    Args:
        company_id: The company ID

    Returns:
        DataFrame with date and close_price columns, or None if no data
    """
    try:
        response = (
            supabase.table("stock_prices")
            .select("date, close_price")
            .eq("company_id", company_id)
            .gte("date", "2025-01-01")
            .order("date", desc=False)
            .execute()
        )

        if not response.data:
            return None

        # Convert to DataFrame
        df = pd.DataFrame(response.data)
        df["date"] = pd.to_datetime(df["date"])
        df["close_price"] = df["close_price"].astype(float)

        return df

    except Exception as e:
        print(f"❌ Error fetching price data: {e}")
        return None


def create_chart(
    ticker: str,
    name: str,
    df: pd.DataFrame,
    ytd_return: Optional[float],
    current_price: Optional[float],
    first_price: Optional[float]
) -> str:
    """
    Create a professional YTD performance chart.

    Args:
        ticker: Stock ticker symbol
        name: Company name
        df: DataFrame with date and close_price columns
        ytd_return: YTD return percentage
        current_price: Current/latest price
        first_price: First price in 2025

    Returns:
        Path to saved chart file
    """
    # Set style
    sns.set_style("darkgrid")

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))

    # Determine color based on YTD return
    is_positive = ytd_return is None or ytd_return >= 0
    line_color = POSITIVE_COLOR if is_positive else NEGATIVE_COLOR
    fill_alpha = 0.3

    # Plot main line
    ax.plot(
        df["date"],
        df["close_price"],
        color=line_color,
        linewidth=2.5,
        label=f"{ticker} Price",
        zorder=3
    )

    # Fill area under curve
    ax.fill_between(
        df["date"],
        df["close_price"],
        alpha=fill_alpha,
        color=line_color,
        zorder=2
    )

    # Add data point markers every 2 weeks (every ~10 data points, assuming trading days)
    marker_indices = range(0, len(df), 10)
    ax.plot(
        df["date"].iloc[marker_indices],
        df["close_price"].iloc[marker_indices],
        'o',
        color=line_color,
        markersize=5,
        markeredgewidth=1.5,
        markeredgecolor='white',
        zorder=4
    )

    # Add reference line at starting price
    if first_price:
        ax.axhline(
            y=first_price,
            color='gray',
            linestyle='--',
            linewidth=1,
            alpha=0.5,
            label=f'Starting Price (${first_price:.2f})',
            zorder=1
        )

    # Format y-axis with currency
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'${y:.2f}'))

    # Format x-axis with month names
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    ax.xaxis.set_major_locator(mdates.MonthLocator())

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=0)

    # Set labels
    ax.set_xlabel('Month (2025)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Price (CAD)', fontsize=11, fontweight='bold')

    # Create title with subtitle
    title = f"{ticker} - Year to Date Performance"
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)

    # Add subtitle with metrics
    if current_price is not None and ytd_return is not None:
        ytd_sign = "+" if ytd_return >= 0 else ""
        subtitle_color = POSITIVE_COLOR if ytd_return >= 0 else NEGATIVE_COLOR
        subtitle = f"Current: ${current_price:.2f} | YTD Return: {ytd_sign}{ytd_return:.2f}%"

        ax.text(
            0.5, 0.97,
            subtitle,
            transform=ax.transAxes,
            fontsize=12,
            ha='center',
            va='top',
            color=subtitle_color,
            fontweight='bold'
        )

    # Add legend
    ax.legend(loc='upper left', framealpha=0.9, fontsize=10)

    # Add grid
    ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)

    # Adjust layout for proper padding
    plt.tight_layout()

    # Ensure charts directory exists
    Path(CHART_DIR).mkdir(exist_ok=True)

    # Save chart
    output_path = os.path.join(CHART_DIR, f"{ticker}_ytd_chart.png")
    plt.savefig(output_path, dpi=150, bbox_inches='tight')

    # Display chart
    plt.show()

    return output_path


# ---------------------------------------------------------------------
# Main Function
# ---------------------------------------------------------------------

def main():
    """
    Main function to generate stock performance chart.
    """
    # Check command line arguments
    if len(sys.argv) < 2:
        print("❌ Error: Ticker symbol required")
        print("\nUsage: python visualize_stock_performance.py <TICKER>")
        print("Example: python visualize_stock_performance.py SHOP")
        sys.exit(1)

    ticker = sys.argv[1].upper()

    print(f"\n{'='*60}")
    print(f"Generating Chart for {ticker}")
    print(f"{'='*60}\n")

    # Get stock info
    print(f"Fetching stock information for {ticker}...")
    stock_info = get_stock_info(ticker)

    if not stock_info:
        print(f"❌ Error: Ticker '{ticker}' not found in database")
        print("\nMake sure the ticker exists in the stocks table.")
        sys.exit(1)

    company_id = stock_info["id"]
    name = stock_info.get("name", ticker)
    ytd_return = stock_info.get("ytd_return")
    current_price = stock_info.get("current_price")
    first_price = stock_info.get("first_price_2025")

    print(f"✅ Found: {name}")

    # Get price data
    print(f"Fetching price data...")
    df = get_price_data(company_id)

    if df is None or len(df) == 0:
        print(f"❌ Error: No price data found for {ticker}")
        print("\nMake sure you've run fetch_stock_prices.py to populate price data.")
        sys.exit(1)

    print(f"✅ Loaded {len(df)} data points")

    # Create chart
    print(f"Generating chart...")
    output_path = create_chart(
        ticker,
        name,
        df,
        ytd_return,
        current_price,
        first_price
    )

    # Print success message
    print(f"\n{'='*60}")
    print(f"✅ Generated chart: {output_path}")

    if current_price is not None and ytd_return is not None:
        ytd_sign = "+" if ytd_return >= 0 else ""
        print(f"📈 {ticker}: ${current_price:.2f} | YTD Return: {ytd_sign}{ytd_return:.2f}%")

    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
