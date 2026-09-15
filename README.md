# Omarchy MCP Server

A purpose-built [Model Context Protocol](https://modelcontextprotocol.io/) server that runs on an Omarchy (Arch Linux) VM and exposes local AI agents and system tools as MCP tools — consumable by [Hermes Agent](https://github.com/NousResearch/hermes-agent) or any MCP client.

It replaces an SSH-based dispatch pipeline with a structured, authenticated MCP protocol — removing plaintext credentials from skill files, eliminating fragile heredoc quoting, and replacing ANSI-scraping with structured JSON-RPC results.

## Why

Before this server, dispatching tasks from Hermes Agent (Mac) to the Omarchy VM required writing prompts to files, SCP-ing them over, SSH-ing to run `claude -p` or `codex exec`, SCP-ing results back, and stripping ANSI with a 3-pass regex. That pipeline had a plaintext password embedded in skill files, fragile heredoc quoting, silent failures on timeout, and no streaming.

This server collapses that into authenticated, structured tool calls over Streamable HTTP.

## Architecture

```
┌─────────────────────────────────────┐
│  Machine A (Mac / control plane)    │
│                                     │
│  Hermes Agent                       │
│  config.yaml:                       │
│    mcp_servers:                     │
│      omarchy:                       │
│        url: "http://<vm>:8911/mcp"  │
│        headers:                     │
│          Authorization: Bearer <t>  │
└─────────────────────┬───────────────┘
                      │  Streamable HTTP
┌─────────────────────▼───────────────┐
│  Machine B (Omarchy VM / worker)    │
│                                     │
│  omarchy-mcp (systemd)              │
│  FastMCP v2 + uvicorn, port 8911    │
│                                     │
│  Tools:                             │
│  ├─ claude_execute()                │
│  ├─ codex_execute()                 │
│  ├─ file_read / file_write / list   │
│  ├─ system_run() (whitelisted)      │
│  └─ status()                        │
└─────────────────────────────────────┘
```

## Tools

| Tool | Description |
|------|-------------|
| `claude_execute(prompt, cwd?, timeout?)` | Run Claude Code CLI (YOLO mode) with a prompt via stdin |
| `codex_execute(prompt, cwd?, timeout?)` | Run Codex CLI with a prompt via stdin |
| `file_read(path, offset?, limit?)` | Read a file from the Omarchy filesystem |
| `file_write(path, content, mode?)` | Write a file on the Omarchy filesystem |
| `file_list(path?)` | List directory contents |
| `system_run(command, cwd?, timeout?)` | Run a whitelisted shell command (git, python3, ls, cat, ...) |
| `status()` | VM health: uptime, memory, load, tool availability |

Full specifications in [SPEC.md](./SPEC.md).

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/JPeetz/omarchy-mcp.git
cd omarchy-mcp
pip install -r requirements.txt
```

MCP SDK 2.x (`mcp>=2.0.0`, which bundles uvicorn/starlette) and `psutil` are required.

### 2. Configure

```bash
cp .env.example .env
# Generate a strong token:
openssl rand -hex 32
# Set OMARCHY_MCP_TOKEN in .env
```

### 3. Run

```bash
python3 server.py
```

Or install as a systemd service:

```ini
[Unit]
Description=Omarchy MCP Server
After=network.target

[Service]
Type=simple
User=jpeetz
WorkingDirectory=/path/to/omarchy-mcp
EnvironmentFile=/path/to/omarchy-mcp/.env
ExecStart=/usr/bin/python3 /path/to/omarchy-mcp/server.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 4. Connect Hermes Agent

```bash
hermes config set mcp_servers.omarchy.url "http://<vm>:8911/mcp"
hermes config set mcp_servers.omarchy.headers.Authorization "Bearer <token>"
hermes mcp test omarchy
```

Then call the tools directly:

```bash
hermes -c "Call the omarchy status tool and show me the result"
```

## Security

- **Bearer token auth** — constant-time comparison on every request
- **Token in `.env`** — never in skill files or session prompts
- **Path validation** — `file_read`/`file_write` restricted to `/home/*` and `/tmp`
- **Command whitelist** — `system_run` only allows pre-approved commands
- **Firewall** — open only the MCP port on the VM's firewall

**Note:** This is a tool-level fence, not an OS-level one. The MCP server runs as the same OS user as the agents it drives. Treat it as equivalent to SSH access — use a strong token and run it behind a firewall or VPN when possible.

## Docker

A `Dockerfile` is included. The container runs the MCP server; you may want to add your own `claude`/`codex` binaries via a custom image.

## License

MIT — see [LICENSE](./LICENSE).