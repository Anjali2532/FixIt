# FixIt development setup

## Completed on October 31, 2026

### Project foundation — SIGNUP.ENV

1. Created separate `client/` and `server/` folders.
2. Added React/Vite, a Python virtual environment, package lists and Git exclusions.
3. Connected the React starter page to Flask through the Vite API proxy.
4. Checked the desktop and mobile layouts, unavailable-service message and retry button.

This establishes a working frontend-to-backend connection before account and report features are added.

### User database — SIGNUP.DB

1. Created the SQLAlchemy user model with names, normalized unique emails, password hashes, roles, active status and login-control fields.
2. Generated a Flask-Migrate migration for the users table.
3. Applied the migration to a separate local PostgreSQL development database using a non-superuser account.
4. Verified database connectivity, migration rollback and migration reapplication.
5. Ran the test suite against a separate PostgreSQL test database.

The database foundation gives future signup and login features consistent account records and database constraints.

### Password helpers — SECURITY.HASH

1. Added shared Werkzeug scrypt hashing and verification helpers.
2. Checked that identical passwords receive different salted hashes.
3. Tested correct and incorrect passwords, invalid inputs and malformed hashes.

These helpers now handle passwords for signup, login and administrator creation without storing passwords as plain text.

### Phase 1 — accounts and access

1. Added signup and login screens with validation and live password rules.
2. Connected them to Flask registration and authentication endpoints.
3. Added revocable database-backed sessions, refresh persistence and logout.
4. Added 60-minute inactivity expiry, five-attempt account lockout and per-IP rate limits.
5. Added CSRF protection, private-response cache headers and server-side role checks.
6. Added separate resident and administrator dashboards and a local administrator creation command.

The authentication cookie contains an opaque login identifier signed by Flask. Its hash, account ID and expiry are stored in `auth_sessions`. Logout removes the server record, so an old cookie cannot log in again. Roles and account activity are checked against the database on every authenticated request. This uses Flask's cookie signing and SQLAlchemy rather than the originally considered Flask-Session extension.

## Account-phase verification

- Backend tests with in-memory SQLite: **45 passed**.
- Backend tests with local PostgreSQL: **45 passed**.
- Initial users migration upgrade, downgrade and upgrade: **passed**.
- Authentication-session migration applied to PostgreSQL: **passed**.
- React production build: **passed**.
- Eight end-to-end account checks: **passed**, including signup validation, refresh persistence, role restrictions, logout cookie revocation, incorrect credentials, duplicate signup and administrator access.
- Desktop and mobile account layouts: **passed**.

These checks cover Phase 1. They do not establish that report submission or report management is implemented.

## Screenshots

- [Signup form](evidence/phase1-signup.png)
- [Login error handling](evidence/phase1-login.png)
- [Resident dashboard](evidence/phase1-resident-dashboard.png)
- [Administrator dashboard](evidence/phase1-admin-dashboard.png)
- [Mobile signup form](evidence/phase1-signup-mobile.png)
- [Mobile administrator dashboard](evidence/phase1-admin-mobile.png)
- [Backend test output](evidence/phase1-backend-tests.txt)
- [PostgreSQL test output](evidence/phase1-postgres-tests.txt)
- [Browser check results](evidence/phase1-browser-checks.json)

The earlier `starter-*.png` and `backend-checks.png` images document the initial foundation; they predate the account screens.

## Start the existing local setup

Use the project in `Documents/Workspace/FixIt`. The environment and packages are already installed on this computer. Do not replace the existing `.env` when restarting.

Replace `/path/to/FixIt` with the location where you saved the project.

Backend terminal:

```bash
cd /path/to/FixIt
source .venv/bin/activate
flask --app server.app db-check
flask --app server.app db upgrade
flask --app server.app run --port 5001
```

Frontend terminal:

```bash
cd /path/to/FixIt/client
npm run dev
```

Visit **http://127.0.0.1:5173/**. Keep both terminals running; use `Control+C` to stop them. If a port is busy, stop the previous server first. If `db-check` fails, check that PostgreSQL is running and that `.env` points to it. The temporary database used on this computer is described below.

## Install and run

Prerequisites: Python, PostgreSQL, and Node.js 20.19+ or 22.12+. This session was verified with Python 3.14, Node 26 and PostgreSQL 16.

1. Create and activate a virtual environment at the project root.
2. Run `pip install -r requirements-dev.txt`. `requirements-lock.txt` records the exact Python versions used during verification.
3. Create a PostgreSQL application login and databases named `fixit_db` and `fixit_test`. Give the login ownership of these development databases, without superuser privileges. Use separate migration and runtime permissions for a production deployment.
4. Copy `.env.example` to `.env`, fill in the local connection URL and replace `SECRET_KEY` with a long random value. Generate one with `python -c "import secrets; print(secrets.token_hex(32))"`. Never upload `.env`, `.venv` or `.local/`.
5. Run `flask --app server.app db upgrade` and `flask --app server.app db-check`.
6. Start Flask with `flask --app server.app run --port 5001`.
7. In `client/`, run `npm ci` followed by `npm run dev`.
8. Open `http://127.0.0.1:5173`.

The isolated database used for this verification runs on local port **55432**, with data under `/tmp/fixit-oct31/postgres`. It is a local test instance, not a hosted or permanent database. The ignored `.env` currently points to it. For ongoing work, configure your normal PostgreSQL instance and update `.env`.

## Administrator accounts

Public signup cannot create administrators. Run this command from the project root and enter the details when prompted:

```bash
flask --app server.app create-admin
```

A local administrator was created for this implementation session. Its generated credentials are in `.local/admin-login.txt`, excluded from Git. Use those only with this local development database.

To deactivate an account for testing:

```bash
flask --app server.app set-account-active --email resident@example.test --inactive
```

Use `--active` to restore access. Deactivated accounts cannot log in, and existing sessions are rejected on their next request.

## Session and deployment settings

Local development uses HttpOnly, SameSite=Lax cookies over HTTP. Set `FIXIT_ENV=production` behind HTTPS to enable the Secure cookie flag. Keep the frontend and API on one origin. Configure `RATELIMIT_STORAGE_URI` to a shared store such as Redis before running multiple server workers; the default in-memory limiter is for one local process.

## Repeat the checks

At the project root with the virtual environment active:

```bash
python -m pytest -q
```

Tests use in-memory SQLite by default. To test PostgreSQL, create an empty local `fixit_test` database and set `FIXIT_TEST_DATABASE_URL` in the process environment before running pytest. The tests create and remove their tables. They refuse non-local PostgreSQL databases or a database name other than `fixit_test`.

```bash
cd client
npm run build
```

## Next work

- Add photo uploads and report assignment, including the Assigned status.
- Align categories and the remaining report rules with the use case narratives.
- Complete the remaining administrator features and deploy the app.

## Work Log evidence

The new code and screenshots are saved locally. Upload them before using new GitHub file links as evidence. Actual personal work hours must be recorded separately; test results and commit timestamps do not measure time spent.


## Reporting workflow added October 31, 2026

Residents can create reports at `/reports/new`, list their own reports at `/my-reports`, and open `/reports/:id` to see details and progress history. The form validates title, description, location, category and priority. Search and filters run on the backend, with 20 reports per page.

Administrators use `/admin/dashboard` to review all reports. A report detail page includes a status selector and a required progress note. Each saved update is kept in history and is visible to the report owner. The server checks ownership and administrator permissions independently of the UI. Reports start as Reported; administrators can move them to In Progress or Resolved, or reopen them as Reported.

Run `flask --app server.app db upgrade` before starting the updated backend. Migration `db260a31f793` adds the issues and issue_updates tables without changing existing accounts.

Verification: 57 backend tests passed on SQLite and on the dedicated local PostgreSQL test database. Six browser checks passed for submission, refresh persistence, search/filtering, administrator updates, resident history and mobile layout. The frontend build passed. Screenshots and browser results are in `docs/evidence/report-*.png`, `my-reports.png`, `admin-report-update.png` and `report-browser-checks.json`. Screenshots use a temporary test account and report, which were removed after verification.

Photo uploads and assignment remain future work. This update does not add hours to the project tracker or publish the local source files to GitHub.
