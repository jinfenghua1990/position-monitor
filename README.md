# 持仓管理系统

## 功能介绍

### 核心定位
**持仓监控与管理系统** — 实时监控持仓状态，触发止盈止损提醒。

### 监控内容
- **持仓盘面**: 实时盈亏、成本、收益率
- **资金账户**: 可用资金、冻结资金
- **课仓查询**: 当日持仓、历史成交
- **委托记录**: 挂单状态跟踪

### 智能提醒
| 类型 | 触发条件 | 操作 |
|------|----------|------|
| 止盈提醒 | 单票浮盈≥+15% | 建议减仓 |
| 止损提醒 | 单票浮亏≥-5% | 建议止损 |
| 盘中异动 | 幅度>±3% | 通知关注 |
| 清仓提醒 | 反弹到成本价 | 建议出局 |

### 数据来源
**mx-moni skill**: 妙想模拟组合API
- 持仓查询
- 资金查询
- 当日委托
- 历史成交

### 输出示例
```
========================================
📊 持仓监控报告
========================================

资金账户
----------------------------------------
总资金: 100,000 元
可用: 35,000 元
市值: 68,500 元
盈亏: +3,500 元 (+3.5%)

持仓明细
----------------------------------------
代码     名称      成本     现价     盈亏     状态
300XXX   半导体A   50.00   52.00   +4.0%   🟢
600XXX   新能源B   30.00   28.50   -5.0%   🔴止损

🔔 智能提醒
----------------------------------------
⚠️ 600XXX 触发止损线(-5%)，建议立即处理
🟢 300XXX 盈利+4%，可考虑适度减仓

========================================
```

## 版本历史

- **v1.0.0** - 初始版本

## 安装使用

### 下载
```bash
# 从GitHub下载
git clone https://github.com/jinfenghua1990/position-monitor.git

# 或从Gitee下载（国内更快）
git clone https://gitee.com/ginohei/position-monitor.git
```

### 安装依赖
见各系统内的 INSTALL.md

### 发版本
```bash
./release.sh v1.1.0 "更新说明"
```

## 下载地址

- **GitHub**: https://github.com/jinfenghua1990/position-monitor/releases
- **Gitee** (推荐): https://gitee.com/ginohei/position-monitor/releases

## 其他说明

本系统是股票分析系统的一部分，其他6个相关系统：
- 板块轮动预警: https://gitee.com/ginohei/sector-rotation-alert
- 超短线交易: https://gitee.com/ginohei/ultrashort-trading
- 四维分析: https://gitee.com/ginohei/stock-4d-analysis
- 信号汇总: https://gitee.com/ginohei/trading-signal-hub
- 持仓管理: https://gitee.com/ginohei/position-monitor
- Hermes Robots: https://gitee.com/ginohei/hermes-robots
- 妙想Skills: https://gitee.com/ginohei/mx-skills-kit
