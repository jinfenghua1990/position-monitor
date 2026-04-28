#!/usr/bin/env python3
"""
position_monitor.py - 持仓监控与止盈止损信号

定时查询模拟组合持仓，检查止盈止损条件，触发时写入信号队列。

用法:
  python3 position_monitor.py              # 正常监控
  python3 position_monitor.py --test       # 测试模式（不写信号）
  python3 position_monitor.py --set-stop 600519 -5%  # 设置止损线
"""

import os
import sys
import json
import requests
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# ===== 配置 =====
MX_APIKEY = os.environ.get('MX_APIKEY', '')
MX_API_URL = os.environ.get('MX_API_URL', 'https://mkapi2.dfcfs.com/finskillshub')
OUTPUT_DIR = Path(os.environ.get('MX_OUTPUT_DIR', '/tmp/mx_moni'))
SIGNAL_DIR = Path(os.environ.get('TRADING_SIGNAL_DIR', '/tmp/trading_signals'))
STOP_CONFIG = Path.home() / '.hermes' / 'position_stops.json'

# 止盈止损默认阈值
DEFAULT_STOP_LOSS = -8.0   # 止损: 亏损8%
DEFAULT_TAKE_PROFIT = 15.0  # 止盈: 盈利15%

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SIGNAL_DIR.mkdir(parents=True, exist_ok=True)


def check_apikey():
    if not MX_APIKEY:
        print("❌ 未配置 MX_APIKEY")
        sys.exit(1)


def fetch_positions() -> List[Dict]:
    """查询模拟组合持仓"""
    check_apikey()
    
    url = f"{MX_API_URL}/api/claw/mockTrading/positions"
    headers = {'apikey': MX_APIKEY, 'Content-Type': 'application/json'}
    
    try:
        resp = requests.post(url, headers=headers, json={'moneyUnit': 1})
        resp.raise_for_status()
        result = resp.json()
        
        # 保存原始数据
        raw_path = OUTPUT_DIR / 'position_monitor_positions.json'
        with open(raw_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        if not result.get('success') and str(result.get('code')) != '200':
            print(f"❌ 查询失败: {result.get('message')}")
            return []
        
        positions = result.get('data', {}).get('posList', [])
        return positions
        
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return []


def fetch_current_price(stock_code: str) -> Optional[float]:
    """获取当前股价（通过妙想API）"""
    # 简化版：使用 mx-data 的实时行情
    try:
        # 调用 mx-data 获取实时价格
        from mx_data import MarketData
        mx = MarketData()
        quote = mx.get_quote(stock_code)
        if quote and 'price' in quote:
            return float(quote['price'])
    except:
        pass
    
    # 备用：从持仓数据中获取（上次成交价）
    return None


def load_stop_config() -> Dict:
    """加载止盈止损配置"""
    if STOP_CONFIG.exists():
        try:
            with open(STOP_CONFIG, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}


def save_stop_config(config: Dict):
    """保存止盈止损配置"""
    STOP_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    with open(STOP_CONFIG, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def write_signal(stock_code: str, stock_name: str, direction: str, 
                 signal_type: str, reason: str, quantity: int, 
                 profit_pct: float) -> bool:
    """写入交易信号"""
    import subprocess
    signal_script = Path.home() / '.hermes/skills/finance/trading-signal-hub/signal_push.py'
    
    if not signal_script.exists():
        print(f"❌ 信号脚本不存在: {signal_script}")
        return False
    
    try:
        result = subprocess.run([
            'python3', str(signal_script),
            '--action', 'write',
            '--stock-code', stock_code,
            '--stock-name', stock_name,
            '--direction', direction,
            '--source', 'hermes1',
            '--signal-type', signal_type,
            '--reason', reason,
            '--quantity', str(quantity),
            '--score', str(abs(profit_pct))
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"  ✅ 信号已写入: {stock_name}({stock_code})")
            return True
        else:
            print(f"  ❌ 写入失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"  ❌ 写入异常: {e}")
        return False


def check_positions(test_mode: bool = False):
    """检查持仓止盈止损"""
    positions = fetch_positions()
    
    if not positions:
        print("ℹ️ 当前无持仓")
        return
    
    stop_config = load_stop_config()
    
    print(f"\n📊 持仓监控 ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
    print("=" * 60)
    
    alerts = []
    
    for pos in positions:
        code = pos.get('stockCode', '')
        name = pos.get('stockName', '')
        quantity = pos.get('quantity', 0)
        cost_price = pos.get('costPrice', 0)
        current_price = pos.get('currentPrice', cost_price)  # 持仓数据可能含当前价
        
        # 计算盈亏比例
        if cost_price > 0:
            profit_pct = ((current_price - cost_price) / cost_price) * 100
        else:
            profit_pct = 0
        
        # 获取个性化止盈止损阈值
        cfg = stop_config.get(code, {})
        stop_loss = cfg.get('stop_loss', DEFAULT_STOP_LOSS)
        take_profit = cfg.get('take_profit', DEFAULT_TAKE_PROFIT)
        
        # 判断盈亏
        pnl_icon = "🟢" if profit_pct >= 0 else "🔴"
        pnl_str = f"{profit_pct:+.2f}%"
        
        print(f"\n{pnl_icon} {name}({code}) x{quantity}股")
        print(f"   成本: {cost_price:.2f} | 现价: {current_price:.2f} | 盈亏: {pnl_str}")
        
        # 检查止损
        if profit_pct <= stop_loss:
            alert_msg = f"⚠️ 触发止损 ({profit_pct:.2f}% ≤ {stop_loss}%)"
            print(f"   {alert_msg}")
            
            if not test_mode:
                reason = f"持仓亏损{profit_pct:.1f}%触发止损({stop_loss}%)"
                write_signal(code, name, 'sell', 'stop_loss', reason, quantity, profit_pct)
            alerts.append(('stop_loss', code, name, profit_pct))
        
        # 检查止盈
        elif profit_pct >= take_profit:
            alert_msg = f"🎯 触发止盈 ({profit_pct:.2f}% ≥ {take_profit}%)"
            print(f"   {alert_msg}")
            
            if not test_mode:
                reason = f"持仓盈利{profit_pct:.1f}%触发止盈({take_profit}%)"
                write_signal(code, name, 'sell', 'take_profit', reason, quantity, profit_pct)
            alerts.append(('take_profit', code, name, profit_pct))
    
    print("\n" + "=" * 60)
    
    if alerts:
        print(f"📋 共 {len(alerts)} 条止盈止损信号")
        if test_mode:
            print("   ⚠️ 测试模式：信号未写入")
    else:
        print("✅ 当前无触发止盈止损")
    
    return alerts


def set_stop(stock_code: str, stop_loss: Optional[float] = None, 
             take_profit: Optional[float] = None):
    """设置止盈止损阈值"""
    config = load_stop_config()
    
    if stock_code not in config:
        config[stock_code] = {}
    
    if stop_loss is not None:
        config[stock_code]['stop_loss'] = stop_loss
        print(f"✅ {stock_code} 止损线设置为 {stop_loss}%")
    
    if take_profit is not None:
        config[stock_code]['take_profit'] = take_profit
        print(f"✅ {stock_code} 止盈线设置为 {take_profit}%")
    
    save_stop_config(config)
    print(f"📁 配置已保存: {STOP_CONFIG}")


def main():
    parser = argparse.ArgumentParser(description='持仓监控与止盈止损')
    parser.add_argument('--test', action='store_true', help='测试模式（不写信号）')
    parser.add_argument('--set-stop', metavar='CODE', help='设置止盈止损')
    parser.add_argument('--stop-loss', type=float, help='止损阈值(%%)')
    parser.add_argument('--take-profit', type=float, help='止盈阈值(%%)')
    
    args = parser.parse_args()
    
    if args.set_stop:
        set_stop(args.set_stop, args.stop_loss, args.take_profit)
    else:
        check_positions(test_mode=args.test)


if __name__ == '__main__':
    main()
