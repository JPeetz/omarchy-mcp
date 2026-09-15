from tools.claude import register as register_claude
from tools.codex import register as register_codex
from tools.files import register as register_files
from tools.system import register as register_system
from tools.status import register as register_status

ALL_TOOLS = [register_claude, register_codex, register_files, register_system, register_status]