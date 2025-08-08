"""
Database module for investment system configuration
Provides database-backed configuration management
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

class DatabaseConfig:
    """Database configuration manager"""
    
    def __init__(self, db_path: str = "investment_system.db"):
        self.db_path = Path(__file__).parent.parent.parent / db_path
        self.conn = None
        self._ensure_database()
    
    def _ensure_database(self):
        """Ensure database exists and is initialized"""
        if not self.db_path.exists():
            self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database with schema"""
        from .migration import ConfigMigrator
        migrator = ConfigMigrator(str(self.db_path))
        migrator.migrate_all()
    
    def connect(self):
        """Connect to database"""
        if not self.conn:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def get_user_profile(self) -> Dict[str, Any]:
        """Get user profile configuration"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM user_profile LIMIT 1")
        profile = cursor.fetchone()
        
        if not profile:
            return {}
        
        # Get goals
        cursor.execute("""
            SELECT g.goal 
            FROM investment_goals g
            JOIN user_goals ug ON g.id = ug.goal_id
            WHERE ug.user_id = ?
        """, (profile['id'],))
        
        goals = [row['goal'] for row in cursor.fetchall()]
        
        return dict(profile) | {'investment_goals': goals}
    
    def get_target_stocks(self) -> List[str]:
        """Get target stocks from database"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT symbol FROM securities 
            WHERE security_type = 'stock'
        """)
        
        return [row['symbol'] for row in cursor.fetchall()]
    
    def get_target_etfs(self) -> List[str]:
        """Get target ETFs from database"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT symbol FROM securities 
            WHERE security_type = 'etf'
        """)
        
        return [row['symbol'] for row in cursor.fetchall()]
    
    def get_analysis_settings(self) -> Dict[str, Any]:
        """Get analysis settings"""
        conn = self.connect()
        cursor = conn.cursor()
        
        settings = {}
        
        # Confidence thresholds
        cursor.execute("""
            SELECT name, value FROM analysis_settings 
            WHERE setting_type = 'confidence_threshold'
        """)
        confidence = {row['name']: row['value'] for row in cursor.fetchall()}
        
        # Alert thresholds
        cursor.execute("""
            SELECT name, value FROM analysis_settings 
            WHERE setting_type = 'alert_threshold'
        """)
        alerts = {row['name']: row['value'] for row in cursor.fetchall()}
        
        return {
            'confidence_thresholds': confidence,
            'alert_thresholds': alerts
        }
    
    def get_ethics_configuration(self) -> Dict[str, Any]:
        """Get ethics configuration"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Get blacklist
        cursor.execute("SELECT symbol, name, reason, alternative_symbol FROM ethics_blacklist")
        blacklist = [dict(row) for row in cursor.fetchall()]
        
        # Get preferred categories
        cursor.execute("""
            SELECT category_name FROM ethics_categories 
            WHERE category_type = 'preferred'
        """)
        preferred = [row['category_name'] for row in cursor.fetchall()]
        
        # Get blocked categories
        cursor.execute("""
            SELECT category_name FROM ethics_categories 
            WHERE category_type = 'blocked'
        """)
        blocked = [row['category_name'] for row in cursor.fetchall()]
        
        return {
            'blacklist': blacklist,
            'preferred_categories': preferred,
            'blocked_categories': blocked
        }
    
    def get_keywords(self, keyword_type: str = None) -> List[str]:
        """Get keywords by type"""
        conn = self.connect()
        cursor = conn.cursor()
        
        if keyword_type:
            cursor.execute("""
                SELECT keyword FROM keywords 
                WHERE keyword_type = ? AND enabled = 1
            """, (keyword_type,))
        else:
            cursor.execute("SELECT keyword FROM keywords WHERE enabled = 1")
        
        return [row['keyword'] for row in cursor.fetchall()]
    
    def get_institutions(self, priority: str = None) -> List[Dict[str, Any]]:
        """Get institutions, optionally filtered by priority"""
        conn = self.connect()
        cursor = conn.cursor()
        
        if priority:
            cursor.execute("""
                SELECT * FROM institutions 
                WHERE priority = ?
            """, (priority,))
        else:
            cursor.execute("SELECT * FROM institutions")
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_defense_contractors(self) -> List[Dict[str, Any]]:
        """Get defense contractors"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM defense_contractors")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_government_agencies(self) -> List[Dict[str, Any]]:
        """Get government agencies"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM government_agencies")
        return [dict(row) for row in cursor.fetchall()]
    
    def cache_analysis_result(self, analysis_type: str, symbol: str, 
                             result_data: Dict, confidence_score: float, 
                             expires_hours: int = 24):
        """Cache analysis result"""
        conn = self.connect()
        cursor = conn.cursor()
        
        expires_at = datetime.now()
        expires_at = expires_at.replace(hour=expires_at.hour + expires_hours)
        
        cursor.execute("""
            INSERT INTO analysis_cache (analysis_type, security_symbol, 
                                      result_data, confidence_score, expires_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            analysis_type,
            symbol,
            json.dumps(result_data),
            confidence_score,
            expires_at
        ))
        
        conn.commit()
    
    def get_cached_analysis(self, analysis_type: str, symbol: str) -> Optional[Dict]:
        """Get cached analysis result if not expired"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT result_data, confidence_score, expires_at
            FROM analysis_cache
            WHERE analysis_type = ? AND security_symbol = ?
            AND expires_at > datetime('now')
            ORDER BY created_timestamp DESC
            LIMIT 1
        """, (analysis_type, symbol))
        
        row = cursor.fetchone()
        if row:
            return {
                'result': json.loads(row['result_data']),
                'confidence': row['confidence_score'],
                'expires_at': row['expires_at']
            }
        
        return None
    
    def update_portfolio_holding(self, symbol: str, shares: float, 
                                average_cost: float, current_price: float):
        """Update portfolio holding"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Get security ID
        cursor.execute("SELECT id FROM securities WHERE symbol = ?", (symbol,))
        security_row = cursor.fetchone()
        
        if not security_row:
            # Create security if it doesn't exist
            cursor.execute("""
                INSERT INTO securities (symbol, name, security_type)
                VALUES (?, ?, 'stock')
            """, (symbol, symbol))
            security_id = cursor.lastrowid
        else:
            security_id = security_row['id']
        
        # Update or insert holding
        cursor.execute("""
            INSERT OR REPLACE INTO portfolio_holdings 
            (security_id, shares, average_cost, current_price, last_updated)
            VALUES (?, ?, ?, ?, datetime('now'))
        """, (security_id, shares, average_cost, current_price))
        
        conn.commit()
    
    def get_portfolio_holdings(self) -> List[Dict[str, Any]]:
        """Get all portfolio holdings"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT s.symbol, s.name, ph.shares, ph.average_cost, 
                   ph.current_price, ph.last_updated
            FROM portfolio_holdings ph
            JOIN securities s ON ph.security_id = s.id
            ORDER BY s.symbol
        """)
        
        return [dict(row) for row in cursor.fetchall()]

# Global database instance
_db_instance = None

def get_database():
    """Get global database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseConfig()
    return _db_instance

def close_database():
    """Close global database instance"""
    global _db_instance
    if _db_instance:
        _db_instance.close()
        _db_instance = None

# Convenience functions
def get_config():
    """Get configuration from database"""
    db = get_database()
    return {
        'user_profile': db.get_user_profile(),
        'target_stocks': db.get_target_stocks(),
        'target_etfs': db.get_target_etfs(),
        'analysis_settings': db.get_analysis_settings(),
        'ethics_configuration': db.get_ethics_configuration(),
        'ai_keywords': db.get_keywords('ai'),
        'sustainability_keywords': db.get_keywords('sustainability'),
        'institutions': db.get_institutions(),
        'defense_contractors': db.get_defense_contractors(),
        'government_agencies': db.get_government_agencies()
    }

if __name__ == "__main__":
    # Test database
    db = get_database()
    config = get_config()
    print("Database initialized successfully!")
    print(f"Target stocks: {len(config['target_stocks'])} securities")
    print(f"Target ETFs: {len(config['target_etfs'])} ETFs")
    print(f"AI keywords: {len(config['ai_keywords'])} keywords")
    print(f"Institutions: {len(config['institutions'])} tracked")
    close_database()