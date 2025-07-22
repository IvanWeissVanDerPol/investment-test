#!/usr/bin/env python3
"""
Power BI Report Automation Tools
Automates report generation, exports, and distribution for investment system
"""

import json
import os
import sys
import base64
import io
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import time

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))
from mcp.powerbi_mcp import PowerBIMCPServer

class PowerBIReportAutomation:
    """Automates Power BI report operations"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.powerbi_server = PowerBIMCPServer(config_path)
        self.exports_dir = Path(__file__).parent.parent.parent / "powerbi_project" / "exports"
        self.reports_dir = Path(__file__).parent.parent.parent / "reports"
        
    def create_investment_report_template(self) -> Dict[str, Any]:
        """Define Power BI report template for investment analysis"""
        report_template = {
            "name": "Investment System Dashboard",
            "pages": [
                {
                    "name": "Executive Summary",
                    "displayName": "Executive Summary",
                    "visuals": [
                        {
                            "title": "Portfolio Overview",
                            "visualType": "card",
                            "config": {
                                "measure": "Total Securities",
                                "format": "number",
                                "position": {"x": 0, "y": 0, "width": 200, "height": 100}
                            }
                        },
                        {
                            "title": "AI/Robotics Focus",
                            "visualType": "donutChart",
                            "config": {
                                "category": "investment_category",
                                "measure": "Count",
                                "position": {"x": 220, "y": 0, "width": 300, "height": 200}
                            }
                        },
                        {
                            "title": "Performance Overview",
                            "visualType": "columnChart",
                            "config": {
                                "category": "sector",
                                "measure": "Average YTD Performance",
                                "position": {"x": 0, "y": 220, "width": 520, "height": 250}
                            }
                        },
                        {
                            "title": "Top Performers",
                            "visualType": "table",
                            "config": {
                                "columns": ["symbol", "name", "ytd_performance_pct"],
                                "sort": {"column": "ytd_performance_pct", "direction": "desc"},
                                "top": 10,
                                "position": {"x": 540, "y": 0, "width": 400, "height": 470}
                            }
                        }
                    ]
                },
                {
                    "name": "Detailed Analysis",
                    "displayName": "Detailed Analysis", 
                    "visuals": [
                        {
                            "title": "Stock Performance Matrix",
                            "visualType": "matrix",
                            "config": {
                                "rows": ["sector"],
                                "columns": ["investment_category"],
                                "values": ["Average YTD Performance"],
                                "position": {"x": 0, "y": 0, "width": 500, "height": 300}
                            }
                        },
                        {
                            "title": "Price vs Performance",
                            "visualType": "scatterChart",
                            "config": {
                                "x_axis": "current_price",
                                "y_axis": "ytd_performance_pct",
                                "size": "market_cap_category",
                                "color": "sector",
                                "position": {"x": 520, "y": 0, "width": 420, "height": 300}
                            }
                        },
                        {
                            "title": "Detailed Stock List",
                            "visualType": "table",
                            "config": {
                                "columns": [
                                    "symbol", "name", "sector", "current_price", 
                                    "ytd_performance_pct", "market_cap_category"
                                ],
                                "position": {"x": 0, "y": 320, "width": 940, "height": 300}
                            }
                        }
                    ]
                },
                {
                    "name": "Ethics & Compliance",
                    "displayName": "Ethics & Compliance",
                    "visuals": [
                        {
                            "title": "Ethics Screening Results",
                            "visualType": "card",
                            "config": {
                                "measure": "Ethics Violations",
                                "format": "number",
                                "position": {"x": 0, "y": 0, "width": 200, "height": 100}
                            }
                        },
                        {
                            "title": "Recent Ethics Issues",
                            "visualType": "card",
                            "config": {
                                "measure": "Recent Ethics Issues",
                                "format": "number",
                                "position": {"x": 220, "y": 0, "width": 200, "height": 100}
                            }
                        },
                        {
                            "title": "Blocked Stocks",
                            "visualType": "table",
                            "config": {
                                "columns": ["symbol", "name", "reason", "alternative_symbol"],
                                "position": {"x": 0, "y": 120, "width": 700, "height": 300}
                            }
                        },
                        {
                            "title": "Ethics Timeline",
                            "visualType": "lineChart",
                            "config": {
                                "x_axis": "created_at",
                                "y_axis": "Count",
                                "position": {"x": 720, "y": 120, "width": 220, "height": 300}
                            }
                        }
                    ]
                },
                {
                    "name": "Smart Money",
                    "displayName": "Smart Money Tracking",
                    "visuals": [
                        {
                            "title": "Institution Overview",
                            "visualType": "card",
                            "config": {
                                "measure": "High Priority Institutions",
                                "format": "number",
                                "position": {"x": 0, "y": 0, "width": 200, "height": 100}
                            }
                        },
                        {
                            "title": "AI Focused Funds",
                            "visualType": "card",
                            "config": {
                                "measure": "AI Focused Institutions",
                                "format": "number",
                                "position": {"x": 220, "y": 0, "width": 200, "height": 100}
                            }
                        },
                        {
                            "title": "Institution Priority Distribution",
                            "visualType": "pieChart",
                            "config": {
                                "category": "priority",
                                "measure": "Count",
                                "position": {"x": 440, "y": 0, "width": 250, "height": 200}
                            }
                        },
                        {
                            "title": "Smart Money Institutions",
                            "visualType": "table",
                            "config": {
                                "columns": ["name", "focus_area", "priority"],
                                "sort": {"column": "priority", "direction": "asc"},
                                "position": {"x": 0, "y": 220, "width": 690, "height": 300}
                            }
                        }
                    ]
                }
            ]
        }
        return report_template
    
    def export_report_to_pdf(self, report_id: str, workspace_id: Optional[str] = None, 
                           output_path: Optional[str] = None) -> Optional[str]:
        """Export Power BI report to PDF"""
        workspace_id = workspace_id or self.powerbi_server.config.get("workspace_id")
        
        if workspace_id:
            endpoint = f"groups/{workspace_id}/reports/{report_id}/ExportTo"
        else:
            endpoint = f"reports/{report_id}/ExportTo"
        
        export_config = {
            "format": "PDF",
            "powerBIReportConfiguration": {
                "settings": {
                    "includeHiddenPages": False
                }
            }
        }
        
        # Start export
        result = self.powerbi_server._make_api_request(endpoint, method="POST", data=export_config)
        
        if not result or "id" not in result:
            print("❌ Failed to start report export")
            return None
        
        export_id = result["id"]
        print(f"📄 Export started: {export_id}")
        
        # Poll for completion
        if workspace_id:
            status_endpoint = f"groups/{workspace_id}/reports/{report_id}/exports/{export_id}"
        else:
            status_endpoint = f"reports/{report_id}/exports/{export_id}"
        
        max_attempts = 30  # 5 minutes max
        for attempt in range(max_attempts):
            time.sleep(10)  # Wait 10 seconds between checks
            
            status = self.powerbi_server._make_api_request(status_endpoint)
            if not status:
                continue
            
            export_status = status.get("status")
            print(f"📊 Export status: {export_status}")
            
            if export_status == "Succeeded":
                # Get the file
                if workspace_id:
                    file_endpoint = f"groups/{workspace_id}/reports/{report_id}/exports/{export_id}/file"
                else:
                    file_endpoint = f"reports/{report_id}/exports/{export_id}/file"
                
                file_result = self.powerbi_server._make_api_request(file_endpoint)
                
                if file_result:
                    # Save the PDF
                    if not output_path:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        output_path = self.exports_dir / f"investment_report_{timestamp}.pdf"
                    
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    
                    # The API returns binary data
                    with open(output_path, 'wb') as f:
                        f.write(base64.b64decode(file_result))
                    
                    print(f"✅ Report exported to: {output_path}")
                    return str(output_path)
                
            elif export_status == "Failed":
                print("❌ Export failed")
                return None
        
        print("⏰ Export timed out")
        return None
    
    def export_report_to_powerpoint(self, report_id: str, workspace_id: Optional[str] = None,
                                  output_path: Optional[str] = None) -> Optional[str]:
        """Export Power BI report to PowerPoint"""
        workspace_id = workspace_id or self.powerbi_server.config.get("workspace_id")
        
        if workspace_id:
            endpoint = f"groups/{workspace_id}/reports/{report_id}/ExportTo"
        else:
            endpoint = f"reports/{report_id}/ExportTo"
        
        export_config = {
            "format": "PPTX",
            "powerBIReportConfiguration": {
                "settings": {
                    "includeHiddenPages": False
                }
            }
        }
        
        # Similar process as PDF export
        result = self.powerbi_server._make_api_request(endpoint, method="POST", data=export_config)
        
        if not result or "id" not in result:
            print("❌ Failed to start PowerPoint export")
            return None
        
        export_id = result["id"]
        print(f"📊 PowerPoint export started: {export_id}")
        
        # Poll for completion (similar to PDF)
        if workspace_id:
            status_endpoint = f"groups/{workspace_id}/reports/{report_id}/exports/{export_id}"
        else:
            status_endpoint = f"reports/{report_id}/exports/{export_id}"
        
        max_attempts = 30
        for attempt in range(max_attempts):
            time.sleep(10)
            
            status = self.powerbi_server._make_api_request(status_endpoint)
            if not status:
                continue
            
            export_status = status.get("status")
            print(f"📈 Export status: {export_status}")
            
            if export_status == "Succeeded":
                if workspace_id:
                    file_endpoint = f"groups/{workspace_id}/reports/{report_id}/exports/{export_id}/file"
                else:
                    file_endpoint = f"reports/{report_id}/exports/{export_id}/file"
                
                file_result = self.powerbi_server._make_api_request(file_endpoint)
                
                if file_result:
                    if not output_path:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        output_path = self.exports_dir / f"investment_presentation_{timestamp}.pptx"
                    
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    
                    with open(output_path, 'wb') as f:
                        f.write(base64.b64decode(file_result))
                    
                    print(f"✅ Presentation exported to: {output_path}")
                    return str(output_path)
                
            elif export_status == "Failed":
                print("❌ PowerPoint export failed")
                return None
        
        print("⏰ PowerPoint export timed out")
        return None
    
    def get_report_pages(self, report_id: str, workspace_id: Optional[str] = None) -> List[Dict]:
        """Get pages in a report"""
        workspace_id = workspace_id or self.powerbi_server.config.get("workspace_id")
        
        if workspace_id:
            endpoint = f"groups/{workspace_id}/reports/{report_id}/pages"
        else:
            endpoint = f"reports/{report_id}/pages"
        
        result = self.powerbi_server._make_api_request(endpoint)
        return result.get("value", []) if result else []
    
    def clone_report(self, report_id: str, new_name: str, target_workspace_id: Optional[str] = None,
                    source_workspace_id: Optional[str] = None) -> Optional[str]:
        """Clone a report to create a new copy"""
        source_workspace_id = source_workspace_id or self.powerbi_server.config.get("workspace_id")
        target_workspace_id = target_workspace_id or source_workspace_id
        
        if source_workspace_id:
            endpoint = f"groups/{source_workspace_id}/reports/{report_id}/Clone"
        else:
            endpoint = f"reports/{report_id}/Clone"
        
        clone_config = {
            "name": new_name,
            "targetWorkspaceId": target_workspace_id
        }
        
        result = self.powerbi_server._make_api_request(endpoint, method="POST", data=clone_config)
        
        if result and "id" in result:
            new_report_id = result["id"]
            print(f"✅ Report cloned successfully: {new_report_id}")
            return new_report_id
        else:
            print("❌ Failed to clone report")
            return None
    
    def schedule_report_export(self, report_id: str, format_type: str = "PDF", 
                             schedule_config: Optional[Dict] = None) -> Dict[str, Any]:
        """Schedule automated report exports"""
        if not schedule_config:
            schedule_config = {
                "frequency": "daily",
                "time": "07:00",
                "timezone": "UTC",
                "enabled": True,
                "email_recipients": [],
                "export_format": format_type
            }
        
        # This would typically integrate with a task scheduler or cron job
        scheduler_config = {
            "report_id": report_id,
            "workspace_id": self.powerbi_server.config.get("workspace_id"),
            "schedule": schedule_config,
            "created_at": datetime.now().isoformat()
        }
        
        # Save schedule configuration
        schedules_dir = self.exports_dir / "schedules"
        os.makedirs(schedules_dir, exist_ok=True)
        
        schedule_file = schedules_dir / f"report_{report_id}_schedule.json"
        with open(schedule_file, 'w') as f:
            json.dump(scheduler_config, f, indent=2)
        
        print(f"✅ Export schedule saved: {schedule_file}")
        return scheduler_config
    
    def generate_report_summary(self, report_id: str, workspace_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate summary information about a report"""
        workspace_id = workspace_id or self.powerbi_server.config.get("workspace_id")
        
        # Get report info
        if workspace_id:
            endpoint = f"groups/{workspace_id}/reports/{report_id}"
        else:
            endpoint = f"reports/{report_id}"
        
        report_info = self.powerbi_server._make_api_request(endpoint)
        
        if not report_info:
            return {"error": "Report not found"}
        
        # Get pages
        pages = self.get_report_pages(report_id, workspace_id)
        
        # Get dataset info
        dataset_id = report_info.get("datasetId")
        dataset_info = None
        if dataset_id:
            if workspace_id:
                dataset_endpoint = f"groups/{workspace_id}/datasets/{dataset_id}"
            else:
                dataset_endpoint = f"datasets/{dataset_id}"
            dataset_info = self.powerbi_server._make_api_request(dataset_endpoint)
        
        summary = {
            "report_id": report_id,
            "name": report_info.get("name"),
            "created_date": report_info.get("createdDateTime"),
            "modified_date": report_info.get("modifiedDateTime"),
            "dataset_id": dataset_id,
            "dataset_name": dataset_info.get("name") if dataset_info else None,
            "pages": [{"name": p.get("name"), "displayName": p.get("displayName")} for p in pages],
            "page_count": len(pages),
            "web_url": report_info.get("webUrl"),
            "embed_url": report_info.get("embedUrl")
        }
        
        return summary
    
    def create_automated_report_workflow(self) -> Dict[str, str]:
        """Create automated workflow for investment reports"""
        workflow_scripts = {}
        
        # Daily report automation script
        daily_script = """#!/usr/bin/env python3
\"\"\"
Daily Investment Report Automation
Automatically generates and exports investment reports
\"\"\"

import sys
import os
from pathlib import Path

# Add project path
sys.path.append(str(Path(__file__).parent.parent.parent))

from tools.powerbi.report_automation import PowerBIReportAutomation
from tools.powerbi.dataset_manager import PowerBIDatasetManager

def main():
    print("🚀 Starting daily investment report generation...")
    
    # Update dataset with fresh data
    dataset_manager = PowerBIDatasetManager()
    print("📊 Updating dataset with fresh investment data...")
    success = dataset_manager.update_dataset_data()
    
    if not success:
        print("❌ Failed to update dataset")
        return False
    
    # Export reports
    report_automation = PowerBIReportAutomation()
    
    # Get report ID from config or environment
    report_id = os.getenv('POWERBI_REPORT_ID')
    if not report_id:
        print("❌ POWERBI_REPORT_ID environment variable not set")
        return False
    
    timestamp = datetime.now().strftime("%Y%m%d")
    
    # Export PDF
    pdf_path = report_automation.export_report_to_pdf(
        report_id, 
        output_path=f"./reports/daily/investment_report_{timestamp}.pdf"
    )
    
    # Export PowerPoint  
    pptx_path = report_automation.export_report_to_powerpoint(
        report_id,
        output_path=f"./reports/daily/investment_presentation_{timestamp}.pptx"
    )
    
    print("✅ Daily report generation completed")
    print(f"📄 PDF: {pdf_path}")
    print(f"📊 PowerPoint: {pptx_path}")
    
    return True

if __name__ == "__main__":
    from datetime import datetime
    success = main()
    sys.exit(0 if success else 1)
"""
        
        daily_script_path = Path(__file__).parent / "daily_report_automation.py"
        with open(daily_script_path, 'w') as f:
            f.write(daily_script)
        workflow_scripts["daily_automation"] = str(daily_script_path)
        
        # Batch file for Windows scheduling
        batch_script = f"""@echo off
REM Daily Investment Report Generation
REM Schedule this with Windows Task Scheduler

cd /d "{Path(__file__).parent.parent.parent}"
python tools\\powerbi\\daily_report_automation.py

if %ERRORLEVEL% EQU 0 (
    echo Report generation successful
) else (
    echo Report generation failed
    exit /b 1
)
"""
        
        batch_script_path = Path(__file__).parent / "run_daily_reports.bat"
        with open(batch_script_path, 'w') as f:
            f.write(batch_script)
        workflow_scripts["batch_automation"] = str(batch_script_path)
        
        print("✅ Automated workflow scripts created")
        return workflow_scripts

def main():
    """Main CLI interface"""
    if len(sys.argv) < 2:
        print("Power BI Report Automation")
        print("Usage: python report_automation.py [command] [options]")
        print("Commands:")
        print("  export-pdf [report_id] [output_path]     - Export report to PDF")
        print("  export-pptx [report_id] [output_path]    - Export report to PowerPoint")
        print("  pages [report_id]                        - List report pages")
        print("  clone [report_id] [new_name]             - Clone report")
        print("  schedule [report_id] [format]            - Schedule automated exports")
        print("  summary [report_id]                      - Get report summary")
        print("  workflow                                 - Create automation workflows")
        return
    
    command = sys.argv[1]
    automation = PowerBIReportAutomation()
    
    if command == "export-pdf":
        report_id = sys.argv[2] if len(sys.argv) > 2 else None
        output_path = sys.argv[3] if len(sys.argv) > 3 else None
        if not report_id:
            print("❌ Report ID required")
            return
        result = automation.export_report_to_pdf(report_id, output_path=output_path)
        print(f"Export result: {result}")
    
    elif command == "export-pptx":
        report_id = sys.argv[2] if len(sys.argv) > 2 else None
        output_path = sys.argv[3] if len(sys.argv) > 3 else None
        if not report_id:
            print("❌ Report ID required")
            return
        result = automation.export_report_to_powerpoint(report_id, output_path=output_path)
        print(f"Export result: {result}")
    
    elif command == "pages":
        report_id = sys.argv[2] if len(sys.argv) > 2 else None
        if not report_id:
            print("❌ Report ID required")
            return
        pages = automation.get_report_pages(report_id)
        print(json.dumps(pages, indent=2))
    
    elif command == "clone":
        report_id = sys.argv[2] if len(sys.argv) > 2 else None
        new_name = sys.argv[3] if len(sys.argv) > 3 else None
        if not report_id or not new_name:
            print("❌ Report ID and new name required")
            return
        new_id = automation.clone_report(report_id, new_name)
        print(f"Cloned report ID: {new_id}")
    
    elif command == "schedule":
        report_id = sys.argv[2] if len(sys.argv) > 2 else None
        format_type = sys.argv[3] if len(sys.argv) > 3 else "PDF"
        if not report_id:
            print("❌ Report ID required")
            return
        config = automation.schedule_report_export(report_id, format_type)
        print(json.dumps(config, indent=2))
    
    elif command == "summary":
        report_id = sys.argv[2] if len(sys.argv) > 2 else None
        if not report_id:
            print("❌ Report ID required")
            return
        summary = automation.generate_report_summary(report_id)
        print(json.dumps(summary, indent=2))
    
    elif command == "workflow":
        scripts = automation.create_automated_report_workflow()
        print("Created workflow scripts:")
        for name, path in scripts.items():
            print(f"  {name}: {path}")
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()