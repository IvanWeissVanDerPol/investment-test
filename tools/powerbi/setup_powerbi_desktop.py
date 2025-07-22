#!/usr/bin/env python3
"""
Power BI Desktop Integration Setup
Configures Power BI Desktop for investment system integration
"""

import json
import os
import sys
from pathlib import Path
import shutil
import subprocess
from typing import Dict, List, Optional, Any

class PowerBIDesktopSetup:
    """Handles Power BI Desktop configuration and setup"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.exports_dir = self.project_root / "powerbi_project" / "exports"
        self.templates_dir = self.project_root / "powerbi_project" / "templates"
        self.config_dir = self.project_root / "config"
        
    def create_powerbi_template(self) -> str:
        """Create Power BI template file (.pbit) configuration"""
        
        template_config = {
            "version": "1.0",
            "dataModel": {
                "name": "Investment System Analysis",
                "description": "Comprehensive investment portfolio analysis for AI/Robotics focus",
                "tables": [
                    {
                        "name": "AIRoboticsStocks",
                        "description": "AI and Robotics focused stock data",
                        "columns": [
                            {"name": "symbol", "dataType": "text", "description": "Stock symbol"},
                            {"name": "name", "dataType": "text", "description": "Company name"},
                            {"name": "sector", "dataType": "text", "description": "Business sector"},
                            {"name": "market_cap_category", "dataType": "text", "description": "Market cap size"},
                            {"name": "current_price", "dataType": "decimal", "description": "Current stock price"},
                            {"name": "ytd_performance_pct", "dataType": "decimal", "description": "Year-to-date performance %"},
                            {"name": "investment_category", "dataType": "text", "description": "AI/Robotics category"}
                        ]
                    },
                    {
                        "name": "EthicsScreening",
                        "description": "Ethics screening results",
                        "columns": [
                            {"name": "symbol", "dataType": "text", "description": "Stock symbol"},
                            {"name": "name", "dataType": "text", "description": "Company name"},
                            {"name": "reason", "dataType": "text", "description": "Reason for screening"},
                            {"name": "alternative_symbol", "dataType": "text", "description": "Suggested alternative"}
                        ]
                    },
                    {
                        "name": "SmartMoneyInstitutions",
                        "description": "Smart money institution tracking",
                        "columns": [
                            {"name": "name", "dataType": "text", "description": "Institution name"},
                            {"name": "focus_area", "dataType": "text", "description": "Investment focus"},
                            {"name": "priority", "dataType": "text", "description": "Tracking priority"}
                        ]
                    }
                ]
            },
            "reports": [
                {
                    "name": "Executive Dashboard",
                    "pages": [
                        {
                            "name": "Overview",
                            "visuals": [
                                {"type": "card", "title": "Total Securities", "measure": "COUNT(AIRoboticsStocks[symbol])"},
                                {"type": "donut", "title": "Category Distribution", "axis": "investment_category"},
                                {"type": "column", "title": "Performance by Sector", "axis": "sector", "value": "ytd_performance_pct"}
                            ]
                        }
                    ]
                }
            ],
            "measures": {
                "Total Securities": "COUNTROWS(AIRoboticsStocks)",
                "Average Performance": "AVERAGE(AIRoboticsStocks[ytd_performance_pct])",
                "AI Software Count": "CALCULATE(COUNTROWS(AIRoboticsStocks), AIRoboticsStocks[investment_category] = \"ai_software\")",
                "AI Hardware Count": "CALCULATE(COUNTROWS(AIRoboticsStocks), AIRoboticsStocks[investment_category] = \"ai_hardware\")",
                "Robotics Count": "CALCULATE(COUNTROWS(AIRoboticsStocks), AIRoboticsStocks[investment_category] = \"robotics\")",
                "Ethics Issues": "COUNTROWS(EthicsScreening)",
                "High Priority Institutions": "CALCULATE(COUNTROWS(SmartMoneyInstitutions), SmartMoneyInstitutions[priority] = \"high\")"
            }
        }
        
        # Save template configuration
        os.makedirs(self.templates_dir, exist_ok=True)
        template_path = self.templates_dir / "investment_analysis_template.json"
        
        with open(template_path, 'w') as f:
            json.dump(template_config, f, indent=2)
        
        print(f"✅ Power BI template configuration created: {template_path}")
        return str(template_path)
    
    def generate_data_connection_script(self) -> str:
        """Generate M script for data connections"""
        
        m_script = '''
// Investment System Data Connection Script
// This M script connects to the exported CSV files from the investment system

let
    // Define file paths (update these paths to match your export location)
    ExportPath = "C:\\Users\\jandr\\Documents\\ivan\\powerbi_project\\exports\\powerbi_import\\",
    
    // Load AI/Robotics Stocks data
    AIRoboticsStocks_Source = Csv.Document(File.Contents(ExportPath & "ai_robotics_stocks.csv"), [Delimiter=",", Columns=9, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    AIRoboticsStocks_Headers = Table.PromoteHeaders(AIRoboticsStocks_Source, [PromoteAllScalars=true]),
    AIRoboticsStocks_Types = Table.TransformColumnTypes(AIRoboticsStocks_Headers,{
        {"symbol", type text}, 
        {"name", type text}, 
        {"sector", type text}, 
        {"market_cap_category", type text}, 
        {"price_52w_high", type number}, 
        {"price_52w_low", type number}, 
        {"current_price", type number}, 
        {"ytd_performance_pct", type number}, 
        {"investment_category", type text}
    }),
    
    // Load Ethics Screening data
    EthicsScreening_Source = Csv.Document(File.Contents(ExportPath & "ethics_screening.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.None]),
    EthicsScreening_Headers = Table.PromoteHeaders(EthicsScreening_Source, [PromoteAllScalars=true]),
    EthicsScreening_Types = Table.TransformColumnTypes(EthicsScreening_Headers,{
        {"symbol", type text}, 
        {"name", type text}, 
        {"reason", type text}, 
        {"alternative_symbol", type text}, 
        {"created_at", type datetime}
    }),
    
    // Load Smart Money Institutions data
    SmartMoney_Source = Csv.Document(File.Contents(ExportPath & "smart_money_institutions.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.None]),
    SmartMoney_Headers = Table.PromoteHeaders(SmartMoney_Source, [PromoteAllScalars=true]),
    SmartMoney_Types = Table.TransformColumnTypes(SmartMoney_Headers,{
        {"name", type text}, 
        {"focus_area", type text}, 
        {"priority", type text}, 
        {"metadata_json", type text}
    }),
    
    // Load Portfolio Summary data
    Portfolio_Source = Csv.Document(File.Contents(ExportPath & "portfolio_summary.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.None]),
    Portfolio_Headers = Table.PromoteHeaders(Portfolio_Source, [PromoteAllScalars=true]),
    Portfolio_Types = Table.TransformColumnTypes(Portfolio_Headers,{
        {"total_securities", Int64.Type}, 
        {"stocks", Int64.Type}, 
        {"etfs", Int64.Type}, 
        {"sectors", Int64.Type}
    }),
    
    // Create a single table with all data references
    DataSources = Table.FromRecords({
        [Table="AIRoboticsStocks", Data=AIRoboticsStocks_Types],
        [Table="EthicsScreening", Data=EthicsScreening_Types],
        [Table="SmartMoneyInstitutions", Data=SmartMoney_Types],
        [Table="PortfolioSummary", Data=Portfolio_Types]
    })

in
    DataSources
'''
        
        script_path = self.templates_dir / "investment_data_connection.m"
        with open(script_path, 'w') as f:
            f.write(m_script)
        
        print(f"✅ M script for data connections created: {script_path}")
        return str(script_path)
    
    def create_dax_measures_file(self) -> str:
        """Create comprehensive DAX measures file"""
        
        dax_measures = {
            "Portfolio Metrics": {
                "Total Securities": "COUNTROWS(AIRoboticsStocks)",
                "AI Software Stocks": "CALCULATE(COUNTROWS(AIRoboticsStocks), AIRoboticsStocks[investment_category] = \"ai_software\")",
                "AI Hardware Stocks": "CALCULATE(COUNTROWS(AIRoboticsStocks), AIRoboticsStocks[investment_category] = \"ai_hardware\")",
                "Robotics Stocks": "CALCULATE(COUNTROWS(AIRoboticsStocks), AIRoboticsStocks[investment_category] = \"robotics\")",
                "Total Sectors": "DISTINCTCOUNT(AIRoboticsStocks[sector])"
            },
            "Performance Metrics": {
                "Average YTD Performance": "AVERAGE(AIRoboticsStocks[ytd_performance_pct])",
                "Best Performer": "MAXX(AIRoboticsStocks, AIRoboticsStocks[ytd_performance_pct])",
                "Worst Performer": "MINX(AIRoboticsStocks, AIRoboticsStocks[ytd_performance_pct])",
                "Positive Performance Count": "CALCULATE(COUNTROWS(AIRoboticsStocks), AIRoboticsStocks[ytd_performance_pct] > 0)",
                "Performance Range": "MAXX(AIRoboticsStocks, AIRoboticsStocks[ytd_performance_pct]) - MINX(AIRoboticsStocks, AIRoboticsStocks[ytd_performance_pct])"
            },
            "Price Analysis": {
                "Average Current Price": "AVERAGE(AIRoboticsStocks[current_price])",
                "Price Weighted Performance": "SUMX(AIRoboticsStocks, AIRoboticsStocks[current_price] * AIRoboticsStocks[ytd_performance_pct]) / SUM(AIRoboticsStocks[current_price])",
                "High Price Stocks": "CALCULATE(COUNTROWS(AIRoboticsStocks), AIRoboticsStocks[current_price] > 100)",
                "Total Market Value": "SUMX(AIRoboticsStocks, AIRoboticsStocks[current_price])"
            },
            "Ethics & Compliance": {
                "Ethics Violations": "COUNTROWS(EthicsScreening)",
                "Recent Ethics Issues": "CALCULATE(COUNTROWS(EthicsScreening), EthicsScreening[created_at] >= TODAY() - 30)",
                "Ethics Violation Rate": "DIVIDE([Ethics Violations], [Total Securities], 0)",
                "Clean Stocks": "[Total Securities] - [Ethics Violations]"
            },
            "Smart Money Analysis": {
                "Total Institutions": "COUNTROWS(SmartMoneyInstitutions)",
                "High Priority Institutions": "CALCULATE(COUNTROWS(SmartMoneyInstitutions), SmartMoneyInstitutions[priority] = \"high\")",
                "AI Focused Institutions": "CALCULATE(COUNTROWS(SmartMoneyInstitutions), SEARCH(\"AI\", UPPER(SmartMoneyInstitutions[focus_area]), 1, 0) > 0)",
                "Priority Score": "SUMX(SmartMoneyInstitutions, SWITCH(SmartMoneyInstitutions[priority], \"high\", 3, \"medium\", 2, \"low\", 1, 0))"
            },
            "Sector Analysis": {
                "Technology Sector %": "DIVIDE(CALCULATE(COUNTROWS(AIRoboticsStocks), AIRoboticsStocks[sector] = \"Technology\"), [Total Securities], 0) * 100",
                "Healthcare Sector %": "DIVIDE(CALCULATE(COUNTROWS(AIRoboticsStocks), AIRoboticsStocks[sector] = \"Healthcare\"), [Total Securities], 0) * 100",
                "Top Performing Sector": "TOPN(1, SUMMARIZE(AIRoboticsStocks, AIRoboticsStocks[sector], \"Avg Performance\", AVERAGE(AIRoboticsStocks[ytd_performance_pct])), [Avg Performance], DESC)",
                "Sector Diversity": "DISTINCTCOUNT(AIRoboticsStocks[sector])"
            },
            "Market Cap Analysis": {
                "Large Cap Count": "CALCULATE(COUNTROWS(AIRoboticsStocks), AIRoboticsStocks[market_cap_category] = \"large\")",
                "Mid Cap Count": "CALCULATE(COUNTROWS(AIRoboticsStocks), AIRoboticsStocks[market_cap_category] = \"mid\")",
                "Small Cap Count": "CALCULATE(COUNTROWS(AIRoboticsStocks), AIRoboticsStocks[market_cap_category] = \"small\")",
                "Large Cap %": "DIVIDE([Large Cap Count], [Total Securities], 0) * 100"
            },
            "Conditional Formatting": {
                "Performance Color": "SWITCH(TRUE(), [Average YTD Performance] > 10, \"Green\", [Average YTD Performance] > 0, \"Yellow\", \"Red\")",
                "Risk Level": "SWITCH(TRUE(), [Performance Range] > 50, \"High\", [Performance Range] > 20, \"Medium\", \"Low\")",
                "Portfolio Health": "SWITCH(TRUE(), [Ethics Violation Rate] < 0.05 && [Average YTD Performance] > 5, \"Excellent\", [Ethics Violation Rate] < 0.1 && [Average YTD Performance] > 0, \"Good\", \"Needs Attention\")"
            }
        }
        
        # Create DAX file with proper formatting
        dax_content = "// Investment System DAX Measures\n"
        dax_content += "// Copy these measures into Power BI Desktop\n\n"
        
        for category, measures in dax_measures.items():
            dax_content += f"// === {category} ===\n\n"
            for measure_name, formula in measures.items():
                dax_content += f"{measure_name} = {formula}\n\n"
        
        dax_path = self.templates_dir / "investment_dax_measures.dax"
        with open(dax_path, 'w') as f:
            f.write(dax_content)
        
        # Also save as JSON for programmatic access
        json_path = self.templates_dir / "investment_dax_measures.json"
        with open(json_path, 'w') as f:
            json.dump(dax_measures, f, indent=2)
        
        print(f"✅ DAX measures created: {dax_path}")
        print(f"✅ DAX measures JSON: {json_path}")
        return str(dax_path)
    
    def create_setup_instructions(self) -> str:
        """Create comprehensive setup instructions"""
        
        instructions = """# Power BI Desktop Setup Instructions
## Investment System Integration

### Prerequisites
1. **Power BI Desktop** - Download from Microsoft Store or PowerBI.com
2. **Investment System Data** - Ensure CSV exports are available
3. **File Access** - Power BI Desktop needs read access to export directory

---

## Step 1: Data Connection Setup

### Option A: Manual CSV Import
1. Open Power BI Desktop
2. Click **Get Data** → **Text/CSV**
3. Navigate to: `powerbi_project/exports/powerbi_import/`
4. Import these files in order:
   - `portfolio_summary.csv`
   - `ai_robotics_stocks.csv`
   - `ethics_screening.csv`
   - `smart_money_institutions.csv`
   - `analysis_settings.csv`

### Option B: Use M Script (Recommended)
1. Open Power BI Desktop
2. Click **Get Data** → **Blank Query**
3. Open **Advanced Editor**
4. Copy and paste the M script from `templates/investment_data_connection.m`
5. Update the `ExportPath` variable to your actual export directory
6. Click **Done**

---

## Step 2: Data Model Configuration

### Column Data Types
Ensure these data types are set correctly:

**AIRoboticsStocks Table:**
- `symbol`: Text
- `name`: Text  
- `sector`: Text
- `market_cap_category`: Text
- `price_52w_high`: Decimal Number
- `price_52w_low`: Decimal Number
- `current_price`: Decimal Number
- `ytd_performance_pct`: Decimal Number
- `investment_category`: Text

**EthicsScreening Table:**
- `symbol`: Text
- `name`: Text
- `reason`: Text
- `alternative_symbol`: Text
- `created_at`: Date/Time

### Relationships
Create these relationships in Model view:
- `EthicsScreening[symbol]` → `AIRoboticsStocks[symbol]` (Many-to-One)

---

## Step 3: Add DAX Measures

1. In the **Fields** pane, right-click on `AIRoboticsStocks` table
2. Select **New Measure**
3. Copy measures from `templates/investment_dax_measures.dax`
4. Add each measure individually

### Key Measures to Add First:
```dax
Total Securities = COUNTROWS(AIRoboticsStocks)
Average YTD Performance = AVERAGE(AIRoboticsStocks[ytd_performance_pct])
AI Software Stocks = CALCULATE(COUNTROWS(AIRoboticsStocks), AIRoboticsStocks[investment_category] = "ai_software")
Ethics Violations = COUNTROWS(EthicsScreening)
```

---

## Step 4: Create Report Pages

### Page 1: Executive Dashboard
**Visuals to add:**
1. **Card**: Total Securities
2. **Card**: Average YTD Performance  
3. **Donut Chart**: Investment Category Distribution
4. **Column Chart**: Performance by Sector
5. **Table**: Top 10 Performers

### Page 2: Detailed Analysis
**Visuals to add:**
1. **Matrix**: Sector vs Investment Category
2. **Scatter Chart**: Price vs Performance
3. **Table**: Full Stock List with filters

### Page 3: Ethics & Compliance
**Visuals to add:**
1. **Card**: Ethics Violations
2. **Table**: Blocked Stocks
3. **Timeline**: Ethics Issues Over Time

### Page 4: Smart Money Tracking
**Visuals to add:**
1. **Card**: High Priority Institutions
2. **Pie Chart**: Priority Distribution
3. **Table**: Institution Details

---

## Step 5: Setup Data Refresh

### For Manual Refresh:
1. Click **Refresh** in the Home ribbon
2. Data will update from CSV files

### For Scheduled Refresh (Power BI Service):
1. Publish report to Power BI Service
2. Go to dataset settings
3. Configure data source credentials
4. Set refresh schedule (daily recommended)

---

## Step 6: Advanced Configuration

### Slicers and Filters
Add these for better interactivity:
- Date range slicer (if date columns available)
- Sector filter
- Investment category filter
- Market cap category filter

### Conditional Formatting
Apply to performance metrics:
- Green: > 10% performance
- Yellow: 0-10% performance  
- Red: < 0% performance

### Bookmarks
Create bookmarks for:
- Top performers view
- Sector analysis view
- Ethics compliance view

---

## Troubleshooting

### Data Not Loading
- Check file paths in M script
- Verify CSV files exist and aren't locked
- Ensure Power BI has file system permissions

### Performance Issues
- Limit data to last 2 years if datasets are large
- Use DirectQuery for very large datasets
- Optimize DAX measures for better performance

### Connection Errors
- Update file paths after moving export directory
- Check for special characters in file names
- Ensure CSV files have proper encoding (UTF-8)

---

## Automation Integration

### Daily Data Updates
1. Run investment system data export
2. Refresh Power BI dataset
3. Reports automatically update

### API Integration (Advanced)
- Use Power BI REST API for programmatic updates
- Set up automated refresh triggers
- Configure email alerts for data issues

---

## Support Files

- **Template**: `templates/investment_analysis_template.json`
- **M Script**: `templates/investment_data_connection.m` 
- **DAX Measures**: `templates/investment_dax_measures.dax`
- **Sample Data**: `exports/powerbi_import/*.csv`

For additional help, refer to the investment system documentation or Power BI community forums.
"""
        
        instructions_path = self.templates_dir / "powerbi_desktop_setup_guide.md"
        with open(instructions_path, 'w') as f:
            f.write(instructions)
        
        print(f"✅ Setup instructions created: {instructions_path}")
        return str(instructions_path)
    
    def create_automation_scripts(self) -> Dict[str, str]:
        """Create automation scripts for Power BI Desktop workflow"""
        
        scripts = {}
        
        # PowerShell script for automated setup
        powershell_script = '''# Power BI Desktop Automation Script
# Automates data export and Power BI refresh

param(
    [string]$PowerBIPath = "C:\\Program Files\\Microsoft Power BI Desktop\\bin\\PBIDesktop.exe",
    [string]$ReportPath = "",
    [switch]$ExportFirst = $false
)

Write-Host "🚀 Starting Power BI automation workflow..." -ForegroundColor Green

# Step 1: Export fresh data from investment system
if ($ExportFirst) {
    Write-Host "📊 Exporting fresh investment data..." -ForegroundColor Yellow
    cd (Split-Path $PSScriptRoot)
    python -m mcp.powerbi_mcp export
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Data export failed" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✅ Data export completed" -ForegroundColor Green
}

# Step 2: Open Power BI Desktop (if path provided)
if ($ReportPath -and (Test-Path $PowerBIPath)) {
    Write-Host "📈 Opening Power BI Desktop..." -ForegroundColor Yellow
    Start-Process $PowerBIPath -ArgumentList $ReportPath
    Write-Host "✅ Power BI Desktop started" -ForegroundColor Green
} else {
    Write-Host "⚠️  Power BI Desktop path not found or report path not specified" -ForegroundColor Yellow
    Write-Host "Manual refresh required in Power BI Desktop" -ForegroundColor Yellow
}

Write-Host "🏁 Automation workflow completed" -ForegroundColor Green
'''
        
        powershell_path = Path(__file__).parent / "automate_powerbi.ps1"
        with open(powershell_path, 'w') as f:
            f.write(powershell_script)
        scripts["powershell_automation"] = str(powershell_path)
        
        # Batch file for easy execution
        batch_script = f'''@echo off
REM Power BI Desktop Automation
REM Updates data and optionally opens Power BI Desktop

echo 🚀 Starting Power BI workflow...

REM Change to project directory
cd /d "{self.project_root}"

REM Export fresh data
echo 📊 Exporting investment data...
python -m mcp.powerbi_mcp export
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Data export failed
    pause
    exit /b 1
)

echo ✅ Data exported successfully
echo.
echo 📈 Next steps:
echo 1. Open Power BI Desktop
echo 2. Open your investment report
echo 3. Click Refresh to update data
echo.

REM Optionally open Power BI Desktop
set /p OPEN_PBI="Open Power BI Desktop? (y/n): "
if /i "%OPEN_PBI%"=="y" (
    start "" "C:\\Program Files\\Microsoft Power BI Desktop\\bin\\PBIDesktop.exe"
)

echo 🏁 Workflow completed
pause
'''
        
        batch_path = Path(__file__).parent / "run_powerbi_workflow.bat"
        with open(batch_path, 'w') as f:
            f.write(batch_script)
        scripts["batch_workflow"] = str(batch_path)
        
        # Python script for data validation
        python_validation = '''#!/usr/bin/env python3
"""
Power BI Data Validation Script
Validates exported data before Power BI import
"""

import pandas as pd
import json
import os
from pathlib import Path
from datetime import datetime

def validate_export_data():
    """Validate exported CSV files for Power BI"""
    
    export_dir = Path(__file__).parent.parent.parent / "powerbi_project" / "exports" / "powerbi_import"
    
    if not export_dir.exists():
        print("❌ Export directory not found")
        return False
    
    required_files = [
        "portfolio_summary.csv",
        "ai_robotics_stocks.csv", 
        "ethics_screening.csv",
        "smart_money_institutions.csv"
    ]
    
    validation_results = {}
    all_valid = True
    
    for file_name in required_files:
        file_path = export_dir / file_name
        
        if not file_path.exists():
            print(f"❌ Missing file: {file_name}")
            validation_results[file_name] = {"exists": False}
            all_valid = False
            continue
        
        try:
            df = pd.read_csv(file_path)
            validation_results[file_name] = {
                "exists": True,
                "rows": len(df),
                "columns": len(df.columns),
                "size_mb": round(file_path.stat().st_size / 1024 / 1024, 2),
                "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            }
            
            print(f"✅ {file_name}: {len(df)} rows, {len(df.columns)} columns")
            
            # Check for empty data
            if len(df) == 0:
                print(f"⚠️  {file_name} is empty")
                validation_results[file_name]["warning"] = "Empty dataset"
            
        except Exception as e:
            print(f"❌ Error reading {file_name}: {e}")
            validation_results[file_name]["error"] = str(e)
            all_valid = False
    
    # Save validation report
    report_path = export_dir / "validation_report.json"
    validation_report = {
        "validation_timestamp": datetime.now().isoformat(),
        "overall_status": "valid" if all_valid else "invalid",
        "files": validation_results
    }
    
    with open(report_path, 'w') as f:
        json.dump(validation_report, f, indent=2)
    
    print(f"\\n📋 Validation report saved: {report_path}")
    return all_valid

if __name__ == "__main__":
    print("🔍 Validating Power BI export data...")
    success = validate_export_data()
    
    if success:
        print("\\n✅ All data files are valid for Power BI import")
    else:
        print("\\n❌ Data validation failed - check files before importing to Power BI")
'''
        
        validation_path = Path(__file__).parent / "validate_powerbi_data.py"
        with open(validation_path, 'w') as f:
            f.write(python_validation)
        scripts["data_validation"] = str(validation_path)
        
        print("✅ Automation scripts created")
        return scripts
    
    def run_complete_setup(self) -> Dict[str, str]:
        """Run complete Power BI Desktop setup"""
        
        print("🚀 Starting complete Power BI Desktop setup...")
        
        results = {}
        
        # Create all components
        results["template"] = self.create_powerbi_template()
        results["m_script"] = self.generate_data_connection_script()
        results["dax_measures"] = self.create_dax_measures_file()
        results["instructions"] = self.create_setup_instructions()
        results.update(self.create_automation_scripts())
        
        # Export sample data
        print("📊 Exporting sample data...")
        from mcp.powerbi_mcp import PowerBIMCPServer
        powerbi_server = PowerBIMCPServer()
        export_results = powerbi_server.export_to_powerbi_format()
        
        if "error" not in export_results:
            results["sample_data"] = "✅ Sample data exported"
            print("✅ Sample data exported successfully")
        else:
            results["sample_data"] = f"❌ Sample data export failed: {export_results['error']}"
            print(f"❌ Sample data export failed: {export_results['error']}")
        
        print("\\n🎉 Power BI Desktop setup completed!")
        print("\\nCreated files:")
        for component, path in results.items():
            print(f"  {component}: {path}")
        
        print("\\n📖 Next steps:")
        print("1. Open Power BI Desktop")
        print("2. Follow the setup guide in templates/powerbi_desktop_setup_guide.md")
        print("3. Use the M script for data connections")
        print("4. Add DAX measures from the measures file")
        print("5. Run validation script before importing data")
        
        return results

def main():
    """Main CLI interface"""
    if len(sys.argv) < 2:
        print("Power BI Desktop Setup Tool")
        print("Usage: python setup_powerbi_desktop.py [command]")
        print("Commands:")
        print("  template    - Create Power BI template configuration")
        print("  script      - Generate M script for data connections")
        print("  measures    - Create DAX measures file")
        print("  instructions- Generate setup instructions")
        print("  automation  - Create automation scripts")
        print("  setup       - Run complete setup (all components)")
        return
    
    command = sys.argv[1]
    setup = PowerBIDesktopSetup()
    
    if command == "template":
        result = setup.create_powerbi_template()
        print(f"Template created: {result}")
    
    elif command == "script":
        result = setup.generate_data_connection_script()
        print(f"M script created: {result}")
    
    elif command == "measures":
        result = setup.create_dax_measures_file()
        print(f"DAX measures created: {result}")
    
    elif command == "instructions":
        result = setup.create_setup_instructions()
        print(f"Instructions created: {result}")
    
    elif command == "automation":
        results = setup.create_automation_scripts()
        print("Automation scripts created:")
        for name, path in results.items():
            print(f"  {name}: {path}")
    
    elif command == "setup":
        results = setup.run_complete_setup()
        print("\\nSetup completed successfully!")
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()