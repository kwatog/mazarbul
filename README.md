# Mazarbul
## Procurement Tracking System

Mazarbul is a comprehensive procurement tracking system built with FastAPI and Nuxt 4, featuring enterprise-grade audit logging, role-based access control, and Kubernetes deployment capabilities.

## Features

### 🔐 Authentication & Authorization
- JWT-based authentication with HTTP-only cookies
- Role-based access control (Admin, Manager, User, Viewer)
- Record-level access permissions
- User groups for simplified permission management

### 📊 Data Management
- Complete procurement workflow tracking
- Purchase orders, business cases, and asset management
- Work breakdown structure (WBS) support
- Goods receipt and allocation tracking

### 🔍 Audit & Compliance
- Comprehensive audit trail for all changes
- User activity tracking with timestamps
- JSON diff viewing for change analysis
- Filterable audit log viewer

### 👥 User Management
- User groups with role inheritance
- Record sharing with granular permissions
- Access control with expiration dates
- Admin interface for user management

## Architecture

- **Backend**: FastAPI with SQLAlchemy ORM
- **Frontend**: Nuxt 4 with Vue 3 and TypeScript
- **Database**: SQLite (configurable for PostgreSQL)
- **Authentication**: JWT tokens with bcrypt password hashing
- **Deployment**: Kubernetes with Helm charts

## Quick Start

### Using Docker Compose (Recommended)

```bash
git clone https://github.com/kwatog/mazarbul.git
cd mazarbul
docker-compose up --build
```

Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Manual Setup

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Kubernetes Deployment

### Prerequisites
- Kubernetes cluster
- Helm 3.x
- Docker registry access

### Quick Deploy
```bash
# Build and push images
docker build -t your-registry/mazarbul/backend:latest ./backend
docker build -t your-registry/mazarbul/frontend:latest ./frontend
docker push your-registry/mazarbul/backend:latest
docker push your-registry/mazarbul/frontend:latest

# Deploy to development
./k8s/development-deploy.sh
```

### Environment-Specific Deployments

#### Development
```bash
helm install mazarbul-dev ./helm/mazarbul \
  --namespace mazarbul-development \
  --create-namespace \
  -f ./helm/mazarbul/values-development.yaml
```

#### Staging
```bash
helm install mazarbul-staging ./helm/mazarbul \
  --namespace mazarbul-staging \
  --create-namespace \
  -f ./helm/mazarbul/values-staging.yaml
```

#### Production
```bash
helm install mazarbul-prod ./helm/mazarbul \
  --namespace mazarbul-production \
  --create-namespace \
  -f ./helm/mazarbul/values-production.yaml
```

### Independent Component Deployment
```bash
# Deploy only backend
helm install mazarbul ./helm/mazarbul \
  --set backend.enabled=true \
  --set frontend.enabled=false

# Deploy only frontend
helm install mazarbul ./helm/mazarbul \
  --set backend.enabled=false \
  --set frontend.enabled=true
```

## CI/CD

The project includes a Jenkins pipeline (`Jenkinsfile`) supporting:

- Multi-environment deployments
- Independent backend/frontend deployment
- Automated testing and health checks
- Zero-downtime deployments
- Rollback capabilities

### Jenkins Parameters
- `DEPLOYMENT_TARGET`: Environment (development/staging/production)
- `DEPLOY_BACKEND`: Enable/disable backend deployment
- `DEPLOY_FRONTEND`: Enable/disable frontend deployment
- `SKIP_TESTS`: Skip test execution

## Configuration

### Environment Variables

#### Backend
- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: JWT signing secret
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time

#### Frontend
- `NUXT_PUBLIC_API_BASE`: Backend API URL

### Helm Configuration

Configuration is managed through Helm values files:
- `values.yaml`: Default configuration
- `values-development.yaml`: Development overrides
- `values-staging.yaml`: Staging overrides
- `values-production.yaml`: Production overrides

## API Documentation

Once the backend is running, visit:
- OpenAPI Documentation: http://localhost:8000/docs
- ReDoc Documentation: http://localhost:8000/redoc

## Default Credentials

**Note**: For production deployment, ensure you create proper admin credentials and configure secure authentication.

## Database Schema

The system includes 12 main entities:
- Users and UserGroups
- PurchaseOrder, BusinessCase
- Asset, WBS, Resource
- GoodsReceipt, Allocation
- RecordAccess, AuditLog, Alert

All entities include comprehensive audit tracking with created/updated timestamps and user attribution.

## Security Features

- Password hashing with bcrypt
- JWT token-based authentication
- Role-based access control with inheritance
- Record-level permissions
- Comprehensive audit logging
- CORS protection
- Input validation with Pydantic

## Monitoring & Health Checks

### Health Endpoints
- Backend: `/health`
- Frontend: `/health` (when implemented)

### Kubernetes Features
- Liveness and readiness probes
- Horizontal Pod Autoscaling (HPA)
- Resource limits and requests
- Persistent volume claims for data

## Scaling

```bash
# Manual scaling
kubectl scale deployment mazarbul-backend --replicas=5

# Auto-scaling
helm upgrade mazarbul ./helm/mazarbul \
  --set backend.autoscaling.enabled=true \
  --set backend.autoscaling.minReplicas=2 \
  --set backend.autoscaling.maxReplicas=10
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions, please open an issue in the GitHub repository.