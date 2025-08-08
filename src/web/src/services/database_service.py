import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
import json
from contextlib import contextmanager

from ..models.portfolio import Position, PortfolioSummary, SectorAllocation

class DatabaseService:
    """Service class for database operations."""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def get_portfolio_summary(self) -> Optional[PortfolioSummary]:
        """Get the latest portfolio summary."""
        with self.get_connection() as conn:
            row = conn.execute('''
                SELECT * FROM portfolio_summary 
                ORDER BY date DESC LIMIT 1
            ''').fetchone()
            
            if row:
                return PortfolioSummary(
                    total_value=row['total_value'] or 0,
                    available_cash=row['available_cash'] or 0,
                    invested_amount=row['invested_amount'] or 0,
                    daily_change=row['daily_change'] or 0,
                    daily_change_percent=row['daily_change_percent'] or 0,
                    ai_allocation_percent=row['ai_allocation_percent'] or 0,
                    green_allocation_percent=row['green_allocation_percent'] or 0,
                    total_return=row['total_return'] or 0,
                    total_return_percent=row['total_return_percent'] or 0,
                    last_updated=datetime.fromisoformat(row['date'])
                )
            return None
    
    def get_positions(self) -> List[Position]:
        """Get all current positions."""
        with self.get_connection() as conn:
            rows = conn.execute('''
                SELECT p.*, s.name, s.sector, s.industry, s.market_cap
                FROM positions p
                JOIN stocks s ON p.symbol = s.symbol
                WHERE p.quantity > 0
                ORDER BY p.market_value DESC
            ''').fetchall()
            
            positions = []
            for row in rows:
                positions.append(Position(
                    symbol=row['symbol'],
                    name=row['name'],
                    sector=row['sector'],
                    industry=row['industry'],
                    quantity=row['quantity'] or 0,
                    average_cost=row['average_cost'] or 0,
                    current_price=row['current_price'] or 0,
                    market_value=row['market_value'] or 0,
                    unrealized_pnl=row['unrealized_pnl'] or 0,
                    unrealized_pnl_percent=row['unrealized_pnl_percent'] or 0,
                    market_cap=row['market_cap']
                ))
            return positions
    
    def get_sector_allocations(self) -> List[SectorAllocation]:
        """Get sector allocations."""
        with self.get_connection() as conn:
            rows = conn.execute('''
                SELECT sector, SUM(market_value) as total_value, 
                       AVG(performance_1d) as avg_performance
                FROM positions p
                JOIN stocks s ON p.symbol = s.symbol
                WHERE p.quantity > 0
                GROUP BY sector
                ORDER BY total_value DESC
            ''').fetchall()
            
            allocations = []
            total_value = sum(row['total_value'] for row in rows)
            
            for row in rows:
                allocations.append(SectorAllocation(
                    sector=row['sector'],
                    total_value=row['total_value'] or 0,
                    percentage=(row['total_value'] or 0) / total_value * 100,
                    avg_performance=row['avg_performance'] or 0
                ))
            return allocations
    
    def get_portfolio_history(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get portfolio history for charting."""
        with self.get_connection() as conn:
            rows = conn.execute('''
                SELECT * FROM portfolio_summary 
                WHERE date >= date('now', '-{} days')
                ORDER BY date ASC
            '''.format(days)).fetchall()
            
            history = []
            for row in rows:
                history.append({
                    'date': row['date'],
                    'total_value': row['total_value'],
                    'daily_change': row['daily_change'],
                    'daily_change_percent': row['daily_change_percent']
                })
            return history
    
    def get_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent alerts."""
        with self.get_connection() as conn:
            rows = conn.execute('''
                SELECT * FROM alerts 
                ORDER BY created_at DESC LIMIT ?
            ''', (limit,)).fetchall()
            
            alerts = []
            for row in rows:
                alerts.append({
                    'id': row['id'],
                    'title': row['title'],
                    'description': row['description'],
                    'severity': row['severity'],
                    'type': row['type'],
                    'created_at': row['created_at']
                })
            return alerts
    
    def get_stocks(self) -> List[Dict[str, Any]]:
        """Get all tracked stocks."""
        with self.get_connection() as conn:
            rows = conn.execute('''
                SELECT s.*, 
                       a.signal as latest_signal,
                       a.confidence as signal_confidence,
                       a.created_at as last_analysis
                FROM stocks s
                LEFT JOIN analysis_results a ON s.symbol = a.symbol
                ORDER BY s.market_cap DESC
            ''').fetchall()
            
            stocks = []
            for row in rows:
                stocks.append(dict(row))
            return stocks
    
    def get_stock_detail(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get detailed stock information."""
        with self.get_connection() as conn:
            stock = conn.execute('SELECT * FROM stocks WHERE symbol = ?', (symbol,)).fetchone()
            if not stock:
                return None
            
            # Get analysis history
            analysis = conn.execute('''
                SELECT * FROM analysis_results 
                WHERE symbol = ? ORDER BY created_at DESC LIMIT 10
            ''', (symbol,)).fetchall()
            
            # Get price history
            prices = conn.execute('''
                SELECT * FROM price_history 
                WHERE symbol = ? ORDER BY date DESC LIMIT 90
            ''', (symbol,)).fetchall()
            
            # Get news sentiment
            news = conn.execute('''
                SELECT * FROM news_sentiment 
                WHERE symbol = ? ORDER BY published_at DESC LIMIT 20
            ''', (symbol,)).fetchall()
            
            return {
                'stock': dict(stock),
                'analysis': [dict(a) for a in analysis],
                'prices': [dict(p) for p in prices],
                'news': [dict(n) for n in news]
            }
    
    def get_price_history(self, symbol: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get price history for a stock."""
        with self.get_connection() as conn:
            rows = conn.execute('''
                SELECT date, close, volume
                FROM price_history 
                WHERE symbol = ? 
                ORDER BY date DESC LIMIT ?
            ''', (symbol, days)).fetchall()
            
            return [dict(row) for row in reversed(rows)]
    
    def update_position(self, symbol: str, updates: Dict[str, Any]) -> bool:
        """Update a position."""
        with self.get_connection() as conn:
            set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values()) + [symbol]
            
            result = conn.execute(f'''
                UPDATE positions SET {set_clause}
                WHERE symbol = ?
            ''', values)
            
            conn.commit()
            return result.rowcount > 0