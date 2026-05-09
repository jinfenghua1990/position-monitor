from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console

from src.pipeline import format_pipeline_result, run_daily_pipeline

console = Console()


def read_input_text(input_path: str | None) -> str:
    if input_path:
        path = Path(input_path)
        if not path.exists():
            raise FileNotFoundError(f'输入文件不存在: {input_path}')
        return path.read_text(encoding='utf-8')

    console.print('请粘贴持仓文本，结束后按 Ctrl+D (Linux/macOS) 或 Ctrl+Z (Windows)：', style='bold cyan')
    return sys.stdin.read()


def main() -> None:
    parser = argparse.ArgumentParser(description='position-monitor AI交易辅助系统')
    parser.add_argument(
        '--input',
        type=str,
        help='持仓文本文件路径，例如 data/input/positions.txt',
    )

    args = parser.parse_args()

    raw_text = read_input_text(args.input)

    if not raw_text.strip():
        console.print('未检测到输入内容。', style='bold red')
        return

    result = run_daily_pipeline(raw_text)

    console.print('\n📊 position-monitor v2.1\n', style='bold green')
    console.print(format_pipeline_result(result))


if __name__ == '__main__':
    main()
