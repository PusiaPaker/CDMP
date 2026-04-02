from __future__ import annotations

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
    env_map: dict[str, str] = {}

    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            env_map[key.strip()] = value.strip()

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
