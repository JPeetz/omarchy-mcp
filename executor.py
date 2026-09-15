import os
import signal
import subprocess
import time
import re

_ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def strip_ansi(text: str) -> str:
    return _ANSI_ESCAPE.sub("", text).strip()

def run_command(cmd: list[str], cwd: str = "/home/jpeetz", timeout: int = 300, env: dict | None = None) -> dict:
    start = time.monotonic()
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=cwd,
            env=merged_env,
            start_new_session=True,
        )
        try:
            stdout_bytes, _ = proc.communicate(timeout=timeout)
            exit_code = proc.returncode
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
            return {
                "ok": False,
                "output": f"Command timed out after {timeout}s",
                "exit_code": -1,
                "duration_s": time.monotonic() - start,
                "error": "timeout",
            }
        duration = time.monotonic() - start
        output = strip_ansi(stdout_bytes.decode("utf-8", errors="replace"))
        return {
            "ok": exit_code == 0,
            "output": output,
            "exit_code": exit_code,
            "duration_s": round(duration, 2),
            "error": None if exit_code == 0 else f"exit code {exit_code}",
        }
    except FileNotFoundError as e:
        return {
            "ok": False,
            "output": f"Command not found: {e}",
            "exit_code": -1,
            "duration_s": time.monotonic() - start,
            "error": f"command not found: {e}",
        }
    except Exception as e:
        return {
            "ok": False,
            "output": str(e),
            "exit_code": -1,
            "duration_s": time.monotonic() - start,
            "error": str(e),
        }
