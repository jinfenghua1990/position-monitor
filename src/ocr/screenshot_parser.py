from pathlib import Path

from src.data.text_importer import TextDataImporter


class ScreenshotParser:
    """
    截图识别入口。

    当前设计目标：
    1. 优先使用 PaddleOCR 识别中文券商/同花顺截图。
    2. OCR 得到原始文本后，复用 TextDataImporter 做结构化解析。
    3. 如果本地未安装 OCR 依赖，给出明确提示，不影响文本导入流程。
    """

    def __init__(self):
        self.text_importer = TextDataImporter()

    def extract_text(self, image_path):
        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(f'截图文件不存在: {image_path}')

        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:
            raise RuntimeError(
                '未安装 PaddleOCR。请先运行: pip install paddleocr paddlepaddle'
            ) from exc

        ocr = PaddleOCR(use_angle_cls=True, lang='ch')
        result = ocr.ocr(str(image_path), cls=True)

        lines = []

        for page in result:
            if not page:
                continue
            for row in page:
                if len(row) >= 2 and row[1]:
                    lines.append(row[1][0])

        return '\n'.join(lines)

    def parse_positions_from_screenshot(self, image_path):
        raw_text = self.extract_text(image_path)
        positions = self.text_importer.parse_positions(raw_text)

        return {
            'raw_text': raw_text,
            'positions': positions,
        }


if __name__ == '__main__':
    parser = ScreenshotParser()
    print('请在代码中传入同花顺持仓截图路径，例如: parser.parse_positions_from_screenshot("data/screenshots/position.png")')
