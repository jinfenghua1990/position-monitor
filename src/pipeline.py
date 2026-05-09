from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from src.data.text_importer import TextDataImporter
from src.journal.trading_journal import TradingJournal
from src.report.reporter import generate_daily_report
from src.strategy.risk_control import check_risk_rules
from src.strategy.second_wave import analyze_second_wave


@dataclass
class PipelineResult:
    positions: List[Dict[str, Any]]
    alerts: List[str]
    second_wave_items: List[str]
    report_path: Optional[str]
    learning_notes: List[str]
    raw_text_path: Optional[str]


def load_config(path: str | Path = "config.yaml") -> Dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        return {}
    with config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def run_daily_pipeline(
    raw_text: str,
    *,
    config_path: str | Path = "config.yaml",
    save_raw: bool = True,
    raw_category: str = "positions",
) -> PipelineResult:
    config = load_config(config_path)
    importer = TextDataImporter()

    raw_text_path = importer.save_raw_text(raw_text, raw_category) if save_raw else None
    positions = importer.parse_positions(raw_text)

    alerts = check_risk_rules(positions, config)
    second_wave_items = analyze_second_wave(config)
    report_path = generate_daily_report(positions, alerts, second_wave_items)

    journal = TradingJournal()
    learning_notes = journal.generate_learning_notes()

    return PipelineResult(
        positions=positions,
        alerts=alerts,
        second_wave_items=second_wave_items,
        report_path=report_path,
        learning_notes=learning_notes,
        raw_text_path=raw_text_path,
    )


def format_pipeline_result(result: PipelineResult) -> str:
    lines: List[str] = []
    lines.append("# 今日分析结果")

    lines.append("\n## 持仓解析")
    if result.positions:
        for p in result.positions:
            lines.append(
                f"- {p.get('symbol')} {p.get('name')} 成本:{p.get('cost_price')} 现价:{p.get('current_price')} 盈亏:{p.get('profit_pct')}%"
            )
    else:
        lines.append("- 未解析到持仓，请检查文本格式。")

    lines.append("\n## 风控提醒")
    if result.alerts:
        for alert in result.alerts:
            lines.append(f"- {alert}")
    else:
        lines.append("- 暂无风控提醒。")

    lines.append("\n## 二波观察")
    if result.second_wave_items:
        for item in result.second_wave_items:
            lines.append(f"- {item}")
    else:
        lines.append("- 暂无二波观察目标。")

    lines.append("\n## 学习建议")
    for note in result.learning_notes:
        lines.append(f"- {note}")

    if result.raw_text_path:
        lines.append(f"\n原始文本已保存：{result.raw_text_path}")
    if result.report_path:
        lines.append(f"日报已生成：{result.report_path}")

    return "\n".join(lines)
