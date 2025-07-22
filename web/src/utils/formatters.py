"""
Utility functions for formatting data for display.
"""

def format_currency(value: float, currency: str = "USD") -> str:
    """Format a number as currency."""
    if value is None:
        return "$0.00"
    
    symbols = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£"
    }
    
    symbol = symbols.get(currency, "$")
    return f"{symbol}{value:,.2f}"

def format_percentage(value: float, decimals: int = 2) -> str:
    """Format a number as percentage."""
    if value is None:
        return "0.00%"
    
    return f"{value:.{decimals}f}%"

def format_large_number(value: float) -> str:
    """Format large numbers with abbreviations."""
    if value is None:
        return "0"
    
    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f}B"
    elif abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    elif abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"
    else:
        return f"{int(value)}"

def get_performance_color(value: float) -> str:
    """Get color class based on performance."""
    if value is None:
        return "text-muted"
    
    if value > 0:
        return "text-success"
    elif value < 0:
        return "text-danger"
    else:
        return "text-muted"

def get_performance_icon(value: float) -> str:
    """Get icon class based on performance."""
    if value is None:
        return "fas fa-minus"
    
    if value > 0:
        return "fas fa-arrow-up"
    elif value < 0:
        return "fas fa-arrow-down"
    else:
        return "fas fa-minus"

def format_market_cap_category(market_cap: float) -> str:
    """Format market cap into category."""
    if market_cap is None:
        return "Unknown"
    
    if market_cap >= 200_000_000_000:
        return "Mega Cap"
    elif market_cap >= 10_000_000_000:
        return "Large Cap"
    elif market_cap >= 2_000_000_000:
        return "Mid Cap"
    elif market_cap >= 300_000_000:
        return "Small Cap"
    elif market_cap >= 50_000_000:
        return "Micro Cap"
    else:
        return "Nano Cap"

def format_risk_score(score: float) -> str:
    """Format risk score into text."""
    if score is None:
        return "Unknown"
    
    if score <= 20:
        return "Very Low"
    elif score <= 40:
        return "Low"
    elif score <= 60:
        return "Medium"
    elif score <= 80:
        return "High"
    else:
        return "Very High"

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length."""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length].rsplit(' ', 1)[0] + "..."

def format_date(date_str: str, format_str: str = "%Y-%m-%d") -> str:
    """Format date string."""
    if not date_str:
        return ""
    
    try:
        from datetime import datetime
        date = datetime.fromisoformat(date_str)
        return date.strftime(format_str)
    except ValueError:
        return date_str

def format_time_ago(date_str: str) -> str:
    """Format date as time ago."""
    if not date_str:
        return "Never"
    
    try:
        from datetime import datetime
        date = datetime.fromisoformat(date_str)
        now = datetime.now()
        diff = now - date
        
        if diff.days > 365:
            return f"{diff.days // 365}y ago"
        elif diff.days > 30:
            return f"{diff.days // 30}mo ago"
        elif diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600}h ago"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60}m ago"
        else:
            return "Just now"
    except ValueError:
        return date_str