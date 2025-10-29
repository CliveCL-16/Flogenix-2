# Flogenix Enterprise Claims Processing Platform

## 🚀 Project Overview

Flogenix is an enterprise-grade agentic AI-powered healthcare claims processing platform that combines cutting-edge artificial intelligence with robust backend architecture to automate and streamline insurance claim adjudication.

### ✨ Key Features

- **🤖 Multi-Agent AI System**: Specialized AI agents for intake, eligibility, clinical review, fraud detection, and final adjudication
- **🔐 Enterprise Security**: JWT authentication, role-based access control, 2FA support, and comprehensive audit trails  
- **⚡ Real-time Processing**: Async claim processing with Celery and Redis for scalable background operations
- **📊 Advanced Analytics**: Comprehensive dashboards with real-time metrics, charts, and insights
- **🛡️ Fraud Detection**: AI-powered fraud analysis with risk scoring and automated flagging
- **👥 Role-Based Access**: Separate interfaces for users, processors, and administrators
- **📱 Modern UI**: React-based frontend with TypeScript, shadcn/ui components, and responsive design
- **🔍 Audit Trail**: Complete logging and tracking of all agent decisions and processing steps

## 🏗️ Architecture

### Backend Stack
- **FastAPI**: High-performance Python web framework with automatic API documentation
- **SQLAlchemy**: ORM with support for PostgreSQL and SQLite databases
- **Celery + Redis**: Distributed task queue for async processing and caching
- **Pydantic**: Data validation and settings management
- **JWT Authentication**: Secure token-based authentication with refresh tokens

### Frontend Stack  
- **React 18**: Modern React with hooks and functional components
- **TypeScript**: Type-safe development with comprehensive type definitions
- **shadcn/ui**: Modern, accessible UI component library
- **Tailwind CSS**: Utility-first CSS framework for rapid styling
- **React Router**: Client-side routing for SPA navigation
- **React Query**: Server state management and caching

### AI/ML Components
- **Multi-Agent Architecture**: ReAct pattern implementation with specialized agents
- **OpenAI Integration**: GPT-4 powered decision making and reasoning
- **Tool-Calling Framework**: Dynamic tool execution for data retrieval and validation
- **Reasoning Transparency**: Complete audit trail of AI decision processes

## 📁 Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/                    # API endpoints
│   │   │   ├── claims.py           # Legacy claim endpoints  
│   │   │   └── enterprise_claims.py # Enterprise API endpoints
│   │   ├── models/                 # Database models
│   │   │   ├── __init__.py
│   │   │   └── models.py           # SQLAlchemy models
│   │   └── services/               # Business logic
│   │       ├── enhanced_multi_agent_processor.py # Multi-agent AI system
│   │       ├── security.py         # Authentication & authorization
│   │       ├── celery_tasks.py     # Background task definitions
│   │       └── ...
│   ├── config.py                   # Enterprise configuration management
│   ├── main.py                     # FastAPI application entry point
│   └── requirements.txt            # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/ui/          # Reusable UI components
│   │   ├── hooks/                  # React hooks (auth, etc.)
│   │   ├── lib/                    # Utilities and API client
│   │   │   ├── api.ts              # Enterprise API client
│   │   │   └── utils.ts            # Helper functions
│   │   └── pages/                  # Application pages
│   │       ├── EnterpriseIndex.tsx        # Enterprise dashboard
│   │       ├── EnterpriseSubmitClaim.tsx  # Enhanced claim submission
│   │       ├── EnterpriseViewClaims.tsx   # Claims management interface
│   │       └── EnterpriseClaimDetails.tsx # Detailed claim view with AI insights
│   ├── package.json                # Node.js dependencies
│   └── vite.config.ts              # Vite build configuration
├── data/                           # JSON data files
└── scripts/                        # Deployment and utility scripts
```

## 🤖 Multi-Agent AI System

### Agent Specializations

1. **Intake Agent** (`FileText` icon)
   - Initial claim validation and data extraction
   - Format verification and completeness checks
   - Patient demographics validation

2. **Eligibility Agent** (`User` icon)  
   - Insurance coverage verification
   - Policy status and benefits checking
   - Prior authorization requirements

3. **Clinical Review Agent** (`Brain` icon)
   - Medical necessity assessment
   - Diagnosis and procedure code validation
   - Clinical guidelines compliance

4. **Fraud Detection Agent** (`Shield` icon)
   - Pattern analysis and anomaly detection
   - Risk factor identification
   - Fraud score calculation

5. **Final Adjudication Agent** (`Award` icon)
   - Decision synthesis and recommendation
   - Confidence scoring and final determination
   - Reasoning documentation

### ReAct Pattern Implementation

Each agent follows the ReAct (Reasoning + Acting) pattern:
- **Thought**: Analysis and reasoning about the current step
- **Action**: Tool execution or data retrieval  
- **Observation**: Result analysis and next step determination
- **Repeat**: Continue until task completion

## 🔐 Security Features

### Authentication & Authorization
- JWT access and refresh tokens
- Role-based permissions (USER, PROCESSOR, ADMIN, SUPER_ADMIN)
- Two-factor authentication support
- Session management and token validation

### Data Protection
- Password hashing with bcrypt
- API endpoint protection with dependency injection
- Audit logging for all sensitive operations
- Request/response validation with Pydantic

### Access Control
- Role-based UI component rendering
- Protected routes and API endpoints
- Resource-level permissions
- Comprehensive audit trails

## 📊 Dashboard Features

### Real-time Metrics
- Total claims processed and pending
- Approval/denial rates and trends
- Average processing times
- Revenue tracking and analytics

### Interactive Charts
- Claims volume over time
- Status distribution pie charts
- Processing time trends
- Agent performance metrics

### Role-Based Views
- **Users**: Personal claim tracking and submission
- **Processors**: Claims queue management and review tools
- **Administrators**: System-wide analytics and user management

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+
- Redis server
- PostgreSQL (optional, SQLite included)

### Backend Setup
```bash
cd backend
python -m venv vev
source vev/bin/activate  # Windows: vev\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Frontend Setup  
```bash
cd frontend
npm install
npm run dev
```

### Environment Configuration
Create `.env` file in backend directory:
```env
# Database
DATABASE_URL=postgresql://user:pass@localhost/flogenix
# or for SQLite: DATABASE_URL=sqlite:///./flogenix.db

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Configuration  
OPENAI_API_KEY=your-openai-api-key

# Redis
REDIS_URL=redis://localhost:6379

# API Settings
API_V1_STR=/api
```

## 🔧 Enterprise Configuration

The platform uses a comprehensive configuration system in `config.py`:

### Database Settings
- PostgreSQL for production
- SQLite for development  
- Connection pooling and optimization

### Security Configuration
- JWT token settings
- Password policies
- Session management
- CORS configuration

### AI Configuration
- OpenAI API settings
- Model selection and parameters
- Agent behavior tuning
- Tool execution limits

### Processing Configuration
- Celery worker settings
- Redis caching configuration
- Background task priorities
- Performance monitoring

## 📈 API Endpoints

### Authentication
- `POST /auth/login` - User authentication
- `POST /auth/logout` - Session termination  
- `GET /auth/me` - Current user information
- `POST /auth/refresh` - Token refresh

### Claims Management
- `POST /api/claims/submit` - Submit new claim
- `GET /api/claims` - List claims with filtering
- `GET /api/claims/{id}` - Get claim details
- `POST /api/claims/{id}/process` - Trigger processing
- `GET /api/claims/{id}/agent-timeline` - Agent processing history

### Analytics & Reporting
- `GET /api/dashboard/metrics` - Real-time dashboard data
- `POST /api/claims/export` - Export claims data
- `GET /api/analytics/trends` - Trend analysis
- `GET /api/reports/performance` - Performance metrics

## 🧪 Testing

### Backend Testing
```bash
cd backend
pytest tests/
```

### Frontend Testing
```bash
cd frontend  
npm run test
```

### Integration Testing
```bash
# Start backend and frontend
npm run test:e2e
```

## 🚀 Deployment

### Production Setup
1. Configure environment variables
2. Set up PostgreSQL database
3. Deploy Redis instance
4. Configure Celery workers
5. Set up reverse proxy (nginx)
6. Enable HTTPS/SSL

### Docker Deployment
```bash
docker-compose up -d
```

### Monitoring
- Application metrics via FastAPI metrics
- Celery monitoring with Flower
- Database performance monitoring
- Frontend error tracking

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create feature branch
3. Implement changes with tests
4. Submit pull request
5. Code review and merge

### Code Standards
- Python: Black formatter, type hints
- TypeScript: ESLint, Prettier
- Commit messages: Conventional commits
- Documentation: Inline and README updates

## 📚 Documentation

### API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Component Documentation
- Storybook: `npm run storybook`
- Type definitions in TypeScript files

## 🛣️ Roadmap

### Phase 1: Core Platform ✅
- Multi-agent AI system
- Basic claim processing
- User authentication
- REST API development

### Phase 2: Enterprise Features ✅  
- Advanced analytics dashboard
- Role-based access control
- Fraud detection enhancement
- Real-time processing

### Phase 3: Advanced Features 🚧
- Machine learning model training
- Integration with external systems
- Mobile application
- Advanced reporting

### Phase 4: Scale & Optimize 📋
- Performance optimization
- Multi-tenant architecture
- Advanced monitoring
- Compliance certifications

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙋‍♂️ Support

For support and questions:
- GitHub Issues: Report bugs and feature requests
- Documentation: Comprehensive guides and API docs
- Community: Discussion forums and chat

---

**Flogenix** - Transforming healthcare claims processing with intelligent automation.