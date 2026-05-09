"""交易日志与评分记录模块。

这个模块的目标不是预测某一笔交易必涨，而是长期记录：
- 买入时评分
- 买入理由
- 仓位与止损
- 后续 1/3/5 日结果
- 最大收益与最大回撤
- 退出原因与失败原因

后续系统可以基于这些记录统计：不同评分区间的胜率、平均收益、平均回撤，
以及最常见的亏损模式，帮助判断“83 分是否真的值得做”。
"""

from __future__ import annotations

import json
from collections import Counter
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

    # 交易结果回写字段
    result_1d_pct: Optional[float] = None
    result_3d_pct: Optional[float] = None
    result_5d_pct: Optional[float] = None
    max_profit_pct: Optional[float] = None
    max_drawdown_pct: Optional[float] = None
    exit_date: Optional[str] = None
    exit_reason: str = ""  # stop_loss / take_profit / manual / timeout / break_structure
    followed_plan: Optional[bool] = None

    # 失败数据库字段
    failure_tags: List[str] = field(default_factory=list)
    failure_note: str = ""
    review: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    updated_at: Optional[str] = None

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
        exit_date: Optional[str] = None,
        exit_reason: Optional[str] = None,
        followed_plan: Optional[bool] = None,
        failure_tags: Optional[List[str]] = None,
        failure_note: Optional[str] = None,
        review: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """回写某笔交易结果。

        symbol + trade_date 用来定位一笔交易。
        如果找不到，返回 None，调用方可以提示用户先补交易记录。
        """
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
            "exit_date": exit_date,
            "exit_reason": exit_reason,
            "followed_plan": followed_plan,
            "failure_tags": failure_tags,
            "failure_note": failure_note,
            "review": review,
        }
        for key, value in updates.items():
            if value is not None:
                target[key] = value
        target["updated_at"] = datetime.now().isoformat(timespec="seconds")

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

    def summarize_failures(self) -> Dict[str, Any]:
        """统计失败数据库。

        亏损判断优先看 result_5d_pct，其次看 max_drawdown_pct。
        failure_tags 用来沉淀亏损模式，例如：追高、缩量、板块退潮、假突破。
        """
        entries = self.load()
        loss_entries = [item for item in entries if _is_loss_trade(item)]

        tag_counter: Counter[str] = Counter()
        exit_reason_counter: Counter[str] = Counter()
        plan_break_count = 0

        for item in loss_entries:
            tag_counter.update(item.get("failure_tags") or [])
            if item.get("exit_reason"):
                exit_reason_counter.update([item["exit_reason"]])
            if item.get("followed_plan") is False:
                plan_break_count += 1

        return {
            "loss_count": len(loss_entries),
            "top_failure_tags": tag_counter.most_common(10),
            "exit_reasons": exit_reason_counter.most_common(10),
            "plan_break_count": plan_break_count,
            "plan_break_rate_pct": round(plan_break_count / len(loss_entries) * 100, 2) if loss_entries else None,
        }

    def generate_learning_notes(self) -> List[str]:
        """基于现有日志生成简单学习提示。"""
        notes: List[str] = []
        failure_summary = self.summarize_failures()
        score_summary = self.summarize_by_score_bucket()

        top_tags = failure_summary.get("top_failure_tags") or []
        if top_tags:
            tag, count = top_tags[0]
            notes.append(f"最近亏损最常见原因是：{tag}（{count} 次），下次出现该标签时建议降低仓位。")

        plan_break_rate = failure_summary.get("plan_break_rate_pct")
        if plan_break_rate is not None and plan_break_rate >= 30:
            notes.append(f"亏损交易中有 {plan_break_rate}% 未按计划执行，优先优化纪律，而不是优化选股。")

        for row in score_summary:
            if row["completed_count"] >= 5 and row["avg_5d_pct"] is not None:
                if row["avg_5d_pct"] < 0:
                    notes.append(f"评分区间 {row['bucket']} 的 5 日平均收益为 {row['avg_5d_pct']}%，暂时不宜盲目加仓。")
                elif row["win_rate_pct"] is not None and row["win_rate_pct"] >= 60:
                    notes.append(f"评分区间 {row['bucket']} 当前胜率 {row['win_rate_pct']}%，可以继续观察是否稳定。")

        if not notes:
            notes.append("交易样本还不够，先持续记录 30-50 笔，再判断评分系统是否有效。")
        return notes


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


def _is_loss_trade(item: Dict[str, Any]) -> bool:
    result_5d = item.get("result_5d_pct")
    if result_5d is not None:
        return float(result_5d) < 0

    max_drawdown = item.get("max_drawdown_pct")
    if max_drawdown is not None:
        return float(max_drawdown) < 0

    return False
