import os
import json
import stat as stat_module


def register(mcp):
    @mcp.tool()
    async def file_read(
        path: str,
        offset: int = 0,
        limit: int = 2000,
    ) -> str:
        """Read a file's content from the Omarchy filesystem.

        Args:
            path: Absolute path to file
            offset: Starting line (0-indexed)
            limit: Maximum lines to return
        """
        real_path = os.path.realpath(path)
        if not real_path.startswith("/home/jpeetz") and not real_path.startswith("/tmp"):
            return json.dumps({"error": "path must be under /home/jpeetz or /tmp"})

        try:
            with open(real_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            total = len(lines)
            selected = lines[offset : offset + limit]
            content = "".join(selected)

            return json.dumps({
                "content": content,
                "total_lines": total,
                "offset": offset,
                "returned_lines": len(selected),
                "truncated": (offset + limit) < total,
            })
        except FileNotFoundError:
            return json.dumps({"error": f"File not found: {path}"})
        except IsADirectoryError:
            return json.dumps({"error": f"Path is a directory: {path}"})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def file_write(
        path: str,
        content: str,
        mode: str = "overwrite",
    ) -> str:
        """Write content to a file on Omarchy.

        Args:
            path: Absolute path to file
            content: Content to write
            mode: 'overwrite' or 'append'
        """
        real_path = os.path.realpath(path)
        if not real_path.startswith("/home/jpeetz") and not real_path.startswith("/tmp"):
            return json.dumps({"error": "path must be under /home/jpeetz or /tmp"})

        try:
            write_mode = "a" if mode == "append" else "w"
            os.makedirs(os.path.dirname(real_path), exist_ok=True)
            with open(real_path, write_mode, encoding="utf-8") as f:
                f.write(content)
            return json.dumps({"ok": True, "path": real_path, "mode": mode, "bytes": len(content)})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def file_list(
        path: str = "/home/jpeetz",
    ) -> str:
        """List files and directories at a path on Omarchy.

        Args:
            path: Directory path to list
        """
        real_path = os.path.realpath(path)
        try:
            entries = os.listdir(real_path)
            result = []
            for name in sorted(entries):
                full = os.path.join(real_path, name)
                try:
                    st = os.stat(full)
                    result.append({
                        "name": name,
                        "type": "dir" if os.path.isdir(full) else "file",
                        "size": st.st_size,
                        "mtime": st.st_mtime,
                    })
                except OSError:
                    result.append({"name": name, "type": "unknown", "size": 0, "mtime": 0})
            return json.dumps({"entries": result, "count": len(result)})
        except FileNotFoundError:
            return json.dumps({"error": f"Directory not found: {path}"})
        except NotADirectoryError:
            return json.dumps({"error": f"Not a directory: {path}"})
        except Exception as e:
            return json.dumps({"error": str(e)})