#!/usr/bin/env python3
"""
Supervisor for Spidy TXT-EXTRACTOR on Render (Web Service)
- Starts Gunicorn (Flask health-check) so Render health checks pass
- Starts the actual Telegram bot (python -m Extractor)
- Forwards SIGTERM/SIGINT cleanly
"""

import os
import signal
import subprocess
import sys
import time

procs = []


def start():
    # Create sessions directory if needed
    os.makedirs("sessions", exist_ok=True)

    # 1. Health-check server using Gunicorn (binds to $PORT)
    port = os.environ.get("PORT", "10000")
    procs.append(subprocess.Popen([
        "gunicorn",
        "app:app",                    # uses existing app.py
        "--bind", f"0.0.0.0:{port}",
        "--workers", "1",
        "--threads", "2",
        "--timeout", "120",
        "--access-logfile", "-",
        "--error-logfile", "-",
        "--log-level", "info"
    ]))

    # 2. Telegram Bot
    procs.append(subprocess.Popen([sys.executable, "-m", "Extractor"]))


def handle_signal(signum, frame):
    print(f"[Supervisor] Received signal {signum}, shutting down...")
    for p in procs:
        if p.poll() is None:
            try:
                p.send_signal(signum)
            except Exception as e:
                print(f"Error signaling {p.pid}: {e}")
    for p in procs:
        try:
            p.wait(timeout=12)
        except subprocess.TimeoutExpired:
            p.kill()
    sys.exit(0)


signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)

print("[Supervisor] Starting Gunicorn + Bot...")
start()

# Monitor both processes
try:
    while True:
        time.sleep(3)
        for p in procs:
            ret = p.poll()
            if ret is not None:
                print(f"[Supervisor] Process {p.pid} exited with code {ret}. Shutting down.")
                for other in procs:
                    if other is not p and other.poll() is None:
                        other.terminate()
                sys.exit(ret or 1)
except KeyboardInterrupt:
    handle_signal(signal.SIGINT, None)
