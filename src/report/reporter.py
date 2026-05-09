from datetime import datetime
from pathlib import Path


def generate_daily_report(positions, alerts, second_wave_items):
    today = datetime.now().strftime('%Y_%m_%d')

    report_dir = Path('reports')
    report_dir.mkdir(exist_ok=True)

    report_path = report_dir / f'daily_report_{today}.md'

    content = []

    content.append(f'# 每日持仓报告 {today}\n')

    content.append('## 当前持仓\n')

    for p in positions:
        content.append(
            f"- {p['symbol']} {p['name']} 收益率: {p['profit_pct']}%"
        )

    content.append('\n## 风控提醒\n')

    if alerts:
        for item in alerts:
            content.append(f'- {item}')
    else:
        content.append('- 今日暂无风控警报')

    content.append('\n## 二波观察池\n')

    if second_wave_items:
        for item in second_wave_items:
            content.append(f'- {item}')
    else:
        content.append('- 暂无二波观察目标')

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))

    return str(report_path)
