#!/usr/bin/env python3
"""
Investment System MCP Server
Provides structured access to investment system data and operations
"""

import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime

class InvestmentMCPServer:
    def __init__(self, db_path=None):
        if db_path is None:
            self.db_path = Path(__file__).parent.parent / "investment_system.db"
        else:
            self.db_path = Path(db_path)
    
    def get_portfolio_summary(self):
        """Get portfolio summary"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_securities,
                SUM(CASE WHEN security_type = 'stock' THEN 1 ELSE 0 END) as stocks,
                SUM(CASE WHEN security_type = 'etf' THEN 1 ELSE 0 END) as etfs
            FROM securities
        """)
        
        result = dict(cursor.fetchone())
        conn.close()
        
        return {
            "portfolio_summary": result,
            "timestamp": datetime.now().isoformat(),
            "status": "active"
        }
    
    def get_target_stocks(self):
        """Get target AI/robotics stocks"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT s.symbol, s.name, s.sector, s.market_cap_category
            FROM securities s
            JOIN security_categories sc ON s.id = sc.security_id
            JOIN categories c ON sc.category_id = c.id
            WHERE c.category_name IN ('ai_software', 'ai_hardware', 'robotics')
            AND s.security_type = 'stock'
            ORDER BY s.symbol
        """)
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {
            "target_stocks": results,
            "count": len(results),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_user_profile(self):
        """Get user profile configuration"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM user_profile LIMIT 1")
        profile = dict(cursor.fetchone()) if cursor.fetchone() else {}
        
        # Get goals
        if profile:
            cursor.execute("""
                SELECT g.goal FROM investment_goals g
                JOIN user_goals ug ON g.id = ug.goal_id
                WHERE ug.user_id = ?
            """, (profile['id'],))
            goals = [row['goal'] for row in cursor.fetchall()]
            profile['investment_goals'] = goals
        
        conn.close()
        return profile
    
    def get_analysis_settings(self):
        """Get analysis configuration"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Confidence thresholds
        cursor.execute("SELECT name, value FROM analysis_settings WHERE setting_type = 'confidence_threshold'")
        confidence = {row['name']: row['value'] for row in cursor.fetchall()}
        
        # Alert thresholds
        cursor.execute("SELECT name, value FROM analysis_settings WHERE setting_type = 'alert_threshold'")
        alerts = {row['name']: row['value'] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            "confidence_thresholds": confidence,
            "alert_thresholds": alerts
        }
    
    def get_smart_money_funds(self):
        """Get smart money institutions"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, focus_area, priority, metadata_json
            FROM institutions
            ORDER BY 
                CASE priority 
                    WHEN 'high' THEN 1 
                    WHEN 'medium' THEN 2 
                    WHEN 'low' THEN 3 
                END
        """)
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {
            "smart_money_funds": results,
            "count": len(results)
        }
    
    def get_defense_contractors(self):
        """Get defense contractors"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, symbol, ai_focus, government_contracts, metadata_json
            FROM defense_contractors
            ORDER BY ai_focus DESC, name
        """)
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {
            "defense_contractors": results,
            "count": len(results)
        }
    
    def get_ethics_config(self):
        """Get ethics configuration"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Blacklist
        cursor.execute("SELECT symbol, name, reason, alternative_symbol FROM ethics_blacklist")
        blacklist = [dict(row) for row in cursor.fetchall()]
        
        # Preferred categories
        cursor.execute("SELECT category_name FROM ethics_categories WHERE category_type = 'preferred'")
        preferred = [row['category_name'] for row in cursor.fetchall()]
        
        # Blocked categories
        cursor.execute("SELECT category_name FROM ethics_categories WHERE category_type = 'blocked'")
        blocked = [row['category_name'] for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            "ethics_configuration": {
                "blacklist": blacklist,
                "preferred_categories": preferred,
                "blocked_categories": blocked
            }
        }
    
    def get_keywords(self, keyword_type=None):
        """Get keywords for analysis"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if keyword_type:
            cursor.execute("""
                SELECT keyword FROM keywords 
                WHERE keyword_type = ? AND enabled = 1
            """, (keyword_type,))
        else:
            cursor.execute("SELECT keyword_type, keyword FROM keywords WHERE enabled = 1")
        
        if keyword_type:
            keywords = [row['keyword'] for row in cursor.fetchall()]
            return {f"{keyword_type}_keywords": keywords}
        else:
            keywords = {}
            for row in cursor.fetchall():
                kw_type = row['keyword_type']
                if kw_type not in keywords:
                    keywords[kw_type] = []
                keywords[kw_type].append(row['keyword'])
            return keywords
        
        conn.close()

# CLI interface for testing
if __name__ == "__main__":
    import sys
    
    server = InvestmentMCPServer()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "portfolio":
            print(json.dumps(server.get_portfolio_summary(), indent=2))
        elif command == "stocks":
            print(json.dumps(server.get_target_stocks(), indent=2))
        elif command == "profile":
            print(json.dumps(server.get_user_profile(), indent=2))
        elif command == "settings":
            print(json.dumps(server.get_analysis_settings(), indent=2))
        elif command == "funds":
            print(json.dumps(server.get_smart_money_funds(), indent=2))
        elif command == "defense":
            print(json.dumps(server.get_defense_contractors(), indent=2))
        elif command == "ethics":
            print(json.dumps(server.get_ethics_config(), indent=2))
        elif command == "keywords":
            keyword_type = sys.argv[2] if len(sys.argv) > 2 else None
            print(json.dumps(server.get_keywords(keyword_type), indent=2))
        else:
            print(json.dumps({"error": f"Unknown command: {command}"}))
    else:
        print(json.dumps({
            "available_commands": [
                "portfolio", "stocks", "profile", "settings", 
                "funds", "defense", "ethics", "keywords"
            ]
        }, indent=2))