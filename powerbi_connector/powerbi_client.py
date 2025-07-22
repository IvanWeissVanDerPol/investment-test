import os
import json
import pandas as pd
import requests
from auth import PowerBIAuth
from dotenv import load_dotenv

class PowerBIClient:
    def __init__(self):
        load_dotenv()
        self.auth = PowerBIAuth()
        self.workspace_id = os.getenv('WORKSPACE_ID')
        self.base_url = "https://api.powerbi.com/v1.0/myorg"
        
    def create_dataset(self, dataset_name, csv_file_path):
        """Create a dataset from CSV file"""
        # Read CSV to understand structure
        df = pd.read_csv(csv_file_path)
        
        # Define dataset schema based on CSV
        dataset_def = {
            "name": dataset_name,
            "tables": [
                {
                    "name": "SalesData",
                    "columns": self._get_columns_from_dataframe(df)
                }
            ]
        }
        
        headers = self.auth.get_headers()
        url = f"{self.base_url}/groups/{self.workspace_id}/datasets"
        
        response = requests.post(url, headers=headers, json=dataset_def)
        
        if response.status_code == 201:
            dataset_id = response.json()['id']
            print(f"Dataset created successfully: {dataset_id}")
            return dataset_id
        else:
            raise Exception(f"Failed to create dataset: {response.text}")
    
    def upload_data_to_dataset(self, dataset_id, csv_file_path):
        """Upload CSV data to existing dataset"""
        df = pd.read_csv(csv_file_path)
        
        # Convert DataFrame to JSON format for Power BI
        rows = df.to_dict('records')
        
        # Upload data in batches
        headers = self.auth.get_headers()
        url = f"{self.base_url}/groups/{self.workspace_id}/datasets/{dataset_id}/tables/SalesData/rows"
        
        # Clear existing data first
        requests.delete(url, headers=headers)
        
        # Upload new data
        data = {"rows": rows}
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            print("Data uploaded successfully")
            return True
        else:
            raise Exception(f"Failed to upload data: {response.text}")
    
    def create_report_from_template(self, dataset_id, report_name):
        """Create a basic report with visualizations"""
        # This would typically involve creating a .pbix file or using Power BI REST API
        # For now, we'll create a basic report structure
        
        report_def = {
            "datasetId": dataset_id,
            "name": report_name
        }
        
        headers = self.auth.get_headers()
        url = f"{self.base_url}/groups/{self.workspace_id}/reports"
        
        # Note: Creating reports via REST API has limitations
        # You may need to use Power BI Embedded or upload a .pbix template
        print(f"Dataset {dataset_id} is ready for report creation in Power BI Service")
        return dataset_id
    
    def _get_columns_from_dataframe(self, df):
        """Convert DataFrame columns to Power BI column definitions"""
        columns = []
        for col in df.columns:
            dtype = df[col].dtype
            
            if dtype == 'object':
                if pd.api.types.is_datetime64_any_dtype(pd.to_datetime(df[col], errors='coerce')):
                    dataType = "DateTime"
                else:
                    dataType = "String"
            elif dtype in ['int64', 'int32']:
                dataType = "Int64"
            elif dtype in ['float64', 'float32']:
                dataType = "Double"
            else:
                dataType = "String"
            
            columns.append({
                "name": col,
                "dataType": dataType
            })
        
        return columns
    
    def get_workspaces(self):
        """List available workspaces"""
        headers = self.auth.get_headers()
        url = f"{self.base_url}/groups"
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()['value']
        else:
            raise Exception(f"Failed to get workspaces: {response.text}")
    
    def get_datasets(self):
        """List datasets in workspace"""
        headers = self.auth.get_headers()
        url = f"{self.base_url}/groups/{self.workspace_id}/datasets"
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()['value']
        else:
            raise Exception(f"Failed to get datasets: {response.text}")