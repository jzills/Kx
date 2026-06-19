#!/usr/bin/env python3
"""Regenerate the command reference table in README.md from the CLI definition.

Run with --check to exit 1 if the table is stale (used by pre-commit).
"""

import re
import sys

sys.path.insert(0, "src")

import typer.main
from typer.core import TyperArgument, TyperOption
from kx.main import app

SENTINEL_START = "<!-- commands-table-start -->"
SENTINEL_END = "<!-- commands-table-end -->"
README_PATH = "README.md"


def format_param(param) -> str:
    if getattr(param, "hidden", False):
        return ""
    if isinstance(param, TyperArgument):
        name = param.name or "arg"
        if param.nargs == -1:
            return f"[<{name}>...]" if not param.required else f"<{name}>..."
        return f"<{name}>" if param.required else f"[<{name}>]"
    if isinstance(param, TyperOption):
        if getattr(param, "is_eager", False):
            return ""
        opts = "/".join(param.opts)
        if param.is_flag:
            return f"[{opts}]"
        type_name = getattr(param.type, "name", "value")
        return f"[{opts} {type_name}]"
    return ""


def build_signature(cmd_name: str, cmd) -> str:
    parts = [f"kx {cmd_name}"]
    for param in cmd.params:
        formatted = format_param(param)
        if formatted:
            parts.append(formatted)
    if cmd.context_settings.get("allow_extra_args", False):
        parts.append("[kubectl flags...]")
    return " ".join(parts)


def generate_table() -> str:
    click_app = typer.main.get_command(app)
    rows = ["| Command | Description |", "|---|---|"]
    for name, cmd in click_app.commands.items():
        if cmd.hidden:
            continue
        sig = build_signature(name, cmd)
        description = (cmd.help or "").replace("\n", " ").strip()
        rows.append(f"| `{sig}` | {description} |")
    return "\n".join(rows)


def update_readme(check: bool = False) -> bool:
    with open(README_PATH) as f:
        content = f.read()

    pattern = re.compile(
        rf"{re.escape(SENTINEL_START)}\n.*?\n?{re.escape(SENTINEL_END)}",
        re.DOTALL,
    )
    if not pattern.search(content):
        print(f"Sentinel comments not found in {README_PATH}. Add:")
        print(f"  {SENTINEL_START}")
        print(f"  {SENTINEL_END}")
        sys.exit(1)

    table = generate_table()
    replacement = f"{SENTINEL_START}\n{table}\n{SENTINEL_END}"
    new_content = pattern.sub(replacement, content)

    if new_content == content:
        return False

    if check:
        return True

    with open(README_PATH, "w") as f:
        f.write(new_content)
    return True


if __name__ == "__main__":
    check_mode = "--check" in sys.argv
    changed = update_readme(check=check_mode)
    if check_mode and changed:
        print(
            "README.md command table is out of date. Run: python scripts/gen_command_table.py"
        )
        sys.exit(1)
    if changed:
        print(f"Updated {README_PATH}.")
        sys.exit(1)  # non-zero so pre-commit surfaces the change for staging
    else:
        print(f"{README_PATH} is up to date.")
