# 🏥 Flogenix - Enterprise Agentic AI Healthcare Claims Platform

An **enterprise-grade, agentic AI-powered** healthcare claims processing system that uses multi-agent collaboration to autonomously process medical insurance claims, detect fraud, handle exceptions with learning capabilities, and provide comprehensive administrative controls.

## 🚀 Quick Start

### Windows Users
```bash
# Run the enterprise startup script
start_enterprise.bat
```

### Linux/Mac Users
```bash
# Make script executable and run
chmod +x start_enterprise.sh
./start_enterprise.sh
```

The platform will automatically:
- Set up Python virtual environment
- Install all dependencies
- Start enterprise backend server (port 8000)
- Start React frontend (port 5173)
- Open browser to http://localhost:5173

**Default Login**: admin / admin123 (SUPER_ADMIN role)

## 🎯 Enterprise Features

### 🤖 Multi-Agent AI System
- **Intake Agent**: Validates claim data and extracts entities
- **Eligibility Agent**: Verifies insurance coverage and provider credentials  
- **Clinical Review Agent**: Validates medical codes and treatment necessity
- **Fraud Detection Agent**: Advanced pattern analysis and risk scoring
- **Adjudication Agent**: Final decision synthesis with explainable reasoning

### � Enterprise Security
- **JWT Authentication**: Secure token-based authentication
- **Two-Factor Authentication**: TOTP-based 2FA with QR codes
- **Role-Based Access Control**: USER, PROCESSOR, ADMIN, SUPER_ADMIN roles
- **Comprehensive Audit Trails**: Full activity logging and monitoring
- **Data Protection**: Input validation, sanitization, and encryption

### 👥 User Management & Roles
- **USER**: Submit claims, view personal dashboard
- **PROCESSOR**: Process claims, review fraud alerts, access queue
- **ADMIN**: User management, system configuration, analytics
- **SUPER_ADMIN**: Full system control, security settings, global configuration

### 📊 Advanced Analytics
- **Real-time Dashboards**: Live system metrics and performance indicators
- **Claims Analytics**: Processing volumes, approval rates, trends
- **Fraud Insights**: Risk patterns and prevention effectiveness
- **Agent Performance**: AI processing metrics and success rates
- **Business Intelligence**: Revenue analysis and operational reports

### � Real-time Notifications
- **System Alerts**: Service status, maintenance, critical events
- **Fraud Warnings**: High-risk claims requiring immediate attention
- **Processing Updates**: Real-time claim status changes
- **Performance Monitoring**: SLA breaches and system anomalies

## 🏗️ System Architecture

### Backend (FastAPI + Python)
```
backend/
├── main_enterprise.py          # Enterprise FastAPI application
├── app/
│   ├── core/
│   │   ├── config.py          # Enterprise configuration management
│   │   ├── models.py          # SQLAlchemy database models
│   │   ├── security.py        # Authentication & authorization
│   │   └── database.py        # Database connection & management
│   ├── api/
│   │   └── claims.py          # Claims processing endpoints
│   └── services/
│       ├── multi_agent_processor.py    # AI agent orchestration
│       ├── fraud_detection.py          # Advanced fraud detection
│       ├── ai_processing.py            # Core AI processing logic
│       └── validation.py               # Data validation services
└── requirements_enterprise.txt         # Production dependencies
```

### Frontend (React + TypeScript)
```
frontend/
├── src/
│   ├── pages/
│   │   ├── EnterpriseIndex.tsx          # Enterprise dashboard
│   │   ├── EnterpriseAdminPortal.tsx    # Admin management portal
│   │   ├── EnterpriseSubmitClaim.tsx    # Advanced claim submission
│   │   └── EnterpriseViewClaims.tsx     # Claims management interface
│   ├── components/
│   │   ├── ui/                          # shadcn/ui components
│   │   └── NotificationSystem.tsx       # Real-time notifications
│   ├── hooks/
│   │   └── useAuth.tsx                  # Authentication context
│   └── lib/
│       ├── api.ts                       # Enterprise API client
│       └── utils.ts                     # Utility functions
├── package.json                         # Frontend dependencies
└── tailwind.config.ts                   # Tailwind CSS configuration
```

## 🤖 Agentic AI Capabilities

### Autonomous Decision Making
- **ReAct Reasoning**: Reason → Act → Observe pattern with full transparency
- **Tool Integration**: Agents autonomously invoke APIs, databases, and external services
- **Multi-Agent Collaboration**: Agents communicate, share state, and coordinate workflows
- **Adaptive Learning**: Exception handling that learns from past resolutions

### Enterprise AI Features
- **Confidence Scoring**: Configurable thresholds for auto-approval
- **Fraud Prevention**: Real-time pattern analysis and risk assessment
- **Clinical Validation**: Medical necessity and coding compliance checks
- **Regulatory Compliance**: HIPAA and healthcare regulation adherence
- **Explainable AI**: Natural language explanations for all decisions

## 📊 Demo Scenarios

### 1. **Standard Processing**: Multi-Agent Collaboration
- Submit routine medical claim
- Watch agents process in parallel: Intake → Eligibility & Clinical & Fraud → Adjudication
- View real-time agent reasoning and tool usage
- **Admin Portal**: Monitor processing queue and agent performance

### 2. **Fraud Detection**: Advanced Risk Analysis
- Submit suspicious duplicate claim
- Fraud Detection Agent analyzes patterns and provider history
- System automatically flags high-risk claims
- **Admin Portal**: Review fraud alerts and investigation tools

### 3. **Exception Handling**: Intelligent Problem Resolution
- Submit claim with missing documentation
- Exception Handler escalates to human review
- System learns resolution patterns for future automation
- **Admin Portal**: Manage exception workflows and resolutions

### 4. **Enterprise Administration**: System Management
- User role management and permission assignment
- System configuration and security settings
- Performance monitoring and analytics dashboards
- **Admin Portal**: Complete enterprise control center

## 🌐 Service URLs

- **Frontend Dashboard**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Interactive API**: http://localhost:8000/redoc

## 🔐 Default Credentials

| Role | Username | Password | Capabilities |
|------|----------|----------|-------------|
| SUPER_ADMIN | admin | admin123 | Full system access |
| ADMIN | admin_user | admin123 | Administrative controls |
| PROCESSOR | processor | processor123 | Claims processing |
| USER | user | user123 | Basic claim submission |

## 📚 Documentation

- **[Enterprise Features Guide](./ENTERPRISE_FEATURES.md)** - Complete feature documentation
- **[Integration Guide](./INTEGRATION_GUIDE.md)** - API integration instructions
- **[Demo Guide](./DEMO_GUIDE.md)** - Step-by-step demo scenarios
- **[Buildathon Summary](./BUILDATHON_SUMMARY.md)** - Project overview and achievements

## 🛠️ Technology Stack

### Backend Technologies
- **FastAPI**: High-performance async Python web framework
- **SQLAlchemy**: Advanced ORM with enterprise database support
- **LangChain/LangGraph**: Multi-agent AI orchestration
- **OpenAI GPT-4**: Advanced language model for claim processing
- **Celery**: Distributed task queue for background processing
- **Redis**: In-memory data structure store for caching

### Frontend Technologies
- **React 18**: Modern React with hooks and concurrent features
- **TypeScript**: Type-safe JavaScript for enterprise development
- **shadcn/ui**: High-quality accessible UI components
- **Tailwind CSS**: Utility-first CSS framework
- **React Router**: Client-side routing and navigation
- **Vite**: Fast build tool and development server

### Enterprise Integrations
- **JWT Authentication**: Industry-standard token authentication
- **TOTP 2FA**: Time-based one-time password two-factor auth
- **Role-Based Access**: Granular permission system
- **Audit Logging**: Comprehensive activity tracking
- **Real-time Notifications**: WebSocket-based live updates

## 🏆 Why This is True "Agentic AI"

✅ **Autonomous Agents**: Each agent makes independent decisions about tools and actions
✅ **Goal-Oriented Processing**: Agents work toward specific healthcare objectives
✅ **Intelligent Tool Usage**: Context-aware selection and execution of appropriate tools
✅ **Multi-Agent Collaboration**: Specialized agents communicate and coordinate workflows
✅ **Reasoning Transparency**: Complete visibility into agent decision-making processes
✅ **Adaptive Learning**: System learns from experience and improves over time
✅ **Enterprise State Management**: Agents maintain context across complex business workflows
✅ **Healthcare Domain Expertise**: Specialized knowledge for medical claims processing

## 🚀 Enterprise Deployment

The platform supports multiple deployment options:
- **Development**: Local SQLite with hot reload
- **Production**: PostgreSQL with load balancing
- **Enterprise**: Multi-region with high availability
- **Cloud**: AWS, Azure, GCP compatible

---

**Built for Enterprise Healthcare** - A complete agentic AI solution for autonomous healthcare claims processing with enterprise security, comprehensive administration, and advanced analytics.

*Transform your healthcare claims processing with AI-powered automation.*