import shlex
import json


WHITELIST = [
    "git", "python3", "ls", "cat", "head", "tail", "grep", "which",
    "whoami", "hostname", "uname", "date", "pwd", "echo", "wc",
    "find", "du", "df", "ps", "uptime", "free",
]


def register(mcp):
    @mcp.tool()
    async def system_run(
        command: str,
        cwd: str = "/home/jpeetz",
        timeout: int = 60,
    ) -> str:
        """Execute a shell command on Omarchy (whitelisted commands only).

        Args:
            command: Shell command to run
            cwd: Working directory
            timeout: Max seconds to wait (5-300)
        """
        parts = shlex.split(command)
        if not parts:
            return json.dumps({"error": "empty command"})
        base = parts[0]
        if base not in WHITELIST:
            return json.dumps({
                "error": f"Command '{base}' is not in the whitelist",
                "whitelist": WHITELIST,
            })

        from executor import run_command
        result = run_command(
            ["bash", "-c", command],
            cwd=cwd,
            timeout=min(max(timeout, 5), 300),
        )
        return json.dumps(result)