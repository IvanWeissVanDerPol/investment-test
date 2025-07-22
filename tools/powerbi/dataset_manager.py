#!/usr/bin/env python3
"""
Power BI Dataset Management Tools
Automates dataset creation, updates, and management for investment system
"""

import json
import os
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import sys
import requests
from typing import Dict, List, Optional, Any

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))
from mcp.powerbi_mcp import PowerBIMCPServer

class PowerBIDatasetManager:
    """Manages Power BI datasets for investment system"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.powerbi_server = PowerBIMCPServer(config_path)
        self.db_path = Path(__file__).parent.parent.parent / "investment_system.db"
        self.exports_dir = Path(__file__).parent.parent.parent / "powerbi_project" / "exports"
        
    def create_investment_dataset_schema(self) -> Dict[str, Any]:
        """Define Power BI dataset schema for investment data"""
        schema = {
            "name": "InvestmentSystemData",
            "tables": [
                {
                    "name": "PortfolioSummary",
                    "columns": [
                        {"name": "total_securities", "dataType": "Int64"},
                        {"name": "stocks", "dataType": "Int64"},
                        {"name": "etfs", "dataType": "Int64"},
                        {"name": "sectors", "dataType": "Int64"},
                        {"name": "last_updated", "dataType": "DateTime"}
                    ]
                },
                {
                    "name": "AIRoboticsStocks", 
                    "columns": [
                        {"name": "symbol", "dataType": "String"},
                        {"name": "name", "dataType": "String"},
                        {"name": "sector", "dataType": "String"},
                        {"name": "market_cap_category", "dataType": "String"},
                        {"name": "price_52w_high", "dataType": "Double"},
                        {"name": "price_52w_low", "dataType": "Double"},
                        {"name": "current_price", "dataType": "Double"},
                        {"name": "ytd_performance_pct", "dataType": "Double"},
                        {"name": "investment_category", "dataType": "String"}
                    ]
                },
                {
                    "name": "EthicsScreening",
                    "columns": [
                        {"name": "symbol", "dataType": "String"},
                        {"name": "name", "dataType": "String"},
                        {"name": "reason", "dataType": "String"},
                        {"name": "alternative_symbol", "dataType": "String"},
                        {"name": "created_at", "dataType": "DateTime"}
                    ]
                },
                {
                    "name": "SmartMoneyInstitutions",
                    "columns": [
                        {"name": "name", "dataType": "String"},
                        {"name": "focus_area", "dataType": "String"},
                        {"name": "priority", "dataType": "String"},
                        {"name": "metadata_json", "dataType": "String"}
                    ]
                },
                {
                    "name": "AnalysisSettings",
                    "columns": [
                        {"name": "setting_type", "dataType": "String"},
                        {"name": "name", "dataType": "String"},
                        {"name": "value", "dataType": "String"}
                    ]
                },
                {
                    "name": "DateDimension",
                    "columns": [
                        {"name": "Date", "dataType": "DateTime"},
                        {"name": "Year", "dataType": "Int64"},
                        {"name": "Quarter", "dataType": "Int64"},
                        {"name": "Month", "dataType": "Int64"},
                        {"name": "MonthName", "dataType": "String"},
                        {"name": "WeekOfYear", "dataType": "Int64"},
                        {"name": "DayOfYear", "dataType": "Int64"},
                        {"name": "DayOfMonth", "dataType": "Int64"},
                        {"name": "DayOfWeek", "dataType": "Int64"},
                        {"name": "DayName", "dataType": "String"},
                        {"name": "IsWeekend", "dataType": "Boolean"},
                        {"name": "FiscalYear", "dataType": "Int64"}
                    ]
                }
            ],
            "relationships": [
                {
                    "name": "EthicsToStocks",
                    "fromTable": "EthicsScreening",
                    "fromColumn": "symbol",
                    "toTable": "AIRoboticsStocks", 
                    "toColumn": "symbol",
                    "crossFilteringBehavior": "bothDirections"
                }
            ]
        }
        return schema
    
    def create_dataset(self, workspace_id: Optional[str] = None) -> Optional[str]:
        """Create new Power BI dataset"""
        workspace_id = workspace_id or self.powerbi_server.config.get("workspace_id")
        schema = self.create_investment_dataset_schema()
        
        if workspace_id:
            endpoint = f"groups/{workspace_id}/datasets"
        else:
            endpoint = "datasets"
        
        result = self.powerbi_server._make_api_request(endpoint, method="POST", data=schema)
        
        if result and "id" in result:
            dataset_id = result["id"]
            print(f"✅ Dataset created successfully: {dataset_id}")
            
            # Update config with new dataset ID
            self.powerbi_server.config["dataset_id"] = dataset_id
            with open(self.powerbi_server.config_path, 'w') as f:
                json.dump(self.powerbi_server.config, f, indent=2)
            
            return dataset_id
        else:
            print(f"❌ Failed to create dataset: {result}")
            return None
    
    def update_dataset_data(self, dataset_id: Optional[str] = None, workspace_id: Optional[str] = None) -> bool:
        """Update dataset with fresh investment data"""
        dataset_id = dataset_id or self.powerbi_server.config.get("dataset_id")
        workspace_id = workspace_id or self.powerbi_server.config.get("workspace_id")
        
        if not dataset_id:
            print("❌ Dataset ID required")
            return False
        
        # Get fresh data from investment system
        data = self.powerbi_server.get_investment_data_for_powerbi()
        if "error" in data:
            print(f"❌ Failed to get investment data: {data['error']}")
            return False
        
        success = True
        
        # Update each table
        tables_to_update = [
            ("PortfolioSummary", [data["portfolio_summary"]]),
            ("AIRoboticsStocks", data["ai_robotics_stocks"]),
            ("EthicsScreening", data["ethics_screening"]), 
            ("SmartMoneyInstitutions", data["smart_money_institutions"]),
            ("AnalysisSettings", data["analysis_settings"])
        ]
        
        for table_name, table_data in tables_to_update:
            if table_data:
                if self._update_table_data(dataset_id, table_name, table_data, workspace_id):
                    print(f"✅ Updated {table_name}: {len(table_data)} rows")
                else:
                    print(f"❌ Failed to update {table_name}")
                    success = False
            else:
                print(f"⚠️  No data for {table_name}")
        
        # Update date dimension
        if self._update_date_dimension(dataset_id, workspace_id):
            print("✅ Updated DateDimension")
        else:
            print("❌ Failed to update DateDimension")
            success = False
        
        return success
    
    def _update_table_data(self, dataset_id: str, table_name: str, data: List[Dict], workspace_id: Optional[str] = None) -> bool:
        """Update specific table data in Power BI dataset"""
        if workspace_id:
            endpoint = f"groups/{workspace_id}/datasets/{dataset_id}/tables/{table_name}/rows"
        else:
            endpoint = f"datasets/{dataset_id}/tables/{table_name}/rows"
        
        # Clear existing data first
        delete_result = self.powerbi_server._make_api_request(endpoint, method="DELETE")
        
        # Add new data
        payload = {"rows": data}
        result = self.powerbi_server._make_api_request(endpoint, method="POST", data=payload)
        
        return result is not None
    
    def _update_date_dimension(self, dataset_id: str, workspace_id: Optional[str] = None) -> bool:
        """Update date dimension table"""
        # Generate date dimension data
        start_date = datetime.now() - timedelta(days=730)  # 2 years back
        end_date = datetime.now() + timedelta(days=365)    # 1 year forward
        
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        date_data = []
        for date in date_range:
            date_data.append({
                "Date": date.strftime("%Y-%m-%dT%H:%M:%S"),
                "Year": date.year,
                "Quarter": date.quarter,
                "Month": date.month,
                "MonthName": date.strftime('%B'),
                "WeekOfYear": date.isocalendar().week,
                "DayOfYear": date.dayofyear,
                "DayOfMonth": date.day,
                "DayOfWeek": date.dayofweek + 1,
                "DayName": date.strftime('%A'),
                "IsWeekend": date.dayofweek >= 5,
                "FiscalYear": date.year + 1 if date.month >= 4 else date.year
            })
        
        return self._update_table_data(dataset_id, "DateDimension", date_data, workspace_id)
    
    def get_dataset_info(self, dataset_id: Optional[str] = None, workspace_id: Optional[str] = None) -> Optional[Dict]:
        """Get dataset information"""
        dataset_id = dataset_id or self.powerbi_server.config.get("dataset_id")
        workspace_id = workspace_id or self.powerbi_server.config.get("workspace_id")
        
        if not dataset_id:
            print("❌ Dataset ID required")
            return None
        
        if workspace_id:
            endpoint = f"groups/{workspace_id}/datasets/{dataset_id}"
        else:
            endpoint = f"datasets/{dataset_id}"
        
        return self.powerbi_server._make_api_request(endpoint)
    
    def list_dataset_tables(self, dataset_id: Optional[str] = None, workspace_id: Optional[str] = None) -> List[Dict]:
        """List tables in dataset"""
        dataset_id = dataset_id or self.powerbi_server.config.get("dataset_id")
        workspace_id = workspace_id or self.powerbi_server.config.get("workspace_id")
        
        if not dataset_id:
            return []
        
        if workspace_id:
            endpoint = f"groups/{workspace_id}/datasets/{dataset_id}/tables"
        else:
            endpoint = f"datasets/{dataset_id}/tables"
        
        result = self.powerbi_server._make_api_request(endpoint)
        return result.get("value", []) if result else []
    
    def delete_dataset(self, dataset_id: Optional[str] = None, workspace_id: Optional[str] = None) -> bool:
        """Delete dataset"""
        dataset_id = dataset_id or self.powerbi_server.config.get("dataset_id")
        workspace_id = workspace_id or self.powerbi_server.config.get("workspace_id")
        
        if not dataset_id:
            print("❌ Dataset ID required")
            return False
        
        if workspace_id:
            endpoint = f"groups/{workspace_id}/datasets/{dataset_id}"
        else:
            endpoint = f"datasets/{dataset_id}"
        
        result = self.powerbi_server._make_api_request(endpoint, method="DELETE")
        
        if result is not None:
            print(f"✅ Dataset deleted: {dataset_id}")
            return True
        else:
            print(f"❌ Failed to delete dataset: {dataset_id}")
            return False
    
    def setup_scheduled_refresh(self, dataset_id: Optional[str] = None, workspace_id: Optional[str] = None) -> bool:
        """Configure scheduled refresh for dataset"""
        dataset_id = dataset_id or self.powerbi_server.config.get("dataset_id")
        workspace_id = workspace_id or self.powerbi_server.config.get("workspace_id")
        
        if not dataset_id:
            print("❌ Dataset ID required")
            return False
        
        refresh_config = {
            "value": {
                "enabled": True,
                "times": ["06:00", "18:00"],  # 6 AM and 6 PM
                "days": ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
                "timeZone": "UTC",
                "NotifyOption": "MailOnFailure"
            }
        }
        
        if workspace_id:
            endpoint = f"groups/{workspace_id}/datasets/{dataset_id}/refreshSchedule"
        else:
            endpoint = f"datasets/{dataset_id}/refreshSchedule"
        
        result = self.powerbi_server._make_api_request(endpoint, method="PATCH", data=refresh_config)
        
        if result is not None:
            print("✅ Scheduled refresh configured")
            return True
        else:
            print("❌ Failed to configure scheduled refresh")
            return False
    
    def export_dataset_to_files(self, output_dir: Optional[str] = None) -> Dict[str, str]:
        """Export dataset structure and data to files"""
        output_dir = output_dir or self.exports_dir / "dataset_backup"
        os.makedirs(output_dir, exist_ok=True)
        
        exported_files = {}
        
        # Export schema
        schema = self.create_investment_dataset_schema()
        schema_file = os.path.join(output_dir, "dataset_schema.json")
        with open(schema_file, 'w') as f:
            json.dump(schema, f, indent=2)
        exported_files["schema"] = schema_file
        
        # Export data
        data = self.powerbi_server.get_investment_data_for_powerbi()
        if "error" not in data:
            data_file = os.path.join(output_dir, "dataset_data.json")
            with open(data_file, 'w') as f:
                json.dump(data, f, indent=2)
            exported_files["data"] = data_file
            
            # Export as CSV files
            csv_files = self.powerbi_server.export_to_powerbi_format(os.path.join(output_dir, "csv"))
            exported_files.update(csv_files)
        
        # Export configuration
        config_file = os.path.join(output_dir, "powerbi_config.json") 
        with open(config_file, 'w') as f:
            # Don't export sensitive data
            safe_config = {k: v for k, v in self.powerbi_server.config.items() 
                          if k not in ['client_secret']}
            json.dump(safe_config, f, indent=2)
        exported_files["config"] = config_file
        
        print(f"✅ Dataset exported to: {output_dir}")
        return exported_files

def main():
    """Main CLI interface"""
    if len(sys.argv) < 2:
        print("Power BI Dataset Manager")
        print("Usage: python dataset_manager.py [command] [options]")
        print("Commands:")
        print("  create              - Create new dataset")
        print("  update              - Update dataset with fresh data") 
        print("  info                - Get dataset information")
        print("  tables              - List dataset tables")
        print("  delete              - Delete dataset")
        print("  schedule            - Setup scheduled refresh")
        print("  export [output_dir] - Export dataset to files")
        return
    
    command = sys.argv[1]
    manager = PowerBIDatasetManager()
    
    if command == "create":
        workspace_id = sys.argv[2] if len(sys.argv) > 2 else None
        dataset_id = manager.create_dataset(workspace_id)
        if dataset_id:
            print(f"Dataset ID: {dataset_id}")
    
    elif command == "update":
        dataset_id = sys.argv[2] if len(sys.argv) > 2 else None
        workspace_id = sys.argv[3] if len(sys.argv) > 3 else None
        success = manager.update_dataset_data(dataset_id, workspace_id)
        print(f"Update {'successful' if success else 'failed'}")
    
    elif command == "info":
        dataset_id = sys.argv[2] if len(sys.argv) > 2 else None
        workspace_id = sys.argv[3] if len(sys.argv) > 3 else None
        info = manager.get_dataset_info(dataset_id, workspace_id)
        if info:
            print(json.dumps(info, indent=2))
    
    elif command == "tables":
        dataset_id = sys.argv[2] if len(sys.argv) > 2 else None
        workspace_id = sys.argv[3] if len(sys.argv) > 3 else None
        tables = manager.list_dataset_tables(dataset_id, workspace_id)
        print(json.dumps(tables, indent=2))
    
    elif command == "delete":
        dataset_id = sys.argv[2] if len(sys.argv) > 2 else None
        workspace_id = sys.argv[3] if len(sys.argv) > 3 else None
        success = manager.delete_dataset(dataset_id, workspace_id)
        print(f"Delete {'successful' if success else 'failed'}")
    
    elif command == "schedule":
        dataset_id = sys.argv[2] if len(sys.argv) > 2 else None
        workspace_id = sys.argv[3] if len(sys.argv) > 3 else None
        success = manager.setup_scheduled_refresh(dataset_id, workspace_id)
        print(f"Schedule setup {'successful' if success else 'failed'}")
    
    elif command == "export":
        output_dir = sys.argv[2] if len(sys.argv) > 2 else None
        files = manager.export_dataset_to_files(output_dir)
        print("Exported files:")
        for name, path in files.items():
            print(f"  {name}: {path}")
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()