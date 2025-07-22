#!/usr/bin/env python3
"""
Power BI Authentication Setup Tool
Helps configure Azure AD app registration and Power BI API access
"""

import json
import os
import sys
from pathlib import Path
import getpass
import requests

class PowerBIAuthSetup:
    def __init__(self):
        self.config_path = Path(__file__).parent.parent.parent / "config" / "powerbi_config.json"
        self.config = self._load_config()
    
    def _load_config(self):
        """Load existing configuration"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_config(self):
        """Save configuration to file"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def interactive_setup(self):
        """Interactive setup wizard"""
        print("=== Power BI Authentication Setup ===")
        print()
        
        # Azure AD Configuration
        print("1. Azure AD App Registration Details")
        print("   (Create at: https://portal.azure.com → Azure Active Directory → App registrations)")
        print()
        
        client_id = input(f"Client ID (Application ID) [{self.config.get('client_id', '')}]: ").strip()
        if client_id:
            self.config['client_id'] = client_id
        
        tenant_id = input(f"Tenant ID (Directory ID) [{self.config.get('tenant_id', '')}]: ").strip()
        if tenant_id:
            self.config['tenant_id'] = tenant_id
        
        print()
        client_secret = getpass.getpass("Client Secret (hidden input): ").strip()
        if client_secret:
            self.config['client_secret'] = client_secret
        
        # Power BI Workspace
        print()
        print("2. Power BI Workspace Configuration")
        workspace_id = input(f"Workspace ID (optional) [{self.config.get('workspace_id', '')}]: ").strip()
        if workspace_id:
            self.config['workspace_id'] = workspace_id
        
        dataset_id = input(f"Dataset ID (optional) [{self.config.get('dataset_id', '')}]: ").strip()
        if dataset_id:
            self.config['dataset_id'] = dataset_id
        
        # Test connection
        print()
        test_connection = input("Test connection now? (y/n): ").lower().strip()
        if test_connection == 'y':
            if self.test_connection():
                print("✅ Connection successful!")
            else:
                print("❌ Connection failed. Check your credentials.")
        
        # Save configuration
        self._save_config()
        print(f"✅ Configuration saved to: {self.config_path}")
        
        return True
    
    def test_connection(self):
        """Test Power BI API connection"""
        if not all([self.config.get('client_id'), self.config.get('client_secret'), self.config.get('tenant_id')]):
            print("❌ Missing required authentication configuration")
            return False
        
        try:
            import msal
            
            app = msal.ConfidentialClientApplication(
                self.config['client_id'],
                authority=f"https://login.microsoftonline.com/{self.config['tenant_id']}",
                client_credential=self.config['client_secret']
            )
            
            result = app.acquire_token_for_client(
                scopes=["https://analysis.windows.net/powerbi/api/.default"]
            )
            
            if "access_token" in result:
                # Test API call
                headers = {
                    "Authorization": f"Bearer {result['access_token']}",
                    "Content-Type": "application/json"
                }
                
                response = requests.get(
                    "https://api.powerbi.com/v1.0/myorg/groups",
                    headers=headers
                )
                
                if response.status_code == 200:
                    workspaces = response.json().get('value', [])
                    print(f"✅ Found {len(workspaces)} workspaces")
                    
                    if workspaces:
                        print("Available workspaces:")
                        for ws in workspaces[:5]:  # Show first 5
                            print(f"  - {ws['name']} (ID: {ws['id']})")
                    
                    return True
                else:
                    print(f"❌ API call failed: {response.status_code}")
                    return False
            else:
                print(f"❌ Token acquisition failed: {result.get('error_description', 'Unknown error')}")
                return False
                
        except ImportError:
            print("❌ Missing required package: pip install msal")
            return False
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False
    
    def generate_setup_script(self):
        """Generate PowerShell script for Azure AD app setup"""
        script = """# Power BI Azure AD App Registration Setup Script
# Run this in Azure Cloud Shell or with Azure PowerShell module

# Login to Azure (if not already logged in)
# Connect-AzAccount

# Variables
$AppName = "Investment System Power BI Integration"
$RequiredResourceAccess = @(
    @{
        ResourceAppId = "00000009-0000-0000-c000-000000000000" # Power BI Service
        ResourceAccess = @(
            @{
                Id = "4ae1bf56-f562-4747-b7bc-2fa0874ed46f" # Dataset.ReadWrite.All
                Type = "Role"
            },
            @{
                Id = "7504609f-c495-4c64-8542-686125a5a36c" # Report.ReadWrite.All  
                Type = "Role"
            },
            @{
                Id = "2448370f-f988-42cd-909c-6528efd67c1a" # Workspace.ReadWrite.All
                Type = "Role"
            }
        )
    }
)

# Create the application
$App = New-AzADApplication -DisplayName $AppName -RequiredResourceAccess $RequiredResourceAccess

# Create service principal
$SP = New-AzADServicePrincipal -ApplicationId $App.AppId

# Create client secret (valid for 2 years)
$Secret = New-AzADAppCredential -ApplicationId $App.AppId -EndDate (Get-Date).AddYears(2)

Write-Host "Application created successfully!" -ForegroundColor Green
Write-Host "Client ID: $($App.AppId)" -ForegroundColor Yellow
Write-Host "Tenant ID: $((Get-AzContext).Tenant.Id)" -ForegroundColor Yellow
Write-Host "Client Secret: $($Secret.SecretText)" -ForegroundColor Red
Write-Host ""
Write-Host "IMPORTANT: Save the client secret - you won't see it again!" -ForegroundColor Red
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Grant admin consent for the application in Azure Portal"
Write-Host "2. Add the service principal to your Power BI workspace"
Write-Host "3. Configure the MCP server with these credentials"
"""
        
        script_path = Path(__file__).parent / "setup_azure_app.ps1"
        with open(script_path, 'w') as f:
            f.write(script)
        
        print(f"✅ Azure setup script generated: {script_path}")
        return script_path
    
    def show_permissions_guide(self):
        """Show required permissions setup guide"""
        guide = """
=== Power BI API Permissions Setup ===

Required Application Permissions:
1. Dataset.ReadWrite.All - Read and write all datasets
2. Report.ReadWrite.All - Read and write all reports  
3. Workspace.ReadWrite.All - Read and write all workspaces

Setup Steps:
1. Go to Azure Portal → Azure Active Directory → App registrations
2. Select your application
3. Go to "API permissions"
4. Click "Add a permission"
5. Select "Power BI Service"
6. Choose "Application permissions"
7. Add the required permissions above
8. Click "Grant admin consent for [your organization]"

Workspace Access:
1. In Power BI Service, go to your workspace
2. Click "Access" 
3. Add your service principal with "Admin" or "Member" role
4. The service principal name will be your app registration name

Testing:
Use the test_connection() method to verify setup is correct.
"""
        print(guide)

def main():
    """Main CLI interface"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        setup = PowerBIAuthSetup()
        
        if command == "setup":
            setup.interactive_setup()
        elif command == "test":
            setup.test_connection()
        elif command == "script":
            setup.generate_setup_script()
        elif command == "permissions":
            setup.show_permissions_guide()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: setup, test, script, permissions")
    else:
        print("Power BI Authentication Setup Tool")
        print("Usage: python setup_powerbi_auth.py [command]")
        print("Commands:")
        print("  setup       - Interactive setup wizard")
        print("  test        - Test existing configuration")
        print("  script      - Generate Azure PowerShell setup script")
        print("  permissions - Show permissions setup guide")

if __name__ == "__main__":
    main()