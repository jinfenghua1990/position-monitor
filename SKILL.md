---
name: position-monitor
description: 持仓监控与止盈止损系统 - 查询模拟组合持仓，检查止盈止损条件，触发预警信号
version: 1.0.0
tags:
  - 持仓监控
  - 止盈止损
  - 预警通知
  - 妙想API
dependencies:
  - requests
---

# 持仓监控系统 (position-monitor)

## 功能

- **持仓查询**: 通过 mx-moni API 查询模拟组合持仓
- **止盈止损检查**: 实时监控盈亏比例，触发阈值时生成信号
- **信号推送**: 触发信号写入 trading-signal-hub 队列

## 使用方法

### 监控持仓
```bash
python3 ~/.hermes-robot-3/skills/position-monitor/position_monitor.py
```

### 测试模式（不写信号）
```bash
python3 ~/.hermes-robot-3/skills/position-monitor/position_monitor.py --test
```

### 设置止盈止损
```bash
# 设置止损线
python3 ~/.hermes-robot-3/skills/position-monitor/position_monitor.py --set-stop 600519 --stop-loss -8

# 设置止盈线
python3 ~/.hermes-robot-3/skills/position-monitor/position_monitor.py --set-stop 600519 --take-profit 15

# 同时设置
python3 ~/.hermes-robot-3/skills/position-monitor/position_monitor.py --set-stop 600519 --stop-loss -5 --take-profit 20
```

## 默认阈值

| 类型 | 阈值 |
|------|------|
| 止损 | -8% |
| 止盈 | +15% |

## 配置文件

止盈止损配置保存在: `~/.hermes/position_stops.json`

格式:
```json
{
  "600519": {
    "stop_loss": -5.0,
    "take_profit": 20.0
  }
}
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| MX_APIKEY | 妙想API密钥 | (必填) |
| MX_API_URL | API地址 | https://mkapi2.dfcfs.com/finskillshub |
| MX_OUTPUT_DIR | 输出目录 | /tmp/mx_moni |
| TRADING_SIGNAL_DIR | 信号目录 | /tmp/trading_signals |

## 输出示例

```
📊 持仓监控 (2025-05-07 12:30)
============================================================

🟢 贵州茅台(600519) x100股
   成本: 1800.00 | 现价: 1850.00 | 盈亏: +2.78%

🔴 某某股票(002XXX) x200股
   成本: 25.00 | 现价: 22.50 | 盈亏: -10.00%
   ⚠️ 触发止损 (-10.00% ≤ -8%)

============================================================
📋 共 1 条止盈止损信号
```

## 关联系统

- **mx-moni**: 妙想模拟组合 API
- **trading-signal-hub**: 信号汇总系统
- **mx-data**: 实时行情数据

## Pitfalls

### 0. Robot-3 初始化工作流程
Robot-3 应首先检查本地 skills 目录 `~/.hermes-robot-3/skills/`，而非调用 `skills_list()` 列出全局 skills。用户配置的"软路由"意味着已预装本地专属 skills。

```python
# ✅ 正确：先检查本地
import os
local_skills_dir = os.path.expanduser('~/.hermes-robot-3/skills')
if os.path.exists(local_skills_dir):
    # 列出本地 skills
    skills = [d for d in os.listdir(local_skills_dir) 
              if os.path.isdir(os.path.join(local_skills_dir, d)) and not d.startswith('.')]
```

### 1. 妙想API字段名不匹配
文档中描述的字段名（如 `stockCode`, `stockName`, `quantity`）与妙想API实际返回的字段名**不一致**：

| 文档字段 | 实际字段 | 处理方式 |
|----------|----------|----------|
| `stockCode` | `secCode` | 使用 `pos.get('secCode', pos.get('stockCode', ''))` |
| `stockName` | `secName` | 使用 `pos.get('secName', pos.get('stockName', ''))` |
| `quantity` | `count` | 使用 `pos.get('count', pos.get('quantity', 0))` |
| `costPrice` | `costPrice` + `costPriceDec` | 价格需除以 `10^costPriceDec` |
| `currentPrice` | `price` + `priceDec` | 价格需除以 `10^priceDec` |

**详细字段映射参考**: `references/miaoxiang-api-fields.md`

### 2. 价格精度问题
妙想API返回的价格是整数倍价格，必须除以精度因子才能得到真实价格：

```python
# ❌ 错误：直接使用返回值
cost_price = pos['costPrice']  # 得到 93054

# ✅ 正确：除以精度因子
cost_price = pos['costPrice'] / (10 ** pos['costPriceDec'])  # 得到 93.054
```

### 3. 盈亏比例直接可用
`profitPct` 字段已经是百分比数值（如 25.9378 表示 +25.94%），无需手动计算或乘100。

## 维护者

Robot-3 (持仓管理专家)

## 更新记录

- 2026-05-07: v1.0.1 - 修复妙想API字段映射bug，添加 references/miaoxiang-api-fields.md