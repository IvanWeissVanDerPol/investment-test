#!/usr/bin/env python3
"""
Database Migration Script
Converts JSON configuration files to SQLite database
"""

import json
import sqlite3
import os
from pathlib import Path
from datetime import datetime

class ConfigMigrator:
    def __init__(self, db_path="investment_system.db"):
        self.db_path = Path(db_path)
        self.config_dir = Path("../../config")
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Connect to SQLite database"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
    def create_tables(self):
        """Create database tables from schema"""
        schema_path = Path(__file__).parent / "schema.sql"
        
        with open(schema_path, 'r') as f:
            schema = f.read()
            
        # Execute schema creation
        self.cursor.executescript(schema)
        self.conn.commit()
        
    def migrate_user_profile(self, config_data):
        """Migrate user profile from JSON"""
        user = config_data.get('user_profile', {})
        
        self.cursor.execute("""
            INSERT INTO user_profile (
                name, email, dukascopy_balance, interactive_brokers_balance,
                total_portfolio_value, currency, risk_tolerance,
                target_ai_allocation_percent, target_green_allocation_percent,
                max_single_position_percent, account_id, created_date, timezone
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user.get('name', 'Ivan'),
            user.get('email', ''),
            user.get('dukascopy_balance', 900),
            user.get('interactive_brokers_balance', 0),
            user.get('total_portfolio_value', 900),
            user.get('currency', 'USD'),
            user.get('risk_tolerance', 'medium'),
            user.get('target_ai_allocation_percent', 50),
            user.get('target_green_allocation_percent', 30),
            user.get('max_single_position_percent', 15),
            user.get('account_id', ''),
            user.get('created_date', '2025-01-20'),
            user.get('timezone', 'UTC')
        ))
        
        user_id = self.cursor.lastrowid
        
        # Migrate investment goals
        goals = user.get('investment_goals', [])
        for goal in goals:
            self.cursor.execute(
                "INSERT OR IGNORE INTO investment_goals (goal) VALUES (?)",
                (goal,)
            )
            self.cursor.execute(
                "SELECT id FROM investment_goals WHERE goal = ?",
                (goal,)
            )
            goal_id = self.cursor.fetchone()[0]
            
            self.cursor.execute(
                "INSERT INTO user_goals (user_id, goal_id) VALUES (?, ?)",
                (user_id, goal_id)
            )
            
    def migrate_broker_config(self, config_data):
        """Migrate broker configuration"""
        ib_config = config_data.get('interactive_brokers', {})
        
        self.cursor.execute("""
            INSERT INTO broker_config (
                broker_name, enabled, connection_type, host, tws_port,
                gateway_port, client_id, auto_sync, sync_interval_minutes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'Interactive Brokers',
            ib_config.get('enabled', True),
            ib_config.get('connection_type', 'auto'),
            ib_config.get('host', '127.0.0.1'),
            ib_config.get('tws_port', 7497),
            ib_config.get('gateway_port', 4001),
            ib_config.get('client_id', 1),
            ib_config.get('auto_sync', True),
            ib_config.get('sync_interval_minutes', 15)
        ))
        
    def migrate_api_config(self, config_data):
        """Migrate API configurations"""
        # Alpha Vantage
        alpha_config = config_data.get('alpha_vantage', {})
        self.cursor.execute("""
            INSERT INTO api_config (service_name, api_key, base_url, enabled)
            VALUES (?, ?, ?, ?)
        """, (
            'Alpha Vantage',
            alpha_config.get('api_key', 'demo'),
            alpha_config.get('base_url', 'https://www.alphavantage.co/query'),
            True
        ))
        
    def migrate_securities(self, data_config):
        """Migrate securities data"""
        companies = data_config.get('companies', {})
        
        # Migrate stocks
        stock_universe = companies.get('stock_universe', {})
        for category, symbols in stock_universe.items():
            # Ensure category exists
            self.cursor.execute(
                "INSERT OR IGNORE INTO categories (category_name, category_type) VALUES (?, ?)",
                (category, 'sector')
            )
            
            self.cursor.execute(
                "SELECT id FROM categories WHERE category_name = ?",
                (category,)
            )
            category_id = self.cursor.fetchone()[0]
            
            for symbol in symbols:
                # Insert security
                self.cursor.execute("""
                    INSERT OR IGNORE INTO securities (symbol, name, sector, security_type)
                    VALUES (?, ?, ?, ?)
                """, (symbol, symbol, category, 'stock'))
                
                self.cursor.execute(
                    "SELECT id FROM securities WHERE symbol = ?",
                    (symbol,)
                )
                security_id = self.cursor.fetchone()[0]
                
                # Link to category
                self.cursor.execute(
                    "INSERT OR IGNORE INTO security_categories (security_id, category_id) VALUES (?, ?)",
                    (security_id, category_id)
                )
        
        # Migrate ETFs
        etfs = companies.get('etfs', {})
        for etf_category, etf_list in etfs.items():
            for etf_symbol in etf_list:
                self.cursor.execute("""
                    INSERT OR IGNORE INTO securities (symbol, name, sector, security_type)
                    VALUES (?, ?, ?, ?)
                """, (etf_symbol, etf_symbol, etf_category, 'etf'))
        
        # Migrate company metadata
        company_metadata = companies.get('company_metadata', {})
        for symbol, meta in company_metadata.items():
            self.cursor.execute("""
                UPDATE securities 
                SET name = ?, sector = ?, market_cap_category = ?
                WHERE symbol = ?
            """, (
                meta.get('name', symbol),
                meta.get('sector', 'Unknown'),
                meta.get('market_cap_category', 'unknown'),
                symbol
            ))
            
    def migrate_institutions(self, data_config):
        """Migrate institutional data"""
        institutions = data_config.get('institutions', {})
        
        # Smart money funds
        smart_funds = institutions.get('smart_money_funds', [])
        for fund in smart_funds:
            self.cursor.execute("""
                INSERT INTO institutions (name, focus_area, priority)
                VALUES (?, ?, ?)
            """, (
                fund['name'],
                fund.get('focus', 'general'),
                fund.get('priority', 'medium')
            ))
            
        # Defense contractors
        defense_contractors = institutions.get('defense_contractors', [])
        for contractor in defense_contractors:
            self.cursor.execute("""
                INSERT INTO defense_contractors (name, symbol, ai_focus, government_contracts)
                VALUES (?, ?, ?, ?)
            """, (
                contractor['name'],
                contractor.get('symbol'),
                contractor.get('ai_focus', 'medium'),
                contractor.get('government_contracts', 'medium')
            ))
            
        # Government agencies
        agencies = institutions.get('government_agencies', [])
        for agency in agencies:
            self.cursor.execute("""
                INSERT INTO government_agencies (name, abbreviation, ai_budget_level)
                VALUES (?, ?, ?)
            """, (
                agency['name'],
                agency.get('abbreviation'),
                agency.get('ai_budget', 'medium')
            ))
            
    def migrate_ethics_config(self, config_data):
        """Migrate ethics configuration"""
        ethics = config_data.get('ethics_preferences', {})
        
        # Migrate ethics blacklist
        blacklist = ethics.get('blacklist', [])
        for item in blacklist:
            self.cursor.execute("""
                INSERT INTO ethics_blacklist (symbol, name, reason, alternative_symbol)
                VALUES (?, ?, ?, ?)
            """, (
                item['symbol'],
                item['name'],
                item['reason'],
                item.get('alternative')
            ))
            
    def migrate_keywords(self, config_data):
        """Migrate keywords configuration"""
        # AI keywords
        ai_keywords = config_data.get('ai_keywords', [])
        for keyword in ai_keywords:
            self.cursor.execute(
                "INSERT OR IGNORE INTO keywords (keyword_type, keyword) VALUES (?, ?)",
                ('ai', keyword)
            )
            
        # Sustainability keywords
        sustainability_keywords = config_data.get('sustainability_keywords', [])
        for keyword in sustainability_keywords:
            self.cursor.execute(
                "INSERT OR IGNORE INTO keywords (keyword_type, keyword) VALUES (?, ?)",
                ('sustainability', keyword)
            )
            
    def migrate_analysis_settings(self, config_data):
        """Migrate analysis settings"""
        analysis = config_data.get('analysis_settings', {})
        
        # Confidence thresholds
        thresholds = analysis.get('confidence_thresholds', {})
        for name, value in thresholds.items():
            self.cursor.execute(
                "INSERT INTO analysis_settings (setting_type, name, value, description) VALUES (?, ?, ?, ?)",
                ('confidence_threshold', name, value, f'Confidence threshold for {name}')
            )
            
        # Alert thresholds
        alerts = analysis.get('alert_thresholds', {})
        for name, value in alerts.items():
            self.cursor.execute(
                "INSERT INTO analysis_settings (setting_type, name, value, description) VALUES (?, ?, ?, ?)",
                ('alert_threshold', name, value, f'Alert threshold for {name}')
            )
            
    def migrate_all(self):
        """Run complete migration"""
        print("Starting database migration...")
        
        # Load configuration files
        config_path = self.config_dir / "config.json"
        data_path = self.config_dir / "data.json"
        
        if not config_path.exists() or not data_path.exists():
            print("Error: Configuration files not found")
            return
            
        with open(config_path, 'r') as f:
            config_data = json.load(f)
            
        with open(data_path, 'r') as f:
            data_config = json.load(f)
            
        # Connect to database
        self.connect()
        
        # Create tables
        print("Creating database tables...")
        self.create_tables()
        
        # Migrate data
        print("Migrating user profile...")
        self.migrate_user_profile(config_data)
        
        print("Migrating broker configuration...")
        self.migrate_broker_config(config_data)
        
        print("Migrating API configuration...")
        self.migrate_api_config(config_data)
        
        print("Migrating securities...")
        self.migrate_securities(data_config)
        
        print("Migrating institutions...")
        self.migrate_institutions(data_config)
        
        print("Migrating ethics configuration...")
        self.migrate_ethics_config(config_data)
        
        print("Migrating keywords...")
        self.migrate_keywords(config_data)
        
        print("Migrating analysis settings...")
        self.migrate_analysis_settings(config_data)
        
        # Commit changes
        self.conn.commit()
        print("Migration completed successfully!")
        
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

if __name__ == "__main__":
    migrator = ConfigMigrator()
    try:
        migrator.migrate_all()
    finally:
        migrator.close()