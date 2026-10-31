# FixIt

*Report It. Track It. Get It Fixed.*

FixIt is my individual software capstone project. I am building a web app where people can report problems in their community, such as a broken light, a plumbing issue or overflowing trash, and check what is happening with their report.

The idea is to keep reports in one place so they are easier for residents and administrators to follow.

## What I plan to build

Residents will be able to create an account, report an issue, attach a photo and track their own reports. Administrators will be able to review reports, search and filter them, assign someone to handle a problem and update its status.

Reports will move through four statuses: **Reported, Assigned, In Progress and Resolved**. A history of updates will help residents see the progress.

## Planned technology stack

- React, JavaScript, HTML and CSS for the frontend
- Python and Flask for the backend
- PostgreSQL for the database
- SQLAlchemy and Flask-Migrate for database access and schema changes
- pytest and the Flask test client for backend testing
- Git and GitHub for version control

I originally planned to use Node.js and Express for the backend. I have revised the plan to use Python and Flask and updated the project documents to match.

## Current progress

Phase 1 is complete:

- Residents can create an account, log in, refresh the page and log out.
- Signup validates names, emails and passwords and rejects duplicate emails.
- Passwords are hashed with Werkzeug scrypt.
- Login sessions are backed by PostgreSQL, expire after 60 inactive minutes and are revoked on logout.
- Residents and administrators have separate protected dashboards.
- CSRF protection, account lockout and login rate limits are enabled.
- Account creation, login and logout pass backend and browser checks.

The reporting workflow is also working:

- Residents can submit an issue with a title, description, location, category and priority.
- My Reports shows saved issues and counts for Reported, In Progress and Resolved.
- Search, status and category filters help find reports; lists have pagination.
- Each report has a detail page and a history of progress updates.
- Administrators can review all reports, change their status and add a note visible to the resident.
- Residents can only read their own reports and cannot change administrator progress updates.
- All 57 backend tests pass on SQLite and PostgreSQL. Six browser checks cover the reporting workflow and mobile layout.

Photo uploads and assignment are still planned. The current workflow uses three statuses; Assigned will be added with assignment.

## Run locally

### Start again on this computer

The project is in `Documents/Workspace/FixIt`. Its Python environment, frontend packages and local `.env` are already set up. PostgreSQL must be running.

Replace `/path/to/FixIt` with the location where you saved the project.

Open a terminal for the backend:

```bash
cd /path/to/FixIt
source .venv/bin/activate
flask --app server.app db-check
flask --app server.app db upgrade
flask --app server.app run --port 5001
```

Open a second terminal for the frontend:

```bash
cd /path/to/FixIt/client
npm run dev
```

Open **http://127.0.0.1:5173/**. Keep both terminals open. Press `Control+C` in each terminal to stop the app. If a port is already in use, stop the earlier server before starting another.

### First-time installation

See [Development setup](docs/development-setup.md) for the database and `.env` configuration. From the project folder, after setting up `.env` and PostgreSQL:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
flask --app server.app db upgrade
flask --app server.app run --port 5001
```

In a second terminal:

```bash
cd client
npm ci
npm run dev
```

Open `http://127.0.0.1:5173`. Run backend tests with `python -m pytest -q` and build the frontend with `npm run build` from `client/`.

Public signup always creates a Resident account. To create an administrator, run `flask --app server.app create-admin` from the project root with the virtual environment active and follow the prompts.

## Code layout

- `client/src/pages/` contains the home, account and report screens.
- `client/src/components/` contains small pieces shared between screens.
- `client/src/api.js` sends requests to Flask.
- `client/src/auth.jsx` keeps track of the signed-in user.
- `server/app/` contains the Flask routes and database models.
- `server/app/security/` contains password and session helpers.
- `server/migrations/` contains database changes generated with Flask-Migrate.
- `server/tests/` contains the backend tests.

## Project documents

- [Project plan](docs/project-plan.md)
- [Use case narratives](docs/use-case-narratives.md)
- [Project tracker workbook](docs/FixIt_Project_Tracker_Workbook.xlsx)
- [Development setup and verification](docs/development-setup.md)

## Scope

The first version will focus on reporting and tracking community issues. Maps, notifications, voting and native mobile apps are outside the current scope.

## Author

Anjaliben Valand
