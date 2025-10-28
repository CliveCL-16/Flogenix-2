# Start both backend and frontend in separate PowerShell windows
Write-Host "Starting Flogenix Full Application..." -ForegroundColor Green

# Start backend in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$pwd\..\backend'; python main.py"

# Wait a moment for backend to start
Start-Sleep -Seconds 3

# Start frontend in new window  
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$pwd\..\frontend'; npm run dev"

Write-Host "Both servers are starting in separate windows..." -ForegroundColor Yellow
Write-Host "Backend: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Cyan