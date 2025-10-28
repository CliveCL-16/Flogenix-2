# Quick Start Scripts

This folder contains convenience scripts to quickly start the Flogenix application.

## For Windows (PowerShell)

### Start Backend
```powershell
.\start_backend.ps1
```

### Start Frontend  
```powershell
.\start_frontend.ps1
```

### Start Both (in separate terminals)
```powershell
.\start_full_app.ps1
```

## For Linux/Mac (Bash)

### Start Backend
```bash
./start_backend.sh
```

### Start Frontend
```bash
./start_frontend.sh
```

### Start Both
```bash
./start_full_app.sh
```

## Manual Start

### Backend
```bash
cd backend
python main.py
```

### Frontend
```bash
cd frontend
npm install  # First time only
npm run dev
```

## Access Points

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Troubleshooting

### Backend Issues
- Ensure Python 3.8+ is installed
- Install dependencies: `pip install -r requirements.txt`
- Check port 8000 is not in use

### Frontend Issues  
- Ensure Node.js 16+ is installed
- Run `npm install` if modules are missing
- Check port 5173 is not in use

### CORS Issues
- Backend is configured for common frontend ports
- If using custom port, update CORS settings in `backend/main.py`