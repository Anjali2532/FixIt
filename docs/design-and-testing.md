# FixIt design and testing

FixIt separates the interface, request handling and stored data. React displays forms and reports. Flask validates requests and checks the signed-in user. SQLAlchemy maps Python objects to PostgreSQL tables. The browser never connects directly to the database.

## Database requests

`DATABASE_URL` is read in [the app setup](../server/app/__init__.py) and assigned to `SQLALCHEMY_DATABASE_URI`. The shared `db` object is initialized there. SQLAlchemy uses the psycopg driver to execute SQL through that PostgreSQL connection; Python query expressions become SQL with bound parameter values. [The models](../server/app/models.py) define the tables and relationships; migrations apply schema changes to an existing database.

For example, submitting a report follows these steps:

1. `NewReport.jsx` collects the fields and optional photo. [api.js](../client/src/api.js) sends a POST request to `/api/issues`, including the session cookie and CSRF token. A photo uses multipart form data.
2. Flask checks that the user is a Resident and validates lengths, category and priority. The owner comes from the authenticated user, so changing an owner field in the browser cannot assign a report to someone else.
3. `create_issue()` constructs an `Issue`. `db.session.add()` stages it and `flush()` sends the insert to obtain its ID without committing yet. That ID links the initial `IssueUpdate` to the report.
4. `db.session.commit()` saves both records together. If saving fails, rollback cancels the transaction and the newly uploaded photo is removed.
5. Flask returns JSON with status 201. React uses the response to show the confirmation and report number. Reloading reads the saved record from the database.

The main tables have separate purposes: `users` stores accounts; `auth_sessions` stores revocable login records; `issues` stores each report's current state; `staff_contacts` stores assignment contacts; and `issue_updates` stores its history. Foreign keys connect a report to its resident, staff contact and updates. A contact is not a staff login account.

## Photos and drafts

The photo bytes are stored in an upload folder; the report row stores only the generated filename. [photos.py](../server/app/photos.py) checks the actual image contents, limits size and pixel count, corrects orientation and writes a clean JPEG without the original metadata. A generated name avoids trusting the uploaded filename. The protected photo endpoint checks report ownership before sending the file.

Draft text stays in browser session storage scoped to the resident account, so a failed request or expired login does not immediately lose the typed report. The browser cannot restore a file input after login, so the photo must be selected again. A submission identifier and database uniqueness rule prevent a retry from saving the same report twice. These choices address failed submissions separately from photo storage.

## Assignment and history

The assignment endpoint in [issues.py](../server/app/issues.py) accepts a staff ID and the report version. Flask requires an Administrator, checks that the contact is active and rejects assignment of a resolved report. A new assignment moves Reported to Assigned. Reassignment keeps an In Progress report in that status.

The current staff ID belongs on `Issue`, while `IssueUpdate` records what changed, the old/new names, note, actor and time. Saving both in one transaction avoids showing a new assignment without its matching history. Deactivating a contact keeps earlier records intact.

The detail endpoint reads updates for one report, ordered by timestamp and ID. React displays that list as a timeline. Residents can see progress on their own reports; only administrators receive the actor's name and administrator controls. Ownership is checked in the database query, not just by hiding buttons.

## Status rules

Flask keeps the allowed status transitions in `update_issue()`. Assigned and In Progress require an assignee. A changed status needs a 5–1,000 character note, including an explanation when resolving a report. Reopening allows further work. Saving the same status does not create duplicate history.

Each edit sends the version that React last loaded. The server locks the report row and compares that number with the stored version. A successful change increases the version. If another administrator saved first, the old edit receives HTTP 409 and the user must reload. This prevents an older tab from silently overwriting newer work.

## Dashboard queries

`visible_query()` limits a resident to `Issue.user_id == g.user.id`; administrators can query all reports. The server adds search, status, category and administrator-only staff filters to this query. It allows only predefined sorting choices, then selects 20 records for the requested page. Filtering before pagination keeps the results consistent across pages.

Status totals and administrator summaries are calculated with database counts. Needs Attention means a report is open and either unassigned or more than seven days old. These counts help administrators find outstanding work without reading every report.

## Tests and their setup

[conftest.py](../server/tests/conftest.py) creates a fresh Flask test app for each test. By default it uses an in-memory SQLite database; setting `FIXIT_TEST_DATABASE_URL` runs against the separate local `fixit_test` PostgreSQL database. The fixture creates tables, gives the test a Flask client, and removes the tables afterward. Uploaded test images use a temporary folder. The PostgreSQL guard prevents these tests from resetting the normal application database.

Tests use setup, action and assertion: create the required users/data, send an HTTP request through the Flask client, and assert both the response and stored records. The `send()` helper in [test_admin.py](../server/tests/test_admin.py) fetches a CSRF token and attaches it to a request. Separate clients represent separate signed-in users.

Specific examples explain what the assertions prove:

- **Ownership:** `test_other_resident_cannot_read_or_change_report` creates two residents and a report belonging to the first. The second cannot read or update it. This checks the server-side boundary independently of React.
- **Assignment and history:** `test_assignment_reassignment_status_and_resident_history` assigns two different contacts in sequence, changes status and reopens the report. Assertions check the current assignee, old/new history values and the resident's restricted response.
- **Old edits:** `test_stale_update_and_assignment_return_conflict` saves a version, makes a newer assignment, then submits the old version. It expects 409 and verifies the report remains Assigned. It simulates an outdated edit sequentially rather than running two browsers concurrently.
- **Rollback:** `test_assignment_and_history_rollback_together` installs a temporary SQLAlchemy event that raises an error before history insertion. The request must fail with 503, while the report remains unassigned, Reported and version 1. The event is removed afterward. This checks that the transaction does not save half an update.
- **Photos:** tests in [test_photos.py](../server/tests/test_photos.py) generate small image files in memory, upload them through the client and inspect responses and temporary storage. Cases include unsupported contents, size limits, another resident's access, duplicate retries and cleanup after a database failure.

## Running the checks

From the project root, with the virtual environment active:

```bash
python -m pytest -q
python -m pytest server/tests/test_admin.py -q
```

For the PostgreSQL run, set `FIXIT_TEST_DATABASE_URL` to the private connection URL for the local `fixit_test` database before running pytest. Never use the application database. Build the frontend with `npm run build` in `client/`.

The saved November 15 results show **94 passing backend tests on SQLite and 94 on PostgreSQL**. [Browser results](evidence/phase3-browser-checks.json) record ten workflow checks each in Chrome, Firefox and WebKit: reporting with a photo, staff management, assignment, progress, history, filtering, mobile layout and access restrictions. Browser automation used separate resident/admin contexts, filled forms, clicked controls and asserted visible results and responses. The 390-pixel mobile checks are emulation, not physical-phone tests. Backend tests check data and permissions; browser checks cover the interface connecting those operations.

## Setup and demonstration

[Development setup](development-setup.md) explains how to start PostgreSQL, Flask and React. [The demo guide](demo-guide.md) walks through a resident report and administrator follow-up. [Hosting notes](deployment.md) list the remaining publication requirements. The app is currently local; no live deployment is claimed.
