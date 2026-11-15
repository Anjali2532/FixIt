# FixIt final demonstration

Use two browser sessions: one resident and one administrator. Use clearly labeled demonstration contacts and an example location. Staff contacts are assignment records, not additional login accounts.

## Start the app

Follow the README to start the local database, Flask and React. Open `http://127.0.0.1:5173`. The ignored `.local/admin-login.txt` contains this computer’s existing development administrator login; never upload it. On a new installation, create an administrator with `flask --app server.app create-admin`.

## Demonstration steps

1. Create a resident account. Show password rules, email validation and the empty My Reports dashboard.
2. Submit a report with title, location, category and an optional photo. Show the preview, remove/reselect control, confirmation and report number.
3. Open My Reports. Show All, Open and Resolved views, search, category filters and the mobile card layout.
4. In the administrator session, open Staff and create two demonstration maintenance contacts.
5. Open the resident’s report, assign it to the first contact and add a note. Show the automatic Assigned status and the resident’s updated assignment.
6. Change the report to In Progress, reassign it to the second contact and explain the history’s old/new values, timestamp and administrator name.
7. Resolve the report with a note explaining the fix. Show that a resolved report cannot be reassigned until reopened. Reopen it and add a progress note without changing its status.
8. Open the same report in two administrator tabs. Save from one tab; try saving the older version from the other. Show the conflict message and reload the latest report before editing again.
9. Show that a resident cannot open the Staff page or another resident’s report/photo. Log out and confirm protected pages require login again.
10. Show the saved test results, run instructions, hosting notes and project tracker. Explain which work was completed and which hosting steps remain.

## Points to explain

- React sends requests to Flask, which uses SQLAlchemy to access PostgreSQL.
- Passwords use salted scrypt hashes; login records can be revoked on logout.
- Server-side roles and ownership checks protect reports and photos.
- Report updates and history entries commit together. Version checks stop stale updates from overwriting newer work.
- Uploaded images are validated, renamed and stored separately from the database.
- A hosted deployment needs HTTPS, a durable database, Redis and persistent photo storage.

## Before final submission

- Enter actual dates and personal hours in the new work-log entries.
- Push the code and screenshots, then open the tracker’s GitHub evidence links.
- Confirm the commit name and verified email belong to the intended contributor.
- Run the backend tests and frontend build; review the saved cross-browser results.
- If a live URL is required, finish hosting setup and the online smoke test before calling the project deployed.
- Submit the final tracker and repository link, and follow the instructor’s requirements for the demo or report.
