#!/bin/bash
echo "🏥 Flowgenix Setup for Unix/Linux/Mac"
echo "===================================="

# Setup backend
echo "Setting up backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

# Setup frontend  
echo "Setting up frontend..."
cd frontend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Copy backend/.env.example to backend/.env and add your OpenAI API key"
echo "2. Start backend: cd backend && source venv/bin/activate && python main.py"
echo "3. Start frontend: cd frontend && source venv/bin/activate && streamlit run app.py"
echo "4. Generate demo data: python demo_scenarios.py"