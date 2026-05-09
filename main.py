import yaml
from rich.console import Console
from rich.table import Table

from src.strategy.risk_control import check_risk_rules
from src.strategy.second_wave import analyze_second_wave

console = Console()


def load_config():
    with open('config.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def mock_positions():
    return [
        {
            'symbol': '300001',
            'name': '示例科技',
            'cost_price': 10.0,
            'current_price': 11.8,
            'profit_pct': 18.0,
        },
        {
            'symbol': '600001',
            'name': '新能源A',
            'cost_price': 20.0,
            'current_price': 18.8,
            'profit_pct': -6.0,
        },
    ]


def main():
    config = load_config()
    positions = mock_positions()

    console.print('\n📊 持仓监控系统 v2.0\n', style='bold green')

    table = Table(title='当前持仓')
    table.add_column('代码')
    table.add_column('名称')
    table.add_column('成本')
    table.add_column('现价')
    table.add_column('收益率')

    for p in positions:
        table.add_row(
            p['symbol'],
            p['name'],
            str(p['cost_price']),
            str(p['current_price']),
            f"{p['profit_pct']}%"
        )

    console.print(table)

    alerts = check_risk_rules(positions, config)

    if alerts:
        console.print('\n⚠ 风控提醒', style='bold red')
        for item in alerts:
            console.print(f'- {item}')

    second_wave = analyze_second_wave(config)

    if second_wave:
        console.print('\n🔁 二波观察池', style='bold yellow')
        for item in second_wave:
            console.print(f'- {item}')


if __name__ == '__main__':
    main()
