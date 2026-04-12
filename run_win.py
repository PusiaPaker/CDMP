from __future__ import annotations

import sqlite3
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
VENV_DIR = PROJECT_ROOT / "venv"
VENV_PYTHON = VENV_DIR / "Scripts" / "python.exe"
ACTIVATE_SCRIPT = VENV_DIR / "Scripts" / "Activate.ps1"
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"
ENV_FILE = PROJECT_ROOT / ".env"
APP_ENTRYPOINT = "app.py"
APP_URL = "http://localhost:5000"


def read_env_file() -> dict[str, str]:
    env_map: dict[str, str] = {}
    if not ENV_FILE.exists():
        return env_map

    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env_map[key.strip()] = value.strip()

    return env_map

def run_command(
    command: list[str],
    cwd: Path = PROJECT_ROOT,
    check: bool = True,
    capture_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    print(f"\n> {' '.join(command)}")
    return subprocess.run(
        command,
        cwd=str(cwd),
        check=check,
        capture_output=capture_output,
        text=True,
    )


def run_powershell(
    command: str,
    check: bool = True,
    capture_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    return run_command(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            command,
        ],
        check=check,
        capture_output=capture_output,
    )


def ensure_virtualenv() -> None:
    if VENV_PYTHON.exists():
        print("Virtual environment already exists.")
        return

    print("Creating virtual environment...")
    run_command([sys.executable, "-m", "venv", str(VENV_DIR)])


def allow_scripts_for_current_user() -> None:
    print("Setting execution policy for current user...")
    result = run_powershell(
        "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force",
        check=False,
        capture_output=True,
    )

    if result.returncode == 0:
        return

    details = f"{result.stdout}\n{result.stderr}"
    if "ExecutionPolicyOverride" in details or (
        "overridden by a policy defined at a more specific scope" in details
    ):
        print(
            "Execution policy is managed by another scope. Continuing with "
            "process-scoped Bypass."
        )
        return

    raise subprocess.CalledProcessError(
        result.returncode,
        result.args,
        output=result.stdout,
        stderr=result.stderr,
    )


def activate_virtualenv_script() -> None:
    if not ACTIVATE_SCRIPT.exists():
        raise FileNotFoundError(f"Could not find activation script: {ACTIVATE_SCRIPT}")

    print("Running Activate.ps1...")
    run_powershell(f"& '{ACTIVATE_SCRIPT}'")


def install_requirements() -> None:
    if not REQUIREMENTS_FILE.exists():
        raise FileNotFoundError(f"Could not find requirements file: {REQUIREMENTS_FILE}")

    print("Installing dependencies from requirements.txt...")
    run_command(
        [str(VENV_PYTHON), "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)]
    )
    
def create_dotenv(download_file_path: str) -> str:
    selected_path = download_file_path.strip().strip('"')
    env_map = read_env_file()

    if not selected_path and "FILE_UPLOAD_STORAGE_PATH" in env_map:
        selected_path = env_map["FILE_UPLOAD_STORAGE_PATH"].strip().strip('"')
        if selected_path:
            print("Using FILE_UPLOAD_STORAGE_PATH from existing .env.")

    while not selected_path:
        selected_path = input(
            "Enter file path for file storage (example: C:\\xxx\\xxxx\\): "
        ).strip().strip('"')
        if not selected_path:
            print("Path cannot be blank.")

    env_map["FILE_UPLOAD_STORAGE_PATH"] = selected_path
    lines = [f"{key}={value}" for key, value in env_map.items()]
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Updated {ENV_FILE.name} with FILE_UPLOAD_STORAGE_PATH.")
    return selected_path


def resolve_sqlite_database_path() -> Path | None:
    env_map = read_env_file()
    database_uri = env_map.get("SQLALCHEMY_DATABASE_URI", "sqlite:///database.db")
    normalized_uri = database_uri.strip().strip('"').strip("'")

    if not normalized_uri.startswith(("sqlite:///", "sqlite+pysqlite:///")):
        return None

    after_scheme = normalized_uri.split("://", 1)[1]
    if after_scheme in {"/:memory:", ":memory:"}:
        return None

    relative_candidate = after_scheme.lstrip("/")
    if len(relative_candidate) >= 2 and relative_candidate[1] == ":":
        return Path(relative_candidate)

    return PROJECT_ROOT / "instance" / relative_candidate


def ensure_legacy_sqlite_schema() -> None:
    database_path = resolve_sqlite_database_path()
    if database_path is None:
        print("Database is not a local SQLite file. Skipping schema compatibility check.")
        return

    if not database_path.exists():
        print(f"No existing database found at {database_path}. A fresh one will be created.")
        return

    database_path.parent.mkdir(parents=True, exist_ok=True)
    updates: list[str] = []

    with sqlite3.connect(database_path) as connection:
        table_names = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }

        if "users" in table_names:
            user_columns = {
                row[1] for row in connection.execute("PRAGMA table_info(users)")
            }
            if "full_name" not in user_columns:
                connection.execute(
                    "ALTER TABLE users ADD COLUMN full_name VARCHAR(255)"
                )
                updates.append("users.full_name")

        if "projects" in table_names:
            project_columns = {
                row[1] for row in connection.execute("PRAGMA table_info(projects)")
            }
            if "budget_amount" not in project_columns:
                connection.execute(
                    "ALTER TABLE projects ADD COLUMN budget_amount NUMERIC(12, 2)"
                )
                updates.append("projects.budget_amount")

        if updates:
            connection.commit()

    if updates:
        print(
            "Updated legacy SQLite schema in "
            f"{database_path} to add: {', '.join(updates)}"
        )
    else:
        print("SQLite schema compatibility check passed.")

def flask_populate() -> None:
    print("Populating database with flask populate...")
    run_command([str(VENV_PYTHON), "-m", "flask", "--app", APP_ENTRYPOINT, "populate"])


def open_browser_after_delay(seconds: int = 2) -> None:
    def _open() -> None:
        time.sleep(seconds)
        webbrowser.open(APP_URL)

    threading.Thread(target=_open, daemon=True).start()


def run_flask() -> None:
    print("Starting Flask app...")
    run_command([str(VENV_PYTHON), "-m", "flask", "--app", APP_ENTRYPOINT, "run"])


def main() -> None:
    download_file_path = ""
    ensure_virtualenv()
    allow_scripts_for_current_user()
    activate_virtualenv_script()
    install_requirements()
    create_dotenv(download_file_path)
    ensure_legacy_sqlite_schema()
    flask_populate()
    open_browser_after_delay()
    run_flask()

    
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped by user.")
    except subprocess.CalledProcessError as exc:
        print(f"\nCommand failed with exit code {exc.returncode}.")
        raise SystemExit(exc.returncode)
