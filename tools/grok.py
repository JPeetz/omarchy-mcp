import os
import subprocess as sp
import signal
import time
from executor import strip_ansi


def register(mcp):
    @mcp.tool()
    async def grok_execute(
        prompt: str,
        cwd: str = "/home/jpeetz",
        timeout: int = 300,
    ) -> str:
        """Execute a prompt with Grok CLI (xAI) on Omarchy.

        Args:
            prompt: The full prompt to send to Grok via stdin
            cwd: Working directory on Omarchy
            timeout: Max seconds to wait (30-1800)
        """
        effective_timeout = min(max(timeout, 30), 1800)
        start = time.monotonic()
        try:
            proc = sp.Popen(
                ["grok", "-p", prompt],
                stdin=sp.DEVNULL, stdout=sp.PIPE, stderr=sp.STDOUT,
                cwd=cwd, env=os.environ.copy(), start_new_session=True,
            )
            stdout_bytes, _ = proc.communicate(timeout=effective_timeout)
            exit_code = proc.returncode
        except sp.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=5)
            except sp.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
            return f"Grok timed out after {effective_timeout}s"
        duration = time.monotonic() - start
        output = strip_ansi(stdout_bytes.decode("utf-8", errors="replace"))
        tail = f"\n\n---\nExited {exit_code} in {duration:.1f}s"
        return output + tail if exit_code != 0 else output