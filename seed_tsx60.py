import os
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import yfinance as yf
from supabase import create_client, Client
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load environment variables from .env
# ---------------------------------------------------------------------------

# This will look for a .env file in the current directory or parent directories
load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# ---------------------------------------------------------------------------
# TSX 60 tickers (Yahoo format)
# ---------------------------------------------------------------------------

TSX60_TICKERS = [
    "AEM.TO", "AQN.TO", "ATD.TO", "BMO.TO", "BNS.TO", "ABX.TO", "BCE.TO", "BAM.TO",
    "BN.TO", "BIP-UN.TO", "CAE.TO", "CCO.TO", "CAR-UN.TO", "CM.TO", "CNR.TO", "CNQ.TO",
    "CP.TO", "CTC-A.TO", "CCL-B.TO", "CVE.TO", "GIB-A.TO", "CSU.TO", "DOL.TO", "EMA.TO",
    "ENB.TO", "FM.TO", "FSV.TO", "FTS.TO", "FNV.TO", "WN.TO", "GIL.TO", "H.TO", "IMO.TO",
    "IFC.TO", "K.TO", "L.TO", "MG.TO", "MFC.TO", "MRU.TO", "NA.TO", "NTR.TO", "OTEX.TO",
    "PPL.TO", "POW.TO", "QSR.TO", "RCI-B.TO", "RY.TO", "SAP.TO", "SHOP.TO", "SLF.TO",
    "SU.TO", "TRP.TO", "TECK-B.TO", "T.TO", "TRI.TO", "TD.TO", "TOU.TO", "WCN.TO",
    "WPM.TO", "WSP.TO"
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def clean_ticker(yahoo_symbol: str) -> str:
    """
    Convert Yahoo symbols like 'BIP-UN.TO' into DB-friendly tickers like 'BIP.UN'.
    """
    if yahoo_symbol.endswith(".TO"):
        yahoo_symbol = yahoo_symbol[:-3]

    if "-" in yahoo_symbol:
        parts = yahoo_symbol.split("-", 1)
        return f"{parts[0]}.{parts[1]}"

    return yahoo_symbol


def build_logo_url(website: Optional[str]) -> Optional[str]:
    """
    Derive a logo URL from the company's website using Google's favicon service.
    Example: https://www.google.com/s2/favicons?sz=128&domain_url=www.shopify.com
    """
    if not website:
        return None

    try:
        parsed = urlparse(website)
        host = parsed.netloc or parsed.path
        host = host.strip("/")
        if not host:
            return None

        return f"https://www.google.com/s2/favicons?sz=128&domain_url={host}"
    except Exception:
        return None


def fetch_stock_row(yahoo_symbol: str) -> Optional[Dict[str, Any]]:
    print(f"Fetching {yahoo_symbol}...")
    ticker_obj = yf.Ticker(yahoo_symbol)

    try:
        info = ticker_obj.get_info()
    except Exception as e:
        print(f"  Error fetching info for {yahoo_symbol}: {e}")
        return None

    if not info:
        print(f"  No info returned for {yahoo_symbol}")
        return None

    current_price = info.get("currentPrice")
    prev_close = info.get("previousClose")

    price_change_abs: Optional[float] = None
    price_change_pct: Optional[float] = None

    if current_price is not None and prev_close is not None and prev_close != 0:
        price_change_abs = float(current_price) - float(prev_close)
        price_change_pct = (price_change_abs / float(prev_close)) * 100.0

    dividend_yield = info.get("dividendYield")
    if dividend_yield is not None:
        dividend_yield = float(dividend_yield) * 100.0

    profit_margin = info.get("profitMargins")
    if profit_margin is not None:
        profit_margin = float(profit_margin) * 100.0

    website = info.get("website")
    logo_url = build_logo_url(website)
    ticker = clean_ticker(yahoo_symbol)

    row: Dict[str, Any] = {
        "ticker": ticker,
        "name": info.get("shortName") or info.get("longName") or ticker,
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "description": info.get("longBusinessSummary"),
        "market_cap": info.get("marketCap"),
        "current_price": current_price,
        "price_change_pct": price_change_pct,
        "price_change_usd": price_change_abs,
        "pe_ratio": info.get("trailingPE"),
        "dividend_yield": dividend_yield,
        "profit_margin": profit_margin,
        "logo_url": logo_url,
    }

    return row


# ---------------------------------------------------------------------------
# Main seeding logic
# ---------------------------------------------------------------------------

def seed_tsx60() -> None:
    rows: List[Dict[str, Any]] = []

    for symbol in TSX60_TICKERS:
        row = fetch_stock_row(symbol)
        if row is not None:
            rows.append(row)

    print(f"\nUpserting {len(rows)} rows into Supabase...")

    # Upsert behavior:
    # - UPDATE existing rows when ticker matches
    # - INSERT new rows when ticker does not exist
    resp = supabase.table("stocks").upsert(rows, on_conflict="ticker").execute()

    print("Supabase response:", resp)


if __name__ == "__main__":
    seed_tsx60()
