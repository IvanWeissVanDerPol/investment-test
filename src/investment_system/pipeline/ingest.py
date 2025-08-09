"""Data ingestion module with caching and resilience."""

import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
import yfinance as yf
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

logger = logging.getLogger(__name__)

CACHE_DIR = Path("runtime/cache")
CACHE_TTL_MINUTES = 10
RATE_LIMIT_DELAY = 0.2  # 200ms between requests (~5 req/s max)
REQUEST_TIMEOUT = 25  # seconds per symbol

# Minimal fallback sample for offline tests
FALLBACK_SAMPLE = pd.DataFrame({
    'date': pd.date_range('2024-01-01', periods=5),
    'open': [150.0, 151.0, 152.0, 151.5, 152.5],
    'high': [152.0, 153.0, 154.0, 153.5, 154.5],
    'low': [149.0, 150.0, 151.0, 150.5, 151.5],
    'close': [151.0, 152.0, 153.0, 152.5, 153.5],
    'volume': [1000000, 1100000, 1200000, 1150000, 1250000],
    'symbol': ['TEST'] * 5
})


def ensure_cache_dir():
    """Ensure cache directory exists."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_cache_path(symbol: str) -> Path:
    """Get cache file path for a symbol."""
    return CACHE_DIR / f"{symbol}.parquet"


def is_cache_valid(cache_path: Path) -> bool:
    """Check if cache file is within TTL."""
    if not cache_path.exists():
        return False
    
    cache_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
    return cache_age < timedelta(minutes=CACHE_TTL_MINUTES)


def load_from_cache(symbol: str) -> Optional[pd.DataFrame]:
    """Load cached data if valid."""
    cache_path = get_cache_path(symbol)
    
    if is_cache_valid(cache_path):
        try:
            df = pd.read_parquet(cache_path)
            logger.info(f"Loaded {symbol} from cache")
            return df
        except Exception as e:
            logger.warning(f"Failed to load cache for {symbol}: {e}")
    
    # Try stale cache if exists
    if cache_path.exists():
        try:
            df = pd.read_parquet(cache_path)
            df['stale'] = True
            logger.warning(f"Using stale cache for {symbol}")
            return df
        except Exception as e:
            logger.error(f"Failed to load stale cache for {symbol}: {e}")
    
    return None


def save_to_cache(symbol: str, df: pd.DataFrame):
    """Save data to cache."""
    ensure_cache_dir()
    cache_path = get_cache_path(symbol)
    
    try:
        df.to_parquet(cache_path)
        logger.info(f"Cached {symbol} data")
    except Exception as e:
        logger.error(f"Failed to cache {symbol}: {e}")


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
)
def fetch_symbol_data(symbol: str, lookback_days: int) -> pd.DataFrame:
    """Fetch data for a single symbol with retry logic."""
    ticker = yf.Ticker(symbol)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=lookback_days)
    
    logger.info(f"Fetching {symbol} from {start_date.date()} to {end_date.date()}")
    
    # Fetch with timeout context
    df = ticker.history(
        start=start_date,
        end=end_date,
        timeout=REQUEST_TIMEOUT
    )
    
    if df.empty:
        raise ValueError(f"No data returned for {symbol}")
    
    # Normalize column names
    df.columns = df.columns.str.lower()
    df.reset_index(inplace=True)
    df['date'] = pd.to_datetime(df['date']).dt.date
    df['symbol'] = symbol
    
    # Ensure required columns
    required_cols = ['date', 'open', 'high', 'low', 'close', 'volume', 'symbol']
    for col in required_cols:
        if col not in df.columns:
            if col == 'volume' and 'vol' in df.columns:
                df['volume'] = df['vol']
            else:
                raise ValueError(f"Missing required column: {col}")
    
    return df[required_cols]


def fetch_prices(symbols: list[str], lookback_days: int = 120) -> pd.DataFrame:
    """
    Fetch price data for multiple symbols with caching and resilience.
    
    Args:
        symbols: List of ticker symbols
        lookback_days: Number of days to look back
    
    Returns:
        DataFrame with columns: date, open, high, low, close, volume, symbol
    """
    if not symbols:
        logger.warning("No symbols provided, returning fallback sample")
        return FALLBACK_SAMPLE
    
    all_data = []
    
    for i, symbol in enumerate(symbols):
        # Rate limiting
        if i > 0:
            time.sleep(RATE_LIMIT_DELAY)
        
        # Try cache first
        cached_df = load_from_cache(symbol)
        if cached_df is not None and 'stale' not in cached_df.columns:
            all_data.append(cached_df)
            continue
        
        # Try live fetch
        try:
            df = fetch_symbol_data(symbol, lookback_days)
            save_to_cache(symbol, df)
            all_data.append(df)
        except Exception as e:
            logger.error(f"Failed to fetch {symbol}: {e}")
            
            # Use stale cache if available
            if cached_df is not None:
                all_data.append(cached_df)
            else:
                # Use fallback sample with this symbol
                fallback = FALLBACK_SAMPLE.copy()
                fallback['symbol'] = symbol
                fallback['stale'] = True
                all_data.append(fallback)
    
    if not all_data:
        logger.error("No data fetched, returning fallback sample")
        return FALLBACK_SAMPLE
    
    result = pd.concat(all_data, ignore_index=True)
    
    # Mark if any data is stale
    if 'stale' in result.columns:
        result['is_stale'] = result.get('stale', False).fillna(False)
        result = result.drop(columns=['stale'], errors='ignore')
    else:
        result['is_stale'] = False
    
    return result