#!/usr/bin/env python3
"""
Database Setup Script
Sets up the SQLite database for the investment system
"""

import os
import sys
from pathlib import Path

def setup_database():
    """Complete database setup"""
    print("Setting up investment system database...")
    
    # Add core directory to path
    current_dir = Path(__file__).parent.parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    
    # Import and run migration
    from database.migration import ConfigMigrator
    
    db_path = Path(__file__).parent.parent.parent / "investment_system.db"
    migrator = ConfigMigrator(str(db_path))
    
    try:
        migrator.migrate_all()
        print("✅ Database setup completed successfully!")
        print(f"📊 Database location: {db_path}")
        
        # Verify database
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"📋 Created {len(tables)} tables:")
        for table in tables:
            print(f"   - {table[0]}")
        
        # Check data count
        cursor.execute("SELECT COUNT(*) FROM securities")
        security_count = cursor.fetchone()[0]
        print(f"📈 Migrated {security_count} securities")
        
        cursor.execute("SELECT COUNT(*) FROM institutions")
        institution_count = cursor.fetchone()[0]
        print(f"🏢 Migrated {institution_count} institutions")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_database()