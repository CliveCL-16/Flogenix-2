# Frontend-Backend Integration Documentation

## Overview
The Flogenix application has been successfully integrated with a complete frontend-backend architecture. The system provides a comprehensive healthcare claims processing platform with both user and admin interfaces.

## Architecture

### Backend (FastAPI)
- **Location**: `/backend/`
- **Port**: 8000
- **Framework**: FastAPI with Python
- **API Base URL**: `http://localhost:8000/api`

### Frontend (React + TypeScript)
- **Location**: `/frontend/`
- **Port**: 5173 (Vite dev server)
- **Framework**: React with TypeScript, TailwindCSS, Shadcn/UI

## Key Features Implemented

### 🔐 Authentication System
- Role-based authentication (User/Admin)
- Protected routes based on user type
- Login/logout functionality

### 👥 User Portal (`/user`)
- Submit new claims
- View claim history with filtering
- Detailed claim information
- Real-time status updates

### 🔧 Admin Portal (`/admin`)
- Dashboard with real-time metrics
- Manage all claims in the system
- Process pending claims
- View fraud analysis and agent processing details

### 📊 Claims Management
- **Submit Claims**: Complete form with medical codes, patient info, insurance details
- **View Claims**: Searchable, filterable list with status badges
- **Claim Details**: Comprehensive view with tabs for overview, details, analysis, and processing timeline

## API Integration

### API Client (`/frontend/src/lib/api.ts`)
Complete TypeScript client for all backend endpoints:

#### Claims Endpoints
- `POST /api/claims/submit` - Submit new claim
- `GET /api/claims` - Get all claims (with optional status filter)
- `GET /api/claims/{id}` - Get claim details
- `POST /api/claims/{id}/process` - Process claim with AI
- `GET /api/claims/{id}/fraud-analysis` - Get fraud analysis
- `GET /api/claims/{id}/agent-timeline` - Get agent processing timeline
- `GET /api/claims/{id}/agent-reasoning` - Get detailed reasoning
- `GET /api/claims/{id}/tool-usage` - Get tool usage stats

#### Dashboard Endpoints
- `GET /api/dashboard/metrics` - Get dashboard metrics

#### Health Check
- `GET /api/health` - Backend health status

### Data Models
TypeScript interfaces matching backend Pydantic models:
- `ClaimSubmission` - Form data for new claims
- `Claim` - Full claim object with metadata
- `ClaimDetail` - Extended claim with related data
- `DashboardMetrics` - Admin dashboard statistics
- `FraudAnalysis` - Fraud detection results

## Routing Structure

```
/ - Landing page
/login - Authentication
/user - User portal dashboard
/user/submit-claim - Submit new claim form
/user/claims - View user's claims
/user/claim/:id - Detailed claim view
/admin - Admin portal dashboard  
/admin/claims - View all claims
/admin/claim/:id - Detailed claim view (with processing controls)
```

## Component Structure

### Pages
- `Index.tsx` - Landing page
- `Login.tsx` - Authentication
- `UserPortal.tsx` - User dashboard with recent claims
- `AdminPortal.tsx` - Admin dashboard with metrics
- `SubmitClaim.tsx` - Claim submission form
- `ViewClaims.tsx` - Claims list with filtering
- `ClaimDetails.tsx` - Detailed claim view with tabs

### UI Components
- Complete Shadcn/UI component library
- Custom styled components with TailwindCSS
- Responsive design for all screen sizes

## Backend Updates

### CORS Configuration
Updated to allow frontend development ports:
- `http://localhost:5173` (Vite default)
- `http://localhost:3000` (React default)
- `http://localhost:4173` (Vite preview)
- `http://localhost:8501` (Streamlit)

## Getting Started

### Prerequisites
- Python 3.8+ (backend)
- Node.js 16+ (frontend)

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
python main.py
```
Server runs on http://localhost:8000

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Application runs on http://localhost:5173

### Demo Flow

#### As a User:
1. Visit http://localhost:5173
2. Click "User Portal" and login
3. Submit a new claim with medical information
4. View submitted claims and their status
5. Click on any claim to see detailed information

#### As an Admin:
1. Visit http://localhost:5173
2. Click "Admin Portal" and login
3. View dashboard metrics and recent claims
4. Process pending claims with AI
5. View detailed fraud analysis and processing timeline

## Features Working

✅ **Complete Integration**: Frontend connects to backend APIs
✅ **Real-time Data**: All displays show live data from backend
✅ **Error Handling**: Comprehensive error handling with user feedback
✅ **Loading States**: Loading indicators during API calls
✅ **Responsive Design**: Works on all device sizes
✅ **Type Safety**: Full TypeScript integration
✅ **Form Validation**: Client-side validation with proper error messages
✅ **Status Management**: Real-time claim status updates
✅ **Search & Filter**: Advanced filtering capabilities
✅ **Role-based Access**: Different views for users vs admins

## Missing Features (Future Enhancements)

- Real-time notifications
- File upload for claim documents
- Bulk claim processing
- Advanced reporting and analytics
- Email notifications
- Claim appeals process
- Integration with external insurance APIs

## Technical Notes

### Error Handling
- All API calls wrapped in try-catch blocks
- Toast notifications for user feedback
- Graceful fallbacks for failed requests

### Performance
- React Query for efficient data fetching and caching
- Optimistic updates where appropriate
- Lazy loading for large data sets

### Security
- CORS properly configured
- Input validation on both client and server
- Protected routes with authentication checks

## Testing

The integration has been tested for:
- User login and claim submission flow
- Admin dashboard and claim processing
- API connectivity and error handling
- Responsive design across devices
- Form validation and error states

All major user flows are working correctly with the backend integration.