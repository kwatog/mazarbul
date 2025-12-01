# Mazarbul Code Review and Improvements

This document captures a focused review of `requirements-codex.md` and the current codebase, with concrete, high‑impact recommendations.

## Status Snapshot
- Resolved:
  - Record access revoke/update endpoints implemented (`DELETE` and `PUT`).
  - Secrets and token expiry read from environment variables.
  - CORS allowlist driven by `ALLOWED_ORIGINS` (no wildcard).
  - Admin bootstrap gated by env (no default hardcoded password).
  - Server now issues HttpOnly `access_token` cookie, and `/auth/refresh` + `/auth/logout` added.
  - Helm chart now contains Deployments/Services/Ingress/HPA/PVC/ServiceAccounts.
- Partial:
  - SQLAlchemy `session.get(...)` adopted in record-access router; other routers still use deprecated `query(...).get(...)`.
  - Frontend still expects token in JSON and stores JS-readable cookies; not fully aligned with HttpOnly cookie flow.
- Open:
  - No update endpoints (PUT/PATCH) for main entities; no UPDATE audit trail.
  - List endpoints lack department/grant-based filtering and pagination.
  - Timestamps stored as strings; DB constraints (Unique/Check) missing.
  - No centralized access helper, migrations, or test/lint setup.

## Biggest Gaps
- CRUD completeness [OPEN]: Routers mostly expose list/get/create/delete. Add update endpoints across all entities and audit logging for UPDATE.
- Auth token handling [PARTIAL]: Backend uses HttpOnly cookies; frontend still expects token JSON and sets JS cookies. Align client to cookie-based auth.

## Security
- Secrets [RESOLVED]: `SECRET_KEY` and `ACCESS_TOKEN_EXPIRE_MINUTES` read from env.
- CORS + credentials [RESOLVED]: Allowed origins from `ALLOWED_ORIGINS`; no wildcard with credentials.
- Token storage [PARTIAL]: Server sets HttpOnly cookie; frontend must switch to `credentials: 'include'` and stop reading tokens in JS.
- Default admin [RESOLVED]: Admin creation via env gating; no secret printing.

## Access Control
- Department access & inheritance [OPEN]: Implement dept scoping for `User` role and inheritance BC → WBS → Asset → PO → GR across reads/writes. List endpoints currently return all rows.
- Centralize checks [OPEN]: Provide a utility to compute effective access (role, creator, grants, department) to eliminate duplication.

## Audit Trail
- Update coverage [OPEN]: Decorator logs CREATE/DELETE; capture `old_values` and `new_values` for UPDATE, and call it from update endpoints.
- Request context [OPEN]: Capture `ip_address` and `user_agent` consistently via Request or middleware.
- Naming consistency [OPEN]: Ensure `record_type` and audit `table_name` names are consistent.

## Backend Engineering
- Datetimes [OPEN]: Store timestamps as `DateTime` (not strings); same for `expires_at`.
- Constraints [OPEN]:
  - `user_group_membership`: unique `(user_id, group_id)` via `UniqueConstraint`.
  - `record_access`: `CHECK (user_id IS NOT NULL OR group_id IS NOT NULL)`.
- Pagination/filtering [OPEN]: Add `limit`, `offset`, sorting, and basic filters to list endpoints.
- Migrations [OPEN]: Introduce Alembic for schema evolution instead of `Base.metadata.create_all`.
- SQLAlchemy API [PARTIAL]: Replace deprecated `query.get(id)` with `session.get(Model, id)` across routers.

## Frontend
- Auth flow [OPEN]: Centralize API calls with a composable/plugin that uses `credentials: 'include'`, handles 401 → `/auth/refresh` → retry, and removes per-component token headers.
- Role guards [OPEN]: Use route middleware for role‑gated pages (still enforce on backend).
- Health endpoint [OK]: `pages/health.vue` exists; optionally add a tiny server route returning JSON.
- UX coverage [OPEN]: Add PO detail with GRs and remaining calc, alerts page consuming `/alerts`, and inline editing for CRUD.

## DevOps/CI/CD
- Helm chart [RESOLVED]: Templates added for Deployments/Services/Ingress/HPA/PVC/ServiceAccounts.
- Config as env [RESOLVED]: Backend reads key env vars; frontend already supports `NUXT_*` API base.
- Jenkinsfile [INFO]: Pipeline assumes charts exist (now present). Keep validation steps to fail fast on misconfig.
- Artifacts [PARTIAL]: `mazarbul.db` exists locally but is not committed (ignored). Ensure DB files never enter VCS.

## Data Model
- Required fields [OPEN]: Enforce NOT NULL where implied (e.g., `po_number`, dates). Add indexes on `po_number`, `wbs_code`, `asset_code`.
- Money handling [OPEN]: Consider `Decimal` for amounts; validate currency codes.

## Testing and Quality
- Minimal tests [OPEN]: Auth (happy/negative), access control, audit create/update/delete, alerts edges.
- Lint/type checks [OPEN]: Add ruff/black/mypy for backend; ESLint/TypeScript strict for frontend. Integrate into CI as fast‑fail.

## Quick Wins (Updated)
- Align frontend auth with cookies: use `credentials: 'include'`, remove JS token storage, and add refresh-retry wrapper.
- Add `PUT /purchase-orders/{id}` with UPDATE audit as a reference; replicate to other entities.
- Add pagination (`limit`/`offset`) and default sorting to list endpoints.
- Replace remaining `query(...).get(...)` with `session.get(...)`.
- Add `UniqueConstraint` on group membership and `CHECK` on record_access.

## Suggested Next Steps
1. Frontend: switch to cookie-based auth and add a unified `$fetch` wrapper with refresh-on-401.
2. Backend: implement a sample update + audit (PurchaseOrder), then propagate.
3. Lists: add dept/grant-based scoping for User role and pagination.
4. Schema: add constraints and migrate timestamps to `DateTime` (introduce Alembic).
5. Replace deprecated SQLAlchemy calls across routers and add basic tests.
