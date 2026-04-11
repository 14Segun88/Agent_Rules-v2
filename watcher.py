#!/usr/bin/env python3
"""
AGENTS_RULES v2 — Watcher

Monitors the raw/ directory for new session logs and automatically
triggers compile.py when changes are detected.

Uses watchdog for filesystem monitoring with a debounce mechanism
to avoid multiple compilations for rapid changes.

Usage:
    python3 watcher.py                  # Run in foreground
    python3 watcher.py --daemon         # Run as background daemon
    python3 watcher.py --stop           # Stop the daemon

Dependencies:
    pip install watchdog
"""

import argparse
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import NoReturn

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] WATCHER %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("watcher")

BASE_DIR = Path(__file__).parent.resolve()
RAW_DIR = BASE_DIR / "raw"
COMPILE_SCRIPT = BASE_DIR / "compile.py"
PID_FILE = BASE_DIR / "watcher.pid"

# Debounce: wait this many seconds after the last change before compiling
DEBOUNCE_SECONDS = 5.0

# Minimum interval between compilations (seconds)
MIN_COMPILE_INTERVAL = 30.0


def install_watchdog() -> bool:
    """Install watchdog if not available."""
    try:
        import watchdog  # noqa: F401
        return True
    except ImportError:
        log.info("Installing watchdog...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "watchdog", "--quiet"],
                timeout=60,
            )
            return True
        except Exception as e:
            log.error("Failed to install watchdog: %s", e)
            return False


def run_compile() -> None:
    """Run the compile.py script."""
    log.info("🔄 Running compile.py...")
    try:
        result = subprocess.run(
            [sys.executable, str(COMPILE_SCRIPT)],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            log.info("✅ Compilation complete")
            if result.stdout.strip():
                for line in result.stdout.strip().splitlines()[-5:]:
                    log.info("  %s", line)
        else:
            log.error("❌ Compilation failed: %s", result.stderr[-500:] if result.stderr else "unknown error")
    except subprocess.TimeoutExpired:
        log.error("❌ Compilation timed out (120s)")
    except Exception as e:
        log.error("❌ Compilation error: %s", e)


def git_pull() -> None:
    """Pull latest changes before processing."""
    try:
        subprocess.run(
            ["git", "pull", "--rebase", "origin", "main"],
            cwd=str(BASE_DIR),
            capture_output=True,
            timeout=30,
        )
    except Exception:
        pass  # Non-critical


class RawLogHandler:
    """Handles filesystem events in raw/ directory."""

    def __init__(self) -> None:
        self.last_event_time: float = 0.0
        self.last_compile_time: float = 0.0
        self.pending: bool = False

    def on_event(self, filepath: str) -> None:
        """Called when a file event occurs."""
        if not filepath.endswith(".md"):
            return

        self.last_event_time = time.time()
        self.pending = True
        log.info("📝 Detected change: %s", Path(filepath).name)

    def check_and_compile(self) -> None:
        """Check if we should compile (debounce logic)."""
        if not self.pending:
            return

        now = time.time()
        time_since_event = now - self.last_event_time
        time_since_compile = now - self.last_compile_time

        if time_since_event >= DEBOUNCE_SECONDS and time_since_compile >= MIN_COMPILE_INTERVAL:
            self.pending = False
            self.last_compile_time = now
            git_pull()
            run_compile()


def run_with_watchdog(handler: RawLogHandler) -> NoReturn:
    """Run using watchdog for efficient filesystem monitoring."""
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer

    class WatchdogHandler(FileSystemEventHandler):
        def on_created(self, event) -> None:  # type: ignore[override]
            if not event.is_directory:
                handler.on_event(event.src_path)

        def on_modified(self, event) -> None:  # type: ignore[override]
            if not event.is_directory:
                handler.on_event(event.src_path)

    RAW_DIR.mkdir(exist_ok=True)
    observer = Observer()
    observer.schedule(WatchdogHandler(), str(RAW_DIR), recursive=False)
    observer.start()
    log.info("👁️ Watching %s (watchdog mode)", RAW_DIR)

    try:
        while True:
            handler.check_and_compile()
            time.sleep(1.0)
    except KeyboardInterrupt:
        observer.stop()
        log.info("Watcher stopped.")
    observer.join()
    sys.exit(0)


def run_polling(handler: RawLogHandler) -> NoReturn:
    """Fallback: polling-based monitoring."""
    RAW_DIR.mkdir(exist_ok=True)
    known_files: set[str] = set()
    known_mtimes: dict[str, float] = {}

    # Initial scan
    for f in RAW_DIR.glob("*.md"):
        known_files.add(f.name)
        known_mtimes[f.name] = f.stat().st_mtime

    log.info("👁️ Watching %s (polling mode, interval=3s)", RAW_DIR)

    try:
        while True:
            current_files = {f.name: f.stat().st_mtime for f in RAW_DIR.glob("*.md")}

            # Detect new or modified files
            for name, mtime in current_files.items():
                if name not in known_files or mtime != known_mtimes.get(name):
                    handler.on_event(str(RAW_DIR / name))

            known_files = set(current_files.keys())
            known_mtimes = current_files

            handler.check_and_compile()
            time.sleep(3.0)
    except KeyboardInterrupt:
        log.info("Watcher stopped.")
        sys.exit(0)


def daemonize() -> None:
    """Fork and run in background."""
    if os.name == "nt":
        log.error("Daemon mode not supported on Windows")
        sys.exit(1)

    pid = os.fork()
    if pid > 0:
        # Parent process
        PID_FILE.write_text(str(pid))
        log.info("Watcher started as daemon (PID: %d)", pid)
        log.info("To stop: python3 watcher.py --stop")
        sys.exit(0)

    # Child process
    os.setsid()
    log.info("Daemon running (PID: %d)", os.getpid())


def stop_daemon() -> None:
    """Stop the background daemon."""
    if not PID_FILE.exists():
        log.info("No running daemon found (no PID file)")
        return

    pid = int(PID_FILE.read_text().strip())
    try:
        os.kill(pid, signal.SIGTERM)
        log.info("Daemon stopped (PID: %d)", pid)
    except ProcessLookupError:
        log.info("Daemon already stopped (PID: %d)", pid)
    finally:
        PID_FILE.unlink(missing_ok=True)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="AGENTS_RULES v2 Watcher")
    parser.add_argument("--daemon", action="store_true", help="Run as background daemon")
    parser.add_argument("--stop", action="store_true", help="Stop the background daemon")
    args = parser.parse_args()

    if args.stop:
        stop_daemon()
        return

    if args.daemon:
        daemonize()

    # Write PID for foreground mode too
    PID_FILE.write_text(str(os.getpid()))

    handler = RawLogHandler()

    # Compile any pending files on startup
    run_compile()

    # Start watching
    if install_watchdog():
        run_with_watchdog(handler)
    else:
        log.warning("Falling back to polling mode")
        run_polling(handler)


if __name__ == "__main__":
    main()
