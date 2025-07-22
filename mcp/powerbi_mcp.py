#!/usr/bin/env python3
"""
Power BI MCP Server
Provides structured access to Power BI services and investment data integration
"""

import os
import json
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import requests
from typing import Dict, List, Optional, Any
import msal
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PowerBIMCPServer:
    """MCP Server for Power BI integration with investment system"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or Path(__file__).parent.parent / "config" / "powerbi_config.json"
        self.db_path = Path(__file__).parent.parent / "investment_system.db"
        self.cache_dir = Path(__file__).parent.parent / "cache"
        self.config = self._load_config()
        self.app = None
        self.token = None
        
    def _load_config(self) -> Dict[str, Any]:
        """Load Power BI configuration"""
        default_config = {
            "client_id": "",
            "client_secret": "",
            "tenant_id": "",
            "scope": ["https://analysis.windows.net/powerbi/api/.default"],
            "authority": "https://login.microsoftonline.com/",
            "workspace_id": "",
            "dataset_id": "",
            "api_base": "https://api.powerbi.com/v1.0/myorg",
            "cache_timeout": 300,
            "auto_refresh": True
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    default_config.update(config)
            except Exception as e:
                logger.warning(f"Could not load config: {e}")
        
        return default_config
    
    def _get_access_token(self) -> Optional[str]:
        """Get Microsoft Graph access token for Power BI API"""
        if not all([self.config["client_id"], self.config["client_secret"], self.config["tenant_id"]]):
            logger.error("Missing required authentication configuration")
            return None
        
        if not self.app:
            self.app = msal.ConfidentialClientApplication(
                self.config["client_id"],
                authority=f"{self.config['authority']}{self.config['tenant_id']}",
                client_credential=self.config["client_secret"]
            )
        
        # Try to get token from cache
        result = self.app.acquire_token_silent(self.config["scope"], account=None)
        
        if not result:
            # Get new token
            result = self.app.acquire_token_for_client(scopes=self.config["scope"])
        
        if "access_token" in result:
            self.token = result["access_token"]
            return self.token
        else:
            logger.error(f"Failed to acquire token: {result.get('error_description', 'Unknown error')}")
            return None
    
    def _make_api_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Optional[Dict]:
        """Make authenticated API request to Power BI"""
        token = self._get_access_token()
        if not token:
            return None
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.config['api_base']}/{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json() if response.text else {}
        
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
    
    def get_workspaces(self) -> List[Dict[str, Any]]:
        """Get all Power BI workspaces"""
        result = self._make_api_request("groups")
        return result.get("value", []) if result else []
    
    def get_datasets(self, workspace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get datasets from workspace"""
        workspace_id = workspace_id or self.config["workspace_id"]
        if not workspace_id:
            endpoint = "datasets"
        else:
            endpoint = f"groups/{workspace_id}/datasets"
        
        result = self._make_api_request(endpoint)
        return result.get("value", []) if result else []
    
    def get_reports(self, workspace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get reports from workspace"""
        workspace_id = workspace_id or self.config["workspace_id"]
        if not workspace_id:
            endpoint = "reports"
        else:
            endpoint = f"groups/{workspace_id}/reports"
        
        result = self._make_api_request(endpoint)
        return result.get("value", []) if result else []
    
    def refresh_dataset(self, dataset_id: Optional[str] = None, workspace_id: Optional[str] = None) -> bool:
        """Trigger dataset refresh"""
        dataset_id = dataset_id or self.config["dataset_id"]
        workspace_id = workspace_id or self.config["workspace_id"]
        
        if not dataset_id:
            logger.error("Dataset ID is required")
            return False
        
        if workspace_id:
            endpoint = f"groups/{workspace_id}/datasets/{dataset_id}/refreshes"
        else:
            endpoint = f"datasets/{dataset_id}/refreshes"
        
        data = {"notifyOption": "MailOnCompletion"}
        result = self._make_api_request(endpoint, method="POST", data=data)
        return result is not None
    
    def get_refresh_history(self, dataset_id: Optional[str] = None, workspace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get dataset refresh history"""
        dataset_id = dataset_id or self.config["dataset_id"]
        workspace_id = workspace_id or self.config["workspace_id"]
        
        if not dataset_id:
            return []
        
        if workspace_id:
            endpoint = f"groups/{workspace_id}/datasets/{dataset_id}/refreshes"
        else:
            endpoint = f"datasets/{dataset_id}/refreshes"
        
        result = self._make_api_request(endpoint)
        return result.get("value", []) if result else []
    
    def get_investment_data_for_powerbi(self) -> Dict[str, Any]:
        """Get investment system data formatted for Power BI"""
        if not os.path.exists(self.db_path):
            return {"error": "Investment database not found"}
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        try:
            # Portfolio summary
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_securities,
                    SUM(CASE WHEN security_type = 'stock' THEN 1 ELSE 0 END) as stocks,
                    SUM(CASE WHEN security_type = 'etf' THEN 1 ELSE 0 END) as etfs,
                    COUNT(DISTINCT sector) as sectors
                FROM securities
            """)
            portfolio_summary = dict(cursor.fetchone())
            
            # AI/Robotics stocks with analysis data
            cursor.execute("""
                SELECT 
                    s.symbol,
                    s.name,
                    s.sector,
                    s.market_cap_category,
                    s.price_52w_high,
                    s.price_52w_low,
                    s.current_price,
                    CASE 
                        WHEN s.current_price > 0 AND s.price_52w_low > 0 
                        THEN ROUND((s.current_price - s.price_52w_low) / s.price_52w_low * 100, 2)
                        ELSE 0 
                    END as ytd_performance_pct,
                    c.category_name as investment_category
                FROM securities s
                JOIN security_categories sc ON s.id = sc.security_id
                JOIN categories c ON sc.category_id = c.id
                WHERE c.category_name IN ('ai_software', 'ai_hardware', 'robotics')
                AND s.security_type = 'stock'
                ORDER BY s.symbol
            """)
            stocks_data = [dict(row) for row in cursor.fetchall()]
            
            # Ethics screening results
            cursor.execute("""
                SELECT 
                    symbol,
                    name,
                    reason,
                    alternative_symbol,
                    created_at
                FROM ethics_blacklist
                ORDER BY created_at DESC
            """)
            ethics_data = [dict(row) for row in cursor.fetchall()]
            
            # Smart money institutions
            cursor.execute("""
                SELECT 
                    name,
                    focus_area,
                    priority,
                    metadata_json
                FROM institutions
                ORDER BY 
                    CASE priority 
                        WHEN 'high' THEN 1 
                        WHEN 'medium' THEN 2 
                        WHEN 'low' THEN 3 
                    END
            """)
            institutions_data = [dict(row) for row in cursor.fetchall()]
            
            # Analysis settings
            cursor.execute("""
                SELECT setting_type, name, value 
                FROM analysis_settings 
                ORDER BY setting_type, name
            """)
            settings_data = [dict(row) for row in cursor.fetchall()]
            
            return {
                "timestamp": datetime.now().isoformat(),
                "portfolio_summary": portfolio_summary,
                "ai_robotics_stocks": stocks_data,
                "ethics_screening": ethics_data,
                "smart_money_institutions": institutions_data,
                "analysis_settings": settings_data,
                "data_freshness": "real_time"
            }
            
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            return {"error": str(e)}
        finally:
            conn.close()
    
    def export_to_powerbi_format(self, output_dir: Optional[str] = None) -> Dict[str, str]:
        """Export investment data in Power BI compatible format"""
        output_dir = output_dir or (Path(__file__).parent.parent / "powerbi_project" / "exports" / "powerbi_import")
        os.makedirs(output_dir, exist_ok=True)
        
        data = self.get_investment_data_for_powerbi()
        if "error" in data:
            return {"error": data["error"]}
        
        exported_files = {}
        
        try:
            # Export portfolio summary
            portfolio_df = pd.DataFrame([data["portfolio_summary"]])
            portfolio_file = os.path.join(output_dir, "portfolio_summary.csv")
            portfolio_df.to_csv(portfolio_file, index=False)
            exported_files["portfolio_summary"] = portfolio_file
            
            # Export AI/Robotics stocks
            if data["ai_robotics_stocks"]:
                stocks_df = pd.DataFrame(data["ai_robotics_stocks"])
                stocks_file = os.path.join(output_dir, "ai_robotics_stocks.csv")
                stocks_df.to_csv(stocks_file, index=False)
                exported_files["ai_robotics_stocks"] = stocks_file
            
            # Export ethics data
            if data["ethics_screening"]:
                ethics_df = pd.DataFrame(data["ethics_screening"])
                ethics_file = os.path.join(output_dir, "ethics_screening.csv")
                ethics_df.to_csv(ethics_file, index=False)
                exported_files["ethics_screening"] = ethics_file
            
            # Export institutions data
            if data["smart_money_institutions"]:
                institutions_df = pd.DataFrame(data["smart_money_institutions"])
                institutions_file = os.path.join(output_dir, "smart_money_institutions.csv")
                institutions_df.to_csv(institutions_file, index=False)
                exported_files["smart_money_institutions"] = institutions_file
            
            # Export settings data
            if data["analysis_settings"]:
                settings_df = pd.DataFrame(data["analysis_settings"])
                settings_file = os.path.join(output_dir, "analysis_settings.csv")
                settings_df.to_csv(settings_file, index=False)
                exported_files["analysis_settings"] = settings_file
            
            # Create metadata file
            metadata = {
                "export_timestamp": data["timestamp"],
                "exported_files": list(exported_files.keys()),
                "data_source": "investment_system_database",
                "format": "csv_for_powerbi"
            }
            metadata_file = os.path.join(output_dir, "export_metadata.json")
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            exported_files["metadata"] = metadata_file
            
            return exported_files
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return {"error": str(e)}
    
    def create_powerbi_measures(self) -> Dict[str, str]:
        """Generate DAX measures for investment analysis"""
        measures = {
            # Portfolio Metrics
            "Total Securities": "COUNTROWS(ai_robotics_stocks)",
            "AI Software Stocks": "CALCULATE(COUNTROWS(ai_robotics_stocks), ai_robotics_stocks[investment_category] = \"ai_software\")",
            "AI Hardware Stocks": "CALCULATE(COUNTROWS(ai_robotics_stocks), ai_robotics_stocks[investment_category] = \"ai_hardware\")",
            "Robotics Stocks": "CALCULATE(COUNTROWS(ai_robotics_stocks), ai_robotics_stocks[investment_category] = \"robotics\")",
            
            # Performance Metrics
            "Average YTD Performance": "AVERAGE(ai_robotics_stocks[ytd_performance_pct])",
            "Best Performer": "MAXX(ai_robotics_stocks, ai_robotics_stocks[ytd_performance_pct])",
            "Worst Performer": "MINX(ai_robotics_stocks, ai_robotics_stocks[ytd_performance_pct])",
            "Stocks Above 52W Low": "CALCULATE(COUNTROWS(ai_robotics_stocks), ai_robotics_stocks[ytd_performance_pct] > 0)",
            
            # Price Analysis
            "Average Current Price": "AVERAGE(ai_robotics_stocks[current_price])",
            "Total Market Value": "SUMX(ai_robotics_stocks, ai_robotics_stocks[current_price])",
            "Price Range Spread": "AVERAGE(ai_robotics_stocks[price_52w_high]) - AVERAGE(ai_robotics_stocks[price_52w_low])",
            
            # Ethics Metrics
            "Ethics Violations": "COUNTROWS(ethics_screening)",
            "Recent Ethics Issues": "CALCULATE(COUNTROWS(ethics_screening), ethics_screening[created_at] >= TODAY() - 30)",
            
            # Smart Money Metrics
            "High Priority Institutions": "CALCULATE(COUNTROWS(smart_money_institutions), smart_money_institutions[priority] = \"high\")",
            "AI Focused Institutions": "CALCULATE(COUNTROWS(smart_money_institutions), SEARCH(\"ai\", smart_money_institutions[focus_area], 1, 0) > 0)",
            
            # Sector Analysis
            "Technology Sector %": "DIVIDE(CALCULATE(COUNTROWS(ai_robotics_stocks), ai_robotics_stocks[sector] = \"Technology\"), COUNTROWS(ai_robotics_stocks), 0) * 100",
            "Healthcare Sector %": "DIVIDE(CALCULATE(COUNTROWS(ai_robotics_stocks), ai_robotics_stocks[sector] = \"Healthcare\"), COUNTROWS(ai_robotics_stocks), 0) * 100",
            
            # Market Cap Analysis
            "Large Cap Stocks": "CALCULATE(COUNTROWS(ai_robotics_stocks), ai_robotics_stocks[market_cap_category] = \"large\")",
            "Mid Cap Stocks": "CALCULATE(COUNTROWS(ai_robotics_stocks), ai_robotics_stocks[market_cap_category] = \"mid\")",
            "Small Cap Stocks": "CALCULATE(COUNTROWS(ai_robotics_stocks), ai_robotics_stocks[market_cap_category] = \"small\")"
        }
        
        return measures
    
    def get_powerbi_setup_instructions(self) -> str:
        """Generate setup instructions for Power BI integration"""
        return """# Power BI Investment System Integration Setup

## Prerequisites
1. Power BI Desktop installed
2. Power BI Pro or Premium license (for API access)
3. Azure AD app registration for authentication

## Authentication Setup

### 1. Azure AD App Registration
1. Go to Azure Portal → Azure Active Directory → App registrations
2. Click "New registration"
3. Name: "Investment System Power BI Integration"
4. Supported account types: "Accounts in this organizational directory only"
5. Redirect URI: Not required for service principal
6. Click "Register"

### 2. Configure App Permissions
1. Go to "API permissions"
2. Click "Add a permission"
3. Select "Power BI Service"
4. Choose "Application permissions"
5. Add: Dataset.ReadWrite.All, Report.ReadWrite.All, Workspace.ReadWrite.All
6. Click "Grant admin consent"

### 3. Create Client Secret
1. Go to "Certificates & secrets"
2. Click "New client secret"
3. Description: "Power BI MCP Integration"
4. Expiry: 24 months
5. Click "Add"
6. Copy the secret value (you won't see it again)

### 4. Configure MCP Server
Create config file at: config/powerbi_config.json
```json
{
  "client_id": "your_app_id_here",
  "client_secret": "your_client_secret_here", 
  "tenant_id": "your_tenant_id_here",
  "workspace_id": "your_powerbi_workspace_id",
  "dataset_id": "your_dataset_id"
}
```

## Data Import Process

### 1. Export Investment Data
Run: `python mcp/powerbi_mcp.py export`
This creates CSV files in: powerbi_project/exports/powerbi_import/

### 2. Import to Power BI Desktop
1. Open Power BI Desktop
2. Get Data → Text/CSV
3. Import these files:
   - portfolio_summary.csv
   - ai_robotics_stocks.csv  
   - ethics_screening.csv
   - smart_money_institutions.csv
   - analysis_settings.csv

### 3. Create Data Model
1. Go to Model view
2. Create relationships:
   - None needed (independent tables for now)

### 4. Add DAX Measures
Copy measures from the generated DAX file:
```
Total Securities = COUNTROWS(ai_robotics_stocks)
Average YTD Performance = AVERAGE(ai_robotics_stocks[ytd_performance_pct])
```

## Report Templates

### Executive Dashboard
- KPI cards: Total Securities, Average Performance, Ethics Issues
- Charts: Performance by Category, Sector Distribution
- Tables: Top/Bottom Performers

### Detailed Analysis  
- Matrix: Stocks by Sector and Category
- Scatter: Price vs Performance
- Waterfall: Performance Distribution

### Ethics & Compliance
- Table: Ethics Violations
- Timeline: Issues Over Time
- Alternatives: Recommended Replacements

## Automation

### Scheduled Refresh
1. Publish report to Power BI Service
2. Go to Dataset settings
3. Configure scheduled refresh
4. Set frequency (daily recommended)

### API Integration
Use the MCP server for:
- Real-time data refresh
- Automated report generation
- Custom analysis triggers

## Troubleshooting

### Authentication Issues
- Verify app permissions are granted
- Check client secret hasn't expired
- Ensure service principal has workspace access

### Data Import Issues  
- Verify CSV file formats
- Check data types match expectations
- Ensure all required columns exist

### Performance Issues
- Limit date ranges for large datasets
- Use incremental refresh for historical data
- Optimize DAX measures
"""

# CLI Interface for testing
if __name__ == "__main__":
    import sys
    
    server = PowerBIMCPServer()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "workspaces":
            print(json.dumps(server.get_workspaces(), indent=2))
        elif command == "datasets":
            workspace_id = sys.argv[2] if len(sys.argv) > 2 else None
            print(json.dumps(server.get_datasets(workspace_id), indent=2))
        elif command == "reports":
            workspace_id = sys.argv[2] if len(sys.argv) > 2 else None
            print(json.dumps(server.get_reports(workspace_id), indent=2))
        elif command == "refresh":
            dataset_id = sys.argv[2] if len(sys.argv) > 2 else None
            workspace_id = sys.argv[3] if len(sys.argv) > 3 else None
            result = server.refresh_dataset(dataset_id, workspace_id)
            print(json.dumps({"refresh_triggered": result}, indent=2))
        elif command == "history":
            dataset_id = sys.argv[2] if len(sys.argv) > 2 else None
            workspace_id = sys.argv[3] if len(sys.argv) > 3 else None
            print(json.dumps(server.get_refresh_history(dataset_id, workspace_id), indent=2))
        elif command == "data":
            print(json.dumps(server.get_investment_data_for_powerbi(), indent=2))
        elif command == "export":
            output_dir = sys.argv[2] if len(sys.argv) > 2 else None
            result = server.export_to_powerbi_format(output_dir)
            print(json.dumps(result, indent=2))
        elif command == "measures":
            print(json.dumps(server.create_powerbi_measures(), indent=2))
        elif command == "setup":
            print(server.get_powerbi_setup_instructions())
        else:
            print(json.dumps({"error": f"Unknown command: {command}"}))
    else:
        print(json.dumps({
            "available_commands": [
                "workspaces", "datasets", "reports", "refresh", "history",
                "data", "export", "measures", "setup"
            ]
        }, indent=2))