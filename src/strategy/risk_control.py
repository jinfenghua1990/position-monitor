def check_risk_rules(positions, config):
    rules = config.get('risk_rules', {})
    take_profit = rules.get('take_profit_pct', 15)
    stop_loss = rules.get('stop_loss_pct', -5)

    alerts = []

    for position in positions:
        pct = position.get('profit_pct', 0)
        symbol = position.get('symbol')
        name = position.get('name')

        if pct >= take_profit:
            alerts.append(
                f'{symbol} {name} 已达到止盈线 ({pct}%)，建议关注减仓。'
            )

        if pct <= stop_loss:
            alerts.append(
                f'{symbol} {name} 已触发止损线 ({pct}%)，注意风险。'
            )

    return alerts
