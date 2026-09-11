#!/usr/bin/env python3
"""
NETRA-X Unified Full-Stack Dev Server Runner
Runs both FastAPI Backend and Vite React Frontend concurrently in a single terminal
with color-coded log multiplexing and graceful Ctrl+C cleanup.
"""

import os
import sys
import subprocess
import threading
import signal
import time
from pathlib import Path

# Safe Unicode / UTF-8 stdout configuration for Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ANSI Color Codes for terminal
RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
RED = "\033[91m"
DIM = "\033[2m"

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"

# Locate Python in backend/.venv if present, otherwise use sys.executable
VENV_PYTHON = BACKEND_DIR / ".venv" / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python")
PYTHON_EXE = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable

# Locate npm
NPM_CMD = "npm.cmd" if os.name == "nt" else "npm"

processes = []

def stream_logs(process, prefix, color):
    """Streams stdout/stderr of a subprocess with a stylized prefix."""
    try:
        for line in iter(process.stdout.readline, ""):
            if not line:
                break
            print(f"{color}{BOLD}[{prefix}]{RESET} {line.rstrip()}", flush=True)
    except Exception:
        pass

def cleanup(signum=None, frame=None):
    """Cleanly terminates child processes on Ctrl+C."""
    print(f"\n{YELLOW}{BOLD}Shutting down NETRA-X servers...{RESET}", flush=True)
    for p in processes:
        if p.poll() is None:
            try:
                if os.name == "nt":
                    subprocess.call(["taskkill", "/F", "/T", "/PID", str(p.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    p.terminate()
            except Exception:
                pass
    print(f"{GREEN}✓ NETRA-X Backend and Frontend stopped cleanly.{RESET}", flush=True)
    sys.exit(0)

def main():
    # Enable ANSI colors on Windows CMD/PowerShell if possible
    if os.name == "nt":
        os.system("color")

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    print(f"{CYAN}{BOLD}============================================================{RESET}", flush=True)
    print(f"{CYAN}{BOLD}  [*] NETRA-X — UNIFIED COMMAND & INTELLIGENCE PLATFORM     {RESET}", flush=True)
    print(f"{CYAN}{BOLD}============================================================{RESET}", flush=True)
    print(f"{GREEN}➜ Backend  :{RESET} http://localhost:8000 (Docs: http://localhost:8000/docs)", flush=True)
    print(f"{YELLOW}➜ Frontend :{RESET} http://localhost:5173", flush=True)
    print(f"{DIM}Press Ctrl+C at any time to stop both servers.{RESET}\n", flush=True)

    # 1. Start Backend Process (FastAPI / Uvicorn)
    backend_cmd = [
        PYTHON_EXE,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--reload",
    ]
    backend_proc = subprocess.Popen(
        backend_cmd,
        cwd=str(BACKEND_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    processes.append(backend_proc)

    # 2. Start Frontend Process (Vite React)
    frontend_cmd = [NPM_CMD, "run", "dev"]
    frontend_proc = subprocess.Popen(
        frontend_cmd,
        cwd=str(FRONTEND_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    processes.append(frontend_proc)

    # Launch streaming threads
    t_backend = threading.Thread(target=stream_logs, args=(backend_proc, "BACKEND", CYAN), daemon=True)
    t_frontend = threading.Thread(target=stream_logs, args=(frontend_proc, "FRONTEND", YELLOW), daemon=True)

    t_backend.start()
    t_frontend.start()

    # Monitor processes
    try:
        while True:
            time.sleep(0.5)
            if backend_proc.poll() is not None:
                print(f"{RED}[BACKEND] Server exited with code {backend_proc.returncode}{RESET}", flush=True)
                cleanup()
            if frontend_proc.poll() is not None:
                print(f"{RED}[FRONTEND] Server exited with code {frontend_proc.returncode}{RESET}", flush=True)
                cleanup()
    except KeyboardInterrupt:
        cleanup()

if __name__ == "__main__":
    main()
