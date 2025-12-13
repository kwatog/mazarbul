# Operations

## Local development

Backend:

- Create/activate venv, then run: `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`
- Swagger: `http://127.0.0.1:8000/docs`

Frontend:

- Install deps and run: `npm run dev`
- App: `http://localhost:3000`

## Testing (frontend)

- Unit tests: `npm run test:unit`
- E2E tests: `npm run test:e2e`

Note: Playwright requires browser binaries. If they are not present in your environment, run `npx playwright install`.

## Environment variables (backend)

- `DATABASE_URL` — SQLAlchemy connection string.
- `SECRET_KEY` — JWT signing key.
- `ACCESS_TOKEN_EXPIRE_MINUTES` — token lifetime.
- `ALLOWED_ORIGINS` — comma-separated CORS origins.

Optional admin bootstrap:

- `CREATE_ADMIN_USER=true`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `ADMIN_EMAIL`
- `ADMIN_FULL_NAME`
