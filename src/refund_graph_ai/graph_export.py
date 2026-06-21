from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

from .workflow import WORKFLOW_GRAPH


def _find_mermaid_command() -> list[str] | None:
    if shutil.which("mmdc"):
        return ["mmdc"]

    npx_path = shutil.which("npx")
    if npx_path:
        return [npx_path, "@mermaid-js/mermaid-cli"]

    return None


def _render_png(input_path: Path, output_path: Path) -> bool:
    command_prefix = _find_mermaid_command()
    if not command_prefix:
        print("Mermaid CLI not found. Generated .mmd only.")
        print("Install with: npm i -g @mermaid-js/mermaid-cli")
        return False

    command = [
        *command_prefix,
        "-i",
        str(input_path),
        "-o",
        str(output_path),
    ]

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        print(f"Failed to render PNG: {exc}")
        return False

    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export the refund workflow graph as Mermaid (.mmd) and optional PNG."
    )
    parser.add_argument("--mmd", default="graph.mmd", help="Output Mermaid file path")
    parser.add_argument("--png", default="graph.png", help="Output PNG file path")
    parser.add_argument(
        "--no-png",
        action="store_true",
        help="Only export Mermaid text and skip PNG rendering",
    )
    args = parser.parse_args()

    mmd_path = Path(args.mmd)
    mmd_path.write_text(WORKFLOW_GRAPH.get_graph().draw_mermaid(), encoding="utf-8")
    print(f"Mermaid graph written to: {mmd_path}")

    if args.no_png:
        return

    png_path = Path(args.png)
    if _render_png(mmd_path, png_path):
        print(f"PNG graph written to: {png_path}")
