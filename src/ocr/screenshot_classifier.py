class ScreenshotClassifier:
    """
    自动识别截图类型。

    当前支持：
    - 持仓截图
    - 委托截图
    - 成交截图
    - 资金截图

    后续可以继续增加：
    - 自选股
    - 分时图
    - 龙虎榜
    """

    POSITION_KEYWORDS = [
        '持仓', '证券代码', '证券名称', '盈亏', '持仓数量',
        '成本价', '市值', '浮动盈亏'
    ]

    ORDER_KEYWORDS = [
        '委托', '委托时间', '委托价格', '委托数量',
        '已撤', '未成交', '部分成交'
    ]

    TRADE_KEYWORDS = [
        '成交', '成交时间', '成交均价', '成交数量',
        '买入成交', '卖出成交'
    ]

    ACCOUNT_KEYWORDS = [
        '总资产', '可用资金', '冻结资金', '账户资产',
        '资金余额', '可取金额'
    ]

    def classify(self, text):
        text = text or ''

        score_map = {
            'positions': self._score(text, self.POSITION_KEYWORDS),
            'orders': self._score(text, self.ORDER_KEYWORDS),
            'trades': self._score(text, self.TRADE_KEYWORDS),
            'account': self._score(text, self.ACCOUNT_KEYWORDS),
        }

        best_type = max(score_map, key=score_map.get)
        best_score = score_map[best_type]

        if best_score <= 0:
            return {
                'type': 'unknown',
                'score_map': score_map,
            }

        return {
            'type': best_type,
            'score_map': score_map,
        }

    def _score(self, text, keywords):
        score = 0

        for keyword in keywords:
            if keyword in text:
                score += 1

        return score


if __name__ == '__main__':
    demo_text = '''
    证券代码 证券名称 持仓数量 成本价 市值 浮动盈亏
    300001 示例科技 1000 10.00 11800 1800
    '''

    classifier = ScreenshotClassifier()
    result = classifier.classify(demo_text)

    print(result)
