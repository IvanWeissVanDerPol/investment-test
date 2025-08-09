"""Technical analysis module for generating trading signals."""

import logging
from typing import List, Dict, Any

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def calculate_sma(series: pd.Series, window: int) -> pd.Series:
    """Calculate Simple Moving Average."""
    return series.rolling(window=window, min_periods=1).mean()


def calculate_rsi(series: pd.Series, window: int = 14) -> pd.Series:
    """Calculate Relative Strength Index."""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window, min_periods=1).mean()
    
    # Avoid division by zero
    rs = gain / loss.replace(0, 1e-10)
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add technical indicators to price data.
    
    Args:
        df: DataFrame with price data
    
    Returns:
        DataFrame with added indicators: SMA_20, SMA_50, RSI_14
    """
    result = df.copy()
    
    # Group by symbol for indicator calculation
    for symbol in result['symbol'].unique():
        mask = result['symbol'] == symbol
        symbol_data = result[mask].sort_values('date')
        
        # Calculate indicators
        result.loc[mask, 'sma_20'] = calculate_sma(symbol_data['close'], 20).values
        result.loc[mask, 'sma_50'] = calculate_sma(symbol_data['close'], 50).values
        result.loc[mask, 'rsi_14'] = calculate_rsi(symbol_data['close'], 14).values
    
    logger.info(f"Added indicators for {len(result['symbol'].unique())} symbols")
    
    return result


def generate_signal_for_row(row: pd.Series) -> str:
    """Generate signal for a single row based on indicators."""
    # Skip if indicators not available
    if pd.isna(row['sma_20']) or pd.isna(row['sma_50']) or pd.isna(row['rsi_14']):
        return 'hold'
    
    # SMA crossover signals
    sma_diff = row['sma_20'] - row['sma_50']
    
    # RSI extremes
    rsi = row['rsi_14']
    
    # Generate signal
    if sma_diff > 0:  # SMA20 above SMA50 (bullish)
        if rsi < 30:  # Oversold
            return 'buy'
        elif rsi > 70:  # Overbought but trending up
            return 'hold'
        else:
            return 'buy'
    elif sma_diff < 0:  # SMA20 below SMA50 (bearish)
        if rsi > 70:  # Overbought
            return 'sell'
        elif rsi < 30:  # Oversold but trending down
            return 'hold'
        else:
            return 'sell'
    else:
        return 'hold'


def generate_signals(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Generate trading signals from price data with indicators.
    
    Args:
        df: DataFrame with price data and indicators
    
    Returns:
        List of signal dictionaries with keys:
        {symbol, ts, signal, rsi, sma20, sma50}
    """
    # Ensure indicators are present
    if 'sma_20' not in df.columns:
        df = add_indicators(df)
    
    signals = []
    
    # Group by symbol and get latest data points
    for symbol in df['symbol'].unique():
        symbol_data = df[df['symbol'] == symbol].sort_values('date')
        
        # Skip warmup period (need at least 50 rows for SMA50)
        if len(symbol_data) < 50:
            logger.warning(f"Insufficient data for {symbol}, using available data")
        
        # Drop rows with NaN in indicators (warmup period)
        clean_data = symbol_data.dropna(subset=['sma_20', 'sma_50', 'rsi_14'])
        
        if clean_data.empty:
            logger.warning(f"No valid signals for {symbol} after warmup")
            continue
        
        # Generate signals for recent data (last 5 days or available)
        recent_data = clean_data.tail(5)
        
        for _, row in recent_data.iterrows():
            signal = generate_signal_for_row(row)
            
            signals.append({
                'symbol': symbol,
                'ts': pd.Timestamp(row['date']).isoformat(),
                'signal': signal,
                'rsi': round(row['rsi_14'], 2),
                'sma20': round(row['sma_20'], 2),
                'sma50': round(row['sma_50'], 2),
                'close': round(row['close'], 2),
                'is_stale': row.get('is_stale', False)
            })
    
    logger.info(f"Generated {len(signals)} signals for {len(df['symbol'].unique())} symbols")
    
    return signals