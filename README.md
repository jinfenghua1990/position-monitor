# position-monitor

个人 AI 交易辅助系统：持仓监控、风控提醒、二波观察、交易评分、交易日志、失败数据库与每日复盘。

> 本项目不是自动交易机器人，也不承诺预测涨跌。它的目标是帮助个人投资者建立交易纪律、沉淀交易记忆、统计评分有效性，并持续优化自己的交易模式。

---

## 当前定位

position-monitor 已从早期“持仓监控工具”升级为：

```text
文本/截图/OCR 数据
→ 结构化持仓
→ 风控分析
→ 二波观察
→ 交易日志
→ 失败模式统计
→ 每日复盘
→ AI 学习建议
```

适合以下场景：

- 每天手工回传同花顺/券商持仓文本
- 记录买入理由、评分、仓位和止损
- 3日/5日后回写交易结果
- 统计不同评分区间的胜率和平均收益
- 发现常见亏损原因，例如追高、缩量、假突破、板块退潮
- 沉淀“曾经盈利股票”的二波观察池

---

## 核心功能

### 1. 文本回传解析

支持粘贴类似文本：

```text
300001 示例科技 成本10.00 现价11.80 盈亏18%
600001 新能源A 成本20.00 现价18.80 盈亏-6%
```

也支持较宽松的表格/OCR文本：

```text
证券代码 证券名称 持仓 可用 成本价 现价 市值 盈亏 盈亏比例
300001 示例科技 1000 800 10.00 11.80 11800 1800 18%
```

### 2. 风控提醒

根据 `config.yaml` 触发：

- 止盈提醒
- 止损提醒
- 单票风险提醒
- 仓位风险提醒

### 3. 二波观察池

用于跟踪曾经盈利卖出的股票，观察其后续是否出现：

- 回调企稳
- 放量突破
- 重新站上均线
- 接近前高

### 4. 交易日志与评分系统

记录每笔交易：

- 股票代码/名称
- 动作：观察、买入、卖出、跳过
- 当前评分
- 买入理由
- 仓位
- 止损
- 预期

### 5. 结果回写与失败数据库

3日或5日后回写：

- 1日收益
- 3日收益
- 5日收益
- 最大盈利
- 最大回撤
- 退出原因
- 是否按计划执行
- 失败标签：追高、缩量、假突破、板块退潮等

系统会统计：

- 不同评分区间胜率
- 平均收益
- 平均回撤
- 最常见亏损原因
- 纪律失控比例

### 6. 每日 Pipeline

`src/pipeline.py` 已经打通：

```text
文本输入 → 持仓解析 → 风控分析 → 二波观察 → 日报生成 → AI学习建议
```

---

## 项目结构

```text
position-monitor/
├── main.py                         # 命令行入口
├── config.yaml                     # 风控、二波、提醒配置
├── requirements.txt                # Python依赖
├── README_USAGE.md                 # 每日使用流程
├── src/
│   ├── pipeline.py                 # 每日主流程
│   ├── data/
│   │   └── text_importer.py        # 文本/OCR结果解析
│   ├── journal/
│   │   └── trading_journal.py      # 交易日志、结果回写、失败统计
│   ├── strategy/
│   │   ├── risk_control.py         # 风控规则
│   │   └── second_wave.py          # 二波观察
│   ├── report/
│   │   └── reporter.py             # 日报生成
│   └── ocr/
│       ├── screenshot_parser.py    # 截图OCR入口
│       └── screenshot_classifier.py# 截图类型识别
├── data/
│   ├── history_trades.json
│   ├── second_wave_pool.json
│   └── trading_journal.json        # 自动生成，交易日志数据
└── reports/                        # 自动生成，每日报告
```

---

## 安装

```bash
git clone https://github.com/jinfenghua1990/position-monitor.git
cd position-monitor
python -m venv .venv
source .venv/bin/activate  # Windows 使用 .venv\\Scripts\\activate
pip install -r requirements.txt
```

如暂时不用 OCR，可先不安装 PaddleOCR 相关依赖；文本回传流程不依赖截图识别。

---

## 快速使用

### 方式一：从文件读取持仓文本

创建文件：

```bash
mkdir -p data/input
cat > data/input/positions.txt <<'EOF'
300001 示例科技 成本10.00 现价11.80 盈亏18%
600001 新能源A 成本20.00 现价18.80 盈亏-6%
EOF
```

运行：

```bash
python main.py --input data/input/positions.txt
```

### 方式二：从命令行标准输入粘贴

```bash
python main.py
```

然后粘贴持仓文本，按 Ctrl+D 结束输入。

---

## 每日交易记录格式

买入/观察前记录：

```text
记录交易：
股票：300XXX
名称：示例科技
动作：买入
评分：83
仓位：20%
止损：-4%
理由：
- 二波回踩
- 放量
- 站上5日线
预期：3日内冲前高
```

3日/5日后回写结果：

```text
回写结果：
股票：300XXX
买入日期：2026-05-09
1日结果：+2%
3日结果：+5%
5日结果：-1%
最大盈利：+8%
最大回撤：-4%
退出原因：止盈
是否按计划：是
失败原因：
- 追高
- 板块退潮
复盘：买点没问题，但卖点过早。
```

详细流程见：[`README_USAGE.md`](README_USAGE.md)

---

## Skill / Agent 集成方向

本项目已经具备标准主流程，可作为 Hermes、OpenClaw 或其他 Agent 的 Skill 基础：

- 输入：持仓文本、交易记录、结果回写
- 输出：风控提醒、二波观察、日报、学习建议
- 核心入口：`src/pipeline.py`
- 命令行入口：`main.py`

后续可以继续封装：

```text
position-monitor-skill
```

能力包括：

- analyze_positions
- add_trade_journal
- update_trade_result
- summarize_failures
- generate_daily_report

---

## 版本路线

### v2.1 当前阶段

- 文本回传主流程
- 风控分析
- 二波观察
- 交易评分记录
- 结果回写
- 失败数据库
- 每日报告
- AI学习建议

### v2.2 下一阶段

- SQLite 持久化
- Telegram / 企业微信提醒
- Web Dashboard
- 更完整的二波评分系统

### v3.0 方向

- 个性化交易风格学习
- AI复盘
- 情绪风险识别
- 评分有效性回测

---

## 核心原则

不要追求“95分神票”。

真正重要的是：

```text
长期正期望 + 风险控制 + 纪律执行 + 持续复盘
```

本项目的价值，是帮助你长期沉淀自己的交易数据库，让系统逐渐理解：

- 哪种结构你更容易赚钱
- 哪种行情你更容易亏损
- 哪种评分区间更有效
- 哪些失败模式需要规避
