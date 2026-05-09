def analyze_second_wave(config):
    second_wave_config = config.get('second_wave', {})

    if not second_wave_config.get('enabled', False):
        return []

    # 这里后续会接入真实历史盈利交易记录。
    # 当前先给出示例结构。
    watchlist = [
        {
            'symbol': '300001',
            'name': '示例科技',
            'pullback_pct': 8,
            'signal': '重新站上5日线',
        },
        {
            'symbol': '600009',
            'name': '半导体趋势股',
            'pullback_pct': 12,
            'signal': '放量突破',
        },
    ]

    result = []

    for item in watchlist:
        result.append(
            f"{item['symbol']} {item['name']} 回调{item['pullback_pct']}%，{item['signal']}，可关注二波机会。"
        )

    return result
