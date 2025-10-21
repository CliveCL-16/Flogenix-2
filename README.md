# Flowgenix - Intelligent Autonomous Healthcare Claims Approval Platform

An **agentic AI-powered** healthcare claims processing system that uses multi-agent collaboration to autonomously process medical insurance claims, detect fraud, handle exceptions with learning capabilities, and provide real-time dashboards.

## 🤖 Agentic AI Architecture

Flowgenix leverages **LangChain and LangGraph** to implement a true multi-agent system where specialized AI agents collaborate autonomously:

### Specialized Agents
- **🔍 Intake Agent**: Validates claim data and extracts entities
- **✅ Eligibility Agent**: Verifies insurance coverage and provider credentials  
- **🏥 Clinical Review Agent**: Validates medical codes and compatibility
- **🚨 Fraud Detection Agent**: Investigates patterns and calculates risk scores
- **⚖️ Adjudication Agent**: Synthesizes all reports and makes final decisions
- **🔧 Exception Handler Agent**: Manages exceptions with learning from past cases

### Agentic Capabilities
- **Autonomous Decision Making**: Agents independently choose tools and actions
- **ReAct Reasoning**: Reason → Act → Observe pattern with full transparency
- **Tool Integration**: Agents autonomously invoke APIs, databases, and external services
- **Multi-Agent Collaboration**: Agents communicate, share state, and hand off tasks
- **Adaptive Learning**: Exception handling that learns from past resolutions

## Features

- 🤖 **Multi-Agent Processing**: Specialized AI agents collaborate autonomously
- 🔍 **Fraud Detection**: Pattern-based fraud detection with real-time scoring
- 🧠 **Self-Learning Exception Handling**: Learn from exceptions and auto-resolve future similar cases
- 📊 **Real-Time Dashboard**: Live metrics and claim status tracking
- 🔍 **Explainable AI**: Natural language explanations for all AI decisions
- 🕸️ **Agent Visualization**: See agents collaborate in real-time with reasoning transparency

## Project Structure

```
flowgenix/
├── backend/                 # FastAPI backend with multi-agent system
│   ├── app/
│   │   ├── models/         # Pydantic models including agent state
│   │   ├── api/            # API endpoints + agent timeline endpoints
│   │   └── services/       # Multi-agent processor, agent tools, AI services
│   ├── main.py             # FastAPI application
│   └── requirements.txt    # Includes LangChain/LangGraph dependencies
├── frontend/               # Streamlit dashboard with agent visualization
│   ├── app.py             # Main Streamlit app with agent processing view
│   ├── utils/             # API client with agent endpoint support
│   └── requirements.txt   # Frontend dependencies
├── data/                  # JSON data storage
└── demo_scenarios.py      # Generate test data for agent demonstration
```

## Quick Start

### Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # On Windows (or source venv/bin/activate on Unix)
pip install -r requirements.txt
# Create .env file with: OPENAI_API_KEY=your_key_here
python main.py
```

### Frontend Setup
```bash
cd frontend
python -m venv venv
venv\Scripts\activate  # On Windows (or source venv/bin/activate on Unix)
pip install -r requirements.txt
streamlit run app.py
```

### Generate Demo Data
```bash
python demo_scenarios.py
```

## 🎯 Demo Scenarios

### 1. **Happy Path**: Multi-Agent Approval
- Submit routine checkup claim
- Watch agents collaborate: Intake → Eligibility & Clinical & Fraud (parallel) → Adjudication
- See real-time agent reasoning and tool usage
- **Demonstrates**: Autonomous agent collaboration

### 2. **Exception Learning**: Agent Memory
- Submit specialist claim missing referral
- Exception Handler Agent escalates to human review
- Submit similar claim - Agent auto-resolves using learned solution
- **Demonstrates**: Agent learning and memory

### 3. **Fraud Detection**: Agent Investigation
- Submit duplicate claim
- Fraud Detection Agent queries database, detects pattern
- Agent autonomously flags for investigation
- **Demonstrates**: Proactive agent investigation

### 4. **Code Mismatch**: Clinical Agent Reasoning
- Submit claim with incompatible diagnosis/procedure codes
- Clinical Review Agent validates codes, detects mismatch
- Agent provides detailed reasoning for denial
- **Demonstrates**: Domain-specific agent expertise

## 🤖 Agentic AI Dashboard Features

### Agent Processing Timeline
- Real-time visualization of agents working
- Processing duration and status for each agent
- Agent handoff visualization

### Agent Reasoning Logs (ReAct Pattern)
- **Reason**: Agent analyzes situation and decides what to do
- **Act**: Agent uses tools (APIs, databases, calculations)
- **Observe**: Agent reviews results and updates understanding
- Complete transparency into agent thought processes

### Agent Communication Graph
- Network diagram showing agent collaboration
- Visual representation of information flow
- Multi-agent coordination patterns

### Tool Usage Dashboard  
- Which tools each agent used
- Success/failure status of tool calls
- Parameters and results for each tool invocation

## Technology Stack

- **Backend**: FastAPI, LangChain, LangGraph, OpenAI GPT-4
- **Frontend**: Streamlit with real-time agent visualization
- **Data Storage**: JSON files (MVP), PostgreSQL (future)
- **AI/ML**: Multi-agent system with autonomous tool selection
- **Agent Framework**: LangChain agents with ReAct reasoning

## API Endpoints

### Standard Endpoints
- `POST /api/claims/submit` - Submit new claim
- `POST /api/claims/{id}/process` - Process with multi-agent system
- `GET /api/claims` - List all claims
- `GET /api/claims/{id}` - Get claim details

### Agent-Specific Endpoints
- `GET /api/claims/{id}/agent-timeline` - Agent processing timeline
- `GET /api/claims/{id}/agent-reasoning` - Detailed agent reasoning steps
- `GET /api/claims/{id}/tool-usage` - Tool usage by all agents
- `GET /api/dashboard/metrics` - Dashboard metrics

## Why This is True "Agentic AI"

✅ **Autonomous Agents**: Each agent makes independent decisions about tools and actions
✅ **Goal-Oriented**: Agents have specific objectives and work toward them autonomously  
✅ **Tool Usage**: Agents select and execute appropriate tools based on context
✅ **Multi-Agent Collaboration**: Specialized agents communicate and hand off work
✅ **Reasoning Transparency**: Full visibility into agent decision-making process
✅ **Adaptive Behavior**: Agents learn from experience and adjust strategies
✅ **State Management**: Agents maintain context across complex workflows

Built for agentic AI buildathon - demonstrating autonomous multi-agent healthcare claims processing with full transparency and collaboration.