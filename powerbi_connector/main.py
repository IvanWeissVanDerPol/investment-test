#!/usr/bin/env python3
"""
Power BI Connector - Upload CSV data to Power BI Service
"""

import os
from powerbi_client import PowerBIClient
from dotenv import load_dotenv

def main():
    """Main function to upload CSV data to Power BI"""
    load_dotenv()
    
    # Initialize client
    client = PowerBIClient()
    
    # Configuration
    csv_file_path = os.getenv('CSV_FILE_PATH', '../sample_sales_data.csv')
    dataset_name = "Sales_Data_Dashboard"
    report_name = "Sales Analytics Report"
    
    try:
        print("🔐 Authenticating with Power BI...")
        
        print("📁 Listing available workspaces...")
        workspaces = client.get_workspaces()
        print(f"Found {len(workspaces)} workspaces")
        
        print(f"📊 Creating dataset: {dataset_name}")
        dataset_id = client.create_dataset(dataset_name, csv_file_path)
        
        print(f"📤 Uploading data from: {csv_file_path}")
        client.upload_data_to_dataset(dataset_id, csv_file_path)
        
        print(f"📈 Creating report: {report_name}")
        client.create_report_from_template(dataset_id, report_name)
        
        print("✅ Successfully uploaded data to Power BI!")
        print(f"Dataset ID: {dataset_id}")
        print("You can now create visualizations in Power BI Service")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())