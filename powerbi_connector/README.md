# Power BI Connector

Python project to connect to Power BI Service and upload CSV data.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create Azure App Registration:**
   - Go to Azure Portal > App Registrations
   - Create new registration
   - Note: Client ID, Client Secret, Tenant ID
   - Add Power BI Service permissions

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. **Get Workspace ID:**
   - Go to Power BI Service
   - Navigate to workspace
   - Copy ID from URL

## Usage

```bash
python main.py
```

## Files

- `auth.py` - Authentication with Azure AD
- `powerbi_client.py` - Power BI API client
- `main.py` - Main execution script
- `.env` - Configuration (create from .env.example)

## Requirements

- Power BI Pro license
- Azure App Registration
- CSV data file