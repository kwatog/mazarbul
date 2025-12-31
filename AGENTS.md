# Ebrose Development Setup

## Virtual Environment Setup

### Create Virtual Environment
```bash
cd backend
python3 -m venv venv
```

### Activate Virtual Environment
```bash
# From project root
source backend/venv/bin/activate
```

### Install Backend Dependencies
```bash
cd backend
pip install -r requirements.txt
```

## Running the Application

### Backend (FastAPI)
```bash
# Activate venv first
source backend/venv/bin/activate
cd backend
python3 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Database Reset and Seed
```bash
cd backend
python3 reset_and_seed.py
```

### Running Tests
```bash
# Activate venv first
source backend/venv/bin/activate
cd backend
python3 -m pytest tests/ -v
```

### Running Specific Test Suites
```bash
# Access control tests
python3 -m pytest tests/test_access_control.py tests/test_owner_group_access.py tests/test_business_case_hybrid_access.py -v

# Budget items CRUD tests
python3 -m pytest tests/test_budget_items.py -v

# Authentication tests
python3 -m pytest tests/test_auth.py -v
```

### Frontend (Nuxt 4)
```bash
cd frontend
npm install
npm run dev
```

### Frontend E2E Tests
```bash
# Option 1: Using Docker Compose (recommended)
cd /Users/mmmiciano/ISEngineering/ebrose
docker compose -f docker-compose.playwright.yml up --build

# Option 2: Using Docker directly (run all test files)
cd /Users/mmmiciano/ISEngineering/ebrose

# Build and run tests with a single command (Docker)
docker run --rm \
  -e CI=true \
  -e PLAYWRIGHT_BASE_URL=http://host.docker.internal:3000 \
  -v $(pwd)/frontend/tests/screenshots:/app/tests/screenshots \
  -v $(pwd)/frontend:/app \
  -w /app \
  mcr.microsoft.com/playwright:v1.55.0-jammy \
  npx playwright test tests/e2e/

# Or with Podman
podman run --rm \
  -e CI=true \
  -e PLAYWRIGHT_BASE_URL=http://host.docker.internal:3000 \
  -v $(pwd)/frontend/tests/screenshots:/app/tests/screenshots:z \
  -v $(pwd)/frontend:/app \
  -w /app \
  mcr.microsoft.com/playwright:v1.55.0-jammy \
  npx playwright test tests/e2e/

# View test report
open PLAYWRIGHT_TEST_REPORT.html
```

**Note:** E2E tests require Docker/Podman with Playwright browser support. Start the backend and frontend first, or use the full docker-compose setup.

## Authentication
- Default Admin: `admin` / password set via `ADMIN_PASSWORD` env var (required in production)
- JWT tokens with HttpOnly cookies
- Roles: Admin, Manager, User, Viewer

## Environment Variables

### Required for Production
```bash
SECRET_KEY=<your-secret-key>              # Required in production
ADMIN_PASSWORD=<admin-password>           # Required for initial admin user
ENVIRONMENT=production                     # Required for SECRET_KEY enforcement
```

### Optional
```bash
ALLOWED_ORIGINS=http://localhost:3000     # CORS origins (comma-separated)
ACCESS_TOKEN_EXPIRE_MINUTES=15            # Token expiration
DATABASE_URL=postgresql://...             # Use external DB (default: SQLite)
```

## API Documentation
- Backend API: http://127.0.0.1:8000/docs
- Health Check: http://127.0.0.1:8000/health

## 🎯 Completed Features

### ✅ Core Backend (100% Complete)
- **All 14 Data Models** with audit tracking (created_by, updated_by, timestamps)
- **JWT Authentication** with role-based access control (Admin, Manager, User, Viewer)
- **14 API Routers** including auth, users, groups, record access, audit logs
- **Comprehensive Access Control** with record-level permissions and group support
- **Automatic Audit Logging** for all CRUD operations
- **SQLite Database** with foreign key constraints
- **Owner-Group Access Scoping** - List/read endpoints filter by owner_group_id
- **Hybrid BusinessCase Access** - Creator + line-item based + explicit grants
- **Decimal Money Handling** - All currency fields use Numeric(10,2) with 2dp rounding

### ✅ Frontend Implementation (100% Complete)
- **Login System** with JWT token management
- **Dashboard** with backend health monitoring
- **Purchase Orders** with access sharing functionality
- **Admin Panel** with dropdown navigation (Manager/Admin only)
- **User Groups Management** (`/admin/groups`)
  - Create/edit/delete groups
  - Add/remove group members
  - Real-time membership management
- **Audit Log Viewer** (`/admin/audit`)
  - Filterable audit trail
  - JSON diff viewing for changes
  - User and date filtering
- **Record Access Sharing** (via Share button on records)
  - Grant access to individual users or groups
  - Set access levels (Read/Write/Full)
  - Temporary access with expiration dates
  - View and revoke existing permissions

### ✅ Security & Compliance Features
- **Complete Audit Trail** - Every change tracked with user, timestamp, old/new values
- **Role-Based Permissions** - 4-tier access control system
- **Record-Level Security** - Creators can grant specific access to their records
- **Group-Based Access** - Organize permissions through user groups
- **Access Inheritance** - Child records inherit parent permissions
- **Route Protection** - Frontend pages protected by role requirements

## 📱 User Interface Features

### For All Users:
- **Dashboard** - System overview and health monitoring
- **Purchase Orders** - View POs with role-based access
- **Profile Management** - View user info and logout

### For Manager/Admin Users:
- **User Groups** - Complete group management interface
- **Audit Logs** - System-wide change tracking and filtering
- **Access Management** - Grant/revoke access to any record

### For Record Creators:
- **Share Records** - Grant access to specific users/groups on created records
- **Access Control** - Manage who can view/edit their data

## 🚀 Ready for Production

The system implements **100% of the updated requirements**:
- ✅ All records traced to creating/updating user
- ✅ User groups functionality with full UI
- ✅ Record-level access control with creator permissions
- ✅ Comprehensive audit trail for compliance
- ✅ Role-based security with inheritance rules
- ✅ Owner-group access scoping for all entities
- ✅ Hybrid BusinessCase visibility via line items

### Setup Required:
1. **Configure environment variables** for production secrets (SECRET_KEY required)
2. **Set ADMIN_PASSWORD** for initial admin user creation

The codebase is **enterprise-ready** with comprehensive security, audit compliance, and user-friendly management interfaces.

---

# Access Control Architecture

## Owner-Group Access Scoping

All list/read endpoints filter records by owner_group_id membership for non-admin users:
- User must be member of the record's owner_group_id, OR
- User created the record, OR
- User has explicit RecordAccess grant

```python
# Example from budget_items.py list endpoint
if current_user.role not in ["Admin", "Manager"]:
    accessible_ids_query = db.query(BudgetItem.id).filter(
        (BudgetItem.owner_group_id.in_(group_ids)) |
        (BudgetItem.created_by == current_user.id)
    )
```

## Hybrid BusinessCase Access

Business cases use a 3-path access model (in priority order):

1. **Creator Access**: Creator has Read always, Write for Draft status only
2. **Line-Item Based Access (Primary)**: Access via budget items linked through line items
3. **Explicit RecordAccess (Override)**: Direct grants from admins/managers

## Owner Group Inheritance

Child records inherit owner_group_id from parent chain:
- LineItem → WBS → Asset → PO → GR & Allocation
- Client-provided owner_group_id is ignored for child records

---

# Deployment Instructions

## Local Development
The application can be run locally using FastAPI and Nuxt development servers or Docker Compose:

```bash
# Using Docker Compose (recommended)
docker-compose up --build

# Or manually
# Backend: cd backend && uvicorn app.main:app --reload
# Frontend: cd frontend && npm run dev
```

## Kubernetes Deployment

### Prerequisites
- Kubernetes cluster with Helm installed
- Docker registry access
- kubectl configured for your cluster

### Quick Start
```bash
# Build and push images
docker build -t your-registry/ebrose/backend:latest ./backend
docker build -t your-registry/ebrose/frontend:latest ./frontend
docker push your-registry/ebrose/backend:latest
docker push your-registry/ebrose/frontend:latest

# Deploy to development
./k8s/development-deploy.sh

# Or deploy manually with Helm
helm install ebrose ./helm/ebrose \
  --namespace ebrose-development \
  --create-namespace \
  -f ./helm/ebrose/values-development.yaml
```

### Environment-Specific Deployments

#### Development
```bash
helm upgrade --install ebrose-dev ./helm/ebrose \
  --namespace ebrose-development \
  --create-namespace \
  -f ./helm/ebrose/values-development.yaml
```

#### Staging
```bash
helm upgrade --install ebrose-staging ./helm/ebrose \
  --namespace ebrose-staging \
  --create-namespace \
  -f ./helm/ebrose/values-staging.yaml \
  --set backend.image.tag=staging-v1.0.0 \
  --set frontend.image.tag=staging-v1.0.0
```

#### Production
```bash
helm upgrade --install ebrose-prod ./helm/ebrose \
  --namespace ebrose-production \
  --create-namespace \
  -f ./helm/ebrose/values-production.yaml \
  --set backend.image.tag=prod-v1.0.0 \
  --set frontend.image.tag=prod-v1.0.0
```

### Independent Component Deployment
```bash
# Deploy only backend
helm upgrade --install ebrose ./helm/ebrose \
  --set backend.enabled=true \
  --set frontend.enabled=false

# Deploy only frontend
helm upgrade --install ebrose ./helm/ebrose \
  --set backend.enabled=false \
  --set frontend.enabled=true
```

## CI/CD with Jenkins

The project includes a complete Jenkins pipeline (`Jenkinsfile`) that supports:

- **Multi-environment deployments** (development, staging, production)
- **Independent component deployment** (backend and/or frontend)
- **Zero-downtime deployments** with health checks
- **Automated testing** and smoke tests
- **Rollback capabilities**

### Jenkins Setup
1. Configure Jenkins with required plugins:
   - Docker Pipeline
   - Kubernetes CLI
   - Helm
2. Set up credentials:
   - `docker-registry-creds`: Docker registry credentials
   - `kubeconfig`: Kubernetes cluster configuration
3. Create pipeline job using the provided Jenkinsfile

### Pipeline Parameters
- `DEPLOYMENT_TARGET`: Choose environment (development/staging/production)
- `DEPLOY_BACKEND`: Enable/disable backend deployment
- `DEPLOY_FRONTEND`: Enable/disable frontend deployment
- `SKIP_TESTS`: Skip test execution for faster deployments

## Configuration Management

### Helm Values Override
Configuration is managed through Helm values files:
- `values.yaml`: Default values
- `values-development.yaml`: Development overrides
- `values-staging.yaml`: Staging overrides  
- `values-production.yaml`: Production overrides

### Runtime Configuration Changes
```bash
# Update configuration without full rebuild
helm upgrade ebrose ./helm/ebrose \
  --reuse-values \
  --set backend.env.SECRET_KEY=new-secret-key

# Scale replicas
helm upgrade ebrose ./helm/ebrose \
  --reuse-values \
  --set backend.replicaCount=5 \
  --set frontend.replicaCount=3
```

## Monitoring and Health Checks

### Health Endpoints
- Backend: `http://backend:8000/health`
- Frontend: `http://frontend:3000/health`

### Kubernetes Health Checks
Both components include:
- Liveness probes
- Readiness probes  
- Startup probes
- Resource limits and requests

### Scaling
```bash
# Manual scaling
kubectl scale deployment ebrose-backend --replicas=5 -n ebrose-production

# Enable auto-scaling (HPA)
helm upgrade ebrose ./helm/ebrose \
  --set backend.autoscaling.enabled=true \
  --set backend.autoscaling.minReplicas=2 \
  --set backend.autoscaling.maxReplicas=10
```

## Production Considerations

- **Security**: Use proper secrets management (Kubernetes Secrets, HashiCorp Vault)
- **Database**: Configure external database for production (PostgreSQL recommended)
- **Persistence**: Use appropriate storage classes for data persistence
- **SSL/TLS**: Configure cert-manager for automatic certificate management
- **Monitoring**: Integrate with Prometheus/Grafana for observability
- **Logging**: Use centralized logging (ELK stack, Fluentd)
- **Backup**: Implement automated database and configuration backups
