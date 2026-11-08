"""Restart the development database stored in this project's .local folder."""

from pathlib import Path
import shutil
import shlex
import subprocess

root = Path(__file__).resolve().parents[1]
data = root / ".local" / "postgres"
socket = root / ".local" / "postgres-socket"
pg_ctl = shutil.which("pg_ctl") or "/opt/homebrew/opt/postgresql@16/bin/pg_ctl"
if not (data / "PG_VERSION").exists():
    raise SystemExit(
        "Local database not found. Follow the first-time PostgreSQL setup in docs/development-setup.md."
    )
if not Path(pg_ctl).is_file():
    raise SystemExit("pg_ctl was not found. Add your PostgreSQL bin folder to PATH.")
status = subprocess.run([pg_ctl, "-D", str(data), "status"], stdout=subprocess.DEVNULL)
if status.returncode == 0:
    print("The local database is already running.")
else:
    socket.mkdir(parents=True, exist_ok=True)
    options = f"-p 55432 -h 127.0.0.1 -k {shlex.quote(str(socket))}"
    subprocess.run(
        [
            pg_ctl,
            "-D",
            str(data),
            "-l",
            str(root / ".local" / "postgres.log"),
            "-o",
            options,
            "start",
        ],
        check=True,
    )
