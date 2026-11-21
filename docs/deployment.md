# Hosting FixIt

FixIt currently runs locally using React, Flask and PostgreSQL. It is not published online. Follow the README or development setup guide to run it on your computer.

## Before publishing

Choose a host that supports Python, PostgreSQL, HTTPS and persistent photo storage. A hosting account and plan are still needed.

The app can serve the built React frontend and Flask API from the same address. Build the frontend with `npm ci` and `npm run build` in `client/`. From the project root, install the Python requirements and run migrations before starting the server:

```bash
pip install -r requirements-lock.txt
flask --app server.app db upgrade
gunicorn --bind 127.0.0.1:8000 --workers 2 --threads 2 server.wsgi:app
```

The Gunicorn command belongs behind the host's HTTPS proxy. Configure the following private environment values on the host:

- `DATABASE_URL`: the PostgreSQL connection URL.
- `SECRET_KEY`: a new random signing key of at least 32 characters.
- `FIXIT_ENV=production`: enables production checks and secure cookies.
- `UPLOAD_FOLDER`: an absolute folder that survives service restarts.
- `RATELIMIT_STORAGE_URI`: a shared store such as Redis for multiple workers.
- `TRUST_PROXY_COUNT`: the exact number of trusted proxies in front of Flask.

Create an administrator with `flask --app server.app create-admin` and follow the prompts. Keep passwords and connection values out of Git.

## Check the live app

After hosting is set up, check `/api/ready`, signup, login, photo reporting, assignment, status updates and logout. Restart the service and confirm the report and photo remain available. Verify HTTPS and secure session cookies before recording a live URL.

Back up the database and uploaded photos before future upgrades. The current migration is `a921b5f0d618`. Hosting and live-site checks remain pending.
