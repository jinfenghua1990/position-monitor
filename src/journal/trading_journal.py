"""交易日志与评分记录模块。

这个模块的目标不是预测某一笔交易必涨，而是长期记录：
- 买入时评分
- 买入理由
- 仓位与止损
- 后续 1/3/5 日结果
- 最大收益与最大回撤

后续系统可以基于这些记录统计：不同评分区间的胜率、平均收益、平均回撤，
帮助判断“83 分是否真的值得做”。
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


DEFAULT_JOURNAL_PATH = Path("data/trading_journal.json")


@dataclass
class TradeJournalEntry:
    """单笔交易评分记录。"""

    symbol: str
    name: str
    trade_date: str
    score: float
    action: str = "watch"  # watch / buy / sell / skip
    reasons: List[str] = field(default_factory=list)
    position_pct: Optional[float] = None
    stop_loss_pct: Optional[float] = None
    expected: str = ""
    result_1d_pct: Optional[float] = None
    result_3d_pct: Optional[float] = None
    result_5d_pct: Optional[float] = None
    max_profit_pct: Optional[float] = None
    max_drawdown_pct: Optional[float] = None
    review: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TradingJournal:
    """交易日志仓库。"""

    def __init__(self, path: Path | str = DEFAULT_JOURNAL_PATH):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> List[Dict[str, Any]]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError(f"交易日志格式错误，期望 list: {self.path}")
        return data

    def save(self, entries: Iterable[Dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(list(entries), f, ensure_ascii=False, indent=2)

    def add_entry(self, entry: TradeJournalEntry) -> Dict[str, Any]:
        entries = self.load()
        item = entry.to_dict()
        entries.append(item)
        self.save(entries)
        return item

    def update_result(
        self,
        symbol: str,
        trade_date: str,
        *,
        result_1d_pct: Optional[float] = None,
        result_3d_pct: Optional[float] = None,
        result_5d_pct: Optional[float] = None,
        max_profit_pct: Optional[float] = None,
        max_drawdown_pct: Optional[float] = None,
        review: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """回写某笔交易结果。"""
        entries = self.load()
        target = None
        for item in reversed(entries):
            if item.get("symbol") == symbol and item.get("trade_date") == trade_date:
                target = item
                break

        if target is None:
            return None

        updates = {
            "result_1d_pct": result_1d_pct,
            "result_3d_pct": result_3d_pct,
            "result_5d_pct": result_5d_pct,
            "max_profit_pct": max_profit_pct,
            "max_drawdown_pct": max_drawdown_pct,
            "review": review,
        }
        for key, value in updates.items():
            if value is not None:
                target[key] = value

        self.save(entries)
        return target

    def summarize_by_score_bucket(self) -> List[Dict[str, Any]]:
        """按评分区间统计历史表现。"""
        entries = self.load()
        buckets = {
            "90+": [],
            "80-89": [],
            "70-79": [],
            "<70": [],
        }

        for item in entries:
            score = float(item.get("score", 0))
            if score >= 90:
                bucket = "90+"
            elif score >= 80:
                bucket = "80-89"
            elif score >= 70:
                bucket = "70-79"
            else:
                bucket = "<70"
            buckets[bucket].append(item)

        summary: List[Dict[str, Any]] = []
        for bucket, items in buckets.items():
            completed = [x for x in items if x.get("result_5d_pct") is not None]
            wins = [x for x in completed if float(x.get("result_5d_pct", 0)) > 0]
            avg_5d = _average([x.get("result_5d_pct") for x in completed])
            avg_drawdown = _average([x.get("max_drawdown_pct") for x in completed])
            summary.append(
                {
                    "bucket": bucket,
                    "count": len(items),
                    "completed_count": len(completed),
                    "win_rate_pct": round(len(wins) / len(completed) * 100, 2) if completed else None,
                    "avg_5d_pct": avg_5d,
                    "avg_drawdown_pct": avg_drawdown,
                }
            )
        return summary


def create_today_entry(
    symbol: str,
    name: str,
    score: float,
    reasons: List[str],
    *,
    action: str = "buy",
    position_pct: Optional[float] = None,
    stop_loss_pct: Optional[float] = None,
    expected: str = "",
) -> TradeJournalEntry:
    """便捷创建今日交易记录。"""
    return TradeJournalEntry(
        symbol=symbol,
        name=name,
        trade_date=date.today().isoformat(),
        score=score,
        action=action,
        reasons=reasons,
        position_pct=position_pct,
        stop_loss_pct=stop_loss_pct,
        expected=expected,
    )


def _average(values: Iterable[Optional[float]]) -> Optional[float]:
    nums = [float(v) for v in values if v is not None]
    if not nums:
        return None
    return round(sum(nums) / len(nums), 2)
