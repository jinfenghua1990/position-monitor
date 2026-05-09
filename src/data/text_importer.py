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
    """

    def __init__(self):
        self.today = datetime.now().strftime('%Y-%m-%d')

    def save_raw_text(self, text, category='positions'):
        daily_dir = Path(f'data/daily/{self.today}')
        daily_dir.mkdir(parents=True, exist_ok=True)

        file_path = daily_dir / f'{category}.txt'

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)

        return str(file_path)

    def parse_positions(self, text):
        """
        示例格式：

        300001 示例科技 成本10.00 现价11.80 盈亏18%
        600001 新能源A 成本20.00 现价18.80 盈亏-6%
        """

        positions = []

        pattern = re.findall(
            r'(\d{6})\s+(\S+)\s+成本([\d\.]+)\s+现价([\d\.]+)\s+盈亏([\-\d\.]+)%',
            text
        )

        for item in pattern:
            positions.append({
                'symbol': item[0],
                'name': item[1],
                'cost_price': float(item[2]),
                'current_price': float(item[3]),
                'profit_pct': float(item[4]),
            })

        return positions


if __name__ == '__main__':
    demo_text = '''
    300001 示例科技 成本10.00 现价11.80 盈亏18%
    600001 新能源A 成本20.00 现价18.80 盈亏-6%
    '''

    importer = TextDataImporter()

    parsed = importer.parse_positions(demo_text)

    print(parsed)
