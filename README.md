# PyQt6 Digital Display Application

A PyQt6-based digital display application for corporate dashboards, supporting Power BI reports, SharePoint documents, and PI Vision displays with Windows authentication.

## Features

- **Multi-window display management** - Arrange multiple web pages across your screen
- **Windows Authentication** - Seamless SSO for Power BI, SharePoint, and corporate domains
- **Layout Management** - Save and restore custom window layouts
- **Popup Authentication** - Handles Microsoft OAuth flows in dedicated windows
- **Drag & Resize** - Edit mode for repositioning windows
- **Profile Persistence** - Maintains login sessions between app restarts

## Requirements

- Windows 10/11
- Python 3.10+
- Corporate network access for target domains
- PyQt6 and PyQt6-WebEngine

## Installation

1. Clone the repository:
   ```powershell
   git clone https://github.com/SupplychainGantour/affichage.git
   cd affichage
   ```

2. Create a virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

## Configuration

### Window Configuration (`config/windows.json`)
Define your pages and their positions:
```json
[
  {
    "id": "powerbi_report",
    "url": "https://app.powerbi.com/reportEmbed?reportId=YOUR_REPORT_ID&autoAuth=true&ctid=YOUR_TENANT_ID",
    "geometry": { "x": 850, "y": 50, "width": 1000, "height": 700 }
  }
]
```

### Optional Authentication (`config/auth.json`)
For explicit credentials (if Windows SSO isn't available):
```json
{
  "username": "DOMAIN\\your.username", 
  "password": "your-password"
}
```

## Usage

Run the application:
```powershell
python main.py
```

### Controls
- **Menu button (☰)** - Open screen layout manager
- **Reload button (↻)** - Refresh all pages
- **Edit button (✎)** - Toggle drag/resize mode
- **Save button (✓)** - Save current layout (edit mode only)
- **Quit button (Q)** - Close application

### Authentication
- Windows authentication is handled automatically for configured domains
- Authentication popups will appear for Microsoft services when needed
- Sessions persist between app restarts

## Supported Services

- **Power BI** - Embedded reports and dashboards
- **SharePoint** - Documents and lists
- **PI Vision** - Process intelligence dashboards
- **Any web content** - Via corporate authentication

## Remote Debugging

Chrome DevTools available at `http://localhost:9222` for troubleshooting web content.

## License

MIT License