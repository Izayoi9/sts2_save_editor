"""STS2 存档修改器 — 入口文件。"""

import sys
from pathlib import Path

# 将项目根目录加入 sys.path，确保模块能正确导入
sys.path.insert(0, str(Path(__file__).parent))

__version__ = "1.0.0"

from ui.app import App


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
