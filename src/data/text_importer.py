import re
from datetime import datetime
from pathlib import Path


class TextDataImporter:
    """
    文本数据导入器

    适用于：
    - 券商复制文本
    - OCR结果
    - 手工粘贴持仓
    - 微信/聊天记录

    设计原则：
    - 先尽量解析，不轻易失败。
    - OCR 文本通常会出现空格错位、列名混杂、百分号缺失。
    - 解析结果不确定时，也保留 raw_line 方便人工排查。
    """

    HEADER_KEYWORDS = [
        '证券代码', '证券名称', '股票代码', '股票名称', '持仓', '可用',
        '成本价', '现价', '最新价', '市值', '盈亏', '盈亏比例', '浮动盈亏'
    ]

    def __init__(self):
        self.today = datetime.now().strftime('%Y-%m-%d')

    def save_raw_text(self, text, category='positions'):
        daily_dir = Path(f'data/daily/{self.today}')
        daily_dir.mkdir(parents=True, exist_ok=True)

        file_path = daily_dir / f'{category}.txt'

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)

        return str(file_path)

    def normalize_text(self, text):
        text = text.replace('％', '%')
        text = text.replace('，', ',')
        text = text.replace('＋', '+')
        text = text.replace('－', '-')
        text = text.replace('—', '-')
        text = re.sub(r'[\t,|]+', ' ', text)
        text = re.sub(r' +', ' ', text)
        return text.strip()

    def _is_header_or_noise(self, line):
        if not line:
            return True

        if any(keyword in line for keyword in self.HEADER_KEYWORDS) and not re.search(r'\d{6}', line):
            return True

        # 太短且没有股票代码，基本不是有效行。
        if len(line) < 6 and not re.search(r'\d{6}', line):
            return True

        return False

    def _safe_float(self, value):
        if value is None:
            return None

        value = str(value).replace('%', '').replace('+', '').strip()

        try:
            return float(value)
        except ValueError:
            return None

    def parse_positions(self, text):
        """
        支持两类输入：

        1. 标准手工格式：
           300001 示例科技 成本10.00 现价11.80 盈亏18%

        2. 同花顺/OCR 宽松格式：
           300001 示例科技 1000 800 10.00 11.80 11800 1800 18%
        """

        normalized = self.normalize_text(text)
        positions = []

        for raw_line in normalized.splitlines():
            line = raw_line.strip()

            if self._is_header_or_noise(line):
                continue

            parsed = self._parse_standard_line(line)

            if not parsed:
                parsed = self._parse_loose_table_line(line)

            if parsed:
                parsed['raw_line'] = raw_line.strip()
                positions.append(parsed)

        return positions

    def _parse_standard_line(self, line):
        pattern = re.search(
            r'(\d{6})\s+(\S+)\s+成本\s*([\d\.]+)\s+现价\s*([\d\.]+)\s+盈亏\s*([\+\-\d\.]+)%?',
            line
        )

        if not pattern:
            return None

        return {
            'symbol': pattern.group(1),
            'name': pattern.group(2),
            'cost_price': self._safe_float(pattern.group(3)),
            'current_price': self._safe_float(pattern.group(4)),
            'profit_pct': self._safe_float(pattern.group(5)),
        }

    def _parse_loose_table_line(self, line):
        symbol_match = re.search(r'\b(\d{6})\b', line)

        if not symbol_match:
            return None

        symbol = symbol_match.group(1)
        after_symbol = line[symbol_match.end():].strip()

        # 股票名称通常出现在代码后的第一个中文/中英文 token。
        name_match = re.search(r'([\u4e00-\u9fa5A-Za-z\*STst]+)', after_symbol)
        name = name_match.group(1) if name_match else ''

        numbers = re.findall(r'[\+\-]?\d+(?:\.\d+)?%?', line)
        numbers = [n for n in numbers if n != symbol]

        numeric_values = [self._safe_float(n) for n in numbers]
        numeric_values = [n for n in numeric_values if n is not None]

        # 常见同花顺列：持仓、可用、成本价、现价、市值、盈亏、盈亏比例
        cost_price = None
        current_price = None
        profit_pct = None

        percent_match = re.search(r'([\+\-]?\d+(?:\.\d+)?)\s*%', line)
        if percent_match:
            profit_pct = self._safe_float(percent_match.group(1))

        # 如果没有百分号，尝试取最后一个看起来像百分比的数字。
        if profit_pct is None and numeric_values:
            candidate = numeric_values[-1]
            if -100 <= candidate <= 100:
                profit_pct = candidate

        # 尝试从数字序列中找成本价、现价。
        # 对常见持仓行，前两个大整数通常是持仓/可用，后面两个小数通常是成本/现价。
        price_candidates = [n for n in numeric_values if 0 < n < 10000]

        if len(price_candidates) >= 4:
            cost_price = price_candidates[2]
            current_price = price_candidates[3]
        elif len(price_candidates) >= 2:
            cost_price = price_candidates[0]
            current_price = price_candidates[1]

        return {
            'symbol': symbol,
            'name': name,
            'cost_price': cost_price,
            'current_price': current_price,
            'profit_pct': profit_pct,
        }


if __name__ == '__main__':
    demo_text = '''
    证券代码 证券名称 持仓 可用 成本价 现价 市值 盈亏 盈亏比例
    300001 示例科技 1000 800 10.00 11.80 11800 1800 18%
    600001 新能源A 成本20.00 现价18.80 盈亏-6%
    '''

    importer = TextDataImporter()
    parsed = importer.parse_positions(demo_text)
    print(parsed)
